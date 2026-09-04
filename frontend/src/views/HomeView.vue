<script setup>
// 首页信息流（归属：前端 B）
// TODO(前端B)：卡片样式美化、分页体验优化、分类图标、活动报名入口、广告子分类角标等扩展点
import { onMounted, ref } from 'vue'
import { useRouter } from 'vue-router'
import * as postApi from '@/api/post'
import { formatTime } from '@/api/const'
import { TYPE_MAP } from '@/api/typeMap' // B 扩展版：含美食分享 / 失物招领

const router = useRouter()

// 顶部 Tab：全部 + 六分类（value='all' 代表全部，请求时转 undefined）
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

async function load() {
  loading.value = true
  try {
    const data = await postApi.listContents({
      type: activeType.value === 'all' ? undefined : activeType.value,
      page: page.value,
      size: size.value
    })
    list.value = data.items
    total.value = data.total
  } finally {
    loading.value = false
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

onMounted(load)
</script>

<template>
  <div class="page-container">
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
</template>

<style scoped>
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
  display: flex;
}

.item-card .el-card__body {
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
</style>
