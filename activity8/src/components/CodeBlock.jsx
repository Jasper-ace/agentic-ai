import React, { useState } from 'react';

export default function CodeBlock({ language, code }) {
  const [copied, setCopied] = useState(false);

  const handleCopy = async () => {
    try {
      await navigator.clipboard.writeText(code);
      setCopied(true);
      setTimeout(() => setCopied(false), 2000);
    } catch (err) {
      console.error('Failed to copy text: ', err);
    }
  };

  return (
    <div className="code-block-container" style={styles.container}>
      <div className="code-block-header" style={styles.header}>
        <span className="code-block-lang" style={styles.lang}>
          {language || 'javascript'}
        </span>
        <button className="btn-copy" onClick={handleCopy} style={styles.copyBtn}>
          {copied ? (
            <>
              <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.5">
                <polyline points="20 6 9 17 4 12"></polyline>
              </svg>
              <span>Copied!</span>
            </>
          ) : (
            <>
              <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
                <rect x="9" y="9" width="13" height="13" rx="2" ry="2"></rect>
                <path d="M5 15H4a2 2 0 0 1-2-2V4a2 2 0 0 1 2-2h9a2 2 0 0 1 2 2v1"></path>
              </svg>
              <span>Copy code</span>
            </>
          )}
        </button>
      </div>
      <pre style={styles.pre}>
        <code style={styles.code}>{code}</code>
      </pre>
    </div>
  );
}

const styles = {
  container: {
    backgroundColor: '#0b0f19',
    borderRadius: '8px',
    overflow: 'hidden',
    margin: '12px 0',
    border: '1px solid #1e293b',
    boxShadow: '0 4px 6px -1px rgba(0, 0, 0, 0.1)',
    fontFamily: 'var(--font-mono)',
    textAlign: 'left',
  },
  header: {
    display: 'flex',
    justifyContent: 'space-between',
    alignItems: 'center',
    padding: '8px 16px',
    backgroundColor: '#161b22',
    borderBottom: '1px solid #21262d',
    userSelect: 'none',
  },
  lang: {
    fontSize: '12px',
    color: '#8b949e',
    fontWeight: '500',
    textTransform: 'lowercase',
  },
  copyBtn: {
    display: 'inline-flex',
    alignItems: 'center',
    gap: '6px',
    backgroundColor: 'transparent',
    border: 'none',
    color: '#8b949e',
    cursor: 'pointer',
    fontSize: '12px',
    padding: '4px 8px',
    borderRadius: '4px',
    transition: 'all 0.15s ease',
  },
  pre: {
    padding: '16px',
    margin: '0',
    overflowX: 'auto',
  },
  code: {
    color: '#e6edf3',
    fontSize: '13px',
    fontFamily: 'var(--font-mono)',
    lineHeight: '1.6',
    whiteSpace: 'pre-wrap',
    wordBreak: 'break-all',
  }
};
