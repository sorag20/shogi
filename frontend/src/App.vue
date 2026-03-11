<template>
  <div id="app" class="app-container">
    <header class="app-header">
      <div class="header-content">
        <nav class="app-nav">
          <button
            :class="{ active: currentMode === 'free' }"
            @click="switchMode('free')"
            class="nav-btn"
          >
            自由配置モード
          </button>
          <button
            :class="{ active: currentMode === 'replay' }"
            @click="switchMode('replay')"
            class="nav-btn"
          >
            棋譜再生モード
          </button>
        </nav>
        <div class="auth-section">
          <template v-if="currentUser">
            <span class="username">{{ currentUser.username }}</span>
            <button @click="handleLogout" class="auth-btn">ログアウト</button>
          </template>
          <template v-else>
            <button @click="showLoginForm = true" class="auth-btn">ログイン</button>
          </template>
        </div>
      </div>
    </header>

    <LoginForm
      v-if="showLoginForm"
      @close="showLoginForm = false"
      @success="onLoginSuccess"
    />

    <main class="app-main">
      <ErrorMessage
        v-if="error"
        :error="error"
        @dismiss="error = null"
      />

      <LoadingSpinner
        :is-loading="isLoading"
        message="読み込み中..."
      />

      <div v-if="!isLoading" class="content">
        <!-- 自由配置モード -->
        <div v-if="currentMode === 'free'" class="mode-content">
          <div class="header-section">
            <div class="header-content">
              <div>
                <h2>自由配置モード</h2>
                <p class="mode-description">駒を自由に配置して局面を作成できます。ドラッグ＆ドロップで駒を移動できます。</p>
              </div>
              <button @click="resetFreeMode" class="btn btn-secondary">
                保存データをクリア
              </button>
            </div>
          </div>
          <div class="two-column-layout">
            <div class="board-section">
              <Board
                :initial-board="freeModeBoard || undefined"
                :editable="true"
                @update:board="onBoardUpdate"
                @move="onMove"
              />
            </div>
            <div class="side-section">
              <MoveHistory
                :moves="freeModeHistory"
                :current-move="freeModeCurrentMove"
                @select-move="onFreeModeSelectMove"
              />
            </div>
          </div>
        </div>

        <!-- 棋譜再生モード -->
        <div v-else-if="currentMode === 'replay'" class="mode-content">
          <div class="header-section">
            <h2>棋譜再生モード</h2>
            <p class="mode-description">KIF形式の棋譜ファイルをアップロードして、棋譜を再生できます。</p>
          </div>

          <div v-if="!kifData" class="upload-section">
            <KifUploader @file-uploaded="onFileUploaded" />
          </div>

          <div v-else class="two-column-layout">
            <div class="board-section">
              <Board
                :initial-board="currentBoardState"
                :editable="false"
              />
              <ReplayControls
                :current-move="currentMove"
                :total-moves="totalMoves"
                :current-notation="currentNotation"
                :current-comment="currentComment"
                @next="nextMove"
                @previous="previousMove"
                @jump="jumpToMove"
              />
              <button @click="resetReplay" class="btn btn-danger">
                新しい棋譜をアップロード
              </button>
            </div>
            <div class="side-section">
              <MoveHistory
                :moves="replayModeHistory"
                :current-move="currentMove"
                @select-move="jumpToMove"
              />
            </div>
          </div>
        </div>
      </div>
    </main>

  </div>
</template>

<script setup lang="ts">
import { ref, watch, onMounted } from 'vue'
import { LoadingSpinner, ErrorMessage, Board, ReplayControls, KifUploader, MoveHistory, LoginForm } from './components'
import type { BoardState } from './types/shogi'

const STORAGE_KEY = 'shogi-app-state'

const currentMode = ref<'free' | 'replay'>('free')
const isLoading = ref(false)
const error = ref<string | null>(null)
const showLoginForm = ref(false)
const currentUser = ref<any>(null)

// 自由配置モードの状態
const freeModeHistory = ref<Array<{ notation: string; time?: string; comment?: string }>>([])
const freeModeCurrentMove = ref(0)
const freeModeBoard = ref<BoardState | null>(null)

