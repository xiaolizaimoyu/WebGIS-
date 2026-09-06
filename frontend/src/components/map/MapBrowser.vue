<script setup>
// 地图浏览组件（归属：前端 A）——彩色分类点 + 点击弹窗 + 类型筛选
// 父组件传入带坐标的 points，本组件负责渲染与筛选；点“查看详情”跳帖子页。
import { ref, watch, onMounted, onBeforeUnmount, nextTick } from 'vue'
import { useRouter } from 'vue-router'
import L from 'leaflet'
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
let layer = null
let fitted = false

function normalized(item) {
  if (item.longitude == null || item.latitude == null) return null
  return { ...item, lng: Number(item.longitude), lat: Number(item.latitude) }
}

function render() {
  if (!layer) return
  layer.clearLayers()
  const show = activeType.value === 'all'
    ? props.points
    : props.points.filter((p) => p.type === activeType.value)
  let count = 0
  for (const raw of show) {
    const p = normalized(raw)
    if (!p) continue
    count++
    const marker = L.circleMarker([p.lat, p.lng], {
      radius: 8,
      color: '#ffffff',
      weight: 2,
      fillColor: colorOf(p.type),
      fillOpacity: 0.9
    }).addTo(layer)
    marker.bindPopup(buildPopupEl(p, (id) => router.push(`/content/${id}`)))
  }
  // 第一次有数据时把视野框到点位上
  if (!fitted && layer.getLayers().length) {
    fitted = true
    map.fitBounds(layer.getBounds().pad(0.2))
  }
}

watch(() => props.points, render, { deep: true })
watch(activeType, () => {
  if (map) render()
})

onMounted(async () => {
  await nextTick()
  map = initMap(rootEl.value)
  layer = L.layerGroup().addTo(map)
  // 容器尺寸稳定后再渲染一次，避免初始化时宽度为 0
  setTimeout(() => { map.invalidateSize(); render() }, 60)
})

onBeforeUnmount(() => {
  if (map) { map.remove(); map = null }
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
.map-root .leaflet-container {
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
