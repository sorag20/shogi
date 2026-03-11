<template>
  <div class="login-form-overlay" @click="$emit('close')">
    <div class="login-form-container" @click.stop>
      <button class="close-btn" @click="$emit('close')">&times;</button>

      <h2>{{ isRegister ? 'アカウント登録' : 'ログイン' }}</h2>

      <form @submit.prevent="handleSubmit">
        <div v-if="error" class="error-message">
          {{ error }}
        </div>

        <div class="form-group">
          <label for="username">ユーザー名</label>
          <input
            id="username"
            v-model="formData.username"
            type="text"
            required
            :disabled="loading"
            placeholder="ユーザー名を入力"
          />
        </div>

        <div v-if="isRegister" class="form-group">
          <label for="email">メールアドレス</label>
          <input
            id="email"
            v-model="formData.email"
            type="email"
            required
            :disabled="loading"
            placeholder="メールアドレスを入力"
          />
        </div>

        <div class="form-group">
          <label for="password">パスワード</label>
          <input
            id="password"
            v-model="formData.password"
            type="password"
            required
            :disabled="loading"
            :placeholder="isRegister ? '6文字以上' : 'パスワードを入力'"
          />
        </div>

        <button type="submit" class="submit-btn" :disabled="loading">
          {{ loading ? '処理中...' : (isRegister ? '登録' : 'ログイン') }}
        </button>
      </form>

      <div class="toggle-mode">
        <button @click="toggleMode" :disabled="loading">
          {{ isRegister ? 'ログインはこちら' : '新規登録はこちら' }}
        </button>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, reactive } from 'vue'

const emit = defineEmits(['close', 'success'])

const isRegister = ref(false)
const loading = ref(false)
const error = ref<string | null>(null)

const formData = reactive({
  username: '',
  email: '',
  password: '',
})

const toggleMode = () => {
  isRegister.value = !isRegister.value
  error.value = null
}

const handleSubmit = async () => {
  error.value = null
  loading.value = true

  try {
    const endpoint = isRegister.value ? '/api/auth/register' : '/api/auth/login'
    const payload = isRegister.value
      ? formData
      : { username: formData.username, password: formData.password }

    const response = await fetch(`http://localhost:5001${endpoint}`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      credentials: 'include',
      body: JSON.stringify(payload),
    })

    const data = await response.json()

    if (!response.ok) {
      throw new Error(data.message || 'エラーが発生しました')
    }

    emit('success', data.user)
    emit('close')
  } catch (err: any) {
    error.value = err.message || 'エラーが発生しました'
  } finally {
    loading.value = false
  }
}
</script>

<style scoped>
.login-form-overlay {
  position: fixed;
  top: 0;
  left: 0;
  right: 0;
  bottom: 0;
  background-color: rgba(0, 0, 0, 0.5);
  display: flex;
  align-items: center;
  justify-content: center;
  z-index: 2000;
}

.login-form-container {
  background: white;
  border-radius: 8px;
  padding: 30px;
  max-width: 400px;
  width: 90%;
  position: relative;
  box-shadow: 0 4px 12px rgba(0, 0, 0, 0.15);
}

.close-btn {
  position: absolute;
  top: 10px;
  right: 10px;
  background: none;
  border: none;
  font-size: 28px;
  cursor: pointer;
  color: #999;
  line-height: 1;
  padding: 5px 10px;
}

.close-btn:hover {
  color: #333;
}

h2 {
  margin: 0 0 20px 0;
  color: #2c3e50;
  font-size: 24px;
  text-align: center;
}

.error-message {
  background-color: #ffebee;
  color: #c62828;
  padding: 10px;
  border-radius: 4px;
  margin-bottom: 15px;
  font-size: 14px;
}

.form-group {
  margin-bottom: 20px;
}

.form-group label {
  display: block;
  margin-bottom: 5px;
  font-weight: bold;
  color: #333;
  font-size: 14px;
}

.form-group input {
  width: 100%;
  padding: 10px;
  border: 1px solid #ddd;
  border-radius: 4px;
  font-size: 14px;
  box-sizing: border-box;
}

.form-group input:focus {
  outline: none;
  border-color: #3498db;
}

.form-group input:disabled {
  background-color: #f5f5f5;
  cursor: not-allowed;
}

.submit-btn {
  width: 100%;
  padding: 12px;
  background-color: #3498db;
  color: white;
  border: none;
  border-radius: 4px;
  font-size: 16px;
  font-weight: bold;
  cursor: pointer;
  transition: background-color 0.3s;
}

.submit-btn:hover:not(:disabled) {
  background-color: #2980b9;
}

.submit-btn:disabled {
  background-color: #95a5a6;
  cursor: not-allowed;
}

.toggle-mode {
  margin-top: 20px;
  text-align: center;
}

.toggle-mode button {
  background: none;
  border: none;
  color: #3498db;
  cursor: pointer;
  font-size: 14px;
  text-decoration: underline;
}

.toggle-mode button:hover:not(:disabled) {
  color: #2980b9;
}

.toggle-mode button:disabled {
  color: #95a5a6;
  cursor: not-allowed;
}
</style>
