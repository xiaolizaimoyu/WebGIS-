<script setup>
// 注册页（归属：前端 A）——账号注册模板
// TODO(前端A)：昵称头像、密码强度、注册成功自动登录等扩展点
import { ref, reactive } from 'vue'
import { useRouter } from 'vue-router'
import { ElMessage } from 'element-plus'
import * as userApi from '@/api/user'

const router = useRouter()

const formRef = ref()
const loading = ref(false)
const form = reactive({ username: '', nickname: '', password: '', confirm: '' })

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
  try {
    await formRef.value.validate()
  } catch {
    return
  }
  loading.value = true
  try {
    await userApi.register({
      username: form.username.trim(),
      nickname: form.nickname.trim(),
      password: form.password
    })
    ElMessage.success('注册成功，请登录')
    router.push('/login')
  } catch {
    // 错误提示已由 request.js 统一弹出
  } finally {
    loading.value = false
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
          <el-input v-model="form.password" type="password" placeholder="密码（至少 6 位）" show-password />
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
