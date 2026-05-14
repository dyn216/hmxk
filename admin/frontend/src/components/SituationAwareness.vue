<template>
  <section class="situation-page">
    <section class="situation-hero reveal" data-delay="1">
      <div>
        <p class="situation-kicker">SITUATION AWARENESS</p>
        <h2>慢病监测态势感知</h2>
        <p class="situation-copy">聚合患者监测、风险预警、设备活跃和数据趋势，帮助管理端快速发现异常变化。</p>
      </div>
      <div class="situation-orbit" aria-hidden="true">
        <span></span>
        <span></span>
        <strong>{{ overview.compliance_rate ?? 0 }}%</strong>
        <em>依从率</em>
      </div>
    </section>

    <section class="situation-metrics">
      <article v-for="item in metricCards" :key="item.label" class="situation-metric reveal" :data-tone="item.tone">
        <span>{{ item.label }}</span>
        <strong>{{ item.value }}</strong>
        <small>{{ item.hint }}</small>
      </article>
    </section>

    <section class="situation-board">
      <article class="situation-panel situation-panel--wide reveal" data-delay="2">
        <div class="panel-head">
          <div>
            <p>近 {{ windowDays }} 天数据态势</p>
            <h3>监测趋势 / 异常叠加</h3>
          </div>
          <span>{{ formatDateTime(overview.latest_measurement_at) }}</span>
        </div>
        <svg class="trend-chart" viewBox="0 0 100 56" preserveAspectRatio="none" role="img" aria-label="监测趋势图">
          <defs>
            <linearGradient id="totalLine" x1="0" x2="1" y1="0" y2="0">
              <stop offset="0%" stop-color="#3F7D6E" />
              <stop offset="100%" stop-color="#8EBFAE" />
            </linearGradient>
            <linearGradient id="abnormalLine" x1="0" x2="1" y1="0" y2="0">
              <stop offset="0%" stop-color="#C0894E" />
              <stop offset="100%" stop-color="#C75D4F" />
            </linearGradient>
          </defs>
          <polyline class="trend-area" :points="totalAreaPoints" />
          <polyline class="trend-line total" :points="totalLinePoints" />
          <polyline class="trend-line abnormal" :points="abnormalLinePoints" />
        </svg>
        <div class="trend-legend">
          <span><i class="dot total"></i>监测量</span>
          <span><i class="dot abnormal"></i>异常量</span>
          <span>峰值 {{ maxTrendValue.toLocaleString('zh-CN') }}</span>
        </div>
      </article>

      <article class="situation-panel reveal" data-delay="3">
        <div class="panel-head compact-head">
          <div>
            <p>风险分层</p>
            <h3>预警占比</h3>
          </div>
        </div>
        <div class="risk-stack">
          <div v-for="item in riskDistribution" :key="item.risk_level" class="risk-row">
            <span>{{ item.label }}</span>
            <div class="bar-track"><i :style="{ width: percent(item.count, riskTotal) + '%' }"></i></div>
            <strong>{{ item.count }}</strong>
          </div>
        </div>
      </article>

      <article class="situation-panel reveal" data-delay="4">
        <div class="panel-head compact-head">
          <div>
            <p>数据类型</p>
            <h3>采集构成</h3>
          </div>
        </div>
        <div class="type-list">
          <div v-for="item in typeDistribution" :key="item.type" class="type-item">
            <div>
              <strong>{{ item.label }}</strong>
              <span>均值 {{ item.avg_label || item.avg_value }}</span>
            </div>
            <div class="bar-track"><i :style="{ width: percent(item.count, typeTotal) + '%' }"></i></div>
            <em>{{ item.count }}</em>
          </div>
        </div>
      </article>
    </section>

    <section class="situation-lists">
      <article class="situation-panel reveal" data-delay="2">
        <div class="panel-head compact-head">
          <div>
            <p>患者活跃排行</p>
            <h3>高频监测人群</h3>
          </div>
        </div>
        <div class="rank-list">
          <div v-for="(item, index) in patientRanking" :key="item.patient_id" class="rank-item">
            <b>{{ index + 1 }}</b>
            <div>
              <strong>{{ item.name }}</strong>
              <span>{{ item.phone || '—' }} · 最近 {{ formatDateTime(item.latest_measurement) }}</span>
            </div>
            <em>{{ item.measurement_count }} 次</em>
          </div>
        </div>
      </article>

      <article class="situation-panel situation-panel--wide reveal" data-delay="3">
        <div class="panel-head compact-head">
          <div>
            <p>异常告警</p>
            <h3>最新需要关注的数据</h3>
          </div>
        </div>
        <div class="alert-list">
          <div v-for="item in latestAbnormal" :key="item.id" class="alert-item" :data-risk="item.risk_level">
            <div class="alert-mark">{{ item.risk_label }}</div>
            <div class="alert-main">
              <strong>{{ item.patient_name }} · {{ item.type_label }} {{ item.value }}</strong>
              <span>{{ item.ai_suggestion || '暂无建议' }}</span>
            </div>
            <time>{{ formatDateTime(item.measured_at) }}</time>
          </div>
          <div v-if="latestAbnormal.length === 0" class="empty-line">暂无异常告警</div>
        </div>
      </article>
    </section>

    <section class="situation-panel reveal" data-delay="4">
      <div class="panel-head compact-head">
        <div>
          <p>数据流</p>
          <h3>最近监测明细</h3>
        </div>
      </div>
      <div class="stream-table">
        <div class="stream-row stream-row--head">
          <span>患者</span>
          <span>类型</span>
          <span>数值</span>
          <span>风险</span>
          <span>设备</span>
          <span>时间</span>
        </div>
        <div v-for="item in latestMeasurements" :key="item.id" class="stream-row">
          <span>{{ item.patient_name }}</span>
          <span>{{ item.type_label }}</span>
          <span>{{ item.value }}</span>
          <span><i class="risk-pill" :data-risk="item.risk_level">{{ item.risk_label }}</i></span>
          <span>{{ item.device_id || '—' }}</span>
          <span>{{ formatDateTime(item.measured_at) }}</span>
        </div>
      </div>
    </section>
  </section>
