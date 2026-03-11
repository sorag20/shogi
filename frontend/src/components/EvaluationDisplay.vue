<template>
  <div class="evaluation-display">
    <div class="evaluation-header">
      <h3>AI評価値</h3>
      <button @click="requestEvaluation" class="btn btn-sm" :disabled="isLoading">
        {{ isLoading ? '計算中...' : '評価値を取得' }}
      </button>
    </div>

    <LoadingSpinner v-if="isLoading" :is-loading="true" message="評価値を計算中..." />

    <ErrorMessage v-if="error" :error="error" @dismiss="error = null" />

    <div v-if="evaluation !== null && !isLoading" class="evaluation-result">
      <div class="evaluation-value">
        <span class="label">評価値:</span>
        <span :class="['value', evaluationClass]">
          {{ formatEvaluation(evaluation) }}
        </span>
      </div>

      <div v-if="bestMove" class="best-move">
        <span class="label">最善手:</span>
        <span class="value">{{ bestMove }}</span>
      </div>

      <div v-if="pv && pv.length > 0" class="pv">
        <span class="label">主要変化:</span>
        <span class="value">{{ pv.join(' → ') }}</span>
      </div>

      <div class="computed-at">
        <small>計算時刻: {{ computedAt }}</small>
      </div>
    </div>

    <div v-else-if="!isLoading && evaluation === null" class="no-evaluation">
      <p>評価値を取得するには「評価値を取得」ボタンをクリックしてください</p>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, computed } from 'vue'
import { evaluationApi } from '../api'
import { LoadingSpinner, ErrorMessage } from './index'

interface Props {
  position?: {
    board: any
    turn: 'black' | 'white'
  }
}

const props = defineProps<Props>()

const evaluation = ref<number | null>(null)
const bestMove = ref<string | null>(null)
const pv = ref<string[]>([])
const computedAt = ref<string>('')
const isLoading = ref(false)
const error = ref<string | null>(null)

const evaluationClass = computed(() => {
  if (evaluation.value === null) return ''
  if (evaluation.value > 100) return 'positive'
  if (evaluation.value < -100) return 'negative'
  return 'neutral'
})

const formatEvaluation = (value: number): string => {
  return value > 0 ? `+${value.toFixed(2)}` : value.toFixed(2)
}

const requestEvaluation = async () => {
  if (!props.position) {
    error.value = '局面が設定されていません'
    return
  }

  isLoading.value = true
  error.value = null

  try {
    const result = await evaluationApi.evaluate(props.position)
    evaluation.value = result.evaluation
    bestMove.value = result.best_move || null
    pv.value = result.pv || []
    computedAt.value = new Date(result.computed_at).toLocaleString('ja-JP')
  } catch (err) {
    error.value = err instanceof Error ? err.message : '評価値の取得に失敗しました'
  } finally {
    isLoading.value = false
  }
}
</script>

<style scoped>
.evaluation-display {
  padding: 15px;
  background-color: white;
  border-radius: 4px;
  box-shadow: 0 1px 3px rgba(0, 0, 0, 0.1);
}

.evaluation-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 15px;
}

.evaluation-header h3 {
  margin: 0;
  font-size: 16px;
  color: #2c3e50;
}

.evaluation-result {
  display: flex;
  flex-direction: column;
  gap: 10px;
}

.evaluation-value,
.best-move,
.pv {
  display: flex;
  gap: 10px;
  align-items: center;
}

.label {
  font-weight: bold;
  color: #666;
  min-width: 80px;
}

.value {
  font-size: 14px;
  color: #333;
}

.value.positive {
  color: #27ae60;
  font-weight: bold;
}

.value.negative {
  color: #e74c3c;
  font-weight: bold;
}

.value.neutral {
  color: #3498db;
}

.computed-at {
  margin-top: 10px;
  padding-top: 10px;
  border-top: 1px solid #eee;
  color: #999;
  font-size: 12px;
}

.no-evaluation {
  padding: 20px;
  text-align: center;
  color: #999;
  font-size: 13px;
}

.btn {
  padding: 6px 12px;
  background-color: #3498db;
  color: white;
  border: none;
  border-radius: 4px;
  cursor: pointer;
  font-size: 12px;
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
</style>
