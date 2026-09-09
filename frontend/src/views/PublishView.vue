<script setup>
// 发布 / 编辑页（归属：前端 B）
// - 无 :id 路由 = 新建发布
// - 带 :id 路由（/publish/:id）＝ 编辑已有内容（仅作者可进入，编辑由后端校验权限）
// 说明：本路由 requiresAuth，未登录会被全局守卫拦截到登录页
// TODO(前端B)：富文本编辑器、发布后二次编辑预览等扩展点
// 地点：可选校园地点（如 二餐）自动定位，也可在地图上手动点击拾取精确位置
import { ref, reactive, computed, onMounted, watch } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { ElMessage } from 'element-plus'
import * as postApi from '@/api/post'
import LocationPicker from '@/components/map/LocationPicker.vue' // 前端A的Leaflet选点组件（免key）
import { CAMPUS_PLACES } from '@/api/const'

const route = useRoute()
const router = useRouter()
const formRef = ref()
const submitting = ref(false)

// 校园地点选项（真实校园位置：如 二餐 → 自动定位到第二食堂坐标）
const placeOptions = CAMPUS_PLACES.map((p) => ({ value: p.name, lng: p.lng, lat: p.lat, label: p.name }))

const isEdit = computed(() => !!route.params.id)
const editId = computed(() => (route.params.id ? Number(route.params.id) : null))

const form = reactive({
  title: '',
  body: '',
  type: 'meeting',
  category: '',
  longitude: null,
  latitude: null,
  location_name: ''
})

// ===== 草稿自动保存（前端 B，规划书 TODO：草稿箱）=====
// 仅"新建发布"时生效：输入停顿 600ms 自动存 localStorage，发布成功后清除；
// 编辑已有内容不写草稿（改的是线上数据，无草稿语义）。
// key 独立前缀，不与队友的 utils/storage.js（auth 专用）混用。
const DRAFT_KEY = 'campus_draft_publish_B'
let draftTimer = null

watch(
  () => ({ title: form.title, body: form.body, type: form.type }),
  (val) => {
    if (isEdit.value) return
    if (!val.title.trim() && !val.body.trim()) return // 空表单不存
    clearTimeout(draftTimer)
    draftTimer = setTimeout(() => {
      localStorage.setItem(DRAFT_KEY, JSON.stringify({ ...val, savedAt: Date.now() }))
    }, 600)
  }
)

function restoreDraft() {
  try {
    const draft = JSON.parse(localStorage.getItem(DRAFT_KEY) || 'null')
    if (!draft) return
    // 草稿超过 7 天视为过期，直接丢弃
    if (Date.now() - draft.savedAt > 7 * 24 * 3600 * 1000) {
      localStorage.removeItem(DRAFT_KEY)
      return
    }
    form.title = draft.title || ''
    form.body = draft.body || ''
    form.type = draft.type || 'meeting'
    if (form.title || form.body) {
      ElMessage.info('已恢复上次未发布的草稿')
    }
  } catch {
    localStorage.removeItem(DRAFT_KEY)
  }
}

function clearDraft() {
  localStorage.removeItem(DRAFT_KEY)
}

const rules = {
  title: [{ required: true, message: '请输入标题', trigger: 'blur' }],
  body: [{ required: true, message: '请输入正文内容', trigger: 'blur' }]
}

const fileList = ref([])
const previewVisible = ref(false)
const previewUrl = ref('')

// 编辑模式：回填表单
async function loadEditing() {
  const data = await postApi.getContent(editId.value)
  form.title = data.title
  form.body = data.body
  form.type = data.type
  form.category = data.category || ''
  form.longitude = data.longitude ?? null
  form.latitude = data.latitude ?? null
  form.location_name = data.location_name || ''
  fileList.value = (data.images || []).map((url) => ({ name: url.split('/').pop(), url }))
}

// 选择校园地点 → 自动填充坐标
function onPlaceChange(name) {
  const p = placeOptions.find((x) => x.value === name)
  if (!p) return
  form.location_name = p.value
  form.longitude = p.lng
  form.latitude = p.lat
  ElMessage.success(`已定位到「${p.label}」`)
}

// LocationPicker 手动选点 → 清除地点名（自定义位置）
function onManualPick(loc) {
  if (!loc || loc.lng == null) return
  form.location_name = ''
  form.longitude = loc.lng
  form.latitude = loc.lat
}

function clearPoint() {
  form.longitude = null
  form.latitude = null
  form.location_name = ''
}

