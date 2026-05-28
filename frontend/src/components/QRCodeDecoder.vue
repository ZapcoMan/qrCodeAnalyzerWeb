<script setup lang="ts">
import { ref } from 'vue'

interface DecodeResult {
  success: boolean
  result: string
  type: string
  error?: string
}

const selectedFile = ref<File | null>(null)
const isLoading = ref(false)
const result = ref<DecodeResult | null>(null)
const uploadAreaRef = ref<HTMLElement | null>(null)
const fileInputRef = ref<HTMLInputElement | null>(null)
const isDragOver = ref(false)

const handleFileSelect = (event: Event) => {
  const target = event.target as HTMLInputElement
  const file = target.files?.[0]
  if (file) {
    selectedFile.value = file
    result.value = null
  }
}

const handleDragOver = (event: DragEvent) => {
  event.preventDefault()
  isDragOver.value = true
}

const handleDragLeave = (event: DragEvent) => {
  event.preventDefault()
  isDragOver.value = false
}

const handleDrop = (event: DragEvent) => {
  event.preventDefault()
  isDragOver.value = false
  const file = event.dataTransfer?.files[0]
  if (file && file.type.startsWith('image/')) {
    selectedFile.value = file
    result.value = null
  }
}

const openFileDialog = () => {
  fileInputRef.value?.click()
}

const decodeQRCode = async () => {
  if (!selectedFile.value) {
    alert('请选择一张图片')
    return
  }

  const formData = new FormData()
  formData.append('file', selectedFile.value)

  isLoading.value = true
  result.value = null

  try {
    const response = await fetch('/api/decode', {
      method: 'POST',
      body: formData
    })

    const data: DecodeResult = await response.json()
    result.value = data
  } catch (error) {
    result.value = {
      success: false,
      result: '',
      type: '',
      error: (error as Error).message
    }
  } finally {
    isLoading.value = false
  }
}

const reset = () => {
  selectedFile.value = null
  result.value = null
  if (fileInputRef.value) {
    fileInputRef.value.value = ''
  }
}
</script>

<template>
  <div class="page-wrapper">
    <div class="background-decoration"></div>

    <div class="container">
      <header class="header">
        <div class="logo-icon">
          <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
            <rect x="3" y="3" width="7" height="7" rx="1"/>
            <rect x="14" y="3" width="7" height="7" rx="1"/>
            <rect x="3" y="14" width="7" height="7" rx="1"/>
            <rect x="14" y="14" width="3" height="3" rx="0.5"/>
            <rect x="18" y="14" width="3" height="3" rx="0.5"/>
            <rect x="14" y="18" width="3" height="3" rx="0.5"/>
            <rect x="18" y="18" width="3" height="3" rx="0.5"/>
          </svg>
        </div>
        <h1>二维码解析器</h1>
        <p class="subtitle">上传图片或拖拽文件即可快速解析二维码内容</p>
      </header>

      <main class="main-content">
        <div
          ref="uploadAreaRef"
          :class="['upload-area', { 'drag-over': isDragOver, 'has-file': selectedFile }]"
          @click="openFileDialog"
          @dragover="handleDragOver"
          @dragleave="handleDragLeave"
          @drop="handleDrop"
        >
          <input
            ref="fileInputRef"
            type="file"
            id="fileInput"
            accept="image/*"
            class="file-input"
            @change="handleFileSelect"
          />

          <div v-if="!selectedFile" class="upload-placeholder">
            <div class="upload-icon">
              <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5">
                <path d="M12 16V4m0 0l-4 4m4-4l4 4"/>
                <path d="M3 15v4a2 2 0 002 2h14a2 2 0 002-2v-4"/>
              </svg>
            </div>
            <p class="upload-text">点击上传或拖拽图片到此处</p>
            <p class="upload-hint">支持 PNG、JPG、GIF、WebP 格式</p>
          </div>

          <div v-else class="file-preview">
            <div class="file-icon">
              <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5">
                <rect x="3" y="3" width="18" height="18" rx="2"/>
                <circle cx="8.5" cy="8.5" r="1.5"/>
                <path d="M21 15l-5-5L5 21"/>
              </svg>
            </div>
            <div class="file-info">
              <p class="file-name">{{ selectedFile.name }}</p>
              <p class="file-size">{{ (selectedFile.size / 1024).toFixed(1) }} KB</p>
            </div>
            <button class="remove-btn" @click.stop="reset">
              <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                <path d="M18 6L6 18M6 6l12 12"/>
              </svg>
            </button>
          </div>
        </div>

        <button
          class="decode-btn"
          @click="decodeQRCode"
          :disabled="isLoading || !selectedFile"
        >
          <span v-if="isLoading" class="loading-spinner"></span>
          <span v-else>{{ isLoading ? '解析中...' : '解析二维码' }}</span>
        </button>

        <Transition name="fade-slide">
          <div v-if="result" :class="['result-card', { error: !result.success }]">
            <div class="result-header">
              <div :class="['status-icon', { success: result.success, error: !result.success }]">
                <svg v-if="result.success" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5">
                  <path d="M20 6L9 17l-5-5"/>
                </svg>
                <svg v-else viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5">
                  <path d="M18 6L6 18M6 6l12 12"/>
                </svg>
              </div>
              <h3>{{ result.success ? '解析成功' : '解析失败' }}</h3>
            </div>

            <div v-if="result.success" class="result-content">
              <div class="result-item">
                <span class="label">内容</span>
                <span class="value">{{ result.result }}</span>
              </div>
              <div class="result-item">
                <span class="label">类型</span>
                <span class="badge">{{ result.type }}</span>
              </div>
            </div>

            <div v-else class="error-content">
              <p>{{ result.error }}</p>
            </div>
          </div>
        </Transition>
      </main>

      <footer class="footer">
        <p>支持多种二维码格式 · 高识别率 · 安全便捷</p>
      </footer>
    </div>
  </div>
