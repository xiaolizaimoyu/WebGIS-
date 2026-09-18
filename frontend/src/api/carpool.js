// 组队拼车接口（前端 C）——对接后端 /api/carpools（carpools 表，完整 CRUD + 申请流程）
import request from './request'

// 拼车列表
export const listCarpools = (params) => request.get('/carpools', { params })

// 拼车详情
export const getCarpool = (id) => request.get(`/carpools/${id}`)

// 发布拼车
export const createCarpool = (data) => request.post('/carpools', data)

// 编辑拼车（仅作者）
export const updateCarpool = (id, data) => request.put(`/carpools/${id}`, data)

// 删除拼车（仅作者）
export const deleteCarpool = (id) => request.delete(`/carpools/${id}`)

// 申请加入拼车（提交后待车主确认，不直接扣座位）
export const applyCarpool = (id, data) => request.post(`/carpools/${id}/apply`, data)

// 我的拼车申请列表
export const myCarpoolApplications = (params) => request.get('/carpools/my-applications', { params })

// 车主：查看某拼车的申请列表
export const listApplications = (id) => request.get(`/carpools/${id}/applications`)

// 车主：同意申请（扣座位）
export const approveApplication = (cid, aid) => request.post(`/carpools/${cid}/applications/${aid}/approve`)

// 车主：拒绝申请
export const rejectApplication = (cid, aid) => request.post(`/carpools/${cid}/applications/${aid}/reject`)

// 申请人：取消申请 / 退出拼车（已加入后可退出并释放座位）
export const cancelApplication = (cid, aid) => request.post(`/carpools/${cid}/applications/${aid}/cancel`)

// 车主：移除已加入成员
export const removeMember = (cid, aid) => request.post(`/carpools/${cid}/applications/${aid}/remove`)

// 拼车聊天：获取消息列表
export const listMessages = (cid) => request.get(`/carpools/${cid}/messages`)

// 拼车聊天：发送消息
export const sendMessage = (cid, content) => request.post(`/carpools/${cid}/messages`, { content })
