import json
import random
from datetime import datetime, timedelta

def random_date_within_last_year():
    days_ago = random.randint(0, 364)
    date = datetime.now() - timedelta(days=days_ago)
    return date.strftime("%Y-%m-%d")

def generate_order_id(i):
    return f"PSO{1000 + i}"

def generate_customer_id():
    return str(random.randint(10000, 99999))

def generate_status():
    return random.choice(["order_placed", "shipped", "out for delivery"])

def generate_carrier():
    return random.choice(["UPS", "Delivery"])

def generate_city():
    cities = [
        "New York", "Los Angeles", "Chicago", "Houston", "Phoenix", "Philadelphia",
        "San Antonio", "San Diego", "Dallas", "San Jose", "Austin", "Jacksonville"
    ]
    return random.choice(cities)

def generate_items(parts, max_items=3):
    num_items = random.randint(1, max_items)
    items = []
    chosen_parts = random.sample(parts, num_items)
    for part in chosen_parts:
        qty = random.randint(1, 3)
        # Remove $ and commas, convert to float
        unit_price = float(part["price"].replace("$", "").replace(",", ""))
        total_price = round(unit_price * qty, 2)
        items.append({
            "part_number": part["part_number"],
            "qty": qty,
            "price": total_price
        })
    return items

def main():
    # Load parts data
    with open("data/parts_data.json") as f:
        parts = json.load(f)

    num_orders = 200
    orders = []
    for i in range(num_orders):
        items = generate_items(parts)
        order = {
            "order_id": generate_order_id(i),
            "customer_id": generate_customer_id(),
            "created_id": random_date_within_last_year(),
            "status": generate_status(),
            "carrier": generate_carrier(),
            "items": items,
            "address_city": generate_city()
        }
        orders.append(order)

    with open("data/transactions_data.json", "w") as f:
        json.dump(orders, f, indent=2)

    print(f"Generated {num_orders} synthetic transactions.")

if __name__ == "__main__":
    main()