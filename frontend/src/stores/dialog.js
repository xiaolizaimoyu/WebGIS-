// 全局弹窗状态管理（归属：前端 C）
// 使用方式：
//   import { useDialogStore } from '@/stores/dialog'
//   const dialog = useDialogStore()
//   dialog.open({ title: '提示', content: '操作成功', type: 'success' })
//   dialog.confirm({ title: '确认', content: '确定删除？', onConfirm: () => {...} })
import { defineStore } from 'pinia'
import { ref } from 'vue'

export const useDialogStore = defineStore('globalDialog', () => {
  const visible = ref(false)
  const title = ref('提示')
  const content = ref('')
  const type = ref('info') // success / warning / info / error
  const showCancel = ref(false)
  const confirmText = ref('确定')
  const cancelText = ref('取消')
  const width = ref('420px')
  let onConfirmCb = null
  let onCancelCb = null

  function open(options = {}) {
    title.value = options.title || '提示'
    content.value = options.content || ''
    type.value = options.type || 'info'
    showCancel.value = options.showCancel ?? false
    confirmText.value = options.confirmText || '确定'
    cancelText.value = options.cancelText || '取消'
    width.value = options.width || '420px'
    onConfirmCb = options.onConfirm || null
    onCancelCb = options.onCancel || null
    visible.value = true
  }

  function confirm(options = {}) {
    open({ ...options, showCancel: true })
  }

  function close() {
    visible.value = false
    onConfirmCb = null
    onCancelCb = null
  }

  function onConfirm() {
    if (onConfirmCb) onConfirmCb()
    close()
  }

  function onCancel() {
    if (onCancelCb) onCancelCb()
    close()
  }

  return {
    visible,
    title,
    content,
    type,
    showCancel,
    confirmText,
    cancelText,
    width,
    open,
    confirm,
    close,
    onConfirm,
    onCancel
  }
})
