<script setup>
// 管理后台（归属：后端 D 实现）
// 独立全屏布局：统计卡片 + 帖子审核表格 + 用户管理表格
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
const contentQuery = reactive({ page: 1, page_size: 10, type: '' })
const contentList = ref({ total: 0, list: [] })

// 用户管理
const userQuery = reactive({ page: 1, page_size: 10, keyword: '' })
const userList = ref({ total: 0, list: [] })

const TYPE_LABEL = {
  meeting: '校园会议', news: '校园动态', food: '校园美食', lost: '失物招领'
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
})
</script>

<template>
  <div class="admin-page">
    <header class="admin-header">
      <div class="header-inner">
        <span class="brand">🛡️ 管理后台</span>
        <div class="spacer" />
        <span class="admin-name">{{ store.userInfo?.nickname }}</span>
        <el-button size="small" @click="onLogout">退出</el-button>
      </div>
    </header>

    <main class="admin-main">
      <!-- 统计卡片 -->
      <div class="stat-cards">
        <div class="stat-card"><div class="num">{{ stats.total_users ?? '-' }}</div><div class="label">用户总数</div></div>
        <div class="stat-card"><div class="num">{{ stats.total_contents ?? '-' }}</div><div class="label">帖子总数</div></div>
        <div class="stat-card"><div class="num">{{ stats.total_comments ?? '-' }}</div><div class="label">评论总数</div></div>
        <div class="stat-card"><div class="num">{{ stats.today_new_users ?? '-' }}</div><div class="label">今日新增用户</div></div>
        <div class="stat-card"><div class="num">{{ stats.today_new_contents ?? '-' }}</div><div class="label">今日新增帖子</div></div>
      </div>

      <el-tabs v-model="activeTab" class="admin-tabs">
        <!-- 帖子审核 -->
        <el-tab-pane label="帖子审核" name="contents">
          <div class="filter-row">
            <el-select v-model="contentQuery.type" placeholder="全部分类" clearable style="width:160px" @change="contentQuery.page=1; loadContents()">
              <el-option v-for="(label, key) in TYPE_LABEL" :key="key" :label="label" :value="key" />
            </el-select>
          </div>
          <el-table :data="contentList.list" border stripe>
            <el-table-column prop="title" label="标题" min-width="180" show-overflow-tooltip />
            <el-table-column prop="author_name" label="作者" width="120" />
            <el-table-column label="分类" width="100">
              <template #default="{ row }">{{ TYPE_LABEL[row.type] || row.type }}</template>
            </el-table-column>
            <el-table-column prop="created_at" label="发布时间" width="170">
              <template #default="{ row }">{{ row.created_at?.slice(0, 16).replace('T', ' ') }}</template>
            </el-table-column>
            <el-table-column label="操作" width="100" fixed="right">
              <template #default="{ row }">
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
            <el-button @click="userQuery.page=1; loadUsers()">搜索</el-button>
          </div>
          <el-table :data="userList.list" border stripe>
            <el-table-column prop="username" label="账号" width="140" />
            <el-table-column prop="nickname" label="昵称" width="140" />
            <el-table-column label="身份" width="90">
              <template #default="{ row }">
                <el-tag v-if="row.is_admin" type="danger" size="small">管理员</el-tag>
                <el-tag v-else type="info" size="small">用户</el-tag>
              </template>
            </el-table-column>
            <el-table-column prop="content_count" label="发帖数" width="90" />
            <el-table-column prop="comment_count" label="评论数" width="90" />
            <el-table-column prop="created_at" label="注册时间" width="170">
              <template #default="{ row }">{{ row.created_at?.slice(0, 16).replace('T', ' ') }}</template>
            </el-table-column>
            <el-table-column label="操作" width="100" fixed="right">
              <template #default="{ row }">
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
      </el-tabs>
    </main>
  </div>
</template>

<style scoped>
.admin-page {
  min-height: 100vh;
  background: #f0f2f5;
}

.admin-header {
  background: #1a1f2e;
  color: #f1f3f5;
  position: sticky;
  top: 0;
  z-index: 100;
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.2);
}

.header-inner {
  max-width: 1100px;
  margin: 0 auto;
  height: 56px;
  display: flex;
  align-items: center;
  gap: 12px;
  padding: 0 20px;
}

.brand {
  font-size: 18px;
  font-weight: 600;
}

.spacer {
  flex: 1;
}

.admin-name {
  color: #c0c4d0;
  font-size: 14px;
}

.admin-main {
  max-width: 1100px;
  margin: 0 auto;
  padding: 24px 20px;
}

.stat-cards {
  display: grid;
  grid-template-columns: repeat(5, 1fr);
  gap: 16px;
  margin-bottom: 24px;
}

.stat-card {
  background: #fff;
  border-radius: 10px;
  padding: 18px;
  text-align: center;
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.05);
}

.stat-card .num {
  font-size: 26px;
  font-weight: 700;
  color: #303133;
}

.stat-card .label {
  font-size: 13px;
  color: #909399;
  margin-top: 4px;
}

.admin-tabs {
  background: #fff;
  border-radius: 10px;
  padding: 16px 20px;
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.05);
}

.filter-row {
  display: flex;
  gap: 10px;
  margin-bottom: 14px;
}

.pager {
  margin-top: 14px;
  justify-content: flex-end;
}
</style>
