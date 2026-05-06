import React, { useState } from 'react'
import { evaluateSystem } from '../services/api'
import { useApi } from '../hooks/useApi'

export default function EvalPage() {
  const [queriesText, setQueriesText] = useState('')
  const [groundTruthsText, setGroundTruthsText] = useState('')
  const { data: result, loading, error, execute } = useApi(evaluateSystem)

  const handleEvaluate = async () => {
    const queries = queriesText.split('\n').map(q => q.trim()).filter(Boolean)
    if (queries.length === 0) return

    const groundTruths = groundTruthsText.trim()
      ? groundTruthsText.split('\n').map(g => g.trim()).filter(Boolean)
      : null

    await execute(queries, groundTruths)
  }

  const getScoreColor = (score) => {
    if (score >= 0.7) return 'var(--success)'
    if (score >= 0.4) return 'var(--warning)'
    return 'var(--danger)'
  }

  return (
    <div>
      <div className="card">
        <h2 className="card-title">RAGAS Evaluation</h2>
        <p style={{ color: 'var(--text-secondary)', fontSize: '0.875rem', marginBottom: 16 }}>
          Evaluate your RAG pipeline quality using RAGAS metrics.
          Enter one query per line. Optionally provide ground truth answers (one per line, matching query order).
        </p>

        <div style={{ marginBottom: 16 }}>
          <label style={{ display: 'block', fontSize: '0.8rem', fontWeight: 500, marginBottom: 6, color: 'var(--text-secondary)' }}>
            Test Queries (one per line)
          </label>
          <textarea
            className="input"
            rows={5}
            value={queriesText}
            onChange={(e) => setQueriesText(e.target.value)}
            placeholder={"What are the main findings of the study?\nHow does method A compare to method B?\nWhat limitations were identified?"}
          />
        </div>

        <div style={{ marginBottom: 16 }}>
          <label style={{ display: 'block', fontSize: '0.8rem', fontWeight: 500, marginBottom: 6, color: 'var(--text-secondary)' }}>
            Ground Truth Answers (optional, one per line)
          </label>
          <textarea
            className="input"
            rows={5}
            value={groundTruthsText}
            onChange={(e) => setGroundTruthsText(e.target.value)}
            placeholder="Leave empty to skip context_recall metric"
          />
        </div>

        <button
          className="btn btn-primary"
          onClick={handleEvaluate}
          disabled={loading || !queriesText.trim()}
        >
          {loading ? (
            <>
              <div className="spinner" />
              Running Evaluation...
            </>
          ) : (
            'Run Evaluation'
          )}
        </button>

        {error && (
          <div style={{ color: 'var(--danger)', fontSize: '0.85rem', marginTop: 12 }}>
            Error: {error}
          </div>
        )}
      </div>

      {result && (
        <>
          <div className="card">
            <h2 className="card-title">Overall Scores</h2>
            <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(180px, 1fr))', gap: 16 }}>
              {[
                { label: 'Overall', value: result.overall_score },
                { label: 'Faithfulness', value: result.faithfulness },
                { label: 'Answer Relevancy', value: result.answer_relevancy },
                { label: 'Context Precision', value: result.context_precision },
                ...(result.context_recall != null
                  ? [{ label: 'Context Recall', value: result.context_recall }]
                  : []),
              ].map((metric) => (
                <div
                  key={metric.label}
                  style={{
                    background: 'var(--bg-input)',
                    borderRadius: 'var(--radius)',
                    padding: 16,
                    textAlign: 'center',
                  }}
                >
                  <div style={{ fontSize: '0.75rem', color: 'var(--text-muted)', marginBottom: 8 }}>
                    {metric.label}
                  </div>
                  <div style={{ fontSize: '1.75rem', fontWeight: 700, color: getScoreColor(metric.value) }}>
                    {(metric.value * 100).toFixed(1)}%
                  </div>
                </div>
              ))}
            </div>
          </div>

          {result.per_query_scores && result.per_query_scores.length > 0 && (
            <div className="card">
              <h2 className="card-title">Per-Query Results</h2>
              <div style={{ overflowX: 'auto' }}>
                <table className="comparison-table">
                  <thead>
                    <tr>
                      <th>Query</th>
                      <th>Faithfulness</th>
                      <th>Relevancy</th>
                      <th>Precision</th>
                    </tr>
                  </thead>
                  <tbody>
                    {result.per_query_scores.map((row, idx) => (
                      <tr key={idx}>
                        <td style={{ maxWidth: 300, overflow: 'hidden', textOverflow: 'ellipsis' }}>
                          {row.question}
                        </td>
                        <td style={{ color: getScoreColor(row.faithfulness) }}>
                          {(row.faithfulness * 100).toFixed(1)}%
                        </td>
                        <td style={{ color: getScoreColor(row.answer_relevancy) }}>
                          {(row.answer_relevancy * 100).toFixed(1)}%
                        </td>
                        <td style={{ color: getScoreColor(row.context_precision) }}>
                          {(row.context_precision * 100).toFixed(1)}%
                        </td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            </div>
          )}
        </>
      )}
    </div>
  )
}
