<script setup>
// 我的发布管理页（归属：前端 B）
// 两个 Tab：我的发布（查看 / 编辑 / 删除）+ 我的收藏（对接后端 F 的 /api/social）
// TODO(前端B)：批量管理、数据统计展示等扩展点
import { onMounted, ref } from 'vue'
import { useRouter } from 'vue-router'
import { ElMessage, ElMessageBox } from 'element-plus'
import * as postApi from '@/api/post'
import * as socialApi from '@/api/social'
import { getMe } from '@/api/user' // 复用前端A的封装：/user/me 返回 content_count/comment_count
import { formatTime, TYPE_MAP } from '@/api/const'

const router = useRouter()
const activeTab = ref('posts')

// ===== 个人统计（规划书 TODO：数据统计展示）=====
// 我的发布/我的评论来自 /user/me，我的收藏来自 /social/favorites/mine
const statContent = ref(0)
const statComment = ref(0)
const statFav = ref(0)

async function loadStats() {
  try {
    const [me, fav] = await Promise.all([
      getMe().catch(() => null),
      socialApi.myFavorites({ page: 1, size: 1 }).catch(() => null)
    ])
    if (me) {
      statContent.value = me.content_count ?? 0
      statComment.value = me.comment_count ?? 0
    }
    if (fav) statFav.value = fav.total ?? 0
  } catch {
    // 统计加载失败不阻塞页面
  }
}

// ===== 我的发布 =====
const list = ref([])
const total = ref(0)
const page = ref(1)
const size = ref(8)
const loading = ref(false)

async function load() {
  loading.value = true
  try {
    const data = await postApi.mineContents({ page: page.value, size: size.value })
    list.value = data.items
    total.value = data.total
  } finally {
    loading.value = false
  }
}

// ===== 批量管理（规划书 TODO：批量管理）=====
// 后端暂无批量删除接口，逐条调用 DELETE 后统一刷新（已删除的自动跳过）
const managing = ref(false)
const selected = ref([]) // 选中的内容 id 数组

const toggleManaging = () => {
  managing.value = !managing.value
  selected.value = []
}

const isSelected = (id) => selected.value.includes(id)

function toggleSelect(id) {
  const i = selected.value.indexOf(id)
  if (i >= 0) selected.value.splice(i, 1)
  else selected.value.push(id)
}

function selectAll() {
  // 全选/反选本页
  selected.value =
    selected.value.length === list.value.length ? [] : list.value.map((c) => c.id)
}

async function removeSelected() {
  if (!selected.value.length) {
    ElMessage.info('请先勾选要删除的内容')
    return
  }
  const count = selected.value.length
  try {
    await ElMessageBox.confirm(
      `确定批量删除选中的 ${count} 条内容吗？删除后不可恢复，其下评论也会一并删除。`,
      '批量删除确认',
      { type: 'warning', confirmButtonText: '全部删除', cancelButtonText: '取消' }
    )
  } catch {
    return
  }
  const results = await Promise.allSettled(selected.value.map((id) => postApi.deleteContent(id)))
  const okCount = results.filter((r) => r.status === 'fulfilled').length
  ElMessage.success(`已删除 ${okCount} 条`)
  selected.value = []
  await load()
  loadStats()
}

// ===== 我的收藏 =====
// 接口只返回 content_id，需逐条取详情组装（N+1，待后端提供批量/联表接口后优化）
const favList = ref([])
const favTotal = ref(0)
const favPage = ref(1)
const favLoading = ref(false)

async function loadFavorites() {
  favLoading.value = true
  try {
    const data = await socialApi.myFavorites({ page: favPage.value, size: size.value })
    favTotal.value = data.total
    const items = await Promise.all(
      (data.items || []).map(async (f) => {
        try {
          // 内容可能已被作者删除：取详情失败则跳过该条
          const content = await postApi.getContent(f.content_id)
          return { content, favTime: f.created_at }
        } catch {
          return null
        }
      })
    )
    favList.value = items.filter(Boolean)
  } finally {
    favLoading.value = false
  }
}

// 切换 Tab 时按需加载（每类数据只拉一次，翻页再更新）
function onTabChange(tab) {
  if (tab === 'favorites' && !favList.value.length && !favLoading.value) loadFavorites()
}

