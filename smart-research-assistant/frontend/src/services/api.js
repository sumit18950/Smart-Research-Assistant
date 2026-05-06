import axios from 'axios'

const API_BASE = '/api/v1'

const api = axios.create({
  baseURL: API_BASE,
  timeout: 120000, // 2 min for LLM calls
})

// Attach JWT token to every request if available
api.interceptors.request.use((config) => {
  const token = localStorage.getItem('token')
  if (token) {
    config.headers.Authorization = `Bearer ${token}`
  }
  return config
})

// ── Auth API ────────────────────────────────────────────────────

export async function registerUser({ username, email, password, fullName }) {
  const response = await api.post('/auth/register', {
    username,
    email,
    password,
    full_name: fullName || '',
  })
  return response.data
}

export async function loginUser({ username, password }) {
  const response = await api.post('/auth/login', { username, password })
  return response.data
}

export async function getMe() {
  const response = await api.get('/auth/me')
  return response.data
}

// ── Document API ────────────────────────────────────────────────

export async function uploadDocument(file) {
  const formData = new FormData()
  formData.append('file', file)
  const response = await api.post('/upload-doc', formData, {
    headers: { 'Content-Type': 'multipart/form-data' },
  })
  return response.data
}

export async function queryAssistant({ query, topK = 5, useWebSearch = false, compareSources = false }) {
  const response = await api.post('/query', {
    query,
    top_k: topK,
    use_web_search: useWebSearch,
    compare_sources: compareSources,
  })
  return response.data
}

export async function evaluateSystem(queries, groundTruths = null) {
  const response = await api.post('/evaluate', {
    queries,
    ground_truths: groundTruths,
  })
  return response.data
}

export async function healthCheck() {
  const response = await api.get('/health')
  return response.data
}
