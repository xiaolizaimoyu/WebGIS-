// 地点坐标库接口（手动校准的真实坐标）
import request from './request'

// 公开：全部地点坐标 [{id, name, lng, lat}]（发布选点、地图点位使用）
export const getLocations = () => request.get('/locations')

// 管理员：新增/更新地点坐标（按名称 upsert，同名覆盖）
export const adminSaveLocation = (data) => request.post('/admin/locations', data)

// 管理员：删除地点坐标
export const adminDeleteLocation = (id) => request.delete(`/admin/locations/${id}`)
