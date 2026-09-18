<script setup>
// 详情页（归属：前端 B）——内容详情 + 评论区
// 未登录用户可浏览，发表评论会被引导到登录页
// 已加固：加载中显示骨架、接口失败显示错误+重试，不再出现空白页
import { onMounted, onUnmounted, ref, nextTick } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { ElMessage, ElMessageBox } from 'element-plus'
import * as postApi from '@/api/post'
import * as socialApi from '@/api/social'
import { TYPE_MAP, formatTime } from '@/api/const'
import { useUserStore } from '@/stores/user'

const route = useRoute()
const router = useRouter()
const store = useUserStore()

const contentId = Number(route.params.id)
const content = ref(null)
const comments = ref([])
const commentTotal = ref(0)
const commentText = ref('')
const sending = ref(false)
const replyTo = ref(null) // 当前回复的对象 { id, name }，null=普通评论
const loading = ref(true)
const loadFailed = ref(false)
const showBackTop = ref(false) // 回到顶部按钮显隐

async function loadDetail() {
  try {
    content.value = await postApi.getContent(contentId)
    loadFailed.value = false
  } catch (e) {
    // 接口失败：保留页面结构，展示错误与重试按钮，绝不静默空白
    loadFailed.value = true
    content.value = null
  }
}

async function loadComments() {
  try {
    const data = await postApi.listComments(contentId)
    // 接口返回 { total, items }，必须取 items 数组（直接赋对象会导致 v-for 崩溃）
    comments.value = Array.isArray(data) ? data : (data?.items || [])
    commentTotal.value = data?.total ?? comments.value.length
  } catch (e) {
    // 评论加载失败不阻塞页面，置空即可
    comments.value = []
    commentTotal.value = 0
  }
}

async function loadAll() {
  loading.value = true
  loadFailed.value = false
  await Promise.all([loadDetail(), loadComments()])
  loading.value = false
}

// 帖子带经纬度时展示「地图导航」入口（规划书 5-2：详情页导航按钮触发地图跳转定位）
// 契约：携带坐标跳转到校园地图页（首页），地图组件读取 route.query 完成定位高亮。
function toMapNav() {
  router.push({
    path: '/map',
    query: {
      navLng: content.value.longitude,
      navLat: content.value.latitude,
      navTitle: content.value.title
    }
  })
}

// ===== 分享功能（前端 B）=====
// 优先调用 Web Share API（移动端原生分享），不支持则复制链接到剪贴板
async function onShare() {
  const url = window.location.href
  const shareData = { title: content.value?.title || '校园内容', text: content.value?.title || '', url }
  try {
    if (navigator.share) {
      await navigator.share(shareData)
      return
    }
  } catch {
    // 用户取消分享，不报错
  }
  // 降级：复制链接到剪贴板
  try {
    await navigator.clipboard.writeText(url)
    ElMessage.success('链接已复制到剪贴板，快去分享吧～')
  } catch {
    // 剪贴板权限不足时用 textarea 兜底
    const ta = document.createElement('textarea')
    ta.value = url
    ta.style.position = 'fixed'
    ta.style.opacity = '0'
    document.body.appendChild(ta)
    ta.select()
    try {
      document.execCommand('copy')
      ElMessage.success('链接已复制到剪贴板，快去分享吧～')
    } catch {
      ElMessage.info(`分享链接：${url}`)
    }
    document.body.removeChild(ta)
  }
}

// 楼层回复（纯前端方案：@前缀+UI提示，不需后端改）
function setReply(c) {
  replyTo.value = { id: c.id, name: c.author_name }
  // 自动聚焦评论框
  nextTick(() => {
    document.querySelector('.comment-input textarea')?.focus()
  })
}

function cancelReply() {
  replyTo.value = null
}

// 解析评论 body 中的 @前缀，返回 { replyName, text }
function parseReply(body) {
  if (!body) return { replyName: null, text: '' }
  const m = body.match(/^@(.+?)\s(.+)/s)
  return m ? { replyName: m[1], text: m[2] } : { replyName: null, text: body }
}

async function sendComment() {
  if (!store.isLoggedIn) {
    ElMessage.warning('请先登录后再评论')
    router.push({ path: '/login', query: { redirect: route.fullPath } })
    return
  }
  const text = commentText.value.trim()
  if (!text) return
  // 回复模式：body 前面加 @被回复人 前缀
  const payload = replyTo.value ? `@${replyTo.value.name} ${text}` : text
  sending.value = true
  try {
    await postApi.createComment(contentId, payload)
    commentText.value = ''
    replyTo.value = null
    ElMessage.success('评论成功')
    await loadComments()
  } catch (e) {
    // request.js 已弹错误提示
  } finally {
    sending.value = false
  }
}

