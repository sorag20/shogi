<template>
  <div class="lp">
    <!-- Hero -->
    <section class="hero">
      <div class="hero-bg">
        <div class="hero-piece p1">王</div>
        <div class="hero-piece p2">飛</div>
        <div class="hero-piece p3">角</div>
        <div class="hero-piece p4">金</div>
        <div class="hero-piece p5">銀</div>
        <div class="hero-piece p6">と</div>
      </div>
      <div class="hero-content">
        <div class="logo-mark">将</div>
        <h1 class="hero-title">
          <span class="title-main">将棋AI</span>
          <span class="title-sub">SHOGI ANALYZER</span>
        </h1>
        <p class="hero-desc">
          機械学習による評価関数搭載。<br>
          局面を分析し、最善手を提案します。
        </p>
        <div class="hero-actions">
          <button class="btn-primary" @click="$emit('start')">
            <span class="btn-icon">▶</span>
            今すぐ始める
          </button>
          <button class="btn-secondary" @click="scrollTo('features')">
            機能を見る
          </button>
        </div>
        <div class="hero-badges">
          <span class="badge">機械学習</span>
          <span class="badge">強化学習</span>
          <span class="badge">棋譜解析</span>
        </div>
      </div>
      <div class="hero-board">
        <div class="mini-board">
          <div v-for="row in 9" :key="row" class="mini-row">
            <div v-for="col in 9" :key="col" class="mini-sq" :class="getMiniBoardClass(row-1, col-1)">
              <span v-if="getMiniPiece(row-1, col-1)" class="mini-piece" :class="getMiniPieceOwner(row-1, col-1)">
                {{ getMiniPiece(row-1, col-1) }}
              </span>
            </div>
          </div>
        </div>
      </div>
    </section>

    <!-- Features -->
    <section id="features" class="features">
      <div class="section-header">
        <h2>主な機能</h2>
        <div class="section-line"></div>
      </div>
      <div class="feature-grid">
        <div class="feature-card">
          <div class="feature-icon">🧠</div>
          <h3>AI評価値分析</h3>
          <p>ニューラルネットワークが現在の局面を数値で評価。先手・後手どちらが有利かをリアルタイムに表示します。</p>
        </div>
        <div class="feature-card">
          <div class="feature-icon">♟️</div>
          <h3>最善手提案</h3>
          <p>機械学習モデルが次の最善手を計算。TD学習による強化学習でモデルを継続的に改善しています。</p>
        </div>
        <div class="feature-card">
          <div class="feature-icon">📋</div>
          <h3>棋譜再生</h3>
          <p>KIF形式の棋譜ファイルをアップロードして対局を再生。名局の手順をステップごとに確認できます。</p>
        </div>
        <div class="feature-card">
          <div class="feature-icon">🎯</div>
          <h3>自由配置モード</h3>
          <p>任意の局面を自由に作成。持ち駒の打ちも対応し、詰め将棋の研究や棋力向上に活用できます。</p>
        </div>
      </div>
    </section>

    <!-- Tech Stack -->
    <section class="tech">
      <div class="section-header">
        <h2>技術スタック</h2>
        <div class="section-line"></div>
      </div>
      <div class="tech-grid">
        <div class="tech-item">
          <div class="tech-label">Frontend</div>
          <div class="tech-name">Vue 3</div>
        </div>
        <div class="tech-divider">+</div>
        <div class="tech-item">
          <div class="tech-label">Backend</div>
          <div class="tech-name">Flask</div>
        </div>
        <div class="tech-divider">+</div>
        <div class="tech-item">
          <div class="tech-label">AI Engine</div>
          <div class="tech-name">PyTorch</div>
        </div>
        <div class="tech-divider">+</div>
        <div class="tech-item">
          <div class="tech-label">Database</div>
          <div class="tech-name">MySQL</div>
        </div>
      </div>
      <div class="ml-flow">
        <div class="ml-step">
          <div class="ml-step-num">1</div>
          <div class="ml-step-text">ランダム自己対局で<br>局面データを生成</div>
        </div>
        <div class="ml-arrow">→</div>
        <div class="ml-step">
          <div class="ml-step-num">2</div>
          <div class="ml-step-text">駒得評価を正解として<br>教師あり学習</div>
        </div>
        <div class="ml-arrow">→</div>
        <div class="ml-step">
          <div class="ml-step-num">3</div>
          <div class="ml-step-text">TD学習による<br>強化学習で精度向上</div>
        </div>
        <div class="ml-arrow">→</div>
        <div class="ml-step">
          <div class="ml-step-num">4</div>
          <div class="ml-step-text">リアルタイム<br>局面評価・最善手提示</div>
        </div>
      </div>
    </section>

    <!-- CTA -->
    <section class="cta">
      <h2>さあ、将棋を始めよう</h2>
      <p>ログインして対局記録を保存することもできます</p>
      <div class="cta-actions">
        <button class="btn-primary large" @click="$emit('start')">
          アプリを起動する
        </button>
      </div>
    </section>

    <footer class="lp-footer">
      <p>SHOGI ANALYZER — Powered by PyTorch &amp; Vue 3</p>
    </footer>
  </div>
