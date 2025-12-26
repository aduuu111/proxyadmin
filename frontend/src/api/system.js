import request from '@/utils/request'

export function getDashboardStats() {
  return request({
    url: '/system/dashboard',
    method: 'get'
  })
}

export function downloadBackup() {
  return request({
    url: '/system/backup',
    method: 'get',
    responseType: 'blob'
  })
}

export function syncTraffic() {
  return request({
    url: '/system/sync-traffic',
    method: 'post'
  })
}

export function checkExpired() {
  return request({
    url: '/system/check-expired',
    method: 'post'
  })
}
