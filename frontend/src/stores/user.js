// 用户状态（归属：前端 C 功能 + 前端 A storage 封装）
// 登录后全局共享当前用户，统一走 utils/storage 持久化；并内置签到/积分状态（前端 C）
import { defineStore } from 'pinia'
import * as userApi from '@/api/user'
import * as signApi from '@/api/sign'
import { storage } from '@/utils/storage'
import { getMockSignStatus } from '@/utils/mockData'

export const useUserStore = defineStore('user', {
  state: () => ({
    token: storage.getToken(),
    userInfo: storage.getUser(),
    // 签到与积分状态
    signStatus: null,
    signLoading: false
  }),

  getters: {
    isLoggedIn: (state) => !!state.token
  },

  actions: {
    async login(form) {
      const data = await userApi.login(form)
      this.token = data.token
      this.userInfo = data.user
      storage.setToken(data.token)
      storage.setUser(data.user)
    },

    setUser(user) {
      this.userInfo = { ...this.userInfo, ...user }
      storage.setUser(this.userInfo)
    },

    logout() {
      this.token = ''
      this.userInfo = null
      this.signStatus = null
      storage.clearAuth()
    },

    // 获取签到状态；后端接口未通时用 mock 兜底
    async fetchSignStatus() {
      if (!this.isLoggedIn) return
      try {
        this.signStatus = await signApi.getSignStatus()
      } catch {
        this.signStatus = getMockSignStatus()
      }
    },

    // 执行签到
    async doSign() {
      if (!this.isLoggedIn) return null
      this.signLoading = true
      try {
        const result = await signApi.doSign()
        await this.fetchSignStatus()
        return result
      } catch {
        // mock 模式：模拟签到成功
        if (!this.signStatus) this.signStatus = getMockSignStatus()
        if (!this.signStatus.signedToday) {
          this.signStatus.signedToday = true
          this.signStatus.continuousDays += 1
          this.signStatus.totalPoints += 10
          this.signStatus.signRecords.unshift({
            date: new Date().toISOString().slice(0, 10),
            points: 10
          })
        }
        return { points: 10, continuousDays: this.signStatus.continuousDays }
      } finally {
        this.signLoading = false
      }
    }
  }
})
