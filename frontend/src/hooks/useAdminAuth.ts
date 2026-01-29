/** Hook for admin authentication */
import { useState, useEffect } from 'react'

const AUTH_TOKEN_KEY = 'admin_auth_token'
const AUTH_TIME_KEY = 'admin_auth_time'
const AUTH_EXPIRY_HOURS = 24

export function useAdminAuth() {
  const [isAuthenticated, setIsAuthenticated] = useState(false)
  const [isChecking, setIsChecking] = useState(true)

  useEffect(() => {
    checkAuth()
  }, [])

  const checkAuth = async () => {
    const token = localStorage.getItem(AUTH_TOKEN_KEY)
    const authTime = localStorage.getItem(AUTH_TIME_KEY)

    if (!token || !authTime) {
      setIsAuthenticated(false)
      setIsChecking(false)
      return
    }

    // Check if token is expired (24 hours)
    const timeElapsed = Date.now() - parseInt(authTime)
    const hoursElapsed = timeElapsed / (1000 * 60 * 60)

    if (hoursElapsed > AUTH_EXPIRY_HOURS) {
      // Token expired
      localStorage.removeItem(AUTH_TOKEN_KEY)
      localStorage.removeItem(AUTH_TIME_KEY)
      setIsAuthenticated(false)
      setIsChecking(false)
      return
    }

    // Verify token with backend
    try {
      const response = await fetch(`${import.meta.env.VITE_API_URL || 'http://localhost:8000'}/api/admin/auth/verify?token=${token}`)
      if (response.ok) {
        setIsAuthenticated(true)
      } else {
        // Token invalid
        localStorage.removeItem(AUTH_TOKEN_KEY)
        localStorage.removeItem(AUTH_TIME_KEY)
        setIsAuthenticated(false)
      }
    } catch (error) {
      // Network error - assume valid if token exists and not expired
      setIsAuthenticated(true)
    } finally {
      setIsChecking(false)
    }
  }

  const logout = () => {
    localStorage.removeItem(AUTH_TOKEN_KEY)
    localStorage.removeItem(AUTH_TIME_KEY)
    setIsAuthenticated(false)
  }

  return {
    isAuthenticated,
    isChecking,
    checkAuth,
    logout,
  }
}
