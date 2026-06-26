import React, { useRef, useEffect, useState } from 'react';

export default function PromptBar({ input, setInput, onSend, isLoading }) {
  const textareaRef = useRef(null);
  const fileInputRef = useRef(null);
  const [attachedFile, setAttachedFile] = useState(null);

  // Auto-grow height on content change
  useEffect(() => {
    if (textareaRef.current) {
      textareaRef.current.style.height = 'auto';
      textareaRef.current.style.height = `${Math.min(textareaRef.current.scrollHeight, 200)}px`;
    }
  }, [input]);

  const handleKeyDown = (e) => {
    // Submit on Enter without Shift key
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault();
      handleSubmit();
    }
  };

  const handleAttachClick = () => {
    if (fileInputRef.current) {
      fileInputRef.current.click();
    }
  };

  const handleFileChange = (e) => {
    const file = e.target.files[0];
    if (!file) return;

    const reader = new FileReader();
    reader.onload = (event) => {
      setAttachedFile({
        name: file.name,
        size: file.size,
        type: file.type || 'text/plain',
        content: event.target.result,
      });
    };
    reader.readAsText(file);
    e.target.value = ''; // Reset input
  };

  const handleRemoveFile = () => {
    setAttachedFile(null);
  };

  const handleSubmit = () => {
    if ((input.trim() || attachedFile) && !isLoading) {
      onSend(input, attachedFile);
      setInput('');
      setAttachedFile(null);
      if (textareaRef.current) {
        textareaRef.current.style.height = 'auto';
      }
    }
  };

  return (
    <div style={styles.outerContainer}>
      <div style={styles.promptBar}>
        {attachedFile && (
          <div className="file-preview-card">
            <div style={styles.fileIconWrapper}>
              <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.5" style={{ color: 'var(--color-primary)' }}>
                <path d="M14.5 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V7.5L14.5 2z"></path>
                <polyline points="14 2 14 8 20 8"></polyline>
              </svg>
            </div>
            <div style={styles.fileDetails}>
              <div style={styles.fileName} title={attachedFile.name}>{attachedFile.name}</div>
              <div style={styles.fileSize}>{(attachedFile.size / 1024).toFixed(1)} KB</div>
            </div>
            <button 
              onClick={handleRemoveFile}
              className="file-remove-btn"
              title="Remove file"
            >
              <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.5">
                <line x1="18" y1="6" x2="6" y2="18"></line>
                <line x1="6" y1="6" x2="18" y2="18"></line>
              </svg>
            </button>
          </div>
        )}

        <div style={styles.inputRow}>
          <button
            onClick={handleAttachClick}
            disabled={isLoading}
            className="attach-btn"
            style={{
              cursor: isLoading ? 'not-allowed' : 'pointer',
            }}
            title="Upload Text File"
          >
            <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.5">
              <path d="m21.44 11.05-9.19 9.19a6 6 0 0 1-8.49-8.49l9.19-9.19a4 4 0 0 1 5.66 5.66l-9.2 9.19a2 2 0 0 1-2.83-2.83l8.49-8.48" />
            </svg>
          </button>
          <input
            type="file"
            ref={fileInputRef}
            onChange={handleFileChange}
            accept=".txt,.js,.py,.html,.css,.json,.md,.csv,.ts,.jsx,.tsx"
            style={{ display: 'none' }}
          />

          <textarea
            ref={textareaRef}
            value={input}
            onChange={(e) => setInput(e.target.value)}
            onKeyDown={handleKeyDown}
            placeholder="Message Lumina AI or upload a file..."
            rows={1}
            disabled={isLoading}
            style={{
              ...styles.textarea,
              color: 'var(--color-text-main)',
            }}
          />
          <button
            onClick={handleSubmit}
            disabled={(!input.trim() && !attachedFile) || isLoading}
            style={{
              ...styles.sendBtn,
              backgroundColor: (input.trim() || attachedFile) && !isLoading ? 'var(--color-primary)' : 'var(--color-surface)',
              color: (input.trim() || attachedFile) && !isLoading ? 'var(--color-on-primary)' : 'var(--color-text-muted)',
              cursor: (input.trim() || attachedFile) && !isLoading ? 'pointer' : 'not-allowed',
              border: (input.trim() || attachedFile) && !isLoading ? 'none' : '1px solid var(--color-border)',
            }}
            title="Send Message"
          >
            <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.5">
              <line x1="22" y1="2" x2="11" y2="13"></line>
              <polygon points="22 2 15 22 11 13 2 9 22 2"></polygon>
            </svg>
          </button>
        </div>
      </div>
      <div style={styles.disclaimer}>
        Lumina AI can make mistakes. Please verify important information.
      </div>
    </div>
  );
}

const styles = {
  outerContainer: {
    width: '100%',
    maxWidth: 'var(--chat-max-width)',
    margin: '0 auto',
    padding: '0 20px 20px 20px',
  },
  promptBar: {
    display: 'flex',
    flexDirection: 'column',
    backgroundColor: 'var(--color-surface)',
    border: '1px solid var(--color-border)',
    borderRadius: 'var(--radius-lg)',
    padding: '12px 16px',
    boxShadow: '0 10px 15px -3px var(--color-shadow), 0 4px 6px -4px var(--color-shadow)',
    transition: 'all 0.2s ease',
    position: 'relative',
    gap: '12px',
  },
  inputRow: {
    display: 'flex',
    alignItems: 'flex-end',
    width: '100%',
    gap: '8px',
  },
  fileIconWrapper: {
    display: 'flex',
    alignItems: 'center',
    justifyContent: 'center',
    width: '32px',
    height: '32px',
    borderRadius: '8px',
    backgroundColor: 'var(--color-surface-container-high)',
    flexShrink: 0,
  },
  fileDetails: {
    display: 'flex',
    flexDirection: 'column',
    overflow: 'hidden',
    flex: 1,
  },
  fileName: {
    fontSize: '13px',
    fontWeight: '600',
    color: 'var(--color-text-main)',
    whiteSpace: 'nowrap',
    overflow: 'hidden',
    textOverflow: 'ellipsis',
  },
  fileSize: {
    fontSize: '11px',
    color: 'var(--color-text-muted)',
  },
  textarea: {
    flex: 1,
    border: 'none',
    backgroundColor: 'transparent',
    outline: 'none',
    resize: 'none',
    fontSize: '15px',
    lineHeight: '1.5',
    maxHeight: '200px',
    paddingRight: '12px',
    fontFamily: 'var(--font-sans)',
  },
  sendBtn: {
    width: '36px',
    height: '36px',
    borderRadius: '50%',
    display: 'flex',
    alignItems: 'center',
    justifyContent: 'center',
    transition: 'all var(--transition-fast)',
    flexShrink: 0,
    outline: 'none',
  },
  disclaimer: {
    fontSize: '11px',
    color: 'var(--color-text-muted)',
    textAlign: 'center',
    marginTop: '8px',
    userSelect: 'none',
  }
};
