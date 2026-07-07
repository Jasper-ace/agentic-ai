import React, { useState } from 'react';
import CodeBlock from './CodeBlock';

export default function MessageBubble({ message }) {
  const { sender, text, timestamp, file, evaluation } = message;
  const isUser = sender === 'user';
  const [showFileContent, setShowFileContent] = useState(false);
  const [isEvalExpanded, setIsEvalExpanded] = useState(false);

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
              // Parse simple markdown paragraphs and lists
              return (
                <div key={index} style={styles.textParagraph}>
                  {part.content.split('\n').map((line, lIdx) => {
                    // Check if it's a list item
                    if (line.trim().startsWith('- ') || line.trim().startsWith('* ')) {
                      return (
                        <li key={lIdx} style={styles.listItem}>
                          {line.replace(/^[-*]\s+/, '')}
                        </li>
                      );
                    }
                    // Return normal line, or line break
                    return (
                      <p key={lIdx} style={{ margin: line.trim() === '' ? '10px 0' : '2px 0' }}>
                        {line}
                      </p>
                    );
                  })}
                </div>
              );
            }
          })}
        </div>
        )}

        {/* RAG Triad Evaluation Panel */}
        {!isUser && evaluation && (
          <div style={styles.evaluationContainer}>
            <div 
              style={styles.evaluationHeader} 
              onClick={() => setIsEvalExpanded(!isEvalExpanded)}
              title="Click to view details"
            >
              <div style={styles.evaluationHeaderLeft}>
                <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.5" style={{ color: 'var(--color-primary)' }}>
                  <path d="M12 22s8-4 8-10V5l-8-3-8 3v7c0 6 8 10 8 10z"/>
                </svg>
                <span style={styles.evaluationTitle}>RAG Triad Quality Metrics</span>
              </div>
              <div style={styles.evaluationHeaderRight}>
                <span style={styles.evaluationAverage}>
                  Avg: {((evaluation.context_relevance.score + evaluation.groundedness.score + evaluation.answer_relevance.score) / 3 * 100).toFixed(0)}%
                </span>
                <svg 
                  width="14" 
                  height="14" 
                  viewBox="0 0 24 24" 
                  fill="none" 
                  stroke="currentColor" 
                  strokeWidth="2.5" 
                  style={{ 
                    transform: isEvalExpanded ? 'rotate(180deg)' : 'rotate(0deg)', 
                    transition: 'transform 0.2s ease',
                    color: 'var(--color-text-muted)',
                    marginLeft: '4px'
                  }}
                >
                  <polyline points="6 9 12 15 18 9"></polyline>
                </svg>
              </div>
            </div>

            {isEvalExpanded && (
              <div style={styles.evaluationBody}>
                {Object.entries({
                  'Context Relevance': { ...evaluation.context_relevance, label: 'Context Relevance', desc: 'Is retrieved context relevant to query?' },
                  'Groundedness': { ...evaluation.groundedness, label: 'Groundedness / Faithfulness', desc: 'Is response fully grounded in context?' },
                  'Answer Relevance': { ...evaluation.answer_relevance, label: 'Answer Relevance', desc: 'Is response relevant to user query?' }
                }).map(([key, data]) => {
                  const scorePct = (data.score * 100).toFixed(0);
                  let statusColor = '#ef4444'; // Red
                  let statusBg = 'rgba(239, 68, 68, 0.1)';
                  let statusText = 'Low';
                  
                  if (data.score >= 0.8) {
                    statusColor = '#0d9488'; // Teal
                    statusBg = 'rgba(13, 148, 136, 0.1)';
                    statusText = 'Excellent';
                  } else if (data.score >= 0.5) {
                    statusColor = '#f59e0b'; // Amber
                    statusBg = 'rgba(245, 158, 11, 0.1)';
                    statusText = 'Fair';
                  }

                  return (
                    <div key={key} style={styles.metricRow}>
                      <div style={styles.metricMeta}>
                        <div>
                          <span style={styles.metricName}>{data.label}</span>
                          <span style={styles.metricDesc}>{data.desc}</span>
                        </div>
                        <div style={styles.metricScoreWrapper}>
                          <span style={{ ...styles.metricBadge, backgroundColor: statusBg, color: statusColor }}>
                            {statusText}
                          </span>
                          <span style={{ ...styles.metricScoreValue, color: statusColor }}>
                            {scorePct}%
                          </span>
                        </div>
                      </div>
                      <div style={styles.progressContainer}>
                        <div style={{ ...styles.progressBar, width: `${scorePct}%`, backgroundColor: statusColor }}></div>
                      </div>
                      <div style={styles.metricReason}>
                        <strong>Rationale:</strong> {data.reason}
                      </div>
                    </div>
                  );
                })}
              </div>
            )}
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
  },
  evaluationContainer: {
    marginTop: '12px',
    border: '1px solid var(--color-border)',
    borderRadius: '12px',
    backgroundColor: 'var(--color-surface-container-low)',
    overflow: 'hidden',
    fontSize: '13px',
    width: '100%',
    boxShadow: '0 2px 8px var(--color-shadow)',
  },
  evaluationHeader: {
    display: 'flex',
    justifyContent: 'space-between',
    alignItems: 'center',
    padding: '10px 14px',
    backgroundColor: 'var(--color-surface-container-high)',
    cursor: 'pointer',
    userSelect: 'none',
    borderBottom: '1px solid var(--color-border)',
    transition: 'background-color var(--transition-fast)',
  },
  evaluationHeaderLeft: {
    display: 'flex',
    alignItems: 'center',
    gap: '8px',
  },
  evaluationTitle: {
    fontWeight: '600',
    color: 'var(--color-text-main)',
  },
  evaluationHeaderRight: {
    display: 'flex',
    alignItems: 'center',
    gap: '6px',
  },
  evaluationAverage: {
    fontSize: '11px',
    fontWeight: '600',
    color: 'var(--color-primary)',
    backgroundColor: 'var(--color-surface)',
    padding: '2px 8px',
    borderRadius: '12px',
    border: '1px solid var(--color-border)',
  },
  evaluationBody: {
    padding: '14px',
    display: 'flex',
    flexDirection: 'column',
    gap: '14px',
    backgroundColor: 'var(--color-surface)',
  },
  metricRow: {
    display: 'flex',
    flexDirection: 'column',
    gap: '6px',
    paddingBottom: '10px',
    borderBottom: '1px solid var(--color-border)',
  },
  metricMeta: {
    display: 'flex',
    justifyContent: 'space-between',
    alignItems: 'flex-start',
  },
  metricName: {
    fontWeight: '600',
    color: 'var(--color-text-main)',
    display: 'block',
  },
  metricDesc: {
    fontSize: '11px',
    color: 'var(--color-text-muted)',
    display: 'block',
    marginTop: '1px',
  },
  metricScoreWrapper: {
    display: 'flex',
    alignItems: 'center',
    gap: '8px',
  },
  metricBadge: {
    fontSize: '10px',
    fontWeight: '600',
    padding: '2px 8px',
    borderRadius: '12px',
    textTransform: 'uppercase',
  },
  metricScoreValue: {
    fontWeight: '700',
    fontSize: '14px',
  },
  progressContainer: {
    height: '6px',
    backgroundColor: 'var(--color-surface-container-low)',
    borderRadius: '3px',
    overflow: 'hidden',
    width: '100%',
  },
  progressBar: {
    height: '100%',
    borderRadius: '3px',
    transition: 'width 0.3s ease',
  },
  metricReason: {
    fontSize: '11px',
    color: 'var(--color-text-muted)',
    lineHeight: '1.4',
    marginTop: '2px',
  }
};
