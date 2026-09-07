<script setup>
// 商品详情页（归属：前端 C）——商品详情 + 兑换弹窗
import { onMounted, ref, reactive, computed } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { ElMessage } from 'element-plus'
import * as mallApi from '@/api/mall'
import { getMockGoodsDetail } from '@/utils/mockData'
import { useUserStore } from '@/stores/user'
import { useDialogStore } from '@/stores/dialog'

const route = useRoute()
const router = useRouter()
const store = useUserStore()
const dialog = useDialogStore()

const goodsId = Number(route.params.id)
const goods = ref(null)
const quantity = ref(1)

const userPoints = computed(() => store.signStatus?.totalPoints || 0)
const totalPoints = computed(() => ((goods.value?.points ?? goods.value?.points_price) || 0) * quantity.value)
const canAfford = computed(() => userPoints.value >= totalPoints.value)
const hasStock = computed(() => (goods.value?.stock || 0) >= quantity.value)

// 兑换弹窗
const redeemVisible = ref(false)
const redeemForm = reactive({
  name: '',
  phone: '',
  address: '',
  remark: ''
})
const redeeming = ref(false)

async function loadDetail() {
  try {
    goods.value = await mallApi.getGoods(goodsId)
  } catch {
    goods.value = getMockGoodsDetail(goodsId)
  }
}

function openRedeemDialog() {
  if (!store.isLoggedIn) {
    ElMessage.warning('请先登录后再兑换')
    router.push({ path: '/login', query: { redirect: route.fullPath } })
    return
  }
  if (!canAfford.value) {
    ElMessage.warning(`积分不足，还差 ${totalPoints.value - userPoints.value} 积分`)
    return
  }
  if (!hasStock.value) {
    ElMessage.warning('库存不足')
    return
  }
  redeemForm.name = store.userInfo?.nickname || ''
  redeemForm.phone = ''
  redeemForm.address = ''
  redeemForm.remark = ''
  redeemVisible.value = true
}

async function submitRedeem() {
  if (!redeemForm.name.trim()) {
    ElMessage.warning('请填写收货人姓名')
    return
  }
  if (!redeemForm.phone.trim()) {
    ElMessage.warning('请填写联系电话')
    return
  }
  if (!redeemForm.address.trim()) {
    ElMessage.warning('请填写收货地址')
    return
  }
  redeeming.value = true
  try {
    await mallApi.redeemGoods(goodsId, quantity.value)
    // 扣减积分
    if (store.signStatus) {
      store.signStatus.totalPoints -= totalPoints.value
    }
    if (goods.value) goods.value.stock -= quantity.value
    redeemVisible.value = false
    ElMessage.success('兑换成功！')
    // 全局弹窗提示
    dialog.open({
      title: '🎉 兑换成功',
      content: `您已成功兑换「${goods.value.name}」x${quantity.value}，消耗 ${totalPoints.value} 积分。商品将在3个工作日内发放，请保持电话畅通。`,
      type: 'success',
      confirmText: '查看兑换记录',
      showCancel: true,
      cancelText: '继续逛逛',
      onConfirm: () => router.push('/mall/records')
    })
  } catch {
    // mock 模式
    if (store.signStatus) {
      store.signStatus.totalPoints -= totalPoints.value
    }
    if (goods.value) goods.value.stock -= quantity.value
    redeemVisible.value = false
    ElMessage.success('兑换成功（模拟）')
    dialog.open({
      title: '🎉 兑换成功',
      content: `您已成功兑换「${goods.value.name}」x${quantity.value}，消耗 ${totalPoints.value} 积分。`,
      type: 'success',
      confirmText: '查看兑换记录',
      showCancel: true,
      cancelText: '继续逛逛',
      onConfirm: () => router.push('/mall/records')
    })
  } finally {
    redeeming.value = false
  }
}

// 外链图片加载失败（如 Unsplash 被墙/慢）时回退到本地 emoji 占位，避免裂图
function onImgError(e) {
  e.target.src = 'data:image/svg+xml;utf8,' + encodeURIComponent(
    "<svg xmlns='http://www.w3.org/2000/svg' viewBox='0 0 100 100'>" +
    "<rect width='100' height='100' fill='%23f0f2f5'/>" +
    "<text x='50' y='62' font-size='40' text-anchor='middle'>🎁</text></svg>"
  )
  e.target.onerror = null
}

const tagColorMap = {
  '热门': 'danger',
  '新品': 'success',
  '限时特惠': 'warning',
  '限量': 'danger',
  '专业必备': 'primary'
}

