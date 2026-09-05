<script setup>
// 整体布局外壳（归属：前端 C）——顶部导航栏 + 主内容区
import { computed, onMounted, ref } from 'vue'
import { useRouter, useRoute } from 'vue-router'
import { ElMessage } from 'element-plus'
import { useUserStore } from '@/stores/user'
import { useNotificationStore } from '@/stores/notification'
import { formatTime } from '@/api/const'

const router = useRouter()
const route = useRoute()
const store = useUserStore()
const notificationStore = useNotificationStore()

const isLoggedIn = computed(() => store.isLoggedIn)
const avatarUrl = computed(() => store.userInfo?.avatar || '')
const avatarText = computed(() => (store.userInfo?.nickname || '?').slice(0, 1))
const unreadCount = computed(() => notificationStore.unreadCount)
const signStatus = computed(() => store.signStatus)
const totalPoints = computed(() => store.signStatus?.totalPoints || 0)
const continuousDays = computed(() => store.signStatus?.continuousDays || 0)
const signedToday = computed(() => store.signStatus?.signedToday || false)

// 通知下拉
const notifyVisible = ref(false)
const notifyList = computed(() => notificationStore.list.slice(0, 5))

// 导航菜单
const navMenus = [
  { path: '/', label: '首页', icon: '🏠' },
  { path: '/questions', label: '校园问答', icon: '❓' },
  { path: '/materials', label: '学习资料', icon: '📚' },
  { path: '/carpool', label: '组队拼车', icon: '🚗' },
  { path: '/lost-found', label: '失物招领', icon: '🔍' }
]

function isActive(path) {
  if (path === '/') return route.path === '/'
  return route.path.startsWith(path)
}

function onCommand(cmd) {
  if (cmd === 'profile') {
    router.push('/profile')
  } else if (cmd === 'user-home') {
    router.push(`/user/profile/${store.userInfo?.id || 1}`)
  } else if (cmd === 'mine') {
    router.push('/mine')
  } else if (cmd === 'logout') {
    store.logout()
    ElMessage.success('已退出登录')
    router.push('/')
  }
}

async function handleSign() {
  if (!isLoggedIn.value) {
    router.push('/login')
    return
  }
  if (signedToday.value) {
    ElMessage.info('今日已签到，明天再来吧')
    return
  }
  const result = await store.doSign()
  if (result) {
    ElMessage.success(`签到成功！获得 ${result.points} 积分，连续签到 ${result.continuousDays} 天`)
  }
}

function goToNotifications() {
  notifyVisible.value = false
  router.push('/notifications')
}

function handleNotifyClick(n) {
  notifyVisible.value = false
  if (n.related_type === 'question' && n.related_id) {
    router.push(`/question/${n.related_id}`)
  } else if (n.related_type === 'carpool' && n.related_id) {
    router.push(`/carpool/${n.related_id}`)
  } else {
    router.push('/notifications')
  }
  if (!n.read) notificationStore.markRead(n.id)
}

const notifyTypeIcon = {
  comment: '💬', like: '❤️', answer: '✏️', system: '🔔',
  carpool: '🚗', sign: '🎁', follow: '👥', default: '📩'
}

onMounted(() => {
  if (isLoggedIn.value) {
    store.fetchSignStatus()
    notificationStore.fetchUnreadCount()
    notificationStore.fetchList()
  }
})
</script>

