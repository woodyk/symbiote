import React, { useState } from 'react';
import axios from 'axios';
import ChatBox from '../components/ChatBox';

function ChatPage() {
  const [messages, setMessages] = useState([]);

  const handleSendMessage = async (message) => {
    const response = await axios.post('/chat', { message });
    setMessages([...messages, { text: response.data.response, sender: 'AI' }]);
  };

  return (
    <div>
      <h1>Chat with AI</h1>
      <ChatBox messages={messages} onSendMessage={handleSendMessage} />
    </div>
  );
}

export default ChatPage;
