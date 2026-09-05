// 学习资料接口（前端 C）——对接后端 /api/materials，后端未启动时回退 mock
import request from './request'

// 资料列表：{ keyword?, subject?, page, size } -> { total, items }
export const listMaterials = (params) => request.get('/materials', { params })

// 资料详情
export const getMaterial = (id) => request.get(`/materials/${id}`)

// 上传资料（文件上传，返回资料信息）
export const uploadMaterial = (formData) => request.post('/materials/upload', formData)

// 下载资料（返回下载链接）
export const downloadMaterial = (id) => request.get(`/materials/${id}/download`)

// 点赞资料
export const likeMaterial = (id) => request.post(`/materials/${id}/like`)
