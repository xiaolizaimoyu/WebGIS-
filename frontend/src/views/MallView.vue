<script setup>
// 积分商城列表页（归属：前端 C）——商品网格展示 + 分类筛选 + 积分余额
import { onMounted, ref, computed } from 'vue'
import { useRouter } from 'vue-router'
import * as mallApi from '@/api/mall'
import { getMockGoods, getMockCategories } from '@/utils/mockData'
import { useUserStore } from '@/stores/user'
import MapComponent from '@/components/MapComponent.vue'
import WeatherWidget from '@/components/WeatherWidget.vue'

const router = useRouter()
const store = useUserStore()
const mapRef = ref(null)

const categories = ref(['全部'])
const activeCategory = ref('全部')
const keyword = ref('')
const list = ref([])
const total = ref(0)
const page = ref(1)
const size = ref(12)
const loading = ref(false)
let requestId = 0

const userPoints = computed(() => store.signStatus?.totalPoints || 0)

const tagColorMap = {
  '热门': 'danger',
  '新品': 'success',
  '限时特惠': 'warning',
  '限量': 'danger',
  '专业必备': 'primary'
}

async function load() {
  const currentRequestId = ++requestId
  loading.value = true
  try {
    const data = await mallApi.listGoods({
      category: activeCategory.value === '全部' ? undefined : activeCategory.value,
      keyword: keyword.value || undefined,
      page: page.value,
      size: size.value
    })
    if (currentRequestId !== requestId) return
    list.value = data.items || data || []
    total.value = data.total ?? list.value.length
  } catch {
    if (currentRequestId !== requestId) return
    let mock = getMockGoods()
    if (activeCategory.value !== '全部') mock = mock.filter((g) => g.category === activeCategory.value)
    if (keyword.value) mock = mock.filter((g) => g.name.includes(keyword.value))
    list.value = mock
    total.value = mock.length
  } finally {
    loading.value = false
  }
}

async function loadCategories() {
  try {
    const data = await mallApi.listCategories()
    categories.value = ['全部', ...(data || [])]
  } catch {
    categories.value = getMockCategories()
  }
}

function onCategoryChange(c) {
  activeCategory.value = c
  page.value = 1
  load()
}

function onSearch() {
  page.value = 1
  load()
}

function resetFilters() {
  keyword.value = ''
  activeCategory.value = '全部'
  page.value = 1
  load()
}

function toDetail(id) {
  router.push(`/mall/goods/${id}`)
}

function goToMyRecords() {
  router.push('/mall/records')
}

const mapCenter = ref([116.397428, 39.90923])
const mapMarkers = computed(() => [])