<template>
  <el-container class="app-layout">
    <el-header class="app-header">
      <div class="header-inner">
        <router-link to="/" class="brand">🎓 校园活动交流平台</router-link>

        <!-- 导航菜单 -->
        <nav class="nav-menu">
          <router-link
            v-for="m in navMenus"
            :key="m.path"
            :to="m.path"
            class="nav-item"
            :class="{ active: isActive(m.path) }"
          >
            <span class="nav-icon">{{ m.icon }}</span>
            <span class="nav-label">{{ m.label }}</span>
          </router-link>
        </nav>

        <div class="spacer" />

        <!-- 签到按钮 -->
        <div v-if="isLoggedIn" class="sign-section" @click="handleSign">
          <div class="sign-btn" :class="{ signed: signedToday }">
            <span class="sign-icon">{{ signedToday ? '✅' : '📅' }}</span>
            <div class="sign-info">
              <span class="sign-text">{{ signedToday ? '已签到' : '签到' }}</span>
              <span class="sign-points">{{ totalPoints }}积分 · {{ continuousDays }}天</span>
            </div>
          </div>
        </div>

        <!-- 通知铃铛 -->
        <el-dropdown v-if="isLoggedIn" trigger="click" v-model:visible="notifyVisible" @command="() => {}">
          <div class="notify-bell">
            <el-badge :value="unreadCount" :hidden="unreadCount === 0" :max="99" class="bell-badge">
              <span class="bell-icon">🔔</span>
            </el-badge>
          </div>
          <template #dropdown>
            <el-dropdown-menu class="notify-dropdown">
              <div class="notify-header">
                <span>消息通知</span>
                <el-button text type="primary" size="small" @click.stop="goToNotifications">查看全部</el-button>
              </div>
              <el-empty v-if="!notifyList.length" description="暂无通知" :image-size="60" />
              <div
                v-for="n in notifyList"
                :key="n.id"
                class="notify-item"
                :class="{ unread: !n.read }"
                @click.stop="handleNotifyClick(n)"
              >
                <span class="notify-icon">{{ notifyTypeIcon[n.type] || '📩' }}</span>
                <div class="notify-content">
                  <div class="notify-title">{{ n.title }}</div>
                  <div class="notify-text">{{ n.content }}</div>
                  <div class="notify-time">{{ formatTime(n.created_at) }}</div>
                </div>
                <div v-if="!n.read" class="notify-dot"></div>
              </div>
            </el-dropdown-menu>
          </template>
        </el-dropdown>

        <!-- 发布按钮 -->
        <el-button v-if="isLoggedIn" type="primary" round class="publish-btn" @click="router.push('/publish')">
          ＋ 发布
        </el-button>

        <!-- 用户下拉菜单 -->
        <el-dropdown v-if="isLoggedIn" @command="onCommand">
          <span class="user-name">
            <el-avatar :size="30" :src="avatarUrl || undefined" class="nav-avatar">
              {{ avatarText }}
            </el-avatar>
            <span class="user-nick">{{ store.userInfo?.nickname }}</span>
            <span class="dropdown-arrow">▾</span>
          </span>
          <template #dropdown>
            <el-dropdown-menu>
              <el-dropdown-item command="profile">
                <span>👤 个人中心</span>
              </el-dropdown-item>
              <el-dropdown-item command="user-home">
                <span>🏠 我的主页</span>
              </el-dropdown-item>
              <el-dropdown-item command="mine">
                <span>📝 我的发布</span>
              </el-dropdown-item>
              <el-dropdown-item divided command="logout">
                <span>🚪 退出登录</span>
              </el-dropdown-item>
            </el-dropdown-menu>
          </template>
        </el-dropdown>

        <template v-else>
          <el-button @click="router.push('/login')">登录</el-button>
          <el-button type="primary" plain @click="router.push('/register')">注册</el-button>
        </template>
      </div>
    </el-header>

    <el-main class="app-main">
      <router-view />
    </el-main>
  </el-container>
</template>

<style scoped>
.app-layout {
  min-height: 100vh;
}

