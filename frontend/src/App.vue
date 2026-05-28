<script setup lang="ts">
import QRCodeDecoder from './components/QRCodeDecoder.vue'
</script>

<template>
  <div class="app">
    <QRCodeDecoder />
  </div>
</template>

<style scoped>
.app {
  min-height: 100vh;
  padding: 40px 20px;
}
</style>
