import React, { useState } from 'react';
import CodeBlock from './CodeBlock';

export default function MessageBubble({ message }) {
  const { sender, text, timestamp, file } = message;
  const isUser = sender === 'user';
  const [showFileContent, setShowFileContent] = useState(false);

  // Helper to parse message text into text chunks and code blocks
  const parseMessageContent = (content) => {
    if (!content) return [];
    
    const parts = [];
    const regex = /```(\w*)\n([\s\S]*?)```/g;
    let lastIndex = 0;
    let match;

    while ((match = regex.exec(content)) !== null) {
      // Add text before the code block
      if (match.index > lastIndex) {
        parts.push({
          type: 'text',
          content: content.substring(lastIndex, match.index),
        });
      }
      
      // Add the code block
      parts.push({
        type: 'code',
        language: match[1] || 'javascript',
        content: match[2],
      });

      lastIndex = regex.lastIndex;
    }

    // Add remaining text
    if (lastIndex < content.length) {
      parts.push({
        type: 'text',
        content: content.substring(lastIndex),
      });
    }

    return parts;
  };

  const parsedParts = parseMessageContent(text);

  return (
    <div style={{
      ...styles.wrapper,
      justifyContent: isUser ? 'flex-end' : 'flex-start',
    }}>
      {/* AI Avatar */}
      {!isUser && (
        <div style={styles.avatar}>
          <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.5">
            <path d="M12 2a10 10 0 0 1 10 10c0 5.523-4.477 10-10 10S2 17.523 2 12A10 10 0 0 1 12 2z"></path>
            <path d="M12 6v6l4 2"></path>
          </svg>
        </div>
      )}

      {/* Bubble Container */}
      <div style={{
        ...styles.bubble,
        backgroundColor: isUser 
          ? 'var(--color-surface-container)' 
          : 'transparent',
        border: isUser ? 'none' : '1px solid var(--color-border)',
        borderRadius: isUser 
          ? '1.5rem 1.5rem 0.25rem 1.5rem' 
          : '1.5rem 1.5rem 1.5rem 0.25rem',
        maxWidth: '75%',
      }}>
        {file && (
          <div className="message-file-card" style={styles.fileCard}>
            <div style={styles.fileIconContainer}>
              <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.5" style={{ color: 'var(--color-primary)' }}>
                <path d="M14.5 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V7.5L14.5 2z"></path>
                <polyline points="14 2 14 8 20 8"></polyline>
              </svg>
            </div>
            <div style={styles.fileCardDetails}>
              <div style={styles.fileCardName} title={file.name}>{file.name}</div>
              <div style={styles.fileCardSize}>{(file.size / 1024).toFixed(1)} KB • Text File</div>
            </div>
            <button 
              onClick={() => setShowFileContent(!showFileContent)} 
              className="btn btn-secondary"
              style={styles.fileViewBtn}
            >
              {showFileContent ? 'Hide' : 'View'}
            </button>
          </div>
        )}

        {file && showFileContent && (
          <div style={styles.expandedContent} className="animate-fade-in">
            <CodeBlock 
              language={file.name.split('.').pop() || 'text'} 
              code={file.content} 
            />
          </div>
        )}

        {text && (
          <div style={styles.content}>
          {parsedParts.map((part, index) => {
            if (part.type === 'code') {
              return (
                <CodeBlock 
                  key={index} 
                  language={part.language} 
                  code={part.content} 
                />
              );
            } else {
              // Helper to parse inline markdown (bold, italic, inline code)
              const parseInlineMarkdown = (rawText) => {
                let html = rawText
                  .replace(/&/g, "&amp;")
                  .replace(/</g, "&lt;")
                  .replace(/>/g, "&gt;");
                
                // Bold: **text**
                html = html.replace(/\*\*(.*?)\*\*/g, '<strong>$1</strong>');
                // Italic: *text*
                html = html.replace(/\*(.*?)\*/g, '<em>$1</em>');
                // Inline Code: `text`
                html = html.replace(/`(.*?)`/g, '<code style="background-color: var(--color-surface-container-high); padding: 2px 6px; border-radius: 4px; font-family: monospace; font-size: 0.9em; color: var(--color-primary);">$1</code>');
                
                return <span dangerouslySetInnerHTML={{ __html: html }} />;
              };

              // Parse headings, dividers, and lists
              return (
                <div key={index} style={styles.textParagraph}>
                  {part.content.split('\n').map((line, lIdx) => {
                    const trimmed = line.trim();
                    
                    // 1. Horizontal Rules
                    if (trimmed === '---') {
                      return <hr key={lIdx} style={{ border: 'none', borderTop: '1px solid var(--color-border)', margin: '16px 0' }} />;
                    }
                    
                    // 2. Headings
                    if (trimmed.startsWith('### ')) {
                      return <h3 key={lIdx} style={{ fontSize: '1.1rem', fontWeight: '600', margin: '14px 0 6px 0', color: 'var(--color-primary)' }}>{parseInlineMarkdown(trimmed.replace(/^###\s+/, ''))}</h3>;
                    }
                    if (trimmed.startsWith('## ')) {
                      return <h2 key={lIdx} style={{ fontSize: '1.25rem', fontWeight: '600', margin: '16px 0 8px 0', color: 'var(--color-primary)' }}>{parseInlineMarkdown(trimmed.replace(/^##\s+/, ''))}</h2>;
                    }
                    if (trimmed.startsWith('# ')) {
                      return <h1 key={lIdx} style={{ fontSize: '1.4rem', fontWeight: '600', margin: '18px 0 10px 0', color: 'var(--color-primary)' }}>{parseInlineMarkdown(trimmed.replace(/^#\s+/, ''))}</h1>;
                    }
                    
                    // 3. List Items
                    if (trimmed.startsWith('- ') || trimmed.startsWith('* ')) {
                      return (
                        <li key={lIdx} style={styles.listItem}>
                          {parseInlineMarkdown(trimmed.replace(/^[-*]\s+/, ''))}
                        </li>
                      );
                    }
                    
                    // 4. Normal Paragraph (skip empty lines or render spaces)
                    if (trimmed === '') {
                      return <div key={lIdx} style={{ height: '10px' }} />;
                    }
                    
                    return (
                      <p key={lIdx} style={{ margin: '2px 0' }}>
                        {parseInlineMarkdown(line)}
                      </p>
                    );
                  })}
                </div>
              );
            }
          })}
        </div>
        )}
        <div style={{
          ...styles.time,
          textAlign: isUser ? 'right' : 'left',
        }}>
          {timestamp}
        </div>
      </div>
    </div>
  );
}

const styles = {
  wrapper: {
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
  bubble: {
    padding: '12px 18px',
    boxShadow: '0 2px 6px var(--color-shadow)',
    transition: 'all 0.2s ease',
  },
  content: {
    fontSize: '15px',
    lineHeight: '1.6',
    color: 'var(--color-text-main)',
    wordBreak: 'break-word',
  },
  textParagraph: {
    display: 'flex',
    flexDirection: 'column',
  },
  listItem: {
    marginLeft: '20px',
    listStyleType: 'disc',
    margin: '4px 0 4px 20px',
  },
  time: {
    fontSize: '10px',
    color: 'var(--color-text-muted)',
    marginTop: '6px',
    userSelect: 'none',
  },
  fileCard: {
    display: 'flex',
    alignItems: 'center',
    padding: '10px 14px',
    backgroundColor: 'var(--color-surface)',
    border: '1px solid var(--color-border)',
    borderRadius: 'var(--radius-md)',
    gap: '12px',
    marginBottom: '8px',
    minWidth: '240px',
    maxWidth: '100%',
  },
  fileIconContainer: {
    display: 'flex',
    alignItems: 'center',
    justifyContent: 'center',
    width: '36px',
    height: '36px',
    borderRadius: '8px',
    backgroundColor: 'var(--color-surface-container-high)',
    flexShrink: 0,
  },
  fileCardDetails: {
    display: 'flex',
    flexDirection: 'column',
    overflow: 'hidden',
    flex: 1,
    marginRight: '8px',
  },
  fileCardName: {
    fontSize: '13px',
    fontWeight: '600',
    color: 'var(--color-text-main)',
    whiteSpace: 'nowrap',
    overflow: 'hidden',
    textOverflow: 'ellipsis',
  },
  fileCardSize: {
    fontSize: '11px',
    color: 'var(--color-text-muted)',
  },
  fileViewBtn: {
    fontSize: '12px',
    padding: '4px 10px',
    height: 'auto',
    borderRadius: '6px',
    flexShrink: 0,
  },
  expandedContent: {
    marginTop: '8px',
    width: '100%',
  }
};
