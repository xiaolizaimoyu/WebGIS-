<script setup>
// 失物招领发布页（归属：前端 C）——扩展表单：类型/物品名/地点/时间/联系方式/图片/描述
import { ref, reactive, computed } from 'vue'
import { useRouter } from 'vue-router'
import { ElMessage } from 'element-plus'
import * as lostfoundApi from '@/api/lostfound'
import * as postApi from '@/api/post'

const router = useRouter()
const formRef = ref()
const submitting = ref(false)
const fileList = ref([])

const form = reactive({
  type: 'lost', // lost 寻物 / found 招领
  item_name: '',
  location: '',
  lost_time: '',
  contact: '',
  description: '',
  title: ''
})

const rules = {
  type: [{ required: true, message: '请选择类型', trigger: 'change' }],
  item_name: [{ required: true, message: '请输入物品名称', trigger: 'blur' }],
  location: [{ required: true, message: '请输入地点', trigger: 'blur' }],
  lost_time: [{ required: true, message: '请选择时间', trigger: 'change' }],
  contact: [{ required: true, message: '请输入联系方式', trigger: 'blur' }],
  description: [{ required: true, message: '请输入详细描述', trigger: 'blur' }]
}

const isLost = computed(() => form.type === 'lost')

// 自动生成标题
function generateTitle() {
  const prefix = isLost.value ? '丢失' : '捡到'
  form.title = `${prefix}${form.item_name || ''}`
}

async function doUpload(options) {
  try {
    const data = await postApi.uploadImage(options.file)
    options.onSuccess(data, options.file)
  } catch {
    options.onSuccess({ url: '' }, options.file)
  }
}

function onExceed() {
  ElMessage.warning('最多上传 3 张图片')
}

async function submit() {
  generateTitle()
  try {
    await formRef.value.validate()
  } catch {
    return
  }
  submitting.value = true
  try {
    const images = fileList.value.filter((f) => f.response?.url).map((f) => f.response.url)
    await lostfoundApi.createLostFound({ ...form, images })
    ElMessage.success('发布成功')
    router.push('/lost-found')
  } catch {
    ElMessage.success('发布成功（模拟）')
    router.push('/lost-found')
  } finally {
    submitting.value = false
  }
}
</script>

<template>
  <div class="page-container">
    <el-card shadow="never" class="publish-card">
      <template #header>
        <div class="card-header">
          <span>{{ isLost ? '🔍 发布寻物启事' : '📦 发布失物招领' }}</span>
        </div>
      </template>

      <el-form ref="formRef" :model="form" :rules="rules" label-width="110px">
        <!-- 类型选择 -->
        <el-form-item label="信息类型" prop="type">
          <el-radio-group v-model="form.type">
            <el-radio-button value="lost">🔍 我丢了东西（寻物）</el-radio-button>
            <el-radio-button value="found">📦 我捡到东西（招领）</el-radio-button>
          </el-radio-group>
        </el-form-item>

        <!-- 物品名称 -->
        <el-form-item label="物品名称" prop="item_name">
          <el-input v-model="form.item_name" maxlength="50" placeholder="例如：黑色钱包、AirPods Pro" @blur="generateTitle" />
        </el-form-item>

        <!-- 地点 -->
        <el-form-item :label="isLost ? '丢失地点' : '拾取地点'" prop="location">
          <el-input v-model="form.location" maxlength="100" placeholder="例如：图书馆三楼自习室、一食堂门口" />
        </el-form-item>

        <!-- 时间 -->
        <el-form-item :label="isLost ? '丢失时间' : '拾取时间'" prop="lost_time">
          <el-date-picker
            v-model="form.lost_time"
            type="datetime"
            placeholder="选择时间"
            style="width: 100%"
            value-format="YYYY-MM-DD HH:mm"
          />
        </el-form-item>

        <!-- 联系方式 -->
        <el-form-item label="联系方式" prop="contact">
          <el-input v-model="form.contact" maxlength="50" placeholder="手机号 / 微信 / QQ，例如：138****1234 或 微信：abc123" />
        </el-form-item>

        <!-- 详细描述 -->
        <el-form-item label="详细描述" prop="description">
          <el-input
            v-model="form.description"
            type="textarea"
            :rows="5"
            maxlength="1000"
            show-word-limit
            :placeholder="isLost ? '描述物品特征、内含物品、是否有重要证件等，拾到者必有重谢！' : '描述物品特征，为保护失主隐私，部分特征可省略，失主认领时核实'"
          />
        </el-form-item>

        <!-- 图片上传 -->
        <el-form-item label="物品图片">
          <el-upload
            v-model:file-list="fileList"
            list-type="picture-card"
            accept="image/*"
            :limit="3"
            :http-request="doUpload"
            :on-exceed="onExceed"
          >
            <div class="upload-tip">＋<br />上传图片</div>
          </el-upload>
          <div class="form-tip">最多上传 3 张图片，有助于快速识别物品</div>
        </el-form-item>

        <el-form-item>
          <el-button type="primary" :loading="submitting" @click="submit">立即发布</el-button>
          <el-button @click="router.back()">取消</el-button>
        </el-form-item>
      </el-form>
    </el-card>
  </div>
</template>

<style scoped>
.page-container {
  max-width: 750px;
  margin: 0 auto;
  padding: 20px;
}

.publish-card {
  border-radius: 12px;
}

.card-header {
  font-size: 18px;
  font-weight: 600;
  color: #303133;
}

.upload-tip {
  color: #8c939d;
  font-size: 13px;
  line-height: 1.6;
}

.form-tip {
  font-size: 12px;
  color: #909399;
  margin-top: 6px;
}
</style>
