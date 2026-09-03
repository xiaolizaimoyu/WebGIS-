// 内容与评论接口（前端 B 使用，对接后端 E 的 /api/contents）
import request from './request'

// 上传单张图片，返回 { url }
export const uploadImage = (file) => {
  const form = new FormData()
  form.append('file', file)
  // 交给 axios 自动处理 multipart 边界，不要手动设 Content-Type
  return request.post('/upload', form)
}

// 发布内容
export const createContent = (data) => request.post('/contents', data)

// 内容列表：{ type?, page, size } -> { total, items }
export const listContents = (params) => request.get('/contents', { params })

// 内容详情
export const getContent = (id) => request.get(`/contents/${id}`)

// 某内容的评论列表
export const listComments = (id) => request.get(`/contents/${id}/comments`)

// 发表评论：body 为纯文本
export const createComment = (id, body) => request.post(`/contents/${id}/comments`, { body })

// 我的发布列表：{ page, size } -> { total, items }（需登录）
export const mineContents = (params) => request.get('/contents/mine', { params })

// 编辑自己发布的内容（需登录）
export const updateContent = (id, data) => request.put(`/contents/${id}`, data)

// 删除自己发布的内容（需登录，连带删除评论）
export const deleteContent = (id) => request.delete(`/contents/${id}`)
