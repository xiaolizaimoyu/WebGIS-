<script setup>
// 拼车详情页（归属：前端 C）——含全局申请弹窗整合
import { onMounted, ref, reactive } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { ElMessage } from 'element-plus'
import * as carpoolApi from '@/api/carpool'
import { formatTime } from '@/api/const'
import { getMockCarpoolDetail } from '@/utils/mockData'
import { useUserStore } from '@/stores/user'
import { useDialogStore } from '@/stores/dialog'

const route = useRoute()
const router = useRouter()
const store = useUserStore()
const dialog = useDialogStore()

const carpoolId = Number(route.params.id)
const carpool = ref(null)

// 申请弹窗（全局整合：使用 dialog store 统一管理）
const applyVisible = ref(false)
const applyForm = reactive({
  name: '',
  phone: '',
  people_count: 1,
  remark: ''
})
const applying = ref(false)

async function loadDetail() {
  try {
    carpool.value = await carpoolApi.getCarpool(carpoolId)
  } catch {
    carpool.value = getMockCarpoolDetail(carpoolId)
  }
}

// 打开申请弹窗 —— 全局整合入口
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
  // 预填用户信息
  applyForm.name = store.userInfo?.nickname || ''
  applyForm.phone = ''
  applyForm.people_count = 1
  applyForm.remark = ''
  applyVisible.value = true
}

async function submitApply() {
  if (!applyForm.name.trim()) {
    ElMessage.warning('请填写姓名')
    return
  }
  if (!applyForm.phone.trim()) {
    ElMessage.warning('请填写联系电话')
    return
  }
  applying.value = true
  try {
    await carpoolApi.applyCarpool(carpoolId, { ...applyForm })
    ElMessage.success('申请已提交，等待车主确认')
    applyVisible.value = false
    // 全局弹窗提示
    dialog.open({
      title: '申请成功',
      content: `您已成功申请「${carpool.value.title}」，车主确认后会通过消息通知您。`,
      type: 'success',
      confirmText: '知道了'
    })
  } catch {
    // mock 模式
    ElMessage.success('申请已提交（模拟）')
    applyVisible.value = false
    dialog.open({
      title: '申请成功',
      content: `您已成功申请「${carpool.value.title}」，车主确认后会通过消息通知您。`,
      type: 'success',
      confirmText: '知道了'
    })
  } finally {
    applying.value = false
  }
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

      <div class="actions">
        <el-button
          type="primary"
          size="large"
          :disabled="carpool.seats_left <= 0"
          @click="openApplyDialog"
        >
          {{ carpool.seats_left > 0 ? '🙋 申请加入' : '已满员' }}
        </el-button>
        <el-button size="large" @click="router.back()">← 返回列表</el-button>
      </div>
    </el-card>

    <!-- 申请弹窗（全局整合） -->
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
          <el-input v-model="applyForm.remark" type="textarea" :rows="2" placeholder="有特殊需求可备注（如行李较多等）" />
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
.page-container {
  max-width: 800px;
  margin: 0 auto;
  padding: 20px;
}

.detail-card {
  border-radius: 12px;
}

.card-head {
  display: flex;
  gap: 8px;
  margin-bottom: 12px;
}

.title {
  font-size: 24px;
  color: #303133;
  margin: 0 0 20px 0;
}

.route-box {
  background: linear-gradient(135deg, #fdf6ec, #fff);
  border-radius: 12px;
  padding: 20px;
  margin-bottom: 20px;
  display: flex;
  align-items: center;
  gap: 16px;
}

.route-point {
  display: flex;
  align-items: center;
  gap: 10px;
  flex: 1;
}

.point-dot {
  width: 14px;
  height: 14px;
  border-radius: 50%;
  flex-shrink: 0;
}

.point-dot.start {
  background: #67c23a;
  box-shadow: 0 0 0 4px rgba(103, 194, 58, 0.2);
}

.point-dot.end {
  background: #f56c6c;
  box-shadow: 0 0 0 4px rgba(245, 108, 108, 0.2);
}

.point-label {
  font-size: 12px;
  color: #909399;
}

.point-name {
  font-size: 16px;
  font-weight: 600;
  color: #303133;
}

.route-line {
  flex: 0 0 60px;
  height: 2px;
  background: linear-gradient(90deg, #67c23a, #f56c6c);
  position: relative;
}

.route-line::after {
  content: '→';
  position: absolute;
  top: 50%;
  left: 50%;
  transform: translate(-50%, -50%);
  background: #fff;
  padding: 0 4px;
  color: #e6a23c;
  font-weight: bold;
}

.info-grid {
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: 16px;
  margin-bottom: 20px;
}

.info-item {
  display: flex;
  flex-direction: column;
  gap: 4px;
}

.info-label {
  font-size: 12px;
  color: #909399;
}

.info-value {
  font-size: 15px;
  color: #303133;
  font-weight: 500;
}

.info-value.price {
  color: #f56c6c;
  font-size: 18px;
  font-weight: 700;
}

.note-box {
  background: #f5f7fa;
  border-radius: 10px;
  padding: 16px;
  margin-bottom: 20px;
}

.note-title {
  font-weight: 600;
  color: #303133;
  margin-bottom: 8px;
}

.note-box p {
  color: #606266;
  font-size: 14px;
  line-height: 1.7;
  margin: 0;
}

.actions {
  display: flex;
  gap: 12px;
  justify-content: center;
}

.hint {
  font-size: 12px;
  color: #909399;
  margin-left: 8px;
}
</style>
