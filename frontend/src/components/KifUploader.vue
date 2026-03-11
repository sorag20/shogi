<template>
  <div class="kif-uploader">
    <div class="upload-area" @dragover.prevent @drop.prevent="onDrop">
      <input
        ref="fileInput"
        type="file"
        accept=".kif,.kifu"
        @change="onFileSelected"
        style="display: none"
      />
      <button @click="selectFile" class="btn btn-primary">
        ファイルを選択
      </button>
      <p class="upload-hint">またはファイルをドラッグ&ドロップ</p>
      <p v-if="selectedFileName" class="selected-file">
        選択ファイル: {{ selectedFileName }}
      </p>
    </div>

    <div v-if="isLoading" class="loading">
      <LoadingSpinner :is-loading="true" message="ファイルをアップロード中..." />
    </div>

    <div v-if="error" class="error">
      <ErrorMessage :error="error" @dismiss="error = null" />
    </div>

    <button
      v-if="selectedFileName && !isLoading"
      @click="uploadFile"
      class="btn btn-primary"
      :disabled="!selectedFile"
    >
      アップロード
    </button>
  </div>
</template>

<script setup lang="ts">
import { ref } from 'vue'
import { kifuApi } from '../api'
import { LoadingSpinner, ErrorMessage } from './index'

interface Emits {
  (e: 'file-uploaded', data: any): void
}

const emit = defineEmits<Emits>()

const fileInput = ref<HTMLInputElement | null>(null)
const selectedFile = ref<File | null>(null)
const selectedFileName = ref<string>('')
const isLoading = ref(false)
const error = ref<string | null>(null)

const selectFile = () => {
  fileInput.value?.click()
}

const onFileSelected = (event: Event) => {
  const target = event.target as HTMLInputElement
  const files = target.files
  if (files && files.length > 0) {
    selectedFile.value = files[0]
    selectedFileName.value = files[0].name
  }
}

const onDrop = (event: DragEvent) => {
  const files = event.dataTransfer?.files
  if (files && files.length > 0) {
    selectedFile.value = files[0]
    selectedFileName.value = files[0].name
  }
}

const uploadFile = async () => {
  if (!selectedFile.value) return

  isLoading.value = true
  error.value = null

  try {
    const result = await kifuApi.upload(selectedFile.value)
    emit('file-uploaded', result)
    selectedFile.value = null
    selectedFileName.value = ''
  } catch (err) {
    error.value = err instanceof Error ? err.message : 'ファイルのアップロードに失敗しました'
  } finally {
    isLoading.value = false
  }
}
</script>

<style scoped>
.kif-uploader {
  display: flex;
  flex-direction: column;
  gap: 15px;
  padding: 20px;
  background-color: white;
  border-radius: 4px;
  box-shadow: 0 1px 3px rgba(0, 0, 0, 0.1);
}

.upload-area {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  padding: 30px;
  border: 2px dashed #3498db;
  border-radius: 4px;
  background-color: #f9f9f9;
  cursor: pointer;
  transition: all 0.3s;
}

.upload-area:hover {
  background-color: #f0f8ff;
  border-color: #2980b9;
}

.upload-hint {
  margin: 10px 0 0 0;
  color: #666;
  font-size: 13px;
}

.selected-file {
  margin: 10px 0 0 0;
  color: #27ae60;
  font-size: 13px;
  font-weight: bold;
}

.loading {
  padding: 20px;
}

.error {
  padding: 10px 0;
}

.btn {
  padding: 10px 20px;
  background-color: #3498db;
  color: white;
  border: none;
  border-radius: 4px;
  cursor: pointer;
  font-size: 14px;
  transition: background-color 0.3s;
}

.btn:hover:not(:disabled) {
  background-color: #2980b9;
}

.btn:disabled {
  background-color: #bdc3c7;
  cursor: not-allowed;
}

.btn-primary {
  background-color: #27ae60;
}

.btn-primary:hover:not(:disabled) {
  background-color: #229954;
}
</style>
