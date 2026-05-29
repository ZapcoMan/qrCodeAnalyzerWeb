<script setup lang="ts">
import { ref } from 'vue'

interface DecodeResult {
  success: boolean
  data?: {
    result: string
    type: string
  }
  error?: string
  code?: number
}

const API_BASE_URL = '/api'

const selectedFile = ref<File | null>(null)
const isLoading = ref(false)
const result = ref<DecodeResult | null>(null)
const uploadAreaRef = ref<HTMLElement | null>(null)
const fileInputRef = ref<HTMLInputElement | null>(null)
const isDragOver = ref(false)
const copied = ref(false)

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
    const response = await fetch(`${API_BASE_URL}/decode`, {
      method: 'POST',
      body: formData
    })

    const data: DecodeResult = await response.json()
    
    if (data.success && data.data) {
      result.value = {
        success: true,
        data: {
          result: data.data.result,
          type: data.data.type
        }
      }
    } else {
      result.value = {
        success: false,
        error: data.error || '解析失败'
      }
    }
  } catch (error) {
    result.value = {
      success: false,
      error: (error as Error).message
    }
  } finally {
    isLoading.value = false
  }
}

const reset = () => {
  selectedFile.value = null
  result.value = null
  copied.value = false
  if (fileInputRef.value) {
    fileInputRef.value.value = ''
  }
}

const copyToClipboard = async (text: string) => {
  try {
    await navigator.clipboard.writeText(text)
    copied.value = true
    setTimeout(() => {
      copied.value = false
    }, 2000)
  } catch (err) {
    console.error('复制失败:', err)
  }
}
</script>

<template>
  <div class="page-wrapper">
    <div class="background-decoration"></div>
    <div class="floating-blobs">
      <div class="blob blob-1"></div>
      <div class="blob blob-2"></div>
      <div class="blob blob-3"></div>
    </div>

    <div class="container">
      <header class="header">
        <div class="logo-icon">
          <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5">
            <rect x="3" y="3" width="7" height="7" rx="1.5"/>
            <rect x="14" y="3" width="7" height="7" rx="1.5"/>
            <rect x="3" y="14" width="7" height="7" rx="1.5"/>
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
                <svg v-if="result.success" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                  <path d="M20 6L9 17l-5-5"/>
                </svg>
                <svg v-else viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                  <path d="M18 6L6 18M6 6l12 12"/>
                </svg>
              </div>
              <h3>{{ result.success ? '解析成功' : '解析失败' }}</h3>
            </div>

            <div v-if="result.success && result.data" class="result-content">
              <div class="result-item">
                <span class="label">内容</span>
                <div class="value-wrapper">
                  <span class="value">{{ result.data.result }}</span>
                  <button class="copy-btn" @click="copyToClipboard(result.data.result)">
                    <svg v-if="!copied" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5">
                      <rect x="9" y="9" width="13" height="13" rx="2" ry="2"/>
                      <path d="M5 15H4a2 2 0 01-2-2V4a2 2 0 012-2h9a2 2 0 012 2v1"/>
                    </svg>
                    <svg v-else viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5">
                      <polyline points="20 6 9 17 4 12"/>
                    </svg>
                  </button>
                </div>
              </div>
              <div class="result-item">
                <span class="label">类型</span>
                <span class="badge">{{ result.data.type }}</span>
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
  width: 100%;
  height: 100%;
  min-height: 100vh;
  background: linear-gradient(135deg, #667eea 0%, #764ba2 50%, #f093fb 100%);
  position: relative;
  overflow: hidden;
}

.background-decoration {
  position: absolute;
  top: -50%;
  right: -20%;
  width: 80%;
  height: 150%;
  background: radial-gradient(circle, rgba(255,255,255,0.15) 0%, transparent 70%);
  pointer-events: none;
}

.floating-blobs {
  position: absolute;
  width: 100%;
  height: 100%;
  overflow: hidden;
  pointer-events: none;
}

.blob {
  position: absolute;
  border-radius: 50%;
  opacity: 0.15;
  filter: blur(60px);
  animation: float 20s infinite ease-in-out;
}

.blob-1 {
  width: 400px;
  height: 400px;
  background: rgba(255, 255, 255, 0.3);
  top: -200px;
  left: -100px;
  animation-delay: 0s;
}

.blob-2 {
  width: 300px;
  height: 300px;
  background: rgba(255, 182, 193, 0.4);
  bottom: -100px;
  right: -50px;
  animation-delay: -7s;
}

.blob-3 {
  width: 350px;
  height: 350px;
  background: rgba(176, 196, 222, 0.3);
  top: 30%;
  right: 10%;
  animation-delay: -14s;
}

