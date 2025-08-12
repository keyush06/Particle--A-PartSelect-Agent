// this is a list for the all the messages that one can see in a session chat

// import React  from "react";
import { useEffect, useRef } from "react";
import type { ChatMessage } from "../types/chats";

// ncode
interface Props {
  messages: ChatMessage[];
  error?: string | null;
}

export default function MsgList({ messages, error }: Props) {
  const endRef = useRef<HTMLDivElement | null>(null);
  useEffect(() => { endRef.current?.scrollIntoView({ behavior: "smooth" }); }, [messages, error]);

  return (
    <div className="messages">
      {messages.map((m) => (
        <div key={m.id} className={`row ${m.sender === "user" ? "user" : "bot"}`}>
          <div className="bubble">{m.message}</div>
        </div>
      ))}
      {error && (
        <div className="row bot">
          <div className="bubble" style={{ borderColor: "#fecaca", background: "#fff1f2", color: "#7f1d1d" }}>
            {error}
          </div>
        </div>
      )}
      <div ref={endRef} />
    </div>
  );
}

// interface MsgListProps {
//     messages: ChatMessage[];
// }

// // React.FC (or React.FunctionComponent) is a TypeScript type provided by React that represents 
// // the type of a functional component. It is used to explicitly 
// // define the expected type of a functional component, including its props and return type.

// const MessageList: React.FC<MsgListProps> = ({ messages }) => (
//     <div style={{minHeight: 300, marginBottom: 16}}>
//         {messages.map(msg => (
//       <div key={msg.id} style={{ textAlign: msg.sender === 'user' ? 'right' : 'left' }}>
//         <div
//           style={{
//             display: 'inline-block',
//             background: msg.sender === 'user' ? '#e0e7ff' : '#f1f5f9',
//             color: '#22223b',
//             borderRadius: 8,
//             padding: '8px 12px',
//             margin: '4px 0',
//             maxWidth: '70%',
//           }}
//         >
//           {msg.message}
//         </div>
//       </div>
//     ))}
//   </div>
// );

// export default MessageList;

