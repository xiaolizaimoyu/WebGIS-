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
  // 重新从后端拉取（管理员校准坐标后刷新）
  const reload = () => {
    placeMap.value = null
    promise = null
    return useLocations()
  }
  return { placeMap, resolve, resolveContentPoint, reload }
}

// 旧地点名称 → 坐标库名称 的别名映射（旧帖子用的是长名，坐标库是简称）
const PLACE_ALIAS = {
  '图书馆': '逸夫图书馆',
  '逸夫楼': '逸夫图书馆',
  '第一食堂（一餐）': '一餐',
  '第二食堂（二餐）': '二餐',
  '第三食堂（三餐）': '三餐',
  '一号教学楼': '1教',
  '二号教学楼': '2教',
  '三号教学楼': '3教',
  '四号教学楼': '4号教学楼',
  '五号教学楼': '5号教学楼',
  '北门（新村西路）': '北门',
  '南门（淄博路）': '南门',
}

// 名称 → 真实坐标：先精确匹配，再走别名映射（找不到返回 null）
function resolve(name) {
  if (!name || !placeMap.value) return null
  if (placeMap.value[name]) return placeMap.value[name]
  const target = PLACE_ALIAS[name]
  return target ? placeMap.value[target] || null : null
}

// 校园中心（GCJ-02），仅在地点库为空时兜底使用
const MAP_CENTER = { lng: 118.007853, lat: 36.814398 }

// 帖子 → 地图坐标：
// 1) 地点名命中坐标库（含别名）→ 真实坐标；
// 2) 未录入地点名 → 从地点库中按帖子 id 确定性选取一个真实点位（不再随机散布坐标）；
// 3) 地点库为空 → 回退校园中心。
function resolveContentPoint(item) {
  if (!item) return null
  const poi = resolve(item.location_name)
  if (poi) return { lng: poi.lng, lat: poi.lat }
  const list = Object.values(placeMap.value || {})
  if (list.length) {
    const seed = ((item.id || 1) * 2654435761) >>> 0
    const pick = list[seed % list.length]
    return { lng: pick.lng, lat: pick.lat }
  }
  return { lng: MAP_CENTER.lng, lat: MAP_CENTER.lat }
}

export { promise as locationsReady }
