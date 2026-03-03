<script setup lang="ts">
import { computed, onMounted, ref, watch } from 'vue'
import type {
  CanvasMeta,
  CircleCanvasEmits,
  CircleCanvasExposed,
  CircleCanvasProps,
  CircleCanvasState,
  ExportOptions,
  StrokeMetrics,
  StrokePayload,
  StrokePoint,
  ValidationConfig,
  ValidationIssue,
  ValidationResult,
} from './CircleCanvas.types'

const props = withDefaults(defineProps<CircleCanvasProps>(), {
  dpr: undefined,
  disabled: false,
  readOnly: false,
  capturePointer: true,
  sampling: undefined,
  smoothing: undefined,
  validation: undefined,
  showGuide: true,
  guideRadiusPx: undefined,
  showLivePath: true,
  showDebug: false,
  initialStroke: undefined,
  maxStrokeMs: undefined,
  maxPoints: undefined,
})

const emit = defineEmits<CircleCanvasEmits>()

const canvasRef = ref<HTMLCanvasElement | null>(null)
const points = ref<StrokePoint[]>([])
const metrics = ref<StrokeMetrics | null>(null)
const startTime = ref<number | null>(null)
const state = ref<CircleCanvasState>(props.disabled ? 'disabled' : 'idle')
const dirty = ref(false)

const resolvedDpr = computed(() => props.dpr ?? (typeof window !== 'undefined' ? window.devicePixelRatio : 1))
const internalWidth = computed(() => Math.round(props.width * resolvedDpr.value))
const internalHeight = computed(() => Math.round(props.height * resolvedDpr.value))

const defaultValidation: ValidationConfig = {
  minPoints: 60,
  minDurationMs: 400,
  maxDurationMs: 12000,
  requireClosed: true,
  closedThresholdPx: 24,
  minPathLengthPx: undefined,
}

const validationConfig = computed(() => ({ ...defaultValidation, ...props.validation }))

const getMeta = (): CanvasMeta => ({
  widthPx: props.width,
  heightPx: props.height,
  dpr: resolvedDpr.value,
})

const setState = (next: CircleCanvasState) => {
  state.value = next
  emit('state', { state: next })
}

const resetCanvas = () => {
  const canvas = canvasRef.value
  if (!canvas) return
  canvas.width = internalWidth.value
  canvas.height = internalHeight.value
  canvas.style.width = `${props.width}px`
  canvas.style.height = `${props.height}px`
  renderCanvas()
}

const renderCanvas = () => {
  const canvas = canvasRef.value
  if (!canvas) return
  const ctx = canvas.getContext('2d')
  if (!ctx) return
  ctx.setTransform(resolvedDpr.value, 0, 0, resolvedDpr.value, 0, 0)
  ctx.clearRect(0, 0, props.width, props.height)
  if (props.showGuide) {
    const radius = props.guideRadiusPx ?? Math.min(props.width, props.height) / 2 - 12
    ctx.beginPath()
    ctx.strokeStyle = '#cbd5f5'
    ctx.lineWidth = 2
    ctx.setLineDash([6, 6])
    ctx.arc(props.width / 2, props.height / 2, Math.max(radius, 8), 0, Math.PI * 2)
    ctx.stroke()
    ctx.setLineDash([])
  }
  if (points.value.length > 1 && props.showLivePath) {
    const [first, ...rest] = points.value
    if (!first) return
    ctx.beginPath()
    ctx.strokeStyle = '#1f2937'
    ctx.lineWidth = 2
    ctx.moveTo(first.x, first.y)
    for (const point of rest) {
      ctx.lineTo(point.x, point.y)
    }
    ctx.stroke()
  }
}

const getCanvasPoint = (event: PointerEvent, type: StrokePoint['type']): StrokePoint | null => {
  const canvas = canvasRef.value
  if (!canvas || startTime.value === null) return null
  const rect = canvas.getBoundingClientRect()
  const x = event.clientX - rect.left
  const y = event.clientY - rect.top
  const tMs = Math.max(0, Math.round(performance.now() - startTime.value))
  const point: StrokePoint = { x, y, tMs, type }
  if (event.pressure !== undefined) {
    point.pressure = event.pressure
  }
  if (event.tiltX !== undefined) {
    point.tiltX = event.tiltX
  }
  if (event.tiltY !== undefined) {
    point.tiltY = event.tiltY
  }
  if (event.azimuthAngle !== undefined) {
    point.azimuth = event.azimuthAngle
  }
  return point
}

