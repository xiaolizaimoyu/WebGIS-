// 用户认证与社交接口（前端 A 使用，对接后端 D 的 /api/user 与 /api/follows）
import request from './request'

// 登录：返回 { token, user }（需传 captcha_id + captcha_code）
export const login = (data) => request.post('/user/login', data)

// 获取登录图形验证码：返回 { captcha_id, image, expires_in }
export const getCaptcha = () => request.get('/user/captcha')

// 注册：返回用户信息
export const register = (data) => request.post('/user/register', data)

// 获取当前登录用户
export const getMe = () => request.get('/user/me')

// 更新个人资料（昵称/头像），返回新用户信息
export const updateProfile = (data) => request.put('/user/me', data)

// 修改密码 { old_password, new_password }
export const changePassword = (data) => request.put('/user/password', data)

// ===== 用户主页（用户公开信息 / 关注 / 粉丝） =====

// 按 ID 查询用户公开信息（含 content_count / comment_count）
export const getUserPublic = (id) => request.get(`/user/${id}`)

// 批量查询用户公开信息：{ ids: [] } -> { list: [...] }
export const batchUsers = (ids) => request.post('/user/batch', { ids })

// 关注 / 取消关注用户（切换），返回 { following }
export const toggleFollow = (userId) => request.post(`/social/follows/${userId}`)

// 某用户的粉丝列表（返回 id 列表）
export const getFollowers = (userId) => request.get(`/social/follows/followers/${userId}`)

// 某用户关注的人列表（返回 id 列表）
export const getFollowing = (userId) => request.get(`/social/follows/following/${userId}`)
