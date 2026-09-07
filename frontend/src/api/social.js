// 互动接口（归属：前端 B）——点赞 / 收藏，对接后端 F 的 /api/social
import request from './request'

// 点赞/取消点赞（切换），需登录 -> { liked, like_count }
export const toggleLike = (contentId) => request.post(`/social/likes/${contentId}`)

// 检查当前用户是否已点赞 -> { liked }
export const checkLike = (contentId) => request.get(`/social/likes/check/${contentId}`)

// 收藏/取消收藏（切换），需登录 -> { favorited }
export const toggleFavorite = (contentId) => request.post(`/social/favorites/${contentId}`)

// 检查当前用户是否已收藏 -> { favorited }
export const checkFavorite = (contentId) => request.get(`/social/favorites/check/${contentId}`)