</template>

<script setup lang="ts">
defineEmits(['start'])

const scrollTo = (id: string) => {
  document.getElementById(id)?.scrollIntoView({ behavior: 'smooth' })
}

// ミニ将棋盤（初期配置の一部）
const MINI_BOARD: Record<string, { name: string; owner: 'b' | 'w' }> = {
  '0-0': { name: '香', owner: 'w' }, '0-1': { name: '桂', owner: 'w' }, '0-2': { name: '銀', owner: 'w' },
  '0-3': { name: '金', owner: 'w' }, '0-4': { name: '王', owner: 'w' }, '0-5': { name: '金', owner: 'w' },
  '0-6': { name: '銀', owner: 'w' }, '0-7': { name: '桂', owner: 'w' }, '0-8': { name: '香', owner: 'w' },
  '1-1': { name: '飛', owner: 'w' }, '1-7': { name: '角', owner: 'w' },
  '2-0': { name: '歩', owner: 'w' }, '2-1': { name: '歩', owner: 'w' }, '2-2': { name: '歩', owner: 'w' },
  '2-3': { name: '歩', owner: 'w' }, '2-4': { name: '歩', owner: 'w' }, '2-5': { name: '歩', owner: 'w' },
  '2-6': { name: '歩', owner: 'w' }, '2-7': { name: '歩', owner: 'w' }, '2-8': { name: '歩', owner: 'w' },
  '6-0': { name: '歩', owner: 'b' }, '6-1': { name: '歩', owner: 'b' }, '6-2': { name: '歩', owner: 'b' },
  '6-3': { name: '歩', owner: 'b' }, '6-4': { name: '歩', owner: 'b' }, '6-5': { name: '歩', owner: 'b' },
  '6-6': { name: '歩', owner: 'b' }, '6-7': { name: '歩', owner: 'b' }, '6-8': { name: '歩', owner: 'b' },
  '7-1': { name: '角', owner: 'b' }, '7-7': { name: '飛', owner: 'b' },
  '8-0': { name: '香', owner: 'b' }, '8-1': { name: '桂', owner: 'b' }, '8-2': { name: '銀', owner: 'b' },
  '8-3': { name: '金', owner: 'b' }, '8-4': { name: '玉', owner: 'b' }, '8-5': { name: '金', owner: 'b' },
  '8-6': { name: '銀', owner: 'b' }, '8-7': { name: '桂', owner: 'b' }, '8-8': { name: '香', owner: 'b' },
}

const getMiniPiece = (row: number, col: number) => MINI_BOARD[`${row}-${col}`]?.name ?? null
const getMiniPieceOwner = (row: number, col: number) => MINI_BOARD[`${row}-${col}`]?.owner ?? 'b'
const getMiniBoardClass = (row: number, col: number) => {
  const key = `${row}-${col}`
  if (MINI_BOARD[key]) return 'has-piece'
  return ''
}
</script>

<style scoped>
/* ===== Base ===== */
.lp {
  font-family: 'Hiragino Sans', 'Yu Gothic', sans-serif;
  color: #1a1a2e;
  overflow-x: hidden;
}