@keyframes float {
  0%, 100% {
    transform: translate(0, 0) scale(1);
  }
  33% {
    transform: translate(50px, -30px) scale(1.1);
  }
  66% {
    transform: translate(-30px, 50px) scale(0.9);
  }
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
  width: 72px;
  height: 72px;
  margin: 0 auto 24px;
  background: rgba(255, 255, 255, 0.15);
  border-radius: 20px;
  display: flex;
  align-items: center;
  justify-content: center;
  backdrop-filter: blur(12px);
  border: 1px solid rgba(255, 255, 255, 0.2);
  box-shadow: 0 8px 32px rgba(0, 0, 0, 0.1);
  transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1);
}

.logo-icon:hover {
  transform: scale(1.05);
  box-shadow: 0 12px 40px rgba(0, 0, 0, 0.15);
}

.logo-icon svg {
  width: 40px;
  height: 40px;
  color: white;
  filter: drop-shadow(0 2px 4px rgba(0, 0, 0, 0.1));
}

.header h1 {
  font-size: 36px;
  font-weight: 700;
  color: white;
  margin: 0 0 12px;
  letter-spacing: -0.5px;
  text-shadow: 0 2px 10px rgba(0, 0, 0, 0.15);
}

.subtitle {
  font-size: 16px;
  color: rgba(255, 255, 255, 0.85);
  margin: 0;
  font-weight: 400;
}

.main-content {
  display: flex;
  flex-direction: column;
  gap: 24px;
}

.upload-area {
  background: rgba(255, 255, 255, 0.95);
  border-radius: 24px;
  padding: 48px 32px;
  cursor: pointer;
  transition: all 0.4s cubic-bezier(0.4, 0, 0.2, 1);
  box-shadow: 0 20px 60px rgba(0, 0, 0, 0.15);
  border: 2px solid rgba(255, 255, 255, 0.3);
  backdrop-filter: blur(10px);
}

.upload-area:hover {
  transform: translateY(-4px);
  box-shadow: 0 28px 80px rgba(0, 0, 0, 0.2);
}

.upload-area.drag-over {
  border-color: #667eea;
  background: linear-gradient(135deg, rgba(102, 126, 234, 0.08) 0%, rgba(118, 75, 162, 0.08) 100%);
  transform: scale(1.02);
  animation: pulse-border 2s infinite;
}

@keyframes pulse-border {
  0%, 100% {
    box-shadow: 0 0 0 0 rgba(102, 126, 234, 0.4);
  }
  50% {
    box-shadow: 0 0 0 8px rgba(102, 126, 234, 0);
  }
}

.upload-area.has-file {
  padding: 28px;
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
  width: 72px;
  height: 72px;
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
  border-radius: 20px;
  display: flex;
  align-items: center;
  justify-content: center;
  margin-bottom: 24px;
  box-shadow: 0 12px 32px rgba(102, 126, 234, 0.4);
  transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1);
}

.upload-area:hover .upload-icon {
  transform: scale(1.1);
  box-shadow: 0 16px 40px rgba(102, 126, 234, 0.5);
}

.upload-icon svg {
  width: 36px;
  height: 36px;
  color: white;
}

.upload-text {
  font-size: 18px;
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
  width: 52px;
  height: 52px;
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
  border-radius: 14px;
  display: flex;
  align-items: center;
  justify-content: center;
  flex-shrink: 0;
  box-shadow: 0 8px 20px rgba(102, 126, 234, 0.3);
}

.file-icon svg {
  width: 26px;
  height: 26px;
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
  width: 38px;
  height: 38px;
  border: none;
  background: #f0f0f0;
  border-radius: 12px;
  cursor: pointer;
  display: flex;
  align-items: center;
  justify-content: center;
  transition: all 0.25s cubic-bezier(0.4, 0, 0.2, 1);
  flex-shrink: 0;
}

.remove-btn:hover {
  background: #ffe5e5;
  transform: scale(1.1);
}

.remove-btn svg {
  width: 18px;
  height: 18px;
  color: #e53e3e;
}

.decode-btn {
  width: 100%;
  padding: 18px 32px;
  font-size: 16px;
  font-weight: 600;
  color: white;
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
  border: none;
  border-radius: 16px;
  cursor: pointer;
  transition: all 0.4s cubic-bezier(0.4, 0, 0.2, 1);
  box-shadow: 0 12px 32px rgba(102, 126, 234, 0.4);
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 10px;
  position: relative;
  overflow: hidden;
}

