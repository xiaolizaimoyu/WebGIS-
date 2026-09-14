<script setup>
// 地图选点组件（高德 JS API 2.0 版）——发布页用于拾取经纬度
// 用法：<LocationPicker v-model="location" />，location 为 { lng, lat } | null
// 新增：右上角定位按钮（AMap.Geolocation 浏览器定位，精准拾取当前所在位置）
import { ref, watch, onMounted, onBeforeUnmount, nextTick } from 'vue'
import { loadAMap, loadAMapPlugins } from './amap-loader'

const location = defineModel({ default: null }) // { lng, lat } 或 null

const rootEl = ref(null)
let map = null
let AMap = null
let marker = null
let pending = null // 地图未就绪时缓存的待定位坐标 [lng, lat]

function circleSvg() {
  return `<svg xmlns="http://www.w3.org/2000/svg" width="22" height="22" viewBox="0 0 22 22">
    <circle cx="11" cy="11" r="9" fill="#1d6df0" fill-opacity="0.9" stroke="#ffffff" stroke-width="2"/>
    <circle cx="11" cy="11" r="3" fill="#ffffff"/>
  </svg>`
}

function placeMarker(lng, lat) {
  if (!map) {
    pending = [Number(lng), Number(lat)]
    return
  }
  if (!marker) {
    marker = new AMap.Marker({
      content: circleSvg(),
      offset: new AMap.Pixel(-11, -11)
    })
    map.add(marker)
  }
  marker.setPosition([lng, lat])
  map.setZoomAndCenter(Math.max(map.getZoom(), 16), [lng, lat])
}

function clear() {
  location.value = null
  pending = null
  if (marker && map) {
    map.remove(marker)
    marker = null
  }
}

// 定位到当前位置（浏览器 Geolocation，高德返回 GCJ-02）
async function locateMe() {
  try {
    const Am = await loadAMapPlugins(['AMap.Geolocation'])
    const geo = new Am.Geolocation({
      enableHighAccuracy: true,
      timeout: 8000,
      zoomToAccuracy: true
    })
    geo.getCurrentPosition((status, result) => {
      if (status === 'complete' && result.position) {
        const { lng, lat } = result.position
        location.value = { lng: +lng.toFixed(6), lat: +lat.toFixed(6) }
        placeMarker(lng, lat)
      } else {
        // 定位失败回退到校园中心
        const c = { lng: 118.007853, lat: 36.814398 }
        location.value = c
        placeMarker(c.lng, c.lat)
      }
    })
  } catch (e) {
    console.error('定位失败', e)
  }
}

// 外部（如选择校园地点/编辑回填）传入了坐标 → 打点定位
watch(location, (v) => {
  if (v && v.lng != null && v.lat != null) placeMarker(Number(v.lng), Number(v.lat))
})

onMounted(async () => {
  await nextTick()
  AMap = await loadAMap()
  map = new AMap.Map(rootEl.value, {
    center: [118.007853, 36.814398],
    zoom: 16,
    mapStyle: 'amap://styles/normal'
  })
  if (pending) {
    placeMarker(pending[0], pending[1])
    pending = null
  }
  map.on('click', (e) => {
    const lng = e.lnglat.getLng()
    const lat = e.lnglat.getLat()
    location.value = { lng: +lng.toFixed(6), lat: +lat.toFixed(6) }
    placeMarker(lng, lat)
  })
  setTimeout(() => map.resize(), 60)
})

onBeforeUnmount(() => {
  if (map) {
    map.destroy()
    map = null
  }
})
</script>

<template>
  <div class="picker">
    <div ref="rootEl" class="picker-map">
      <el-button class="picker-locate" size="small" type="primary" round @click="locateMe">
        📍 定位我的位置
      </el-button>
    </div>
    <div class="picker-bar">
      <span v-if="location && location.lng != null && location.lat != null" class="picker-text">
        已选位置：经度 {{ location.lng }}，纬度 {{ location.lat }}
      </span>
      <span v-else class="picker-hint">选择上方地点、点击「定位我的位置」或在地图上点击拾取位置</span>
      <el-button v-if="location && location.lng != null" size="small" text type="danger" @click="clear">清除位置</el-button>
    </div>
  </div>
</template>

<style scoped>
.picker-map {
  position: relative;
  width: 100%;
  height: 300px;
  border-radius: 8px;
  overflow: hidden;
  border: 1px solid #e4e7ed;
}
.picker-locate {
  position: absolute;
  top: 12px;
  right: 12px;
  z-index: 10;
  box-shadow: 0 1px 6px rgba(0, 0, 0, 0.15);
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
