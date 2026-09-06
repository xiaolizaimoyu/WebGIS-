// 签到与积分接口（前端 C）——对接后端 /api/points
import request from './request'

// 获取签到状态：{ signedToday, continuousDays, totalPoints, recent_records }
export const getSignStatus = () => request.get('/points/sign/status')

// 执行签到
export const doSign = () => request.post('/points/sign/do')

// 积分明细
export const getPointsLog = (params) => request.get('/points/points/log', { params })
