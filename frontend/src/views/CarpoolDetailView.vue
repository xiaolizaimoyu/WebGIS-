<script setup>
// 拼车详情页（前端 C）——申请提交后待车主确认；车主可同意/拒绝；申请人可取消
// 功能：① 申请加入拼车（待车主确认，可取消）② 车主同意/拒绝申请 ③ 行程路线地图（出发/到达标记+橙色虚线）④ 与发起人聊天（演示）
import { onMounted, onBeforeUnmount, ref, reactive, computed, nextTick } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { ElMessage, ElMessageBox } from 'element-plus'
import * as carpoolApi from '@/api/carpool'
import { getMockCarpoolDetail } from '@/utils/mockData'
import { useUserStore } from '@/stores/user'
import { useDialogStore } from '@/stores/dialog'
import MapComponent from '@/components/MapComponent.vue'
import request from '@/api/request'
import { loadAMapPlugins } from '@/components/map/amap-loader'

const route = useRoute()
const router = useRouter()
const store = useUserStore()
const dialog = useDialogStore()

const carpoolId = Number(route.params.id)
const carpool = ref(null)

// 行程路线地图
const mapRef = ref(null)
const mapMarkers = ref([])
// 淄博校区周边及目的地坐标（GCJ-02，用于路线地图展示；未命中的地点回退到校园中心附近）
const locationCoords = {
  '学校南门': [117.9985, 36.8060],
  '学校北门': [117.9975, 36.8145],
  '学校东门': [118.0050, 36.8100],
  '学校西门': [117.9890, 36.8100],
  '第一食堂': [118.0030, 36.8090],
  '第二食堂': [118.0080, 36.8120],
  '图书馆': [118.0045, 36.8085],
  '泰山风景区': [117.1060, 36.2530],
  '济南火车站': [117.0000, 36.6510],
  '淄博北站': [118.0430, 36.8490]
}
// 地点库（后端 /api/locations 管理员手动校准的真实坐标，校园内优先使用）
const placeLib = ref([])
// 高德 POI 名称 → 校园地点库别名映射（拼车地点常用叫法与库中名称对齐）
const placeAlias = {
  '学校北门': '北门',
  '学校南门': '南门',
  '学校东门': '东门',
  '学校西门': '西门',
  '第一食堂': '一餐',
  '第二食堂': '二餐',
  '图书馆': '逸夫图书馆'
}
// 解析地点坐标：① 校园地点库真实坐标 → ② 高德 POI 搜索 → ③ 前端坐标库 → ④ 默认回退
async function resolveCoord(name, fallback) {
  if (!name) return fallback
  const lib = placeLib.value
  // ① 校园地点库：精确匹配，再尝试别名匹配（如"学校北门"→"北门"）
  if (lib.length) {
    const exact = lib.find((p) => p.name === name)
    if (exact) return [Number(exact.lng), Number(exact.lat)]
    const alias = placeAlias[name]
    if (alias) {
      const hit = lib.find((p) => p.name === alias)
      if (hit) return [Number(hit.lng), Number(hit.lat)]
    }
    const fuzzy = lib.find((p) => name.includes(p.name) || p.name.includes(name))
    if (fuzzy) return [Number(fuzzy.lng), Number(fuzzy.lat)]
  }
  // ② 高德 POI 搜索（校外地点，如火车站/景区）
  try {
    const AMap = await loadAMapPlugins(['AMap.PlaceSearch'])
    const pos = await new Promise((resolve) => {
      const ps = new AMap.PlaceSearch({ city: '淄博', pageSize: 1, pageIndex: 1 })
      ps.search(name, (status, result) => {
        if (status === 'complete' && result?.poiList?.pois?.length) {
          const p = result.poiList.pois[0]
          resolve([p.location.getLng(), p.location.getLat()])
        } else {
          resolve(null)
        }
      })
    })
    if (pos) return pos
  } catch {
    /* 高德解析失败则继续回退 */
  }
  // ③ 前端坐标库回退
  if (locationCoords[name]) return locationCoords[name]
  // ④ 默认回退
  return fallback
}
async function coordOf(name, fallback) {
  return resolveCoord(name, fallback)
}

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

