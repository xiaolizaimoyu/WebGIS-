// 消息通知接口（前端 C）——对接后端 /api/notifications
import request from './request'

// 通知列表：{ unread?, page, size } -> { total, items }
export const listNotifications = (params) => request.get('/notifications', { params })

// 未读数量
export const getUnreadCount = () => request.get('/notifications/unread-count')

// 标记已读
export const markAsRead = (id) => request.post(`/notifications/${id}/read`)

// 全部标记已读
export const markAllAsRead = () => request.post('/notifications/read-all')
