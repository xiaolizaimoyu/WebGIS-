<script setup>
// 详情页（归属：前端 B）——内容详情 + 评论区
// 未登录用户可浏览，发表评论会被引导到登录页
// TODO(前端B)：点赞/收藏、回复楼中楼、评论时间轴美化等扩展点
import { onMounted, ref } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { ElMessage } from 'element-plus'
import * as postApi from '@/api/post'
import { TYPE_MAP, formatTime } from '@/api/const'
import { useUserStore } from '@/stores/user'

const route = useRoute()
const router = useRouter()
const store = useUserStore()

const contentId = Number(route.params.id)
const content = ref(null)
const comments = ref([])
const commentText = ref('')
const sending = ref(false)

async function loadDetail() {
  content.value = await postApi.getContent(contentId)
}

async function loadComments() {
  comments.value = await postApi.listComments(contentId)
}

// 帖子带经纬度时展示「地图导航」入口（规划书 5-2：详情页导航按钮触发地图跳转定位）
// 契约：携带坐标跳转到首页，前端 A 的地图组件读取 route.query 完成定位 / 模拟导航；
// 地图组件未就绪时仅回到首页，不会报错。
function toMapNav() {
  router.push({
    path: '/',
    query: {
      navLng: content.value.longitude,
      navLat: content.value.latitude,
      navTitle: content.value.title
    }
  })
}

async function sendComment() {
  if (!store.isLoggedIn) {
    ElMessage.warning('请先登录后再评论')
    router.push({ path: '/login', query: { redirect: route.fullPath } })
    return
  }
  const text = commentText.value.trim()
  if (!text) return
  sending.value = true
  try {
    await postApi.createComment(contentId, text)
    commentText.value = ''
    ElMessage.success('评论成功')
    await loadComments()
  } finally {
    sending.value = false
  }
}

onMounted(() => {
  loadDetail()
  loadComments()
})
</script>

<template>
  <div class="page-container" v-if="content">
    <el-card shadow="never" class="detail-card">
      <div class="head">
        <el-tag :type="TYPE_MAP[content.type]?.tagType || 'info'" size="small">
          {{ TYPE_MAP[content.type]?.label || content.type }}
        </el-tag>
        <span v-if="content.category" class="category">· {{ content.category }}</span>
        <span class="meta">
          {{ content.author_name }} 发布于 {{ formatTime(content.created_at) }}
        </span>
      </div>

      <h1 class="title">{{ content.title }}</h1>
      <div class="body">{{ content.body }}</div>

      <div v-if="content.images && content.images.length" class="gallery">
        <el-image
          v-for="(img, i) in content.images"
          :key="i"
          :src="img"
          :preview-src-list="content.images"
          :initial-index="i"
          fit="contain"
          preview-teleported
          class="gallery-img"
        />
      </div>
    </el-card>

    <el-card shadow="never" class="comment-card">
      <template #header>评论（{{ comments.length }}）</template>

      <div class="comment-input">
        <el-input
          v-model="commentText"
          type="textarea"
          :rows="2"
          maxlength="500"
          placeholder="友善评论，理性交流……"
        />
        <div class="input-actions">
          <el-button type="primary" :loading="sending" @click="sendComment">发表评论</el-button>
        </div>
      </div>

      <el-empty v-if="!comments.length" description="还没有评论，来抢沙发～" :image-size="80" />
      <div v-for="c in comments" :key="c.id" class="comment-item">
        <div class="avatar">{{ c.author_name.slice(0, 1) }}</div>
        <div class="comment-main">
          <div class="who">
            <span class="nick">{{ c.author_name }}</span>
            <span class="time">{{ formatTime(c.created_at) }}</span>
          </div>
          <div class="text">{{ c.body }}</div>
        </div>
      </div>
    </el-card>
  </div>
</template>

<style scoped>
.detail-card {
  border-radius: 10px;
  margin-bottom: 16px;
}

.head {
  display: flex;
  align-items: center;
  gap: 8px;
}

.category {
  color: #909399;
  font-size: 13px;
}

.meta {
  margin-left: auto;
  color: #a8abb2;
  font-size: 12px;
}

.title {
  font-size: 24px;
  margin: 12px 0;
  color: #303133;
}

.body {
  color: #4b4b4b;
  font-size: 15px;
  line-height: 1.9;
  white-space: pre-wrap;
  word-break: break-word;
}

.nav-line {
  margin-top: 14px;
  display: flex;
  align-items: center;
  gap: 10px;
}

.gallery {
  margin-top: 16px;
  display: flex;
  flex-wrap: wrap;
  gap: 10px;
}

.gallery-img {
  width: 220px;
  height: 220px;
  border-radius: 8px;
  border: 1px solid #ebeef5;
}

.comment-card {
  border-radius: 10px;
}

.comment-input {
  margin-bottom: 12px;
}

.input-actions {
  margin-top: 8px;
  text-align: right;
}

.comment-item {
  display: flex;
  gap: 12px;
  padding: 14px 0;
  border-top: 1px solid #f0f2f5;
}

.avatar {
  width: 38px;
  height: 38px;
  border-radius: 50%;
  background: #1d6df0;
  color: #fff;
  display: flex;
  align-items: center;
  justify-content: center;
  flex-shrink: 0;
  font-size: 16px;
}

.comment-main {
  flex: 1;
  min-width: 0;
}

.who {
  display: flex;
  align-items: baseline;
  gap: 10px;
}

.nick {
  font-weight: 600;
  color: #303133;
}

.time {
  color: #a8abb2;
  font-size: 12px;
}

.text {
  margin-top: 4px;
  color: #4b4b4b;
  font-size: 14px;
  line-height: 1.6;
  white-space: pre-wrap;
  word-break: break-word;
}
</style>
