<script setup>
// 失物招领详情页（归属：前端 C）
import { onMounted, ref } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import * as lostfoundApi from '@/api/lostfound'
import { formatTime } from '@/api/const'
import { getMockLostFound } from '@/utils/mockData'

const route = useRoute()
const router = useRouter()
const itemId = Number(route.params.id)
const item = ref(null)

async function loadDetail() {
  try {
    item.value = await lostfoundApi.getLostFound(itemId)
  } catch {
    const list = getMockLostFound()
    item.value = list.find((x) => x.id === itemId) || list[0]
  }
}

onMounted(loadDetail)
</script>

<template>
  <div class="page-container" v-if="item">
    <el-card shadow="never" class="detail-card">
      <div class="head">
        <el-tag :type="item.type === 'lost' ? 'danger' : 'success'" size="large">
          {{ item.type === 'lost' ? '🔍 寻物启事' : '📦 失物招领' }}
        </el-tag>
        <span class="meta">{{ item.author_name }} 发布于 {{ formatTime(item.created_at) }}</span>
      </div>

      <h1 class="title">{{ item.title }}</h1>

      <div class="info-grid">
        <div class="info-item">
          <span class="info-label">📦 物品名称</span>
          <span class="info-value">{{ item.item_name }}</span>
        </div>
        <div class="info-item">
          <span class="info-label">📍 {{ item.type === 'lost' ? '丢失地点' : '拾取地点' }}</span>
          <span class="info-value">{{ item.location }}</span>
        </div>
        <div class="info-item">
          <span class="info-label">🕐 {{ item.type === 'lost' ? '丢失时间' : '拾取时间' }}</span>
          <span class="info-value">{{ item.lost_time }}</span>
        </div>
        <div class="info-item">
          <span class="info-label">📱 联系方式</span>
          <span class="info-value contact">{{ item.contact }}</span>
        </div>
      </div>

      <div class="description-box">
        <div class="desc-title">📝 详细描述</div>
        <p>{{ item.description }}</p>
      </div>

      <div v-if="item.images && item.images.length" class="gallery">
        <el-image
          v-for="(img, i) in item.images"
          :key="i"
          :src="img"
          :preview-src-list="item.images"
          :initial-index="i"
          fit="cover"
          preview-teleported
          class="gallery-img"
        />
      </div>

      <div class="actions">
        <el-button type="primary" size="large" @click="router.back()">← 返回列表</el-button>
      </div>
    </el-card>
  </div>
</template>

<style scoped>
.page-container { max-width: 800px; margin: 0 auto; padding: 20px; }
.detail-card { border-radius: 12px; }
.head { display: flex; align-items: center; gap: 12px; margin-bottom: 16px; }
.meta { margin-left: auto; color: #a8abb2; font-size: 12px; }
.title { font-size: 24px; color: #303133; margin: 0 0 20px 0; }
.info-grid { display: grid; grid-template-columns: 1fr 1fr; gap: 16px; margin-bottom: 20px; }
.info-item { display: flex; flex-direction: column; gap: 4px; }
.info-label { font-size: 12px; color: #909399; }
.info-value { font-size: 15px; color: #303133; font-weight: 500; }
.info-value.contact { color: #1d6df0; }
.description-box { background: #f5f7fa; border-radius: 10px; padding: 16px; margin-bottom: 20px; }
.desc-title { font-weight: 600; color: #303133; margin-bottom: 8px; }
.description-box p { color: #4b4b4b; font-size: 14px; line-height: 1.8; margin: 0; white-space: pre-wrap; }
.gallery { display: flex; flex-wrap: wrap; gap: 10px; margin-bottom: 20px; }
.gallery-img { width: 200px; height: 200px; border-radius: 8px; border: 1px solid #ebeef5; }
.actions { display: flex; justify-content: center; }
</style>
