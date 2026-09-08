// axios 统一封装（归属：前端 C）
// - 所有请求自动带 Token（Authorization: Bearer xxx）
// - 统一解包：后端返回 { code, msg, data }，这里只把成功(data)交给业务代码
// - code!==0 自动弹错误提示；401 自动清理登录态并跳登录页
//
// 注意：本文件直接读写 localStorage，不依赖 Pinia，避免模块循环引用。
import axios from 'axios'
import { ElMessage } from 'element-plus'

const TOKEN_KEY = 'campus_token'

const request = axios.create({
  baseURL: '/api', // 开发期由 vite 代理到后端 8000
  timeout: 10000
})

// 请求拦截：注入 Token
request.interceptors.request.use((config) => {
  const token = localStorage.getItem(TOKEN_KEY)
  if (token) config.headers.Authorization = `Bearer ${token}`
  return config
})

// 处理非 0 的业务错误码
function dealError(code, msg) {
  if (code === 401) {
    localStorage.removeItem(TOKEN_KEY)
    localStorage.removeItem('campus_user')
    ElMessage.warning('登录已过期，请重新登录')
    // 整页跳转登录，保证内存状态一并清空
    window.location.href = '/login'
    return
  }
  ElMessage.error(msg || '请求失败，请稍后重试')
}

// 响应拦截：成功且 code=0 时只返回 data，其余弹错并 reject
request.interceptors.response.use(
  (response) => {
    const body = response.data
    if (body && body.code === 0) return body.data
    if (body) dealError(body.code, body.msg)
    return Promise.reject(new Error(body?.msg || '请求失败'))
  },
  (error) => {
    const status = error.response?.status
    const body = error.response?.data
    // 404：后端接口尚未实现（新模块待后端对接），不弹全局错误，由各页面 catch 后使用 mock 数据兜底
    if (status === 404) {
      return Promise.reject(error)
    }
    if (body && body.code !== undefined) {
      dealError(body.code, body.msg)
    } else if (error.code === 'ERR_NETWORK' || !error.response) {
      // 真正的网络错误（后端未启动）才提示
      ElMessage.error('网络连接失败，请确认后端服务已启动')
    }
    return Promise.reject(error)
  }
)

export default request