</template>

<style scoped>
.page-wrapper {
  min-height: 100vh;
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
  position: relative;
  overflow: hidden;
}

.background-decoration {
  position: absolute;
  top: -50%;
  right: -20%;
  width: 80%;
  height: 150%;
  background: radial-gradient(circle, rgba(255,255,255,0.1) 0%, transparent 70%);
  pointer-events: none;
}

.container {
  max-width: 520px;
  margin: 0 auto;
  padding: 60px 24px;
  position: relative;
  z-index: 1;
}

.header {
  text-align: center;
  margin-bottom: 40px;
}

.logo-icon {
  width: 64px;
  height: 64px;
  margin: 0 auto 20px;
  background: rgba(255,255,255,0.2);
  border-radius: 16px;
  display: flex;
  align-items: center;
  justify-content: center;
  backdrop-filter: blur(10px);
}

.logo-icon svg {
  width: 36px;
  height: 36px;
  color: white;
}

.header h1 {
  font-size: 32px;
  font-weight: 700;
  color: white;
  margin: 0 0 12px;
  letter-spacing: -0.5px;
}

.subtitle {
  font-size: 16px;
  color: rgba(255,255,255,0.8);
  margin: 0;
}

.main-content {
  display: flex;
  flex-direction: column;
  gap: 20px;
}

.upload-area {
  background: white;
  border-radius: 20px;
  padding: 40px 30px;
  cursor: pointer;
  transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1);
  box-shadow: 0 10px 40px rgba(0,0,0,0.15);
}

.upload-area:hover {
  transform: translateY(-2px);
  box-shadow: 0 15px 50px rgba(0,0,0,0.2);
}

.upload-area.drag-over {
  border: 2px dashed #667eea;
  background: linear-gradient(135deg, rgba(102,126,234,0.05) 0%, rgba(118,75,162,0.05) 100%);
  transform: scale(1.02);
}

.upload-area.has-file {
  padding: 30px;
}

.file-input {
  display: none;
}

.upload-placeholder {
  display: flex;
  flex-direction: column;
  align-items: center;
  text-align: center;
}

.upload-icon {
  width: 64px;
  height: 64px;
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
  border-radius: 16px;
  display: flex;
  align-items: center;
  justify-content: center;
  margin-bottom: 20px;
}

.upload-icon svg {
  width: 32px;
  height: 32px;
  color: white;
}

.upload-text {
  font-size: 16px;
  font-weight: 600;
  color: #1a1a2e;
  margin: 0 0 8px;
}

.upload-hint {
  font-size: 14px;
  color: #666;
  margin: 0;
}

.file-preview {
  display: flex;
  align-items: center;
  gap: 16px;
}

