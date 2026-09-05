<script setup>
// 用户主页（归属：前端 C）——/user/profile/:id，用户信息 + 统计 + 帖子/关注/粉丝 Tab
import { onMounted, ref, computed, watch } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { getMockUserProfile, getMockUserPosts, getMockFollowers, getMockFollowing } from '@/utils/mockData'
import { formatTime } from '@/api/const'
import { useUserStore } from '@/stores/user'

const route = useRoute()
const router = useRouter()
const store = useUserStore()

const userId = computed(() => Number(route.params.id))
const user = ref(null)
const posts = ref([])
const followers = ref([])
const following = ref([])
const activeTab = ref('posts')
const isFollowing = ref(false)

const isMe = computed(() => store.userInfo?.id === userId.value)

async function loadData() {
  // mock 数据
  user.value = getMockUserProfile(userId.value)
  posts.value = getMockUserPosts(userId.value)
  followers.value = getMockFollowers(userId.value)
  following.value = getMockFollowing(userId.value)
}

function toggleFollow() {
  isFollowing.value = !isFollowing.value
}

function toPostDetail(id) {
  router.push(`/content/${id}`)
}

function goToUserProfile(id) {
  router.push(`/user/profile/${id}`)
}

watch(() => route.params.id, () => {
  loadData()
})

onMounted(loadData)
</script>

<template>
  <div class="user-profile-page" v-if="user">
    <!-- 用户信息头部 -->
    <el-card shadow="never" class="header-card">
      <div class="user-header">
        <el-avatar :size="90" class="user-avatar">{{ user.nickname.slice(0, 1) }}</el-avatar>
        <div class="user-info">
          <div class="name-row">
            <h2 class="nickname">{{ user.nickname }}</h2>
            <el-tag v-if="isMe" type="info" size="small">这是我</el-tag>
          </div>
          <p class="bio">{{ user.bio }}</p>
          <div class="meta-row">
            <span v-if="user.major">🎓 {{ user.major }}</span>
            <span v-if="user.grade">📚 {{ user.grade }}</span>
            <span>📅 加入于 {{ formatTime(user.created_at).slice(0, 10) }}</span>
          </div>
          <div class="stats-row">
            <div class="stat" @click="activeTab = 'posts'">
              <span class="num">{{ user.post_count }}</span>
              <span class="label">帖子</span>
            </div>
            <div class="stat" @click="activeTab = 'following'">
              <span class="num">{{ user.following_count }}</span>
              <span class="label">关注</span>
            </div>
            <div class="stat" @click="activeTab = 'followers'">
              <span class="num">{{ user.follower_count }}</span>
              <span class="label">粉丝</span>
            </div>
            <div class="stat">
              <span class="num">{{ user.likes_received }}</span>
              <span class="label">获赞</span>
            </div>
          </div>
        </div>
        <div class="actions" v-if="!isMe">
          <el-button :type="isFollowing ? 'default' : 'primary'" @click="toggleFollow">
            {{ isFollowing ? '已关注' : '+ 关注' }}
          </el-button>
          <el-button>💬 私信</el-button>
        </div>
      </div>
    </el-card>

    <!-- Tab 内容 -->
    <el-card shadow="never" class="content-card">
      <el-tabs v-model="activeTab">
        <!-- 帖子 Tab -->
        <el-tab-pane :label="`📝 帖子 (${posts.length})`" name="posts">
          <div class="posts-list">
            <el-empty v-if="!posts.length" description="暂无帖子" :image-size="100" />
            <el-card
              v-for="p in posts"
              :key="p.id"
              class="post-item"
              shadow="hover"
              @click="toPostDetail(p.id)"
            >
              <h4 class="post-title">{{ p.title }}</h4>
              <p class="post-summary">{{ p.body }}</p>
              <div class="post-meta">
                <span>{{ formatTime(p.created_at) }}</span>
              </div>
            </el-card>
          </div>
        </el-tab-pane>

        <!-- 关注 Tab -->
        <el-tab-pane :label="`👥 关注 (${following.length})`" name="following">
          <div class="user-list">
            <el-empty v-if="!following.length" description="暂无关注" :image-size="100" />
            <div v-for="u in following" :key="u.id" class="user-item" @click="goToUserProfile(u.id)">
              <el-avatar :size="48">{{ u.nickname.slice(0, 1) }}</el-avatar>
              <div class="user-item-info">
                <div class="user-item-name">{{ u.nickname }}</div>
                <div class="user-item-bio">{{ u.bio || '暂无简介' }}</div>
              </div>
            </div>
          </div>
        </el-tab-pane>

        <!-- 粉丝 Tab -->
        <el-tab-pane :label="`❤️ 粉丝 (${followers.length})`" name="followers">
          <div class="user-list">
            <el-empty v-if="!followers.length" description="暂无粉丝" :image-size="100" />
            <div v-for="u in followers" :key="u.id" class="user-item" @click="goToUserProfile(u.id)">
              <el-avatar :size="48">{{ u.nickname.slice(0, 1) }}</el-avatar>
              <div class="user-item-info">
                <div class="user-item-name">{{ u.nickname }}</div>
                <div class="user-item-bio">{{ u.bio || '暂无简介' }}</div>
              </div>
            </div>
          </div>
        </el-tab-pane>
      </el-tabs>
    </el-card>
  </div>
