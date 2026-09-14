<script setup>
// 地图浏览组件（高德 JS API 2.0 版）——彩色分类点 + 点击弹窗 + 类型筛选
// 父组件传入带坐标的 points，本组件负责渲染与筛选；点「查看详情」跳帖子页。
import { ref, watch, onMounted, onBeforeUnmount, nextTick } from 'vue'
import { useRouter } from 'vue-router'
import { initMap, colorOf, buildPopupEl } from './mapUtil'
import { TYPE_MAP } from '@/api/const'

const props = defineProps({
  // 每项至少含 { id, title, type, longitude, latitude, author_name, created_at, body }
  points: { type: Array, default: () => [] }
})

const router = useRouter()
const rootEl = ref(null)
const activeType = ref('all') // 'all' 或某 type

const options = [{ value: 'all', label: '全部类型' }]
for (const [v, item] of Object.entries(TYPE_MAP)) options.push({ value: v, label: item.label })

let map = null
let AMap = null
let markers = []
let infoWindow = null
let fitted = false

function circleSvg(color) {
  return `<svg xmlns="http://www.w3.org/2000/svg" width="22" height="22" viewBox="0 0 22 22">
    <circle cx="11" cy="11" r="9" fill="${color}" fill-opacity="0.9" stroke="#ffffff" stroke-width="2"/>
  </svg>`
}

function normalized(item) {
  if (item.longitude == null || item.latitude == null) return null
  return { ...item, lng: Number(item.longitude), lat: Number(item.latitude) }
}

function render() {
  if (!map || !AMap) return
  if (markers.length) map.remove(markers)
  markers = []
  const show = activeType.value === 'all'
    ? props.points
    : props.points.filter((p) => p.type === activeType.value)
  let count = 0
  for (const raw of show) {
    const p = normalized(raw)
    if (!p) continue
    count++
    const marker = new AMap.Marker({
      position: [p.lng, p.lat],
      content: circleSvg(colorOf(p.type)),
      offset: new AMap.Pixel(-11, -11)
    })
    marker.setLabel({
      content: `<div style="font-size:11px;color:#303133;background:#fff;padding:1px 6px;border-radius:4px;border:1px solid #e4e7ed;white-space:nowrap;max-width:150px;overflow:hidden;text-overflow:ellipsis;">${p.title}</div>`,
      direction: 'top',
      offset: new AMap.Pixel(0, -6)
    })
    marker.on('click', () => {
      if (!infoWindow) infoWindow = new AMap.InfoWindow({ offset: new AMap.Pixel(0, -22) })
      infoWindow.setContent(buildPopupEl(p, (id) => router.push(`/content/${id}`)))
      infoWindow.open(map, [p.lng, p.lat])
    })
    markers.push(marker)
  }
  map.add(markers)
  if (!fitted && markers.length) {
    fitted = true
    map.setFitView(markers, false, [60, 60, 60, 60])
  }
}

watch(() => props.points, render, { deep: true })
watch(activeType, () => {
  if (map) render()
})

onMounted(async () => {
  await nextTick()
  try {
    map = await initMap(rootEl.value)
    AMap = window.AMap
    setTimeout(() => { map.resize(); render() }, 60)
  } catch (e) {
    console.error('地图初始化失败', e)
  }
})

onBeforeUnmount(() => {
  if (map) {
    map.destroy()
    map = null
  }
})

// 对外：定位到指定坐标（详情页「地图导航」跳转消费）
defineExpose({
  setCenter: (lng, lat, zoom) => {
    if (map) {
      map.setZoomAndCenter(zoom || 17, [Number(lng), Number(lat)])
      // 高亮：在目标位置叠加一个临时放大点位
      const hl = new AMap.Marker({
        position: [Number(lng), Number(lat)],
        content: circleSvg('#f56c6c'),
        offset: new AMap.Pixel(-11, -11)
      })
      map.add(hl)
      setTimeout(() => map.remove(hl), 4000)
    }
  }
})
</script>

<template>
  <div ref="rootEl" class="map-root">
    <div class="map-filter">
      <el-select v-model="activeType" size="small" style="width: 150px">
        <el-option v-for="o in options" :key="o.value" :label="o.label" :value="o.value" />
      </el-select>
    </div>
  </div>
</template>

<style>
.map-root {
  position: relative;
  width: 100%;
  height: 100%;
}
.map-root .amap-container {
  width: 100%;
  height: 100%;
}
.map-filter {
  position: absolute;
  top: 12px;
  left: 12px;
  z-index: 500; /* 高于地图控件 */
  background: #fff;
  border-radius: 8px;
  box-shadow: 0 1px 6px rgba(0, 0, 0, 0.15);
  padding: 4px 6px;
}
</style>
