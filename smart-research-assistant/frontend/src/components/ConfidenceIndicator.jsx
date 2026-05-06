import React from 'react'

export default function ConfidenceIndicator({ score }) {
  const safeScore = Math.max(0, Math.min(1, score || 0))
  const percent = Math.round(safeScore * 100)
  const level = safeScore >= 0.7 ? 'high' : safeScore >= 0.4 ? 'medium' : 'low'
  const label = safeScore >= 0.7 ? 'High' : safeScore >= 0.4 ? 'Medium' : 'Low'

  return (
    <div className="confidence-bar">
      <span className="confidence-label" style={{ color: `var(--${level === 'high' ? 'success' : level === 'medium' ? 'warning' : 'danger'})` }}>
        {label} confidence: {percent}%
      </span>
      <div className="confidence-track">
        <div
          className={`confidence-fill ${level}`}
          style={{ width: `${percent}%` }}
        />
      </div>
    </div>
  )
}
