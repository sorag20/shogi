<template>
  <div class="move-history">
    <h3>棋譜</h3>
    <div class="moves-container">
      <div v-if="moves.length === 0" class="no-moves">
        <p>まだ手が進んでいません</p>
      </div>
      <div v-else class="moves-list">
        <div
          v-for="(move, index) in moves"
          :key="index"
          :class="['move-item', { active: index === currentMove - 1 }]"
          @click="onMoveClick(index)"
        >
          <span class="move-number">{{ index + 1 }}.</span>
          <span class="move-notation">{{ move.notation || '---' }}</span>
          <span v-if="move.time" class="move-time">({{ move.time }})</span>
        </div>
      </div>
    </div>
    <div v-if="moveCount > 0" class="history-info">
      <p class="info-text">総手数: {{ moveCount }}</p>
    </div>
  </div>
</template>

<script setup lang="ts">
import { computed } from 'vue'

interface Move {
  notation: string
  time?: string
  comment?: string
}

interface Props {
  moves: Move[]
  currentMove?: number
}

interface Emits {
  (e: 'select-move', moveIndex: number): void
}

const props = withDefaults(defineProps<Props>(), {
  currentMove: 0,
})

const emit = defineEmits<Emits>()

const moveCount = computed(() => props.moves.length)

const onMoveClick = (index: number) => {
  emit('select-move', index)
}
</script>

<style scoped>
.move-history {
  display: flex;
  flex-direction: column;
  height: 100%;
  background-color: white;
  border-radius: 4px;
  box-shadow: 0 1px 3px rgba(0, 0, 0, 0.1);
  overflow: hidden;
}

.move-history h3 {
  margin: 0;
  padding: 15px;
  background-color: #2c3e50;
  color: white;
  font-size: 18px;
  font-weight: 600;
}

.moves-container {
  flex: 1;
  overflow-y: auto;
  padding: 10px;
}

.no-moves {
  display: flex;
  align-items: center;
  justify-content: center;
  height: 100%;
  color: #999;
  font-size: 14px;
}

.no-moves p {
  margin: 0;
}

.moves-list {
  display: flex;
  flex-direction: column;
  gap: 2px;
}

.move-item {
  display: flex;
  align-items: center;
  gap: 8px;
  padding: 8px 12px;
  border-radius: 4px;
  cursor: pointer;
  transition: background-color 0.2s;
  font-size: 14px;
}

.move-item:hover {
  background-color: #f0f0f0;
}

.move-item.active {
  background-color: #3498db;
  color: white;
}

.move-number {
  font-weight: bold;
  min-width: 35px;
  color: #666;
}

.move-item.active .move-number {
  color: white;
}

.move-notation {
  flex: 1;
  font-family: 'Courier New', monospace;
}

.move-time {
  font-size: 12px;
  color: #999;
}

.move-item.active .move-time {
  color: rgba(255, 255, 255, 0.8);
}

.history-info {
  padding: 10px 15px;
  border-top: 1px solid #e0e0e0;
  background-color: #f9f9f9;
}

.info-text {
  margin: 0;
  font-size: 13px;
  color: #666;
}
</style>
