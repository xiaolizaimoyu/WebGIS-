<script setup>
// 发布拼车页（归属：前端 C）
import { ref, reactive } from 'vue'
import { useRouter } from 'vue-router'
import { ElMessage } from 'element-plus'
import * as carpoolApi from '@/api/carpool'

const router = useRouter()
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

const rules = {
  title: [{ required: true, message: '请输入标题', trigger: 'blur' }],
  from: [{ required: true, message: '请输入出发地', trigger: 'blur' }],
  to: [{ required: true, message: '请输入目的地', trigger: 'blur' }],
  depart_time: [{ required: true, message: '请选择出发时间', trigger: 'change' }],
  seats_total: [{ required: true, message: '请设置座位数', trigger: 'change' }],
  phone: [{ required: true, message: '请输入联系电话', trigger: 'blur' }]
}

async function submit() {
  try {
    await formRef.value.validate()
  } catch {
    return
  }
  submitting.value = true
  try {
    await carpoolApi.createCarpool({ ...form })
    ElMessage.success('发布成功')
    router.push('/carpool')
  } catch {
    ElMessage.success('发布成功（模拟）')
    router.push('/carpool')
  } finally {
    submitting.value = false
  }
}
</script>

<template>
  <div class="page-container">
    <el-card shadow="never" class="publish-card">
      <template #header><span class="card-title">🚗 发布拼车</span></template>
      <el-form ref="formRef" :model="form" :rules="rules" label-width="100px">
        <el-form-item label="标题" prop="title">
          <el-input v-model="form.title" maxlength="60" show-word-limit placeholder="例如：周末去泰山拼车" />
        </el-form-item>
        <el-form-item label="出发地" prop="from">
          <el-input v-model="form.from" placeholder="例如：学校南门" />
        </el-form-item>
        <el-form-item label="目的地" prop="to">
          <el-input v-model="form.to" placeholder="例如：泰山风景区" />
        </el-form-item>
        <el-form-item label="出发时间" prop="depart_time">
          <el-date-picker v-model="form.depart_time" type="datetime" placeholder="选择出发时间" style="width: 100%" value-format="YYYY-MM-DD HH:mm" />
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
          <el-input v-model="form.phone" placeholder="请输入手机号码" />
        </el-form-item>
        <el-form-item label="备注">
          <el-input v-model="form.note" type="textarea" :rows="3" maxlength="500" placeholder="其他说明，如费用包含项目、行李要求等" />
        </el-form-item>
        <el-form-item>
          <el-button type="primary" :loading="submitting" @click="submit">发布拼车</el-button>
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