</template>

<script setup>
import { computed } from 'vue';

const props = defineProps({
  data: { type: Object, default: () => ({}) }
});

const overview = computed(() => props.data?.overview || {});
const windowDays = computed(() => props.data?.window_days || 30);
const trend = computed(() => props.data?.trend || []);
const riskDistribution = computed(() => props.data?.risk_distribution || []);
const typeDistribution = computed(() => props.data?.type_distribution || []);
const patientRanking = computed(() => props.data?.patient_ranking || []);
const latestAbnormal = computed(() => props.data?.latest_abnormal || []);
const latestMeasurements = computed(() => props.data?.latest_measurements || []);

const metricCards = computed(() => [
  {
    label: '累计监测',
    value: formatNumber(overview.value.total_measurements),
    hint: `近${windowDays.value}天 ${formatNumber(overview.value.window_measurements)} 条`,
    tone: 'sage'
  },
  {
    label: '今日上传',
    value: formatNumber(overview.value.today_measurements),
    hint: '实时监测流入量',
    tone: 'jade'
  },
  {
    label: '异常预警',
    value: formatNumber(overview.value.abnormal_measurements),
    hint: `高危 ${formatNumber(overview.value.danger_measurements)} 条`,
    tone: 'amber'
  },
  {
    label: '活跃患者',
    value: formatNumber(overview.value.active_patients),
    hint: `共 ${formatNumber(overview.value.total_patients)} 名患者`,
    tone: 'coral'
  },
  {
    label: '在线设备',
    value: `${formatNumber(overview.value.online_devices)}/${formatNumber(overview.value.total_devices)}`,
    hint: '设备在线状态',
    tone: 'ink'
  }
]);

