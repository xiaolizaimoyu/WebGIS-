<script setup>
// 根组件（归属：前端 C）——挂载路由出口 + 全局弹窗
import GlobalDialog from '@/components/GlobalDialog.vue'
</script>

<template>
  <router-view />
  <GlobalDialog />
</template>
