<script setup>
// 上传资料页（归属：前端 C）
import { ref, reactive } from 'vue'
import { useRouter } from 'vue-router'
import { ElMessage } from 'element-plus'
import * as materialApi from '@/api/material'

const router = useRouter()
const formRef = ref()
const submitting = ref(false)
const fileList = ref([])

const subjects = ['数学', '英语', 'GIS', '遥感', '编程', '专业课', '其他']

const form = reactive({
  title: '',
  description: '',
  subject: '专业课',
  tags: ''
})

const rules = {
  title: [{ required: true, message: '请输入资料标题', trigger: 'blur' }],
  description: [{ required: true, message: '请输入资料描述', trigger: 'blur' }],
  subject: [{ required: true, message: '请选择学科分类', trigger: 'change' }]
}

function beforeUpload(file) {
  const maxSize = 50 * 1024 * 1024 // 50MB
  if (file.size > maxSize) {
    ElMessage.error('文件大小不能超过 50MB')
    return false
  }
  return true
}

function onExceed() {
  ElMessage.warning('只能上传一个文件')
}

async function submit() {
  try {
    await formRef.value.validate()
  } catch {
    return
  }
  if (!fileList.value.length) {
    ElMessage.warning('请选择要上传的文件')
    return
  }
  submitting.value = true
  try {
    const formData = new FormData()
    formData.append('file', fileList.value[0].raw)
    formData.append('title', form.title)
    formData.append('description', form.description)
    formData.append('subject', form.subject)
    formData.append('tags', form.tags)
    await materialApi.uploadMaterial(formData)
    ElMessage.success('上传成功，审核通过后将展示')
    router.push('/materials')
  } catch {
    // mock 模式
    ElMessage.success('上传成功（模拟）')
    router.push('/materials')
  } finally {
    submitting.value = false
  }
}
</script>

<template>
  <div class="page-container">
    <el-card shadow="never" class="upload-card">
      <template #header>
        <div class="card-header">
          <span>⬆️ 上传学习资料</span>
        </div>
      </template>

      <el-form ref="formRef" :model="form" :rules="rules" label-width="100px">
        <el-form-item label="资料文件" required>
          <el-upload
            v-model:file-list="fileList"
            :auto-upload="false"
            :limit="1"
            :before-upload="beforeUpload"
            :on-exceed="onExceed"
            drag
          >
            <el-icon class="el-icon--upload"><upload-filled /></el-icon>
            <div class="el-upload__text">将文件拖到此处，或<em>点击上传</em></div>
            <template #tip>
              <div class="el-upload__tip">支持 PDF / Word / PPT / ZIP 等格式，单个文件不超过 50MB</div>
            </template>
          </el-upload>
        </el-form-item>

        <el-form-item label="学科分类" prop="subject">
          <el-select v-model="form.subject" placeholder="请选择学科" style="width: 220px">
            <el-option v-for="s in subjects" :key="s" :label="s" :value="s" />
          </el-select>
        </el-form-item>

        <el-form-item label="资料标题" prop="title">
          <el-input v-model="form.title" maxlength="100" show-word-limit placeholder="例如：高等数学（下册）期末复习笔记" />
        </el-form-item>

        <el-form-item label="资料描述" prop="description">
          <el-input
            v-model="form.description"
            type="textarea"
            :rows="5"
            maxlength="1000"
            show-word-limit
            placeholder="简要描述资料内容、适用人群、使用建议等..."
          />
        </el-form-item>

        <el-form-item label="标签">
          <el-input v-model="form.tags" placeholder="多个标签用逗号分隔，如：高数,期末,复习" />
        </el-form-item>

        <el-form-item>
          <el-button type="primary" :loading="submitting" @click="submit">提交上传</el-button>
          <el-button @click="router.back()">取消</el-button>
        </el-form-item>
      </el-form>
    </el-card>
  </div>
</template>

<script>
import { UploadFilled } from '@element-plus/icons-vue'
export default { components: { UploadFilled } }
</script>

<style scoped>
.page-container {
  max-width: 800px;
  margin: 0 auto;
  padding: 20px;
}

.upload-card {
  border-radius: 12px;
}

.card-header {
  font-size: 18px;
  font-weight: 600;
  color: #303133;
}
</style>
