// 高德地图 JS API 2.0 加载器（统一管理 key / 安全密钥 / 插件加载）
// 说明：2021-12 后申请的高德 key 必须配合「安全密钥」(securityJsCode) 使用，
//       密钥在高德开放平台 → 应用管理 → 对应 key 的「设置」→ JS API 安全密钥 中查看。
export const AMAP_KEY = '942fa2831e5a2aba83cb0c30f35d0c87'
// 若页面报 INVALID_USER_SCODE，请把高德控制台的安全密钥填到这里
export const AMAP_SECURITY_CODE = ''

let amapPromise = null

export function loadAMap() {
  if (window.AMap) return Promise.resolve(window.AMap)
  if (amapPromise) return amapPromise
  amapPromise = new Promise((resolve, reject) => {
    if (AMAP_SECURITY_CODE) {
      window._AMapSecurityConfig = { securityJsCode: AMAP_SECURITY_CODE }
    }
    const script = document.createElement('script')
    script.src = `https://webapi.amap.com/maps?v=2.0&key=${AMAP_KEY}`
    script.onload = () => resolve(window.AMap)
    script.onerror = () => {
      amapPromise = null
      reject(new Error('高德地图加载失败，请检查网络或 key 配置'))
    }
    document.head.appendChild(script)
  })
  return amapPromise
}

// 异步加载插件（定位 / 逆地理编码 / POI 搜索）
export function loadAMapPlugins(plugins) {
  return loadAMap().then(
    (AMap) =>
      new Promise((resolve, reject) => {
        AMap.plugin(plugins, () => resolve(AMap))
      })
  )
}
