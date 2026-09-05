// 用户状态（归属：前端 C）——登录后全局共享当前用户，配合 localStorage 持久化
import { defineStore } from 'pinia'
import * as userApi from '@/api/user'

export const useUserStore = defineStore('user', {
  state: () => ({
    // token 与 userInfo 在页面刷新后从 localStorage 恢复
    token: localStorage.getItem('campus_token') || '',
    userInfo: JSON.parse(localStorage.getItem('campus_user') || 'null')
  }),

  getters: {
    isLoggedIn: (state) => !!state.token
  },

  actions: {
    // 登录成功：存 Pinia 状态 + localStorage
    async login(form) {
      const data = await userApi.login(form)
      this.token = data.token
      this.userInfo = data.user
      localStorage.setItem('campus_token', data.token)
      localStorage.setItem('campus_user', JSON.stringify(data.user))
    },

    // 退出：清空状态
    logout() {
      this.token = ''
      this.userInfo = null
      localStorage.removeItem('campus_token')
      localStorage.removeItem('campus_user')
    }
  }
})
