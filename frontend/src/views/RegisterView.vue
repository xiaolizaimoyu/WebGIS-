<script setup>
import { ref, reactive, computed } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { ElMessage } from 'element-plus'
import * as userApi from '@/api/user'
import { useUserStore } from '@/stores/user'

const router = useRouter()
const route = useRoute()
const store = useUserStore()

const formRef = ref()
const loading = ref(false)
const submitted = ref(false)
const form = reactive({ username: '', nickname: '', password: '', confirm: '' })

const passwordStrength = computed(() => {
  const pwd = form.password
  if (!pwd) return { level: 0, label: '', color: '' }
  let score = 0
  if (pwd.length >= 8) score++
  if (/[a-z]/.test(pwd)) score++
  if (/[A-Z]/.test(pwd)) score++
  if (/\d/.test(pwd)) score++
  if (/[^a-zA-Z0-9]/.test(pwd)) score++
  if (score <= 1) return { level: 1, label: '弱', color: '#f56c6c' }
  if (score <= 3) return { level: 2, label: '中', color: '#e6a23c' }
  return { level: 3, label: '强', color: '#67c23a' }
})

const rules = {
  username: [
    { required: true, message: '请输入账号', trigger: 'blur' },
    { min: 2, max: 30, message: '账号长度 2-30 位', trigger: 'blur' }
  ],
  nickname: [{ required: true, message: '请输入昵称', trigger: 'blur' }],
  password: [
    { required: true, message: '请输入密码', trigger: 'blur' },
    { min: 6, max: 64, message: '密码至少 6 位', trigger: 'blur' }
  ],
  confirm: [
    { required: true, message: '请再次输入密码', trigger: 'blur' },
    {
      validator: (rule, value, callback) => {
        if (value !== form.password) callback(new Error('两次输入的密码不一致'))
        else callback()
      },
      trigger: 'blur'
    }
  ]
}

async function submit() {
  if (submitted.value || loading.value) return
  submitted.value = true
  try {
    await formRef.value.validate()
  } catch {
    submitted.value = false
    return
  }
  loading.value = true
  try {
    await userApi.register({
      username: form.username.trim(),
      nickname: form.nickname.trim(),
      password: form.password
    })
    await store.login({
      username: form.username.trim(),
      password: form.password
    })
    ElMessage.success('注册成功，已自动登录')
    const redirect = route.query.redirect
    router.push(redirect ? String(redirect) : '/')
  } catch {
  } finally {
    loading.value = false
    submitted.value = false
  }
}
</script>

<template>
  <div class="register-page">
    <div class="register-card">
      <h1 class="title">创建账号</h1>
      <p class="sub">加入校园活动交流平台</p>

      <el-form ref="formRef" :model="form" :rules="rules" size="large">
        <el-form-item prop="username">
          <el-input v-model="form.username" placeholder="账号（2-30 位，建议学号）" clearable />
        </el-form-item>
        <el-form-item prop="nickname">
          <el-input v-model="form.nickname" placeholder="昵称（展示给其他同学）" clearable />
        </el-form-item>
        <el-form-item prop="password">
          <el-input v-model="form.password" type="password" placeholder="密码（至少 6 位，越长越复杂越安全）" show-password />
          <div v-if="form.password" class="pwd-strength">
            <div class="bars">
              <span class="bar" :class="{ active: passwordStrength.level >= 1 }" :style="{ background: passwordStrength.level >= 1 ? passwordStrength.color : '' }" />
              <span class="bar" :class="{ active: passwordStrength.level >= 2 }" :style="{ background: passwordStrength.level >= 2 ? passwordStrength.color : '' }" />
              <span class="bar" :class="{ active: passwordStrength.level >= 3 }" :style="{ background: passwordStrength.level >= 3 ? passwordStrength.color : '' }" />
            </div>
            <span class="label" :style="{ color: passwordStrength.color }">密码强度：{{ passwordStrength.label }}</span>
          </div>
        </el-form-item>
        <el-form-item prop="confirm">
          <el-input v-model="form.confirm" type="password" placeholder="确认密码" show-password />
        </el-form-item>
        <el-button class="submit-btn" type="primary" size="large" :loading="loading" @click="submit">
          注 册
        </el-button>
      </el-form>

      <div class="footer">
        已有账号？
        <router-link class="link" to="/login">去登录</router-link>
      </div>
    </div>
  </div>
</template>

<style scoped>
.register-page {
  min-height: 100vh;
  display: flex;
  align-items: center;
  justify-content: center;
  background: linear-gradient(135deg, #4facfe 0%, #6fdc8f 100%);
}

.register-card {
  width: 420px;
  background: #fff;
  border-radius: 14px;
  padding: 34px 36px 30px;
  box-shadow: 0 12px 40px rgba(0, 0, 0, 0.15);
}

.title {
  text-align: center;
  font-size: 22px;
  color: #303133;
}

.sub {
  text-align: center;
  color: #909399;
  font-size: 13px;
  margin: 6px 0 22px;
}

.pwd-strength {
  display: flex;
  align-items: center;
  gap: 10px;
  margin-top: 6px;
  font-size: 12px;
}

.pwd-strength .bars {
  display: flex;
  gap: 4px;
}

.pwd-strength .bar {
  display: block;
  width: 44px;
  height: 6px;
  border-radius: 3px;
  background: #ebeef5;
  transition: background 0.2s;
}

.submit-btn {
  width: 100%;
}

.footer {
  margin-top: 16px;
  text-align: center;
  color: #909399;
  font-size: 14px;
}

.link {
  color: #1d6df0;
}
</style>
