import re
import json
from langchain_pinecone import PineconeVectorStore

session_keeper = {}

def norm(s):
    return s.lower().replace("-", "").replace(" ", "")

def extract_part_number(text):
    # Matches PS followed by 6+ digits, with optional dash/space
    match = re.search(r"\bPS[-\s]?\d{6,}\b", text, re.IGNORECASE)
    if match:
        return match.group(0)
    return None

def extract_model_number(text):
    # Example: matches models like WDT780SAEM1, FGID2476SF, etc.
    match = re.search(r"\b[A-Z]{2,}\d[A-Z0-9]+\b", text)
    if match:
        return match.group(0)
    return None

ORDER_ID_RE = re.compile(r"\bPSO\d{4}\b", re.IGNORECASE)
def extract_order_id(text: str):
    m = ORDER_ID_RE.search(text or "")
    return m.group(0).upper() if m else None

def resolve_entities(session_id, text):
    part = extract_part_number(text)
    model = extract_model_number(text)
    order = extract_order_id(text)
    ctx = session_keeper.setdefault(session_id, {"active_part": None, "active_model": None, "active_order": None})


    if not part and ("this part" in text.lower() or "does this part" in text.lower()):
        part = ctx["active_part"]

    if not order and "this order" in text.lower():
        order = ctx["active_order"]

    # Update context when we see new entities
    if part:
        ctx["active_part"] = norm(part)
    if model:
        ctx["active_model"] = norm(model)

    if order:
        ctx["active_order"] = norm(order)
    return part, model, order, ctx



"""For routing to the correct namespace. We can add LLM Fallback if the user query is not clear."""
TXN_ORDER_KWS = {"order", "status", "track", "tracking", "cancel", "return", "refund", "exchange", "city"}
TXN_POLICY_KWS = {"shipping", "delivery", "policy", "refund policy", "return policy", "cancellation policy", "cancel policy"}
def route_intent(text: str, session_id: str | None = None) -> str:
    t = text.lower()

    if any(k in t for k in TXN_POLICY_KWS):
        return "transactions_policy"
    
    if any(k in t for k in TXN_ORDER_KWS):
        return "transactions_order"

    if extract_order_id(text):
        return "transactions_order"
    if extract_part_number(text) or extract_model_number(text):
        return "products"
    if session_id:
        ctx = session_keeper.get(session_id, {})
        if ctx.get("active_order"):
            return "transactions_order"
    return "products"

def static_policies():
    policies = {}
    policies["return policy"] = "You can return most items within 30 days of delivery. Please visit our Returns page for details."
    policies["cancellation policy"] = "You can cancel your order within 5 hours of placing it. Orders that are out for delivery/shipped cannot be cancelled. Please visit our Cancellations page for details."
    policies["shipping policy"] = "Shipping times and costs vary by location, however, we offer free shipping on orders over $50. Standard shipping takes 3-5 business days. Please visit our Shipping page for details."

    return policies

# # ----------------- Transaction tools -----------------
# def _load_txn_data():
#     with open("data/transactions_data.json") as f:
#         return json.load(f)

# def get_order_status(order_id: str) -> dict:
#     txns = _load_txn_data()
#     for t in txns:
#         if t["order_id"].upper() == order_id.upper():
#             return {"ok": True, "order_id": t["order_id"], "status": t["status"], "carrier": t["carrier"], "created_id": t["created_id"], "address_city": t["address_city"], "items": t["items"]}
#     return {"ok": False, "error": "Order not found."}

# def cancel_order(order_id: str) -> dict:
#     txns = _load_txn_data()
#     for t in txns:
#         if t["order_id"].upper() == order_id.upper():
#             if t["status"] == "order_placed":
#                 return {"ok": True, "message": f"Order {order_id} cancellation request submitted."}
#             return {"ok": False, "message": f"Order {order_id} cannot be cancelled because status is '{t['status']}'."}
#     return {"ok": False, "message": "Order not found."}

# def initiate_return(order_id: str, part_number: str | None = None, reason: str | None = None) -> dict:
#     txns = _load_txn_data()
#     for t in txns:
#         if t["order_id"].upper() == order_id.upper():
#             return {"ok": True, "message": f"Return initiated for order {order_id}" + (f", item {part_number}" if part_number else "") + "."}
#     return {"ok": False, "message": "Order not found."}

# def status_get(raw: str | None) -> str:
#     if not raw:
#         return "being processed"
#     m = {
#         "order_placed": "placed and awaiting shipment",
#         "processing": "being prepared for shipment",
#         "shipped": "shipped",
#         "out for delivery": "out for delivery",
#         "delivered": "delivered",
#         "return_initiated": "in return processing",
#         "cancelled": "cancelled",
#     }
#     key = str(raw).lower().strip()
#     return m.get(key, key.replace("_", " "))

# def items(items: list[dict]) -> str:
#     if not items:
#         return "no items listed"
#     parts = [f"{it.get('qty', 1)} x {it.get('part_number', 'unknown')}" for it in items]
#     if len(parts) == 1:
#         return parts[0]
#     return ", ".join(parts[:-1]) + f", and {parts[-1]}"

# def format_order_answer(res: dict, user_msg: str) -> str:
#     if not res.get("ok"):
#         return res.get("error") or "Sorry, I couldn't retrieve your order right now."

#     # If tool already produced a user-facing message, prefer it.
#     if res.get("message") and not res.get("status"):
#         return res["message"]

#     oid = res.get("order_id", "your order")
#     status = status_get(res.get("status"))
#     carrier = res.get("carrier") or "the carrier"
#     created = res.get("created_id") or "an unknown date"
#     city = res.get("address_city") or "your address"
#     items_str = items(res.get("items", []))

#     m = (user_msg or "").lower()

#     if any(k in m for k in ["status", "track", "tracking"]):
#         return (
#             f"Your order {oid} is currently {status} with {carrier}. "
#             f"It's heading to {city}. Items in this order: {items_str}."
#         )

#     if "cancel" in m:
#         # If cancel tool returns a message, it was handled above.
#         return (
#             f"I have submitted a cancellation request for order {oid}. "
#             f"The current status is {status}. You'll receive a confirmation shortly."
#         )

#     if any(k in m for k in ["return", "refund", "exchange"]):
#         return (
#             f"I have initiated a return for order {oid}. "
#             f"A label from {carrier} will be sent to you. Items affected: {items_str}."
#         )

#     return (
#         f"Order {oid} was placed on {created}. "
#         f"The current status is {status} with {carrier}, shipping to {city}. "
#         f"Items: {items_str}.")