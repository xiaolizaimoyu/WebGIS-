// 管理员接口（前端 A 使用，对接后端 D 的 /api/admin）
import request from './request'

// 管理员登录（独立入口，普通接口会拦截管理员账号）
export const adminLogin = (data) => request.post('/admin/login', data)

// 概览统计：{ total_users, total_contents, total_comments, today_new_users, today_new_contents }
export const getStats = () => request.get('/admin/stats')

// 帖子审核列表（分页）：{ total, page, page_size, list: [...] }
export const listContents = (params) => request.get('/admin/contents', { params })

// 删除任意帖子
export const deleteContent = (id) => request.delete(`/admin/contents/${id}`)

// 用户管理列表（分页）：{ total, page, page_size, list: [...] }
export const listUsers = (params) => request.get('/admin/users', { params })

// 删除用户
export const deleteUser = (id) => request.delete(`/admin/users/${id}`)

// 删除任意评论
export const deleteComment = (id) => request.delete(`/admin/comments/${id}`)

// 订单发货管理列表（分页）：{ total, page, page_size, list: [...] }
export const listOrders = (params) => request.get('/admin/orders', { params })

// 更新订单发货状态：status = shipping | delivered | cancelled
export const updateOrderStatus = (id, status) =>
  request.patch(`/admin/orders/${id}/status`, { status })
