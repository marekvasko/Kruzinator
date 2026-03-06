<script setup lang="ts">
import { computed, ref, watchEffect } from 'vue'
import { useRouter } from 'vue-router'
import { useMutation } from '@tanstack/vue-query'
import CircleCanvas from '@/components/CircleCanvas.vue'
import { kruzinatorApi } from '@/api/kruzinatorApi'
import type { DatapointCreate, SessionCreate } from '@/api/types'
import { useWorkflowStore } from '@/stores/workflow'

const router = useRouter()
const workflow = useWorkflowStore()

const canvasRef = ref<InstanceType<typeof CircleCanvas> | null>(null)

const prompt = computed(() => workflow.currentPrompt)
const stepText = computed(() => {
  const total = workflow.promptPlan.length
  const idx = workflow.promptIndex + 1
  return `${Math.min(idx, total)} of ${total}`
})

watchEffect(() => {
  if (workflow.isPromptPlanComplete) {
    router.replace({ name: 'review' })
  }
})

const createSessionMutation = useMutation({
  mutationFn: async (payload: SessionCreate) => kruzinatorApi.createSession(payload),
})

const createDatapointMutation = useMutation({
  mutationFn: async (payload: DatapointCreate) => kruzinatorApi.createDatapoint(payload),
})

const statusMessage = ref<string>('')

const canSave = computed(() => {
  const canvas = canvasRef.value
  if (!canvas) return false
  if (canvas.isDrawing()) return false
  return canvas.getPoints().length >= 10
})

async function ensureSession() {
  if (workflow.sessionId) return workflow.sessionId
  if (!workflow.userId) throw new Error('Missing userId')

  const session = await createSessionMutation.mutateAsync({
    user_id: workflow.userId,
    protocol_version: workflow.protocolVersion,
    prompt_plan: {
      prompts: workflow.promptPlan,
      createdAt: new Date().toISOString(),
    },
  })

  workflow.sessionId = session.id
  return session.id
}

async function saveAttempt() {
  const canvas = canvasRef.value
  if (!canvas) return
  if (!workflow.userId) return
  if (!prompt.value) return

  statusMessage.value = ''

  try {
    const sessionId = await ensureSession()
    const pts = canvas.getPoints()
    const cssSize = canvas.getCanvasCssSize()

    const payload: DatapointCreate = {
      user_id: workflow.userId,
      session_id: sessionId,
      capture_label: prompt.value.captureLabel,
      protocol_version: workflow.protocolVersion,
      metadata: {
        app: 'kruzinator-vue',
        captured_at: new Date().toISOString(),
        canvas: {
          cssWidth: cssSize.width,
          cssHeight: cssSize.height,
          dpr: canvas.getDpr(),
        },
        input: {
          pointerType: canvas.getLastPointerType(),
        },
        sampling: 'raw',
        userAgent: navigator.userAgent,
      },
      points: pts,
    }

    await createDatapointMutation.mutateAsync(payload)

    canvas.reset()
    workflow.nextPrompt()

    if (workflow.isPromptPlanComplete) {
      router.push({ name: 'review' })
    } else {
      statusMessage.value = 'Saved. Ready for the next circle.'
    }
  } catch {
    statusMessage.value = 'Failed to save. Check connection and try again.'
  }
}

function resetStroke() {
  canvasRef.value?.reset()
  statusMessage.value = ''
}

function goToReview() {
  router.push({ name: 'review' })
}
</script>

<template>
  <section aria-labelledby="capture-title">
    <h2 id="capture-title" style="margin-top: 0">Capture</h2>

    <div style="display: grid; gap: 10px; margin-bottom: 12px">
      <div style="display: flex; justify-content: space-between; gap: 10px">
        <div style="font-weight: 600">Step {{ stepText }}</div>
        <button type="button" @click="goToReview" style="padding: 8px 10px">Review</button>
      </div>
      <div
        v-if="prompt"
        style="padding: 12px; border: 1px solid #e5e5e5; border-radius: 10px"
        aria-live="polite"
      >
        {{ prompt.instruction }}
      </div>
    </div>

    <CircleCanvas ref="canvasRef" aria-label="Draw a circle" />

    <div style="display: grid; gap: 10px; margin-top: 12px">
      <button type="button" @click="resetStroke" style="width: 100%; padding: 12px; font-size: 16px">
        Reset
      </button>

      <button
        type="button"
        @click="saveAttempt"
        :disabled="!canSave || createDatapointMutation.isPending.value"
        style="width: 100%; padding: 14px 12px; font-size: 16px"
      >
        {{ createDatapointMutation.isPending.value ? 'Saving…' : 'Save This Circle' }}
      </button>

      <div aria-live="polite" style="min-height: 20px; font-size: 14px; color: #444">
        {{ statusMessage }}
      </div>

      <p style="margin: 0; color: #444; font-size: 14px">
        Tip: Keep your finger/stylus inside the box. If your browser scrolls, try again with one
        continuous stroke.
      </p>
    </div>

    <p v-if="createSessionMutation.isError.value" role="alert" style="color: #b00020">
      Failed to start session.
    </p>
  </section>
</template>
