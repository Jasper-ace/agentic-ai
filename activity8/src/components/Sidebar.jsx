import React from 'react';

export default function Sidebar({
  theme,
  setTheme,
  onNewChat,
  isCollapsed,
  setIsCollapsed
}) {
  const [documents, setDocuments] = React.useState([]);
  const [isUploading, setIsUploading] = React.useState(false);
  const [isFetchingDocs, setIsFetchingDocs] = React.useState(false);
  const [errorMsg, setErrorMsg] = React.useState('');
  const fileInputRef = React.useRef(null);

  const fetchDocuments = async () => {
    setIsFetchingDocs(true);
    setErrorMsg('');
    try {
      const res = await fetch('http://localhost:5000/documents');
      if (res.ok) {
        const data = await res.json();
        setDocuments(data);
      } else {
        throw new Error('Failed to retrieve document index');
      }
    } catch (err) {
      console.warn("Could not load knowledge base documents:", err);
      setDocuments([]);
    } finally {
      setIsFetchingDocs(false);
    }
  };

  React.useEffect(() => {
    fetchDocuments();
    // Poll every 10 seconds to keep synced if changes happen elsewhere
    const interval = setInterval(fetchDocuments, 10000);
    return () => clearInterval(interval);
  }, []);

  const handleDocUploadClick = () => {
    if (fileInputRef.current) {
      fileInputRef.current.click();
    }
  };

  const handleDocFileChange = async (e) => {
    const files = e.target.files;
    if (!files || files.length === 0) return;

    setIsUploading(true);
    setErrorMsg('');
    const formData = new FormData();
    for (let i = 0; i < files.length; i++) {
      formData.append('files', files[i]);
    }

    try {
      const res = await fetch('http://localhost:5000/upload', {
        method: 'POST',
        body: formData,
      });

      if (!res.ok) {
        const errData = await res.json();
        throw new Error(errData.error || 'Failed to upload documents');
      }

      await fetchDocuments();
    } catch (err) {
      setErrorMsg(err.message);
    } finally {
      setIsUploading(false);
      e.target.value = ''; // Reset input
    }
  };

  const handleDeleteDoc = async (filename) => {
    if (!window.confirm(`Are you sure you want to delete "${filename}" from the Knowledge Base?`)) return;
    
    try {
      const res = await fetch(`http://localhost:5000/documents/${encodeURIComponent(filename)}`, {
        method: 'DELETE',
      });
      if (!res.ok) {
        const errData = await res.json();
        throw new Error(errData.error || 'Failed to delete document');
      }
      await fetchDocuments();
    } catch (err) {
      alert(`Error: ${err.message}`);
    }
  };

  const handleClearAllDocs = async () => {
    if (!window.confirm("Are you sure you want to wipe the entire Knowledge Base? This deletes all vectors from Qdrant.")) return;
    
    try {
      const res = await fetch('http://localhost:5000/documents', {
        method: 'DELETE',
      });
      if (!res.ok) {
        const errData = await res.json();
        throw new Error(errData.error || 'Failed to clear knowledge base');
      }
      await fetchDocuments();
    } catch (err) {
      alert(`Error: ${err.message}`);
    }
  };

  return (
    <aside style={{
      ...styles.sidebar,
      width: isCollapsed ? '60px' : 'var(--sidebar-width)',
      backgroundColor: 'var(--color-sidebar-bg)',
      borderRight: '1px solid var(--color-border)',
    }}>
      {/* Sidebar Header */}
      <div style={styles.header}>
        {!isCollapsed && (
          <div style={styles.logoContainer}>
            <div style={styles.logoIcon}>L</div>
            <span style={styles.logoText}>Lumina</span>
          </div>
        )}
        <button
          onClick={() => setIsCollapsed(!isCollapsed)}
          style={styles.collapseBtn}
          title={isCollapsed ? "Expand Sidebar" : "Collapse Sidebar"}
        >
          <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
            {isCollapsed ? (
              <path d="M9 18l6-6-6-6"></path>
            ) : (
              <path d="M15 19l-7-7 7-7"></path>
            )}
          </svg>
        </button>
      </div>

      {/* New Chat Button */}
      <div style={styles.actionContainer}>
        <button 
          onClick={onNewChat} 
          style={{
            ...styles.newChatBtn,
            padding: isCollapsed ? '10px' : '12px 16px',
            justifyContent: isCollapsed ? 'center' : 'flex-start'
          }}
          title="Clear Conversation"
        >
          <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
            <line x1="12" y1="5" x2="12" y2="19"></line>
            <line x1="5" y1="12" x2="19" y2="12"></line>
          </svg>
          {!isCollapsed && <span style={styles.newChatText}>Clear chat</span>}
        </button>
      </div>

      {/* Knowledge Base Manager Section */}
      {!isCollapsed ? (
        <div style={styles.kbContainer}>
          <div style={styles.kbHeader}>
            <div style={styles.kbTitleGroup}>
              <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.5" style={{ color: 'var(--color-primary)' }}>
                <rect x="2" y="2" width="20" height="8" rx="2" ry="2"></rect>
                <rect x="2" y="14" width="20" height="8" rx="2" ry="2"></rect>
                <line x1="6" y1="6" x2="6.01" y2="6"></line>
                <line x1="6" y1="18" x2="6.01" y2="18"></line>
              </svg>
              <h3 style={styles.kbTitle}>Knowledge Base</h3>
            </div>
            {documents.length > 0 && (
              <button 
                onClick={handleClearAllDocs}
                style={styles.clearAllBtn}
                title="Wipe Database"
              >
                Clear All
              </button>
            )}
          </div>

          <div style={styles.kbContent}>
            <button 
              onClick={handleDocUploadClick}
              disabled={isUploading}
              style={styles.kbUploadBtn}
              className="kb-upload-btn"
            >
              {isUploading ? (
                <>
                  <div className="typing-dot" style={{ width: '6px', height: '6px', margin: 0 }}></div>
                  <span>Indexing...</span>
                </>
              ) : (
                <>
                  <svg width="12" height="12" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.5">
                    <path d="M21 15v4a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2v-4"></path>
                    <polyline points="17 8 12 3 7 8"></polyline>
                    <line x1="12" y1="3" x2="12" y2="15"></line>
                  </svg>
                  <span>Upload Documents</span>
                </>
              )}
            </button>
            <input 
              type="file" 
              ref={fileInputRef}
              onChange={handleDocFileChange}
              accept=".txt"
              multiple
              style={{ display: 'none' }}
            />

            {errorMsg && (
              <div style={styles.kbError}>{errorMsg}</div>
            )}

            <div style={styles.kbFileList}>
              {isFetchingDocs && documents.length === 0 ? (
                <div style={styles.kbEmptyState}>
                  Loading database...
                </div>
              ) : documents.length === 0 ? (
                <div style={styles.kbEmptyState}>
                  No documents indexed. Upload text files to build context.
                </div>
              ) : (
                documents.map((doc) => (
                  <div key={doc.filename} className="kb-file-item" style={styles.kbFileItem}>
                    <div style={styles.kbFileDetails}>
                      <span style={styles.kbFileName} title={doc.filename}>{doc.filename}</span>
                      <span style={styles.kbFileChunks}>{doc.chunks} vector chunks</span>
                    </div>
                    <button 
                      onClick={() => handleDeleteDoc(doc.filename)}
                      className="kb-file-delete-btn"
                      style={styles.kbFileDeleteBtn}
                      title="Delete file"
                    >
                      <svg width="12" height="12" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
                        <polyline points="3 6 5 6 21 6"></polyline>
                        <path d="M19 6v14a2 2 0 0 1-2 2H7a2 2 0 0 1-2-2V6m3 0V4a2 2 0 0 1 2-2h4a2 2 0 0 1 2 2v2"></path>
                      </svg>
                    </button>
                  </div>
                ))
              )}
            </div>
          </div>
        </div>
      ) : (
        <div style={styles.kbCollapsedIconContainer}>
          <button 
            onClick={handleDocUploadClick}
            disabled={isUploading}
            style={styles.kbCollapsedUploadBtn}
            title="Upload Documents to KB"
            className="kb-collapsed-upload-btn"
          >
            <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.5">
              <rect x="2" y="2" width="20" height="8" rx="2" ry="2"></rect>
              <rect x="2" y="14" width="20" height="8" rx="2" ry="2"></rect>
              <line x1="6" y1="6" x2="6.01" y2="6"></line>
              <line x1="6" y1="18" x2="6.01" y2="18"></line>
            </svg>
          </button>
          <input 
            type="file" 
            ref={fileInputRef}
            onChange={handleDocFileChange}
            accept=".txt"
            multiple
            style={{ display: 'none' }}
          />
        </div>
      )}

      {/* Content Spacer */}
      <div style={styles.content} />

      {/* Footer: User & Controls */}
      <div style={{
        ...styles.footer,
        flexDirection: isCollapsed ? 'column' : 'row',
        alignItems: 'center',
        gap: '12px'
      }}>
        {/* Theme Toggle */}
        <button
          onClick={() => setTheme(theme === 'light' ? 'dark' : 'light')}
          style={styles.themeToggleBtn}
          title={theme === 'light' ? 'Switch to Dark Mode' : 'Switch to Light Mode'}
        >
          {theme === 'light' ? (
            <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
              <path d="M21 12.79A9 9 0 1 1 11.21 3 7 7 0 0 0 21 12.79z"></path>
            </svg>
          ) : (
            <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
              <circle cx="12" cy="12" r="5"></circle>
              <line x1="12" y1="1" x2="12" y2="3"></line>
              <line x1="12" y1="21" x2="12" y2="23"></line>
              <line x1="4.22" y1="4.22" x2="5.64" y2="5.64"></line>
              <line x1="18.36" y1="18.36" x2="19.78" y2="19.78"></line>
              <line x1="1" y1="12" x2="3" y2="12"></line>
              <line x1="21" y1="12" x2="23" y2="12"></line>
              <line x1="4.22" y1="19.78" x2="5.64" y2="18.36"></line>
              <line x1="18.36" y1="5.64" x2="19.78" y2="4.22"></line>
            </svg>
          )}
        </button>

        {/* User Profile / Status */}
        {!isCollapsed ? (
          <div style={styles.userSection}>
            <div style={styles.avatar}>U</div>
            <div style={styles.userInfo}>
              <div style={styles.username}>Local User</div>
              <div style={styles.userEmail}>local@lumina.ai</div>
            </div>
          </div>
        ) : (
          <div 
            style={styles.avatarCollapsed}
            title="Local User"
          >
            U
          </div>
        )}
      </div>
    </aside>
  );
}

