<script setup>
// 我的点赞 / 我的收藏（真实对接后端 /api/social）
import { onMounted, ref } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { ElMessage } from 'element-plus'
import * as socialApi from '@/api/social'
import { TYPE_MAP, formatTime } from '@/api/const'

const route = useRoute()
const router = useRouter()
const activeTab = ref(route.query.tab === 'favorites' ? 'favorites' : 'likes')
const likes = ref([])
const favorites = ref([])
const loading = ref(false)

const tabMap = {
  likes: { label: '我的点赞', empty: '还没有点赞过内容' },
  favorites: { label: '我的收藏', empty: '还没有收藏内容' }
}

async function load() {
  loading.value = true
  try {
    const [l, f] = await Promise.all([
      socialApi.myLikes({ page: 1, size: 50 }),
      socialApi.myFavorites({ page: 1, size: 50 })
    ])
    likes.value = l.items || []
    favorites.value = f.items || []
  } catch {
    ElMessage.error('加载失败，请稍后重试')
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
    <el-card shadow="never" class="social-card">
      <el-tabs v-model="activeTab">
        <el-tab-pane :label="`👍 我的点赞 (${likes.length})`" name="likes">
          <el-empty v-if="!likes.length" :description="tabMap.likes.empty" :image-size="100" />
          <div v-for="c in likes" :key="c.id" class="item" @click="toDetail(c.id)">
            <el-tag :type="TYPE_MAP[c.type]?.tagType || 'info'" size="small">
              {{ TYPE_MAP[c.type]?.label || c.type }}
            </el-tag>
            <div class="item-main">
              <div class="item-title">{{ c.title }}</div>
              <div class="item-summary">{{ c.summary }}</div>
              <div class="item-meta">点赞于 {{ formatTime(c.created_at) }}</div>
            </div>
          </div>
        </el-tab-pane>

        <el-tab-pane :label="`⭐ 我的收藏 (${favorites.length})`" name="favorites">
          <el-empty v-if="!favorites.length" :description="tabMap.favorites.empty" :image-size="100" />
          <div v-for="c in favorites" :key="c.id" class="item" @click="toDetail(c.id)">
            <el-tag :type="TYPE_MAP[c.type]?.tagType || 'info'" size="small">
              {{ TYPE_MAP[c.type]?.label || c.type }}
            </el-tag>
            <div class="item-main">
              <div class="item-title">{{ c.title }}</div>
              <div class="item-summary">{{ c.summary }}</div>
              <div class="item-meta">收藏于 {{ formatTime(c.created_at) }}</div>
            </div>
          </div>
        </el-tab-pane>
      </el-tabs>
    </el-card>
  </div>
</template>

<style scoped>
.page-container {
  max-width: 900px;
  margin: 0 auto;
  padding: 20px;
}

.social-card {
  border-radius: 12px;
}

.item {
  display: flex;
  gap: 12px;
  align-items: flex-start;
  padding: 14px 4px;
  border-bottom: 1px solid #f0f2f5;
  cursor: pointer;
  transition: background 0.2s;
}

.item:hover {
  background: #f7f9fc;
}

.item-main {
  flex: 1;
  min-width: 0;
}

.item-title {
  font-size: 15px;
  font-weight: 600;
  color: #303133;
}

.item-summary {
  font-size: 13px;
  color: #606266;
  margin-top: 4px;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.item-meta {
  font-size: 12px;
  color: #a8abb2;
  margin-top: 6px;
}
</style>
