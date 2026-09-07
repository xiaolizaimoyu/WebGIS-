<script setup>
// 资料详情页（归属：前端 C）
import { onMounted, ref } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { ElMessage } from 'element-plus'
import * as materialApi from '@/api/material'
import { formatTime } from '@/api/const'
import { getMockMaterialDetail } from '@/utils/mockData'
import { useUserStore } from '@/stores/user'
import { storage } from '@/utils/storage'

const route = useRoute()
const router = useRouter()
const store = useUserStore()

const materialId = Number(route.params.id)
const material = ref(null)
const liking = ref(false)

const fileTypeIcon = {
  pdf: '📄', docx: '📝', doc: '📝', zip: '📦', rar: '📦',
  ppt: '📊', pptx: '📊', xls: '📈', xlsx: '📈', txt: '📃', default: '📁'
}

async function loadDetail() {
  try {
    material.value = await materialApi.getMaterial(materialId)
  } catch {
    material.value = getMockMaterialDetail(materialId)
  }
}

async function handleDownload() {
  if (!store.isLoggedIn) {
    ElMessage.warning('请先登录后再下载')
    router.push({ path: '/login', query: { redirect: route.fullPath } })
    return
  }
  try {
    // 真实下载：后端动态生成文件，浏览器直接保存（绕过 JSON 拦截器）
    const token = storage.getToken()
    const res = await fetch(`/api/materials/${materialId}/download`, {
      headers: token ? { Authorization: `Bearer ${token}` } : {}
    })
    if (!res.ok) {
      const err = await res.json().catch(() => null)
      ElMessage.error(err?.msg || '下载失败，请稍后重试')
      return
    }
    const blob = await res.blob()
    // 从 Content-Disposition 解析文件名（UTF-8 编码）
    const cd = res.headers.get('Content-Disposition') || ''
    const m = cd.match(/filename\*=UTF-8''([^;]+)/) || cd.match(/filename="([^"]+)/)
    const filename = m ? decodeURIComponent(m[1]) : `资料${materialId}.pdf`
    const url = URL.createObjectURL(blob)
    const a = document.createElement('a')
    a.href = url
    a.download = filename
    document.body.appendChild(a)
    a.click()
    a.remove()
    URL.revokeObjectURL(url)
    // 下载数 +1（本地乐观更新）
    if (material.value) material.value.downloads = (material.value.downloads || 0) + 1
    ElMessage.success('下载成功')
  } catch {
    ElMessage.error('下载失败，请稍后重试')
  }
}

async function handleLike() {
  if (!store.isLoggedIn) {
    ElMessage.warning('请先登录')
    router.push({ path: '/login', query: { redirect: route.fullPath } })
    return
  }
  liking.value = true
  try {
    const data = await materialApi.likeMaterial(materialId)
    // 后端返回最新点赞数；未返回时兜底 +1，杜绝 NaN
    material.value.likes = data?.likes ?? (material.value.likes || 0) + 1
    ElMessage.success('点赞成功')
  } catch {
    material.value.likes = (material.value.likes || 0) + 1
    ElMessage.success('点赞成功（网络异常，已本地+1）')
  } finally {
    liking.value = false
  }
}

onMounted(loadDetail)
</script>

<template>
  <div class="page-container" v-if="material">
    <el-card shadow="never" class="detail-card">
      <div class="detail-head">
        <div class="file-icon">{{ fileTypeIcon[material.file_type] || '📁' }}</div>
        <div class="detail-info">
          <div class="tags">
            <el-tag type="success" size="small">{{ material.subject }}</el-tag>
            <el-tag type="info" size="small">{{ material.file_type.toUpperCase() }}</el-tag>
            <el-tag v-for="t in material.tags" :key="t" size="small" effect="plain">{{ t }}</el-tag>
          </div>
          <h1 class="title">{{ material.title }}</h1>
          <div class="meta">
            <span>👤 {{ material.author_name }}</span>
            <span>🕐 {{ formatTime(material.created_at) }}</span>
            <span>📦 {{ material.file_size }}</span>
          </div>
        </div>
      </div>

      <div class="divider" />

      <div class="description">
        <h3>📋 资料简介</h3>
        <p>{{ material.description }}</p>
      </div>

      <div class="stats-row">
        <div class="stat-item">
          <span class="stat-num">{{ material.downloads }}</span>
          <span class="stat-label">下载量</span>
        </div>
        <div class="stat-item">
          <span class="stat-num">{{ material.likes || 0 }}</span>
          <span class="stat-label">点赞数</span>
        </div>
        <div class="stat-item">
          <span class="stat-num">{{ material.file_size }}</span>
          <span class="stat-label">文件大小</span>
        </div>
      </div>

      <div class="actions">
        <el-button type="primary" size="large" @click="handleDownload">
          ⬇️ 下载资料
        </el-button>
        <el-button size="large" :loading="liking" @click="handleLike">
          ❤️ 点赞 ({{ material.likes || 0 }})
        </el-button>
        <el-button size="large" @click="router.back()">
          ← 返回
        </el-button>
      </div>
    </el-card>
  </div>
</template>

<style scoped>
.page-container {
  max-width: 900px;
  margin: 0 auto;
  padding: 20px;
}

.detail-card {
  border-radius: 12px;
}

.detail-head {
  display: flex;
  gap: 20px;
  align-items: flex-start;
}

.file-icon {
  font-size: 56px;
  width: 80px;
  height: 80px;
  display: flex;
  align-items: center;
  justify-content: center;
  background: linear-gradient(135deg, #f0f9eb, #e1f3d8);
  border-radius: 16px;
  flex-shrink: 0;
}

.detail-info {
  flex: 1;
  min-width: 0;
}

.tags {
  display: flex;
  gap: 6px;
  margin-bottom: 10px;
  flex-wrap: wrap;
}

.title {
  font-size: 22px;
  color: #303133;
  margin-bottom: 8px;
}

.meta {
  display: flex;
  gap: 16px;
  color: #909399;
  font-size: 13px;
}

.divider {
  height: 1px;
  background: #f0f2f5;
  margin: 20px 0;
}

.description h3 {
  font-size: 16px;
  color: #303133;
  margin-bottom: 10px;
}

.description p {
  color: #4b4b4b;
  font-size: 14px;
  line-height: 1.9;
  white-space: pre-wrap;
}

.stats-row {
  display: flex;
  gap: 40px;
  margin: 24px 0;
  padding: 20px;
  background: linear-gradient(135deg, #f5f7fa, #fff);
  border-radius: 12px;
}

.stat-item {
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 4px;
}

.stat-num {
  font-size: 24px;
  font-weight: 700;
  color: #1d6df0;
}

.stat-label {
  font-size: 12px;
  color: #909399;
}

.actions {
  display: flex;
  gap: 12px;
  justify-content: center;
  padding-top: 10px;
}
</style>
