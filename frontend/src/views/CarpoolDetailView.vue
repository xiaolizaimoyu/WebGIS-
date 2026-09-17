<script setup>
// 拼车详情页（归属：前端 C）——路线地图 + 申请状态通知 + 发起人/申请人聊天
import { onMounted, ref, reactive, nextTick } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { ElMessage } from 'element-plus'
import * as carpoolApi from '@/api/carpool'
import { formatTime } from '@/api/const'
import { getMockCarpoolDetail } from '@/utils/mockData'
import { useUserStore } from '@/stores/user'
import { useDialogStore } from '@/stores/dialog'
import MapComponent from '@/components/MapComponent.vue'

const route = useRoute()
const router = useRouter()
const store = useUserStore()
const dialog = useDialogStore()

const carpoolId = Number(route.params.id)
const carpool = ref(null)
const mapRef = ref(null)

// 淄博校区周边及目的地坐标（用于路线地图）
const locationCoords = {
  '学校南门': [117.996, 36.806],
  '学校北门': [117.996, 36.814],
  '学校东门': [118.004, 36.810],
  '学校西门': [117.988, 36.810],
  '泰山风景区': [117.106, 36.253],
  '济南火车站': [117.000, 36.651],
  '淄博北站': [118.043, 36.849]
}

// 申请弹窗
const applyVisible = ref(false)
const applyForm = reactive({ name: '', phone: '', people_count: 1, remark: '' })
const applying = ref(false)

// 申请状态（mock）
const myApplication = ref(null) // { status: 'pending'|'approved'|'rejected', name, phone, time }

// 申请人列表（发起人视角）
const applicants = ref([
  { id: 1, name: '李同学', phone: '138****1234', people_count: 1, remark: '行李少', status: 'pending', time: '10分钟前' },
  { id: 2, name: '张同学', phone: '139****5678', people_count: 2, remark: '两人一起', status: 'approved', time: '1小时前' }
])

// 聊天功能
const chatMessages = ref([
  { id: 1, sender: 'organizer', text: '你好，拼车时间和地点都确认了吗？', time: '10:30' },
  { id: 2, sender: 'me', text: '是的，我周六早上在南门集合', time: '10:32' },
  { id: 3, sender: 'organizer', text: '好的，费用80元每人，出发前一天再联系你', time: '10:35' }
])
const chatInput = ref('')
const chatEndRef = ref(null)

// 判断当前用户是否是发起人
const isAuthor = computed(() => {
  if (!carpool.value || !store.userInfo) return false
  return carpool.value.author_name === store.userInfo.nickname
})

import { computed } from 'vue'

// 地图标记
const mapMarkers = ref([])

async function loadDetail() {
  try {
    carpool.value = await carpoolApi.getCarpool(carpoolId)
  } catch {
    carpool.value = getMockCarpoolDetail(carpoolId)
  }
  // 设置地图标记和路线
  nextTick(() => {
    const fromCoord = locationCoords[carpool.value.from] || [117.996, 36.809]
    const toCoord = locationCoords[carpool.value.to] || [118.05, 36.85]
    mapMarkers.value = [
      { id: 'start', lng: fromCoord[0], lat: fromCoord[1], title: carpool.value.from, color: '#67c23a' },
      { id: 'end', lng: toCoord[0], lat: toCoord[1], title: carpool.value.to, color: '#f56c6c' }
    ]
    nextTick(() => {
      if (mapRef.value) {
        mapRef.value.drawRoute(fromCoord, toCoord)
      }
    })
  })
}

// 打开申请弹窗
function openApplyDialog() {
  if (!store.isLoggedIn) {
    ElMessage.warning('请先登录后再申请拼车')
    router.push({ path: '/login', query: { redirect: route.fullPath } })
    return
  }
  if (carpool.value.seats_left <= 0) {
    ElMessage.warning('该拼车已满员')
    return
  }
  applyForm.name = store.userInfo?.nickname || ''
  applyForm.phone = ''
  applyForm.people_count = 1
  applyForm.remark = ''
  applyVisible.value = true
}

