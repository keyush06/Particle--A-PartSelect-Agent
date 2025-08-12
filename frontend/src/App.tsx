import { useState } from 'react'
import React from 'react';
import './App.css'
import ChatInterface from './components/interface_container';

function App() {
  // const [count, setCount] = useState(0)

  return (
    <div className="page">
      <header className="page-header">
        <h1 className="title">Particle</h1>
        <p className="subtitle">Shoot your questions about products and transactions</p>
      </header>
      
      <main className="app-main" style={{
            display: "flex",
            justifyContent: "center",
            alignItems: "center",
            minHeight: "90vh"
          }}>
        <div className="chat-container">
          {/* Chat components will go here */}
          <ChatInterface />
        </div>
      </main>
    </div>
  );
}

export default App
