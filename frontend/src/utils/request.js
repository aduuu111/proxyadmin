/**
 * Axios instance with automatic token injection and error handling
 */
import axios from 'axios'
import { ElMessage } from 'element-plus'
import router from '@/router'

const request = axios.create({
  baseURL: '/api',
  timeout: 10000
})

// Request interceptor - inject token
request.interceptors.request.use(
  config => {
    const token = localStorage.getItem('token')
    if (token) {
      config.headers.Authorization = `Bearer ${token}`
    }
    return config
  },
  error => {
    console.error('Request error:', error)
    return Promise.reject(error)
  }
)

// Response interceptor - handle errors
request.interceptors.response.use(
  response => {
    return response.data
  },
  error => {
    if (error.response) {
      const { status, data } = error.response

      switch (status) {
        case 401:
          ElMessage.error('Session expired, please login again')
          localStorage.removeItem('token')
          router.push('/login')
          break
        case 403:
          ElMessage.error('Access denied')
          break
        case 404:
          ElMessage.error(data.detail || 'Resource not found')
          break
        case 500:
          ElMessage.error('Server error')
          break
        default:
          ElMessage.error(data.detail || 'Request failed')
      }
    } else {
      ElMessage.error('Network error')
    }

    return Promise.reject(error)
  }
)

export default request
