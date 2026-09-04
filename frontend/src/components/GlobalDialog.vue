<script setup>
// 全局弹窗组件（归属：前端 C）——配合 dialog store 使用
import { computed } from 'vue'
import { useDialogStore } from '@/stores/dialog'

const dialog = useDialogStore()

const iconMap = {
  success: '✅',
  warning: '⚠️',
  info: 'ℹ️',
  error: '❌'
}

const dialogIcon = computed(() => iconMap[dialog.type] || iconMap.info)
</script>

<template>
  <el-dialog
    :model-value="dialog.visible"
    :title="dialog.title"
    :width="dialog.width"
    :close-on-click-modal="false"
    @close="dialog.onCancel"
  >
    <div class="global-dialog-body">
      <span class="dialog-icon">{{ dialogIcon }}</span>
      <span class="dialog-content">{{ dialog.content }}</span>
    </div>
    <template #footer>
      <el-button v-if="dialog.showCancel" @click="dialog.onCancel">
        {{ dialog.cancelText }}
      </el-button>
      <el-button type="primary" @click="dialog.onConfirm">
        {{ dialog.confirmText }}
      </el-button>
    </template>
  </el-dialog>
</template>

<style scoped>
.global-dialog-body {
  display: flex;
  align-items: flex-start;
  gap: 12px;
  padding: 8px 0;
}

.dialog-icon {
  font-size: 24px;
  line-height: 1.4;
  flex-shrink: 0;
}

.dialog-content {
  font-size: 14px;
  line-height: 1.6;
  color: #606266;
  word-break: break-all;
}
</style>
