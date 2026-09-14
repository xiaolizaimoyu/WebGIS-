<script setup>
// 管理员登录页（归属：后端 D 实现，差异化深色主题）
// 与普通登录页视觉区分：深色渐变背景 + "管理后台"标题
// 登录走同一 POST /api/user/login（验证码+限流），成功后校验 is_admin
import { ref, reactive, onMounted } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { ElMessage } from 'element-plus'
import { useUserStore } from '@/stores/user'
import { getCaptcha } from '@/api/user'

const route = useRoute()
const router = useRouter()
const store = useUserStore()

const formRef = ref()
const loading = ref(false)
const form = reactive({ username: '', password: '', captcha_code: '' })
const captchaId = ref('')
const captchaUrl = ref('')

const rules = {
  username: [{ required: true, message: '请输入管理员账号', trigger: 'blur' }],
  password: [{ required: true, message: '请输入密码', trigger: 'blur' }],
  captcha_code: [{ required: true, message: '请输入验证码', trigger: 'blur' }]
}

async function refreshCaptcha() {
  try {
    const data = await getCaptcha()
    captchaId.value = data.captcha_id
    captchaUrl.value = data.image
  } catch {
    // 错误提示由 request.js 统一处理
  }
}

onMounted(refreshCaptcha)

async function submit() {
  try {
    await formRef.value.validate()
  } catch {
    return
  }
  loading.value = true
  try {
    await store.login({ ...form, captcha_id: captchaId.value })
    // 校验是否管理员
    if (!store.isAdmin) {
      ElMessage.error('该账号无管理员权限')
      store.logout()
      refreshCaptcha()
      form.captcha_code = ''
      return
    }
    ElMessage.success('管理员登录成功')
    const redirect = route.query.redirect
    router.push(redirect ? String(redirect) : '/admin')
  } catch {
    form.captcha_code = ''
    refreshCaptcha()
  } finally {
    loading.value = false
  }
}
</script>

<template>
  <div class="admin-login-page">
    <div class="admin-login-card">
      <div class="brand-row">
        <span class="brand-icon">🛡️</span>
        <h1 class="brand">管理后台</h1>
      </div>
      <p class="slogan">仅限管理员账号登录 · 普通用户请前往用户端</p>

      <el-form ref="formRef" :model="form" :rules="rules" size="large" @keyup.enter="submit">
        <el-form-item prop="username">
          <el-input v-model="form.username" placeholder="管理员账号" clearable />
        </el-form-item>
        <el-form-item prop="password">
          <el-input v-model="form.password" type="password" placeholder="密码" show-password />
        </el-form-item>
        <el-form-item prop="captcha_code">
          <div class="captcha-row">
            <el-input v-model="form.captcha_code" placeholder="验证码（不区分大小写）" maxlength="4" clearable />
            <img
              class="captcha-img"
              :src="captchaUrl"
              title="看不清？点击刷新"
              @click="refreshCaptcha"
            />
          </div>
        </el-form-item>
        <el-button class="submit-btn" type="primary" size="large" :loading="loading" @click="submit">
          管理员登录
        </el-button>
      </el-form>

      <div class="footer">
        <router-link class="link" to="/login">← 返回用户登录</router-link>
      </div>
    </div>
  </div>
</template>

<style scoped>
.admin-login-page {
  min-height: 100vh;
  display: flex;
  align-items: center;
  justify-content: center;
  /* 深色渐变：与普通登录页（蓝绿亮色）形成明显视觉差异 */
  background: linear-gradient(135deg, #1a1f2e 0%, #2d3548 100%);
}

.admin-login-card {
  width: 400px;
  background: #252b3a;
  border: 1px solid #3a4154;
  border-radius: 14px;
  padding: 40px 36px 30px;
  box-shadow: 0 12px 40px rgba(0, 0, 0, 0.45);
}

.brand-row {
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 10px;
  margin-bottom: 6px;
}

.brand-icon {
  font-size: 28px;
}

.brand {
  font-size: 24px;
  text-align: center;
  color: #f1f3f5;
  margin: 0;
}

.slogan {
  text-align: center;
  color: #909399;
  font-size: 13px;
  margin-bottom: 26px;
}

/* 深色卡片内表单元素反色 */
:deep(.el-input__wrapper) {
  background-color: #1f2330;
  box-shadow: 0 0 0 1px #3a4154 inset;
}
:deep(.el-input__inner) {
  color: #f1f3f5;
}
:deep(.el-input__wrapper:hover) {
  box-shadow: 0 0 0 1px #4a5170 inset;
}

.captcha-row {
  display: flex;
  gap: 10px;
  width: 100%;
}
.captcha-img {
  height: 40px;
  border-radius: 6px;
  cursor: pointer;
  flex-shrink: 0;
  background: #f5f7fa;
}

.submit-btn {
  width: 100%;
  margin-top: 6px;
  background: #4a5170;
  border-color: #4a5170;
}
.submit-btn:hover {
  background: #5a6388;
  border-color: #5a6388;
}

.footer {
  margin-top: 18px;
  text-align: center;
  font-size: 14px;
}

.link {
  color: #9aa3b8;
  text-decoration: none;
}
.link:hover {
  color: #c0c4d0;
}
</style>
