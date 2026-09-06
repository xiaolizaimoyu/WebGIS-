<script setup>
// 我的兑换记录页（归属：前端 C）
import { onMounted, ref, computed } from 'vue'
import { useRouter } from 'vue-router'
import * as mallApi from '@/api/mall'
import { formatTime } from '@/api/const'
import { getMockRedeemRecords, getMockGoods } from '@/utils/mockData'
import { useUserStore } from '@/stores/user'

const router = useRouter()
const store = useUserStore()

const list = ref([])
const loading = ref(false)
const activeStatus = ref('all')

const userPoints = computed(() => store.signStatus?.totalPoints || 0)

const statusMap = {
  pending: { label: '待发货', type: 'warning', icon: '⏳' },
  shipping: { label: '配送中', type: 'primary', icon: '🚚' },
  delivered: { label: '已完成', type: 'success', icon: '✅' },
  cancelled: { label: '已取消', type: 'info', icon: '❌' }
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

function getGoodsImage(goodsId) {
  const goods = getMockGoods()
  const g = goods.find((x) => x.id === goodsId)
  return g?.image || '🎁'
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

    <!-- 兑换记录列表 -->
    <el-card shadow="never" class="list-card">
      <div v-loading="loading" class="records-list">
        <el-empty v-if="!filteredList.length && !loading" description="暂无兑换记录" :image-size="100">
          <template #footer>
            <el-button type="primary" @click="goToMall">去商城看看</el-button>
          </template>
        </el-empty>

        <div v-for="r in filteredList" :key="r.id" class="record-item">
          <div class="record-icon">{{ getGoodsImage(r.goods_id) }}</div>
          <div class="record-info">
            <div class="record-head">
              <h4 class="record-name">{{ r.goods_name }}</h4>
              <el-tag :type="statusMap[r.status]?.type" size="small" effect="dark">
                {{ statusMap[r.status]?.icon }} {{ statusMap[r.status]?.label }}
              </el-tag>
            </div>
            <div class="record-meta">
              <span>数量：x{{ r.quantity }}</span>
              <span>消耗：<strong class="points-cost">{{ r.points * r.quantity }}</strong> 积分</span>
              <span>兑换时间：{{ formatTime(r.redeem_time) }}</span>
            </div>
            <div v-if="r.status === 'shipping'" class="record-tracking">
              🚚 商品已发出，预计2-3天送达，请保持电话畅通
            </div>
            <div v-if="r.status === 'delivered'" class="record-actions">
              <el-button text type="primary" size="small">查看详情</el-button>
              <el-button text type="success" size="small">评价商品</el-button>
            </div>
          </div>
        </div>
      </div>
    </el-card>
  </div>
</template>

<style scoped>
.records-page {
  max-width: 860px;
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

.list-card {
  border-radius: 12px;
}

.records-list {
  min-height: 300px;
}

.record-item {
  display: flex;
  gap: 16px;
  padding: 16px 0;
  border-bottom: 1px solid #f0f2f5;
}

.record-item:last-child {
  border-bottom: none;
}

.record-icon {
  width: 64px;
  height: 64px;
  background: linear-gradient(135deg, #f5f7fa, #e8ecf1);
  border-radius: 10px;
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 32px;
  flex-shrink: 0;
}

.record-info {
  flex: 1;
  min-width: 0;
}

.record-head {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 8px;
}

.record-name {
  font-size: 15px;
  font-weight: 600;
  color: #303133;
  margin: 0;
}

.record-meta {
  display: flex;
  gap: 16px;
  font-size: 12px;
  color: #909399;
  margin-bottom: 8px;
  flex-wrap: wrap;
}

.points-cost {
  color: #f56c6c;
  font-size: 14px;
}

.record-tracking {
  font-size: 12px;
  color: #1d6df0;
  background: #ecf5ff;
  padding: 6px 10px;
  border-radius: 6px;
  display: inline-block;
}

.record-actions {
  display: flex;
  gap: 12px;
  margin-top: 4px;
}
</style>
