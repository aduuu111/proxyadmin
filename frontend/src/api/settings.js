import request from '@/utils/request'

export function getSystemSettings() {
  return request({
    url: '/settings/',
    method: 'get'
  })
}

export function updateSystemSettings(data) {
  return request({
    url: '/settings/',
    method: 'put',
    data
  })
}

export function generateTestCredentials(protocol = 'socks5') {
  return request({
    url: '/settings/generate-credentials',
    method: 'post',
    params: { protocol }
  })
}