// 已加入成员（车主视角）
const joinedMembers = computed(() =>
  (appList.value || []).filter((a) => a.status === 'approved')
)

// 退出拼车（已加入成员）
async function quitCarpool() {
  try {
    await ElMessageBox.confirm('确定退出该拼车吗？退出后座位将释放。', '退出拼车', {
      type: 'warning',
      confirmButtonText: '退出',
      cancelButtonText: '再想想'
    })
  } catch {
    return
  }
  try {
    const a = myApp.value
    if (!a) return
    await carpoolApi.cancelApplication(carpool.value.id, a.id)
    ElMessage.success('已退出拼车，座位已释放')
    loadDetail()
  } catch (e) {
    ElMessage.error(e?.response?.data?.detail || '退出失败')
  }
}

// 车主移除已加入成员
async function handleRemoveMember(a) {
  try {
    await ElMessageBox.confirm(`确定将「${a.applicant_name}」移出拼车吗？座位将释放。`, '移除成员', {
      type: 'warning',
      confirmButtonText: '移除',
      cancelButtonText: '取消'
    })
  } catch {
    return
  }
  try {
    await carpoolApi.removeMember(carpool.value.id, a.id)
    ElMessage.success('已移除成员')
    loadApplications()
    loadDetail()
  } catch (e) {
    ElMessage.error(e?.response?.data?.detail || '移除失败')
  }
}

// 聊天功能（真实聊天：对接后端 carpool_messages 表，车主与已加入成员可收发）
const chatMessages = ref([])
const chatInput = ref('')
const chatEndRef = ref(null)
const chatListRef = ref(null)
const chatLoading = ref(false)
let chatTimer = null

// 是否有聊天权限（车主或已加入成员）
const canChat = computed(() => {
  if (!carpool.value) return false
  if (carpool.value.is_author) return true
  return myApp.value?.status === 'approved'
})

// 只在聊天列表内部滚动到底部（不影响整个页面位置）
function scrollChatToBottom(force) {
  const list = chatListRef.value
  if (!list) return
  const nearBottom = list.scrollHeight - list.scrollTop - list.clientHeight < 60
  if (force || nearBottom) {
    list.scrollTop = list.scrollHeight
  }
}

async function loadMessages(scroll = 'auto') {
  if (!canChat.value || !carpool.value) return
  try {
    const items = (await carpoolApi.listMessages(carpool.value.id))?.items || []
    chatMessages.value = items.map((m) => ({
      id: m.id,
      sender: m.sender_id === store.userInfo?.id ? 'me' : 'theirs',
      sender_name: m.sender_name,
      text: m.content,
      time: (m.created_at || '').slice(11, 16)
    }))
    // 发送消息后或本来就停在底部时，才在聊天列表内滚动到最新（不滚动整个页面）
    nextTick(() => {
      if (scroll === 'force') {
        scrollChatToBottom(true)
      } else {
        scrollChatToBottom(false)
      }
    })
  } catch {
    /* 无权限或失败时静默 */
  }
}

async function sendChat() {
  const text = chatInput.value.trim()
  if (!text) return
  if (!canChat.value) {
    ElMessage.warning('仅车主或已加入成员可发送消息')
    return
  }
  try {
    await carpoolApi.sendMessage(carpool.value.id, text)
    chatInput.value = ''
    await loadMessages('force')
  } catch (e) {
    ElMessage.error(e?.response?.data?.detail || '发送失败')
  }
}