// localStorage から状態を復元
const loadState = () => {
  try {
    const saved = localStorage.getItem(STORAGE_KEY)
    if (saved) {
      const state = JSON.parse(saved)
      if (state.freeModeHistory) {
        freeModeHistory.value = state.freeModeHistory
      }
      if (state.freeModeCurrentMove) {
        freeModeCurrentMove.value = state.freeModeCurrentMove
      }
      if (state.freeModeBoard) {
        freeModeBoard.value = state.freeModeBoard
      }
      console.log('State loaded from localStorage')
    }
  } catch (e) {
    console.error('Failed to load state from localStorage:', e)
  }
}

// localStorage に状態を保存
const saveState = () => {
  try {
    const state = {
      freeModeHistory: freeModeHistory.value,
      freeModeCurrentMove: freeModeCurrentMove.value,
      freeModeBoard: freeModeBoard.value,
    }
    localStorage.setItem(STORAGE_KEY, JSON.stringify(state))
    console.log('State saved to localStorage')
  } catch (e) {
    console.error('Failed to save state to localStorage:', e)
  }
}

// コンポーネントマウント時に状態を復元
onMounted(() => {
  loadState()
  checkAuth()
})

// 認証状態をチェック
const checkAuth = async () => {
  try {
    const response = await fetch('http://localhost:5001/api/auth/me', {
      credentials: 'include',
    })

    if (response.ok) {
      const data = await response.json()
      currentUser.value = data.user
    }
  } catch (e) {
    console.error('Failed to check auth:', e)
  }
}

// ログイン成功時のハンドラー
const onLoginSuccess = (user: any) => {
  currentUser.value = user
  console.log('Logged in:', user)
}

// ログアウトハンドラー
const handleLogout = async () => {
  try {
    await fetch('http://localhost:5001/api/auth/logout', {
      method: 'POST',
      credentials: 'include',
    })

    currentUser.value = null
    console.log('Logged out')
  } catch (e) {
    console.error('Failed to logout:', e)
  }
}

// 状態が変更されたら保存
watch([freeModeHistory, freeModeCurrentMove, freeModeBoard], () => {
  saveState()
}, { deep: true })

const onBoardUpdate = (board: BoardState) => {
  freeModeBoard.value = board
  console.log('Board updated:', board)
}

const onMove = (moveInfo: any) => {
  // 棋譜履歴に追加
  freeModeHistory.value.push({
    notation: moveInfo.notation,
    time: undefined,
    comment: undefined,
  })
  // 現在の手数を更新
  freeModeCurrentMove.value = freeModeHistory.value.length
  console.log('Move added to history:', moveInfo.notation)
}

const onFreeModeSelectMove = (moveIndex: number) => {
  freeModeCurrentMove.value = moveIndex + 1
  console.log('Selected move:', moveIndex)
  // TODO: 選択した手数まで盤面を戻す
}

const resetFreeMode = () => {
  freeModeHistory.value = []
  freeModeCurrentMove.value = 0
  freeModeBoard.value = null
  console.log('Free mode reset')
}

// 棋譜再生モードの状態
const kifData = ref<any>(null)
const currentMove = ref(0)
const totalMoves = ref(0)
const currentNotation = ref('')
const currentComment = ref('')
const currentBoardState = ref<BoardState | undefined>(undefined)
const replayModeHistory = ref<Array<{ notation: string; time?: string; comment?: string }>>([])

const switchMode = (mode: 'free' | 'replay') => {
  currentMode.value = mode
  error.value = null
}

const onFileUploaded = (data: any) => {
  kifData.value = data
  totalMoves.value = data.moves?.length || 0
  currentMove.value = 0

  // 棋譜データから履歴を作成
  if (data.moves && Array.isArray(data.moves)) {
    replayModeHistory.value = data.moves.map((move: any) => ({
      notation: move.notation || move.move || '---',
      time: move.time,
      comment: move.comment,
    }))
  }

  console.log('KIF file uploaded:', data)
}

const nextMove = () => {
  if (currentMove.value < totalMoves.value) {
    currentMove.value++
    updateCurrentNotation()
    // TODO: 実際の棋譜データから盤面を更新
  }
}

const previousMove = () => {
  if (currentMove.value > 0) {
    currentMove.value--
    updateCurrentNotation()
    // TODO: 実際の棋譜データから盤面を更新
  }
}

const jumpToMove = (moveNumber: number) => {
  currentMove.value = moveNumber
  updateCurrentNotation()
  // TODO: 実際の棋譜データから盤面を更新
}