onMounted(() => {
  if (isEdit.value) loadEditing()
  else restoreDraft() // 新建模式恢复上次草稿
})

// 自定义上传：走 /api/upload（已带 Token）
async function doUpload(options) {
  const data = await postApi.uploadImage(options.file)
  options.onSuccess(data, options.file)
}

function imageUrl(file) {
  return file.response ? file.response.url : file.url
}

function onPreview(file) {
  previewUrl.value = imageUrl(file)
  previewVisible.value = true
}

function onExceed() {
  ElMessage.warning('最多上传 5 张图片')
}

function collectImages() {
  return fileList.value
    .map((f) => (f.response ? f.response.url : isEdit.value ? f.url : null))
    .filter(Boolean)
}

async function submit() {
  try {
    await formRef.value.validate()
  } catch {
    return
  }
  submitting.value = true
  try {
    const payload = {
      title: form.title.trim(),
      body: form.body.trim(),
      type: form.type,
      category: undefined,
      images: collectImages(),
      longitude: form.longitude,
      latitude: form.latitude,
      location_name: form.location_name
    }
    let data
    if (isEdit.value) {
      data = await postApi.updateContent(editId.value, payload)
      ElMessage.success('修改成功')
      router.push('/mine')
    } else {
      data = await postApi.createContent(payload)
      clearDraft() // 发布成功，草稿使命完成
      ElMessage.success('发布成功')
      router.push(`/content/${data.id}`)
    }
  } finally {
    submitting.value = false
  }
}
</script>

<template>
  <div class="page-container">
    <el-card shadow="never">
      <template #header>{{ isEdit ? '编辑内容' : '发布新内容' }}</template>
      <el-form ref="formRef" :model="form" :rules="rules" label-width="90px">
        <el-form-item label="内容分类" prop="type">
          <el-radio-group v-model="form.type">
            <el-radio-button value="meeting">校园会议</el-radio-button>
            <el-radio-button value="news">校园动态</el-radio-button>
            <el-radio-button value="food">美食分享</el-radio-button>
            <el-radio-button value="lost">失物招领</el-radio-button>
          </el-radio-group>
        </el-form-item>

        <el-form-item label="标题" prop="title">
          <el-input
            v-model="form.title"
            maxlength="80"
            show-word-limit
            placeholder="一句话说清内容标题"
          />
        </el-form-item>

        <el-form-item label="正文" prop="body">
          <el-input
            v-model="form.body"
            type="textarea"
            :rows="6"
            maxlength="5000"
            placeholder="详细描述内容……（活动可写时间地点，广告可写价格联系方式等）"
          />
        </el-form-item>

        <el-form-item label="选择地点">
          <el-select
            v-model="form.location_name"
            placeholder="选择校园地点（如 二餐、图书馆），地图自动定位"
            clearable
            filterable
            style="width: 100%"
            @change="onPlaceChange"
            @clear="clearPoint"
          >
            <el-option v-for="p in placeOptions" :key="p.value" :label="p.label" :value="p.value" />
          </el-select>
        </el-form-item>

        <el-form-item label="地图定位">
          <div class="map-wrap">
            <LocationPicker
              :model-value="{ lng: form.longitude, lat: form.latitude }"
              @update:model-value="onManualPick"
            />
            <div class="map-hint">
              💡 可在上方选择校园地点快速定位，也可直接在地图上点击拾取精确位置
            </div>
          </div>
        </el-form-item>

        <el-form-item label="图片">
          <el-upload
            v-model:file-list="fileList"
            list-type="picture-card"
            accept="image/*"
            :limit="5"
            :http-request="doUpload"
            :on-preview="onPreview"
            :on-exceed="onExceed"
          >
            <div class="upload-tip">＋<br />上传图片</div>
          </el-upload>
        </el-form-item>

        <el-form-item>
          <el-button type="primary" :loading="submitting" @click="submit">
            {{ isEdit ? '保存修改' : '立即发布' }}
          </el-button>
          <el-button @click="router.back()">取消</el-button>
        </el-form-item>
      </el-form>
    </el-card>

    <el-dialog v-model="previewVisible" title="图片预览" width="600px">
      <img v-if="previewUrl" :src="previewUrl" alt="preview" style="width: 100%" />
    </el-dialog>
  </div>
</template>

<style scoped>
.upload-tip {
  color: #8c939d;
  font-size: 13px;
  line-height: 1.6;
}

.map-wrap {
  width: 100%;
}

.map-hint {
  margin-top: 6px;
  font-size: 12px;
  color: #909399;
}
</style>
