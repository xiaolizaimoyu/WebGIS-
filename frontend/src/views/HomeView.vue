<script setup>
// 首页（归属：前端 C 整合）——左信息流 + 右地图 分栏布局
// 左侧：前端 B 的业务信息流（保留原有逻辑）
// 右侧：前端 A 的地图组件
// 天气组件（前端 B）为全局右上角悬浮，已在 MainLayout 中挂载
// 已加固：请求竞态保护（快速切换不串数据）、真实字段 longitude/latitude、mock 兜底归一化
import { onMounted, onUnmounted, ref, computed, watch } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import * as postApi from '@/api/post'
import { formatTime } from '@/api/const'
import { TYPE_MAP } from '@/api/typeMap' // B 扩展版：含美食分享 / 失物招领
import { getMockContents } from '@/utils/mockData'
import { useDialogStore } from '@/stores/dialog'
import MapComponent from '@/components/MapComponent.vue'

const route = useRoute()
const router = useRouter()
const dialog = useDialogStore()
const mapRef = ref(null)
const mapWrap = ref(null)

// 顶部 Tab：全部 + 分类（value='all' 代表全部，请求时转 undefined）
const tabs = [
  { value: 'all', label: '全部' },
  ...Object.entries(TYPE_MAP).map(([value, item]) => ({ value, label: item.label }))
]

// 分类状态与 URL 同步（?type=meeting）：进入页面时从 query 恢复，
// 切换 tab 时写入 query，保证从详情页返回时分类正确且数据刷新
const queryType = String(route.query.type || 'all')
const activeType = ref(TYPE_MAP[queryType] ? queryType : 'all')
const list = ref([])
const total = ref(0)
const page = ref(1)
const size = ref(8)
const loading = ref(false)
let requestId = 0

// 请求序号：防止快速切换 tab/翻页时旧请求晚返回覆盖新结果
let loadSeq = 0

// ====== 列表缓存（模块级，跨组件重建保留） ======
// 作用：从详情页返回首页时，先展示上次成功加载的内容，再后台刷新，
// 即使请求慢/失败也不出现空白；切分类后缓存按分类失效。
let cachedList = []
let cachedTotal = 0
let cachedType = ''

// setup 阶段恢复缓存：返回首页时首屏直接渲染上次内容，避免空白/一闪
if (cachedType === activeType.value && cachedList.length) {
  list.value = cachedList
  total.value = cachedTotal
}

// 统一坐标字段：后端返回 longitude/latitude，兼容 mock 的 lng/lat
function normalizeItem(item) {
  return {
    ...item,
    longitude: item.longitude ?? item.lng ?? null,
    latitude: item.latitude ?? item.lat ?? null
  }
}

async function load() {
  const seq = ++loadSeq
  // 有同分类缓存：立即展示缓存内容并后台刷新（不遮罩，返回首页不空白）
  if (cachedType === activeType.value && cachedList.length) {
    list.value = cachedList
    total.value = cachedTotal
    loading.value = false
  } else {
    loading.value = true
  }
  try {
    const data = await postApi.listContents({
      type: activeType.value === 'all' ? undefined : activeType.value,
      page: page.value,
      size: size.value
    })
    if (seq !== loadSeq) return // 已被更新的请求取代
    const items = Array.isArray(data) ? data : (data.items || [])
    list.value = items.map(normalizeItem)
    total.value = data.total ?? list.value.length
    // 仅缓存第一页（翻页不覆盖缓存），按分类记录
    if (page.value === 1) {
      cachedList = list.value
      cachedTotal = total.value
      cachedType = activeType.value
    }
  } catch (e) {
    if (seq !== loadSeq) return
    // 请求失败：有同分类缓存则保留缓存展示；否则用 mock 兜底，绝不空白
    if (!(cachedType === activeType.value && cachedList.length)) {
      list.value = getMockContents().map(normalizeItem)
      total.value = list.value.length
    }
  } finally {
    if (seq === loadSeq) loading.value = false
  }
}

function onTabChange() {
  page.value = 1
  syncTypeToUrl()
  load()
}

// 把当前分类写入 URL query（'all' 时移除，保持 URL 干净）
function syncTypeToUrl() {
  const q = { ...route.query }
  if (activeType.value === 'all') delete q.type
  else q.type = activeType.value
  router.replace({ query: q })
}

// 浏览器前进/后退改变 query.type 时，同步 tab 并重新加载
watch(
  () => route.query.type,
  (t) => {
    const next = t ? String(t) : 'all'
    if (TYPE_MAP[next] && activeType.value !== next) {
      activeType.value = next
      page.value = 1
      load()
    }
  }
)

