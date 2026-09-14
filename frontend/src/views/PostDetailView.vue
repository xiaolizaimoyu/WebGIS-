<script setup>
import { computed, onMounted, ref, watch } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import * as postApi from '@/api/post'
import { TYPE_MAP, formatTime } from '@/api/const'

const route = useRoute()
const router = useRouter()

const categories = [
  { value: 'all', label: '全部帖子', icon: '📌' },
  { value: 'meeting', label: '校园会议', icon: '📅' },
  { value: 'news', label: '校园动态', icon: '📰' },
  { value: 'food', label: '美食分享', icon: '🍜' },
  { value: 'lost', label: '失物招领', icon: '🔍' }
]

const list = ref([])
const loading = ref(false)
const total = ref(0)
const page = ref(1)
const pageSize = 8

const selectedType = computed(() => {
  const type = route.params.type || route.query.type || 'all'
  return TYPE_MAP[type] ? type : 'all'
})

const selectedTitle = computed(() => {
  const type = selectedType.value
  if (type === 'all') return '全部帖子'
  return TYPE_MAP[type]?.label || '帖子详情'
})

function goToCategory(type) {
  if (type === 'all') {
    router.push('/posts')
    return
  }
  router.push(`/posts/${type}`)
}

async function loadPosts() {
  loading.value = true
  try {
    const params = { page: page.value, size: pageSize }
    if (selectedType.value !== 'all') {
      params.type = selectedType.value
    }
    const data = await postApi.listContents(params)
    const items = Array.isArray(data) ? data : (data?.items || [])
    list.value = items
    total.value = data?.total ?? items.length
  } catch {
    list.value = []
    total.value = 0
  } finally {
    loading.value = false
  }
}

watch(
  () => route.params.type,
  () => {
    page.value = 1
    loadPosts()
  },
  { immediate: true }
)

watch(
  () => route.query.type,
  () => {
    page.value = 1
    loadPosts()
  }
)

onMounted(() => {
  loadPosts()
})

function goToDetail(id) {
  router.push(`/content/${id}`)
}
</script>

<template>
  <div class="posts-page">
    <div class="page-header">
      <div>
        <p class="eyebrow">校园交流</p>
        <h2>帖子详情</h2>
      </div>
      <el-button type="primary" round @click="router.push('/publish')">＋ 发布帖子</el-button>
    </div>

    <div class="category-grid">
      <button
        v-for="item in categories"
        :key="item.value"
        class="category-card"
        :class="{ active: selectedType === item.value }"
        @click="goToCategory(item.value)"
      >
        <span class="category-icon">{{ item.icon }}</span>
        <span class="category-label">{{ item.label }}</span>
      </button>
    </div>

    <div class="section-header">
      <h3>{{ selectedTitle }}</h3>
      <span>共 {{ total }} 条</span>
    </div>

    <div v-if="loading" class="loading-box">
      <el-skeleton :rows="5" animated />
    </div>

    <div v-else-if="!list.length" class="empty-box">
      <el-empty description="暂无该分类帖子，快来发布第一条吧" />
    </div>

    <div v-else class="post-list">
      <article v-for="item in list" :key="item.id" class="post-card" @click="goToDetail(item.id)">
        <div class="post-topline">
          <el-tag :type="TYPE_MAP[item.type]?.tagType || 'info'" size="small">
            {{ TYPE_MAP[item.type]?.label || item.type }}
          </el-tag>
          <span class="meta-time">{{ formatTime(item.created_at) }}</span>
        </div>

        <h4>{{ item.title }}</h4>
        <p>{{ item.body || '暂无内容简介' }}</p>

        <div class="post-bottomline">
          <span>作者：{{ item.author_name || '校园用户' }}</span>
          <span>查看详情 →</span>
        </div>
      </article>
    </div>
  </div>
</template>

<style scoped>
.posts-page {
  max-width: 1200px;
  margin: 18px auto 30px;
  padding: 0 18px;
}

.page-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  margin-bottom: 20px;
}

.eyebrow {
  margin: 0 0 4px;
  color: #5b8def;
  font-size: 12px;
  font-weight: 600;
  letter-spacing: 0.08em;
  text-transform: uppercase;
}

h2 {
  margin: 0;
  color: #1d2a36;
  font-size: 30px;
}

.category-grid {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(180px, 1fr));
  gap: 16px;
  margin-bottom: 26px;
}

.category-card {
  display: flex;
  align-items: center;
  gap: 12px;
  border: 1px solid #e4e7ed;
  background: linear-gradient(135deg, #ffffff 0%, #f6faff 100%);
  border-radius: 18px;
  min-height: 92px;
  padding: 18px 20px;
  cursor: pointer;
  transition: all 0.2s ease;
  text-align: left;
  color: #1f2d3d;
}

.category-card:hover,
.category-card.active {
  border-color: #7aa8ff;
  box-shadow: 0 10px 26px rgba(59, 130, 246, 0.12);
  transform: translateY(-2px);
}

.category-icon {
  width: 42px;
  height: 42px;
  display: inline-flex;
  align-items: center;
  justify-content: center;
  border-radius: 12px;
  background: #eaf2ff;
  font-size: 24px;
}

.category-label {
  font-size: 16px;
  font-weight: 600;
}

.section-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  margin: 20px 0 12px;
  padding-bottom: 12px;
  border-bottom: 1px solid #eef1f5;
}

.section-header h3 {
  margin: 0;
  font-size: 24px;
  color: #203041;
}

.section-header span {
  color: #7a8797;
  font-size: 13px;
}

.post-list {
  display: grid;
  gap: 16px;
}

.post-card {
  border: 1px solid #e9edf3;
  background: #fff;
  border-radius: 18px;
  padding: 18px 20px;
  cursor: pointer;
  transition: transform 0.2s ease, box-shadow 0.2s ease;
}

.post-card:hover {
  transform: translateY(-1px);
  box-shadow: 0 12px 24px rgba(16, 24, 40, 0.05);
}

.post-topline,
.post-bottomline {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 12px;
}

.meta-time {
  color: #86909c;
  font-size: 12px;
}

.post-card h4 {
  margin: 12px 0 10px;
  font-size: 24px;
  color: #1f2d3d;
}

.post-card p {
  margin: 0;
  color: #5d6b7a;
  line-height: 1.7;
  display: -webkit-box;
  -webkit-line-clamp: 2;
  -webkit-box-orient: vertical;
  overflow: hidden;
}

.post-bottomline {
  margin-top: 14px;
  color: #6b7a89;
  font-size: 13px;
}

.empty-box,
.loading-box {
  margin-top: 12px;
  background: #fff;
  border: 1px solid #ebedf0;
  border-radius: 18px;
  padding: 18px;
}

@media (max-width: 768px) {
  .page-header,
  .section-header,
  .post-topline,
  .post-bottomline {
    flex-direction: column;
    align-items: flex-start;
  }

  h2 {
    font-size: 24px;
  }
}
</style>
