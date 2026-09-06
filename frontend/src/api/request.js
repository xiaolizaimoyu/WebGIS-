// axios 统一封装（归属：前端 C）
// - 所有请求自动带 Token（Authorization: Bearer xxx）
// - 统一解包：后端返回 { code, msg, data }，这里只把成功(data)交给业务代码
// - code!==0 自动弹错误提示；401 自动清理登录态并跳登录页
// - 404 不弹全局错误（扩展模块后端未实现时，业务层自行降级为 mock 数据）
//
// 注意：本文件直接读写 localStorage，不依赖 Pinia，避免模块循环引用。
import axios from 'axios'
import { ElMessage } from 'element-plus'
import { storage } from '@/utils/storage'

const request = axios.create({
  baseURL: '/api',
  timeout: 10000
})

request.interceptors.request.use((config) => {
  const token = storage.getToken()
  if (token) config.headers.Authorization = `Bearer ${token}`
  return config
})

function dealError(code, msg) {
  if (code === 401) {
    storage.clearAuth()
    ElMessage.warning('登录已过期，请重新登录')
    window.location.href = '/login'
    return
  }
  ElMessage.error(msg || '请求失败，请稍后重试')
}

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
    // 404：后端未实现的扩展模块接口，不弹全局错误，交由业务层降级为 mock
    if (status === 404) {
      return Promise.reject(error)
    }
    if (body && body.code !== undefined) {
      dealError(body.code, body.msg)
    } else if (status >= 500) {
      ElMessage.error('服务器内部错误，请稍后重试')
    } else if (status) {
      // 其他 HTTP 错误静默处理，避免频繁弹窗
      console.warn('API 请求失败:', error.config?.url, status)
    } else {
      // 网络错误（后端未启动/跨域）才提示
      ElMessage.error('网络连接失败，请确认后端服务已启动')
    }
    return Promise.reject(error)
  }
)

export default request