onMounted(() => {
  loadDetail()
  if (store.isLoggedIn) store.fetchSignStatus()
})
</script>

<template>
  <div class="goods-detail-page" v-if="goods">
    <el-card shadow="never" class="detail-card">
      <div class="detail-layout">
        <!-- 左侧商品图 -->
        <div class="goods-image-section">
          <div class="goods-image-large">
            <img :src="goods.image || 'https://images.unsplash.com/photo-1521572267360-ee0c2909d518?auto=format&fit=crop&w=900&q=80'" :alt="goods.name" class="goods-detail-cover" @error="onImgError" />
          </div>
          <div v-if="goods.tags && goods.tags.length" class="goods-tags-large">
            <el-tag
              v-for="t in goods.tags"
              :key="t"
              :type="tagColorMap[t] || 'info'"
              effect="dark"
            >
              {{ t }}
            </el-tag>
          </div>
        </div>

        <!-- 右侧商品信息 -->
        <div class="goods-info-section">
          <h1 class="goods-title">{{ goods.name }}</h1>

          <div class="goods-category">
            <el-tag size="small">{{ goods.category }}</el-tag>
            <span class="sold-count">已兑换 {{ goods.sold ?? 0 }} 件</span>
          </div>

          <div class="price-section">
            <div class="price-label">兑换价</div>
            <div class="price-value">
              <span class="price-icon">🪙</span>
              <span class="price-num">{{ goods.points ?? goods.points_price }}</span>
              <span class="price-unit">积分</span>
            </div>
            <div class="my-points">
              我的积分：<span :class="{ 'points-enough': canAfford, 'points-lack': !canAfford }">{{ userPoints }}</span>
              <span v-if="!canAfford" class="points-tip">（还差 {{ totalPoints - userPoints }} 积分）</span>
            </div>
          </div>

          <div class="stock-section">
            <span class="stock-label">库存：</span>
            <span :class="{ 'stock-low': goods.stock < 20 }">{{ goods.stock }} 件</span>
            <span v-if="goods.stock < 20" class="stock-hurry">（库存紧张，欲兑从速！）</span>
          </div>

          <div class="quantity-section">
            <span class="quantity-label">数量：</span>
            <el-input-number
              v-model="quantity"
              :min="1"
              :max="goods.stock"
              size="default"
            />
            <span class="total-points">合计：<strong>{{ totalPoints }}</strong> 积分</span>
          </div>

          <div class="action-section">
            <el-button
              type="primary"
              size="large"
              :disabled="!canAfford || !hasStock"
              @click="openRedeemDialog"
            >
              {{ !canAfford ? '积分不足' : !hasStock ? '库存不足' : '🎁 立即兑换' }}
            </el-button>
            <el-button size="large" @click="router.back()">← 返回</el-button>
          </div>
        </div>
      </div>

      <!-- 商品详情 -->
      <div class="description-section">
        <div class="section-title">📋 商品详情</div>
        <div class="description-content">{{ goods.description }}</div>
      </div>

      <!-- 兑换说明 -->
      <div class="rules-section">
        <div class="section-title">📌 兑换说明</div>
        <ul class="rules-list">
          <li>兑换成功后，积分将立即扣除，不支持退换</li>
          <li>虚拟商品（如学习资料）将在24小时内通过消息发送下载链接</li>
          <li>实物商品将在3-5个工作日内发货，请保持电话畅通</li>
          <li>收货地址请填写详细的宿舍楼号和房间号</li>
          <li>如有问题请联系平台客服</li>
        </ul>
      </div>
    </el-card>

    <!-- 兑换弹窗 -->
    <el-dialog v-model="redeemVisible" title="🎁 确认兑换" width="500px" :close-on-click-modal="false">
      <div class="redeem-summary">
        <div class="summary-item">
          <span class="summary-label">商品：</span>
          <span class="summary-value">{{ goods.name }}</span>
        </div>
        <div class="summary-item">
          <span class="summary-label">数量：</span>
          <span class="summary-value">x{{ quantity }}</span>
        </div>
        <div class="summary-item">
          <span class="summary-label">消耗积分：</span>
          <span class="summary-value points-cost">{{ totalPoints }} 积分</span>
        </div>
      </div>

      <el-divider />

      <el-form label-width="90px">
        <el-form-item label="收货人" required>
          <el-input v-model="redeemForm.name" placeholder="请输入收货人姓名" />
        </el-form-item>
        <el-form-item label="联系电话" required>
          <el-input v-model="redeemForm.phone" placeholder="请输入手机号码" />
        </el-form-item>
        <el-form-item label="收货地址" required>
          <el-input v-model="redeemForm.address" type="textarea" :rows="2" placeholder="请输入详细收货地址（如：XX宿舍楼XXX室）" />
        </el-form-item>
        <el-form-item label="备注">
          <el-input v-model="redeemForm.remark" placeholder="其他备注信息（可选）" />
        </el-form-item>
      </el-form>

      <template #footer>
        <el-button @click="redeemVisible = false">取消</el-button>
        <el-button type="primary" :loading="redeeming" @click="submitRedeem">
          确认兑换（{{ totalPoints }}积分）
        </el-button>
      </template>
    </el-dialog>
  </div>
