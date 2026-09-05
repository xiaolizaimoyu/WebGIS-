// 失物招领接口（前端 C）——对接后端 /api/lost-found
import request from './request'

// 失物招领列表
export const listLostFound = (params) => request.get('/lost-found', { params })

// 详情
export const getLostFound = (id) => request.get(`/lost-found/${id}`)

// 发布（扩展表单：类型/物品名/地点/时间/联系方式/图片/描述）
export const createLostFound = (data) => request.post('/lost-found', data)
