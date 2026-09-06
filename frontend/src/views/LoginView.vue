<script setup>
import { ref, reactive, onMounted } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { ElMessage } from 'element-plus'
import { useUserStore } from '@/stores/user'
import { storage } from '@/utils/storage'
import { getCaptcha } from '@/api/user'

const route = useRoute()
const router = useRouter()
const store = useUserStore()

const formRef = ref()
const loading = ref(false)
const submitted = ref(false)
const form = reactive({ username: '', password: '', captcha_code: '' })

const captchaId = ref('')
const captchaUrl = ref('')

const remember = ref(false)

// 拉取/刷新验证码
async function refreshCaptcha() {
  try {
    const data = await getCaptcha()
    captchaId.value = data.captcha_id
    captchaUrl.value = data.image
  } catch {
    // 验证码获取失败不阻塞，用户可点击图片重试
  }
}

onMounted(() => {
  const saved = storage.getRememberUser()
  if (saved) {
    form.username = saved
    remember.value = true
  }
  refreshCaptcha()
})

const rules = {
  username: [{ required: true, message: '请输入账号', trigger: 'blur' }],
  password: [{ required: true, message: '请输入密码', trigger: 'blur' }],
  captcha_code: [{ required: true, message: '请输入验证码', trigger: 'blur' }]
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
    await store.login({ ...form, captcha_id: captchaId.value })
    ElMessage.success('登录成功')
    if (remember.value) storage.setRememberUser(form.username.trim())
    else storage.removeRememberUser()
    form.password = ''
    form.captcha_code = ''
    const redirect = route.query.redirect
    router.push(redirect ? String(redirect) : '/')
  } catch {
    // 登录失败后验证码已作废，必须刷新
    form.captcha_code = ''
    refreshCaptcha()
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
  border: 1px solid #dcdfe6;
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