</template>

<style scoped>
.goods-detail-page {
  max-width: 960px;
  margin: 0 auto;
  padding: 20px;
}

.detail-card {
  border-radius: 12px;
}

.detail-layout {
  display: flex;
  gap: 32px;
  margin-bottom: 24px;
}

.goods-image-section {
  width: 320px;
  flex-shrink: 0;
}

.goods-image-large {
  width: 100%;
  height: 280px;
  background: linear-gradient(135deg, #f5f7fa 0%, #e8ecf1 100%);
  border-radius: 12px;
  display: flex;
  align-items: center;
  justify-content: center;
  margin-bottom: 12px;
}

.image-emoji {
  font-size: 100px;
}

.goods-tags-large {
  display: flex;
  gap: 8px;
  flex-wrap: wrap;
}

.goods-info-section {
  flex: 1;
  min-width: 0;
}

.goods-title {
  font-size: 24px;
  font-weight: 700;
  color: #303133;
  margin: 0 0 12px 0;
}

.goods-category {
  display: flex;
  align-items: center;
  gap: 12px;
  margin-bottom: 16px;
}

.sold-count {
  font-size: 13px;
  color: #909399;
}

.price-section {
  background: linear-gradient(135deg, #fef0f0 0%, #fff 100%);
  border-radius: 10px;
  padding: 16px 20px;
  margin-bottom: 16px;
}

.price-label {
  font-size: 13px;
  color: #909399;
  margin-bottom: 4px;
}

.price-value {
  display: flex;
  align-items: baseline;
  gap: 4px;
  margin-bottom: 8px;
}

.price-icon {
  font-size: 20px;
}

.price-num {
  font-size: 36px;
  font-weight: 800;
  color: #f56c6c;
  line-height: 1;
}

.price-unit {
  font-size: 14px;
  color: #f56c6c;
}

.my-points {
  font-size: 13px;
  color: #606266;
}

.points-enough {
  color: #67c23a;
  font-weight: 600;
}

.points-lack {
  color: #f56c6c;
  font-weight: 600;
}

.points-tip {
  color: #f56c6c;
  margin-left: 4px;
}

.stock-section {
  font-size: 14px;
  color: #606266;
  margin-bottom: 16px;
}

.stock-label {
  color: #909399;
}

.stock-low {
  color: #f56c6c;
  font-weight: 600;
}

.stock-hurry {
  color: #f56c6c;
  font-size: 12px;
  margin-left: 8px;
}

.quantity-section {
  display: flex;
  align-items: center;
  gap: 12px;
  margin-bottom: 20px;
}

.quantity-label {
  font-size: 14px;
  color: #606266;
}

.total-points {
  font-size: 14px;
  color: #606266;
  margin-left: 8px;
}

.total-points strong {
  color: #f56c6c;
  font-size: 18px;
}

.action-section {
  display: flex;
  gap: 12px;
}

.description-section,
.rules-section {
  padding-top: 20px;
  border-top: 1px solid #f0f2f5;
  margin-top: 20px;
}

.section-title {
  font-size: 16px;
  font-weight: 600;
  color: #303133;
  margin-bottom: 12px;
}

.description-content {
  font-size: 14px;
  color: #4b4b4b;
  line-height: 1.9;
  white-space: pre-wrap;
}

.rules-list {
  margin: 0;
  padding-left: 20px;
}

.rules-list li {
  font-size: 13px;
  color: #606266;
  line-height: 2;
}

/* 兑换弹窗 */
.redeem-summary {
  background: #f5f7fa;
  border-radius: 8px;
  padding: 12px 16px;
}

.summary-item {
  display: flex;
  justify-content: space-between;
  padding: 4px 0;
  font-size: 14px;
}

.summary-label {
  color: #909399;
}

.summary-value {
  color: #303133;
  font-weight: 500;
}

.points-cost {
  color: #f56c6c !important;
  font-weight: 700 !important;
  font-size: 16px !important;
}
</style>
