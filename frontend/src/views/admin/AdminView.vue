<script setup>
// 管理后台（归属：后端 D 实现 + 组长扩展权限）
// 独立全屏布局：统计卡片 + 帖子审核/置顶/加精 + 用户管理(封禁) + 订单发货
import { ref, reactive, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import { ElMessage, ElMessageBox } from 'element-plus'
import { useUserStore } from '@/stores/user'
import * as adminApi from '@/api/admin'

const router = useRouter()
const store = useUserStore()

const stats = ref({})
const activeTab = ref('contents')

// 帖子审核
const contentQuery = reactive({ page: 1, page_size: 10, type: '', audit_status: '' })
const contentList = ref({ total: 0, list: [] })

// 用户管理
const userQuery = reactive({ page: 1, page_size: 10, keyword: '' })
const userList = ref({ total: 0, list: [] })

// 订单发货管理
const orderQuery = reactive({ page: 1, page_size: 10, status: '' })
const orderList = ref({ total: 0, list: [] })

const ORDER_STATUS_LABEL = {
  pending: { label: '待发货', type: 'warning' },
  shipping: { label: '配送中', type: 'primary' },
  delivered: { label: '已送达', type: 'success' },
  cancelled: { label: '已取消', type: 'info' }
}

const TYPE_LABEL = {
  meeting: '校园会议', news: '校园动态', food: '校园美食', lost: '失物招领'
}

const AUDIT_LABEL = {
  pending: { label: '待审核', type: 'warning' },
  approved: { label: '已通过', type: 'success' },
  rejected: { label: '已驳回', type: 'danger' }
}

async function loadStats() {
  try {
    const data = await adminApi.getStats()
    stats.value = data
  } catch {}
}

async function loadContents() {
  try {
    const params = { page: contentQuery.page, page_size: contentQuery.page_size }
    if (contentQuery.type) params.type = contentQuery.type
    if (contentQuery.audit_status) params.audit_status = contentQuery.audit_status
    const data = await adminApi.listContents(params)
    contentList.value = data
  } catch {}
}

async function loadUsers() {
  try {
    const params = { page: userQuery.page, page_size: userQuery.page_size }
    if (userQuery.keyword) params.keyword = userQuery.keyword
    const data = await adminApi.listUsers(params)
    userList.value = data
  } catch {}
}

async function loadOrders() {
  try {
    const params = { page: orderQuery.page, page_size: orderQuery.page_size }
    if (orderQuery.status) params.status = orderQuery.status
    const data = await adminApi.listOrders(params)
    orderList.value = data
  } catch {}
}

// 管理员更新订单状态：pending->shipping->delivered，或 cancelled
async function onUpdateOrderStatus(row, status) {
  const label = ORDER_STATUS_LABEL[status]?.label
  try {
    await ElMessageBox.confirm(
      `确定将订单 #${row.id}「${row.goods_name}」状态改为「${label}」？`,
      '发货状态更新',
      { type: 'warning', confirmButtonText: '确认更新', cancelButtonText: '取消' }
    )
  } catch { return }
  try {
    await adminApi.updateOrderStatus(row.id, status)
    ElMessage.success('状态已更新')
    loadOrders()
  } catch {}
}

// 审核通过 / 驳回
async function onAuditContent(row, status) {
  const label = status === 'approved' ? '通过' : '驳回'
  try {
    await ElMessageBox.confirm(`确定${label}帖子「${row.title}」？`, '帖子审核', {
      type: 'warning', confirmButtonText: `确认${label}`, cancelButtonText: '取消'
    })
  } catch { return }
  try {
    await adminApi.auditContent(row.id, status)
    ElMessage.success(`已${label}`)
    loadContents()
  } catch {}
}

// 置顶 / 取消置顶
async function onToggleTop(row) {
  const next = !row.is_top
  try {
    await adminApi.toggleTop(row.id, next)
    ElMessage.success(next ? '已置顶' : '已取消置顶')
    loadContents()
  } catch {}
}

// 加精 / 取消加精
async function onToggleEssence(row) {
  const next = !row.is_essence
  try {
    await adminApi.toggleEssence(row.id, next)
    ElMessage.success(next ? '已加精' : '已取消加精')
    loadContents()
  } catch {}
}

async function onDeleteContent(row) {
  try {
    await ElMessageBox.confirm(`确定删除帖子「${row.title}」？该帖下所有评论将一并删除。`, '删帖确认', {
      type: 'warning', confirmButtonText: '删除', cancelButtonText: '取消'
    })
  } catch { return }
  try {
    await adminApi.deleteContent(row.id)
    ElMessage.success('已删除')
    loadStats()
    loadContents()
  } catch {}
}

// 封禁 / 解封
async function onBanUser(row) {
  const next = !row.is_banned
  try {
    await ElMessageBox.confirm(
      `确定${next ? '封禁' : '解封'}用户「${row.username}」？${next ? '封禁后该账号无法登录，已登录会话立即失效。' : ''}`,
      next ? '封禁确认' : '解封确认',
      { type: 'warning', confirmButtonText: next ? '封禁' : '解封', cancelButtonText: '取消' }
    )
  } catch { return }
  try {
    await adminApi.banUser(row.id, next)
    ElMessage.success(next ? '已封禁' : '已解封')
    loadUsers()
  } catch {}
}

async function onDeleteUser(row) {
  if (row.is_admin) {
    ElMessage.warning('管理员账号不可删除')
    return
  }
  try {
    await ElMessageBox.confirm(`确定删除用户「${row.username}」？该用户发布的内容/评论会阻止删除。`, '删用户确认', {
      type: 'warning', confirmButtonText: '删除', cancelButtonText: '取消'
    })
  } catch { return }
  try {
    await adminApi.deleteUser(row.id)
    ElMessage.success('已删除')
    loadStats()
    loadUsers()
  } catch {}
}

function onLogout() {
  store.logout()
  ElMessage.success('已退出')
  router.push('/admin/login')
}

onMounted(() => {
  loadStats()
  loadContents()
  loadUsers()
  loadOrders()
})
</script>

<template>
  <div class="admin-page">
    <header class="admin-header">
      <div class="header-inner">
        <span class="brand">🛡️ 管理后台</span>
        <span class="brand-sub">校园活动交流平台 · 运营中心</span>
        <div class="spacer" />
        <span class="admin-name">{{ store.userInfo?.nickname }}</span>
        <el-button size="small" type="primary" plain round @click="router.push('/admin/locations')">📍 地点坐标管理</el-button>
        <el-button size="small" round @click="onLogout">退出</el-button>
      </div>
    </header>

    <main class="admin-main">
      <!-- 统计卡片 -->
      <div class="stat-cards">
        <div class="stat-card c1"><div class="num">{{ stats.total_users ?? '-' }}</div><div class="label">用户总数</div></div>
        <div class="stat-card c2"><div class="num">{{ stats.total_contents ?? '-' }}</div><div class="label">帖子总数</div></div>
        <div class="stat-card c3"><div class="num">{{ stats.total_comments ?? '-' }}</div><div class="label">评论总数</div></div>
        <div class="stat-card c4"><div class="num">{{ stats.today_new_users ?? '-' }}</div><div class="label">今日新增用户</div></div>
        <div class="stat-card c5"><div class="num">{{ stats.today_new_contents ?? '-' }}</div><div class="label">今日新增帖子</div></div>
      </div>

      <el-tabs v-model="activeTab" class="admin-tabs">
        <!-- 帖子审核 -->
        <el-tab-pane label="帖子审核" name="contents">
          <div class="filter-row">
            <el-select v-model="contentQuery.audit_status" placeholder="全部状态" clearable style="width:140px" @change="contentQuery.page=1; loadContents()">
              <el-option label="待审核" value="pending" />
              <el-option label="已通过" value="approved" />
              <el-option label="已驳回" value="rejected" />
            </el-select>
            <el-select v-model="contentQuery.type" placeholder="全部分类" clearable style="width:140px" @change="contentQuery.page=1; loadContents()">
              <el-option v-for="(label, key) in TYPE_LABEL" :key="key" :label="label" :value="key" />
            </el-select>
          </div>
          <el-table :data="contentList.list" border stripe>
            <el-table-column prop="title" label="标题" min-width="180" show-overflow-tooltip>
              <template #default="{ row }">
                <span class="title-cell">
                  <el-tag v-if="row.is_top" type="danger" size="small" effect="dark" class="mini-tag">置顶</el-tag>
                  <el-tag v-if="row.is_essence" type="warning" size="small" effect="dark" class="mini-tag">精华</el-tag>
                  {{ row.title }}
                </span>
              </template>
            </el-table-column>
            <el-table-column prop="author_name" label="作者" width="100" />
            <el-table-column label="分类" width="95">
              <template #default="{ row }">{{ TYPE_LABEL[row.type] || row.type }}</template>
            </el-table-column>
            <el-table-column label="审核" width="90">
              <template #default="{ row }">
                <el-tag :type="AUDIT_LABEL[row.audit_status]?.type" size="small">
                  {{ AUDIT_LABEL[row.audit_status]?.label || row.audit_status }}
                </el-tag>
              </template>
            </el-table-column>
            <el-table-column prop="created_at" label="发布时间" width="150">
              <template #default="{ row }">{{ row.created_at?.slice(0, 16).replace('T', ' ') }}</template>
            </el-table-column>
            <el-table-column label="操作" width="360" fixed="right">
              <template #default="{ row }">
                <template v-if="row.audit_status === 'pending'">
                  <el-button type="success" size="small" @click="onAuditContent(row, 'approved')">通过</el-button>
                  <el-button type="warning" size="small" plain @click="onAuditContent(row, 'rejected')">驳回</el-button>
                </template>
                <el-button v-if="row.audit_status === 'rejected'" type="success" size="small" @click="onAuditContent(row, 'approved')">通过</el-button>
                <el-button :type="row.is_top ? 'danger' : 'default'" size="small" plain @click="onToggleTop(row)">
                  {{ row.is_top ? '取消置顶' : '置顶' }}
                </el-button>
                <el-button :type="row.is_essence ? 'warning' : 'default'" size="small" plain @click="onToggleEssence(row)">
                  {{ row.is_essence ? '取消加精' : '加精' }}
                </el-button>
                <el-button type="danger" size="small" @click="onDeleteContent(row)">删除</el-button>
              </template>
            </el-table-column>
          </el-table>
          <el-pagination
            class="pager"
            v-model:current-page="contentQuery.page"
            :page-size="contentQuery.page_size"
            :total="contentList.total"
            layout="prev, pager, next, total"
            @current-change="loadContents"
          />
        </el-tab-pane>

        <!-- 用户管理 -->
        <el-tab-pane label="用户管理" name="users">
          <div class="filter-row">
            <el-input v-model="userQuery.keyword" placeholder="搜索用户名/昵称" clearable style="width:240px" @keyup.enter="userQuery.page=1; loadUsers()" @clear="userQuery.page=1; loadUsers()" />
            <el-button type="primary" plain @click="userQuery.page=1; loadUsers()">搜索</el-button>
          </div>
          <el-table :data="userList.list" border stripe>
            <el-table-column prop="username" label="账号" width="130" />
            <el-table-column prop="nickname" label="昵称" width="130" />
            <el-table-column label="身份" width="80">
              <template #default="{ row }">
                <el-tag v-if="row.is_admin" type="danger" size="small">管理员</el-tag>
                <el-tag v-else type="info" size="small">用户</el-tag>
              </template>
            </el-table-column>
            <el-table-column label="状态" width="80">
              <template #default="{ row }">
                <el-tag v-if="row.is_banned" type="danger" size="small" effect="dark">已封禁</el-tag>
                <el-tag v-else type="success" size="small" effect="plain">正常</el-tag>
              </template>
            </el-table-column>
            <el-table-column prop="content_count" label="发帖数" width="80" />
            <el-table-column prop="comment_count" label="评论数" width="80" />
            <el-table-column prop="created_at" label="注册时间" width="150">
              <template #default="{ row }">{{ row.created_at?.slice(0, 16).replace('T', ' ') }}</template>
            </el-table-column>
            <el-table-column label="操作" width="200" fixed="right">
              <template #default="{ row }">
                <el-button :type="row.is_banned ? 'success' : 'danger'" size="small" plain :disabled="row.is_admin" @click="onBanUser(row)">
                  {{ row.is_banned ? '解封' : '封禁' }}
                </el-button>
                <el-button type="danger" size="small" :disabled="row.is_admin" @click="onDeleteUser(row)">删除</el-button>
              </template>
            </el-table-column>
          </el-table>
          <el-pagination
            class="pager"
            v-model:current-page="userQuery.page"
            :page-size="userQuery.page_size"
            :total="userList.total"
            layout="prev, pager, next, total"
            @current-change="loadUsers"
          />
        </el-tab-pane>

        <!-- 订单发货管理 -->
        <el-tab-pane label="订单发货" name="orders">
          <div class="filter-row">
            <el-select v-model="orderQuery.status" placeholder="全部状态" clearable style="width:160px" @change="orderQuery.page=1; loadOrders()">
              <el-option v-for="(s, key) in ORDER_STATUS_LABEL" :key="key" :label="s.label" :value="key" />
            </el-select>
          </div>
          <el-table :data="orderList.list" border stripe>
            <el-table-column prop="id" label="订单号" width="80" />
            <el-table-column prop="goods_name" label="商品" min-width="160" show-overflow-tooltip />
            <el-table-column prop="quantity" label="数量" width="70" align="center" />
            <el-table-column prop="points_cost" label="消耗积分" width="100" align="center" />
            <el-table-column label="状态" width="110">
              <template #default="{ row }">
                <el-tag :type="ORDER_STATUS_LABEL[row.status]?.type" size="small" effect="dark">
                  {{ ORDER_STATUS_LABEL[row.status]?.label }}
                </el-tag>
              </template>
            </el-table-column>
            <el-table-column prop="created_at" label="兑换时间" width="170">
              <template #default="{ row }">{{ row.created_at?.slice(0, 16).replace('T', ' ') }}</template>
            </el-table-column>
            <el-table-column label="发货操作" width="240" fixed="right">
              <template #default="{ row }">
                <el-button v-if="row.status === 'pending'" type="primary" size="small" @click="onUpdateOrderStatus(row, 'shipping')">标记发货</el-button>
                <el-button v-if="row.status === 'shipping'" type="success" size="small" @click="onUpdateOrderStatus(row, 'delivered')">确认送达</el-button>
                <el-button v-if="row.status === 'pending' || row.status === 'shipping'" type="danger" size="small" plain @click="onUpdateOrderStatus(row, 'cancelled')">取消订单</el-button>
                <span v-else class="muted">—</span>
              </template>
            </el-table-column>
          </el-table>
          <el-pagination
            class="pager"
            v-model:current-page="orderQuery.page"
            :page-size="orderQuery.page_size"
            :total="orderList.total"
            layout="prev, pager, next, total"
            @current-change="loadOrders"
          />
        </el-tab-pane>
      </el-tabs>
    </main>
  </div>
</template>

<style scoped>
.admin-page {
  min-height: 100vh;
  background: linear-gradient(160deg, #eef2f9 0%, #e8ecf5 45%, #f4f0f8 100%);
}

.admin-header {
  background: linear-gradient(90deg, #1a1f2e 0%, #232a4a 55%, #2d2b55 100%);
  color: #f1f3f5;
  position: sticky;
  top: 0;
  z-index: 100;
  box-shadow: 0 2px 12px rgba(26, 31, 46, 0.35);
  border-bottom: 1px solid rgba(255, 255, 255, 0.08);
}

.header-inner {
  max-width: 1180px;
  margin: 0 auto;
  height: 58px;
  display: flex;
  align-items: center;
  gap: 12px;
  padding: 0 24px;
}

.brand {
  font-size: 18px;
  font-weight: 700;
  background: linear-gradient(90deg, #ffffff, #c9d4ff);
  -webkit-background-clip: text;
  background-clip: text;
  color: transparent;
}

.brand-sub {
  font-size: 12px;
  color: rgba(255, 255, 255, 0.5);
  letter-spacing: 1px;
}

.spacer {
  flex: 1;
}

.admin-name {
  color: #c0c4d0;
  font-size: 14px;
}

.admin-main {
  max-width: 1180px;
  margin: 0 auto;
  padding: 26px 24px 40px;
}

.stat-cards {
  display: grid;
  grid-template-columns: repeat(5, 1fr);
  gap: 16px;
  margin-bottom: 26px;
}

.stat-card {
  border-radius: 14px;
  padding: 20px 16px;
  text-align: center;
  color: #fff;
  box-shadow: 0 6px 18px rgba(60, 80, 140, 0.18);
  transition: transform 0.18s ease, box-shadow 0.18s ease;
}

.stat-card:hover {
  transform: translateY(-3px);
  box-shadow: 0 10px 24px rgba(60, 80, 140, 0.26);
}

.stat-card.c1 { background: linear-gradient(135deg, #4e7cf6, #6a5af9); }
.stat-card.c2 { background: linear-gradient(135deg, #12b8a6, #23a6d5); }
.stat-card.c3 { background: linear-gradient(135deg, #f7a23c, #f2574e); }
.stat-card.c4 { background: linear-gradient(135deg, #8e6bf0, #c35ad1); }
.stat-card.c5 { background: linear-gradient(135deg, #2eb872, #1f9d8a); }

.stat-card .num {
  font-size: 28px;
  font-weight: 800;
  line-height: 1.2;
  text-shadow: 0 1px 4px rgba(0, 0, 0, 0.15);
}

.stat-card .label {
  font-size: 13px;
  opacity: 0.9;
  margin-top: 5px;
  letter-spacing: 0.5px;
}

.admin-tabs {
  background: #fff;
  border-radius: 14px;
  padding: 18px 22px 24px;
  box-shadow: 0 6px 22px rgba(30, 40, 80, 0.08);
}

.filter-row {
  display: flex;
  gap: 10px;
  margin-bottom: 16px;
}

.pager {
  margin-top: 16px;
  justify-content: flex-end;
}

.title-cell {
  display: inline-flex;
  align-items: center;
  gap: 6px;
}

.mini-tag {
  transform: scale(0.92);
}

.muted {
  color: #c0c4cc;
  font-size: 13px;
}
</style>
