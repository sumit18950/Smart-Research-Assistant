import React from 'react'

export default function ComparisonTable({ data }) {
  if (!data || data.length === 0) return null

  return (
    <div style={{ overflowX: 'auto', marginTop: 12 }}>
      <div style={{ fontSize: '0.8rem', fontWeight: 600, color: 'var(--text-secondary)', marginBottom: 8 }}>
        Source Comparison
      </div>
      <table className="comparison-table">
        <thead>
          <tr>
            <th>Source</th>
            <th>Key Point</th>
            <th>Stance</th>
          </tr>
        </thead>
        <tbody>
          {data.map((row, idx) => (
            <tr key={idx}>
              <td style={{ fontWeight: 500, color: 'var(--accent)' }}>{row.source}</td>
              <td>{row.key_point}</td>
              <td>{row.stance}</td>
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  )
}
