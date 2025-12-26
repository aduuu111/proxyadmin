import request from '@/utils/request'

export function getUsers() {
  return request({
    url: '/users',
    method: 'get'
  })
}

export function getUser(id) {
  return request({
    url: `/users/${id}`,
    method: 'get'
  })
}

export function createUser(data) {
  return request({
    url: '/users',
    method: 'post',
    data
  })
}

export function updateUser(id, data) {
  return request({
    url: `/users/${id}`,
    method: 'put',
    data
  })
}

export function deleteUser(id) {
  return request({
    url: `/users/${id}`,
    method: 'delete'
  })
}

export function resetTraffic(id) {
  return request({
    url: `/users/${id}/reset-traffic`,
    method: 'post'
  })
}

export function toggleUser(id) {
  return request({
    url: `/users/${id}/toggle`,
    method: 'post'
  })
}

export function renewUser(id, expireTime) {
  return request({
    url: `/users/${id}/renew`,
    method: 'post',
    params: { new_expire_time: expireTime }
  })
}
