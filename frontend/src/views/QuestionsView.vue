<script setup>
// 校园问答列表页（归属：前端 C）——左侧问答信息流 + 右侧地图
import { onMounted, ref, computed } from 'vue'
import { useRouter } from 'vue-router'
import * as questionApi from '@/api/question'
import { formatTime } from '@/api/const'
import { getMockQuestions } from '@/utils/mockData'
import MapComponent from '@/components/MapComponent.vue'
import WeatherWidget from '@/components/WeatherWidget.vue'

const router = useRouter()
const mapRef = ref(null)

const tags = ['全部', '高数', '编程', '考研', '生活', '求助', 'GIS', '英语']
const activeTag = ref('全部')
const keyword = ref('')
const list = ref([])
const total = ref(0)
const page = ref(1)
const size = ref(10)
const loading = ref(false)

async function load() {
  loading.value = true
  try {
    const data = await questionApi.listQuestions({
      tag: activeTag.value === '全部' ? undefined : activeTag.value,
      keyword: keyword.value || undefined,
      page: page.value,
      size: size.value
    })
    list.value = data.items || data || []
    total.value = data.total || list.value.length
  } catch {
    let mock = getMockQuestions()
    if (activeTag.value !== '全部') mock = mock.filter((q) => q.tag === activeTag.value)
    if (keyword.value) mock = mock.filter((q) => q.title.includes(keyword.value))
    list.value = mock
    total.value = mock.length
  } finally {
    loading.value = false
  }
}

function onTagChange(tag) {
  activeTag.value = tag
  page.value = 1
  load()
}

function onSearch() {
  page.value = 1
  load()
}

function toDetail(id) {
  router.push(`/question/${id}`)
}

// 右侧地图
const mapCenter = ref([116.397428, 39.90923])
const mapMarkers = computed(() => [])

onMounted(load)
</script>

<template>
  <div class="page-layout">
    <!-- 左侧：问答信息流 -->
    <div class="left-panel">
      <el-card shadow="never" class="filter-card">
        <div class="filter-row">
          <el-input
            v-model="keyword"
            placeholder="搜索问题..."
            clearable
            style="width: 260px"
            @keyup.enter="onSearch"
            @clear="onSearch"
          >
            <template #prefix>🔍</template>
          </el-input>
          <el-button type="primary" @click="router.push('/question/publish')">
            ＋ 我要提问
          </el-button>
        </div>
        <div class="tag-row">
          <el-tag
            v-for="tag in tags"
            :key="tag"
            :type="activeTag === tag ? 'primary' : 'info'"
            :effect="activeTag === tag ? 'dark' : 'plain'"
            class="tag-item"
            @click="onTagChange(tag)"
          >
            {{ tag }}
          </el-tag>
        </div>
      </el-card>

      <div v-loading="loading" class="feed">
        <el-card
          v-for="q in list"
          :key="q.id"
          class="question-card"
          shadow="hover"
          @click="toDetail(q.id)"
        >
          <div class="q-head">
            <el-tag size="small" type="warning">{{ q.tag }}</el-tag>
            <el-tag v-if="q.adopted" size="small" type="success" effect="dark">已解决</el-tag>
            <span class="q-meta">{{ q.author_name }} · {{ formatTime(q.created_at) }}</span>
          </div>
          <h3 class="q-title">{{ q.title }}</h3>
          <p class="q-summary">{{ q.body }}</p>
          <div class="q-stats">
            <span>👁 {{ q.views }} 浏览</span>
            <span>💬 {{ q.answer_count }} 回答</span>
          </div>
        </el-card>

        <el-empty v-if="!loading && !list.length" description="还没有问题，来提第一个吧" />
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

    <!-- 右侧：地图 + 天气 -->
    <div class="right-panel">
      <WeatherWidget city="北京" :use-mock="true" />
      <div class="map-wrapper">
        <div class="map-header">
          <span class="map-title">🗺️ 校园地图</span>
        </div>
        <MapComponent ref="mapRef" :center="mapCenter" :zoom="14" :markers="mapMarkers" height="360px" />
      </div>
      <el-card shadow="never" class="tip-card">
        <div class="tip-title">💡 问答小贴士</div>
        <p>· 提问时尽量描述清楚问题背景</p>
        <p>· 采纳满意回答可获得积分奖励</p>
        <p>· 回答他人问题也能赚积分哦</p>
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

.tag-row {
  display: flex;
  flex-wrap: wrap;
  gap: 8px;
}

.tag-item {
  cursor: pointer;
  transition: all 0.2s;
}

.tag-item:hover {
  transform: translateY(-1px);
}

.feed {
  min-height: 200px;
}

.question-card {
  margin-bottom: 14px;
  border-radius: 12px;
  cursor: pointer;
  transition: all 0.25s;
}

.question-card:hover {
  transform: translateY(-2px);
  box-shadow: 0 8px 24px rgba(29, 109, 240, 0.12) !important;
}

.q-head {
  display: flex;
  align-items: center;
  gap: 8px;
  margin-bottom: 8px;
}

.q-meta {
  margin-left: auto;
  color: #a8abb2;
  font-size: 12px;
}

.q-title {
  font-size: 17px;
  color: #303133;
  margin-bottom: 6px;
}

.q-summary {
  color: #606266;
  font-size: 14px;
  line-height: 1.6;
  display: -webkit-box;
  -webkit-line-clamp: 2;
  -webkit-box-orient: vertical;
  overflow: hidden;
}

.q-stats {
  margin-top: 10px;
  display: flex;
  gap: 16px;
  color: #909399;
  font-size: 13px;
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
