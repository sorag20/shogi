<template>
  <div class="evaluation-display">
    <div class="evaluation-header">
      <h3>評価値</h3>
      <div class="header-controls">
        <div class="model-toggle">
          <button
            @click="modelType = 'nn'"
            :class="['toggle-btn', { active: modelType === 'nn' }]"
          >NN</button>
          <button
            @click="modelType = 'az'"
            :class="['toggle-btn', { active: modelType === 'az' }]"
          >AZ</button>
        </div>
        <button @click="requestEvaluation" class="btn btn-sm" :disabled="isLoading">
          {{ isLoading ? '計算中...' : '更新' }}
        </button>
      </div>
    </div>

    <LoadingSpinner v-if="isLoading" :is-loading="true" message="評価値を計算中..." />

    <ErrorMessage v-if="error" :error="error" @dismiss="error = null" />

    <div v-if="evaluation !== null && !isLoading" class="evaluation-result">
      <div class="bar-wrapper">
        <div class="bar-label">後手</div>
        <div class="eval-bar">
          <div class="eval-fill" :style="fillStyle"></div>
        </div>
        <div class="bar-label">先手</div>
      </div>
      <div class="evaluation-value">
        <span :class="['value', evaluationClass]">{{ formattedValue }}</span>
      </div>
      <div v-if="bestMove" class="best-move">
        <span class="best-move-label">最善手</span>
        <span class="best-move-value">{{ bestMove }}</span>
      </div>
      <div v-else-if="bestMove === null" class="best-move">
        <span class="best-move-label">最善手</span>
        <span class="best-move-none">なし（詰み）</span>
      </div>
    </div>

    <div v-else-if="!isLoading && evaluation === null" class="no-evaluation">
      <p>「更新」ボタンで評価値を計算します</p>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, computed } from 'vue'
import { LoadingSpinner, ErrorMessage } from './index'
import type { BoardState } from '../types/shogi'

interface Props {
  board?: BoardState
}

const props = defineProps<Props>()

const evaluation = ref<number | null>(null)
const bestMove = ref<string | null | undefined>(undefined) // undefined=未取得, null=なし, string=手
const isLoading = ref(false)
const error = ref<string | null>(null)
const modelType = ref<'nn' | 'az'>('nn')

const evaluationClass = computed(() => {
  if (evaluation.value === null) return ''
  if (evaluation.value > 100) return 'positive'
  if (evaluation.value < -100) return 'negative'
  return 'neutral'
})

const formattedValue = computed(() => {
  if (evaluation.value === null) return ''
  const v = evaluation.value
  return v > 0 ? `先手 +${v.toFixed(0)}` : v < 0 ? `後手 +${Math.abs(v).toFixed(0)}` : '互角'
})

// バーの塗り幅: 先手有利なら右側が広くなる (0%=後手圧勝, 50%=互角, 100%=先手圧勝)
const fillStyle = computed(() => {
  if (evaluation.value === null) return { width: '50%' }
  // clamp to [-1000, 1000]
  const clamped = Math.max(-1000, Math.min(1000, evaluation.value))
  const pct = ((clamped + 1000) / 2000) * 100
  return { width: `${pct}%` }
})

const requestEvaluation = async () => {
  if (!props.board) {
    error.value = '局面が設定されていません'
    return
  }

  isLoading.value = true
  error.value = null

  try {
    const [evalRes, moveRes] = await Promise.all([
      fetch('http://localhost:5001/api/evaluate', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        credentials: 'include',
        body: JSON.stringify({ board: props.board, model: modelType.value }),
      }),
      fetch('http://localhost:5001/api/best-move', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        credentials: 'include',
        body: JSON.stringify({ board: props.board }),
      }),
    ])

    const evalData = await evalRes.json()
    if (!evalRes.ok) throw new Error(evalData.message || '評価値の取得に失敗しました')
    evaluation.value = evalData.evaluation

    const moveData = await moveRes.json()
    bestMove.value = moveRes.ok ? (moveData.best_move ?? null) : null
  } catch (err: any) {
    error.value = err.message || '評価値の取得に失敗しました'
  } finally {
    isLoading.value = false
  }
}
</script>

<style scoped>
.evaluation-display {
  padding: 12px;
  background-color: white;
  border-radius: 4px;
  box-shadow: 0 1px 3px rgba(0, 0, 0, 0.1);
}

.evaluation-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 10px;
}

.evaluation-header h3 {
  margin: 0;
  font-size: 15px;
  color: #2c3e50;
}

.header-controls {
  display: flex;
  align-items: center;
  gap: 8px;
}

.model-toggle {
  display: flex;
  border: 1px solid #bdc3c7;
  border-radius: 4px;
  overflow: hidden;
}

.toggle-btn {
  padding: 3px 8px;
  font-size: 11px;
  border: none;
  background: #f5f5f5;
  color: #666;
  cursor: pointer;
}

.toggle-btn.active {
  background: #3498db;
  color: white;
}

.toggle-btn:hover:not(.active) {
  background: #e0e0e0;
}

.bar-wrapper {
  display: flex;
  align-items: center;
  gap: 6px;
  margin-bottom: 8px;
}

.bar-label {
  font-size: 11px;
  color: #666;
  white-space: nowrap;
}

.eval-bar {
  flex: 1;
  height: 16px;
  background: #e74c3c;
  border-radius: 8px;
  overflow: hidden;
}

.eval-fill {
  height: 100%;
  background: #2980b9;
  transition: width 0.4s ease;
}

.evaluation-value {
  text-align: center;
}

.value {
  font-size: 15px;
  font-weight: bold;
}

.value.positive { color: #2980b9; }
.value.negative { color: #e74c3c; }
.value.neutral  { color: #27ae60; }

.best-move {
  display: flex;
  align-items: center;
  gap: 8px;
  margin-top: 8px;
  padding: 6px 8px;
  background: #f0f4f8;
  border-radius: 4px;
}

.best-move-label {
  font-size: 11px;
  color: #666;
  white-space: nowrap;
}

.best-move-value {
  font-size: 15px;
  font-weight: bold;
  color: #2c3e50;
  font-family: "Hiragino Mincho ProN", "Yu Mincho", serif;
}

.best-move-none {
  font-size: 13px;
  color: #e74c3c;
}

.no-evaluation {
  text-align: center;
  color: #999;
  font-size: 12px;
  padding: 10px 0;
}

.btn {
  padding: 5px 10px;
  background-color: #3498db;
  color: white;
  border: none;
  border-radius: 4px;
  cursor: pointer;
  font-size: 12px;
}

.btn:hover:not(:disabled) { background-color: #2980b9; }
.btn:disabled { background-color: #bdc3c7; cursor: not-allowed; }
</style>
