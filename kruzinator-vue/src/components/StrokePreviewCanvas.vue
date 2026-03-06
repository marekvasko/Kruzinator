<script setup lang="ts">
import { onMounted, ref, watch } from 'vue'
import type { Point } from '@/api/types'

const props = defineProps<{
  points: Point[]
  ariaLabel?: string
}>()

const canvasRef = ref<HTMLCanvasElement | null>(null)

function setCanvasSizeToCssPixels() {
  const c = canvasRef.value
  if (!c) return
  const ctx = c.getContext('2d')
  if (!ctx) return

  const rect = c.getBoundingClientRect()
  const dpr = window.devicePixelRatio || 1

  const cssWidth = Math.max(1, Math.round(rect.width))
  const cssHeight = Math.max(1, Math.round(rect.height))

  c.width = Math.round(cssWidth * dpr)
  c.height = Math.round(cssHeight * dpr)

  ctx.setTransform(dpr, 0, 0, dpr, 0, 0)
}

function draw() {
  const c = canvasRef.value
  if (!c) return
  const ctx = c.getContext('2d')
  if (!ctx) return

  // Clear.
  ctx.clearRect(0, 0, c.width, c.height)

  if (!props.points || props.points.length < 2) return

  const first = props.points[0]!

  // Fit points into the canvas with padding.
  const xs = props.points.map((p) => p.x)
  const ys = props.points.map((p) => p.y)
  const minX = Math.min(...xs)
  const maxX = Math.max(...xs)
  const minY = Math.min(...ys)
  const maxY = Math.max(...ys)

  const cssW = c.getBoundingClientRect().width
  const cssH = c.getBoundingClientRect().height

  const pad = 10
  const w = Math.max(1, maxX - minX)
  const h = Math.max(1, maxY - minY)

  const scale = Math.min((cssW - pad * 2) / w, (cssH - pad * 2) / h)
  const offsetX = pad + (cssW - pad * 2 - w * scale) / 2
  const offsetY = pad + (cssH - pad * 2 - h * scale) / 2

  ctx.lineWidth = 2
  ctx.lineCap = 'round'
  ctx.lineJoin = 'round'
  ctx.strokeStyle = '#111'

  ctx.beginPath()
  ctx.moveTo(offsetX + (first.x - minX) * scale, offsetY + (first.y - minY) * scale)
  for (let i = 1; i < props.points.length; i += 1) {
    const p = props.points[i]!
    ctx.lineTo(offsetX + (p.x - minX) * scale, offsetY + (p.y - minY) * scale)
  }
  ctx.stroke()
}

onMounted(() => {
  setCanvasSizeToCssPixels()
  draw()
  window.addEventListener('resize', () => {
    setCanvasSizeToCssPixels()
    draw()
  })
})

watch(
  () => props.points,
  () => {
    setCanvasSizeToCssPixels()
    draw()
  },
  { deep: true },
)
</script>

<template>
  <div class="wrap">
    <canvas ref="canvasRef" class="canvas" :aria-label="ariaLabel ?? 'Stroke preview'" role="img" />
  </div>
</template>

<style scoped>
.wrap {
  width: 100%;
  aspect-ratio: 1 / 1;
  border: 1px solid #e5e5e5;
  border-radius: 12px;
  overflow: hidden;
  background: #fff;
}

.canvas {
  width: 100%;
  height: 100%;
  display: block;
}
</style>