const pushPoint = (point: StrokePoint) => {
  if (props.maxPoints && points.value.length >= props.maxPoints) {
    emit('error', { code: 'MAX_POINTS', message: 'Maximum point count reached.' })
    return
  }
  points.value.push(point)
  emit('stroke:point', { point, count: points.value.length })
  renderCanvas()
}

const computeMetrics = (stroke: StrokePoint[]): StrokeMetrics => {
  const first = stroke[0]
  if (!first) {
    return {
      durationMs: 0,
      points: 0,
      pathLengthPx: 0,
      avgSpeedPxPerS: 0,
    }
  }
  const last = stroke[stroke.length - 1] ?? first
  const durationMs = last.tMs
  let pathLengthPx = 0
  let maxSpeedPxPerS = 0
  for (let i = 1; i < stroke.length; i += 1) {
    const current = stroke[i]
    const previous = stroke[i - 1]
    if (!current || !previous) continue
    const dx = current.x - previous.x
    const dy = current.y - previous.y
    const dt = Math.max(1, current.tMs - previous.tMs)
    const dist = Math.hypot(dx, dy)
    pathLengthPx += dist
    maxSpeedPxPerS = Math.max(maxSpeedPxPerS, (dist / dt) * 1000)
  }
  const closedDistancePx =
    stroke.length > 1 ? Math.hypot(last.x - first.x, last.y - first.y) : undefined
  const avgSpeedPxPerS = durationMs > 0 ? (pathLengthPx / durationMs) * 1000 : 0
  return {
    durationMs,
    points: stroke.length,
    pathLengthPx,
    avgSpeedPxPerS,
    maxSpeedPxPerS,
    closedDistancePx,
  }
}

const validate = (): ValidationResult => {
  const config = validationConfig.value
  const strokeMetrics = metrics.value ?? computeMetrics(points.value)
  const issues: ValidationIssue[] = []

  if (points.value.length < config.minPoints) {
    issues.push({ code: 'TOO_FEW_POINTS', detail: `Need at least ${config.minPoints} points.` })
  }
  if (strokeMetrics.durationMs < config.minDurationMs) {
    issues.push({ code: 'TOO_SHORT', detail: `Need at least ${config.minDurationMs}ms.` })
  }
  if (config.maxDurationMs && strokeMetrics.durationMs > config.maxDurationMs) {
    issues.push({ code: 'TOO_LONG', detail: `Must be under ${config.maxDurationMs}ms.` })
  }
  if (config.requireClosed && strokeMetrics.closedDistancePx !== undefined) {
    if (strokeMetrics.closedDistancePx > config.closedThresholdPx) {
      issues.push({ code: 'NOT_CLOSED', detail: 'Stroke did not close the circle.' })
    }
  }
  if (config.minPathLengthPx && strokeMetrics.pathLengthPx < config.minPathLengthPx) {
    issues.push({ code: 'PATH_TOO_SHORT', detail: `Need path length ≥ ${config.minPathLengthPx}px.` })
  }

  return { ok: issues.length === 0, issues, metrics: strokeMetrics }
}

const exportPayload = (opts?: Partial<ExportOptions>): StrokePayload => {
  const strokeMetrics = metrics.value ?? computeMetrics(points.value)
  const payload: StrokePayload = {
    meta: getMeta(),
    points: [...points.value],
    metrics: strokeMetrics,
  }
  if (opts?.includePreview) {
    payload.previewPngBase64 = capturePreviewPngBase64()
  }
  return payload
}

const capturePreviewPngBase64 = (opts?: { scale?: number; quality?: number }): string => {
  const canvas = canvasRef.value
  if (!canvas) return ''
  const scale = opts?.scale ?? 1
  if (scale === 1) {
    return canvas.toDataURL('image/png', opts?.quality)
  }
  const scaled = document.createElement('canvas')
  scaled.width = Math.round(canvas.width * scale)
  scaled.height = Math.round(canvas.height * scale)
  const ctx = scaled.getContext('2d')
  if (!ctx) return ''
  ctx.drawImage(canvas, 0, 0, scaled.width, scaled.height)
  return scaled.toDataURL('image/png', opts?.quality)
}

