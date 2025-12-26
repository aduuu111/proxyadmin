import request from '@/utils/request'

export function getCoreConfig() {
  return request({
    url: '/core-config/current',
    method: 'get'
  })
}

export function updateCoreConfig(data) {
  return request({
    url: '/core-config/update',
    method: 'post',
    data
  })
}

export function testCoreConnection(data = null) {
  return request({
    url: '/core-config/test',
    method: 'post',
    data
  })
}