// 删除自己的评论（仅本人可见删除按钮）
const deletingId = ref(0)
async function removeComment(c) {
  deletingId.value = c.id
  try {
    await postApi.deleteComment(contentId, c.id)
    ElMessage.success('评论已删除')
    await loadComments()
  } catch (e) {
    // request.js 已弹错误提示
  } finally {
    deletingId.value = 0
  }
}

// ===== 点赞 / 收藏（真实对接后端 social 接口） =====
const liked = ref(false)
const favorited = ref(false)
const liking = ref(false)
const favoriting = ref(false)

// 登录后拉取当前用户对本文的点赞/收藏状态
async function loadSocialState() {
  if (!store.isLoggedIn) return
  try {
    const [l, f] = await Promise.all([
      socialApi.checkLike(contentId),
      socialApi.checkFavorite(contentId)
    ])
    liked.value = !!l?.liked
    favorited.value = !!f?.favorited
  } catch {
    // 状态拉取失败不阻塞页面
  }
}

async function toggleLike() {
  if (!store.isLoggedIn) {
    ElMessage.warning('请先登录后再点赞')
    router.push({ path: '/login', query: { redirect: route.fullPath } })
    return
  }
  liking.value = true
  try {
    const d = await socialApi.toggleLike(contentId)
    liked.value = !!d?.liked
    if (content.value) content.value.like_count = d?.like_count ?? content.value.like_count
    ElMessage.success(d?.liked ? '点赞成功' : '已取消点赞')
  } catch {
    ElMessage.error('操作失败，请稍后重试')
  } finally {
    liking.value = false
  }
}

async function toggleFavorite() {
  if (!store.isLoggedIn) {
    ElMessage.warning('请先登录后再收藏')
    router.push({ path: '/login', query: { redirect: route.fullPath } })
    return
  }
  favoriting.value = true
  try {
    const d = await socialApi.toggleFavorite(contentId)
    favorited.value = !!d?.favorited
    ElMessage.success(d?.favorited ? '收藏成功' : '已取消收藏')
  } catch {
    ElMessage.error('操作失败，请稍后重试')
  } finally {
    favoriting.value = false
  }
}

// 滚动监听：超过 300px 显示回到顶部按钮
function onScroll() {
  showBackTop.value = window.scrollY > 300
}

function backToTop() {
  window.scrollTo({ top: 0, behavior: 'smooth' })
}

onMounted(async () => {
  await loadAll()
  loadSocialState()
  window.addEventListener('scroll', onScroll, { passive: true })
})

onUnmounted(() => {
  window.removeEventListener('scroll', onScroll)
})
</script>