</template>

<style scoped>
.user-profile-page {
  max-width: 900px;
  margin: 0 auto;
  padding: 20px;
}

.header-card {
  border-radius: 12px;
  margin-bottom: 16px;
  background: linear-gradient(135deg, #1d6df0 0%, #4facfe 100%);
  border: none;
}

.header-card :deep(.el-card__body) {
  padding: 28px;
}

.user-header {
  display: flex;
  align-items: flex-start;
  gap: 24px;
}

.user-avatar {
  background: #fff;
  color: #1d6df0;
  font-size: 36px;
  font-weight: 700;
  flex-shrink: 0;
  border: 3px solid rgba(255,255,255,0.3);
}

.user-info {
  flex: 1;
  min-width: 0;
}

.name-row {
  display: flex;
  align-items: center;
  gap: 10px;
  margin-bottom: 6px;
}

.nickname {
  color: #fff;
  font-size: 24px;
  margin: 0;
}

.bio {
  color: rgba(255,255,255,0.85);
  font-size: 14px;
  margin: 0 0 10px 0;
}

.meta-row {
  display: flex;
  gap: 16px;
  color: rgba(255,255,255,0.7);
  font-size: 12px;
  margin-bottom: 14px;
}

.stats-row {
  display: flex;
  gap: 28px;
}

.stat {
  display: flex;
  flex-direction: column;
  cursor: pointer;
}

.stat .num {
  font-size: 20px;
  font-weight: 700;
  color: #fff;
}

.stat .label {
  font-size: 12px;
  color: rgba(255,255,255,0.7);
}

.actions {
  display: flex;
  flex-direction: column;
  gap: 8px;
  flex-shrink: 0;
}

.content-card {
  border-radius: 12px;
}

.posts-list {
  min-height: 200px;
}

.post-item {
  margin-bottom: 12px;
  border-radius: 10px;
  cursor: pointer;
  transition: all 0.2s;
}

.post-item:hover {
  transform: translateY(-2px);
  box-shadow: 0 4px 16px rgba(29,109,240,0.1) !important;
}

.post-title {
  font-size: 15px;
  color: #303133;
  margin: 0 0 6px 0;
}

.post-summary {
  font-size: 13px;
  color: #606266;
  line-height: 1.6;
  margin: 0 0 8px 0;
  display: -webkit-box;
  -webkit-line-clamp: 2;
  -webkit-box-orient: vertical;
  overflow: hidden;
}

.post-meta {
  font-size: 12px;
  color: #a8abb2;
}

.user-list {
  min-height: 200px;
}

.user-item {
  display: flex;
  align-items: center;
  gap: 14px;
  padding: 14px;
  border-radius: 10px;
  background: #f5f7fa;
  margin-bottom: 10px;
  cursor: pointer;
  transition: all 0.2s;
}

.user-item:hover {
  background: #ecf5ff;
}

.user-item-info {
  flex: 1;
}

.user-item-name {
  font-size: 15px;
  font-weight: 600;
  color: #303133;
}

.user-item-bio {
  font-size: 12px;
  color: #909399;
  margin-top: 2px;
}
</style>