// 浏览器 bfcache 后退恢复页面快照时不触发 onMounted，这里强制刷新
function onPageShow(e) {
  if (e.persisted) load()
}

onMounted(() => {
  load()
  window.addEventListener('pageshow', onPageShow)
})

onUnmounted(() => {
  window.removeEventListener('pageshow', onPageShow)
})

function toDetail(id) {
  router.push(`/content/${id}`)
}

function firstImage(item) {
  return item.images && item.images.length ? item.images[0] : ''
}

function summaryText(item) {
  return item.body && item.body.trim() ? item.body.trim() : '暂无内容简介'
}

function onImageError(event) {
  event.target.src = 'data:image/svg+xml;utf8,' + encodeURIComponent(
    "<svg xmlns='http://www.w3.org/2000/svg' viewBox='0 0 120 80'>" +
    "<rect width='120' height='80' fill='%23eef3ff'/>" +
    "<text x='60' y='48' font-size='28' text-anchor='middle'>📷</text>" +
    "</svg>"
  )
  event.target.onerror = null
}

// ====== 右侧地图（前端 A 组件整合） ======
const mapCenter = ref([118.001917, 36.814013])
const mapZoom = ref(12)

function coordinate(value) {
  const number = Number(value)
  return Number.isFinite(number) ? number : null
}

// 从内容列表提取地图标记点（带坐标的内容）
const mapMarkers = computed(() =>
  list.value
    .filter((c) => c.longitude && c.latitude)
    .map((c) => ({
      id: c.id,
      lng: c.longitude,
      lat: c.latitude,
      title: c.title
    }))
)

const hasMapData = computed(() => mapMarkers.value.length > 0)

function resetMapView() {
  if (mapRef.value && typeof mapRef.value.fitToMarkers === 'function') {
    mapRef.value.fitToMarkers()
  }
}

// 地图加载完成回调
function onMapReady(olMap) {
  // 地图就绪后自适应标记点范围
  setTimeout(() => {
    if (mapMarkers.value.length && mapRef.value) {
      mapRef.value.fitToMarkers()
    }
  }, 300)
}

// 地图标记点点击 → 全局弹窗展示详情
function onMarkerClick(marker) {
  const item = list.value.find((c) => c.id === marker.id)
  dialog.open({
    title: marker.title,
    content: item ? `${item.author_name} · ${formatTime(item.created_at)}\n\n${item.body?.slice(0, 100) || ''}` : '无详情',
    type: 'info',
    showCancel: true,
    confirmText: '查看详情',
    cancelText: '关闭',
    onConfirm: () => toDetail(marker.id)
  })
}

// 信息流卡片点击定位到地图：滚动地图到可视区域 + 居中 + 高亮标记
function locateOnMap(item) {
  if (!item.longitude || !item.latitude || !mapRef.value) return
  mapRef.value.setCenter(item.longitude, item.latitude, 15)
  mapRef.value.highlightMarker?.(item.id)
  // 把地图滚动到视野内（窄屏/未固定时兜底）
  mapWrap.value?.scrollIntoView({ behavior: 'smooth', block: 'center' })
}

</script>

