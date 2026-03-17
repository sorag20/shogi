<template>
  <div class="board-container">
    <div class="board-info">
      <p>手番: {{ boardState.turn === 'black' ? '先手' : '後手' }}</p>
      <button @click="switchTurn" class="btn">手番切り替え</button>
    </div>

    <!-- 後手持ち駒 -->
    <div class="hand white-hand">
      <div class="hand-label">後手持ち駒</div>
      <div class="hand-pieces">
        <div
          v-for="(count, type) in handsWithCount('white')"
          :key="type"
          :class="['hand-piece', 'owner-white', { selected: selectedHandPiece === type && boardState.turn === 'white' }]"
          @click="selectHandPiece(toPieceType(type))"
          draggable="true"
          @dragstart="onHandDragStart(toPieceType(type))"
        >
          <span class="hand-piece-name">{{ PIECE_NAMES[toPieceType(type)] }}</span>
          <span class="hand-piece-count">{{ count }}</span>
        </div>
      </div>
    </div>

    <div class="board-wrapper">
      <!-- 列番号（9-1） -->
      <div class="column-labels">
        <div v-for="col in 9" :key="`col-${col}`" class="column-label">
          {{ 10 - col }}
        </div>
        <div class="label-spacer"></div>
      </div>

      <div class="board-with-row-labels">
        <div class="board">
          <div
            v-for="(row, rowIndex) in boardState.board"
            :key="`row-${rowIndex}`"
            class="board-row"
          >
            <div
              v-for="(piece, colIndex) in row"
              :key="`square-${rowIndex}-${colIndex}`"
              :class="[
                'square',
                { selected: isSelected(rowIndex, colIndex) },
                { 'valid-move': isValidMove(rowIndex, colIndex) },
                { highlighted: isHighlighted(rowIndex, colIndex) },
              ]"
              @click="selectSquare(rowIndex, colIndex)"
              @dragover.prevent="onDragOver(rowIndex, colIndex)"
              @drop.prevent="onDrop(rowIndex, colIndex)"
              draggable="true"
              @dragstart="onDragStart(rowIndex, colIndex)"
            >
              <div v-if="piece" :class="['piece', `piece-${piece.type}`, `owner-${piece.owner}`, { promoted: piece.promoted }]">
                <span :class="['piece-name', { 'promoted-piece': piece.promoted }]">{{ getDisplayPieceName(piece) }}</span>
              </div>
              <div v-if="isValidMove(rowIndex, colIndex)" class="move-indicator">
                <div class="move-dot"></div>
              </div>
            </div>

            <!-- 行番号（漢数字）右側のみ -->
            <div class="row-label row-label-right">
              {{ getRowLabel(rowIndex) }}
            </div>
          </div>
        </div>
      </div>
    </div>

    <!-- 成るかどうかの選択ダイアログ -->
    <div v-if="showPromoteDialog && pendingMove" class="promote-dialog-overlay" @click="cancelPromote">
      <div class="promote-dialog" @click.stop :style="getDialogPosition()">
        <div class="promote-title">成りますか？</div>
        <div class="promote-options">
          <button @click="confirmPromote(true)" class="promote-btn promote-yes">
            <span class="piece-preview promoted">{{ getPromotedPieceName() }}</span>
            <span class="promote-label">成る</span>
          </button>
          <button @click="confirmPromote(false)" class="promote-btn promote-no">
            <span class="piece-preview">{{ getCurrentPieceName() }}</span>
            <span class="promote-label">成らない</span>
          </button>
        </div>
      </div>
    </div>

    <!-- 先手持ち駒 -->
    <div class="hand black-hand">
      <div class="hand-label">先手持ち駒</div>
      <div class="hand-pieces">
        <div
          v-for="(count, type) in handsWithCount('black')"
          :key="type"
          :class="['hand-piece', 'owner-black', { selected: selectedHandPiece === type && boardState.turn === 'black' }]"
          @click="selectHandPiece(toPieceType(type))"
          draggable="true"
          @dragstart="onHandDragStart(toPieceType(type))"
        >
          <span class="hand-piece-name">{{ PIECE_NAMES[toPieceType(type)] }}</span>
          <span class="hand-piece-count">{{ count }}</span>
        </div>
      </div>
    </div>

    <div class="board-controls">
      <button @click="resetInitialPosition" class="btn">
        初期局面に戻す
      </button>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, watch } from 'vue'
