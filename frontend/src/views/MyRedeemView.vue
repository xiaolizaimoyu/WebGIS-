<script setup>
// 我的兑换记录页（归属：后端 D 改造）
// 改为表格形式展示发货状态 + 状态进度 + 取消待发货订单
import { onMounted, ref, computed } from 'vue'
import { useRouter } from 'vue-router'
import { ElMessage, ElMessageBox } from 'element-plus'
import * as mallApi from '@/api/mall'
import { formatTime } from '@/api/const'
import { getMockRedeemRecords, getMockGoods } from '@/utils/mockData'
import { useUserStore } from '@/stores/user'

const router = useRouter()
const store = useUserStore()

const list = ref([])
const loading = ref(false)
const cancelling = ref(false)
const activeStatus = ref('all')

const userPoints = computed(() => store.signStatus?.totalPoints || 0)

// 状态：pending 待发货 -> shipping 配送中 -> delivered 已送达；cancelled 已取消
const statusMap = {
  pending: { label: '待发货', type: 'warning', icon: '⏳' },
  shipping: { label: '配送中', type: 'primary', icon: '🚚' },
  delivered: { label: '已送达', type: 'success', icon: '📦' },
  cancelled: { label: '已取消', type: 'info', icon: '❌' }
}

// 表格进度列：按状态高亮到第几步
const stepIndex = (status) => {
  return { pending: 0, shipping: 1, delivered: 2, cancelled: -1 }[status] ?? 0
}

const filteredList = computed(() => {
  if (activeStatus.value === 'all') return list.value
  return list.value.filter((r) => r.status === activeStatus.value)
})

async function load() {
  loading.value = true
  try {
    const data = await mallApi.myRedeemRecords({ page: 1, size: 50 })
    list.value = data.items || data || []
  } catch {
    list.value = getMockRedeemRecords()
  } finally {
    loading.value = false
  }
}

function getGoodsImage(r) {
  if (r.goods_image) return r.goods_image
  const goods = getMockGoods()
  const g = goods.find((x) => x.id === r.goods_id)
  return g?.image || 'https://images.unsplash.com/photo-1521572267360-ee0c2909d518?auto=format&fit=crop&w=900&q=80'
}

function onImgError(e) {
  e.target.src = 'data:image/svg+xml;utf8,' + encodeURIComponent(
    "<svg xmlns='http://www.w3.org/2000/svg' viewBox='0 0 100 100'>" +
    "<rect width='100' height='100' fill='%23f0f2f5'/>" +
    "<text x='50' y='62' font-size='40' text-anchor='middle'>🎁</text></svg>"
  )
  e.target.onerror = null
}

async function onCancel(row) {
  try {
    await ElMessageBox.confirm(
      `确定取消订单「${row.goods_name}」？取消后积分将原路退回。`,
      '取消订单确认',
      { type: 'warning', confirmButtonText: '取消订单', cancelButtonText: '再想想' }
    )
  } catch { return }
  cancelling.value = true
  try {
    await mallApi.cancelOrder(row.id)
    ElMessage.success('订单已取消，积分已退回')
    load()
    if (store.isLoggedIn) store.fetchSignStatus()
  } catch {
    // request.js 统一提示
  } finally {
    cancelling.value = false
  }
}

function goToMall() {
  router.push('/mall')
}

onMounted(() => {
  load()
  if (store.isLoggedIn) store.fetchSignStatus()
})
</script>

