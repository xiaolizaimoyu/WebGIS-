// 用户状态（归属：前端 C）——登录后全局共享当前用户，配合 localStorage 持久化
import { defineStore } from 'pinia'
import { ref, computed } from 'vue'
import * as userApi from '@/api/user'
import * as signApi from '@/api/sign'
import { getMockSignStatus } from '@/utils/mockData'

export const useUserStore = defineStore('user', () => {
  // token 与 userInfo 在页面刷新后从 localStorage 恢复
  const token = ref(localStorage.getItem('campus_token') || '')
  const userInfo = ref(JSON.parse(localStorage.getItem('campus_user') || 'null'))

  // 签到与积分状态
  const signStatus = ref(null)
  const signLoading = ref(false)

  const isLoggedIn = computed(() => !!token.value)

  // 登录成功：存 Pinia 状态 + localStorage
  async function login(form) {
    const data = await userApi.login(form)
    token.value = data.token
    userInfo.value = data.user
    localStorage.setItem('campus_token', data.token)
    localStorage.setItem('campus_user', JSON.stringify(data.user))
  }

  // 更新资料后同步 userInfo（合并并持久化），由个人中心页调用
  function setUser(user) {
    userInfo.value = { ...userInfo.value, ...user }
    localStorage.setItem('campus_user', JSON.stringify(userInfo.value))
  }

  // 退出：清空状态
  function logout() {
    token.value = ''
    userInfo.value = null
    signStatus.value = null
    localStorage.removeItem('campus_token')
    localStorage.removeItem('campus_user')
  }

  // 获取签到状态：后端返回 snake_case，统一转成前端 camelCase
  async function fetchSignStatus() {
    if (!isLoggedIn.value) return
    try {
      const d = await signApi.getSignStatus()
      signStatus.value = {
        signedToday: !!d.signed_today,
        continuousDays: d.continuous_days || 0,
        totalPoints: d.total_points || 0,
        recentRecords: d.recent_records || []
      }
    } catch {
      signStatus.value = getMockSignStatus()
    }
  }

  // 执行签到
  async function doSign() {
    if (!isLoggedIn.value) return null
    signLoading.value = true
    try {
      const result = await signApi.doSign()
      await fetchSignStatus()
      // 后端：重复签到返回 points=0（今日已签到），此时不弹"获得积分"
      if (result.signed && (result.points || 0) === 0) {
        return null
      }
      return {
        signed: true,
        points: result.points || 0,
        bonus: result.bonus || 0,
        continuousDays: result.continuous_days || 0,
        totalPoints: result.total_points || 0
      }
    } catch {
      // mock 模式：模拟签到成功
      if (!signStatus.value) signStatus.value = getMockSignStatus()
      if (!signStatus.value.signedToday) {
        signStatus.value.signedToday = true
        signStatus.value.continuousDays += 1
        signStatus.value.totalPoints += 10
        signStatus.value.signRecords.unshift({
          date: new Date().toISOString().slice(0, 10),
          points: 10
        })
      }
      return { points: 10, continuousDays: signStatus.value.continuousDays }
    } finally {
      signLoading.value = false
    }
  }

  return {
    token,
    userInfo,
    signStatus,
    signLoading,
    isLoggedIn,
    login,
    setUser,
    logout,
    fetchSignStatus,
    doSign
  }
})
