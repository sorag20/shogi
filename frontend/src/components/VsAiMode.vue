<template>
  <!-- セットアップ画面 -->
  <div v-if="gamePhase === 'setup'" class="setup-screen">
    <h2>AI対戦</h2>
    <div class="setup-form">
      <div class="setup-row">
        <label>AIモデル</label>
        <div class="toggle-group">
          <button :class="['toggle-btn', { active: aiModel === 'nn' }]" @click="aiModel = 'nn'">NN</button>
          <button :class="['toggle-btn', { active: aiModel === 'az' }]" @click="aiModel = 'az'">AZ</button>
        </div>
      </div>
      <div class="setup-row">
        <label>あなたの手番</label>
        <div class="toggle-group">
          <button :class="['toggle-btn', { active: userColor === 'black' }]" @click="userColor = 'black'">先手（▲）</button>
          <button :class="['toggle-btn', { active: userColor === 'white' }]" @click="userColor = 'white'">後手（△）</button>
        </div>
      </div>
      <button @click="startGame" class="btn btn-start">対局開始</button>
    </div>
  </div>

  <!-- 対局画面 -->
  <div v-else class="game-screen">
    <div class="game-header">
      <div class="status-area">
        <span :class="['status-badge', aiThinking ? 'thinking' : isUserTurn ? 'user' : 'ai']">
          {{ statusText }}
        </span>
        <span class="model-badge">{{ aiModel.toUpperCase() }}</span>
        <span class="color-badge">あなた: {{ userColor === 'black' ? '先手（▲）' : '後手（△）' }}</span>
      </div>
      <button @click="resetToSetup" class="btn btn-secondary">対局終了</button>
    </div>

    <div class="two-column-layout">
      <div class="board-section">
        <Board
          :initial-board="currentBoard || undefined"
          :editable="isUserTurn"
          @update:board="onBoardUpdate"
          @move="onUserMove"
        />
      </div>
      <div class="side-section">
        <MoveHistory :moves="moveHistory" :current-move="moveHistory.length" />
      </div>
    </div>

    <!-- ゲームオーバーオーバーレイ -->
    <div v-if="gamePhase === 'game-over'" class="overlay">
      <div class="game-over-dialog">
        <h3>{{ gameOverMessage }}</h3>
        <div class="dialog-buttons">
          <button @click="startGame" class="btn">もう一度</button>
          <button @click="resetToSetup" class="btn btn-secondary">設定に戻る</button>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, computed } from 'vue'
import { Board, MoveHistory } from './index'
import { createInitialBoard } from '../utils/boardSetup'
import type { BoardState, PieceType } from '../types/shogi'

const gamePhase = ref<'setup' | 'playing' | 'game-over'>('setup')
const aiModel = ref<'nn' | 'az'>('nn')
const userColor = ref<'black' | 'white'>('black')
const currentBoard = ref<BoardState | null>(null)
const moveHistory = ref<Array<{ notation: string }>>([])
const aiThinking = ref(false)
const gameOverMessage = ref('')

// Board は同じオブジェクト参照を共有するため、
// onBoardUpdate 時には currentBoard.value.turn がすでに切り替わっている。
// onUserMove (move イベント) は update:board より先に発火するので
// フラグで「ユーザーが直前に指した」を記録する。
let _userJustMoved = false

const isUserTurn = computed(() =>
  gamePhase.value === 'playing' &&
  !aiThinking.value &&
  currentBoard.value?.turn === userColor.value
)

const statusText = computed(() => {
  if (gamePhase.value === 'game-over') return gameOverMessage.value
  if (aiThinking.value) return 'AIが考えています...'
  if (isUserTurn.value) return 'あなたの番です'
  return 'AIの番'
})

const startGame = () => {
  currentBoard.value = createInitialBoard()
  moveHistory.value = []
  gameOverMessage.value = ''
  gamePhase.value = 'playing'

  // ユーザーが後手なら先手(AI)から始まる
  if (userColor.value === 'white') {
    requestAiMove()
  }
}

const resetToSetup = () => {
  gamePhase.value = 'setup'
  currentBoard.value = null
  moveHistory.value = []
}

// Board から更新を受け取る（ユーザー操作による盤面変化）
const onBoardUpdate = (board: BoardState) => {
  currentBoard.value = board

  if (gamePhase.value === 'playing' && !aiThinking.value && _userJustMoved) {
    _userJustMoved = false
    requestAiMove()
  }
}

// ユーザーが手を指したとき（move は update:board より先に発火する）
const onUserMove = (moveInfo: any) => {
  moveHistory.value.push({ notation: moveInfo.notation })
  _userJustMoved = true
}

const requestAiMove = async () => {
  if (!currentBoard.value) return
  aiThinking.value = true

  try {
    const res = await fetch('http://localhost:5001/api/best-move', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      credentials: 'include',
      body: JSON.stringify({ board: currentBoard.value, model: aiModel.value }),
    })
    const data = await res.json()

    if (data.best_move === null) {
      gameOverMessage.value = 'あなたの勝ち！'
      gamePhase.value = 'game-over'
      return
    }

    // AI の手を盤面に適用
    if (currentBoard.value && data.move_data) {
      currentBoard.value = applyMoveData(currentBoard.value, data.move_data)
      moveHistory.value.push({ notation: data.best_move })
    }
  } catch (e) {
    console.error('AI move failed:', e)
  } finally {
    aiThinking.value = false
  }
}