// 提交申请
async function submitApply() {
  if (!applyForm.name.trim()) { ElMessage.warning('请填写姓名'); return }
  if (!applyForm.phone.trim()) { ElMessage.warning('请填写联系电话'); return }
  applying.value = true
  try {
    await carpoolApi.applyCarpool(carpoolId, { ...applyForm })
  } catch { /* mock */ }
  applying.value = false
  applyVisible.value = false
  // 记录申请状态
  myApplication.value = { status: 'pending', name: applyForm.name, time: '刚刚' }
  dialog.open({
    title: '申请成功',
    content: `您已成功申请「${carpool.value.title}」，发起人确认后会通过消息通知您。`,
    type: 'success',
    confirmText: '知道了'
  })
}

// 发起人：同意申请
function approveApplication(app) {
  app.status = 'approved'
  carpool.value.seats_left = Math.max(0, carpool.value.seats_left - app.people_count)
  // 弹出消息通知（模拟实时推送）
  ElMessage.success(`已同意 ${app.name} 的申请`)
  dialog.open({
    title: '申请已通过',
    content: `您已通过 ${app.name} 的拼车申请，请及时联系对方确认上车时间和地点。`,
    type: 'success',
    confirmText: '知道了'
  })
  // 模拟给申请人发消息
  chatMessages.value.push({
    id: Date.now(),
    sender: 'organizer',
    text: `${app.name} 的申请已通过，请保持电话畅通，出发前联系。`,
    time: nowTime()
  })
  scrollChatToBottom()
}

// 发起人：拒绝申请
function rejectApplication(app) {
  app.status = 'rejected'
  ElMessage.info(`已拒绝 ${app.name} 的申请`)
  dialog.open({
    title: '申请已拒绝',
    content: `您已拒绝 ${app.name} 的拼车申请。`,
    type: 'warning',
    confirmText: '知道了'
  })
}

// 发送聊天消息
function sendMessage() {
  const text = chatInput.value.trim()
  if (!text) return
  chatMessages.value.push({
    id: Date.now(),
    sender: 'me',
    text: text,
    time: nowTime()
  })
  chatInput.value = ''
  scrollChatToBottom()
  // 模拟自动回复
  setTimeout(() => {
    chatMessages.value.push({
      id: Date.now() + 1,
      sender: 'organizer',
      text: '收到，没问题！',
      time: nowTime()
    })
    scrollChatToBottom()
  }, 1000)
}

function scrollChatToBottom() {
  nextTick(() => {
    if (chatEndRef.value) chatEndRef.value.scrollTop = chatEndRef.value.scrollHeight
  })
}

function nowTime() {
  const d = new Date()
  return `${String(d.getHours()).padStart(2, '0')}:${String(d.getMinutes()).padStart(2, '0')}`
}

onMounted(loadDetail)
</script>

