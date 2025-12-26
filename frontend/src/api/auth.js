import request from '@/utils/request'

export function login(data) {
  return request({
    url: '/auth/login',
    method: 'post',
    data
  })
}

export function getProfile() {
  return request({
    url: '/system/admin/profile',
    method: 'get'
  })
}

export function updateProfile(data) {
  return request({
    url: '/system/admin/profile',
    method: 'put',
    data
  })
}