import type { BoardState, Piece, PieceType } from '../types/shogi'
import { createInitialBoard } from '../utils/boardSetup'
import { getValidMoves, canPromote, type Position } from '../utils/moveRules'
import { moveToNotation, coordinatesToNotation } from '../utils/moveNotation'

interface Props {
  initialBoard?: BoardState
  editable?: boolean
}

interface MoveInfo {
  notation: string
  fromRow: number
  fromCol: number
  toRow: number
  toCol: number
  piece: Piece
  captured: Piece | null
  promoted: boolean
}

interface Emits {
  (e: 'update:board', value: BoardState): void
  (e: 'move', value: MoveInfo): void
  (e: 'reset'): void
}

const props = withDefaults(defineProps<Props>(), {
  editable: true,
})

const emit = defineEmits<Emits>()

const PIECE_NAMES: Record<PieceType, string> = {
  pawn: '歩',
  lance: '香',
  knight: '桂',
  silver: '銀',
  gold: '金',
  bishop: '角',
  rook: '飛',
  king: '玉',
}

const boardState = ref<BoardState>(props.initialBoard || createInitialBoard())

// initialBoard が変更されたら盤面を更新（リロード時の復元用）
watch(() => props.initialBoard, (newBoard) => {
  if (newBoard) {
    boardState.value = newBoard
    console.log('Board restored from saved state')
  }
}, { immediate: true, deep: true })

const selectedRow = ref<number | null>(null)
const selectedCol = ref<number | null>(null)
const validMoves = ref<Position[]>([])
const draggedRow = ref<number | null>(null)
const draggedCol = ref<number | null>(null)
const showPromoteDialog = ref(false)
const pendingMove = ref<{ fromRow: number; fromCol: number; toRow: number; toCol: number } | null>(null)
const selectedHandPiece = ref<PieceType | null>(null)
const draggedHandPiece = ref<PieceType | null>(null)

// string → PieceType キャスト用ヘルパー（テンプレートから使用）
const toPieceType = (t: string): PieceType => t as PieceType

// 持ち駒のうち枚数が1以上のものを返す
const handsWithCount = (owner: 'black' | 'white'): Partial<Record<PieceType, number>> => {
  const hand = boardState.value.hands[owner]
  const result: Partial<Record<PieceType, number>> = {}
  for (const key of Object.keys(hand) as PieceType[]) {
    if (hand[key] > 0) result[key] = hand[key]
  }
  return result
}

// 持ち駒を選択（打ちの準備）
const selectHandPiece = (pieceType: PieceType) => {
  if (!props.editable) return
  if (boardState.value.hands[boardState.value.turn][pieceType] <= 0) return

  if (selectedHandPiece.value === pieceType) {
    selectedHandPiece.value = null
    validMoves.value = []
  } else {
    selectedHandPiece.value = pieceType
    selectedRow.value = null
    selectedCol.value = null
    validMoves.value = getDropMoves(pieceType, boardState.value.turn)
  }
}

// 打てるマスを返す
const getDropMoves = (pieceType: PieceType, owner: 'black' | 'white'): Position[] => {
  const moves: Position[] = []
  for (let row = 0; row < 9; row++) {
    for (let col = 0; col < 9; col++) {
      if (boardState.value.board[row][col] !== null) continue

      // 歩・香：最奥段禁止
      if (pieceType === 'pawn' || pieceType === 'lance') {
        if (owner === 'black' && row === 0) continue
        if (owner === 'white' && row === 8) continue
      }
      // 桂：最奥2段禁止
      if (pieceType === 'knight') {
        if (owner === 'black' && row <= 1) continue
        if (owner === 'white' && row >= 7) continue
      }
      // 二歩チェック
      if (pieceType === 'pawn') {
        let hasPawn = false
        for (let r = 0; r < 9; r++) {
          const p = boardState.value.board[r][col]
          if (p && p.type === 'pawn' && !p.promoted && p.owner === owner) {
            hasPawn = true
            break
          }
        }
        if (hasPawn) continue
      }

      moves.push({ row, col })
    }
  }
  return moves
}

