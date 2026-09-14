<script setup>
// 管理后台：地点坐标管理（手动校准真实坐标）
// 左：高德地图点击拾取坐标；右：地点列表（编辑/删除/定位）
import { ref, computed, onMounted } from 'vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import MapComponent from '@/components/MapComponent.vue'
import { getLocations, adminSaveLocation, adminDeleteLocation } from '@/api/locations'

const mapRef = ref(null)
const locations = ref([])
const loading = ref(false)
const dialogVisible = ref(false)
const nameInput = ref('')
const pick = ref(null) // 地图点击拾取的 {lng, lat}

const locationMarkers = computed(() =>
  locations.value.map((p) => ({ id: 'loc-' + p.id, lng: p.lng, lat: p.lat, title: p.name }))
)

async function load() {
  loading.value = true
  try {
    const data = await getLocations()
    locations.value = data || []
  } catch {
    ElMessage.error('加载地点列表失败')
  } finally {
    loading.value = false
  }
}

// 地图点击 → 弹窗录入名称
function onMapClick({ lng, lat }) {
  pick.value = { lng: Number(Number(lng).toFixed(6)), lat: Number(Number(lat).toFixed(6)) }
  nameInput.value = ''
  dialogVisible.value = true
}

async function savePick() {
  const name = nameInput.value.trim()
  if (!name) {
    ElMessage.warning('请输入地点名称')
    return
  }
  try {
    await adminSaveLocation({ name, lng: pick.value.lng, lat: pick.value.lat })
    ElMessage.success(`「${name}」坐标已保存，发布选点/地图点位全局生效`)
    dialogVisible.value = false
    await load()
    mapRef.value?.setCenter(pick.value.lng, pick.value.lat, 17)
  } catch (e) {
    ElMessage.error(e?.msg || '保存失败')
  }
}

async function onDelete(row) {
  try {
    await ElMessageBox.confirm(`确定删除「${row.name}」？`, '删除确认', { type: 'warning' })
  } catch {
    return
  }
  try {
    await adminDeleteLocation(row.id)
    ElMessage.success('已删除')
    await load()
  } catch (e) {
    ElMessage.error(e?.msg || '删除失败')
  }
}

function locate(row) {
  mapRef.value?.setCenter(row.lng, row.lat, 18)
}

onMounted(load)
</script>

<template>
  <div class="loc-page">
    <div class="loc-header">
      <h2>📍 地点坐标管理</h2>
      <p class="tip">
        在左侧地图上点击真实位置 → 输入地点名称 → 保存。校准后，发布帖子选地点、地图上的帖子点位都会使用真实坐标。
        名称与现有地点相同则为「更新坐标」，不同则为「新增地点」。
      </p>
    </div>
    <div class="loc-body">
      <div class="map-side">
        <MapComponent
          ref="mapRef"
          :center="[118.007853, 36.814398]"
          :zoom="16"
          :markers="locationMarkers"
          height="100%"
          @click="onMapClick"
        />
        <div class="map-hint">🖱️ 点击地图任意位置拾取坐标</div>
      </div>
      <div class="list-side">
        <el-table :data="locations" v-loading="loading" size="small" max-height="560">
          <el-table-column prop="name" label="地点名称" min-width="140" show-overflow-tooltip />
          <el-table-column prop="lng" label="经度" width="112" />
          <el-table-column prop="lat" label="纬度" width="104" />
          <el-table-column label="操作" width="150" fixed="right">
            <template #default="{ row }">
              <el-button link type="primary" size="small" @click="locate(row)">定位</el-button>
              <el-button link type="danger" size="small" @click="onDelete(row)">删除</el-button>
            </template>
          </el-table-column>
        </el-table>
        <div class="count">共 {{ locations.length }} 个地点 · 点击地图即可新增/校准</div>
      </div>
    </div>

    <el-dialog v-model="dialogVisible" title="录入地点坐标" width="420px">
      <div class="pick-info">
        <div>📍 经度：{{ pick ? pick.lng : '-' }}</div>
        <div>📍 纬度：{{ pick ? pick.lat : '-' }}</div>
      </div>
      <el-input
        v-model="nameInput"
        placeholder="输入地点名称，如 第二食堂（同名则更新坐标）"
        maxlength="30"
        clearable
        @keyup.enter="savePick"
      />
      <template #footer>
        <el-button @click="dialogVisible = false">取消</el-button>
        <el-button type="primary" @click="savePick">保存</el-button>
      </template>
    </el-dialog>
  </div>
</template>

<style scoped>
.loc-page {
  padding: 20px;
  max-width: 1200px;
  margin: 0 auto;
}
.loc-header h2 {
  margin: 0 0 6px;
  font-size: 20px;
}
.loc-header .tip {
  margin: 0 0 16px;
  color: #909399;
  font-size: 13px;
}
.loc-body {
  display: flex;
  gap: 16px;
  align-items: flex-start;
}
.map-side {
  flex: 1 1 58%;
  position: relative;
  height: 560px;
  border-radius: 8px;
  overflow: hidden;
}
.map-hint {
  position: absolute;
  left: 10px;
  bottom: 10px;
  z-index: 1;
  background: rgba(255, 255, 255, 0.92);
  border-radius: 6px;
  padding: 5px 10px;
  font-size: 12px;
  color: #606266;
  box-shadow: 0 1px 4px rgba(0, 0, 0, 0.15);
}
.list-side {
  flex: 0 0 42%;
}
.count {
  margin-top: 8px;
  font-size: 12px;
  color: #909399;
}
.pick-info {
  display: flex;
  gap: 18px;
  margin-bottom: 12px;
  font-size: 14px;
  color: #303133;
  background: #f5f7fa;
  border-radius: 6px;
  padding: 10px 12px;
}
</style>
