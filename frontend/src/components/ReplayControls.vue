<template>
  <div class="replay-controls">
    <div class="controls-group">
      <button @click="goToStart" class="btn btn-sm" :disabled="currentMove <= 0">
        ⏮ 最初
      </button>
      <button @click="previousMove" class="btn btn-sm" :disabled="currentMove <= 0">
        ◀ 前へ
      </button>

      <div class="move-display">
        <span class="move-number">{{ currentMove }} / {{ totalMoves }}</span>
      </div>

      <button @click="nextMove" class="btn btn-sm" :disabled="currentMove >= totalMoves">
        次へ ▶
      </button>
      <button @click="goToEnd" class="btn btn-sm" :disabled="currentMove >= totalMoves">
        最後 ⏭
      </button>
    </div>

    <div class="jump-group">
      <label for="move-input">手数へジャンプ:</label>
      <input
        id="move-input"
        v-model.number="jumpMoveNumber"
        type="number"
        min="0"
        :max="totalMoves"
        class="input-sm"
      />
      <button @click="jumpToMove" class="btn btn-sm">ジャンプ</button>
    </div>

    <div v-if="currentNotation" class="move-info">
      <p><strong>手数:</strong> {{ currentMove }}</p>
      <p><strong>棋譜:</strong> {{ currentNotation }}</p>
      <p v-if="currentComment"><strong>コメント:</strong> {{ currentComment }}</p>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, computed } from 'vue'

interface Props {
  currentMove: number
  totalMoves: number
  currentNotation?: string
  currentComment?: string
}

interface Emits {
  (e: 'next'): void
  (e: 'previous'): void
  (e: 'jump', moveNumber: number): void
}

const props = withDefaults(defineProps<Props>(), {
  currentNotation: '',
  currentComment: '',
})

const emit = defineEmits<Emits>()

const jumpMoveNumber = ref<number>(0)

const nextMove = () => {
  if (props.currentMove < props.totalMoves) {
    emit('next')
  }
}

const previousMove = () => {
  if (props.currentMove > 0) {
    emit('previous')
  }
}

const goToStart = () => {
  emit('jump', 0)
}

const goToEnd = () => {
  emit('jump', props.totalMoves)
}

const jumpToMove = () => {
  if (jumpMoveNumber.value >= 0 && jumpMoveNumber.value <= props.totalMoves) {
    emit('jump', jumpMoveNumber.value)
  }
}
</script>

<style scoped>
.replay-controls {
  display: flex;
  flex-direction: column;
  gap: 15px;
  padding: 15px;
  background-color: white;
  border-radius: 4px;
  box-shadow: 0 1px 3px rgba(0, 0, 0, 0.1);
}

.controls-group {
  display: flex;
  align-items: center;
  gap: 10px;
  flex-wrap: wrap;
}

.move-display {
  padding: 8px 12px;
  background-color: #f0f0f0;
  border-radius: 4px;
  font-weight: bold;
  min-width: 80px;
  text-align: center;
}

.move-number {
  font-size: 14px;
  color: #333;
}

.jump-group {
  display: flex;
  align-items: center;
  gap: 10px;
  flex-wrap: wrap;
}

.jump-group label {
  font-size: 14px;
  color: #666;
}

.input-sm {
  padding: 6px 8px;
  border: 1px solid #ddd;
  border-radius: 4px;
  font-size: 14px;
  width: 60px;
}

.btn {
  padding: 8px 12px;
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

.btn-sm {
  padding: 6px 10px;
  font-size: 12px;
}

.move-info {
  padding: 10px;
  background-color: #f9f9f9;
  border-left: 3px solid #3498db;
  border-radius: 2px;
}

.move-info p {
  margin: 5px 0;
  font-size: 13px;
  color: #333;
}

.move-info strong {
  color: #2c3e50;
}
</style>