const updateCurrentNotation = () => {
  if (currentMove.value > 0 && replayModeHistory.value[currentMove.value - 1]) {
    const move = replayModeHistory.value[currentMove.value - 1]
    currentNotation.value = move.notation
    currentComment.value = move.comment || ''
  } else {
    currentNotation.value = ''
    currentComment.value = ''
  }
}

const resetReplay = () => {
  kifData.value = null
  currentMove.value = 0
  totalMoves.value = 0
  currentNotation.value = ''
  currentComment.value = ''
  currentBoardState.value = undefined
  replayModeHistory.value = []
}
</script>

<style scoped>
.app-container {
  display: flex;
  flex-direction: column;
  height: 100vh;
  font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
  background-color: #f5f5f5;
}

.app-header {
  background-color: #2c3e50;
  color: white;
  padding: 12px 20px;
  box-shadow: 0 2px 4px rgba(0, 0, 0, 0.1);
}

.header-content {
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.app-header h1 {
  margin: 0 0 10px 0;
  font-size: 20px;
}

.app-nav {
  display: flex;
  gap: 10px;
}

.auth-section {
  display: flex;
  align-items: center;
  gap: 10px;
}

.username {
  color: white;
  font-size: 14px;
}

.auth-btn {
  padding: 6px 14px;
  background-color: rgba(255, 255, 255, 0.2);
  color: white;
  border: 1px solid rgba(255, 255, 255, 0.3);
  border-radius: 4px;
  cursor: pointer;
  font-size: 13px;
  transition: all 0.3s ease;
}

.auth-btn:hover {
  background-color: rgba(255, 255, 255, 0.3);
}

.nav-btn {
  padding: 6px 14px;
  background-color: rgba(255, 255, 255, 0.2);
  color: white;
  border: 1px solid rgba(255, 255, 255, 0.3);
  border-radius: 4px;
  cursor: pointer;
  font-size: 13px;
  transition: all 0.3s ease;
}

.nav-btn:hover {
  background-color: rgba(255, 255, 255, 0.3);
}

.nav-btn.active {
  background-color: #3498db;
  border-color: #3498db;
}

.app-main {
  flex: 1;
  padding: 20px;
  overflow-y: auto;
}

.content {
  background-color: white;
  padding: 20px;
  border-radius: 4px;
  box-shadow: 0 1px 3px rgba(0, 0, 0, 0.1);
}

.content p {
  margin: 10px 0;
  color: #333;
}

.mode-content {
  display: flex;
  flex-direction: column;
  gap: 20px;
  height: 100%;
}

.header-section {
  display: flex;
  flex-direction: column;
  gap: 5px;
}

.header-content {
  display: flex;
  justify-content: space-between;
  align-items: flex-start;
  gap: 20px;
}

.mode-content h2 {
  margin: 0;
  color: #2c3e50;
  font-size: 24px;
}

.mode-description {
  color: #666;
  font-size: 14px;
  margin: 0;
}

.two-column-layout {
  display: grid;
  grid-template-columns: 1fr 400px;
  gap: 20px;
  flex: 1;
  min-height: 0;
}

@media (max-width: 1200px) {
  .two-column-layout {
    grid-template-columns: 1fr 350px;
  }
}

@media (max-width: 900px) {
  .two-column-layout {
    grid-template-columns: 1fr;
  }
}

.board-section {
  display: flex;
  flex-direction: column;
  gap: 20px;
  min-height: 0;
}

.side-section {
  display: flex;
  flex-direction: column;
  min-height: 0;
  max-height: 700px;
}

.upload-section {
  display: flex;
  flex-direction: column;
  gap: 20px;
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
  align-self: flex-start;
}

.btn:hover:not(:disabled) {
  background-color: #2980b9;
}

.btn-secondary {
  background-color: #95a5a6;
}

.btn-secondary:hover:not(:disabled) {
  background-color: #7f8c8d;
}

.btn-danger {
  background-color: #e74c3c;
}

.btn-danger:hover:not(:disabled) {
  background-color: #c0392b;
}

.app-footer {
  background-color: #2c3e50;
  color: white;
  padding: 15px;
  text-align: center;
  font-size: 12px;
}

.app-footer p {
  margin: 0;
}
</style>
