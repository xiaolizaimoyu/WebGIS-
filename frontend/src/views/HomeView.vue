<script setup>
// 首页（归属：前端 C 整合）——左信息流 + 右地图 分栏布局
// 左侧：前端 B 的业务信息流（保留原有逻辑）
// 右侧：前端 A 的地图组件
// 天气组件（前端 B）为全局右上角悬浮，已在 MainLayout 中挂载
// 已加固：请求竞态保护（快速切换不串数据）、真实字段 longitude/latitude、mock 兜底归一化
import { onMounted, ref, computed } from 'vue'
import { useRouter } from 'vue-router'
import * as postApi from '@/api/post'
import { formatTime } from '@/api/const'
import { TYPE_MAP } from '@/api/typeMap' // B 扩展版：含美食分享 / 失物招领
import { getMockContents } from '@/utils/mockData'
import { useDialogStore } from '@/stores/dialog'
import MapComponent from '@/components/MapComponent.vue'

const router = useRouter()
const dialog = useDialogStore()
const mapRef = ref(null)

// 顶部 Tab：全部 + 分类（value='all' 代表全部，请求时转 undefined）
const tabs = [
  { value: 'all', label: '全部' },
  ...Object.entries(TYPE_MAP).map(([value, item]) => ({ value, label: item.label }))
]
const activeType = ref('all')
const list = ref([])
const total = ref(0)
const page = ref(1)
const size = ref(8)
const loading = ref(false)

// 请求序号：防止快速切换 tab/翻页时旧请求晚返回覆盖新结果
let loadSeq = 0

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
  loading.value = true
  try {
    const data = await postApi.listContents({
      type: activeType.value === 'all' ? undefined : activeType.value,
      page: page.value,
      size: size.value
    })
    if (seq !== loadSeq) return // 已被更新的请求取代
    list.value = (data.items || []).map(normalizeItem)
    total.value = data.total || 0
  } catch (e) {
    if (seq !== loadSeq) return
    // 后端未启动时使用模拟数据，确保前端可独立运行
    list.value = getMockContents().map(normalizeItem)
    total.value = list.value.length
  } finally {
    if (seq === loadSeq) loading.value = false
  }
}

function onTabChange() {
  page.value = 1
  load()
}

function toDetail(id) {
  router.push(`/content/${id}`)
}

function firstImage(item) {
  return item.images && item.images.length ? item.images[0] : ''
}

// ====== 右侧地图（前端 A 组件整合） ======
const mapCenter = ref([116.397428, 39.90923])
const mapZoom = ref(12)

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

// 信息流卡片点击定位到地图
function locateOnMap(item) {
  if (item.longitude && item.latitude && mapRef.value) {
    mapRef.value.setCenter(item.longitude, item.latitude, 15)
  }
}

onMounted(load)
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
            <p class="summary">{{ c.body }}</p>
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
          <el-image v-if="firstImage(c)" :src="firstImage(c)" fit="cover" class="thumb" />
        </el-card>

        <el-empty v-if="!loading && !list.length" description="这里还空空如也，来发布第一条内容吧" />
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
      <div class="map-wrapper">
        <div class="map-header">
          <span class="map-title">🗺️ 活动分布地图</span>
          <el-button text size="small" @click="mapRef?.fitToMarkers()">
            重置视野
          </el-button>
        </div>
        <MapComponent
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
</style>