.file-icon {
  width: 48px;
  height: 48px;
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
  border-radius: 12px;
  display: flex;
  align-items: center;
  justify-content: center;
  flex-shrink: 0;
}

.file-icon svg {
  width: 24px;
  height: 24px;
  color: white;
}

.file-info {
  flex: 1;
  min-width: 0;
}

.file-name {
  font-size: 15px;
  font-weight: 600;
  color: #1a1a2e;
  margin: 0 0 4px;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.file-size {
  font-size: 13px;
  color: #888;
  margin: 0;
}

.remove-btn {
  width: 36px;
  height: 36px;
  border: none;
  background: #f5f5f5;
  border-radius: 10px;
  cursor: pointer;
  display: flex;
  align-items: center;
  justify-content: center;
  transition: all 0.2s;
  flex-shrink: 0;
}

.remove-btn:hover {
  background: #fee;
}

.remove-btn svg {
  width: 18px;
  height: 18px;
  color: #666;
}

.decode-btn {
  width: 100%;
  padding: 16px 32px;
  font-size: 16px;
  font-weight: 600;
  color: white;
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
  border: none;
  border-radius: 14px;
  cursor: pointer;
  transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1);
  box-shadow: 0 8px 24px rgba(102,126,234,0.4);
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 10px;
}

.decode-btn:hover:not(:disabled) {
  transform: translateY(-2px);
  box-shadow: 0 12px 32px rgba(102,126,234,0.5);
}

.decode-btn:active:not(:disabled) {
  transform: translateY(0);
}

.decode-btn:disabled {
  background: #ccc;
  box-shadow: none;
  cursor: not-allowed;
}

.loading-spinner {
  width: 20px;
  height: 20px;
  border: 2px solid rgba(255,255,255,0.3);
  border-top-color: white;
  border-radius: 50%;
  animation: spin 0.8s linear infinite;
}

@keyframes spin {
  to { transform: rotate(360deg); }
}

.result-card {
  background: white;
  border-radius: 20px;
  padding: 24px;
  box-shadow: 0 10px 40px rgba(0,0,0,0.15);
}

.result-card.error {
  background: linear-gradient(135deg, #fff5f5 0%, #fff 100%);
  border: 1px solid #fed7d7;
}

.result-header {
  display: flex;
  align-items: center;
  gap: 12px;
  margin-bottom: 20px;
}

.status-icon {
  width: 40px;
  height: 40px;
  border-radius: 12px;
  display: flex;
  align-items: center;
  justify-content: center;
}

.status-icon.success {
  background: linear-gradient(135deg, #48bb78 0%, #38a169 100%);
}

.status-icon.error {
  background: linear-gradient(135deg, #f56565 0%, #e53e3e 100%);
}

.status-icon svg {
  width: 20px;
  height: 20px;
  color: white;
}

.result-header h3 {
  font-size: 18px;
  font-weight: 600;
  color: #1a1a2e;
  margin: 0;
}

.result-content {
  display: flex;
  flex-direction: column;
  gap: 16px;
}

.result-item {
  display: flex;
  flex-direction: column;
  gap: 6px;
}

.result-item .label {
  font-size: 13px;
  font-weight: 500;
  color: #888;
  text-transform: uppercase;
  letter-spacing: 0.5px;
}

.result-item .value {
  font-size: 16px;
  color: #1a1a2e;
  word-break: break-all;
  padding: 12px 16px;
  background: #f8f9fa;
  border-radius: 10px;
}

.badge {
  display: inline-block;
  padding: 6px 14px;
  font-size: 14px;
  font-weight: 600;
  color: #667eea;
  background: rgba(102,126,234,0.1);
  border-radius: 8px;
  width: fit-content;
}

.error-content p {
  font-size: 15px;
  color: #e53e3e;
  margin: 0;
  line-height: 1.6;
}

.footer {
  text-align: center;
  margin-top: 40px;
}

.footer p {
  font-size: 14px;
  color: rgba(255,255,255,0.7);
  margin: 0;
}

.fade-slide-enter-active {
  transition: all 0.4s cubic-bezier(0.4, 0, 0.2, 1);
}

.fade-slide-leave-active {
  transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1);
}

.fade-slide-enter-from {
  opacity: 0;
  transform: translateY(20px);
}

.fade-slide-leave-to {
  opacity: 0;
  transform: translateY(-10px);
}
</style>