<template>
  <div class="page-container" v-if="carpool">
    <el-card shadow="never" class="detail-card">
      <div class="card-head">
        <el-tag type="warning" size="large">🚗 拼车</el-tag>
        <el-tag :type="carpool.seats_left > 0 ? 'success' : 'info'" size="large">
          {{ carpool.seats_left > 0 ? '招募中' : '已满员' }}
        </el-tag>
      </div>
      <h1 class="title">{{ carpool.title }}</h1>

      <!-- 路线信息 -->
      <div class="route-box">
        <div class="route-point">
          <div class="point-dot start"></div>
          <div class="point-info">
            <div class="point-label">出发地</div>
            <div class="point-name">{{ carpool.from }}</div>
          </div>
        </div>
        <div class="route-line"></div>
        <div class="route-point">
          <div class="point-dot end"></div>
          <div class="point-info">
            <div class="point-label">目的地</div>
            <div class="point-name">{{ carpool.to }}</div>
          </div>
        </div>
      </div>

      <!-- 行程路线地图 -->
      <div class="map-section">
        <div class="section-title">🗺️ 行程路线</div>
        <MapComponent
          ref="mapRef"
          :center="[117.996, 36.809]"
          :zoom="11"
          :markers="mapMarkers"
          height="280px"
        />
      </div>

      <div class="info-grid">
        <div class="info-item">
          <span class="info-label">🕐 出发时间</span>
          <span class="info-value">{{ carpool.depart_time }}</span>
        </div>
        <div class="info-item" v-if="carpool.return_time">
          <span class="info-label">↩️ 返回时间</span>
          <span class="info-value">{{ carpool.return_time }}</span>
        </div>
        <div class="info-item">
          <span class="info-label">💰 费用</span>
          <span class="info-value price">{{ carpool.price_per_person }} 元/人</span>
        </div>
        <div class="info-item">
          <span class="info-label">🪑 座位</span>
          <span class="info-value">剩余 {{ carpool.seats_left }} / {{ carpool.seats_total }} 座</span>
        </div>
        <div class="info-item">
          <span class="info-label">👤 发布者</span>
          <span class="info-value">{{ carpool.author_name }}</span>
        </div>
        <div class="info-item">
          <span class="info-label">📱 联系方式</span>
          <span class="info-value">{{ carpool.phone }}</span>
        </div>
      </div>

      <div class="note-box">
        <div class="note-title">📝 备注说明</div>
        <p>{{ carpool.note }}</p>
      </div>

      <!-- 我的申请状态（申请人视角） -->
      <div class="status-box" v-if="myApplication">
        <div class="section-title">📋 我的申请</div>
        <el-alert
          :title="myApplication.status === 'approved' ? '✅ 申请已通过！发起人会尽快联系你' : myApplication.status === 'rejected' ? '❌ 申请未通过，可尝试其他拼车' : '⏳ 申请待确认，发起人正在审核中...'"
          :type="myApplication.status === 'approved' ? 'success' : myApplication.status === 'rejected' ? 'error' : 'warning'"
          :closable="false"
          show-icon
        />
      </div>

      <!-- 申请管理（发起人视角） -->
      <div class="applicants-section" v-if="isAuthor">
        <div class="section-title">👥 申请管理（{{ applicants.length }}人）</div>
        <div v-for="app in applicants" :key="app.id" class="applicant-item">
          <div class="applicant-info">
            <div class="applicant-name">{{ app.name }}</div>
            <div class="applicant-meta">{{ app.phone }} · {{ app.people_count }}人 · {{ app.time }}</div>
            <div class="applicant-remark" v-if="app.remark">备注：{{ app.remark }}</div>
          </div>
          <div class="applicant-actions">
            <el-tag v-if="app.status === 'pending'" type="warning" size="small">待确认</el-tag>
            <el-tag v-else-if="app.status === 'approved'" type="success" size="small">已通过</el-tag>
            <el-tag v-else type="danger" size="small">已拒绝</el-tag>
            <template v-if="app.status === 'pending'">
              <el-button type="success" size="small" @click="approveApplication(app)">同意</el-button>
              <el-button type="danger" size="small" plain @click="rejectApplication(app)">拒绝</el-button>
            </template>
          </div>
        </div>
      </div>

      <!-- 聊天框 -->
      <div class="chat-section">
        <div class="section-title">💬 拼车沟通</div>
        <div class="chat-box" ref="chatEndRef">
          <div
            v-for="msg in chatMessages"
            :key="msg.id"
            class="chat-msg"
            :class="msg.sender === 'me' ? 'mine' : 'theirs'"
          >
            <div class="bubble">
              <div class="bubble-text">{{ msg.text }}</div>
              <div class="bubble-time">{{ msg.time }}</div>
            </div>
          </div>
        </div>
        <div class="chat-input-bar">
          <el-input
            v-model="chatInput"
            placeholder="输入消息..."
            @keyup.enter="sendMessage"
            maxlength="200"
          />
          <el-button type="primary" @click="sendMessage">发送</el-button>
        </div>
      </div>

      <div class="actions">
        <el-button
          type="primary"
          size="large"
          :disabled="carpool.seats_left <= 0 || myApplication"
          @click="openApplyDialog"
        >
          {{ myApplication ? '已申请' : (carpool.seats_left > 0 ? '🙋 申请加入' : '已满员') }}
        </el-button>
        <el-button size="large" @click="router.back()">← 返回列表</el-button>
      </div>
    </el-card>

    <!-- 申请弹窗 -->
    <el-dialog v-model="applyVisible" title="申请加入拼车" width="480px" :close-on-click-modal="false">
      <el-form label-width="90px">
        <el-form-item label="姓名" required>
          <el-input v-model="applyForm.name" placeholder="请输入您的姓名" />
        </el-form-item>
        <el-form-item label="联系电话" required>
          <el-input v-model="applyForm.phone" placeholder="请输入手机号码" />
        </el-form-item>
        <el-form-item label="人数">
          <el-input-number v-model="applyForm.people_count" :min="1" :max="carpool.seats_left" />
          <span class="hint">（最多 {{ carpool.seats_left }} 人）</span>
        </el-form-item>
        <el-form-item label="备注">
          <el-input v-model="applyForm.remark" type="textarea" :rows="2" placeholder="有特殊需求可备注" />
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="applyVisible = false">取消</el-button>
        <el-button type="primary" :loading="applying" @click="submitApply">提交申请</el-button>
      </template>
    </el-dialog>
  </div>