<template>
  <div class="records-page">
    <!-- 顶部积分卡片 -->
    <el-card shadow="never" class="points-card">
      <div class="points-content">
        <div class="points-left">
          <div class="points-label">当前积分</div>
          <div class="points-value">{{ userPoints }}</div>
        </div>
        <div class="points-right">
          <el-button type="primary" round @click="goToMall">
            🛍️ 去商城兑换
          </el-button>
        </div>
      </div>
    </el-card>

    <!-- 筛选标签 -->
    <el-card shadow="never" class="filter-card">
      <div class="filter-tabs">
        <div
          v-for="(s, key) in { all: { label: '全部' }, ...statusMap }"
          :key="key"
          class="filter-tab"
          :class="{ active: activeStatus === key }"
          @click="activeStatus = key"
        >
          {{ s.label }}
          <span v-if="key !== 'all'" class="tab-count">
            {{ list.filter(r => r.status === key).length }}
          </span>
        </div>
      </div>
    </el-card>

    <!-- 兑换记录表格（列表形式展示发货状态） -->
    <el-card shadow="never" class="table-card">
      <el-table
        v-loading="loading"
        :data="filteredList"
        stripe
        style="width: 100%"
        empty-text="暂无兑换记录"
      >
        <el-table-column label="商品" min-width="220">
          <template #default="{ row }">
            <div class="goods-cell">
              <img
                :src="getGoodsImage(row)"
                :alt="row.goods_name"
                class="goods-thumb"
                @error="onImgError"
              />
              <span class="goods-name">{{ row.goods_name }}</span>
            </div>
          </template>
        </el-table-column>
        <el-table-column label="数量" width="80" align="center">
          <template #default="{ row }">x{{ row.quantity ?? 1 }}</template>
        </el-table-column>
        <el-table-column label="消耗积分" width="110" align="center">
          <template #default="{ row }">
            <span class="points-cost">{{ (row.points_cost ?? row.points ?? 0) * (row.quantity ?? 1) }}</span>
          </template>
        </el-table-column>
        <el-table-column label="兑换时间" width="170">
          <template #default="{ row }">{{ formatTime(row.redeem_time ?? row.created_at) }}</template>
        </el-table-column>
        <el-table-column label="发货状态" min-width="220">
          <template #default="{ row }">
            <!-- 已取消：仅展示标签 -->
            <el-tag v-if="row.status === 'cancelled'" type="info" size="small" effect="dark">
              ❌ 已取消
            </el-tag>
            <!-- 进行中：三步进度条 -->
            <el-steps v-else :active="stepIndex(row.status)" finish-status="success" process-status="finish" class="status-steps">
              <el-step title="待发货" />
              <el-step title="配送中" />
              <el-step title="已送达" />
            </el-steps>
          </template>
        </el-table-column>
        <el-table-column label="操作" width="120" fixed="right">
          <template #default="{ row }">
            <el-button
              v-if="row.status === 'pending'"
              type="danger"
              size="small"
              plain
              :loading="cancelling"
              @click="onCancel(row)"
            >
              取消订单
            </el-button>
            <span v-else-if="row.status === 'shipping'" class="shipping-tip">🚚 运输中</span>
            <span v-else-if="row.status === 'delivered'" class="delivered-tip">✅ 已完成</span>
            <span v-else class="muted">—</span>
          </template>
        </el-table-column>
      </el-table>

      <div v-if="!filteredList.length && !loading" class="empty-action">
        <el-button type="primary" @click="goToMall">去商城看看</el-button>
      </div>
    </el-card>
  </div>
</template>

<style scoped>
.records-page {
  max-width: 960px;
  margin: 0 auto;
  padding: 20px;
}

.points-card {
  border-radius: 12px;
  margin-bottom: 16px;
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%) !important;
  border: none !important;
}

.points-card :deep(.el-card__body) {
  padding: 20px 24px;
}

.points-content {
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.points-left {
  color: #fff;
}

.points-label {
  font-size: 13px;
  opacity: 0.9;
  margin-bottom: 4px;
}

.points-value {
  font-size: 36px;
  font-weight: 800;
  line-height: 1;
}

.filter-card {
  border-radius: 12px;
  margin-bottom: 16px;
}

.filter-card :deep(.el-card__body) {
  padding: 12px 16px;
}

.filter-tabs {
  display: flex;
  gap: 8px;
  flex-wrap: wrap;
}

.filter-tab {
  padding: 6px 16px;
  border-radius: 16px;
  font-size: 13px;
  color: #606266;
  cursor: pointer;
  transition: all 0.2s;
  background: #f5f7fa;
}

.filter-tab:hover {
  background: #ecf5ff;
  color: #1d6df0;
}

.filter-tab.active {
  background: linear-gradient(135deg, #1d6df0, #4facfe);
  color: #fff;
  font-weight: 500;
}

.tab-count {
  margin-left: 4px;
  font-size: 11px;
  opacity: 0.8;
}

.table-card {
  border-radius: 12px;
}

.goods-cell {
  display: flex;
  align-items: center;
  gap: 10px;
}

.goods-thumb {
  width: 44px;
  height: 44px;
  border-radius: 8px;
  object-fit: cover;
  background: #f5f7fa;
  flex-shrink: 0;
}

.goods-name {
  font-size: 14px;
  font-weight: 600;
  color: #303133;
}

.points-cost {
  color: #f56c6c;
  font-weight: 600;
}

/* 三步进度条压缩高度，适配表格行 */
.status-steps {
  margin-top: 4px;
}
.status-steps :deep(.el-step__title) {
  font-size: 12px;
}
.status-steps :deep(.el-step__icon) {
  width: 22px;
  height: 22px;
  font-size: 12px;
}
.status-steps :deep(.el-step__line) {
  top: 11px;
}

.shipping-tip {
  color: #1d6df0;
  font-size: 13px;
}

.delivered-tip {
  color: #67c23a;
  font-size: 13px;
}

.muted {
  color: #c0c4cc;
}

.empty-action {
  text-align: center;
  padding: 30px 0;
}
</style>
