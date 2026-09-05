<script setup>
// 个人中心页（归属：前端 A 资料/改密码 + 前端 C 签到积分 融合）
// 路由 requiresAuth：登录后头像/导航进入
// 功能：① 查看/编辑昵称、更换头像、查看积分 ② 修改密码 ③ 每日签到
import { reactive, ref, onMounted, computed } from 'vue'
import { useRouter } from 'vue-router'
import { ElMessage } from 'element-plus'
import { uploadImage } from '@/api/post'
import { updateProfile, changePassword } from '@/api/user'
import { formatTime } from '@/api/const'
import { useUserStore } from '@/stores/user'

const router = useRouter()
const store = useUserStore()

// ---------- 基本信息（前端 A） ----------
const saving = ref(false)
const form = reactive({ nickname: '', avatar: '' })

onMounted(() => {
  const info = store.userInfo || {}
  form.nickname = info.nickname || ''
  form.avatar = info.avatar || ''
  // 拉取签到状态（后端未通时内部走 mock 兜底）
  store.fetchSignStatus()
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

// ---------- 修改密码（前端 A） ----------
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

// ---------- 签到与积分（前端 C） ----------
const totalPoints = computed(() => store.signStatus?.totalPoints || 0)
const continuousDays = computed(() => store.signStatus?.continuousDays || 0)
const signedToday = computed(() => store.signStatus?.signedToday || false)
const signRecords = computed(() => store.signStatus?.signRecords || [])

async function handleSign() {
  if (signedToday.value) {
    ElMessage.info('今日已签到，明天再来吧')
    return
  }
  const result = await store.doSign()
  if (result) {
    ElMessage.success(`签到成功！获得 ${result.points} 积分，连续签到 ${result.continuousDays} 天`)
  }
}
</script>

<template>
  <div class="profile-page">
    <!-- 个人资料 -->
    <el-card shadow="never">
      <template #header>
        <div class="card-head">
          <span>个人资料</span>
          <el-button type="primary" plain size="small" @click="router.push('/mine')">📝 我的发布</el-button>
        </div>
      </template>
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
          <div class="row">
            <span class="label">累计积分：</span><span class="points-num">{{ totalPoints }}</span>
          </div>
          <div class="row">
            <span class="label">连续签到：</span><span>{{ continuousDays }} 天</span>
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
    <el-card shadow="never" class="block-card">
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

    <!-- 每日签到 -->
    <el-card shadow="never" class="block-card">
      <template #header>每日签到</template>
      <div class="sign-section">
        <div class="sign-banner">
          <div class="sign-info">
            <div class="sign-desc">
              连续签到 <span class="highlight">{{ continuousDays }}</span> 天 · 总积分 <span class="highlight">{{ totalPoints }}</span>
            </div>
          </div>
          <el-button
            type="primary"
            size="large"
            :class="{ signed: signedToday }"
            :disabled="signedToday"
            :loading="store.signLoading"
            @click="handleSign"
          >
            {{ signedToday ? '✅ 今日已签' : '立即签到 +10' }}
          </el-button>
        </div>

        <div class="sign-calendar">
          <div class="calendar-title">最近签到记录</div>
          <div class="calendar-grid">
            <div
              v-for="(record, i) in signRecords"
              :key="i"
              class="calendar-day"
              :class="{ signed: record.points > 0 }"
            >
              <div class="day-date">{{ record.date.slice(5) }}</div>
              <div class="day-points">+{{ record.points }}</div>
            </div>
          </div>
        </div>

        <div class="points-rules">
          <div class="rules-title">🎁 积分规则</div>
          <ul>
            <li>每日签到 +10 积分</li>
            <li>连续签到 7 天额外奖励 +20 积分</li>
            <li>发布内容 +5 积分，被点赞 +1 积分</li>
            <li>回答问题被采纳 +20 积分</li>
            <li>上传资料通过审核 +15 积分</li>
          </ul>
        </div>
      </div>
    </el-card>
  </div>
</template>

<style scoped>
.profile-page {
  max-width: 900px;
  margin: 0 auto;
  padding: 20px;
}

.card-head {
  display: flex;
  justify-content: space-between;
  align-items: center;
}

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

.points-num {
  color: #e6a23c;
  font-weight: 700;
}

.block-card {
  margin-top: 16px;
}

/* ---- 签到与积分（前端 C 样式） ---- */
.sign-section {
  padding: 0 10px;
}

.sign-banner {
  background: linear-gradient(135deg, #fdfbfb 0%, #ebedee 100%);
  border-radius: 12px;
  padding: 20px 24px;
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 20px;
}

.sign-desc {
  font-size: 15px;
  color: #606266;
}

.highlight {
  color: #f56c6c;
  font-weight: 700;
}

.sign-banner .el-button.signed {
  background: #67c23a;
  border-color: #67c23a;
}

.sign-calendar {
  margin-bottom: 20px;
}

.calendar-title {
  font-size: 15px;
  font-weight: 600;
  color: #303133;
  margin-bottom: 12px;
}

.calendar-grid {
  display: flex;
  gap: 10px;
  flex-wrap: wrap;
}

.calendar-day {
  width: 70px;
  padding: 10px;
  border-radius: 10px;
  background: #f5f7fa;
  text-align: center;
  transition: all 0.2s;
}

.calendar-day.signed {
  background: linear-gradient(135deg, #67c23a, #85ce61);
  color: #fff;
}

.day-date {
  font-size: 13px;
  font-weight: 600;
}

.day-points {
  font-size: 11px;
  margin-top: 2px;
  opacity: 0.8;
}

.points-rules {
  background: #fdf6ec;
  border-radius: 10px;
  padding: 16px 20px;
}

.rules-title {
  font-weight: 600;
  color: #e6a23c;
  margin-bottom: 8px;
}

.points-rules ul {
  margin: 0;
  padding-left: 20px;
}

.points-rules li {
  font-size: 13px;
  color: #606266;
  line-height: 2;
}
</style>