async function loadDetail() {
  try {
    carpool.value = await carpoolApi.getCarpool(carpoolId)
  } catch {
    carpool.value = getMockCarpoolDetail(carpoolId)
  }
  // 加载校园地点库（管理员校准的真实坐标）
  try {
    placeLib.value = (await request.get('/locations')) || []
  } catch {
    /* 地点库加载失败则用前端坐标回退 */
  }
  // 设置行程路线地图：出发地/目的地标记，自动绘制真实驾车路线并缩放视野
  nextTick(async () => {
    if (!carpool.value) return
    const from = await coordOf(carpool.value.from, [117.9975, 36.8090])
    const to = await coordOf(carpool.value.to, [118.0430, 36.8490])
    mapMarkers.value = [
      { id: 'start', lng: from[0], lat: from[1], title: `出发：${carpool.value.from}`, color: '#67c23a' },
      { id: 'end', lng: to[0], lat: to[1], title: `到达：${carpool.value.to}`, color: '#f56c6c' }
    ]
    nextTick(() => {
      mapRef.value?.drawRoute?.(from, to)
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

onMounted(() => {
  loadDetail()
  // 聊天轮询（3 秒），退出页面自动清除
  chatTimer = setInterval(() => loadMessages(), 3000)
})

onBeforeUnmount(() => {
  if (chatTimer) clearInterval(chatTimer)
})
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
          <span>✅ 您已加入该拼车（{{ myApp.people_count }} 人），可与车主在下方沟通</span>
          <el-button size="small" type="danger" plain @click="quitCarpool">退出拼车</el-button>
        </template>
        <template v-else-if="myApp.status === 'rejected'">
          <span>❌ 您的申请被车主拒绝了</span>
        </template>
        <template v-else-if="myApp.status === 'removed'">
          <span>⚠️ 您已被车主移出该拼车</span>
        </template>
      </div>

      <div class="note-box">
        <div class="note-title">📝 备注说明</div>
        <p>{{ carpool.note }}</p>
      </div>

      <!-- 行程路线地图 -->
      <div class="map-box">
        <div class="map-box-title">🗺️ 行程路线</div>
        <MapComponent
          ref="mapRef"
          :markers="mapMarkers"
          :center="[117.9975, 36.8090]"
          :zoom="13"
          height="320px"
        />
        <div class="map-legend">
          <span class="legend-item"><i class="legend-dot start-dot"></i>出发地（绿）</span>
          <span class="legend-item"><i class="legend-dot end-dot"></i>目的地（红）</span>
          <span class="legend-item"><i class="legend-line"></i>行程路线（真实驾车路线）</span>
        </div>
      </div>

      <!-- 聊天（真实消息，车主与已加入成员） -->
      <div class="chat-box">
        <div class="chat-box-title">💬 与发起人沟通</div>
        <template v-if="canChat">
          <div v-loading="chatLoading" ref="chatListRef" class="chat-list">
            <el-empty
              v-if="!chatMessages.length"
              description="暂无消息，打个招呼吧～"
              :image-size="60"
            />
            <div
              v-for="m in chatMessages"
              :key="m.id"
              class="chat-msg"
              :class="m.sender === 'me' ? 'mine' : 'theirs'"
            >
              <div class="chat-sender">{{ m.sender_name }}</div>
              <div class="chat-bubble">{{ m.text }}</div>
              <div class="chat-time">{{ m.time }}</div>
            </div>
            <div ref="chatEndRef"></div>
          </div>
          <div class="chat-input-row">
            <el-input
              v-model="chatInput"
              placeholder="输入消息，回车发送"
              maxlength="500"
              @keyup.enter="sendChat"
            />
            <el-button type="primary" @click="sendChat">发送</el-button>
          </div>
        </template>
        <div v-else class="chat-no-perm">
          🔒 加入拼车后可查看并与车主沟通
        </div>
      </div>

      <div class="actions">
        <!-- 申请人视角：待确认时显示取消；已加入时显示已加入+退出；否则显示申请按钮 -->
        <template v-if="!isAuthor">
          <el-button
            v-if="!myApp || (myApp.status !== 'pending' && myApp.status !== 'approved')"
            type="primary"
            size="large"
            :disabled="carpool.seats_left <= 0"
            @click="openApplyDialog"
          >
            {{ carpool.seats_left > 0 ? '🙋 申请加入' : '已满员' }}
          </el-button>
          <el-button
            v-else-if="myApp.status === 'pending'"
            type="warning"
            size="large"
            plain
            @click="cancelMyApplication"
          >⏳ 等待确认，点击取消</el-button>
          <el-button
            v-else
            type="success"
            size="large"
            disabled
          >✅ 已加入拼车</el-button>
          <el-button
            v-if="myApp && myApp.status === 'approved'"
            type="danger"
            size="large"
            plain
            @click="quitCarpool"
          >退出拼车</el-button>
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
                {{ a.status === 'pending' ? '待确认' : (a.status === 'approved' ? '已加入' : (a.status === 'rejected' ? '已拒绝' : (a.status === 'removed' ? '已移除' : '已退出'))) }}
              </el-tag>
            </div>
            <div class="app-meta">📱 {{ a.phone }} · 👥 {{ a.people_count }} 人 · {{ a.created_at.slice(0, 16) }}</div>
            <div v-if="a.remark" class="app-remark">备注：{{ a.remark }}</div>
          </div>
          <div v-if="a.status === 'pending'" class="app-ops">
            <el-button size="small" type="success" @click="handleApprove(a)">同意</el-button>
            <el-button size="small" type="danger" plain @click="handleReject(a)">拒绝</el-button>
          </div>
          <div v-else-if="a.status === 'approved'" class="app-ops">
            <el-button size="small" type="danger" plain @click="handleRemoveMember(a)">移除成员</el-button>
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

.map-box {
  margin-bottom: 20px;
}

.map-box-title {
  font-weight: 600;
  color: #303133;
  margin-bottom: 10px;
}

.map-legend {
  display: flex;
  gap: 16px;
  margin-top: 10px;
  font-size: 12px;
  color: #606266;
  flex-wrap: wrap;
}

.legend-item {
  display: inline-flex;
  align-items: center;
  gap: 5px;
}

.legend-dot {
  width: 10px;
  height: 10px;
  border-radius: 50%;
  display: inline-block;
}

.start-dot { background: #67c23a; }
.end-dot { background: #f56c6c; }

.legend-line {
  width: 24px;
  height: 0;
  border-top: 3px solid #ff7d00;
  display: inline-block;
}

.chat-box {
  border: 1px solid #ebeef5;
  border-radius: 10px;
  padding: 14px;
  margin-bottom: 20px;
  background: #fafafa;
}

.chat-box-title {
  font-weight: 600;
  color: #303133;
  margin-bottom: 10px;
}

.chat-list {
  max-height: 260px;
  overflow-y: auto;
  display: flex;
  flex-direction: column;
  gap: 10px;
  padding: 4px 2px;
}

.chat-msg {
  display: flex;
  flex-direction: column;
  max-width: 75%;
}

.chat-msg.mine {
  align-self: flex-end;
  align-items: flex-end;
}

.chat-msg.theirs {
  align-self: flex-start;
  align-items: flex-start;
}

.chat-bubble {
  padding: 8px 12px;
  border-radius: 10px;
  font-size: 14px;
  line-height: 1.5;
  word-break: break-word;
}

.chat-msg.mine .chat-bubble {
  background: #409eff;
  color: #fff;
  border-bottom-right-radius: 2px;
}

.chat-msg.theirs .chat-bubble {
  background: #fff;
  color: #303133;
  border: 1px solid #e4e7ed;
  border-bottom-left-radius: 2px;
}

.chat-time {
  font-size: 11px;
  color: #909399;
  margin-top: 3px;
}

.chat-input-row {
  display: flex;
  gap: 8px;
  margin-top: 10px;
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
