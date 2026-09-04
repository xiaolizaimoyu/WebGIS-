<script setup>
// 我的发布管理页（归属：前端 B）
// 登录用户管理自己发布的内容：查看 / 编辑 / 删除
// TODO(前端B)：批量管理、草稿箱、数据统计展示等扩展点
import { onMounted, ref } from 'vue'
import { useRouter } from 'vue-router'
import { ElMessage, ElMessageBox } from 'element-plus'
import * as postApi from '@/api/post'
import { formatTime } from '@/api/const'
import { TYPE_MAP } from '@/api/typeMap' // B 扩展版：含美食分享 / 失物招领

const router = useRouter()

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
}

onMounted(load)
</script>

<template>
  <div class="page-container">
    <div class="head">
      <h2>我的发布</h2>
      <span class="count">共 {{ total }} 条</span>
      <el-button type="primary" size="small" @click="router.push('/publish')">＋ 再发一条</el-button>
    </div>

    <div v-loading="loading" class="feed">
      <el-card v-for="c in list" :key="c.id" class="item-card" shadow="hover">
        <div class="item-body" @click="toDetail(c.id)">
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

        <div class="actions">
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
  </div>
</template>

<style scoped>
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
