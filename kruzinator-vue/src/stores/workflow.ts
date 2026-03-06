import { computed, ref, watch } from 'vue'
import { defineStore } from 'pinia'

export type PromptItem = {
  key: string
  instruction: string
  captureLabel: string
}

type PersistedState = {
  consented: boolean
  userId: string | null
  sessionId: string | null
  protocolVersion: string
  promptPlan: PromptItem[]
  promptIndex: number
}

const STORAGE_KEY = 'kruzinator.workflow.v1'

function defaultPromptPlan(): PromptItem[] {
  return [
    { key: 'normal_cw', instruction: 'Draw a smooth circle clockwise at a normal speed.', captureLabel: 'normal_cw' },
    {
      key: 'normal_ccw',
      instruction: 'Draw a smooth circle counterclockwise at a normal speed.',
      captureLabel: 'normal_ccw',
    },
    { key: 'slow', instruction: 'Draw a circle slowly, keeping it smooth.', captureLabel: 'slow' },
    { key: 'fast', instruction: 'Draw a circle quickly, still aiming for smoothness.', captureLabel: 'fast' },
    { key: 'small', instruction: 'Draw a smaller circle in the center.', captureLabel: 'small' },
  ]
}

function safeParse(raw: string | null): PersistedState | null {
  if (!raw) return null
  try {
    const parsed = JSON.parse(raw) as PersistedState
    if (typeof parsed !== 'object' || !parsed) return null
    return parsed
  } catch {
    return null
  }
}

export const useWorkflowStore = defineStore('workflow', () => {
  const persisted = safeParse(localStorage.getItem(STORAGE_KEY))

  const consented = ref(persisted?.consented ?? false)
  const userId = ref<string | null>(persisted?.userId ?? null)
  const sessionId = ref<string | null>(persisted?.sessionId ?? null)
  const protocolVersion = ref(persisted?.protocolVersion ?? 'v1')
  const promptPlan = ref<PromptItem[]>(persisted?.promptPlan ?? defaultPromptPlan())
  const promptIndex = ref<number>(persisted?.promptIndex ?? 0)

  const currentPrompt = computed(() => promptPlan.value[promptIndex.value] ?? null)
  const isPromptPlanComplete = computed(() => promptIndex.value >= promptPlan.value.length)

  function persist() {
    const payload: PersistedState = {
      consented: consented.value,
      userId: userId.value,
      sessionId: sessionId.value,
      protocolVersion: protocolVersion.value,
      promptPlan: promptPlan.value,
      promptIndex: promptIndex.value,
    }
    localStorage.setItem(STORAGE_KEY, JSON.stringify(payload))
  }

  watch([consented, userId, sessionId, protocolVersion, promptPlan, promptIndex], persist, { deep: true })

  function resetAll() {
    consented.value = false
    userId.value = null
    sessionId.value = null
    protocolVersion.value = 'v1'
    promptPlan.value = defaultPromptPlan()
    promptIndex.value = 0
  }

  function resetCaptureProgress() {
    sessionId.value = null
    promptIndex.value = 0
  }

  function nextPrompt() {
    promptIndex.value += 1
  }

  function setUser(id: string) {
    userId.value = id
    sessionId.value = null
    promptIndex.value = 0
  }

  return {
    consented,
    userId,
    sessionId,
    protocolVersion,
    promptPlan,
    promptIndex,
    currentPrompt,
    isPromptPlanComplete,
    setUser,
    nextPrompt,
    resetCaptureProgress,
    resetAll,
  }
})
