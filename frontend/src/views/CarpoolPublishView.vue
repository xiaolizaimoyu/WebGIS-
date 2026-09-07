<script setup>
// 发布/编辑拼车页（前端 C）——支持新增与编辑两种模式（路由带 :id 时为编辑）
import { ref, reactive, onMounted, computed } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { ElMessage } from 'element-plus'
import * as carpoolApi from '@/api/carpool'
import { useUserStore } from '@/stores/user'

const route = useRoute()
const router = useRouter()
const store = useUserStore()

const editId = computed(() => (route.params.id ? Number(route.params.id) : null))
const isEdit = computed(() => editId.value !== null)

const formRef = ref()
const submitting = ref(false)

const form = reactive({
  title: '',
  from: '',
  to: '',
  depart_time: '',
  return_time: '',
  seats_total: 4,
  price_per_person: 0,
  phone: '',
  note: ''
})

// 校验：出发时间不能早于当前时间
function validateDepartTime(rule, value, callback) {
  if (!value) {
    callback(new Error('请选择出发时间'))
    return
  }
  const dt = new Date(value.replace(' ', 'T'))
  if (dt.getTime() < Date.now() - 60 * 1000) {
    callback(new Error('出发时间不能早于当前时间'))
    return
  }
  callback()
}

const rules = {
  title: [{ required: true, message: '请输入标题', trigger: 'blur' }],
  from: [{ required: true, message: '请输入出发地', trigger: 'blur' }],
  to: [{ required: true, message: '请输入目的地', trigger: 'blur' }],
  depart_time: [{ required: true, validator: validateDepartTime, trigger: 'change' }],
  seats_total: [{ required: true, message: '请设置座位数（1-7）', trigger: 'change' }],
  phone: [
    { required: true, message: '请输入联系电话', trigger: 'blur' },
    { pattern: /^1\d{10}$/, message: '手机号需为 11 位数字（如 13812345678）', trigger: 'blur' }
  ]
}

async function loadDetail() {
  try {
    const data = await carpoolApi.getCarpool(editId.value)
    if (store.isLoggedIn && data.is_author === false) {
      ElMessage.warning('只能编辑自己发布的拼车')
      router.replace('/carpool')
      return
    }
    form.title = data.title || ''
    form.from = data.from || ''
    form.to = data.to || ''
    form.depart_time = data.depart_time || ''
    form.return_time = data.return_time || ''
    form.seats_total = data.seats_total || 4
    form.price_per_person = data.price_per_person || 0
    form.phone = data.phone || ''
    form.note = data.note || ''
  } catch {
    ElMessage.error('拼车信息加载失败')
    router.replace('/carpool')
  }
}

onMounted(() => {
  if (isEdit.value) {
    loadDetail()
  }
})

async function submit() {
  try {
    await formRef.value.validate()
  } catch {
    return
  }
  submitting.value = true
  try {
    const payload = { ...form }
    if (isEdit.value) {
      await carpoolApi.updateCarpool(editId.value, payload)
      ElMessage.success('保存成功')
    } else {
      await carpoolApi.createCarpool(payload)
      ElMessage.success('发布成功')
    }
    router.push('/carpool')
  } catch (e) {
    ElMessage.error(e?.response?.data?.detail || '操作失败，请检查输入内容')
  } finally {
    submitting.value = false
  }
}
</script>

<template>
  <div class="page-container">
    <el-card shadow="never" class="publish-card">
      <template #header><span class="card-title">{{ isEdit ? '✏️ 编辑拼车' : '🚗 发布拼车' }}</span></template>
      <el-form ref="formRef" :model="form" :rules="rules" label-width="100px">
        <el-form-item label="标题" prop="title">
          <el-input v-model="form.title" maxlength="60" show-word-limit placeholder="例如：周末去泰山拼车" />
        </el-form-item>
        <el-form-item label="出发地" prop="from">
          <el-input v-model="form.from" maxlength="50" placeholder="例如：学校南门" />
        </el-form-item>
        <el-form-item label="目的地" prop="to">
          <el-input v-model="form.to" maxlength="50" placeholder="例如：泰山风景区" />
        </el-form-item>
        <el-form-item label="出发时间" prop="depart_time">
          <el-date-picker v-model="form.depart_time" type="datetime" placeholder="选择出发时间（需晚于当前时间）" style="width: 100%" value-format="YYYY-MM-DD HH:mm" />
        </el-form-item>
        <el-form-item label="返回时间">
          <el-date-picker v-model="form.return_time" type="datetime" placeholder="选择返回时间（可选）" style="width: 100%" value-format="YYYY-MM-DD HH:mm" />
        </el-form-item>
        <el-form-item label="座位数" prop="seats_total">
          <el-input-number v-model="form.seats_total" :min="1" :max="7" />
        </el-form-item>
        <el-form-item label="费用(元/人)">
          <el-input-number v-model="form.price_per_person" :min="0" :max="1000" />
        </el-form-item>
        <el-form-item label="联系电话" prop="phone">
          <el-input v-model="form.phone" maxlength="11" placeholder="请输入 11 位手机号码" />
        </el-form-item>
        <el-form-item label="备注">
          <el-input v-model="form.note" type="textarea" :rows="3" maxlength="500" placeholder="其他说明，如费用包含项目、行李要求等" />
        </el-form-item>
        <el-form-item>
          <el-button type="primary" :loading="submitting" @click="submit">{{ isEdit ? '保存修改' : '发布拼车' }}</el-button>
          <el-button @click="router.back()">取消</el-button>
        </el-form-item>
      </el-form>
    </el-card>
  </div>
</template>

<style scoped>
.page-container { max-width: 700px; margin: 0 auto; padding: 20px; }
.publish-card { border-radius: 12px; }
.card-title { font-size: 18px; font-weight: 600; color: #303133; }
</style>
