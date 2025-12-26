import request from '@/utils/request'

export function getRules() {
  return request({
    url: '/rules',
    method: 'get'
  })
}

export function getRule(id) {
  return request({
    url: `/rules/${id}`,
    method: 'get'
  })
}

export function createRule(data) {
  return request({
    url: '/rules',
    method: 'post',
    data
  })
}

export function updateRule(id, data) {
  return request({
    url: `/rules/${id}`,
    method: 'put',
    data
  })
}

export function deleteRule(id) {
  return request({
    url: `/rules/${id}`,
    method: 'delete'
  })
}
