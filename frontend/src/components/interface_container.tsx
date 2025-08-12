// import React from "react";
// // import { useChat } from "../hooks/useChat";
// import MessageList from "./MsgList";
// import MessageInput from "./MstInput";

// const ChatInterface: React.FC = () => {
//   const { messages, sendMessage, loading, error } = useChat();

//   return (
//     <div>
//       <MessageList messages={messages} />
//       {loading && <div style={{ color: "#888" }}>Bot is typing...</div>}
//       {error && <div style={{ color: "red" }}>{error}</div>}
//       <MessageInput input={sendMessage} disabled={loading} />
//     </div>
//   );
// };

// export default ChatInterface;

// ---------------------------------------------------------------------------------------------

import React, { useState } from "react";
import MessageInput from "./MsgInput";
import MessageList from "./MsgList";
import type { ChatSession } from "../types/chats";
import type { ChatMessage } from "../types/chats";
import {chatApi} from "../services/api";
import "./chat.css"; 

const ChatInterface: React.FC = () => {

    // Array of chats
    const [chats, setChats] = useState<ChatSession[]>([
        {session_id: null, messages: []}
    ]);


// Index of the currently active chat
    const [activeChatIdx, setActiveChatIdx] = useState(0);
    const [loading, setLoading] = useState(false);
    const [error, setError] = useState<string | null>(null);

    const handleNewChat = () => {
        setChats([...chats, { session_id: null, messages: [] }]);
        setActiveChatIdx(chats.length); // switch to the new chat
        setError(null);
    };

    const sendMessage = async (text:string, session_id: string | null) => {
        const user_message: ChatMessage = {
            id: Date.now().toString(),
            message: text,
            sender: "user",
            timestamp: new Date(),
        };

        const updatedChats = [...chats];
        updatedChats[activeChatIdx].messages.push(user_message);
        setChats(updatedChats);
        setLoading(true);
        setError(null);

        try {
            const response = await chatApi.sendMessage(text, updatedChats[activeChatIdx].session_id);
            const llm_response: ChatMessage = {
                id: Date.now().toString(),
                message: response.answer,
                sender: "bot",
                timestamp: new Date(),
            };
            updatedChats[activeChatIdx].messages.push(llm_response);

            // If there is a new session_id returned, then update the updatedchats
            if (!updatedChats[activeChatIdx].session_id && response.session_id) {
                updatedChats[activeChatIdx].session_id = response.session_id;
            }
            setChats([...updatedChats]);

        } catch (error:any) {
            console.error("Error sending message:", error);
            setError(error.message || "Failed to send message");
        } finally {
            setLoading(false);
        }
    };

    const handleSelectChat = (index: number) => {
        setActiveChatIdx(index);
        setError(null);
    };

    return (
    <div className="app-shell">
      <header className="header">
        <div className="brand">
          <img src="/public/partselect.png" alt="PartSelect" style={{ height: 58, width: 58, marginRight: 8 }} />
          <span>PartSelect Assistant</span>
        </div>
        <div className="tagline">{loading ? "Thinking..." : "PartBot"}</div>
      </header>

      <aside className="sidebar">
        <div className="logo-card">
          {/* {logo && <img src={logo} alt="PartSelect" />} */}
          <h3>PartSelect</h3>
        </div>
        <button className="new-btn" onClick={handleNewChat}>+ New Chat</button>
        {chats.map((chat, idx) => (
          <div
            key={chat.session_id || idx}
            className={`session ${idx === activeChatIdx ? "active" : ""}`}
            onClick={() => setActiveChatIdx(idx)}
          >
            Chat {idx + 1}
          </div>
        ))}
      </aside>

      <main className="chat">
        <MessageList messages={chats[activeChatIdx].messages} error={error} />
        {error && <div style={{ color: "#b91c1c", padding: "0 16px 8px" }}>{error}</div>}
        <MessageInput input={(msg: string) => sendMessage(msg, chats[activeChatIdx].session_id)} disabled={loading} />
      </main>
    </div>
  );
};

export default ChatInterface;