function resolveGoodsImage(image) {
  if (!image) {
    return 'https://images.unsplash.com/photo-1521572267360-ee0c2909d518?auto=format&fit=crop&w=900&q=80'
  }
  return image
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

onMounted(() => {
  loadCategories()
  load()
  if (store.isLoggedIn) store.fetchSignStatus()
})
</script>

<template>
  <div class="page-layout">
    <div class="left-panel">
      <!-- 顶部积分横幅 -->
      <el-card shadow="never" class="points-banner">
        <div class="banner-content">
          <div class="points-info">
            <div class="points-label">我的积分</div>
            <div class="points-value">{{ userPoints }}</div>
            <div class="points-tip">签到、发帖、回答问题均可获得积分</div>
          </div>
          <div class="banner-actions">
            <el-button type="primary" round @click="router.push('/profile')">
              📅 去签到赚积分
            </el-button>
            <el-button round @click="goToMyRecords">
              📦 我的兑换
            </el-button>
          </div>
        </div>
        <div class="banner-decoration">🎁</div>
      </el-card>

      <!-- 筛选栏 -->
      <el-card shadow="never" class="filter-card">
        <div class="filter-row">
          <el-input
            v-model="keyword"
            placeholder="搜索商品..."
            clearable
            style="width: 240px"
            @keyup.enter="onSearch"
            @clear="onSearch"
          >
            <template #prefix>🔍</template>
          </el-input>
          <el-button v-if="keyword || activeCategory !== '全部'" text type="primary" class="reset-btn" @click="resetFilters">
            清空筛选
          </el-button>
        </div>
        <div class="category-row">
          <el-tag
            v-for="c in categories"
            :key="c"
            :type="activeCategory === c ? 'primary' : 'info'"
            :effect="activeCategory === c ? 'dark' : 'plain'"
            class="category-item"
            @click="onCategoryChange(c)"
          >
            {{ c }}
          </el-tag>
        </div>
      </el-card>

      <!-- 商品网格 -->
      <div v-loading="loading" class="goods-grid">
        <div
          v-for="g in list"
          :key="g.id"
          class="goods-card"
          :aria-label="`查看商品：${g.name}`"
          role="button"
          @click="toDetail(g.id)"
        >
          <div class="goods-image">
            <img :src="resolveGoodsImage(g.image)" :alt="g.name || '积分商品'" loading="lazy" decoding="async" class="goods-cover" @error="onImgError" />
            <div v-if="g.tags && g.tags.length" class="goods-tags">
              <el-tag
                v-for="t in g.tags.slice(0, 2)"
                :key="t"
                :type="tagColorMap[t] || 'info'"
                size="small"
                effect="dark"
              >
                {{ t }}
              </el-tag>
            </div>
            <div v-if="g.stock < 20" class="stock-warning">仅剩 {{ g.stock }} 件</div>
          </div>
          <div class="goods-info">
            <h3 class="goods-name">{{ g.name }}</h3>
            <p class="goods-desc">{{ g.description }}</p>
            <div class="goods-footer">
              <div class="goods-price">
                <span class="price-icon">🪙</span>
                <span class="price-value">{{ g.points ?? g.points_price }}</span>
                <span class="price-unit">积分</span>
              </div>
              <div class="goods-sold">已兑 {{ g.sold ?? 0 }}</div>
            </div>
          </div>
        </div>

        <el-empty v-if="!loading && !list.length" description="暂无商品" :image-size="100" aria-live="polite" />
      </div>

      <div v-if="total > size" class="pager">
        <el-pagination
          background
          layout="prev, pager, next"
          :total="total"
          :page-size="size"
          :current-page="page"
          @current-change="(p) => ((page = p), load())"
        />
      </div>
    </div>

    <!-- 右侧 -->
    <div class="right-panel">
      <WeatherWidget city="北京" :use-mock="true" />
      <div class="map-wrapper">
        <div class="map-header"><span class="map-title">🗺️ 校园地图</span></div>
        <MapComponent ref="mapRef" :center="mapCenter" :zoom="14" :markers="mapMarkers" height="300px" />
      </div>
      <el-card shadow="never" class="tip-card">
        <div class="tip-title">💡 积分获取攻略</div>
        <p>· 每日签到 +10 积分</p>
        <p>· 连续签到7天额外 +20</p>
        <p>· 发布内容 +5 积分</p>
        <p>· 回答被采纳 +20 积分</p>
        <p>· 上传资料 +15 积分</p>
      </el-card>
    </div>
  </div>
</template>

<style scoped>
.page-layout {
  display: flex;
  gap: 20px;
  max-width: 1400px;
  margin: 0 auto;
  padding: 20px;
  min-height: calc(100vh - 60px);
}

.left-panel {
  flex: 1;
  min-width: 0;
}

.right-panel {
  width: 420px;
  flex-shrink: 0;
  display: flex;
  flex-direction: column;
  gap: 16px;
  position: sticky;
  top: 80px;
  align-self: flex-start;
}

/* 积分横幅 */
.points-banner {
  border-radius: 16px !important;
  margin-bottom: 16px;
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%) !important;
  border: none !important;
  overflow: hidden;
  position: relative;
}

.points-banner :deep(.el-card__body) {
  padding: 24px;
}

.banner-content {
  display: flex;
  justify-content: space-between;
  align-items: center;
  position: relative;
  z-index: 1;
}

.points-info {
  color: #fff;
}

.points-label {
  font-size: 14px;
  opacity: 0.9;
  margin-bottom: 4px;
}

.points-value {
  font-size: 42px;
  font-weight: 800;
  line-height: 1;
  margin-bottom: 6px;
  text-shadow: 0 2px 8px rgba(0,0,0,0.2);
}

