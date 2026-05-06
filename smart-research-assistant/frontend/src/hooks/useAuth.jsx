import React, { createContext, useContext, useState, useEffect, useCallback } from 'react'
import { loginUser, registerUser, getMe } from '../services/api'

const AuthContext = createContext(null)

export function AuthProvider({ children }) {
  const [user, setUser] = useState(null)
  const [loading, setLoading] = useState(true)

  // On mount, check if token exists and is valid
  useEffect(() => {
    const token = localStorage.getItem('token')
    if (token) {
      getMe()
        .then(setUser)
        .catch(() => {
          localStorage.removeItem('token')
          setUser(null)
        })
        .finally(() => setLoading(false))
    } else {
      setLoading(false)
    }
  }, [])

  const login = useCallback(async (credentials) => {
    const data = await loginUser(credentials)
    localStorage.setItem('token', data.access_token)
    const me = await getMe()
    setUser(me)
    return me
  }, [])

  const register = useCallback(async (details) => {
    const newUser = await registerUser(details)
    // Auto-login after registration
    const data = await loginUser({
      username: details.username,
      password: details.password,
    })
    localStorage.setItem('token', data.access_token)
    setUser(newUser)
    return newUser
  }, [])

  const logout = useCallback(() => {
    localStorage.removeItem('token')
    setUser(null)
  }, [])

  return (
    <AuthContext.Provider value={{ user, loading, login, register, logout }}>
      {children}
    </AuthContext.Provider>
  )
}

export function useAuth() {
  const ctx = useContext(AuthContext)
  if (!ctx) throw new Error('useAuth must be used within AuthProvider')
  return ctx
}