<template>
  <div class="page-container">
    <!-- 加载中：骨架占位，避免白屏 -->
    <div v-if="loading" v-loading="true" class="loading-wrap">
      <el-skeleton :rows="6" animated style="max-width: 860px; margin: 0 auto" />
    </div>

    <!-- 加载失败：错误提示 + 重试 -->
    <div v-else-if="loadFailed || !content" class="error-wrap">
      <el-result icon="warning" title="内容加载失败" sub-title="网络可能有波动，请点击重试">
        <template #extra>
          <el-button type="primary" @click="loadAll">重新加载</el-button>
          <el-button @click="router.push('/')">返回首页</el-button>
        </template>
      </el-result>
    </div>

    <!-- 正常内容 -->
    <template v-else>
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

        <!-- 位置信息：有地点名或坐标时展示，可跳首页地图查看 -->
        <div v-if="content.location_name || (content.longitude != null && content.latitude != null)" class="loc-line">
          <span class="loc-pin">📍</span>
          <span class="loc-text">{{ content.location_name || ('经度 ' + content.longitude + '，纬度 ' + content.latitude) }}</span>
          <el-button size="small" text type="primary" @click="toMapNav">查看地图 →</el-button>
        </div>

        <!-- 点赞 / 收藏操作条 -->
        <div class="action-bar">
          <el-button
            :type="liked ? 'danger' : 'default'"
            round
            :loading="liking"
            @click="toggleLike"
          >
            {{ liked ? '❤️ 已赞' : '🤍 点赞' }} {{ content.like_count || 0 }}
          </el-button>
          <el-button
            :type="favorited ? 'warning' : 'default'"
            round
            :loading="favoriting"
            @click="toggleFavorite"
          >
            {{ favorited ? '⭐ 已收藏' : '☆ 收藏' }}
          </el-button>
          <el-button round @click="onShare">🔗 分享</el-button>
        </div>
      </el-card>

      <el-card shadow="never" class="comment-card">
        <template #header>评论（{{ commentTotal }}）</template>

        <div class="comment-input">
          <!-- 回复提示条：显示当前在回复谁 -->
          <div v-if="replyTo" class="reply-bar">
            <span>回复 @{{ replyTo.name }}：</span>
            <el-button text size="small" @click="cancelReply">取消回复</el-button>
          </div>
          <el-input
            v-model="commentText"
            type="textarea"
            :rows="2"
            maxlength="500"
            :placeholder="replyTo ? `回复 @${replyTo.name}…` : '友善评论，理性交流……'"
          />
          <div class="input-actions">
            <el-button type="primary" :loading="sending" @click="sendComment">发表评论</el-button>
          </div>
        </div>

        <el-empty v-if="!comments.length" description="还没有评论，来抢沙发～" :image-size="80" />
        <div v-for="c in comments" :key="c.id" class="comment-item">
          <div class="avatar">{{ (c.author_name || "?") .slice(0, 1) }}</div>
          <div class="comment-main">
            <div class="who">
              <span class="nick">{{ c.author_name }}</span>
              <span class="time">{{ formatTime(c.created_at) }}</span>
              <el-button
                v-if="c.is_author"
                size="small"
                text
                type="danger"
                :loading="deletingId === c.id"
                class="del-comment"
                @click="removeComment(c)"
              >
                删除
              </el-button>
              <el-button
                v-if="store.isLoggedIn"
                size="small"
                text
                type="primary"
                class="reply-btn"
                @click="setReply(c)"
              >
                回复
              </el-button>
            </div>
            <!-- 回复显示：@前缀高亮为标签 -->
            <div class="text">
              <span v-if="parseReply(c.body).replyName" class="reply-tag">@{{ parseReply(c.body).replyName }}</span>
              {{ parseReply(c.body).text }}
            </div>
          </div>
        </div>
      </el-card>
    </template>

    <!-- 回到顶部悬浮按钮（滚动超过 300px 显示） -->
    <transition name="fade">
      <div v-if="showBackTop" class="back-top" @click="backToTop" title="回到顶部">
        ↑
      </div>
    </transition>
  </div>
</template>

<style scoped>
.loading-wrap {
  min-height: 300px;
  padding: 40px 20px;
}

.error-wrap {
  min-height: 400px;
  display: flex;
  align-items: center;
  justify-content: center;
}

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

.loc-line {
  margin-top: 14px;
  display: flex;
  align-items: center;
  gap: 6px;
  background: #f0f7ff;
  border-radius: 8px;
  padding: 8px 12px;
}

.loc-pin {
  font-size: 14px;
}

.loc-text {
  font-size: 13px;
  color: #1d6df0;
  flex: 1;
  min-width: 0;
}

.nav-line {
  margin-top: 14px;
  display: flex;
  align-items: center;
  gap: 10px;
}

.social-bar {
  margin-top: 14px;
  display: flex;
  align-items: center;
  gap: 4px;
  flex-wrap: wrap;
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

.action-bar {
  margin-top: 14px;
  display: flex;
  gap: 10px;
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

.del-comment {
  margin-left: auto;
}

.reply-btn {
  margin-left: 4px;
}

.reply-bar {
  display: flex;
  align-items: center;
  justify-content: space-between;
  margin-bottom: 6px;
  padding: 4px 12px;
  background: #f0f7ff;
  border-radius: 6px;
  font-size: 13px;
  color: #409eff;
}

.reply-tag {
  color: #409eff;
  font-weight: 600;
  margin-right: 4px;
}

.text {
  margin-top: 4px;
  color: #4b4b4b;
  font-size: 14px;
  line-height: 1.6;
  white-space: pre-wrap;
  word-break: break-word;
}

/* 回到顶部悬浮按钮 */
.back-top {
  position: fixed;
  right: 32px;
  bottom: 80px;
  width: 44px;
  height: 44px;
  line-height: 44px;
  text-align: center;
  background: #fff;
  border: 1px solid #e4e7ed;
  border-radius: 50%;
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.12);
  cursor: pointer;
  font-size: 20px;
  color: #409eff;
  z-index: 100;
  transition: transform 0.2s;
}

.back-top:hover {
  transform: scale(1.1);
}

.fade-enter-active,
.fade-leave-active {
  transition: opacity 0.3s;
}

.fade-enter-from,
.fade-leave-to {
  opacity: 0;
}
</style>