.points-tip {
  font-size: 12px;
  opacity: 0.8;
}

.banner-actions {
  display: flex;
  flex-direction: column;
  gap: 10px;
}

.banner-decoration {
  position: absolute;
  right: 200px;
  top: 50%;
  transform: translateY(-50%);
  font-size: 120px;
  opacity: 0.15;
}

/* 筛选 */
.filter-card {
  border-radius: 12px;
  margin-bottom: 16px;
}

.filter-row {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 12px;
  margin-bottom: 12px;
  flex-wrap: wrap;
}

.reset-btn {
  margin-left: auto;
}

.category-row {
  display: flex;
  flex-wrap: wrap;
  gap: 8px;
}

.category-item {
  cursor: pointer;
  transition: all 0.2s;
}

.category-item:hover {
  transform: translateY(-1px);
}

/* 商品网格 */
.goods-grid {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(220px, 1fr));
  gap: 16px;
  min-height: 200px;
}

.goods-card {
  background: #fff;
  border-radius: 12px;
  overflow: hidden;
  cursor: pointer;
  transition: all 0.25s ease;
  border: 1px solid #ebeef5;
}

.goods-card:hover {
  transform: translateY(-4px);
  box-shadow: 0 12px 28px rgba(102, 126, 234, 0.18);
  border-color: #667eea;
}

.goods-image {
  height: 140px;
  background: linear-gradient(135deg, #f5f7fa 0%, #e8ecf1 100%);
  display: flex;
  align-items: center;
  justify-content: center;
  position: relative;
}

.goods-cover {
  width: 100%;
  height: 100%;
  object-fit: cover;
  display: block;
}

.goods-emoji {
  font-size: 56px;
  transition: transform 0.3s;
}

.goods-card:hover .goods-emoji {
  transform: scale(1.15);
}

.goods-tags {
  position: absolute;
  top: 8px;
  left: 8px;
  display: flex;
  flex-direction: column;
  gap: 4px;
}

.stock-warning {
  position: absolute;
  bottom: 8px;
  right: 8px;
  background: rgba(245, 108, 108, 0.9);
  color: #fff;
  font-size: 11px;
  padding: 2px 8px;
  border-radius: 10px;
}

.goods-info {
  padding: 12px;
}

.goods-name {
  font-size: 15px;
  font-weight: 600;
  color: #303133;
  margin: 0 0 6px 0;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.goods-desc {
  font-size: 12px;
  color: #909399;
  line-height: 1.5;
  margin: 0 0 10px 0;
  display: -webkit-box;
  -webkit-line-clamp: 2;
  -webkit-box-orient: vertical;
  overflow: hidden;
  min-height: 36px;
}

.goods-footer {
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.goods-price {
  display: flex;
  align-items: baseline;
  gap: 2px;
}

.price-icon {
  font-size: 14px;
}

.price-value {
  font-size: 20px;
  font-weight: 800;
  color: #f56c6c;
}

.price-unit {
  font-size: 11px;
  color: #f56c6c;
}

.goods-sold {
  font-size: 11px;
  color: #a8abb2;
}

.pager {
  display: flex;
  justify-content: center;
  padding: 20px 0;
}

.map-wrapper {
  background: #fff;
  border-radius: 12px;
  padding: 12px;
  box-shadow: 0 2px 12px rgba(0,0,0,0.06);
}

.map-header {
  margin-bottom: 8px;
}

.map-title {
  font-size: 15px;
  font-weight: 600;
  color: #303133;
}

.tip-card {
  border-radius: 12px;
}

.tip-title {
  font-weight: 600;
  margin-bottom: 8px;
  color: #303133;
}

.tip-card p {
  font-size: 13px;
  color: #606266;
  line-height: 1.8;
  margin: 0;
}

@media (max-width: 992px) {
  .page-layout {
    flex-direction: column;
  }
  .right-panel {
    width: 100%;
    position: static;
  }
  .goods-grid {
    grid-template-columns: repeat(auto-fill, minmax(160px, 1fr));
  }
}

@media (max-width: 560px) {
  .page-layout {
    padding: 12px;
  }
  .banner-content {
    align-items: flex-start;
  }
  .banner-decoration {
    display: none;
  }
}
</style>
