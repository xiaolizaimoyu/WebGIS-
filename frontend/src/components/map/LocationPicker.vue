<script setup>
// 地图选点组件（归属：前端 A）——发布页用于拾取经纬度
// 用法：<LocationPicker v-model="location" />，location 为 { lng, lat } | null
// 已修复：地图未初始化完成时外部传入坐标（如选择校园地点）会缓存，初始化后自动定位
import { ref, watch, onMounted, onBeforeUnmount, nextTick } from 'vue'
import L from 'leaflet'
import { initMap } from './mapUtil'

const location = defineModel({ default: null }) // { lng, lat } 或 null

const rootEl = ref(null)
let map = null
let marker = null
let pending = null // 地图未就绪时缓存的待定位坐标 [lng, lat]

function placeMarker(lng, lat) {
  if (!map) {
    pending = [Number(lng), Number(lat)]
    return
  }
  if (!marker) {
    marker = L.circleMarker([lat, lng], {
      radius: 9,
      color: '#ffffff',
      weight: 2,
      fillColor: '#1d6df0',
      fillOpacity: 0.9
    }).addTo(map)
  }
  marker.setLatLng([lat, lng])
  map.setView([lat, lng], Math.max(map.getZoom(), 16), { animate: true })
}

function clear() {
  location.value = null
  pending = null
  if (marker) { map.removeLayer(marker); marker = null }
}

// 外部（如选择校园地点/编辑回填）传入了坐标 → 打点定位
watch(location, (v) => {
  if (v && v.lng != null && v.lat != null) placeMarker(Number(v.lng), Number(v.lat))
})

onMounted(async () => {
  await nextTick()
  map = initMap(rootEl.value)
  // 地图就绪后补定位：外部选点发生在地图加载完成前的情况
  if (pending) {
    placeMarker(pending[0], pending[1])
    pending = null
  }
  map.on('click', (e) => {
    const { lat, lng } = e.latlng
    location.value = { lng: +lng.toFixed(6), lat: +lat.toFixed(6) }
    placeMarker(lng, lat)
  })
  setTimeout(() => map.invalidateSize(), 60)
})

onBeforeUnmount(() => { if (map) { map.remove(); map = null } })
</script>

<template>
  <div class="picker">
    <div ref="rootEl" class="picker-map"></div>
    <div class="picker-bar">
      <span v-if="location" class="picker-text">
        已选位置：经度 {{ location.lng }}，纬度 {{ location.lat }}
      </span>
      <span v-else class="picker-hint">选择上方地点或在地图上点击拾取位置</span>
      <el-button v-if="location" size="small" text type="danger" @click="clear">清除位置</el-button>
    </div>
  </div>
</template>

<style scoped>
.picker-map {
  width: 100%;
  height: 300px;
  border-radius: 8px;
  overflow: hidden;
  border: 1px solid #e4e7ed;
}
.picker-bar {
  display: flex;
  align-items: center;
  justify-content: space-between;
  margin-top: 8px;
}
.picker-text {
  font-size: 13px;
  color: #1d6df0;
}
.picker-hint {
  font-size: 13px;
  color: #a8abb2;
}
</style>
