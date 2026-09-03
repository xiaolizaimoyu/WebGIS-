// 用户认证接口（前端 A 使用，对接后端 D 的 /api/user）
import request from './request'

// 登录：返回 { token, user }
export const login = (data) => request.post('/user/login', data)

// 注册：返回用户信息
export const register = (data) => request.post('/user/register', data)

// 获取当前登录用户
export const getMe = () => request.get('/user/me')

// 更新个人资料（昵称/头像），返回新用户信息
export const updateProfile = (data) => request.put('/user/me', data)

// 修改密码 { old_password, new_password }
export const changePassword = (data) => request.put('/user/password', data)