// 持ち駒を盤上に打つ
const dropPiece = (pieceType: PieceType, owner: 'black' | 'white', toRow: number, toCol: number) => {
  if (boardState.value.hands[owner][pieceType] <= 0) return

  boardState.value.hands[owner][pieceType]--
  boardState.value.board[toRow][toCol] = { type: pieceType, owner, promoted: false }

  const notation = `${owner === 'black' ? '▲' : '△'}${coordinatesToNotation(toRow, toCol)}${PIECE_NAMES[pieceType]}打`
  const isCheck = checkForCheck(toRow, toCol)
  playPieceSound(isCheck)

  emit('move', {
    notation,
    fromRow: -1,
    fromCol: -1,
    toRow,
    toCol,
    piece: { type: pieceType, owner, promoted: false },
    captured: null,
    promoted: false,
  })

  boardState.value.turn = boardState.value.turn === 'black' ? 'white' : 'black'
  selectedHandPiece.value = null
  draggedHandPiece.value = null
  validMoves.value = []
  emit('update:board', boardState.value)
}

// 持ち駒のドラッグ開始
const onHandDragStart = (pieceType: PieceType) => {
  if (!props.editable) return
  if (boardState.value.hands[boardState.value.turn][pieceType] <= 0) return
  draggedHandPiece.value = pieceType
  validMoves.value = getDropMoves(pieceType, boardState.value.turn)
}

const isSelected = (row: number, col: number) => {
  return selectedRow.value === row && selectedCol.value === col
}

const isValidMove = (row: number, col: number) => {
  return validMoves.value.some(move => move.row === row && move.col === col)
}

const isHighlighted = (row: number, col: number) => {
  return draggedRow.value === row && draggedCol.value === col
}

const selectSquare = (row: number, col: number) => {
  if (!props.editable) return

  // 持ち駒が選択中の場合：打ち
  if (selectedHandPiece.value !== null) {
    if (isValidMove(row, col)) {
      dropPiece(selectedHandPiece.value, boardState.value.turn, row, col)
    } else {
      selectedHandPiece.value = null
      validMoves.value = []
    }
    return
  }

  const clickedPiece = boardState.value.board[row][col]

  // 盤上の駒が選択されている場合
  if (selectedRow.value !== null && selectedCol.value !== null) {
    if (isValidMove(row, col)) {
      const piece = boardState.value.board[selectedRow.value][selectedCol.value]
      if (piece && canPromote(piece, selectedRow.value, row)) {
        pendingMove.value = {
          fromRow: selectedRow.value,
          fromCol: selectedCol.value,
          toRow: row,
          toCol: col,
        }
        showPromoteDialog.value = true
      } else {
        movePiece(selectedRow.value, selectedCol.value, row, col)
      }
      return
    }
  }

  // 自分の駒をクリックした場合（新しく選択）
  if (clickedPiece && clickedPiece.owner === boardState.value.turn) {
    selectedRow.value = row
    selectedCol.value = col
    selectedHandPiece.value = null
    validMoves.value = getValidMoves(boardState.value.board, row, col)
  } else {
    selectedRow.value = null
    selectedCol.value = null
    validMoves.value = []
  }
}

const onDragStart = (row: number, col: number) => {
  if (!props.editable) return
  const piece = boardState.value.board[row][col]

  // 自分の駒のみドラッグ可能
  if (!piece || piece.owner !== boardState.value.turn) return

  draggedRow.value = row
  draggedCol.value = col

  // ドラッグ開始時に有効な移動先を計算
  validMoves.value = getValidMoves(boardState.value.board, row, col)
}

