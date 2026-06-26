import React, { useRef, useEffect } from 'react';
import MessageBubble from './MessageBubble';
import SuggestedChips from './SuggestedChips';

export default function ChatArea({ 
  messages, 
  isLoading, 
  onSelectChip 
}) {
  const bottomRef = useRef(null);

  // Auto-scroll to bottom of chat
  useEffect(() => {
    bottomRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, [messages, isLoading]);

  return (
    <div style={styles.chatArea}>
      {/* Main Messages View */}
      <div style={styles.messageScrollArea}>
        {messages.length === 0 ? (
          <div style={styles.welcomeContainer}>
            <div style={styles.welcomeHeader}>
              <div style={styles.welcomeIcon}>L</div>
              <h2 style={styles.welcomeTitle}>How can I help you today?</h2>
              <p style={styles.welcomeSub}>I'm Lumina, your adaptive AI companion designed to streamline writing, coding, and thinking.</p>
            </div>
            
            <SuggestedChips onSelectChip={onSelectChip} />
          </div>
        ) : (
          <div style={styles.messageList}>
            {messages.map((msg) => (
              <MessageBubble key={msg.id} message={msg} />
            ))}
            
            {/* AI Typing Indicator */}
            {isLoading && (
              <div style={styles.typingWrapper} className="animate-fade-in">
                <div style={styles.avatar}>
                  <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.5">
                    <path d="M12 2a10 10 0 0 1 10 10c0 5.523-4.477 10-10 10S2 17.523 2 12A10 10 0 0 1 12 2z"></path>
                    <path d="M12 6v6l4 2"></path>
                  </svg>
                </div>
                <div style={styles.typingBubble}>
                  <div className="typing-dot"></div>
                  <div className="typing-dot"></div>
                  <div className="typing-dot"></div>
                </div>
              </div>
            )}
            <div ref={bottomRef} />
          </div>
        )}
      </div>
    </div>
  );
}

const styles = {
  chatArea: {
    flex: 1,
    display: 'flex',
    flexDirection: 'column',
    height: '100%',
    position: 'relative',
    overflow: 'hidden',
  },
  messageScrollArea: {
    flex: 1,
    overflowY: 'auto',
    display: 'flex',
    flexDirection: 'column',
  },
  welcomeContainer: {
    flex: 1,
    display: 'flex',
    flexDirection: 'column',
    justifyContent: 'center',
    alignItems: 'center',
    padding: '40px 20px',
  },
  welcomeHeader: {
    textAlign: 'center',
    maxWidth: '540px',
    marginBottom: '20px',
  },
  welcomeIcon: {
    width: '64px',
    height: '64px',
    borderRadius: '16px',
    backgroundColor: 'var(--color-primary-container)',
    color: 'var(--color-primary)',
    display: 'flex',
    alignItems: 'center',
    justifyContent: 'center',
    fontWeight: 'bold',
    fontSize: '32px',
    margin: '0 auto 24px auto',
    boxShadow: '0 4px 12px var(--color-shadow)',
  },
  welcomeTitle: {
    fontSize: '28px',
    fontWeight: '600',
    color: 'var(--color-text-main)',
    marginBottom: '12px',
  },
  welcomeSub: {
    fontSize: '15px',
    color: 'var(--color-text-muted)',
    lineHeight: '1.5',
  },
  messageList: {
    width: '100%',
    maxWidth: 'var(--chat-max-width)',
    margin: '0 auto',
    padding: '24px 20px',
    flex: 1,
  },
  typingWrapper: {
    display: 'flex',
    alignItems: 'flex-start',
    gap: '12px',
    margin: '16px 0',
    width: '100%',
  },
  avatar: {
    width: '36px',
    height: '36px',
    borderRadius: '50%',
    backgroundColor: 'var(--color-primary-container)',
    color: 'var(--color-primary)',
    display: 'flex',
    alignItems: 'center',
    justifyContent: 'center',
    flexShrink: 0,
    boxShadow: '0 2px 4px rgba(0, 104, 95, 0.1)',
  },
  typingBubble: {
    padding: '16px 20px',
    backgroundColor: 'transparent',
    border: '1px solid var(--color-border)',
    borderRadius: '1.5rem 1.5rem 1.5rem 0.25rem',
    display: 'flex',
    alignItems: 'center',
    gap: '6px',
    boxShadow: '0 2px 6px var(--color-shadow)',
  }
};
