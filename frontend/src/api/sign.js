// 签到与积分接口（前端 C）——对接后端 /api/sign
import request from './request'

// 获取签到状态：{ signedToday, continuousDays, totalPoints, signRecords }
export const getSignStatus = () => request.get('/sign/status')

// 执行签到
export const doSign = () => request.post('/sign/do')

// 积分明细
export const getPointsLog = (params) => request.get('/sign/points-log', { params })