const onDragOver = (row: number, col: number) => {
  if (!props.editable) return
  if (draggedRow.value === null || draggedCol.value === null) return

  // 有効な移動先の場合のみドロップを許可
  const isValid = validMoves.value.some(move => move.row === row && move.col === col)
  if (isValid) {
    // Allow drop
  }
}

const onDrop = (row: number, col: number) => {
  if (!props.editable) return

  // 持ち駒のドロップ
  if (draggedHandPiece.value !== null) {
    if (isValidMove(row, col)) {
      dropPiece(draggedHandPiece.value, boardState.value.turn, row, col)
    }
    draggedHandPiece.value = null
    validMoves.value = []
    return
  }

  if (draggedRow.value === null || draggedCol.value === null) return

  // 有効な移動先かチェック
  const isValid = validMoves.value.some(move => move.row === row && move.col === col)
  if (!isValid) {
    draggedRow.value = null
    draggedCol.value = null
    validMoves.value = []
    return
  }

  const piece = boardState.value.board[draggedRow.value][draggedCol.value]
  if (piece && canPromote(piece, draggedRow.value, row)) {
    // 成れる場合は選択ダイアログを表示
    pendingMove.value = {
      fromRow: draggedRow.value,
      fromCol: draggedCol.value,
      toRow: row,
      toCol: col,
    }
    showPromoteDialog.value = true
  } else {
    // 成れない場合は通常移動
    movePiece(draggedRow.value, draggedCol.value, row, col)
  }

  draggedRow.value = null
  draggedCol.value = null
  validMoves.value = []
}

const movePiece = (fromRow: number, fromCol: number, toRow: number, toCol: number, shouldPromote: boolean = false) => {
  const piece = boardState.value.board[fromRow][fromCol]
  if (!piece) return

  // 取られる駒を記録
  const capturedPiece = boardState.value.board[toRow][toCol]
  const isCapture = capturedPiece !== null

  // 成ったかどうか
  let didPromote = false

  // 成る場合
  if (shouldPromote) {
    piece.promoted = true
    didPromote = true
  }

  // 棋譜表記を生成
  const notation = moveToNotation(piece, fromRow, fromCol, toRow, toCol, isCapture, didPromote)

  // 駒を移動
  boardState.value.board[toRow][toCol] = piece
  boardState.value.board[fromRow][fromCol] = null

  // 取った駒を持ち駒に追加（成り駒は元の種類に戻す）
  if (capturedPiece) {
    const baseType = capturedPiece.type  // 成り駒でも type は元の種類
    boardState.value.hands[piece.owner][baseType]++
  }

  // 王手かチェック
  const isCheck = checkForCheck(toRow, toCol)

  // 駒音を再生
  playPieceSound(isCheck)

  // 移動情報をemit
  emit('move', {
    notation,
    fromRow,
    fromCol,
    toRow,
    toCol,
    piece: { ...piece },
    captured: capturedPiece,
    promoted: didPromote,
  })

  // 手番を切り替え
  boardState.value.turn = boardState.value.turn === 'black' ? 'white' : 'black'

  // 選択解除
  selectedRow.value = null
  selectedCol.value = null
  validMoves.value = []

  emit('update:board', boardState.value)
}

const checkForCheck = (toRow: number, toCol: number): boolean => {
  // 簡易的な王手チェック（移動先の駒が相手の王を攻撃できるか）
  const piece = boardState.value.board[toRow][toCol]
  if (!piece) return false

  const opponentTurn = piece.owner === 'black' ? 'white' : 'black'

  // 相手の王の位置を探す
  for (let row = 0; row < 9; row++) {
    for (let col = 0; col < 9; col++) {
      const targetPiece = boardState.value.board[row][col]
      if (targetPiece && targetPiece.type === 'king' && targetPiece.owner === opponentTurn) {
        // 移動した駒が王を攻撃できるかチェック
        const validMoves = getValidMoves(boardState.value.board, toRow, toCol)
        return validMoves.some(move => move.row === row && move.col === col)
      }
    }
  }
  return false
}

