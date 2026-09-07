<script setup>
// 拼车详情页（前端 C）——申请提交后待车主确认；车主可同意/拒绝；申请人可取消
import { onMounted, ref, reactive, computed } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { ElMessage, ElMessageBox } from 'element-plus'
import * as carpoolApi from '@/api/carpool'
import { getMockCarpoolDetail } from '@/utils/mockData'
import { useUserStore } from '@/stores/user'
import { useDialogStore } from '@/stores/dialog'

const route = useRoute()
const router = useRouter()
const store = useUserStore()
const dialog = useDialogStore()

const carpoolId = Number(route.params.id)
const carpool = ref(null)

// 申请弹窗
const applyVisible = ref(false)
const applyForm = reactive({
  name: '',
  phone: '',
  people_count: 1,
  remark: ''
})
const applying = ref(false)

// 车主管理弹窗
const appsVisible = ref(false)
const appList = ref([])
const appsLoading = ref(false)

// 我的申请状态（由后端详情返回 my_application）
const myApp = computed(() => carpool.value?.my_application || null)
const isAuthor = computed(() => !!carpool.value?.is_author)

async function loadDetail() {
  try {
    carpool.value = await carpoolApi.getCarpool(carpoolId)
  } catch {
    carpool.value = getMockCarpoolDetail(carpoolId)
  }
}

// 打开申请弹窗
function openApplyDialog() {
  if (!store.isLoggedIn) {
    ElMessage.warning('请先登录后再申请拼车')
    router.push({ path: '/login', query: { redirect: route.fullPath } })
    return
  }
  if (isAuthor.value) {
    ElMessage.warning('这是您发布的拼车，不能申请')
    return
  }
  if (carpool.value.seats_left <= 0) {
    ElMessage.warning('该拼车已满员')
    return
  }
  if (myApp.value && myApp.value.status === 'pending') {
    ElMessage.warning('您已提交申请，等待车主确认中')
    return
  }
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
  const phone = applyForm.phone.trim()
  if (!phone) {
    ElMessage.warning('请填写联系电话')
    return
  }
  if (!/^1\d{10}$/.test(phone)) {
    ElMessage.warning('手机号需为 11 位数字（如 13812345678）')
    return
  }
  applying.value = true
  try {
    await carpoolApi.applyCarpool(carpoolId, { ...applyForm })
    ElMessage.success('申请已提交，等待车主确认')
    applyVisible.value = false
    loadDetail() // 刷新我的申请状态
    dialog.open({
      title: '申请已提交',
      content: `您已成功申请「${carpool.value.title}」，车主确认后会通过消息通知您，也可以在详情页取消申请。`,
      type: 'success',
      confirmText: '知道了'
    })
  } catch (e) {
    ElMessage.error(e?.response?.data?.detail || '申请失败，请稍后重试')
  } finally {
    applying.value = false
  }
}

// 取消申请（申请人本人，待确认/已拒绝状态可取消）
async function cancelMyApplication() {
  const a = myApp.value
  if (!a) return
  try {
    await ElMessageBox.confirm('确定取消这条申请吗？', '取消申请', {
      confirmButtonText: '取消申请',
      cancelButtonText: '再想想',
      type: 'warning'
    })
  } catch {
    return
  }
  try {
    await carpoolApi.cancelApplication(carpoolId, a.id)
    ElMessage.success('已取消申请')
    loadDetail()
  } catch (e) {
    ElMessage.error(e?.response?.data?.detail || '取消失败')
  }
}

// ===== 车主管理 =====
async function openAppsDialog() {
  appsVisible.value = true
  appsLoading.value = true
  try {
    const data = await carpoolApi.listApplications(carpoolId)
    appList.value = data.items || []
  } catch (e) {
    ElMessage.error(e?.response?.data?.detail || '申请列表加载失败')
    appsVisible.value = false
  } finally {
    appsLoading.value = false
  }
}

async function handleApprove(a) {
  try {
    const data = await carpoolApi.approveApplication(carpoolId, a.id)
    ElMessage.success(`已同意 ${a.applicant_name} 的申请，剩余座位 ${data.seats_left}`)
    loadDetail()
    openAppsDialog()
  } catch (e) {
    ElMessage.error(e?.response?.data?.detail || '操作失败')
  }
}

async function handleReject(a) {
  try {
    await carpoolApi.rejectApplication(carpoolId, a.id)
    ElMessage.success(`已拒绝 ${a.applicant_name} 的申请`)
    loadDetail()
    openAppsDialog()
  } catch (e) {
    ElMessage.error(e?.response?.data?.detail || '操作失败')
  }
}

// 编辑 / 删除（仅作者）
function toEdit() {
  router.push(`/carpool/publish/${carpoolId}`)
}