const maxTrendValue = computed(() => Math.max(1, ...trend.value.map(item => Math.max(item.total || 0, item.abnormal || 0))));
const totalLinePoints = computed(() => buildLinePoints('total'));
const abnormalLinePoints = computed(() => buildLinePoints('abnormal'));
const totalAreaPoints = computed(() => `${totalLinePoints.value} 100,56 0,56`);
const riskTotal = computed(() => riskDistribution.value.reduce((sum, item) => sum + (item.count || 0), 0));
const typeTotal = computed(() => typeDistribution.value.reduce((sum, item) => sum + (item.count || 0), 0));

function buildLinePoints(key) {
  if (trend.value.length === 0) return '0,50 100,50';
  return trend.value.map((item, index) => {
    const x = trend.value.length === 1 ? 50 : (index / (trend.value.length - 1)) * 100;
    const y = 50 - ((item[key] || 0) / maxTrendValue.value) * 42;
    return `${x.toFixed(2)},${Math.max(6, y).toFixed(2)}`;
  }).join(' ');
}

function formatNumber(value) {
  return Number(value || 0).toLocaleString('zh-CN');
}

function percent(value, total) {
  if (!total) return 0;
  return Math.max(3, Math.round((Number(value || 0) / total) * 100));
}

function formatDateTime(value) {
  if (!value) return '暂无';
  const date = new Date(value);
  if (Number.isNaN(date.getTime())) return '暂无';
  const month = String(date.getMonth() + 1).padStart(2, '0');
  const day = String(date.getDate()).padStart(2, '0');
  const hour = String(date.getHours()).padStart(2, '0');
  const minute = String(date.getMinutes()).padStart(2, '0');
  return `${month}-${day} ${hour}:${minute}`;
}
</script>

<style scoped>
.situation-page {
  display: grid;
  gap: 22px;
}

.situation-hero {
  position: relative;
  overflow: hidden;
  display: grid;
  grid-template-columns: minmax(0, 1fr) 180px;
  gap: 28px;
  padding: 30px;
  border: 1px solid rgba(63, 125, 110, 0.22);
  border-radius: 30px;
  background:
    radial-gradient(circle at 82% 28%, rgba(63, 125, 110, 0.20), transparent 28%),
    linear-gradient(135deg, rgba(255, 254, 250, 0.96), rgba(239, 244, 240, 0.92));
  box-shadow: var(--shadow-lift);
}

.situation-hero::after {
  content: "";
  position: absolute;
  inset: 18px;
  border: 1px solid rgba(255, 255, 255, 0.72);
  border-radius: 24px;
  pointer-events: none;
}

.situation-kicker {
  margin: 0 0 10px;
  color: var(--sage-deep);
  font-family: var(--font-mono);
  font-size: 11px;
  font-weight: 700;
  letter-spacing: 0.26em;
}

.situation-hero h2 {
  margin: 0;
  max-width: 760px;
  font-family: var(--font-display);
  font-size: clamp(32px, 4vw, 52px);
  font-weight: 600;
  line-height: 1.05;
  letter-spacing: -0.04em;
}

.situation-copy {
  max-width: 680px;
  margin: 16px 0 0;
  color: var(--ink-soft);
  font-size: 15px;
}

.situation-orbit {
  position: relative;
  z-index: 1;
  width: 160px;
  height: 160px;
  align-self: center;
  justify-self: end;
  display: grid;
  place-items: center;
  border-radius: 50%;
  background: rgba(255, 254, 250, 0.62);
}

.situation-orbit span {
  position: absolute;
  inset: 8px;
  border-radius: 50%;
  border: 1px dashed rgba(63, 125, 110, 0.42);
  animation: orbitSpin 12s linear infinite;
}

