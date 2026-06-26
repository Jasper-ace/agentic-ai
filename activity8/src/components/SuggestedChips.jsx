import React from 'react';

const SUGGESTIONS = [
  { id: '1', label: 'Write a python script to parse CSV data' },
  { id: '2', label: 'Draft a marketing email for a tech product' },
  { id: '3', label: 'Explain quantum computing in simple terms' },
  { id: '4', label: 'Review best practices for REST API design' },
];

export default function SuggestedChips({ onSelectChip }) {
  return (
    <div style={styles.container}>
      <div style={styles.title}>Suggested Prompts</div>
      <div style={styles.grid}>
        {SUGGESTIONS.map((s) => (
          <button
            key={s.id}
            onClick={() => onSelectChip(s.label)}
            className="chip-button"
            style={styles.chip}
          >
            <span style={styles.text}>{s.label}</span>
            <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.5" style={styles.icon}>
              <line x1="7" y1="17" x2="17" y2="7"></line>
              <polyline points="7 7 17 7 17 17"></polyline>
            </svg>
          </button>
        ))}
      </div>
    </div>
  );
}

const styles = {
  container: {
    display: 'flex',
    flexDirection: 'column',
    alignItems: 'center',
    width: '100%',
    maxWidth: '600px',
    margin: '40px auto 20px auto',
    padding: '0 20px',
  },
  title: {
    fontSize: '12px',
    fontWeight: '600',
    color: 'var(--color-text-muted)',
    textTransform: 'uppercase',
    letterSpacing: '0.05em',
    marginBottom: '16px',
    userSelect: 'none',
  },
  grid: {
    display: 'grid',
    gridTemplateColumns: 'repeat(auto-fit, minmax(260px, 1fr))',
    gap: '12px',
    width: '100%',
  },
  chip: {
    display: 'flex',
    justifyContent: 'space-between',
    alignItems: 'center',
    padding: '14px 18px',
    backgroundColor: 'var(--color-surface)',
    border: '1px solid var(--color-border)',
    borderRadius: 'var(--radius-md)',
    cursor: 'pointer',
    textAlign: 'left',
    transition: 'all 0.2s cubic-bezier(0.4, 0, 0.2, 1)',
    boxShadow: '0 2px 4px var(--color-shadow)',
    outline: 'none',
    ':hover': {
      borderColor: 'var(--color-primary)',
      transform: 'translateY(-2px)',
      boxShadow: '0 4px 8px var(--color-shadow)',
    }
  },
  text: {
    fontSize: '14px',
    color: 'var(--color-text-main)',
    fontWeight: '400',
    marginRight: '12px',
    lineHeight: '1.4',
  },
  icon: {
    color: 'var(--color-primary)',
    opacity: 0.7,
    flexShrink: 0,
  }
};
