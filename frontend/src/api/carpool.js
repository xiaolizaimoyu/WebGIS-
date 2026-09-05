// 组队拼车接口（前端 C）——对接后端 /api/carpools
import request from './request'

// 拼车列表
export const listCarpools = (params) => request.get('/carpools', { params })

// 拼车详情
export const getCarpool = (id) => request.get(`/carpools/${id}`)

// 发布拼车
export const createCarpool = (data) => request.post('/carpools', data)

// 申请加入拼车
export const applyCarpool = (id, data) => request.post(`/carpools/${id}/apply`, data)

// 我的拼车报名
export const myCarpoolApplications = () => request.get('/carpools/my-applications')