// バックエンドの move_data を boardState に適用して新しい boardState を返す
function applyMoveData(board: BoardState, moveData: any): BoardState {
  const newBoardArr = board.board.map(row => row.map(p => (p ? { ...p } : null)))
  const newHands = {
    black: { ...board.hands.black },
    white: { ...board.hands.white },
  }
  const mover = board.turn

  if (moveData.type === 'board') {
    const { from_row, from_col, to_row, to_col, promote } = moveData
    const piece = newBoardArr[from_row][from_col]
    if (!piece) return board

    const captured = newBoardArr[to_row][to_col]
    if (captured && captured.type !== 'king') {
      // 取った駒を手駒に追加（成り駒は元の種類に戻す）
      newHands[mover][captured.type] = (newHands[mover][captured.type] ?? 0) + 1
    }

    newBoardArr[to_row][to_col] = { ...piece, promoted: promote || piece.promoted }
    newBoardArr[from_row][from_col] = null
  } else if (moveData.type === 'drop') {
    const { piece_type, to_row, to_col } = moveData
    const pt = piece_type as PieceType
    newHands[mover][pt] = Math.max(0, (newHands[mover][pt] ?? 0) - 1)
    newBoardArr[to_row][to_col] = { type: pt, owner: mover, promoted: false }
  }

  return {
    board: newBoardArr,
    hands: newHands,
    turn: board.turn === 'black' ? 'white' : 'black',
  }
}
</script>

<style scoped>
.setup-screen {
  display: flex;
  flex-direction: column;
  align-items: center;
  padding: 40px 20px;
  gap: 30px;
}

.setup-screen h2 {
  margin: 0;
  font-size: 24px;
  color: #2c3e50;
}

.setup-form {
  display: flex;
  flex-direction: column;
  gap: 24px;
  width: 100%;
  max-width: 400px;
}

.setup-row {
  display: flex;
  flex-direction: column;
  gap: 8px;
}

.setup-row label {
  font-size: 14px;
  color: #555;
  font-weight: 600;
}

.toggle-group {
  display: flex;
  border: 1px solid #bdc3c7;
  border-radius: 6px;
  overflow: hidden;
}

.toggle-btn {
  flex: 1;
  padding: 10px;
  font-size: 14px;
  border: none;
  background: #f5f5f5;
  color: #555;
  cursor: pointer;
  transition: background 0.2s;
}

.toggle-btn.active {
  background: #3498db;
  color: white;
  font-weight: 600;
}

.toggle-btn:hover:not(.active) {
  background: #e0e0e0;
}

.btn-start {
  padding: 12px;
  font-size: 16px;
  background: #27ae60;
  color: white;
  border: none;
  border-radius: 6px;
  cursor: pointer;
  font-weight: 600;
  transition: background 0.2s;
}

.btn-start:hover {
  background: #219a52;
}

/* ゲーム画面 */
.game-screen {
  display: flex;
  flex-direction: column;
  gap: 16px;
  position: relative;
}

.game-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.status-area {
  display: flex;
  align-items: center;
  gap: 10px;
  flex-wrap: wrap;
}

.status-badge {
  padding: 6px 14px;
  border-radius: 20px;
  font-size: 14px;
  font-weight: 600;
}

.status-badge.user { background: #d5e8d4; color: #27ae60; }
.status-badge.ai   { background: #dae8fc; color: #2980b9; }
.status-badge.thinking { background: #fff3cd; color: #856404; }

.model-badge, .color-badge {
  font-size: 12px;
  color: #888;
  background: #f0f0f0;
  padding: 4px 10px;
  border-radius: 12px;
}

.two-column-layout {
  display: grid;
  grid-template-columns: 1fr 350px;
  gap: 20px;
}

@media (max-width: 900px) {
  .two-column-layout { grid-template-columns: 1fr; }
}

.board-section, .side-section {
  display: flex;
  flex-direction: column;
  gap: 16px;
}

/* ゲームオーバーオーバーレイ */
.overlay {
  position: absolute;
  inset: 0;
  background: rgba(0, 0, 0, 0.5);
  display: flex;
  align-items: center;
  justify-content: center;
  border-radius: 4px;
  z-index: 10;
}

.game-over-dialog {
  background: white;
  padding: 32px 40px;
  border-radius: 12px;
  text-align: center;
  box-shadow: 0 8px 32px rgba(0, 0, 0, 0.2);
}

.game-over-dialog h3 {
  margin: 0 0 24px;
  font-size: 24px;
  color: #2c3e50;
}

.dialog-buttons {
  display: flex;
  gap: 12px;
  justify-content: center;
}

.btn {
  padding: 8px 20px;
  background: #3498db;
  color: white;
  border: none;
  border-radius: 4px;
  cursor: pointer;
  font-size: 14px;
  transition: background 0.2s;
}

.btn:hover { background: #2980b9; }

.btn-secondary {
  background: #95a5a6;
}

.btn-secondary:hover { background: #7f8c8d; }
</style>
