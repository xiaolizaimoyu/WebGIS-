// 社交互动接口（点赞/收藏，对接后端 /api/social）
import request from './request'

// 点赞或取消点赞（切换），返回 { liked, like_count }
export const toggleLike = (contentId) => request.post(`/social/likes/${contentId}`)

// 检查当前用户是否点赞了某内容，返回 { liked }
export const checkLike = (contentId) => request.get(`/social/likes/check/${contentId}`)

// 收藏或取消收藏（切换），返回 { favorited }
export const toggleFavorite = (contentId) => request.post(`/social/favorites/${contentId}`)

// 检查当前用户是否收藏了某内容，返回 { favorited }
export const checkFavorite = (contentId) => request.get(`/social/favorites/check/${contentId}`)

// 我的点赞列表（返回内容详情）
export const myLikes = (params) => request.get('/social/likes/mine', { params })

// 我的收藏列表（返回内容详情）
export const myFavorites = (params) => request.get('/social/favorites/mine', { params })
