// this script is to handle the Input box for user to type and send messages.

import React from "react";

interface MsgInput {
    input: (message:string) => void;
    disabled?: boolean;
}

const MessageInput: React.FC<MsgInput> = ({ input, disabled }) => {
    const [message, setMessage] = React.useState("");

    const handleSubmit = (e: React.FormEvent) => {
        e.preventDefault();
        if (message.trim()){
            input(message.trim());
            setMessage("");
        }
    }

    return (
    <form onSubmit={handleSubmit} style={{ display: 'flex', gap: 8 }}>
      <input
        type="text"
        value={message}
        onChange={e => setMessage(e.target.value)}
        placeholder="Type your query here..."
        style={{ flex: 1, padding: 8, borderRadius: 4, border: '1px solid #ccc' }}
        disabled={disabled}
      />
      <button type="submit" style={{ padding: '8px 16px', borderRadius: 4, background:
        '#667eea', color: '#fff', border: 'none' }} disabled={disabled}>
        Send
      </button>
    </form>
  );
};


export default MessageInput;