</template>

<style scoped>
.page-container { max-width: 800px; margin: 0 auto; padding: 20px; }
.detail-card { border-radius: 12px; }
.card-head { display: flex; gap: 8px; margin-bottom: 12px; }
.title { font-size: 24px; color: #303133; margin: 0 0 20px 0; }

.route-box {
  background: linear-gradient(135deg, #fdf6ec, #fff);
  border-radius: 12px; padding: 20px; margin-bottom: 16px;
  display: flex; align-items: center; gap: 16px;
}
.route-point { display: flex; align-items: center; gap: 10px; flex: 1; }
.point-dot { width: 14px; height: 14px; border-radius: 50%; flex-shrink: 0; }
.point-dot.start { background: #67c23a; box-shadow: 0 0 0 4px rgba(103,194,58,0.2); }
.point-dot.end { background: #f56c6c; box-shadow: 0 0 0 4px rgba(245,108,108,0.2); }
.point-label { font-size: 12px; color: #909399; }
.point-name { font-size: 16px; font-weight: 600; color: #303133; }
.route-line {
  flex: 0 0 60px; height: 2px;
  background: linear-gradient(90deg, #67c23a, #f56c6c); position: relative;
}
.route-line::after {
  content: '→'; position: absolute; top: 50%; left: 50%;
  transform: translate(-50%, -50%); background: #fff; padding: 0 4px;
  color: #e6a23c; font-weight: bold;
}

.map-section { margin-bottom: 20px; }
.section-title { font-size: 16px; font-weight: 600; color: #303133; margin-bottom: 10px; }

.info-grid { display: grid; grid-template-columns: 1fr 1fr; gap: 16px; margin-bottom: 20px; }
.info-item { display: flex; flex-direction: column; gap: 4px; }
.info-label { font-size: 12px; color: #909399; }
.info-value { font-size: 15px; color: #303133; font-weight: 500; }
.info-value.price { color: #f56c6c; font-size: 18px; font-weight: 700; }

.note-box { background: #f5f7fa; border-radius: 10px; padding: 16px; margin-bottom: 20px; }
.note-title { font-weight: 600; color: #303133; margin-bottom: 8px; }
.note-box p { color: #606266; font-size: 14px; line-height: 1.7; margin: 0; }

.status-box { margin-bottom: 20px; }

.applicants-section { margin-bottom: 20px; }
.applicant-item {
  display: flex; justify-content: space-between; align-items: center;
  background: #f9fafc; border-radius: 10px; padding: 12px 16px; margin-bottom: 8px;
}
.applicant-name { font-weight: 600; color: #303133; font-size: 15px; }
.applicant-meta { font-size: 12px; color: #909399; margin-top: 2px; }
.applicant-remark { font-size: 13px; color: #606266; margin-top: 4px; }
.applicant-actions { display: flex; gap: 8px; align-items: center; }

.chat-section { margin-bottom: 20px; }
.chat-box {
  height: 300px; overflow-y: auto; background: #f5f7fa;
  border-radius: 12px; padding: 16px; margin-bottom: 10px;
}
.chat-msg { display: flex; margin-bottom: 12px; }
.chat-msg.mine { justify-content: flex-end; }
.bubble {
  max-width: 70%; padding: 10px 14px; border-radius: 12px;
  font-size: 14px; line-height: 1.5;
}
.chat-msg.mine .bubble {
  background: #409eff; color: #fff; border-bottom-right-radius: 4px;
}
.chat-msg.theirs .bubble {
  background: #fff; color: #303133; border-bottom-left-radius: 4px;
  box-shadow: 0 1px 2px rgba(0,0,0,0.08);
}
.bubble-time { font-size: 11px; opacity: 0.7; margin-top: 4px; }
.chat-input-bar { display: flex; gap: 10px; }
.chat-input-bar .el-input { flex: 1; }

.actions { display: flex; gap: 12px; justify-content: center; }
.hint { font-size: 12px; color: #909399; margin-left: 8px; }
</style>
