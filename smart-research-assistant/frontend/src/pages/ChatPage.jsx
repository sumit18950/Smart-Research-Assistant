import React, { useState, useRef, useEffect } from 'react'
import ReactMarkdown from 'react-markdown'
import { queryAssistant } from '../services/api'
import { useApi } from '../hooks/useApi'
import ConfidenceIndicator from '../components/ConfidenceIndicator'
import SourcesList from '../components/SourcesList'
import ComparisonTable from '../components/ComparisonTable'

export default function ChatPage() {
  const [messages, setMessages] = useState([])
  const [input, setInput] = useState('')
  const [useWebSearch, setUseWebSearch] = useState(false)
  const [compareSources, setCompareSources] = useState(false)
  const messagesEndRef = useRef(null)
  const { loading, execute } = useApi(queryAssistant)

  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' })
  }, [messages])

  const handleSubmit = async (e) => {
    e.preventDefault()
    if (!input.trim() || loading) return

    const userQuery = input.trim()
    setInput('')

    // Add user message
    setMessages(prev => [...prev, { role: 'user', content: userQuery }])

    try {
      const response = await execute({
        query: userQuery,
        topK: 5,
        useWebSearch,
        compareSources,
      })

      setMessages(prev => [...prev, {
        role: 'assistant',
        content: response.answer,
        sources: response.sources,
        confidence: response.confidence_score,
        comparison: response.comparison_table,
        strategy: response.strategy_used,
        tokenUsage: response.token_usage,
      }])
    } catch (err) {
      setMessages(prev => [...prev, {
        role: 'assistant',
        content: 'Sorry, I encountered an error processing your query. Please try again.',
        confidence: 0,
        sources: [],
      }])
    }
  }

  const getStrategyLabel = (strategy) => {
    const map = {
      rag: 'RAG Search',
      rag_compare: 'Comparison',
      web_search: 'Web Search',
      summarize: 'Summary',
      blocked: 'Blocked',
      error: 'Error',
    }
    return map[strategy] || strategy
  }

  const getStrategyClass = (strategy) => {
    if (strategy?.includes('web')) return 'web'
    if (strategy?.includes('compare')) return 'compare'
    if (strategy?.includes('summar')) return 'summarize'
    return 'rag'
  }

  return (
    <div className="chat-container">
      <div className="chat-messages">
        {messages.length === 0 && (
          <div style={{ textAlign: 'center', padding: '60px 20px', color: 'var(--text-muted)' }}>
            <svg width="48" height="48" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.5" style={{ margin: '0 auto 16px', display: 'block' }}>
              <path d="M21 15a2 2 0 0 1-2 2H7l-4 4V5a2 2 0 0 1 2-2h14a2 2 0 0 1 2 2z" />
            </svg>
            <p style={{ fontSize: '1rem', fontWeight: 500, marginBottom: 8 }}>Ask your research question</p>
            <p style={{ fontSize: '0.85rem' }}>
              Upload documents first, then ask questions. The AI will search your documents,
              cite sources, and provide confidence scores.
            </p>
          </div>
        )}

        {messages.map((msg, idx) => (
          <div key={idx} className={`message ${msg.role}`}>
            <div className="message-avatar">
              {msg.role === 'user' ? 'U' : 'AI'}
            </div>
            <div style={{ maxWidth: '80%' }}>
              <div className="message-content">
                {msg.role === 'assistant' ? (
                  <ReactMarkdown>{msg.content}</ReactMarkdown>
                ) : (
                  msg.content
                )}
              </div>

              {msg.role === 'assistant' && (
                <div style={{ marginTop: 8 }}>
                  <div style={{ display: 'flex', alignItems: 'center', gap: 8, marginBottom: 4 }}>
                    {msg.strategy && (
                      <span className={`strategy-badge ${getStrategyClass(msg.strategy)}`}>
                        {getStrategyLabel(msg.strategy)}
                      </span>
                    )}
                    {msg.tokenUsage && (
                      <span style={{ fontSize: '0.7rem', color: 'var(--text-muted)' }}>
                        {msg.tokenUsage.total_tokens} tokens
                      </span>
                    )}
                  </div>

                  {msg.confidence !== undefined && (
                    <ConfidenceIndicator score={msg.confidence} />
                  )}

                  <SourcesList sources={msg.sources} />

                  {msg.comparison && <ComparisonTable data={msg.comparison} />}
                </div>
              )}
            </div>
          </div>
        ))}

        {loading && (
          <div className="message assistant">
            <div className="message-avatar">AI</div>
            <div className="message-content" style={{ display: 'flex', alignItems: 'center', gap: 8 }}>
              <div className="spinner" />
              <span>Researching<span className="loading-dots"></span></span>
            </div>
          </div>
        )}

        <div ref={messagesEndRef} />
      </div>

      <div className="chat-options">
        <label className="checkbox-label">
          <input
            type="checkbox"
            checked={useWebSearch}
            onChange={(e) => setUseWebSearch(e.target.checked)}
          />
          Include web search
        </label>
        <label className="checkbox-label">
          <input
            type="checkbox"
            checked={compareSources}
            onChange={(e) => setCompareSources(e.target.checked)}
          />
          Compare sources
        </label>
      </div>

      <form onSubmit={handleSubmit} className="chat-input-area">
        <input
          type="text"
          className="input"
          value={input}
          onChange={(e) => setInput(e.target.value)}
          placeholder="Ask a research question..."
          disabled={loading}
        />
        <button type="submit" className="btn btn-primary" disabled={loading || !input.trim()}>
          {loading ? <div className="spinner" /> : 'Send'}
        </button>
      </form>
    </div>
  )
}
