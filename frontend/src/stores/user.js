// 用户状态（归属：前端 C）——登录后全局共享当前用户，配合 localStorage 持久化
import { defineStore } from 'pinia'
import * as userApi from '@/api/user'
import { storage } from '@/utils/storage'

export const useUserStore = defineStore('user', {
  state: () => ({
    token: storage.getToken(),
    userInfo: storage.getUser()
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
      storage.clearAuth()
    }
  }
})
