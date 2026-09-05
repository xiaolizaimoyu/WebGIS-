// 校园问答接口（前端 C）——对接后端 /api/questions，后端未启动时回退 mock
import request from './request'

// 问题列表：{ keyword?, tag?, page, size } -> { total, items }
export const listQuestions = (params) => request.get('/questions', { params })

// 问题详情
export const getQuestion = (id) => request.get(`/questions/${id}`)

// 发布问题
export const createQuestion = (data) => request.post('/questions', data)

// 回答列表
export const listAnswers = (questionId) => request.get(`/questions/${questionId}/answers`)

// 发表回答
export const createAnswer = (questionId, body) => request.post(`/questions/${questionId}/answers`, { body })

// 采纳回答
export const adoptAnswer = (questionId, answerId) => request.post(`/questions/${questionId}/answers/${answerId}/adopt`)
