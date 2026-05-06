import React, { useState, useEffect } from 'react'
import { AuthProvider, useAuth } from './hooks/useAuth'
import LoginPage from './pages/LoginPage'
import RegisterPage from './pages/RegisterPage'
import UploadPage from './pages/UploadPage'
import ChatPage from './pages/ChatPage'
import EvalPage from './pages/EvalPage'
import { healthCheck } from './services/api'

const TABS = [
  { id: 'upload', label: 'Upload Documents' },
  { id: 'chat', label: 'Research Chat' },
  { id: 'eval', label: 'Evaluation' },
]

function AppContent() {
  const { user, loading: authLoading, logout } = useAuth()
  const [authView, setAuthView] = useState('login')
  const [activeTab, setActiveTab] = useState('chat')
  const [health, setHealth] = useState(null)

  useEffect(() => {
    healthCheck()
      .then(setHealth)
      .catch(() => setHealth({ status: 'unreachable' }))
  }, [])

  // Show loading spinner while checking auth
  if (authLoading) {
    return (
      <div className="auth-page">
        <div style={{ textAlign: 'center' }}>
          <div className="spinner" style={{ margin: '0 auto 16px', width: 32, height: 32 }} />
          <p style={{ color: 'var(--text-secondary)' }}>Loading...</p>
        </div>
      </div>
    )
  }

  // Show login/register if not authenticated
  if (!user) {
    return authView === 'login'
      ? <LoginPage onSwitchToRegister={() => setAuthView('register')} />
      : <RegisterPage onSwitchToLogin={() => setAuthView('login')} />
  }

  // Authenticated — show main app
  return (
    <div className="app-container">
      <header className="app-header">
        <h1>Smart Research Assistant</h1>
        <div style={{ display: 'flex', alignItems: 'center', gap: 16 }}>
          <span className="status-badge" style={{
            background: health?.status === 'healthy'
              ? 'rgba(34, 197, 94, 0.15)'
              : 'rgba(239, 68, 68, 0.15)',
            color: health?.status === 'healthy'
              ? 'var(--success)'
              : 'var(--danger)',
          }}>
            {health?.status === 'healthy'
              ? `Connected | ${health.llm_provider} | ${health.documents_loaded} docs`
              : 'Backend unavailable'}
          </span>
          <div className="user-menu">
            <span className="user-name">{user.full_name || user.username}</span>
            <button className="btn btn-secondary btn-sm" onClick={logout}>
              Sign Out
            </button>
          </div>
        </div>
      </header>

      <nav className="app-nav">
        {TABS.map(tab => (
          <button
            key={tab.id}
            className={`nav-tab ${activeTab === tab.id ? 'active' : ''}`}
            onClick={() => setActiveTab(tab.id)}
          >
            {tab.label}
          </button>
        ))}
      </nav>

      <main className="app-main">
        {activeTab === 'upload' && <UploadPage />}
        {activeTab === 'chat' && <ChatPage />}
        {activeTab === 'eval' && <EvalPage />}
      </main>
    </div>
  )
}

export default function App() {
  return (
    <AuthProvider>
      <AppContent />
    </AuthProvider>
  )
}