async function unfav(item) {
  try {
    await ElMessageBox.confirm(`确定取消收藏《${item.content.title}》吗？`, '取消收藏', {
      type: 'warning',
      confirmButtonText: '取消收藏',
      cancelButtonText: '再想想'
    })
  } catch {
    return
  }
  await socialApi.toggleFavorite(item.content.id)
  ElMessage.success('已取消收藏')
  await loadFavorites()
  loadStats() // 取消收藏后同步统计
}

function onFavPageChange(p) {
  favPage.value = p
  loadFavorites()
}

function firstImage(item) {
  return item.images && item.images.length ? item.images[0] : ''
}

function toDetail(id) {
  router.push(`/content/${id}`)
}

function toEdit(id) {
  router.push(`/publish/${id}`)
}

async function removeItem(id, title) {
  try {
    await ElMessageBox.confirm(
      `确定删除《${title}》吗？删除后不可恢复，其下评论也会一并删除。`,
      '删除确认',
      { type: 'warning', confirmButtonText: '删除', cancelButtonText: '取消' }
    )
  } catch {
    return // 用户点了取消
  }
  await postApi.deleteContent(id)
  ElMessage.success('已删除')
  await load()
  loadStats() // 删除后同步统计
}

onMounted(() => {
  load()
  loadStats()
})
</script>

<template>
  <div class="page-container">
    <!-- 个人统计条（规划书 TODO：数据统计展示） -->
    <div class="stat-bar">
      <div class="stat-card">
        <span class="stat-num">{{ statContent }}</span>
        <span class="stat-label">我的发布</span>
      </div>
      <div class="stat-card">
        <span class="stat-num">{{ statComment }}</span>
        <span class="stat-label">我的评论</span>
      </div>
      <div class="stat-card">
        <span class="stat-num">{{ statFav }}</span>
        <span class="stat-label">我的收藏</span>
      </div>
    </div>

    <el-tabs v-model="activeTab" class="mine-tabs" @tab-change="onTabChange">
      <!-- ===== 我的发布 ===== -->
      <el-tab-pane label="我的发布" name="posts">
        <div class="head">
          <span class="count">共 {{ total }} 条</span>
          <el-button type="primary" size="small" @click="router.push('/publish')">＋ 再发一条</el-button>
          <el-button
            :type="managing ? 'warning' : 'default'"
            size="small"
            plain
            @click="toggleManaging"
          >
            {{ managing ? '退出管理' : '批量管理' }}
          </el-button>
        </div>

        <div v-loading="loading" class="feed">
          <el-card
            v-for="c in list"
            :key="c.id"
            class="item-card"
            :class="{ selected: managing && isSelected(c.id) }"
            shadow="hover"
          >
            <!-- 管理模式：卡片左侧显示勾选框 -->
            <el-checkbox
              v-if="managing"
              :model-value="isSelected(c.id)"
              class="pick"
              @change="toggleSelect(c.id)"
            />
            <div
              class="item-body"
              @click="managing ? toggleSelect(c.id) : toDetail(c.id)"
            >
              <div class="badge">
                <el-tag :type="TYPE_MAP[c.type]?.tagType || 'info'" size="small">
                  {{ TYPE_MAP[c.type]?.label || c.type }}
                </el-tag>
                <span v-if="c.category" class="category">· {{ c.category }}</span>
              </div>
              <h3 class="title">{{ c.title }}</h3>
              <p class="summary">{{ c.body }}</p>
              <div class="meta">发布于 {{ formatTime(c.created_at) }}</div>
            </div>

            <el-image v-if="firstImage(c)" :src="firstImage(c)" fit="cover" class="thumb" />

            <div class="actions" v-if="!managing">
              <el-button size="small" type="primary" plain @click="toEdit(c.id)">编辑</el-button>
              <el-button size="small" type="danger" plain @click="removeItem(c.id, c.title)">删除</el-button>
            </div>
          </el-card>

          <el-empty v-if="!loading && !list.length" description="你还没有发布过内容">
            <el-button type="primary" @click="router.push('/publish')">去发布第一条</el-button>
          </el-empty>
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

        <!-- 批量管理底部操作栏 -->
        <div v-if="managing && list.length" class="batch-bar">
          <el-checkbox
            :model-value="selected.length === list.length && list.length > 0"
            @change="selectAll"
          >
            全选本页
          </el-checkbox>
          <span class="batch-count">已选 {{ selected.length }} 条</span>
          <el-button size="small" type="danger" :disabled="!selected.length" @click="removeSelected">
            批量删除
          </el-button>
        </div>
      </el-tab-pane>

      <!-- ===== 我的收藏 ===== -->
      <el-tab-pane label="我的收藏" name="favorites">
        <div class="head">
          <span class="count">共收藏 {{ favTotal }} 条</span>
        </div>

        <div v-loading="favLoading" class="feed">
          <el-card v-for="item in favList" :key="item.content.id" class="item-card" shadow="hover">
            <div class="item-body" @click="toDetail(item.content.id)">
              <div class="badge">
                <el-tag :type="TYPE_MAP[item.content.type]?.tagType || 'info'" size="small">
                  {{ TYPE_MAP[item.content.type]?.label || item.content.type }}
                </el-tag>
              </div>
              <h3 class="title">{{ item.content.title }}</h3>
              <p class="summary">{{ item.content.body }}</p>
              <div class="meta">收藏于 {{ formatTime(item.favTime) }}</div>
            </div>

            <el-image v-if="firstImage(item.content)" :src="firstImage(item.content)" fit="cover" class="thumb" />

            <div class="actions">
              <el-button size="small" type="warning" plain @click="unfav(item)">取消收藏</el-button>
            </div>
          </el-card>

          <el-empty v-if="!favLoading && !favList.length" description="还没有收藏内容，去详情页点亮 ⭐ 收藏吧">
            <el-button type="primary" @click="router.push('/')">去首页逛逛</el-button>
          </el-empty>
        </div>

        <div v-if="favTotal > size" class="pager">
          <el-pagination
            background
            layout="prev, pager, next"
            :total="favTotal"
            :page-size="size"
            :current-page="favPage"
            @current-change="onFavPageChange"
          />
        </div>
      </el-tab-pane>
    </el-tabs>
  </div>
