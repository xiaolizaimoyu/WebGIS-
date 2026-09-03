<script setup>
// 个人中心页（归属：前端 A）
// 展示并编辑个人资料（昵称/头像）、修改密码
// 说明：本路由 requiresAuth，未登录会被守卫拦截到登录页
// TODO(前端A)：历史发布入口、头像裁剪、绑定手机号等扩展点
import { reactive, ref, onMounted } from 'vue'
import { ElMessage } from 'element-plus'
import { uploadImage } from '@/api/post'
import { updateProfile, changePassword } from '@/api/user'
import { formatTime } from '@/api/const'
import { useUserStore } from '@/stores/user'

const store = useUserStore()

// ---------- 基本信息 ----------
const saving = ref(false)
const form = reactive({ nickname: '', avatar: '' })

onMounted(() => {
  const info = store.userInfo || {}
  form.nickname = info.nickname || ''
  form.avatar = info.avatar || ''
})

const avatarText = () => {
  if (form.avatar) return ''
  return (form.nickname || store.userInfo?.nickname || '?').slice(0, 1)
}

// 自定义上传头像：走 /api/upload（自动带 Token）
async function doUpload(options) {
  const data = await uploadImage(options.file)
  options.onSuccess(data, options.file)
}

function onUploadSuccess(response) {
  form.avatar = response.url
}

async function saveProfile() {
  const nickname = form.nickname.trim()
  if (!nickname) {
    ElMessage.warning('昵称不能为空')
    return
  }
  saving.value = true
  try {
    const user = await updateProfile({ nickname, avatar: form.avatar || undefined })
    store.setUser(user)
    ElMessage.success('资料已更新')
  } finally {
    saving.value = false
  }
}

// ---------- 修改密码 ----------
const pwdFormRef = ref()
const changing = ref(false)
const pwd = reactive({ old: '', next: '', confirm: '' })
const pwdRules = {
  old: [{ required: true, message: '请输入原密码', trigger: 'blur' }],
  next: [
    { required: true, message: '请输入新密码', trigger: 'blur' },
    { min: 6, max: 64, message: '新密码至少 6 位', trigger: 'blur' }
  ],
  confirm: [
    { required: true, message: '请再次输入新密码', trigger: 'blur' },
    {
      validator: (rule, value, callback) => {
        if (value !== pwd.next) callback(new Error('两次输入的新密码不一致'))
        else callback()
      },
      trigger: 'blur'
    }
  ]
}

async function savePassword() {
  try {
    await pwdFormRef.value.validate()
  } catch {
    return
  }
  changing.value = true
  try {
    await changePassword({ old_password: pwd.old, new_password: pwd.next })
    ElMessage.success('密码修改成功，下次请用新密码登录')
    pwd.old = ''
    pwd.next = ''
    pwd.confirm = ''
    pwdFormRef.value.resetFields()
  } finally {
    changing.value = false
  }
}
</script>

<template>
  <div class="page-container profile-page">
    <!-- 基本信息 -->
    <el-card shadow="never">
      <template #header>个人资料</template>
      <div class="profile-head">
        <div class="avatar-wrap">
          <el-avatar :size="72" :src="form.avatar || undefined" class="big-avatar">
            {{ avatarText() }}
          </el-avatar>
          <el-upload
            :show-file-list="false"
            accept="image/*"
            :http-request="doUpload"
            :on-success="onUploadSuccess"
          >
            <el-button size="small" class="avatar-btn">更换头像</el-button>
          </el-upload>
        </div>
        <div class="info-line">
          <div class="row">
            <span class="label">账号：</span><span>{{ store.userInfo?.username }}</span>
          </div>
          <div class="row">
            <span class="label">注册时间：</span>
            <span>{{ formatTime(store.userInfo?.created_at) || '-' }}</span>
          </div>
        </div>
      </div>

      <el-form label-width="80px" class="profile-form">
        <el-form-item label="昵称">
          <el-input v-model="form.nickname" maxlength="30" show-word-limit style="width: 280px" />
        </el-form-item>
        <el-form-item>
          <el-button type="primary" :loading="saving" @click="saveProfile">保存资料</el-button>
        </el-form-item>
      </el-form>
    </el-card>

    <!-- 修改密码 -->
    <el-card shadow="never" class="pwd-card">
      <template #header>修改密码</template>
      <el-form
        ref="pwdFormRef"
        :model="pwd"
        :rules="pwdRules"
        label-width="90px"
        class="pwd-form"
      >
        <el-form-item label="原密码" prop="old">
          <el-input v-model="pwd.old" type="password" show-password style="width: 280px" placeholder="请输入原密码" />
        </el-form-item>
        <el-form-item label="新密码" prop="next">
          <el-input v-model="pwd.next" type="password" show-password style="width: 280px" placeholder="至少 6 位" />
        </el-form-item>
        <el-form-item label="确认新密码" prop="confirm">
          <el-input v-model="pwd.confirm" type="password" show-password style="width: 280px" placeholder="再次输入新密码" />
        </el-form-item>
        <el-form-item>
          <el-button type="primary" :loading="changing" @click="savePassword">确认修改</el-button>
        </el-form-item>
      </el-form>
    </el-card>
  </div>
</template>

<style scoped>
.profile-head {
  display: flex;
  align-items: center;
  gap: 24px;
  margin-bottom: 20px;
}

.avatar-wrap {
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 8px;
}

.big-avatar {
  font-size: 26px;
  background: #1d6df0;
  color: #fff;
}

.avatar-btn {
  margin: 0;
}

.info-line {
  color: #303133;
  font-size: 14px;
}

.row {
  margin-bottom: 6px;
}

.label {
  color: #909399;
}

.pwd-card {
  margin-top: 16px;
}
</style>
