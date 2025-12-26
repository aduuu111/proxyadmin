import { defineStore } from 'pinia'
import { ref, computed } from 'vue'
import { login as loginApi } from '@/api/auth'

export const useAuthStore = defineStore('auth', () => {
  const token = ref(localStorage.getItem('token') || '')
  const username = ref(localStorage.getItem('username') || '')

  const isAuthenticated = computed(() => !!token.value)

  async function login(credentials) {
    try {
      const response = await loginApi(credentials)
      token.value = response.access_token
      username.value = credentials.username

      localStorage.setItem('token', response.access_token)
      localStorage.setItem('username', credentials.username)

      return true
    } catch (error) {
      return false
    }
  }

  function logout() {
    token.value = ''
    username.value = ''
    localStorage.removeItem('token')
    localStorage.removeItem('username')
  }

  return {
    token,
    username,
    isAuthenticated,
    login,
    logout
  }
})
