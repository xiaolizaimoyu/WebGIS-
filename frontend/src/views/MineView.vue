<script setup>
// 我的发布页（归属：前端 C）
import { onMounted, ref } from 'vue'
import { useRouter } from 'vue-router'
import * as postApi from '@/api/post'
import { TYPE_MAP, formatTime } from '@/api/const'
import { getMockContents } from '@/utils/mockData'
import { useUserStore } from '@/stores/user'

const router = useRouter()
const store = useUserStore()
const list = ref([])
const loading = ref(false)

async function load() {
  loading.value = true
  try {
    const data = await postApi.listContents({ page: 1, size: 50 })
    list.value = (data.items || data || []).filter((c) => c.author_name === store.userInfo?.nickname)
  } catch {
    list.value = getMockContents().slice(0, 2)
  } finally {
    loading.value = false
  }
}

function toDetail(id) {
  router.push(`/content/${id}`)
}

onMounted(load)
</script>

<template>
  <div class="page-container">
    <el-card shadow="never" class="header-card">
      <div class="header-row">
        <h2>📝 我的发布</h2>
        <el-button type="primary" @click="router.push('/publish')">＋ 发布新内容</el-button>
      </div>
    </el-card>

    <div v-loading="loading" class="feed">
      <el-card
        v-for="c in list"
        :key="c.id"
        class="item-card"
        shadow="hover"
        @click="toDetail(c.id)"
      >
        <div class="badge">
          <el-tag :type="TYPE_MAP[c.type]?.tagType || 'info'" size="small">
            {{ TYPE_MAP[c.type]?.label || c.type }}
          </el-tag>
          <span v-if="c.category" class="category">· {{ c.category }}</span>
        </div>
        <h3 class="title">{{ c.title }}</h3>
        <p class="summary">{{ c.body }}</p>
        <div class="meta">
          <span>发布于 {{ formatTime(c.created_at) }}</span>
        </div>
      </el-card>
      <el-empty v-if="!loading && !list.length" description="还没有发布内容" />
    </div>
  </div>
</template>

<style scoped>
.page-container { max-width: 800px; margin: 0 auto; padding: 20px; }
.header-card { border-radius: 12px; margin-bottom: 16px; }
.header-row { display: flex; justify-content: space-between; align-items: center; }
.header-row h2 { margin: 0; font-size: 20px; color: #303133; }
.feed { min-height: 200px; }
.item-card { margin-bottom: 14px; border-radius: 12px; cursor: pointer; transition: all 0.2s; }
.item-card:hover { transform: translateY(-2px); box-shadow: 0 4px 16px rgba(0,0,0,0.08) !important; }
.badge { display: flex; align-items: center; gap: 6px; margin-bottom: 8px; }
.category { color: #909399; font-size: 13px; }
.title { font-size: 16px; color: #303133; margin: 0 0 6px 0; }
.summary { color: #606266; font-size: 14px; line-height: 1.6; margin: 0 0 8px 0; display: -webkit-box; -webkit-line-clamp: 2; -webkit-box-orient: vertical; overflow: hidden; }
.meta { color: #a8abb2; font-size: 12px; }
</style>