async function removeCarpool() {
  try {
    await ElMessageBox.confirm(`确定删除「${carpool.value.title}」吗？删除后不可恢复。`, '删除拼车', {
      confirmButtonText: '删除',
      cancelButtonText: '取消',
      type: 'warning'
    })
  } catch {
    return
  }
  try {
    await carpoolApi.deleteCarpool(carpoolId)
    ElMessage.success('删除成功')
    router.replace('/carpool')
  } catch (e) {
    ElMessage.error(e?.response?.data?.detail || '删除失败')
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
        <el-badge
          v-if="isAuthor && carpool.pending_count > 0"
          :value="carpool.pending_count"
          class="pending-badge"
        >
          <el-button size="small" type="warning" plain @click="openAppsDialog">待确认申请</el-button>
        </el-badge>
        <el-button
          v-else-if="isAuthor"
          size="small"
          plain
          @click="openAppsDialog"
        >查看申请</el-button>
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

      <!-- 我的申请状态 -->
      <div v-if="myApp && myApp.status !== 'cancelled'" class="my-app-box" :class="myApp.status">
        <template v-if="myApp.status === 'pending'">
          <span>⏳ 您已提交申请（{{ myApp.people_count }} 人），等待车主确认</span>
          <el-button size="small" type="danger" plain @click="cancelMyApplication">取消申请</el-button>
        </template>
        <template v-else-if="myApp.status === 'approved'">
          <span>✅ 车主已同意您的申请（{{ myApp.people_count }} 人），请按时赴约</span>
        </template>
        <template v-else-if="myApp.status === 'rejected'">
          <span>❌ 您的申请被车主拒绝了</span>
        </template>
      </div>

      <div class="note-box">
        <div class="note-title">📝 备注说明</div>
        <p>{{ carpool.note }}</p>
      </div>

      <div class="actions">
        <!-- 申请人视角：待确认时显示取消；否则显示申请按钮 -->
        <template v-if="!isAuthor">
          <el-button
            v-if="!myApp || myApp.status !== 'pending'"
            type="primary"
            size="large"
            :disabled="carpool.seats_left <= 0"
            @click="openApplyDialog"
          >
            {{ carpool.seats_left > 0 ? '🙋 申请加入' : '已满员' }}
          </el-button>
          <el-button
            v-else
            type="warning"
            size="large"
            plain
            @click="cancelMyApplication"
          >⏳ 等待确认，点击取消</el-button>
        </template>
        <template v-else>
          <el-button size="large" @click="toEdit">✏️ 编辑</el-button>
          <el-button type="danger" size="large" plain @click="removeCarpool">🗑️ 删除</el-button>
        </template>
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
          <el-input v-model="applyForm.phone" maxlength="11" placeholder="请输入 11 位手机号码" />
        </el-form-item>
        <el-form-item label="人数">
          <el-input-number v-model="applyForm.people_count" :min="1" :max="carpool.seats_total" />
          <span class="hint">（车主确认后占用 {{ carpool.seats_left }} 个剩余座位中的名额）</span>
        </el-form-item>
        <el-form-item label="备注">
          <el-input v-model="applyForm.remark" type="textarea" :rows="2" placeholder="有特殊需求可备注（如行李较多等）" />
        </el-form-item>
      </el-form>
      <div class="apply-tip">提交后需车主确认，不会立即占用座位。</div>
      <template #footer>
        <el-button @click="applyVisible = false">取消</el-button>
        <el-button type="primary" :loading="applying" @click="submitApply">提交申请</el-button>
      </template>
    </el-dialog>

    <!-- 车主：申请管理弹窗 -->
    <el-dialog v-model="appsVisible" title="拼车申请管理" width="560px">
      <div v-loading="appsLoading" class="app-list">
        <el-empty v-if="!appsLoading && !appList.length" description="暂无申请记录" />
        <div v-for="a in appList" :key="a.id" class="app-item">
          <div class="app-main">
            <div class="app-name">{{ a.applicant_name }}
              <el-tag
                size="small"
                :type="a.status === 'pending' ? 'warning' : (a.status === 'approved' ? 'success' : (a.status === 'rejected' ? 'danger' : 'info'))"
              >
                {{ a.status === 'pending' ? '待确认' : (a.status === 'approved' ? '已同意' : (a.status === 'rejected' ? '已拒绝' : '已取消')) }}
              </el-tag>
            </div>
            <div class="app-meta">📱 {{ a.phone }} · 👥 {{ a.people_count }} 人 · {{ a.created_at.slice(0, 16) }}</div>
            <div v-if="a.remark" class="app-remark">备注：{{ a.remark }}</div>
          </div>
          <div v-if="a.status === 'pending'" class="app-ops">
            <el-button size="small" type="success" @click="handleApprove(a)">同意</el-button>
            <el-button size="small" type="danger" plain @click="handleReject(a)">拒绝</el-button>
          </div>
        </div>
      </div>
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
  align-items: center;
  flex-wrap: wrap;
}

.pending-badge {
  margin-left: 4px;
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

.my-app-box {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 10px;
  padding: 12px 16px;
  border-radius: 10px;
  margin-bottom: 16px;
  font-size: 14px;
}

.my-app-box.pending { background: #fdf6ec; color: #b88230; }
.my-app-box.approved { background: #f0f9eb; color: #529b2e; }
.my-app-box.rejected { background: #fef0f0; color: #c45656; }

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
  flex-wrap: wrap;
}

.hint {
  font-size: 12px;
  color: #909399;
  margin-left: 8px;
}

.apply-tip {
  font-size: 12px;
  color: #909399;
  margin-top: -8px;
  margin-bottom: 8px;
}

.app-list {
  max-height: 420px;
  overflow-y: auto;
}

.app-item {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 10px;
  padding: 12px;
  border-bottom: 1px solid #f0f0f0;
}

.app-item:last-child { border-bottom: none; }

.app-main { flex: 1; min-width: 0; }

.app-name {
  font-weight: 600;
  color: #303133;
  display: flex;
  align-items: center;
  gap: 8px;
}

.app-meta {
  font-size: 12px;
  color: #909399;
  margin-top: 4px;
}

.app-remark {
  font-size: 12px;
  color: #606266;
  margin-top: 4px;
  word-break: break-all;
}

.app-ops {
  display: flex;
  gap: 6px;
  flex-shrink: 0;
}
</style>
