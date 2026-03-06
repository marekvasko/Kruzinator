<script setup lang="ts">
import { onBeforeUnmount, onMounted, ref } from 'vue'
import type { Point } from '@/api/types'

type PointerEventWithAzimuth = PointerEvent & {
  azimuthAngle?: number
}

type Exposed = {
  reset: () => void
  getPoints: () => Point[]
  isDrawing: () => boolean
  getLastPointerType: () => string | null
  getCanvasCssSize: () => { width: number; height: number }
  getDpr: () => number
}

const props = withDefaults(
  defineProps<{
    disabled?: boolean
    ariaLabel?: string
  }>(),
  {
    disabled: false,
    ariaLabel: 'Circle drawing canvas',
  },
)

const canvasRef = ref<HTMLCanvasElement | null>(null)
const points = ref<Point[]>([])
const drawing = ref(false)
const lastPointerType = ref<string | null>(null)
let startTime: number | null = null
let resizeObserver: ResizeObserver | null = null

function getCtx(): CanvasRenderingContext2D | null {
  const c = canvasRef.value
  if (!c) return null
  return c.getContext('2d')
}

function clearCanvas() {
  const c = canvasRef.value
  const ctx = getCtx()
  if (!c || !ctx) return
  ctx.clearRect(0, 0, c.width, c.height)
}

function redraw() {
  const ctx = getCtx()
  if (!ctx) return

  clearCanvas()

  if (points.value.length < 2) return

  const first = points.value[0]!

  ctx.lineWidth = 3
  ctx.lineCap = 'round'
  ctx.lineJoin = 'round'
  ctx.strokeStyle = '#111'

  ctx.beginPath()
  ctx.moveTo(first.x, first.y)
  for (let i = 1; i < points.value.length; i += 1) {
    const p = points.value[i]!
    ctx.lineTo(p.x, p.y)
  }
  ctx.stroke()
}

function setCanvasSizeToCssPixels() {
  const c = canvasRef.value
  const ctx = getCtx()
  if (!c || !ctx) return

  const rect = c.getBoundingClientRect()
  const dpr = window.devicePixelRatio || 1

  const cssWidth = Math.max(1, Math.round(rect.width))
  const cssHeight = Math.max(1, Math.round(rect.height))

  c.width = Math.round(cssWidth * dpr)
  c.height = Math.round(cssHeight * dpr)

  // Draw in CSS pixel coordinates.
  ctx.setTransform(dpr, 0, 0, dpr, 0, 0)

  redraw()
}

function getPointFromEvent(e: PointerEvent): { x: number; y: number } {
  const c = canvasRef.value
  if (!c) return { x: 0, y: 0 }
  const rect = c.getBoundingClientRect()
  return {
    x: e.clientX - rect.left,
    y: e.clientY - rect.top,
  }
}

function pushPoint(e: PointerEvent) {
  if (startTime === null) return
  const { x, y } = getPointFromEvent(e)
  const tMs = Math.max(0, Math.round(performance.now() - startTime))

  const prev = points.value[points.value.length - 1]
  if (prev && prev.x === x && prev.y === y && prev.tMs === tMs) return

  points.value.push({
    x,
    y,
    tMs,
    pressure: typeof e.pressure === 'number' ? e.pressure : null,
    tiltX: typeof e.tiltX === 'number' ? e.tiltX : null,
    tiltY: typeof e.tiltY === 'number' ? e.tiltY : null,
    azimuth: typeof (e as PointerEventWithAzimuth).azimuthAngle === 'number' ? (e as PointerEventWithAzimuth).azimuthAngle : null,
  })
}

function onPointerDown(e: PointerEvent) {
  if (props.disabled) return
  const c = canvasRef.value
  if (!c) return

  lastPointerType.value = e.pointerType || null
  drawing.value = true
  points.value = []
  startTime = performance.now()

  c.setPointerCapture(e.pointerId)
  pushPoint(e)
  redraw()
}

function onPointerMove(e: PointerEvent) {
  if (props.disabled) return
  if (!drawing.value) return
  pushPoint(e)

  const ctx = getCtx()
  if (!ctx) return
  const len = points.value.length
  if (len < 2) return

  const a = points.value[len - 2]!
  const b = points.value[len - 1]!

  ctx.lineWidth = 3
  ctx.lineCap = 'round'
  ctx.lineJoin = 'round'
  ctx.strokeStyle = '#111'

  ctx.beginPath()
  ctx.moveTo(a.x, a.y)
  ctx.lineTo(b.x, b.y)
  ctx.stroke()
}

function endStroke() {
  drawing.value = false
  startTime = null
}

function onPointerUp() {
  if (props.disabled) return
  if (!drawing.value) return
  endStroke()
}

function onPointerCancel() {
  if (props.disabled) return
  if (!drawing.value) return
  endStroke()
}

function reset() {
  points.value = []
  drawing.value = false
  startTime = null
  clearCanvas()
}

function getPoints() {
  return points.value.slice()
}

function isDrawing() {
  return drawing.value
}

function getLastPointerType() {
  return lastPointerType.value
}

function getCanvasCssSize() {
  const c = canvasRef.value
  if (!c) return { width: 0, height: 0 }
  const rect = c.getBoundingClientRect()
  return { width: Math.round(rect.width), height: Math.round(rect.height) }
}

function getDpr() {
  return window.devicePixelRatio || 1
}

defineExpose<Exposed>({
  reset,
  getPoints,
  isDrawing,
  getLastPointerType,
  getCanvasCssSize,
  getDpr,
})

onMounted(() => {
  setCanvasSizeToCssPixels()

  const c = canvasRef.value
  if (c) {
    resizeObserver = new ResizeObserver(() => setCanvasSizeToCssPixels())
    resizeObserver.observe(c)
  }

  window.addEventListener('resize', setCanvasSizeToCssPixels)
})

onBeforeUnmount(() => {
  if (resizeObserver && canvasRef.value) resizeObserver.unobserve(canvasRef.value)
  resizeObserver = null
  window.removeEventListener('resize', setCanvasSizeToCssPixels)
})
</script>

<template>
  <div class="canvasWrap">
    <canvas
      ref="canvasRef"
      class="canvas"
      :aria-label="ariaLabel"
      role="img"
      @pointerdown.prevent="onPointerDown"
      @pointermove.prevent="onPointerMove"
      @pointerup.prevent="onPointerUp"
      @pointercancel.prevent="onPointerCancel"
    />
  </div>
</template>

<style scoped>
.canvasWrap {
  width: 100%;
  aspect-ratio: 1 / 1;
  border: 2px solid #111;
  border-radius: 12px;
  overflow: hidden;
  background: #fff;
}

.canvas {
  width: 100%;
  height: 100%;
  display: block;
  touch-action: none;
}
</style>
