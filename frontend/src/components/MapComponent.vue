<script setup>
// 地图组件（归属：前端 A）——基于 OpenLayers 的可复用地图容器
// 对外契约：
//   props: center [lng, lat], zoom, markers [{id, lng, lat, title}]
//   emit:  ready(olMap), click(coordinate), marker-click(marker)
//   expose: addMarker / removeMarker / setCenter / fitToMarkers / getMap
import { ref, onMounted, onBeforeUnmount, watch, nextTick } from 'vue'
import Map from 'ol/Map'
import View from 'ol/View'
import TileLayer from 'ol/layer/Tile'
import XYZ from 'ol/source/XYZ'
import VectorLayer from 'ol/layer/Vector'
import VectorSource from 'ol/source/Vector'
import Feature from 'ol/Feature'
import Point from 'ol/geom/Point'
import { Style, Icon, Fill, Stroke, Text } from 'ol/style'
import { fromLonLat, toLonLat } from 'ol/proj'
import 'ol/ol.css'

const props = defineProps({
  center: { type: Array, default: () => [116.397428, 39.90923] }, // 默认北京
  zoom: { type: Number, default: 12 },
  markers: { type: Array, default: () => [] },
  height: { type: String, default: '100%' }
})

const emit = defineEmits(['ready', 'click', 'marker-click'])

const mapEl = ref(null)
let olMap = null
let vectorLayer = null
let vectorSource = null

// 创建标记点样式
function createMarkerStyle(title) {
  return new Style({
    image: new Icon({
      anchor: [0.5, 1],
      src: 'data:image/svg+xml;utf8,' + encodeURIComponent(`
        <svg xmlns="http://www.w3.org/2000/svg" width="32" height="40" viewBox="0 0 32 40">
          <path d="M16 0C7.16 0 0 7.16 0 16c0 12 16 24 16 24s16-12 16-24C32 7.16 24.84 0 16 0z" fill="#409eff" stroke="#fff" stroke-width="2"/>
          <circle cx="16" cy="16" r="6" fill="#fff"/>
        </svg>
      `),
      scale: 1
    }),
    text: new Text({
      text: title || '',
      offsetY: -44,
      font: '12px sans-serif',
      fill: new Fill({ color: '#303133' }),
      stroke: new Stroke({ color: '#fff', width: 3 })
    })
  })
}

// 渲染所有标记点
function renderMarkers() {
  if (!vectorSource) return
  vectorSource.clear()
  props.markers.forEach((m) => {
    const feature = new Feature({
      geometry: new Point(fromLonLat([m.lng, m.lat])),
      markerId: m.id,
      markerTitle: m.title
    })
    feature.setStyle(createMarkerStyle(m.title))
    vectorSource.addFeature(feature)
  })
}

// 初始化地图
function initMap() {
  if (!mapEl.value) return

  vectorSource = new VectorSource()
  vectorLayer = new VectorLayer({ source: vectorSource })

  olMap = new Map({
    target: mapEl.value,
    layers: [
      // 高德地图瓦片（国内可用，无需 API Key）
      new TileLayer({
        source: new XYZ({
          urls: [
            'https://webrd01.is.autonavi.com/appmaptile?lang=zh_cn&size=1&scale=1&style=8&x={x}&y={y}&z={z}',
            'https://webrd02.is.autonavi.com/appmaptile?lang=zh_cn&size=1&scale=1&style=8&x={x}&y={y}&z={z}',
            'https://webrd03.is.autonavi.com/appmaptile?lang=zh_cn&size=1&scale=1&style=8&x={x}&y={y}&z={z}',
            'https://webrd04.is.autonavi.com/appmaptile?lang=zh_cn&size=1&scale=1&style=8&x={x}&y={y}&z={z}'
          ],
          attributions: '© 高德地图'
        })
      }),
      vectorLayer
    ],
    view: new View({
      center: fromLonLat(props.center),
      zoom: props.zoom
    }),
    controls: [] // 隐藏默认控件，保持简洁
  })

  // 地图点击事件
  olMap.on('click', (evt) => {
    const coord = toLonLat(evt.coordinate)
    emit('click', { lng: coord[0], lat: coord[1], pixel: evt.pixel })
  })

  // 标记点点击事件
  olMap.on('singleclick', (evt) => {
    olMap.forEachFeatureAtPixel(evt.pixel, (feature) => {
      const id = feature.get('markerId')
      if (id !== undefined) {
        emit('marker-click', {
          id,
          title: feature.get('markerTitle'),
          coordinate: toLonLat(feature.getGeometry().getCoordinates())
        })
        return true
      }
      return false
    })
  })

  renderMarkers()
  emit('ready', olMap)
}

// 监听 markers 变化
watch(
  () => props.markers,
  () => renderMarkers(),
  { deep: true }
)

// 监听 center 变化
watch(
  () => props.center,
  (val) => {
    if (olMap && val) {
      olMap.getView().setCenter(fromLonLat(val))
    }
  }
)

// 对外暴露的方法
defineExpose({
  getMap: () => olMap,
  setCenter: (lng, lat, z) => {
    if (olMap) {
      olMap.getView().setCenter(fromLonLat([lng, lat]))
      if (z !== undefined) olMap.getView().setZoom(z)
    }
  },
  addMarker: (m) => {
    if (!vectorSource) return
    const feature = new Feature({
      geometry: new Point(fromLonLat([m.lng, m.lat])),
      markerId: m.id,
      markerTitle: m.title
    })
    feature.setStyle(createMarkerStyle(m.title))
    vectorSource.addFeature(feature)
  },
  removeMarker: (id) => {
    if (!vectorSource) return
    vectorSource.getFeatures().forEach((f) => {
      if (f.get('markerId') === id) vectorSource.removeFeature(f)
    })
  },
  fitToMarkers: () => {
    if (!olMap || !vectorSource || vectorSource.getFeatures().length === 0) return
    olMap.getView().fit(vectorSource.getExtent(), { padding: [40, 40, 40, 40], maxZoom: 15 })
  },
  updateSize: () => {
    if (olMap) {
      nextTick(() => olMap.updateSize())
    }
  }
})

onMounted(() => {
  nextTick(() => initMap())
})

onBeforeUnmount(() => {
  if (olMap) {
    olMap.setTarget(null)
    olMap = null
  }
})
</script>

<template>
  <div ref="mapEl" class="ol-map-container" :style="{ height: height }"></div>
</template>

<style scoped>
.ol-map-container {
  width: 100%;
  min-height: 300px;
  border-radius: 8px;
  overflow: hidden;
}

/* 确保 OpenLayers 内部元素正确撑满 */
.ol-map-container :deep(.ol-viewport) {
  border-radius: 8px;
}
</style>
