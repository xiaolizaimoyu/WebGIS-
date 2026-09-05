<script setup>
// 学习资料列表页（归属：前端 C）——左侧资料信息流 + 右侧地图
import { onMounted, ref, computed } from 'vue'
import { useRouter } from 'vue-router'
import * as materialApi from '@/api/material'
import { formatTime } from '@/api/const'
import { getMockMaterials } from '@/utils/mockData'
import MapComponent from '@/components/MapComponent.vue'
import WeatherWidget from '@/components/WeatherWidget.vue'

const router = useRouter()
const mapRef = ref(null)

const subjects = ['全部', '数学', '英语', 'GIS', '遥感', '编程', '专业课', '其他']
const activeSubject = ref('全部')
const keyword = ref('')
const list = ref([])
const total = ref(0)
const page = ref(1)
const size = ref(10)
const loading = ref(false)

const fileTypeIcon = {
  pdf: '📄', docx: '📝', doc: '📝', zip: '📦', rar: '📦',
  ppt: '📊', pptx: '📊', xls: '📈', xlsx: '📈', txt: '📃', default: '📁'
}

function getIcon(type) {
  return fileTypeIcon[type] || fileTypeIcon.default
}

async function load() {
  loading.value = true
  try {
    const data = await materialApi.listMaterials({
      subject: activeSubject.value === '全部' ? undefined : activeSubject.value,
      keyword: keyword.value || undefined,
      page: page.value,
      size: size.value
    })
    list.value = data.items || data || []
    total.value = data.total || list.value.length
  } catch {
    let mock = getMockMaterials()
    if (activeSubject.value !== '全部') mock = mock.filter((m) => m.subject === activeSubject.value)
    if (keyword.value) mock = mock.filter((m) => m.title.includes(keyword.value))
    list.value = mock
    total.value = mock.length
  } finally {
    loading.value = false
  }
}

function onSubjectChange(s) {
  activeSubject.value = s
  page.value = 1
  load()
}

function onSearch() {
  page.value = 1
  load()
}

function toDetail(id) {
  router.push(`/material/${id}`)
}

const mapCenter = ref([116.397428, 39.90923])
const mapMarkers = computed(() => [])

onMounted(load)
</script>

<template>
  <div class="page-layout">
    <div class="left-panel">
      <el-card shadow="never" class="filter-card">
        <div class="filter-row">
          <el-input
            v-model="keyword"
            placeholder="搜索资料..."
            clearable
            style="width: 260px"
            @keyup.enter="onSearch"
            @clear="onSearch"
          >
            <template #prefix>🔍</template>
          </el-input>
          <el-button type="primary" @click="router.push('/material/upload')">
            ⬆️ 上传资料
          </el-button>
        </div>
        <div class="subject-row">
          <el-tag
            v-for="s in subjects"
            :key="s"
            :type="activeSubject === s ? 'primary' : 'info'"
            :effect="activeSubject === s ? 'dark' : 'plain'"
            class="subject-item"
            @click="onSubjectChange(s)"
          >
            {{ s }}
          </el-tag>
        </div>
      </el-card>

      <div v-loading="loading" class="feed">
        <el-card
          v-for="m in list"
          :key="m.id"
          class="material-card"
          shadow="hover"
          @click="toDetail(m.id)"
        >
          <div class="material-icon">{{ getIcon(m.file_type) }}</div>
          <div class="material-body">
            <div class="material-head">
              <el-tag size="small" type="success">{{ m.subject }}</el-tag>
              <el-tag size="small" type="info">{{ m.file_type.toUpperCase() }}</el-tag>
              <span class="meta">{{ m.author_name }} · {{ formatTime(m.created_at) }}</span>
            </div>
            <h3 class="material-title">{{ m.title }}</h3>
            <p class="material-desc">{{ m.description }}</p>
            <div class="material-tags">
              <el-tag v-for="t in m.tags" :key="t" size="small" effect="plain" class="tag">{{ t }}</el-tag>
            </div>
            <div class="material-stats">
              <span>📥 {{ m.downloads }} 下载</span>
              <span>❤️ {{ m.likes }} 点赞</span>
              <span>📦 {{ m.file_size }}</span>
            </div>
          </div>
        </el-card>

        <el-empty v-if="!loading && !list.length" description="还没有资料，来上传第一份吧" />
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

    <div class="right-panel">
      <WeatherWidget city="北京" :use-mock="true" />
      <div class="map-wrapper">
        <div class="map-header">
          <span class="map-title">🗺️ 校园地图</span>
        </div>
        <MapComponent ref="mapRef" :center="mapCenter" :zoom="14" :markers="mapMarkers" height="360px" />
      </div>
      <el-card shadow="never" class="tip-card">
        <div class="tip-title">💡 资料分享小贴士</div>
        <p>· 上传优质资料可获得积分奖励</p>
        <p>· 资料被下载越多，积分奖励越多</p>
        <p>· 请确保上传资料无版权问题</p>
      </el-card>
    </div>
  </div>
</template>

<style scoped>
.page-layout {
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
  border-radius: 12px;
  margin-bottom: 16px;
}

.filter-row {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 12px;
}

.subject-row {
  display: flex;
  flex-wrap: wrap;
  gap: 8px;
}

.subject-item {
  cursor: pointer;
  transition: all 0.2s;
}

.subject-item:hover {
  transform: translateY(-1px);
}

.feed {
  min-height: 200px;
}

.material-card {
  margin-bottom: 14px;
  border-radius: 12px;
  cursor: pointer;
  transition: all 0.25s;
}

.material-card:hover {
  transform: translateY(-2px);
  box-shadow: 0 8px 24px rgba(103, 194, 58, 0.12) !important;
}

.material-card :deep(.el-card__body) {
  display: flex;
  gap: 16px;
}

.material-icon {
  font-size: 40px;
  width: 60px;
  height: 60px;
  display: flex;
  align-items: center;
  justify-content: center;
  background: linear-gradient(135deg, #f0f9eb, #e1f3d8);
  border-radius: 12px;
  flex-shrink: 0;
}

.material-body {
  flex: 1;
  min-width: 0;
}

.material-head {
  display: flex;
  align-items: center;
  gap: 8px;
  margin-bottom: 6px;
}

.meta {
  margin-left: auto;
  color: #a8abb2;
  font-size: 12px;
}

.material-title {
  font-size: 16px;
  color: #303133;
  margin-bottom: 4px;
}

.material-desc {
  color: #606266;
  font-size: 13px;
  line-height: 1.6;
  display: -webkit-box;
  -webkit-line-clamp: 2;
  -webkit-box-orient: vertical;
  overflow: hidden;
  margin-bottom: 6px;
}

.material-tags {
  display: flex;
  gap: 6px;
  margin-bottom: 8px;
  flex-wrap: wrap;
}

.tag {
  font-size: 11px;
}

.material-stats {
  display: flex;
  gap: 16px;
  color: #909399;
  font-size: 12px;
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
  box-shadow: 0 2px 12px rgba(0, 0, 0, 0.06);
}

.map-header {
  margin-bottom: 8px;
}

.map-title {
  font-size: 15px;
  font-weight: 600;
  color: #303133;
}

.tip-card {
  border-radius: 12px;
}

.tip-title {
  font-weight: 600;
  margin-bottom: 8px;
  color: #303133;
}

.tip-card p {
  font-size: 13px;
  color: #606266;
  line-height: 1.8;
  margin: 0;
}

@media (max-width: 992px) {
  .page-layout {
    flex-direction: column;
  }
  .right-panel {
    width: 100%;
    position: static;
  }
}
</style>
