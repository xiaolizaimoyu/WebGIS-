<script setup>
// 失物招领列表页（归属：前端 C）
import { onMounted, ref, computed } from 'vue'
import { useRouter } from 'vue-router'
import * as lostfoundApi from '@/api/lostfound'
import { formatTime } from '@/api/const'
import { getMockLostFound } from '@/utils/mockData'
import MapComponent from '@/components/MapComponent.vue'
import WeatherWidget from '@/components/WeatherWidget.vue'

const router = useRouter()
const mapRef = ref(null)

const activeType = ref('all')
const list = ref([])
const loading = ref(false)

async function load() {
  loading.value = true
  try {
    const data = await lostfoundApi.listLostFound({ type: activeType.value === 'all' ? undefined : activeType.value })
    list.value = data.items || data || []
  } catch {
    let mock = getMockLostFound()
    if (activeType.value !== 'all') mock = mock.filter((x) => x.type === activeType.value)
    list.value = mock
  } finally {
    loading.value = false
  }
}

function onTypeChange(t) {
  activeType.value = t
  load()
}

function toDetail(id) {
  router.push(`/lost-found/${id}`)
}

const mapCenter = ref([116.397428, 39.90923])
const mapMarkers = computed(() => [])

onMounted(load)
</script>

<template>
  <div class="page-layout">
    <div class="left-panel">
      <el-card shadow="never" class="header-card">
        <div class="header-row">
          <el-radio-group v-model="activeType" @change="onTypeChange">
            <el-radio-button value="all">全部</el-radio-button>
            <el-radio-button value="lost">寻物启事</el-radio-button>
            <el-radio-button value="found">失物招领</el-radio-button>
          </el-radio-group>
          <el-button type="primary" @click="router.push('/lost-found/publish')">＋ 发布</el-button>
        </div>
      </el-card>

      <div v-loading="loading" class="feed">
        <el-card v-for="item in list" :key="item.id" class="lf-card" shadow="hover" @click="toDetail(item.id)">
          <div class="lf-head">
            <el-tag :type="item.type === 'lost' ? 'danger' : 'success'" size="small">
              {{ item.type === 'lost' ? '🔍 寻物' : '📦 招领' }}
            </el-tag>
            <span class="lf-meta">{{ item.author_name }} · {{ formatTime(item.created_at) }}</span>
          </div>
          <h3 class="lf-title">{{ item.title }}</h3>
          <div class="lf-info">
            <span>📍 {{ item.location }}</span>
            <span>🕐 {{ item.lost_time }}</span>
          </div>
          <p class="lf-desc">{{ item.description }}</p>
        </el-card>
        <el-empty v-if="!loading && !list.length" description="暂无信息" />
      </div>
    </div>

    <div class="right-panel">
      <WeatherWidget city="北京" :use-mock="true" />
      <div class="map-wrapper">
        <div class="map-header"><span class="map-title">🗺️ 校园地图</span></div>
        <MapComponent ref="mapRef" :center="mapCenter" :zoom="14" :markers="mapMarkers" height="360px" />
      </div>
    </div>
  </div>
</template>

<style scoped>
.page-layout { display: flex; gap: 20px; max-width: 1400px; margin: 0 auto; padding: 20px; min-height: calc(100vh - 60px); }
.left-panel { flex: 1; min-width: 0; }
.right-panel { width: 420px; flex-shrink: 0; display: flex; flex-direction: column; gap: 16px; position: sticky; top: 80px; align-self: flex-start; }
.header-card { border-radius: 12px; margin-bottom: 16px; }
.header-row { display: flex; justify-content: space-between; align-items: center; }
.feed { min-height: 200px; }
.lf-card { margin-bottom: 14px; border-radius: 12px; cursor: pointer; transition: all 0.25s; }
.lf-card:hover { transform: translateY(-2px); box-shadow: 0 8px 24px rgba(245, 108, 108, 0.12) !important; }
.lf-head { display: flex; align-items: center; gap: 8px; margin-bottom: 8px; }
.lf-meta { margin-left: auto; color: #a8abb2; font-size: 12px; }
.lf-title { font-size: 16px; color: #303133; margin: 0 0 8px 0; }
.lf-info { display: flex; gap: 16px; color: #606266; font-size: 13px; margin-bottom: 8px; }
.lf-desc { color: #909399; font-size: 13px; line-height: 1.6; margin: 0; display: -webkit-box; -webkit-line-clamp: 2; -webkit-box-orient: vertical; overflow: hidden; }
.map-wrapper { background: #fff; border-radius: 12px; padding: 12px; box-shadow: 0 2px 12px rgba(0,0,0,0.06); }
.map-header { margin-bottom: 8px; }
.map-title { font-size: 15px; font-weight: 600; color: #303133; }
@media (max-width: 992px) { .page-layout { flex-direction: column; } .right-panel { width: 100%; position: static; } }
</style>
