// 消息通知状态管理（归属：前端 C）
import { defineStore } from 'pinia'
import { ref, computed } from 'vue'
import * as notificationApi from '@/api/notification'
import { getMockNotifications } from '@/utils/mockData'

export const useNotificationStore = defineStore('notification', () => {
  const list = ref([])
  const unreadCount = ref(0)
  const loading = ref(false)

  const unreadList = computed(() => list.value.filter((n) => !n.read))

  async function fetchUnreadCount() {
    try {
      const data = await notificationApi.getUnreadCount()
      unreadCount.value = data.count || 0
    } catch {
      // 后端未启动时使用 mock
      const mock = getMockNotifications()
      unreadCount.value = mock.filter((n) => !n.read).length
    }
  }

  async function fetchList(params = {}) {
    loading.value = true
    try {
      const data = await notificationApi.listNotifications(params)
      list.value = data.items || data || []
    } catch {
      let mock = getMockNotifications()
      if (params.unread) mock = mock.filter((n) => !n.read)
      list.value = mock
    } finally {
      loading.value = false
    }
  }

  async function markRead(id) {
    try {
      await notificationApi.markAsRead(id)
    } catch {
      // mock 模式下本地更新
    }
    const item = list.value.find((n) => n.id === id)
    if (item) item.read = true
    if (unreadCount.value > 0) unreadCount.value--
  }

  async function markAllRead() {
    try {
      await notificationApi.markAllAsRead()
    } catch {
      // mock 模式
    }
    list.value.forEach((n) => (n.read = true))
    unreadCount.value = 0
  }

  return {
    list,
    unreadCount,
    unreadList,
    loading,
    fetchUnreadCount,
    fetchList,
    markRead,
    markAllRead
  }
})
