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

const handleFileSelect = (event: Event) => {
  const target = event.target as HTMLInputElement
  const file = target.files?.[0]
  if (file) {
    selectedFile.value = file
  }
}

const handleDragOver = (event: DragEvent) => {
  event.preventDefault()
  if (uploadAreaRef.value) {
    uploadAreaRef.value.style.borderColor = '#666'
  }
}

const handleDragLeave = (event: DragEvent) => {
  event.preventDefault()
  if (uploadAreaRef.value) {
    uploadAreaRef.value.style.borderColor = '#ccc'
  }
}

const handleDrop = (event: DragEvent) => {
  event.preventDefault()
  if (uploadAreaRef.value) {
    uploadAreaRef.value.style.borderColor = '#ccc'
  }
  const file = event.dataTransfer?.files[0]
  if (file && file.type.startsWith('image/')) {
    selectedFile.value = file
  }
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
</script>

<template>
  <div class="container">
    <h1>二维码解析器</h1>
    
    <div 
      ref="uploadAreaRef"
      class="upload-area" 
      @click="() => (document.getElementById('fileInput') as HTMLInputElement)?.click()"
      @dragover="handleDragOver"
      @dragleave="handleDragLeave"
      @drop="handleDrop"
    >
      <input 
        type="file" 
        id="fileInput" 
        accept="image/*" 
        class="file-input"
        @change="handleFileSelect"
      />
      <p v-if="!selectedFile">点击选择图片或拖拽图片到此处</p>
      <p v-else>已选择: {{ selectedFile.name }}</p>
    </div>

    <button @click="decodeQRCode" :disabled="isLoading || !selectedFile">
      {{ isLoading ? '解析中...' : '解析二维码' }}
    </button>

    <div v-if="isLoading" class="loading">解析中...</div>

    <div v-if="result" :class="['result', { error: !result.success }]">
      <h3>{{ result.success ? '解析结果' : '解析失败' }}</h3>
      <p v-if="result.success">
        <strong>内容:</strong> {{ result.result }}
      </p>
      <p v-if="result.success">
        <strong>类型:</strong> {{ result.type }}
      </p>
      <p v-if="result.error">{{ result.error }}</p>
    </div>
  </div>
</template>

<style scoped>
.container {
  max-width: 600px;
  margin: 0 auto;
  background: white;
  padding: 30px;
  border-radius: 8px;
  box-shadow: 0 2px 10px rgba(0, 0, 0, 0.1);
}

h1 {
  color: #333;
  text-align: center;
  margin-bottom: 20px;
}

.upload-area {
  border: 2px dashed #ccc;
  padding: 20px;
  text-align: center;
  border-radius: 5px;
  margin: 20px 0;
  cursor: pointer;
  transition: border-color 0.3s;
}

.upload-area:hover {
  border-color: #666;
}

.file-input {
  display: none;
}

button {
  background-color: #4CAF50;
  color: white;
  padding: 10px 20px;
  border: none;
  border-radius: 4px;
  cursor: pointer;
  font-size: 16px;
  width: 100%;
  transition: background-color 0.3s;
}

button:hover:not(:disabled) {
  background-color: #45a049;
}

button:disabled {
  background-color: #cccccc;
  cursor: not-allowed;
}

.loading {
  text-align: center;
  margin: 20px 0;
  color: #666;
}

.result {
  margin-top: 20px;
  padding: 15px;
  background-color: #e7f3ff;
  border-left: 6px solid #2196F3;
}

.result.error {
  background-color: #ffebee;
  border-left-color: #f44336;
}

.result h3 {
  margin-bottom: 10px;
  color: #333;
}

.result p {
  margin: 5px 0;
  color: #666;
}
</style>
