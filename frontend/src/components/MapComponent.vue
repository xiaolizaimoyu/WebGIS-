<script setup>
// 地图组件（高德 JS API 2.0 版）——可复用地图容器
// 对外契约（与旧版 OpenLayers 组件保持一致，调用方无需改动）：
//   props: center [lng, lat], zoom, markers [{id, lng, lat, title}], height
//   emit:  ready(amap), click({lng,lat}), marker-click({id,title})
//   expose: addMarker / removeMarker / setCenter / fitToMarkers / getMap / highlightMarker / updateSize / drawRoute / clearRoute
// 坐标系：全链路 GCJ-02（高德火星坐标），传入坐标须为 GCJ-02
import { ref, onMounted, onBeforeUnmount, watch, nextTick } from 'vue'
import { loadAMap } from './map/amap-loader'

const props = defineProps({
  center: { type: Array, default: () => [118.007853, 36.814398] }, // 默认校园中心（淄博山东理工，GCJ-02）
  zoom: { type: Number, default: 16 },
  markers: { type: Array, default: () => [] },
  height: { type: String, default: '100%' }
})

const emit = defineEmits(['ready', 'click', 'marker-click'])

const mapEl = ref(null)
let map = null
let AMap = null
const markerMap = new Map() // id -> AMap.Marker
let routeOverlay = null // 路线覆盖物（橙色虚线）

// 点位 SVG（默认蓝色）
function pinSvg(color = '#409eff', highlight = false) {
  const w = highlight ? 44 : 32
  const h = highlight ? 56 : 40
  return `<svg xmlns="http://www.w3.org/2000/svg" width="${w}" height="${h}" viewBox="0 0 32 40">
    <path d="M16 0C7.16 0 0 7.16 0 16c0 12 16 24 16 24s16-12 16-24C32 7.16 24.84 0 16 0z" fill="${color}" stroke="#fff" stroke-width="2"/>
    <circle cx="16" cy="16" r="${highlight ? 7 : 6}" fill="#fff"/>
  </svg>`
}

function createMarker(m) {
  if (!map || !AMap) return
  const marker = new AMap.Marker({
    position: [Number(m.lng), Number(m.lat)],
    content: pinSvg(m.color || '#409eff'),
    offset: new AMap.Pixel(-16, -40),
    title: m.title || ''
  })
  if (m.title) {
    marker.setLabel({
      content: `<div style="font-size:12px;color:#303133;background:#fff;padding:2px 6px;border-radius:4px;border:1px solid #e4e7ed;white-space:nowrap;">${m.title}</div>`,
      direction: 'top',
      offset: new AMap.Pixel(0, -8)
    })
  }
  marker.on('click', () => {
    emit('marker-click', { id: m.id, title: m.title })
  })
  markerMap.set(m.id, marker)
  map.add(marker)
}

function renderMarkers() {
  if (!map) return
  const olds = [...markerMap.values()]
  if (olds.length) map.remove(olds)
  markerMap.clear()
  props.markers.forEach(createMarker)
}

async function initMap() {
  if (!mapEl.value) return
  AMap = await loadAMap()
  map = new AMap.Map(mapEl.value, {
    center: props.center,
    zoom: props.zoom,
    mapStyle: 'amap://styles/normal',
    viewMode: '2D'
  })
  map.on('click', (e) => {
    emit('click', { lng: e.lnglat.getLng(), lat: e.lnglat.getLat() })
  })
  renderMarkers()
  emit('ready', map)
}

watch(
  () => props.markers,
  () => renderMarkers(),
  { deep: true }
)

watch(
  () => props.center,
  (val) => {
    if (map && val) map.setCenter(val)
  }
)

defineExpose({
  getMap: () => map,
  setCenter: (lng, lat, z) => {
    if (map) {
      map.setCenter([lng, lat])
      if (z !== undefined) map.setZoom(z)
    }
  },
  addMarker: (m) => createMarker(m),
  removeMarker: (id) => {
    const m = markerMap.get(id)
    if (m && map) {
      map.remove(m)
      markerMap.delete(id)
    }
  },
  fitToMarkers: () => {
    if (!map || markerMap.size === 0) return
    map.setFitView([...markerMap.values()], false, [50, 50, 50, 50])
  },
  highlightMarker: (id) => {
    const m = markerMap.get(id)
    if (!m) return
    m.setContent(pinSvg('#f56c6c', true))
    m.setOffset(new AMap.Pixel(-22, -56))
    setTimeout(() => {
      if (markerMap.get(id) === m) {
        m.setContent(pinSvg('#409eff'))
        m.setOffset(new AMap.Pixel(-16, -40))
      }
    }, 3000)
  },
  updateSize: () => {
    if (map) nextTick(() => map.resize())
  },
  // 绘制出发地→目的地路线（橙色虚线），自动缩放视野
  drawRoute: (start, end) => {
    if (!map || !AMap || !start || !end) return
    if (routeOverlay) {
      map.remove(routeOverlay)
      routeOverlay = null
    }
    routeOverlay = new AMap.Polyline({
      path: [start, end],
      strokeColor: '#ff7d00',
      strokeWeight: 6,
      strokeOpacity: 0.9,
      strokeStyle: 'dashed',
      strokeDasharray: [10, 10],
      lineJoin: 'round',
      lineCap: 'round'
    })
    map.add(routeOverlay)
    map.setFitView([routeOverlay], false, [60, 60, 60, 60])
  },
  clearRoute: () => {
    if (routeOverlay && map) {
      map.remove(routeOverlay)
      routeOverlay = null
    }
  }
})

onMounted(() => {
  nextTick(() => initMap().catch((e) => console.error(e)))
})

onBeforeUnmount(() => {
  if (map) {
    map.destroy()
    map = null
  }
})
</script>

<template>
  <div ref="mapEl" class="amap-container" :style="{ height }"></div>
</template>

<style scoped>
.amap-container {
  width: 100%;
  min-height: 300px;
  border-radius: 8px;
  overflow: hidden;
}
</style>