const clear = () => {
  points.value = []
  metrics.value = null
  dirty.value = false
  startTime.value = null
  setState(props.disabled ? 'disabled' : 'idle')
  renderCanvas()
  emit('cleared')
}

const cancelStroke = () => {
  if (state.value !== 'drawing') return
  const point = getCanvasPoint(new PointerEvent('pointercancel'), 'cancel')
  if (point) {
    pushPoint(point)
  }
  metrics.value = computeMetrics(points.value)
  setState('invalid')
}

const endStroke = (type: StrokePoint['type'], event: PointerEvent) => {
  if (state.value !== 'drawing') return
  const point = getCanvasPoint(event, type)
  if (point) {
    pushPoint(point)
  }
  metrics.value = computeMetrics(points.value)
  const validation = validate()
  emit('stroke:validated', validation)
  setState(validation.ok ? 'completed' : 'invalid')
  emit('stroke:end', { payload: exportPayload() })
}

const onPointerDown = (event: PointerEvent) => {
  if (props.disabled || props.readOnly) return
  dirty.value = true
  points.value = []
  metrics.value = null
  startTime.value = performance.now()
  setState('drawing')
  const point = getCanvasPoint(event, 'down')
  if (point) {
    pushPoint(point)
  }
  if (props.capturePointer && event.target instanceof HTMLElement) {
    event.target.setPointerCapture(event.pointerId)
  }
  emit('stroke:start', { meta: getMeta() })
}

const onPointerMove = (event: PointerEvent) => {
  if (state.value !== 'drawing') return
  if (props.maxStrokeMs && startTime.value) {
    const elapsed = performance.now() - startTime.value
    if (elapsed > props.maxStrokeMs) {
      endStroke('cancel', event)
      return
    }
  }
  const point = getCanvasPoint(event, 'move')
  if (point) {
    pushPoint(point)
  }
}

const onPointerUp = (event: PointerEvent) => {
  endStroke('up', event)
}

const onPointerCancel = (event: PointerEvent) => {
  endStroke('cancel', event)
}

const setStroke = (stroke: StrokePoint[]) => {
  points.value = [...stroke]
  metrics.value = computeMetrics(points.value)
  setState(points.value.length ? 'completed' : 'idle')
  renderCanvas()
}

watch(
  () => props.initialStroke,
  (stroke) => {
    if (stroke) {
      setStroke(stroke)
    }
  },
  { deep: true }
)

watch(
  () => props.disabled,
  (disabled) => {
    setState(disabled ? 'disabled' : 'idle')
  }
)

watch([internalWidth, internalHeight, () => props.showGuide, () => props.showLivePath], () => {
  resetCanvas()
})

onMounted(() => {
  resetCanvas()
})

defineExpose<CircleCanvasExposed>({
  getState: () => state.value,
  isDirty: () => dirty.value,
  canSubmit: () => state.value === 'completed',
  clear,
  cancelStroke,
  getStroke: () => [...points.value],
  getMetrics: () => metrics.value,
  validate,
  exportPayload,
  capturePreviewPngBase64,
  setStroke,
})
</script>

<template>
  <div class="circle-canvas">
    <canvas
      ref="canvasRef"
      class="circle-canvas__surface"
      :style="{ width: `${props.width}px`, height: `${props.height}px` }"
      @pointerdown="onPointerDown"
      @pointermove="onPointerMove"
      @pointerup="onPointerUp"
      @pointercancel="onPointerCancel"
    />
    <div v-if="showDebug" class="circle-canvas__debug">
      <div>State: {{ state }}</div>
      <div>Points: {{ points.length }}</div>
      <div>Duration: {{ metrics?.durationMs ?? 0 }}ms</div>
    </div>
  </div>
</template>

<style scoped>
.circle-canvas {
  display: inline-flex;
  flex-direction: column;
  align-items: flex-start;
  gap: 0.5rem;
}

.circle-canvas__surface {
  touch-action: none;
  border: 2px solid #e2e8f0;
  border-radius: 16px;
  background: #f8fafc;
}

.circle-canvas__debug {
  font-size: 0.75rem;
  color: #475569;
}
</style>
