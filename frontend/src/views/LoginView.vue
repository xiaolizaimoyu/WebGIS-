<script setup>
import { ref, reactive, onMounted } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { ElMessage } from 'element-plus'
import { useUserStore } from '@/stores/user'
import { storage } from '@/utils/storage'

const route = useRoute()
const router = useRouter()
const store = useUserStore()

const formRef = ref()
const loading = ref(false)
const submitted = ref(false)
const form = reactive({ username: '', password: '' })

const remember = ref(false)

onMounted(() => {
  const saved = storage.getRememberUser()
  if (saved) {
    form.username = saved
    remember.value = true
  }
})

const rules = {
  username: [{ required: true, message: '请输入账号', trigger: 'blur' }],
  password: [{ required: true, message: '请输入密码', trigger: 'blur' }]
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
    await store.login({ ...form })
    ElMessage.success('登录成功')
    if (remember.value) storage.setRememberUser(form.username.trim())
    else storage.removeRememberUser()
    form.password = ''
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
  <div class="login-page">
    <div class="login-card">
      <h1 class="brand">🎓 校园活动交流平台</h1>
      <p class="slogan">分享校园新鲜事 · 让每一场活动都被看见</p>

      <el-form ref="formRef" :model="form" :rules="rules" size="large" @keyup.enter="submit">
        <el-form-item prop="username">
          <el-input v-model="form.username" placeholder="请输入账号" clearable />
        </el-form-item>
        <el-form-item prop="password">
          <el-input v-model="form.password" type="password" placeholder="请输入密码" show-password />
        </el-form-item>
        <el-form-item class="remember-item">
          <el-checkbox v-model="remember">记住账号</el-checkbox>
        </el-form-item>
        <el-button class="submit-btn" type="primary" size="large" :loading="loading" @click="submit">
          登 录
        </el-button>
      </el-form>

      <div class="footer">
        还没有账号？
        <router-link class="link" to="/register">立即注册</router-link>
      </div>
    </div>
  </div>
</template>

<style scoped>
.login-page {
  min-height: 100vh;
  display: flex;
  align-items: center;
  justify-content: center;
  /* TODO(前端A)：可换成校园背景图片 */
  background: linear-gradient(135deg, #4facfe 0%, #6fdc8f 100%);
}

.login-card {
  width: 400px;
  background: #fff;
  border-radius: 14px;
  padding: 40px 36px 30px;
  box-shadow: 0 12px 40px rgba(0, 0, 0, 0.15);
}

.brand {
  font-size: 24px;
  text-align: center;
  color: #303133;
  margin-bottom: 6px;
}

.slogan {
  text-align: center;
  color: #909399;
  font-size: 13px;
  margin-bottom: 26px;
}

.submit-btn {
  width: 100%;
  margin-top: 6px;
}

.remember-item {
  margin-bottom: 2px;
}

.footer {
  margin-top: 18px;
  text-align: center;
  color: #909399;
  font-size: 14px;
}

.link {
  color: #1d6df0;
}
</style>
