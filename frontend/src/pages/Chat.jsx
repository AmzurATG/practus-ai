import { useState, useEffect, useRef } from 'react';
import Layout from '../components/Layout';
import ChatInterface from '../components/ChatInterface';
import SuggestedQuestions from '../components/SuggestedQuestions';

export default function Chat() {
  const [messages, setMessages] = useState([]);
  const [loading, setLoading] = useState(false);
  const [suggestions, setSuggestions] = useState([]);

  useEffect(() => {
    loadSuggestions();
  }, []);

  const loadSuggestions = async () => {
    try {
      const token = localStorage.getItem('token');
      const response = await fetch('http://localhost:8080/api/chat/suggestions', {
        headers: { 'Authorization': `Bearer ${token}` }
      });
      const data = await response.json();
      setSuggestions(data.suggestions || []);
    } catch (error) {
      console.error('Error loading suggestions:', error);
    }
  };

  const sendMessage = async (query) => {
    setMessages(prev => [...prev, { role: 'user', content: query }]);
    setLoading(true);

    try {
      const token = localStorage.getItem('token');
      const response = await fetch('http://localhost:8080/api/chat/query', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'Authorization': `Bearer ${token}`
        },
        body: JSON.stringify({ query })
      });

      const data = await response.json();

      if (data.error) {
        setMessages(prev => [...prev, { role: 'error', content: data.error }]);
      } else {
        setMessages(prev => [...prev, {
          role: 'assistant',
          content: data.answer,
          actions: data.actions || [],
          suggestions: data.suggested_followups || [],
          confidence: data.confidence
        }]);
      }
    } catch (error) {
      setMessages(prev => [...prev, { 
        role: 'error', 
        content: 'Failed to get response. Please try again.' 
      }]);
    } finally {
      setLoading(false);
    }
  };

  return (
    <Layout>
      <div className="max-w-4xl mx-auto">
        <div className="mb-6">
          <h1 className="text-3xl font-bold text-gray-900">AI Assistant</h1>
          <p className="text-gray-600 mt-2">Ask questions about your business data in natural language</p>
        </div>

        {messages.length === 0 && (
          <SuggestedQuestions
            suggestions={suggestions}
            onSelect={sendMessage}
          />
        )}

        <ChatInterface
          messages={messages}
          onSendMessage={sendMessage}
          loading={loading}
        />
      </div>
    </Layout>
  );
}


