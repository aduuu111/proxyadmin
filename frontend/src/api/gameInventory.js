import request from '@/utils/request'

export function getAllGameInventories() {
  return request({
    url: '/game-inventory/',
    method: 'get'
  })
}

export function getGameInventory(ruleId) {
  return request({
    url: `/game-inventory/${ruleId}`,
    method: 'get'
  })
}

export function getOutboundUsage(outboundId) {
  return request({
    url: `/game-inventory/outbound/${outboundId}/usage`,
    method: 'get'
  })
}