const playPieceSound = (isCheck: boolean = false) => {
  try {
    const audioContext = new (window.AudioContext || (window as any).webkitAudioContext)()

    if (isCheck) {
      // 王手の音：高く鋭い「パチン」という音
      const oscillator1 = audioContext.createOscillator()
      const oscillator2 = audioContext.createOscillator()
      const gainNode = audioContext.createGain()

      oscillator1.connect(gainNode)
      oscillator2.connect(gainNode)
      gainNode.connect(audioContext.destination)

      oscillator1.type = 'sine'
      oscillator2.type = 'sine'

      oscillator1.frequency.setValueAtTime(2400, audioContext.currentTime)
      oscillator1.frequency.exponentialRampToValueAtTime(1200, audioContext.currentTime + 0.05)

      oscillator2.frequency.setValueAtTime(3200, audioContext.currentTime)
      oscillator2.frequency.exponentialRampToValueAtTime(1600, audioContext.currentTime + 0.05)

      gainNode.gain.setValueAtTime(0.5, audioContext.currentTime)
      gainNode.gain.exponentialRampToValueAtTime(0.01, audioContext.currentTime + 0.12)

      oscillator1.start(audioContext.currentTime)
      oscillator1.stop(audioContext.currentTime + 0.12)
      oscillator2.start(audioContext.currentTime)
      oscillator2.stop(audioContext.currentTime + 0.12)
    } else {
      // 通常の駒音：木の甲高い「カチッ」という音

      // メインの衝突音（高音）
      const osc1 = audioContext.createOscillator()
      const gain1 = audioContext.createGain()
      osc1.connect(gain1)
      gain1.connect(audioContext.destination)

      osc1.type = 'sine'
      osc1.frequency.setValueAtTime(2800, audioContext.currentTime)
      osc1.frequency.exponentialRampToValueAtTime(1400, audioContext.currentTime + 0.015)

      gain1.gain.setValueAtTime(0.4, audioContext.currentTime)
      gain1.gain.exponentialRampToValueAtTime(0.01, audioContext.currentTime + 0.04)

      // 倍音成分
      const osc2 = audioContext.createOscillator()
      const gain2 = audioContext.createGain()
      osc2.connect(gain2)
      gain2.connect(audioContext.destination)

      osc2.type = 'sine'
      osc2.frequency.setValueAtTime(4200, audioContext.currentTime)
      osc2.frequency.exponentialRampToValueAtTime(2100, audioContext.currentTime + 0.01)

      gain2.gain.setValueAtTime(0.2, audioContext.currentTime)
      gain2.gain.exponentialRampToValueAtTime(0.01, audioContext.currentTime + 0.025)

      // さらに高い倍音
      const osc3 = audioContext.createOscillator()
      const gain3 = audioContext.createGain()
      osc3.connect(gain3)
      gain3.connect(audioContext.destination)

      osc3.type = 'sine'
      osc3.frequency.setValueAtTime(5600, audioContext.currentTime)
      osc3.frequency.exponentialRampToValueAtTime(2800, audioContext.currentTime + 0.008)

      gain3.gain.setValueAtTime(0.15, audioContext.currentTime)
      gain3.gain.exponentialRampToValueAtTime(0.01, audioContext.currentTime + 0.02)

      // 白色ノイズ（衝突の瞬間）
      const bufferSize = audioContext.sampleRate * 0.015
      const noiseBuffer = audioContext.createBuffer(1, bufferSize, audioContext.sampleRate)
      const noiseData = noiseBuffer.getChannelData(0)
      for (let i = 0; i < bufferSize; i++) {
        noiseData[i] = (Math.random() * 2 - 1) * Math.exp(-i / (bufferSize * 0.3))
      }

      const noiseSource = audioContext.createBufferSource()
      const noiseGain = audioContext.createGain()
      const noiseFilter = audioContext.createBiquadFilter()

      noiseSource.buffer = noiseBuffer
      noiseSource.connect(noiseFilter)
      noiseFilter.connect(noiseGain)
      noiseGain.connect(audioContext.destination)

      noiseFilter.type = 'highpass'
      noiseFilter.frequency.value = 3000
      noiseFilter.Q.value = 0.5

      noiseGain.gain.setValueAtTime(0.3, audioContext.currentTime)
      noiseGain.gain.exponentialRampToValueAtTime(0.01, audioContext.currentTime + 0.015)

      // すべての音を再生
      osc1.start(audioContext.currentTime)
      osc1.stop(audioContext.currentTime + 0.04)

      osc2.start(audioContext.currentTime)
      osc2.stop(audioContext.currentTime + 0.025)

      osc3.start(audioContext.currentTime)
      osc3.stop(audioContext.currentTime + 0.02)

      noiseSource.start(audioContext.currentTime)
    }
  } catch (e) {
    console.error('Failed to play sound:', e)
  }
}