<template>
  <div class="home-layout">
    <!-- 左侧：信息流 -->
    <div class="left-panel">
      <el-card shadow="never" class="filter-card">
        <el-tabs v-model="activeType" @tab-change="onTabChange">
          <el-tab-pane v-for="t in tabs" :key="t.value" :label="t.label" :name="t.value" />
        </el-tabs>
      </el-card>

      <div v-loading="loading" class="feed">
        <el-card
          v-for="c in list"
          :key="c.id"
          class="item-card"
          shadow="hover"
          @click="toDetail(c.id)"
        >
          <div class="item-body">
            <div class="badge">
              <el-tag :type="TYPE_MAP[c.type]?.tagType || 'info'" size="small">
                {{ TYPE_MAP[c.type]?.label || c.type }}
              </el-tag>
              <span v-if="c.category" class="category">· {{ c.category }}</span>
            </div>
            <h3 class="title">{{ c.title }}</h3>
            <p class="summary">{{ summaryText(c) }}</p>
            <div class="meta">
              <span>{{ c.author_name }}</span>
              <span>发布于 {{ formatTime(c.created_at) }}</span>
            </div>
            <div class="item-actions" v-if="c.longitude && c.latitude">
              <el-button text type="primary" size="small" @click.stop="locateOnMap(c)">
                📍 在地图上查看
              </el-button>
            </div>
          </div>
          <el-image v-if="firstImage(c)" :src="firstImage(c)" fit="cover" lazy class="thumb" @error="onImageError" />
        </el-card>

        <el-empty v-if="!loading && !list.length" description="这里还空空如也，来发布第一条内容吧" aria-live="polite" />
      </div>

      <div v-if="total > size" class="pager">
        <el-pagination
          background
          layout="prev, pager, next"
          :total="total"
          :page-size="size"
          :current-page="page"
          @current-change="(p) => ((page = p), load())"
        />
      </div>
    </div>

    <!-- 右侧：地图 -->
    <div class="right-panel">
      <div ref="mapWrap" class="map-wrapper">
        <div class="map-header">
          <span class="map-title">🗺️ 活动分布地图</span>
          <el-button text size="small" @click="resetMapView">
            重置视野
          </el-button>
        </div>
        <div v-if="!hasMapData" class="map-empty">
          暂无活动点位，先发布一条内容即可展示在地图上。
        </div>
        <MapComponent
          v-else
          ref="mapRef"
          :center="mapCenter"
          :zoom="mapZoom"
          :markers="mapMarkers"
          height="360px"
          @ready="onMapReady"
          @marker-click="onMarkerClick"
        />
        <div class="map-tip">
          💡 点击标记点查看活动详情，点击"在地图上查看"可定位
        </div>
      </div>
    </div>
  </div>
</template>

<style scoped>
.home-layout {
  display: flex;
  gap: 20px;
  max-width: 1400px;
  margin: 0 auto;
  padding: 20px;
  min-height: calc(100vh - 60px);
}

.left-panel {
  flex: 1;
  min-width: 0;
}

.right-panel {
  width: 420px;
  flex-shrink: 0;
  display: flex;
  flex-direction: column;
  gap: 16px;
  position: sticky;
  top: 80px;
  align-self: flex-start;
}

.filter-card {
  border-radius: 10px;
  margin-bottom: 16px;
}

.feed {
  min-height: 200px;
}

.item-card {
  margin-bottom: 14px;
  border-radius: 10px;
  cursor: pointer;
  transition: transform 0.2s ease;
}

.item-card:hover {
  transform: translateY(-2px);
}

.item-card :deep(.el-card__body) {
  display: flex;
  gap: 16px;
  width: 100%;
}

.item-body {
  flex: 1;
  min-width: 0;
}

.badge {
  display: flex;
  align-items: center;
  gap: 6px;
  margin-bottom: 8px;
}

.category {
  color: #909399;
  font-size: 13px;
}

.title {
  font-size: 17px;
  color: #303133;
  margin-bottom: 6px;
}

.summary {
  color: #606266;
  font-size: 14px;
  line-height: 1.6;
  display: -webkit-box;
  -webkit-line-clamp: 2;
  -webkit-box-orient: vertical;
  overflow: hidden;
}

.meta {
  margin-top: 8px;
  color: #a8abb2;
  font-size: 12px;
  display: flex;
  gap: 10px;
}

.item-actions {
  margin-top: 8px;
}

.thumb {
  width: 120px;
  height: 90px;
  border-radius: 8px;
  flex-shrink: 0;
}

.pager {
  display: flex;
  justify-content: center;
  padding: 10px 0 20px;
}

.map-wrapper {
  background: #fff;
  border-radius: 12px;
  padding: 12px;
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.06);
}

.map-empty {
  display: flex;
  align-items: center;
  justify-content: center;
  height: 360px;
  border-radius: 10px;
  background: linear-gradient(135deg, #f5f7ff, #eef4ff);
  color: #7a879d;
  font-size: 13px;
  text-align: center;
  padding: 16px;
}

.map-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 8px;
}

.map-title {
  font-size: 15px;
  font-weight: 600;
  color: #303133;
}

.map-tip {
  font-size: 12px;
  color: #909399;
  margin-top: 8px;
  text-align: center;
  line-height: 1.5;
}

/* 响应式：小屏幕下右侧面板变为全宽 */
@media (max-width: 992px) {
  .home-layout {
    flex-direction: column;
  }
  .right-panel {
    width: 100%;
    position: static;
  }
}

@media (max-width: 560px) {
  .home-layout {
    padding: 12px;
  }
  .item-card :deep(.el-card__body) {
    gap: 10px;
  }
  .thumb {
    width: 96px;
    height: 72px;
  }
  .map-empty {
    height: 280px;
  }
}
</style>
