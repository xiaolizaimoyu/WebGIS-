// 地点坐标共享工具：全局只从后端加载一次，各页面复用
// 提供 名称→真实坐标 解析：发布选点、地图点位渲染统一走这里
import { ref } from 'vue'
import { getLocations } from '@/api/locations'

// null = 尚未加载；加载后为 { '第二食堂': {id, lng, lat}, ... }
const placeMap = ref(null)
let promise = null

export function useLocations() {
  if (placeMap.value === null) {
    promise = getLocations()
      .then((list) => {
        const m = {}
        ;(list || []).forEach((p) => {
          m[p.name] = p
        })
        placeMap.value = m
        return m
      })
      .catch(() => {
        placeMap.value = {}
      })
  }
  // 名称 → 真实坐标（找不到返回 null）
  const resolve = (name) => (name && placeMap.value ? placeMap.value[name] || null : null)
  // 重新从后端拉取（管理员校准坐标后刷新）
  const reload = () => {
    placeMap.value = null
    promise = null
    return useLocations()
  }
  return { placeMap, resolve, reload }
}

export { promise as locationsReady }