const confirmPromote = (promote: boolean) => {
  if (!pendingMove.value) return

  const { fromRow, fromCol, toRow, toCol } = pendingMove.value
  movePiece(fromRow, fromCol, toRow, toCol, promote)

  // ダイアログを閉じる
  showPromoteDialog.value = false
  pendingMove.value = null
}

const cancelPromote = () => {
  showPromoteDialog.value = false
  pendingMove.value = null
  selectedRow.value = null
  selectedCol.value = null
  validMoves.value = []
}

const getDialogPosition = () => {
  if (!pendingMove.value) return {}
  const { toRow, toCol } = pendingMove.value
  // 盤面の座標に基づいてダイアログの位置を計算
  const top = toRow * 51 + 100 // 50px(square) + 1px(gap) + offset
  const left = toCol * 51 + 100
  return {
    top: `${top}px`,
    left: `${left}px`,
  }
}

const getPromotedPieceName = () => {
  if (!pendingMove.value) return ''
  const piece = boardState.value.board[pendingMove.value.fromRow][pendingMove.value.fromCol]
  if (!piece) return ''

  // 成った後の駒名
  const promotedNames: Record<PieceType, string> = {
    pawn: 'と',
    lance: '成香',
    knight: '成桂',
    silver: '成銀',
    gold: '金',
    bishop: '馬',
    rook: '龍',
    king: '玉',
  }
  return promotedNames[piece.type] || PIECE_NAMES[piece.type]
}

const getCurrentPieceName = () => {
  if (!pendingMove.value) return ''
  const piece = boardState.value.board[pendingMove.value.fromRow][pendingMove.value.fromCol]
  if (!piece) return ''
  return PIECE_NAMES[piece.type]
}

const resetInitialPosition = () => {
  if (!props.editable) return
  // Initialize with standard starting position
  boardState.value = createInitialBoard()
  selectedRow.value = null
  selectedCol.value = null
  emit('update:board', boardState.value)
  emit('reset')
}

const switchTurn = () => {
  boardState.value.turn = boardState.value.turn === 'black' ? 'white' : 'black'
  emit('update:board', boardState.value)
}

const getPieceName = (type: PieceType): string => {
  return PIECE_NAMES[type] || type
}

const getDisplayPieceName = (piece: Piece): string => {
  if (!piece.promoted) {
    return PIECE_NAMES[piece.type] || piece.type
  }

  // 成駒の表示名
  const promotedNames: Record<PieceType, string> = {
    pawn: 'と',
    lance: '杏',
    knight: '圭',
    silver: '全',
    gold: '金',
    bishop: '馬',
    rook: '龍',
    king: '玉',
  }
  return promotedNames[piece.type] || PIECE_NAMES[piece.type]
}

const getRowLabel = (rowIndex: number): string => {
  const kanjiNumbers = ['一', '二', '三', '四', '五', '六', '七', '八', '九']
  return kanjiNumbers[rowIndex]
}
</script>

