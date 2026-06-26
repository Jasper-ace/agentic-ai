import React, { useState, useEffect } from 'react';
import Sidebar from './components/Sidebar';
import ChatArea from './components/ChatArea';
import PromptBar from './components/PromptBar';

export default function App() {
  const [theme, setTheme] = useState('light');
  const [isSidebarCollapsed, setIsSidebarCollapsed] = useState(false);
  const [messages, setMessages] = useState([]);
  const [input, setInput] = useState('');
  const [isLoading, setIsLoading] = useState(false);

  // Sync theme changes with DOM attribute
  useEffect(() => {
    document.documentElement.setAttribute('data-theme', theme);
  }, [theme]);

  const handleSelectChip = (chipLabel) => {
    setInput(chipLabel);
  };

  const handleNewChat = () => {
    setMessages([]);
  };

  const handleSend = async (text, attachedFile) => {
    const timestamp = new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' });
    const userMsg = {
      id: `msg-${Date.now()}`,
      sender: 'user',
      text,
      timestamp,
      file: attachedFile
    };

    // Add user message to history
    setMessages(prev => [...prev, userMsg]);
    setIsLoading(true);

    try {
      // 1. If a file is attached, upload it to the backend first
      if (attachedFile) {
        const formData = new FormData();
        const blob = new Blob([attachedFile.content], { type: 'text/plain' });
        formData.append('files', blob, attachedFile.name);

        const uploadRes = await fetch('http://localhost:5000/upload', {
          method: 'POST',
          body: formData,
        });

        if (!uploadRes.ok) {
          const errData = await uploadRes.json();
          throw new Error(errData.error || 'Failed to index file in vector database.');
        }
      }

      // 2. Chat with RAG backend
      const chatRes = await fetch('http://localhost:5000/chat', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          message: text.trim() ? text : `Please summarize the uploaded file: ${attachedFile.name}`
        }),
      });

      if (!chatRes.ok) {
        const errData = await chatRes.json();
        throw new Error(errData.error || 'Failed to query chatbot backend.');
      }

      const chatData = await chatRes.json();
      const aiTimestamp = new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' });
      
      const aiMsg = {
        id: `msg-${Date.now() + 1}`,
        sender: 'ai',
        text: chatData.response,
        timestamp: aiTimestamp
      };

      setMessages(prev => [...prev, aiMsg]);
    } catch (error) {
      console.error(error);
      const aiTimestamp = new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' });
      const errorMsg = {
        id: `msg-${Date.now() + 1}`,
        sender: 'ai',
        text: `⚠️ **Connection Error**: ${error.message}\n\nPlease check if the Docker containers are running with \`docker compose up\` and Gemini API Key is valid.`,
        timestamp: aiTimestamp
      };
      setMessages(prev => [...prev, errorMsg]);
    } finally {
      setIsLoading(false);
    }
  };

  return (
    <div style={styles.appContainer}>
      <Sidebar
        theme={theme}
        setTheme={setTheme}
        onNewChat={handleNewChat}
        isCollapsed={isSidebarCollapsed}
        setIsCollapsed={setIsSidebarCollapsed}
      />

      <main style={styles.mainContainer}>
        {/* Top Header Row */}
        <header style={styles.chatHeader}>
          <h1 style={styles.chatHeaderTitle}>Lumina AI Chat</h1>
        </header>

        {/* Chat Scrolling Area */}
        <ChatArea
          messages={messages}
          isLoading={isLoading}
          onSelectChip={handleSelectChip}
        />

        {/* Prompt Input Area */}
        <PromptBar
          input={input}
          setInput={setInput}
          onSend={handleSend}
          isLoading={isLoading}
        />
      </main>
    </div>
  );
}

const styles = {
  appContainer: {
    display: 'flex',
    height: '100vh',
    width: '100vw',
    overflow: 'hidden',
    backgroundColor: 'var(--color-background)',
    color: 'var(--color-text-main)',
  },
  mainContainer: {
    flex: 1,
    display: 'flex',
    flexDirection: 'column',
    height: '100%',
    overflow: 'hidden',
  },
  chatHeader: {
    display: 'flex',
    justifyContent: 'space-between',
    alignItems: 'center',
    padding: '0 24px',
    height: '70px',
    borderBottom: '1px solid var(--color-border)',
    flexShrink: 0,
    userSelect: 'none',
  },
  chatHeaderTitle: {
    fontSize: '16px',
    fontWeight: '600',
    color: 'var(--color-text-main)',
    whiteSpace: 'nowrap',
    overflow: 'hidden',
    textOverflow: 'ellipsis',
    maxWidth: '70%',
  }
};