const styles = {
  sidebar: {
    display: 'flex',
    flexDirection: 'column',
    height: '100%',
    transition: 'width var(--transition-normal)',
    flexShrink: 0,
    zIndex: 10,
  },
  header: {
    display: 'flex',
    justifyContent: 'space-between',
    alignItems: 'center',
    padding: '20px 16px',
    height: '70px',
  },
  logoContainer: {
    display: 'flex',
    alignItems: 'center',
    gap: '10px',
  },
  logoIcon: {
    width: '32px',
    height: '32px',
    borderRadius: '8px',
    backgroundColor: 'var(--color-primary)',
    color: '#fff',
    display: 'flex',
    alignItems: 'center',
    justifyContent: 'center',
    fontWeight: 'bold',
    fontSize: '18px',
  },
  logoText: {
    fontSize: '18px',
    fontWeight: '600',
    color: 'var(--color-text-main)',
  },
  collapseBtn: {
    backgroundColor: 'transparent',
    border: 'none',
    color: 'var(--color-text-muted)',
    cursor: 'pointer',
    padding: '6px',
    borderRadius: '4px',
    display: 'flex',
    alignItems: 'center',
    justifyContent: 'center',
    transition: 'background-color var(--transition-fast)',
  },
  actionContainer: {
    padding: '0 12px 16px 12px',
  },
  newChatBtn: {
    width: '100%',
    display: 'flex',
    alignItems: 'center',
    gap: '12px',
    backgroundColor: 'var(--color-background)',
    color: 'var(--color-text-main)',
    border: '1px solid var(--color-border)',
    borderRadius: 'var(--radius-md)',
    cursor: 'pointer',
    transition: 'all var(--transition-fast)',
    fontSize: '14px',
    fontWeight: '500',
  },
  newChatText: {
    overflow: 'hidden',
    textOverflow: 'ellipsis',
    whiteSpace: 'nowrap',
  },
  content: {
    flex: 1,
  },
  footer: {
    padding: '16px 12px',
    borderTop: '1px solid var(--color-border)',
    display: 'flex',
    justifyContent: 'space-between',
  },
  themeToggleBtn: {
    backgroundColor: 'transparent',
    border: 'none',
    color: 'var(--color-text-muted)',
    cursor: 'pointer',
    width: '40px',
    height: '40px',
    borderRadius: '50%',
    display: 'flex',
    alignItems: 'center',
    justifyContent: 'center',
    transition: 'all 0.2s',
  },
  userSection: {
    flex: 1,
    display: 'flex',
    alignItems: 'center',
    gap: '10px',
    marginLeft: '4px',
    overflow: 'hidden',
  },
  avatar: {
    width: '32px',
    height: '32px',
    borderRadius: '50%',
    backgroundColor: 'var(--color-primary-container)',
    color: 'var(--color-primary)',
    display: 'flex',
    alignItems: 'center',
    justifyContent: 'center',
    fontWeight: 'bold',
    fontSize: '14px',
    flexShrink: 0,
    boxShadow: '0 2px 4px rgba(0, 104, 95, 0.1)',
  },
  avatarCollapsed: {
    width: '32px',
    height: '32px',
    borderRadius: '50%',
    backgroundColor: 'var(--color-primary-container)',
    color: 'var(--color-primary)',
    display: 'flex',
    alignItems: 'center',
    justifyContent: 'center',
    fontWeight: 'bold',
    fontSize: '14px',
  },
  userInfo: {
    flex: 1,
    overflow: 'hidden',
  },
  username: {
    fontSize: '13px',
    fontWeight: '500',
    color: 'var(--color-text-main)',
    whiteSpace: 'nowrap',
    overflow: 'hidden',
    textOverflow: 'ellipsis',
  },
  userEmail: {
    fontSize: '11px',
    color: 'var(--color-text-muted)',
    whiteSpace: 'nowrap',
    overflow: 'hidden',
    textOverflow: 'ellipsis',
  },
  kbContainer: {
    padding: '0 16px 16px 16px',
    display: 'flex',
    flexDirection: 'column',
    overflow: 'hidden',
    maxHeight: 'calc(100vh - 280px)',
  },
  kbHeader: {
    display: 'flex',
    justifyContent: 'space-between',
    alignItems: 'center',
    marginBottom: '10px',
  },
  kbTitleGroup: {
    display: 'flex',
    alignItems: 'center',
    gap: '8px',
    color: 'var(--color-text-main)',
  },
  kbTitle: {
    fontSize: '11px',
    fontWeight: '600',
    textTransform: 'uppercase',
    letterSpacing: '0.05em',
  },
  clearAllBtn: {
    backgroundColor: 'transparent',
    border: 'none',
    color: '#ef4444',
    cursor: 'pointer',
    fontSize: '11px',
    fontWeight: '500',
    outline: 'none',
  },
  kbContent: {
    display: 'flex',
    flexDirection: 'column',
    gap: '10px',
  },
  kbUploadBtn: {
    display: 'flex',
    alignItems: 'center',
    justifyContent: 'center',
    gap: '8px',
    padding: '8px 12px',
    backgroundColor: 'var(--color-surface)',
    border: '1px dashed var(--color-border)',
    borderRadius: 'var(--radius-md)',
    color: 'var(--color-text-main)',
    cursor: 'pointer',
    fontSize: '12px',
    fontWeight: '500',
    transition: 'all var(--transition-fast)',
    outline: 'none',
  },
  kbError: {
    fontSize: '11px',
    color: '#ef4444',
    padding: '4px 8px',
    backgroundColor: 'rgba(239, 68, 68, 0.08)',
    borderRadius: '4px',
  },
  kbFileList: {
    display: 'flex',
    flexDirection: 'column',
    gap: '6px',
    overflowY: 'auto',
    maxHeight: '180px',
    paddingRight: '4px',
  },
  kbEmptyState: {
    fontSize: '11px',
    color: 'var(--color-text-muted)',
    textAlign: 'center',
    padding: '16px 10px',
    border: '1px solid var(--color-border)',
    borderRadius: 'var(--radius-md)',
    backgroundColor: 'var(--color-background)',
  },
  kbFileItem: {
    display: 'flex',
    alignItems: 'center',
    justifyContent: 'space-between',
    padding: '8px 10px',
    backgroundColor: 'var(--color-background)',
    border: '1px solid var(--color-border)',
    borderRadius: 'var(--radius-md)',
    gap: '8px',
  },
  kbFileDetails: {
    display: 'flex',
    flexDirection: 'column',
    overflow: 'hidden',
    flex: 1,
  },
  kbFileName: {
    fontSize: '12px',
    fontWeight: '500',
    color: 'var(--color-text-main)',
    whiteSpace: 'nowrap',
    overflow: 'hidden',
    textOverflow: 'ellipsis',
  },
  kbFileChunks: {
    fontSize: '10px',
    color: 'var(--color-text-muted)',
  },
  kbFileDeleteBtn: {
    backgroundColor: 'transparent',
    border: 'none',
    color: 'var(--color-text-muted)',
    cursor: 'pointer',
    padding: '4px',
    borderRadius: '4px',
    display: 'flex',
    alignItems: 'center',
    justifyContent: 'center',
    transition: 'all var(--transition-fast)',
    outline: 'none',
  },
  kbCollapsedIconContainer: {
    display: 'flex',
    justifyContent: 'center',
    padding: '12px 0',
  },
  kbCollapsedUploadBtn: {
    width: '40px',
    height: '40px',
    borderRadius: '50%',
    backgroundColor: 'transparent',
    border: 'none',
    color: 'var(--color-text-muted)',
    cursor: 'pointer',
    display: 'flex',
    alignItems: 'center',
    justifyContent: 'center',
    transition: 'all var(--transition-fast)',
    outline: 'none',
  }
};