<style scoped>
.board-container {
  display: flex;
  flex-direction: column;
  gap: 20px;
  padding: 20px;
  background-color: white;
  border-radius: 4px;
  box-shadow: 0 1px 3px rgba(0, 0, 0, 0.1);
}

.board-wrapper {
  display: flex;
  flex-direction: column;
  align-items: center;
  width: fit-content;
  margin: 0 auto;
}

.column-labels {
  display: grid;
  grid-template-columns: repeat(9, 50px) 30px;
  gap: 1px;
  margin-bottom: 5px;
  width: 100%;
}

.label-spacer {
  width: 30px;
  visibility: hidden;
}

.column-label {
  width: 50px;
  text-align: center;
  font-weight: bold;
  font-size: 16px;
  color: #333;
}

.board-with-row-labels {
  display: flex;
  align-items: center;
}

.board {
  display: flex;
  flex-direction: column;
  gap: 1px;
  background-color: #333;
  padding: 1px;
}

.board-row {
  display: grid;
  grid-template-columns: repeat(9, 50px) 30px;
  gap: 1px;
}

.row-label {
  display: flex;
  align-items: center;
  justify-content: center;
  font-weight: bold;
  font-size: 16px;
  color: #333;
  background-color: white;
}

.row-label-right {
  justify-content: flex-start;
  padding-left: 5px;
}

.square {
  width: 50px;
  height: 50px;
  background-color: #deb887;
  border: 1px solid #333;
  display: flex;
  align-items: center;
  justify-content: center;
  position: relative;
  cursor: pointer;
  user-select: none;
  transition: background-color 0.2s;
}

.square:hover {
  background-color: #e0c9a0;
}

.square.selected {
  background-color: #90ee90;
  box-shadow: inset 0 0 0 3px #2ecc71;
}

.square.valid-move {
  background-color: #fff3cd;
  cursor: pointer;
}

.square.valid-move:hover {
  background-color: #ffe69c;
}

.square.highlighted {
  background-color: #ffeb3b;
}

.move-indicator {
  position: absolute;
  width: 100%;
  height: 100%;
  display: flex;
  align-items: center;
  justify-content: center;
  pointer-events: none;
  z-index: 1;
}

.move-dot {
  width: 12px;
  height: 12px;
  background-color: rgba(46, 204, 113, 0.6);
  border-radius: 50%;
  box-shadow: 0 0 4px rgba(46, 204, 113, 0.8);
}

.piece {
  width: 38px;
  height: 42px;
  display: flex;
  align-items: center;
  justify-content: center;
  position: relative;
  cursor: grab;
  font-weight: bold;
  font-size: 16px;
  z-index: 2;
  /* 五角形風の駒の形 */
  clip-path: polygon(50% 0%, 100% 25%, 100% 100%, 0% 100%, 0% 25%);
  box-shadow: 0 2px 4px rgba(0, 0, 0, 0.3);
  transition: transform 0.1s;
}

.piece:hover {
  transform: scale(1.05);
}

