import request from '@/utils/request'

export function getOutbounds() {
  return request({
    url: '/outbounds',
    method: 'get'
  })
}

export function getOutbound(id) {
  return request({
    url: `/outbounds/${id}`,
    method: 'get'
  })
}

export function createOutbound(data) {
  return request({
    url: '/outbounds',
    method: 'post',
    data
  })
}

export function updateOutbound(id, data) {
  return request({
    url: `/outbounds/${id}`,
    method: 'put',
    data
  })
}

export function deleteOutbound(id) {
  return request({
    url: `/outbounds/${id}`,
    method: 'delete'
  })
}

export function scanInterfaces() {
  return request({
    url: '/outbounds/scan',
    method: 'post'
  })
}