.app-header {
  background: linear-gradient(135deg, #ffffff 0%, #f8faff 100%);
  border-bottom: 1px solid #e4e7ed;
  position: sticky;
  top: 0;
  z-index: 100;
  box-shadow: 0 2px 12px rgba(0, 0, 0, 0.06);
  height: 64px !important;
}

.header-inner {
  max-width: 1440px;
  height: 100%;
  margin: 0 auto;
  display: flex;
  align-items: center;
  gap: 12px;
  padding: 0 20px;
}

.brand {
  font-size: 18px;
  font-weight: 700;
  background: linear-gradient(135deg, #1d6df0, #4facfe);
  -webkit-background-clip: text;
  -webkit-text-fill-color: transparent;
  background-clip: text;
  white-space: nowrap;
  flex-shrink: 0;
}

/* 导航菜单 */
.nav-menu {
  display: flex;
  align-items: center;
  gap: 4px;
  margin-left: 20px;
}

.nav-item {
  display: flex;
  align-items: center;
  gap: 4px;
  padding: 6px 12px;
  border-radius: 8px;
  font-size: 14px;
  color: #606266;
  transition: all 0.2s;
  white-space: nowrap;
}

.nav-item:hover {
  background: #ecf5ff;
  color: #1d6df0;
}

.nav-item.active {
  background: linear-gradient(135deg, #1d6df0, #4facfe);
  color: #fff;
  font-weight: 500;
}

.nav-icon {
  font-size: 14px;
}

.spacer {
  flex: 1;
}

/* 签到按钮 */
.sign-section {
  cursor: pointer;
}

.sign-btn {
  display: flex;
  align-items: center;
  gap: 8px;
  padding: 6px 14px;
  border-radius: 20px;
  background: linear-gradient(135deg, #ff9a56, #ff6b6b);
  color: #fff;
  transition: all 0.2s;
}

.sign-btn:hover {
  transform: translateY(-1px);
  box-shadow: 0 4px 12px rgba(255, 107, 107, 0.3);
}

.sign-btn.signed {
  background: linear-gradient(135deg, #67c23a, #85ce61);
}

.sign-icon {
  font-size: 16px;
}

.sign-info {
  display: flex;
  flex-direction: column;
  line-height: 1.2;
}

.sign-text {
  font-size: 12px;
  font-weight: 600;
}

.sign-points {
  font-size: 10px;
  opacity: 0.9;
}

/* 通知铃铛 */
.notify-bell {
  cursor: pointer;
  padding: 6px 10px;
  border-radius: 8px;
  transition: all 0.2s;
  position: relative;
}

.notify-bell:hover {
  background: #ecf5ff;
}

.bell-icon {
  font-size: 20px;
}

.bell-badge :deep(.el-badge__content) {
  top: 2px;
  right: -2px;
}

/* 通知下拉 */
.notify-dropdown {
  width: 360px;
  max-height: 420px;
  overflow-y: auto;
  padding: 0 !important;
}

.notify-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 12px 16px;
  border-bottom: 1px solid #f0f2f5;
  font-weight: 600;
  color: #303133;
  position: sticky;
  top: 0;
  background: #fff;
  z-index: 1;
}

.notify-item {
  display: flex;
  align-items: flex-start;
  gap: 10px;
  padding: 12px 16px;
  cursor: pointer;
  transition: all 0.2s;
  border-bottom: 1px solid #f5f7fa;
  position: relative;
}

.notify-item:hover {
  background: #f5f7fa;
}

.notify-item.unread {
  background: #f0f7ff;
}

.notify-icon {
  font-size: 22px;
  flex-shrink: 0;
  width: 36px;
  height: 36px;
  display: flex;
  align-items: center;
  justify-content: center;
  background: #f5f7fa;
  border-radius: 50%;
}

.notify-content {
  flex: 1;
  min-width: 0;
}

.notify-title {
  font-size: 13px;
  font-weight: 600;
  color: #303133;
  margin-bottom: 2px;
}

.notify-text {
  font-size: 12px;
  color: #606266;
  line-height: 1.4;
  overflow: hidden;
  text-overflow: ellipsis;
  display: -webkit-box;
  -webkit-line-clamp: 2;
  -webkit-box-orient: vertical;
}

.notify-time {
  font-size: 11px;
  color: #a8abb2;
  margin-top: 2px;
}

.notify-dot {
  width: 6px;
  height: 6px;
  border-radius: 50%;
  background: #f56c6c;
  flex-shrink: 0;
  margin-top: 6px;
}

/* 发布按钮 */
.publish-btn {
  background: linear-gradient(135deg, #1d6df0, #4facfe);
  border: none;
  font-weight: 500;
}

.publish-btn:hover {
  box-shadow: 0 4px 12px rgba(29, 109, 240, 0.3);
}

/* 用户下拉 */
.user-name {
  display: flex;
  align-items: center;
  gap: 6px;
  cursor: pointer;
  color: #303133;
  outline: none;
  padding: 4px 8px;
  border-radius: 8px;
  transition: all 0.2s;
}

.user-name:hover {
  background: #f5f7fa;
}

.nav-avatar {
  background: linear-gradient(135deg, #1d6df0, #4facfe);
  color: #fff;
  font-size: 13px;
  flex-shrink: 0;
}

.user-nick {
  font-size: 13px;
  max-width: 80px;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.dropdown-arrow {
  font-size: 10px;
  color: #909399;
}

.app-main {
  padding: 0;
  background: linear-gradient(180deg, #f5f7fa 0%, #eef1f6 100%);
  min-height: calc(100vh - 64px);
}

/* 响应式 */
@media (max-width: 1200px) {
  .nav-label {
    display: none;
  }
  .nav-item {
    padding: 6px 8px;
  }
}

@media (max-width: 768px) {
  .sign-info, .user-nick {
    display: none;
  }
  .nav-menu {
    margin-left: 8px;
  }
}
</style>