.situation-orbit span:nth-child(2) {
  inset: 28px;
  border-color: rgba(199, 93, 79, 0.34);
  animation-direction: reverse;
  animation-duration: 8s;
}

.situation-orbit strong {
  font-family: var(--font-display);
  font-size: 34px;
  line-height: 1;
}

.situation-orbit em {
  position: absolute;
  bottom: 44px;
  color: var(--ink-mute);
  font-style: normal;
  font-size: 12px;
}

.situation-metrics {
  display: grid;
  grid-template-columns: repeat(5, minmax(0, 1fr));
  gap: 14px;
}

.situation-metric,
.situation-panel {
  border: 1px solid var(--hairline);
  border-radius: 22px;
  background: rgba(255, 254, 250, 0.84);
  box-shadow: var(--shadow-card);
}

.situation-metric {
  position: relative;
  overflow: hidden;
  padding: 18px;
}

.situation-metric::before {
  content: "";
  position: absolute;
  right: -26px;
  top: -26px;
  width: 82px;
  height: 82px;
  border-radius: 50%;
  background: rgba(63, 125, 110, 0.12);
}

.situation-metric[data-tone="amber"]::before { background: rgba(192, 137, 78, 0.16); }
.situation-metric[data-tone="coral"]::before { background: rgba(199, 93, 79, 0.14); }
.situation-metric[data-tone="jade"]::before { background: rgba(79, 140, 104, 0.14); }
.situation-metric[data-tone="ink"]::before { background: rgba(14, 30, 38, 0.10); }

.situation-metric span,
.panel-head p,
.type-item span,
.rank-item span,
.alert-main span {
  color: var(--ink-mute);
  font-size: 12px;
}

.situation-metric strong {
  display: block;
  margin: 8px 0 4px;
  font-family: var(--font-display);
  font-size: 30px;
  line-height: 1;
}

.situation-metric small {
  color: var(--ink-soft);
}

.situation-board,
.situation-lists {
  display: grid;
  grid-template-columns: minmax(0, 1.35fr) minmax(280px, 0.65fr);
  gap: 18px;
}

.situation-board {
  grid-template-columns: minmax(0, 1.3fr) minmax(260px, 0.62fr) minmax(280px, 0.72fr);
}

.situation-panel {
  padding: 20px;
}

.situation-panel--wide {
  min-width: 0;
}

.panel-head {
  display: flex;
  align-items: flex-start;
  justify-content: space-between;
  gap: 16px;
  margin-bottom: 16px;
}

.panel-head p,
.panel-head h3 {
  margin: 0;
}

.panel-head h3 {
  margin-top: 2px;
  font-family: var(--font-display);
  font-size: 22px;
  line-height: 1.2;
}

.panel-head > span {
  color: var(--ink-mute);
  font-family: var(--font-mono);
  font-size: 12px;
}

.trend-chart {
  width: 100%;
  height: 240px;
  padding: 6px 0;
  border-radius: 18px;
  background:
    linear-gradient(rgba(14, 30, 38, 0.045) 1px, transparent 1px),
    linear-gradient(90deg, rgba(14, 30, 38, 0.035) 1px, transparent 1px),
    linear-gradient(180deg, rgba(239, 244, 240, 0.76), rgba(255, 254, 250, 0.92));
  background-size: 100% 25%, 12.5% 100%, 100% 100%;
}

.trend-area {
  fill: rgba(63, 125, 110, 0.09);
  stroke: none;
}

.trend-line {
  fill: none;
  stroke-width: 1.9;
  stroke-linecap: round;
  stroke-linejoin: round;
  vector-effect: non-scaling-stroke;
}