</template>

<style scoped>
/* 个人统计条 */
.stat-bar {
  display: flex;
  gap: 12px;
  margin-bottom: 16px;
}

.stat-card {
  flex: 1;
  background: #f7f8fa;
  border-radius: 10px;
  padding: 14px 0;
  text-align: center;
}

.stat-num {
  display: block;
  font-size: 24px;
  font-weight: 700;
  color: #409eff;
}

.stat-label {
  display: block;
  margin-top: 4px;
  font-size: 13px;
  color: #909399;
}

/* 批量管理 */
.item-card.selected {
  border-color: #409eff;
  box-shadow: 0 0 0 1px #409eff inset;
}

.item-card .pick {
  margin-right: 10px;
  vertical-align: middle;
}

.batch-bar {
  display: flex;
  align-items: center;
  gap: 16px;
  margin-top: 16px;
  padding: 10px 16px;
  background: #f7f8fa;
  border-radius: 10px;
}

.batch-count {
  color: #909399;
  font-size: 13px;
}

.head {
  display: flex;
  align-items: baseline;
  gap: 12px;
  margin-bottom: 14px;
}

.head h2 {
  font-size: 20px;
  color: #303133;
}

.count {
  color: #909399;
  font-size: 13px;
  margin-right: auto;
}

.item-card {
  margin-bottom: 14px;
  border-radius: 10px;
  display: flex;
  align-items: center;
  gap: 14px;
}

.item-card .el-card__body {
  display: flex;
  align-items: center;
  gap: 14px;
  width: 100%;
}

.item-body {
  flex: 1;
  min-width: 0;
  cursor: pointer;
}

.badge {
  display: flex;
  align-items: center;
  gap: 6px;
  margin-bottom: 6px;
}

.category {
  color: #909399;
  font-size: 13px;
}

.title {
  font-size: 16px;
  color: #303133;
  margin-bottom: 4px;
}

.summary {
  color: #606266;
  font-size: 13px;
  line-height: 1.6;
  display: -webkit-box;
  -webkit-line-clamp: 1;
  -webkit-box-orient: vertical;
  overflow: hidden;
}

.meta {
  margin-top: 4px;
  color: #a8abb2;
  font-size: 12px;
}

.thumb {
  width: 96px;
  height: 72px;
  border-radius: 8px;
  flex-shrink: 0;
}

.actions {
  flex-shrink: 0;
  display: flex;
  flex-direction: column;
  gap: 8px;
}

.pager {
  display: flex;
  justify-content: center;
  padding: 10px 0 20px;
}
</style>
