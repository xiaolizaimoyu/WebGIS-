<script setup>
// 消息通知中心（归属：前端 C）——/notifications，全部/未读筛选，类型图标，点击跳转
import { onMounted, ref, computed } from 'vue'
import { useRouter } from 'vue-router'
import { ElMessage } from 'element-plus'
import { useNotificationStore } from '@/stores/notification'
import { formatTime } from '@/api/const'

const router = useRouter()
const notificationStore = useNotificationStore()

const activeFilter = ref('all') // all / unread

const notifications = computed(() => {
  if (activeFilter.value === 'unread') {
    return notificationStore.list.filter((n) => !n.read)
  }
  return notificationStore.list
})

const unreadCount = computed(() => notificationStore.unreadCount)

const typeIconMap = {
  comment: '💬',
  like: '❤️',
  answer: '✏️',
  system: '🔔',
  carpool: '🚗',
  sign: '🎁',
  follow: '👥',
  default: '📩'
}

function getIcon(type) {
  return typeIconMap[type] || typeIconMap.default
}

async function loadData() {
  await notificationStore.fetchList()
  await notificationStore.fetchUnreadCount()
}

function onFilterChange(filter) {
  activeFilter.value = filter
}

async function handleClick(n) {
  if (!n.read) {
    await notificationStore.markRead(n.id)
  }
  // 根据类型跳转
  if (n.related_type === 'question' && n.related_id) {
    router.push(`/question/${n.related_id}`)
  } else if (n.related_type === 'carpool' && n.related_id) {
    router.push(`/carpool/${n.related_id}`)
  } else if (n.related_type === 'answer' && n.related_id) {
    router.push(`/question/${n.related_id}`)
  }
}

async function handleMarkAllRead() {
  await notificationStore.markAllRead()
  ElMessage.success('已全部标记为已读')
}

onMounted(loadData)
</script>

<template>
  <div class="notifications-page">
    <el-card shadow="never" class="header-card">
      <div class="header-row">
        <h2>🔔 消息通知</h2>
        <div class="header-actions">
          <el-radio-group v-model="activeFilter" size="small" @change="onFilterChange">
            <el-radio-button value="all">全部</el-radio-button>
            <el-radio-button value="unread">
              未读 <el-badge v-if="unreadCount > 0" :value="unreadCount" class="unread-badge" />
            </el-radio-button>
          </el-radio-group>
          <el-button size="small" @click="handleMarkAllRead" :disabled="unreadCount === 0">
            ✓ 全部已读
          </el-button>
        </div>
      </div>
    </el-card>

    <el-card shadow="never" class="list-card">
      <div v-loading="notificationStore.loading" class="notification-list">
        <el-empty v-if="!notifications.length && !notificationStore.loading" description="暂无通知" :image-size="100" />

        <div
          v-for="n in notifications"
          :key="n.id"
          class="notification-item"
          :class="{ unread: !n.read }"
          @click="handleClick(n)"
        >
          <div class="notif-icon">{{ getIcon(n.type) }}</div>
          <div class="notif-content">
            <div class="notif-title">{{ n.title }}</div>
            <div class="notif-text">{{ n.content }}</div>
            <div class="notif-time">{{ formatTime(n.created_at) }}</div>
          </div>
          <div v-if="!n.read" class="unread-dot"></div>
        </div>
      </div>
    </el-card>
  </div>
</template>

<style scoped>
.notifications-page {
  max-width: 800px;
  margin: 0 auto;
  padding: 20px;
}

.header-card {
  border-radius: 12px;
  margin-bottom: 16px;
}

.header-row {
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.header-row h2 {
  margin: 0;
  font-size: 20px;
  color: #303133;
}

.header-actions {
  display: flex;
  align-items: center;
  gap: 12px;
}

.unread-badge {
  margin-left: 4px;
}

.list-card {
  border-radius: 12px;
}

.notification-list {
  min-height: 300px;
}

.notification-item {
  display: flex;
  align-items: flex-start;
  gap: 14px;
  padding: 16px;
  border-radius: 10px;
  margin-bottom: 8px;
  cursor: pointer;
  transition: all 0.2s;
  position: relative;
  background: #fafafa;
}

.notification-item:hover {
  background: #ecf5ff;
  transform: translateX(4px);
}

.notification-item.unread {
  background: linear-gradient(135deg, #ecf5ff 0%, #fff 100%);
  border-left: 3px solid #1d6df0;
}

.notif-icon {
  font-size: 28px;
  width: 48px;
  height: 48px;
  display: flex;
  align-items: center;
  justify-content: center;
  background: #fff;
  border-radius: 50%;
  flex-shrink: 0;
  box-shadow: 0 2px 8px rgba(0,0,0,0.06);
}

.notif-content {
  flex: 1;
  min-width: 0;
}

.notif-title {
  font-size: 14px;
  font-weight: 600;
  color: #303133;
  margin-bottom: 4px;
}

.notif-text {
  font-size: 13px;
  color: #606266;
  line-height: 1.5;
  margin-bottom: 4px;
}

.notif-time {
  font-size: 12px;
  color: #a8abb2;
}

.unread-dot {
  width: 8px;
  height: 8px;
  border-radius: 50%;
  background: #f56c6c;
  flex-shrink: 0;
  margin-top: 8px;
}
</style>