.trend-line.total { stroke: url(#totalLine); }
.trend-line.abnormal { stroke: url(#abnormalLine); stroke-width: 1.35; }

.trend-legend {
  display: flex;
  flex-wrap: wrap;
  gap: 14px;
  margin-top: 12px;
  color: var(--ink-soft);
  font-size: 12px;
}

.dot {
  display: inline-block;
  width: 8px;
  height: 8px;
  margin-right: 6px;
  border-radius: 50%;
}

.dot.total { background: var(--sage); }
.dot.abnormal { background: var(--coral); }

.risk-stack,
.type-list,
.rank-list,
.alert-list {
  display: grid;
  gap: 12px;
}

.risk-row,
.type-item {
  display: grid;
  align-items: center;
  gap: 10px;
}

.risk-row {
  grid-template-columns: 48px minmax(0, 1fr) 52px;
}

.type-item {
  grid-template-columns: 76px minmax(0, 1fr) 54px;
}

.type-item strong,
.type-item span {
  display: block;
}

.type-item em,
.risk-row strong {
  text-align: right;
  font-family: var(--font-mono);
  font-style: normal;
}

.bar-track {
  overflow: hidden;
  height: 10px;
  border-radius: 999px;
  background: var(--paper-deep);
}

.bar-track i {
  display: block;
  height: 100%;
  border-radius: inherit;
  background: linear-gradient(90deg, var(--sage), var(--amber));
}

.rank-item,
.alert-item,
.stream-row {
  display: grid;
  align-items: center;
  gap: 12px;
  padding: 12px;
  border: 1px solid var(--hairline-soft);
  border-radius: 16px;
  background: rgba(251, 248, 241, 0.64);
}

.rank-item {
  grid-template-columns: 34px minmax(0, 1fr) 74px;
}

.rank-item b {
  display: grid;
  place-items: center;
  width: 30px;
  height: 30px;
  border-radius: 10px;
  color: var(--paper);
  background: var(--sage);
}

.rank-item strong,
.alert-main strong {
  display: block;
}

.rank-item em {
  color: var(--sage-deep);
  font-style: normal;
  font-weight: 700;
  text-align: right;
}

.alert-item {
  grid-template-columns: 58px minmax(0, 1fr) 92px;
}

.alert-mark,
.risk-pill {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  border-radius: 999px;
  font-size: 12px;
  font-weight: 700;
}

.alert-mark {
  min-height: 30px;
  color: var(--amber);
  background: var(--amber-soft);
}

.alert-item[data-risk="danger"] .alert-mark,
.risk-pill[data-risk="danger"] {
  color: var(--coral);
  background: var(--coral-soft);
}

.risk-pill[data-risk="normal"] {
  color: var(--jade);
  background: var(--jade-soft);
}

.risk-pill[data-risk="warning"] {
  color: var(--amber);
  background: var(--amber-soft);
}

.alert-item time {
  color: var(--ink-mute);
  font-family: var(--font-mono);
  font-size: 12px;
  text-align: right;
}

.empty-line {
  padding: 20px;
  color: var(--ink-mute);
  text-align: center;
}

.stream-table {
  display: grid;
  gap: 8px;
}

.stream-row {
  grid-template-columns: 1fr 0.65fr 1fr 0.62fr 1fr 0.86fr;
}

.stream-row--head {
  color: var(--ink-mute);
  font-size: 12px;
  background: transparent;
}

.risk-pill {
  padding: 4px 9px;
}

@keyframes orbitSpin {
  to { transform: rotate(360deg); }
}

@media (max-width: 1180px) {
  .situation-metrics { grid-template-columns: repeat(2, minmax(0, 1fr)); }
  .situation-board,
  .situation-lists { grid-template-columns: 1fr; }
}

@media (max-width: 760px) {
  .situation-hero { grid-template-columns: 1fr; }
  .situation-orbit { justify-self: start; }
  .situation-metrics { grid-template-columns: 1fr; }
  .stream-row { grid-template-columns: 1fr 1fr; }
  .stream-row--head { display: none; }
  .alert-item { grid-template-columns: 1fr; }
  .alert-item time { text-align: left; }
}
</style>
