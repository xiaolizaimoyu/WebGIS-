<script setup>
// 发布 / 编辑页（归属：前端 B）
// - 无 :id 路由 = 新建发布
// - 带 :id 路由（/publish/:id）＝ 编辑已有内容（仅作者可进入，编辑由后端校验权限）
// 说明：本路由 requiresAuth，未登录会被全局守卫拦截到登录页
// TODO(前端B)：草稿、富文本编辑器、发布后二次编辑预览等扩展点
import { ref, reactive, computed, onMounted, watch } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { ElMessage } from 'element-plus'
import * as postApi from '@/api/post'
import LocationPicker from '@/components/map/LocationPicker.vue' // 前端A的Leaflet选点组件（免key）

const route = useRoute()
const router = useRouter()
const formRef = ref()
const submitting = ref(false)

// 编辑模式：/publish/:id 存在 id 即为编辑
const isEdit = computed(() => !!route.params.id)
const editId = computed(() => (route.params.id ? Number(route.params.id) : null))

const form = reactive({
  title: '',
  body: '',
  type: 'meeting',
  category: '',
  location: null // 选点结果 { lng, lat } | null；提交时映射为后端的 longitude / latitude
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

const fileList = ref([]) // el-upload 双向列表；新传成功 file.response={url}；历史图无 response，直接用 file.url
const previewVisible = ref(false)
const previewUrl = ref('')

// 编辑模式：拉取原内容回填表单与图片（后端返回 longitude / latitude）
async function loadEditing() {
  const data = await postApi.getContent(editId.value)
  form.title = data.title
  form.body = data.body
  form.type = data.type
  form.category = data.category || ''
  form.location =
    data.longitude != null && data.latitude != null
      ? { lng: data.longitude, lat: data.latitude }
      : null
  fileList.value = (data.images || []).map((url) => ({ name: url.split('/').pop(), url }))
}

onMounted(() => {
  if (isEdit.value) loadEditing()
})

// 自定义上传：替换默认 xhr，走我们的 /api/upload（已带 Token）
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

// 收集待提交图片：新传图用 response.url，历史图用自身 url（相对路径 /uploads/...）
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
      // 选点结果映射为后端字段：longitude / latitude 需成对提交（后端校验）
      longitude: form.location?.lng ?? null,
      latitude: form.location?.lat ?? null
    }
    let data
    if (isEdit.value) {
      data = await postApi.updateContent(editId.value, payload)
      ElMessage.success('修改成功')
      router.push('/mine') // 编辑后回到我的发布，列表自动刷新
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
            <!-- 新增分类（规划书 5-2）：美食分享 / 失物招领 -->
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

        <!-- 地图选点（前端A的Leaflet组件，点击地图拾取，免key） -->
        <el-form-item label="地图选点">
          <LocationPicker v-model="form.location" style="width: 100%" />
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
</style>