.decode-btn::before {
  content: '';
  position: absolute;
  top: 0;
  left: -100%;
  width: 100%;
  height: 100%;
  background: linear-gradient(90deg, transparent, rgba(255, 255, 255, 0.2), transparent);
  transition: left 0.5s;
}

.decode-btn:hover::before {
  left: 100%;
}

.decode-btn:hover:not(:disabled) {
  transform: translateY(-3px);
  box-shadow: 0 18px 40px rgba(102, 126, 234, 0.5);
}

.decode-btn:active:not(:disabled) {
  transform: translateY(-1px);
}

.decode-btn:disabled {
  background: linear-gradient(135deg, #d0d0d0 0%, #b8b8b8 100%);
  box-shadow: none;
  cursor: not-allowed;
}

.loading-spinner {
  width: 20px;
  height: 20px;
  border: 2px solid rgba(255, 255, 255, 0.3);
  border-top-color: white;
  border-radius: 50%;
  animation: spin 0.8s linear infinite;
}

@keyframes spin {
  to { transform: rotate(360deg); }
}

.result-card {
  background: rgba(255, 255, 255, 0.95);
  border-radius: 24px;
  padding: 28px;
  box-shadow: 0 16px 50px rgba(0, 0, 0, 0.12);
  border: 1px solid rgba(255, 255, 255, 0.5);
  backdrop-filter: blur(10px);
}

.result-card.error {
  background: linear-gradient(135deg, #fff5f5 0%, #ffffff 100%);
  border-color: #fed7d7;
}

.result-header {
  display: flex;
  align-items: center;
  gap: 14px;
  margin-bottom: 22px;
}

.status-icon {
  width: 44px;
  height: 44px;
  border-radius: 14px;
  display: flex;
  align-items: center;
  justify-content: center;
  box-shadow: 0 8px 20px rgba(0, 0, 0, 0.15);
  transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1);
}

.status-icon.success {
  background: linear-gradient(135deg, #48bb78 0%, #38a169 100%);
}

.status-icon.error {
  background: linear-gradient(135deg, #f56565 0%, #e53e3e 100%);
}

.status-icon svg {
  width: 22px;
  height: 22px;
  color: white;
}

.result-header h3 {
  font-size: 20px;
  font-weight: 600;
  color: #1a1a2e;
  margin: 0;
}

.result-content {
  display: flex;
  flex-direction: column;
  gap: 18px;
}

.result-item {
  display: flex;
  flex-direction: column;
  gap: 8px;
}

.result-item .label {
  font-size: 13px;
  font-weight: 500;
  color: #888;
  text-transform: uppercase;
  letter-spacing: 0.5px;
}

.value-wrapper {
  display: flex;
  align-items: center;
  gap: 10px;
  background: #f8f9fa;
  border-radius: 12px;
  padding: 14px 16px;
  flex-wrap: wrap;
}

.result-item .value {
  font-size: 15px;
  color: #1a1a2e;
  word-break: break-all;
  flex: 1;
  min-width: 0;
  line-height: 1.6;
}

.copy-btn {
  width: 36px;
  height: 36px;
  border: none;
  background: #e9ecef;
  border-radius: 10px;
  cursor: pointer;
  display: flex;
  align-items: center;
  justify-content: center;
  transition: all 0.25s cubic-bezier(0.4, 0, 0.2, 1);
  flex-shrink: 0;
}

.copy-btn:hover {
  background: #667eea;
}

.copy-btn svg {
  width: 18px;
  height: 18px;
  color: #666;
  transition: color 0.25s;
}

.copy-btn:hover svg {
  color: white;
}

.badge {
  display: inline-flex;
  align-items: center;
  padding: 8px 16px;
  font-size: 14px;
  font-weight: 600;
  color: #667eea;
  background: rgba(102, 126, 234, 0.1);
  border-radius: 10px;
  width: fit-content;
  box-shadow: 0 2px 8px rgba(102, 126, 234, 0.15);
}

.error-content p {
  font-size: 15px;
  color: #e53e3e;
  margin: 0;
  line-height: 1.6;
}

.footer {
  text-align: center;
  margin-top: 48px;
}

.footer p {
  font-size: 14px;
  color: rgba(255, 255, 255, 0.75);
  margin: 0;
}

.fade-slide-enter-active {
  transition: all 0.5s cubic-bezier(0.4, 0, 0.2, 1);
}

.fade-slide-leave-active {
  transition: all 0.35s cubic-bezier(0.4, 0, 0.2, 1);
}

.fade-slide-enter-from {
  opacity: 0;
  transform: translateY(24px) scale(0.95);
}

.fade-slide-leave-to {
  opacity: 0;
  transform: translateY(-12px) scale(0.98);
}
</style>