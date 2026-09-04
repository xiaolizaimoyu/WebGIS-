<script setup>
// 整体布局外壳（归属：前端 C）——顶部导航栏 + 主内容区
// TODO(前端C)：全站换肤、更多导航入口、用户中心入口可在此扩展
import { computed } from 'vue'
import { useRouter } from 'vue-router'
import { ElMessage } from 'element-plus'
import { useUserStore } from '@/stores/user'

const router = useRouter()
const store = useUserStore()
const isLoggedIn = computed(() => store.isLoggedIn)
const avatarUrl = computed(() => store.userInfo?.avatar || '')
const avatarText = computed(() => (store.userInfo?.nickname || '?').slice(0, 1))

function onCommand(cmd) {
  if (cmd === 'profile') {
    router.push('/profile')
  } else if (cmd === 'mine') {
    router.push('/mine')
  } else if (cmd === 'logout') {
    store.logout()
    ElMessage.success('已退出登录')
    router.push('/')
  }
}
</script>

<template>
  <el-container class="app-layout">
    <el-header class="app-header">
      <div class="header-inner">
        <router-link to="/" class="brand">🎓 校园活动交流平台</router-link>
        <div class="spacer" />
        <el-button v-if="isLoggedIn" type="primary" round @click="router.push('/publish')">
          ＋ 发布内容
        </el-button>
        <el-dropdown v-if="isLoggedIn" @command="onCommand">
          <span class="user-name">
            <el-avatar :size="26" :src="avatarUrl || undefined" class="nav-avatar">
              {{ avatarText }}
            </el-avatar>
            {{ store.userInfo?.nickname }} ▾
          </span>
          <template #dropdown>
            <el-dropdown-menu>
              <el-dropdown-item command="profile">个人中心</el-dropdown-item>
              <el-dropdown-item command="mine">我的发布</el-dropdown-item>
              <el-dropdown-item divided command="logout">退出登录</el-dropdown-item>
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
  background: #fff;
  border-bottom: 1px solid #e4e7ed;
  position: sticky;
  top: 0;
  z-index: 100;
  box-shadow: 0 1px 4px rgba(0, 0, 0, 0.04);
}

.header-inner {
  max-width: 1400px;
  height: 100%;
  margin: 0 auto;
  display: flex;
  align-items: center;
  gap: 16px;
  padding: 0 20px;
}

.brand {
  font-size: 20px;
  font-weight: 700;
  color: #1d6df0;
}

.spacer {
  flex: 1;
}

.user-name {
  display: flex;
  align-items: center;
  gap: 6px;
  cursor: pointer;
  color: #303133;
  outline: none;
}

.nav-avatar {
  background: #1d6df0;
  color: #fff;
  font-size: 13px;
  flex-shrink: 0;
}

.app-main {
  padding: 0;
  background: #f5f7fa;
}
</style>