/* ===== Hero ===== */
.hero {
  min-height: 100vh;
  background: linear-gradient(135deg, #1a1a2e 0%, #16213e 50%, #0f3460 100%);
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 80px;
  padding: 60px 40px;
  position: relative;
  overflow: hidden;
}

.hero-bg {
  position: absolute;
  inset: 0;
  pointer-events: none;
}

.hero-piece {
  position: absolute;
  font-size: 80px;
  font-weight: 900;
  font-family: "Hiragino Mincho ProN", serif;
  opacity: 0.04;
  color: #e2b96e;
  animation: float 8s ease-in-out infinite;
}
.p1 { top: 10%; left: 5%;  animation-delay: 0s;   font-size: 120px; }
.p2 { top: 60%; left: 2%;  animation-delay: 1.5s; font-size: 90px; }
.p3 { top: 20%; right: 8%; animation-delay: 3s;   font-size: 100px; }
.p4 { top: 70%; right: 5%; animation-delay: 2s;   font-size: 80px; }
.p5 { top: 40%; left: 50%; animation-delay: 1s;   font-size: 70px; opacity: 0.02; }
.p6 { top: 80%; left: 30%; animation-delay: 4s;   font-size: 60px; }

@keyframes float {
  0%, 100% { transform: translateY(0) rotate(-5deg); }
  50%       { transform: translateY(-20px) rotate(5deg); }
}

.hero-content {
  max-width: 520px;
  z-index: 1;
}

.logo-mark {
  width: 60px;
  height: 60px;
  background: linear-gradient(135deg, #e2b96e, #c8953a);
  clip-path: polygon(50% 0%, 100% 20%, 100% 100%, 0% 100%, 0% 20%);
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 26px;
  font-weight: 900;
  font-family: "Hiragino Mincho ProN", serif;
  color: #1a1a2e;
  margin-bottom: 24px;
  box-shadow: 0 4px 20px rgba(226, 185, 110, 0.4);
}

.hero-title {
  margin: 0 0 16px;
  line-height: 1.1;
}

.title-main {
  display: block;
  font-size: 56px;
  font-weight: 900;
  color: #e2b96e;
  font-family: "Hiragino Mincho ProN", serif;
  letter-spacing: 4px;
}

.title-sub {
  display: block;
  font-size: 18px;
  font-weight: 400;
  color: rgba(255, 255, 255, 0.5);
  letter-spacing: 6px;
  margin-top: 4px;
}

.hero-desc {
  color: rgba(255, 255, 255, 0.75);
  font-size: 16px;
  line-height: 1.8;
  margin: 0 0 32px;
}

.hero-actions {
  display: flex;
  gap: 16px;
  margin-bottom: 24px;
  flex-wrap: wrap;
}

.btn-primary {
  display: flex;
  align-items: center;
  gap: 8px;
  padding: 14px 32px;
  background: linear-gradient(135deg, #e2b96e, #c8953a);
  color: #1a1a2e;
  border: none;
  border-radius: 8px;
  font-size: 16px;
  font-weight: 700;
  cursor: pointer;
  transition: all 0.3s;
  box-shadow: 0 4px 20px rgba(226, 185, 110, 0.4);
}

.btn-primary:hover {
  transform: translateY(-2px);
  box-shadow: 0 8px 30px rgba(226, 185, 110, 0.5);
}

.btn-primary.large {
  padding: 18px 48px;
  font-size: 18px;
}

.btn-icon { font-size: 12px; }

.btn-secondary {
  padding: 14px 28px;
  background: transparent;
  color: rgba(255, 255, 255, 0.8);
  border: 1px solid rgba(255, 255, 255, 0.3);
  border-radius: 8px;
  font-size: 16px;
  cursor: pointer;
  transition: all 0.3s;
}

.btn-secondary:hover {
  background: rgba(255, 255, 255, 0.1);
  border-color: rgba(255, 255, 255, 0.5);
}

.hero-badges {
  display: flex;
  gap: 10px;
  flex-wrap: wrap;
}

.badge {
  padding: 4px 12px;
  background: rgba(226, 185, 110, 0.15);
  border: 1px solid rgba(226, 185, 110, 0.3);
  border-radius: 20px;
  color: #e2b96e;
  font-size: 12px;
  font-weight: 500;
  letter-spacing: 1px;
}

/* ===== Mini Board ===== */
.hero-board {
  z-index: 1;
  flex-shrink: 0;
}

.mini-board {
  background: #c8953a;
  padding: 3px;
  border-radius: 4px;
  box-shadow: 0 20px 60px rgba(0, 0, 0, 0.5), 0 0 0 1px rgba(226, 185, 110, 0.3);
}

.mini-row { display: flex; }

.mini-sq {
  width: 38px;
  height: 38px;
  background: #deb887;
  border: 0.5px solid rgba(100, 60, 0, 0.3);
  display: flex;
  align-items: center;
  justify-content: center;
}

.mini-piece {
  font-size: 13px;
  font-weight: 900;
  font-family: "Hiragino Mincho ProN", serif;
  line-height: 1;
}

.mini-piece.b {
  color: #1a1a2e;
}

.mini-piece.w {
  color: #1a1a2e;
  display: inline-block;
  transform: rotate(180deg);
}

/* ===== Features ===== */
.features {
  padding: 100px 40px;
  background: #f8f6f0;
}

.section-header {
  text-align: center;
  margin-bottom: 60px;
}

.section-header h2 {
  font-size: 36px;
  font-weight: 900;
  color: #1a1a2e;
  font-family: "Hiragino Mincho ProN", serif;
  margin: 0 0 16px;
}

.section-line {
  width: 60px;
  height: 3px;
  background: linear-gradient(90deg, #e2b96e, #c8953a);
  margin: 0 auto;
  border-radius: 2px;
}

.feature-grid {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(240px, 1fr));
  gap: 28px;
  max-width: 1100px;
  margin: 0 auto;
}

.feature-card {
  background: white;
  border-radius: 12px;
  padding: 36px 28px;
  box-shadow: 0 2px 16px rgba(0, 0, 0, 0.06);
  transition: all 0.3s;
  border: 1px solid rgba(0,0,0,0.05);
}

.feature-card:hover {
  transform: translateY(-6px);
  box-shadow: 0 12px 40px rgba(0, 0, 0, 0.12);
}

.feature-icon {
  font-size: 40px;
  margin-bottom: 16px;
}

.feature-card h3 {
  font-size: 18px;
  font-weight: 700;
  margin: 0 0 12px;
  color: #1a1a2e;
}

.feature-card p {
  font-size: 14px;
  color: #666;
  line-height: 1.7;
  margin: 0;
}

/* ===== Tech ===== */
.tech {
  padding: 100px 40px;
  background: #1a1a2e;
}

.tech .section-header h2 { color: white; }

.tech-grid {
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 20px;
  margin-bottom: 60px;
  flex-wrap: wrap;
}

.tech-item {
  text-align: center;
  background: rgba(255,255,255,0.05);
  border: 1px solid rgba(226, 185, 110, 0.2);
  border-radius: 12px;
  padding: 24px 36px;
  min-width: 140px;
}

.tech-label {
  font-size: 11px;
  color: #e2b96e;
  letter-spacing: 2px;
  text-transform: uppercase;
  margin-bottom: 8px;
}

.tech-name {
  font-size: 22px;
  font-weight: 700;
  color: white;
}

.tech-divider {
  font-size: 24px;
  color: rgba(226, 185, 110, 0.4);
  font-weight: 300;
}

.ml-flow {
  display: flex;
  align-items: flex-start;
  justify-content: center;
  gap: 8px;
  flex-wrap: wrap;
  max-width: 900px;
  margin: 0 auto;
}

.ml-step {
  text-align: center;
  max-width: 160px;
}

.ml-step-num {
  width: 40px;
  height: 40px;
  background: linear-gradient(135deg, #e2b96e, #c8953a);
  border-radius: 50%;
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 18px;
  font-weight: 700;
  color: #1a1a2e;
  margin: 0 auto 12px;
}

.ml-step-text {
  font-size: 13px;
  color: rgba(255,255,255,0.65);
  line-height: 1.6;
}

.ml-arrow {
  font-size: 24px;
  color: rgba(226, 185, 110, 0.4);
  margin-top: 8px;
  align-self: flex-start;
  padding-top: 8px;
}

/* ===== CTA ===== */
.cta {
  padding: 100px 40px;
  background: linear-gradient(135deg, #0f3460 0%, #16213e 100%);
  text-align: center;
}

.cta h2 {
  font-size: 40px;
  font-weight: 900;
  color: white;
  font-family: "Hiragino Mincho ProN", serif;
  margin: 0 0 16px;
}

.cta p {
  color: rgba(255,255,255,0.6);
  font-size: 16px;
  margin: 0 0 40px;
}

.cta-actions {
  display: flex;
  justify-content: center;
}

/* ===== Footer ===== */
.lp-footer {
  background: #0d0d1a;
  padding: 24px;
  text-align: center;
}

.lp-footer p {
  color: rgba(255,255,255,0.3);
  font-size: 12px;
  letter-spacing: 2px;
  margin: 0;
}

/* ===== Responsive ===== */
@media (max-width: 900px) {
  .hero {
    flex-direction: column;
    gap: 40px;
    padding: 80px 24px 60px;
    text-align: center;
  }
  .logo-mark { margin: 0 auto 24px; }
  .hero-actions { justify-content: center; }
  .hero-badges { justify-content: center; }
  .title-main { font-size: 40px; }
  .hero-board { display: none; }
}
</style>
