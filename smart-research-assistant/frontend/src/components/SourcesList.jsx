import React from 'react'

export default function SourcesList({ sources }) {
  if (!sources || sources.length === 0) return null

  return (
    <div className="sources-list">
      <div style={{ fontSize: '0.8rem', fontWeight: 600, color: 'var(--text-secondary)', marginBottom: 4 }}>
        Sources ({sources.length})
      </div>
      {sources.map((source, idx) => (
        <div key={idx} className="source-item">
          <div className="source-title">{source.title}</div>
          <div className="source-snippet">{source.snippet}</div>
          <span className="source-score">
            Relevance: {Math.round(source.relevance_score * 100)}%
            {source.page && ` | Page ${source.page}`}
          </span>
        </div>
      ))}
    </div>
  )
}