.piece.owner-black {
  background: linear-gradient(135deg, #8b7355 0%, #d4a373 50%, #8b7355 100%);
  color: #000;
  text-shadow: 0 0 1px rgba(255, 255, 255, 0.3);
}

.piece.owner-white {
  background: linear-gradient(135deg, #f5deb3 0%, #faf0e6 50%, #f5deb3 100%);
  color: #000;
  text-shadow: 0 0 1px rgba(255, 255, 255, 0.5);
  transform: rotate(180deg);
}

/* 白の駒は反転しているので、テキストも反転 */
.piece.owner-white .piece-name {
  display: inline-block;
  transform: rotate(180deg);
}

.piece.owner-white .promoted-mark {
  transform: rotate(180deg);
}

.promoted-mark {
  position: absolute;
  top: 3px;
  left: 3px;
  font-size: 9px;
  color: #d00;
  font-weight: bold;
  text-shadow: 0 0 2px rgba(255, 255, 255, 0.8);
}

.piece-name {
  font-size: 18px;
  font-weight: 900;
  font-family: "Hiragino Mincho ProN", "Yu Mincho", "MS Mincho", serif;
}

.piece-name.promoted-piece {
  color: #d32f2f;
  text-shadow: 0 0 2px rgba(255, 255, 255, 0.8);
}

.board-controls {
  display: flex;
  gap: 10px;
  flex-wrap: wrap;
}

.board-info {
  display: flex;
  align-items: center;
  gap: 10px;
}

.btn {
  padding: 8px 16px;
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

.btn-danger {
  background-color: #e74c3c;
}

.btn-danger:hover:not(:disabled) {
  background-color: #c0392b;
}

.promote-dialog-overlay {
  position: fixed;
  top: 0;
  left: 0;
  right: 0;
  bottom: 0;
  background-color: rgba(0, 0, 0, 0.5);
  display: flex;
  align-items: center;
  justify-content: center;
  z-index: 1000;
}

.promote-dialog {
  position: absolute;
  background: white;
  border-radius: 8px;
  padding: 20px;
  box-shadow: 0 4px 12px rgba(0, 0, 0, 0.3);
  min-width: 200px;
  transform: translate(-50%, -50%);
}

.promote-title {
  font-size: 16px;
  font-weight: bold;
  margin-bottom: 15px;
  text-align: center;
  color: #2c3e50;
}

.promote-options {
  display: flex;
  gap: 15px;
  justify-content: center;
}

.promote-btn {
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 8px;
  padding: 15px 20px;
  border: 2px solid #ddd;
  border-radius: 8px;
  background: white;
  cursor: pointer;
  transition: all 0.2s;
  min-width: 80px;
}

.promote-btn:hover {
  border-color: #3498db;
  background-color: #f0f8ff;
  transform: scale(1.05);
}

.promote-yes:hover {
  border-color: #e74c3c;
  background-color: #fff5f5;
}

.promote-no:hover {
  border-color: #95a5a6;
  background-color: #f5f5f5;
}

.piece-preview {
  font-size: 32px;
  font-weight: 900;
  font-family: "Hiragino Mincho ProN", "Yu Mincho", "MS Mincho", serif;
  color: #2c3e50;
}

.piece-preview.promoted {
  color: #e74c3c;
}

.promote-label {
  font-size: 14px;
  font-weight: bold;
  color: #666;
}

/* 持ち駒エリア */
.hand {
  display: flex;
  align-items: center;
  gap: 10px;
  padding: 8px 12px;
  background: #f5efe0;
  border: 1px solid #c8a96e;
  border-radius: 4px;
  min-height: 52px;
  width: fit-content;
}

.hand-label {
  font-size: 13px;
  font-weight: bold;
  color: #555;
  white-space: nowrap;
}

.hand-pieces {
  display: flex;
  gap: 6px;
  flex-wrap: wrap;
}

.hand-piece {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  width: 42px;
  height: 46px;
  cursor: pointer;
  border: 2px solid transparent;
  border-radius: 4px;
  clip-path: polygon(50% 0%, 100% 25%, 100% 100%, 0% 100%, 0% 25%);
  box-shadow: 0 2px 4px rgba(0,0,0,0.2);
  transition: transform 0.1s;
  position: relative;
}

.hand-piece:hover {
  transform: scale(1.08);
}

.hand-piece.selected {
  outline: 3px solid #2ecc71;
  outline-offset: 2px;
}

.hand-piece.owner-black {
  background: linear-gradient(135deg, #8b7355 0%, #d4a373 50%, #8b7355 100%);
}

.hand-piece.owner-white {
  background: linear-gradient(135deg, #f5deb3 0%, #faf0e6 50%, #f5deb3 100%);
}

.hand-piece-name {
  font-size: 16px;
  font-weight: 900;
  font-family: "Hiragino Mincho ProN", "Yu Mincho", "MS Mincho", serif;
  line-height: 1;
}

.hand-piece-count {
  font-size: 11px;
  font-weight: bold;
  color: #333;
  line-height: 1;
}
</style>
