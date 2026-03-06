<script setup lang="ts">
import { computed, ref, watch } from 'vue'
import { useRouter } from 'vue-router'
import { useMutation, useQuery, useQueryClient } from '@tanstack/vue-query'
import { kruzinatorApi } from '@/api/kruzinatorApi'
import type { Point, TagCreate, UUID } from '@/api/types'
import StrokePreviewCanvas from '@/components/StrokePreviewCanvas.vue'
import { useWorkflowStore } from '@/stores/workflow'

const router = useRouter()
const queryClient = useQueryClient()
const workflow = useWorkflowStore()

const userId = computed(() => workflow.userId as UUID)

function formatDate(v: string) {
  try {
    return new Date(v).toLocaleString()
  } catch {
    return v
  }
}

const userSummaryQuery = useQuery({
  queryKey: computed(() => ['user', userId.value]),
  enabled: computed(() => Boolean(workflow.userId)),
  queryFn: async () => kruzinatorApi.getUser(userId.value),
})

const datapointsQuery = useQuery({
  queryKey: computed(() => ['userDatapoints', userId.value]),
  enabled: computed(() => Boolean(workflow.userId)),
  queryFn: async () => kruzinatorApi.listUserDatapoints(userId.value),
})

const selectedDatapointId = ref<UUID | null>(null)

const datapointQuery = useQuery({
  queryKey: computed(() => ['datapoint', selectedDatapointId.value]),
  enabled: computed(() => Boolean(selectedDatapointId.value)),
  queryFn: async () => kruzinatorApi.getDatapoint(selectedDatapointId.value as UUID),
})

const rawQuery = useQuery({
  queryKey: computed(() => ['datapointRaw', selectedDatapointId.value]),
  enabled: computed(() => Boolean(selectedDatapointId.value)),
  queryFn: async () => kruzinatorApi.getDatapointRaw(selectedDatapointId.value as UUID),
})

function extractPointsFromRaw(raw: unknown): Point[] {
  const isRecord = (v: unknown): v is Record<string, unknown> => typeof v === 'object' && v !== null

  const looksLikePoint = (v: unknown): v is Point => {
    if (!isRecord(v)) return false
    return typeof v.x === 'number' && typeof v.y === 'number' && typeof v.tMs === 'number'
  }

  const asPointArray = (v: unknown): Point[] | null => {
    if (!Array.isArray(v)) return null
    if (v.length === 0) return []
    if (v.every(looksLikePoint)) return v as Point[]
    return null
  }

  const get = (obj: Record<string, unknown>, key: string): unknown => obj[key]

  if (!isRecord(raw)) return []

  const candidates: unknown[] = []
  candidates.push(get(raw, 'points'))

  const rawNested = get(raw, 'raw')
  if (isRecord(rawNested)) candidates.push(get(rawNested, 'points'))

  const dataNested = get(raw, 'data')
  if (isRecord(dataNested)) candidates.push(get(dataNested, 'points'))

  const strokeNested = get(raw, 'stroke')
  if (isRecord(strokeNested)) candidates.push(get(strokeNested, 'points'))

  for (const c of candidates) {
    const pts = asPointArray(c)
    if (pts) return pts
  }

  return []
}

const selectedPoints = computed<Point[]>(() => {
  const raw = rawQuery.data.value
  if (!raw) return []
  return extractPointsFromRaw(raw.raw)
})

const tag = ref('')
const note = ref('')

const addTagMutation = useMutation({
  mutationFn: async (payload: { datapointId: UUID; body: TagCreate }) =>
    kruzinatorApi.addTag(payload.datapointId, payload.body),
  onSuccess: async () => {
    tag.value = ''
    note.value = ''
    // No tags listing endpoint yet; just keep datapoints list fresh.
    await queryClient.invalidateQueries({ queryKey: ['userDatapoints', userId.value] })
  },
})

function selectDatapoint(id: UUID) {
  selectedDatapointId.value = id
}

watch(
  () => datapointsQuery.data.value,
  (items) => {
    if (!items || items.length === 0) {
      selectedDatapointId.value = null
      return
    }
    if (!selectedDatapointId.value) selectedDatapointId.value = items[0]!.id
  },
)

function backToCapture() {
  router.push({ name: 'capture' })
}

function switchUser() {
  workflow.userId = null
  workflow.sessionId = null
  workflow.promptIndex = 0
  router.push({ name: 'user' })
}

async function addTag() {
  if (!selectedDatapointId.value) return
  await addTagMutation.mutateAsync({
    datapointId: selectedDatapointId.value,
    body: { tag: tag.value || null, note: note.value || null },
  })
}
</script>

<template>
  <section aria-labelledby="review-title">
    <h2 id="review-title" style="margin-top: 0">Review</h2>

    <div style="display: flex; gap: 10px; margin-bottom: 12px">
      <button type="button" @click="backToCapture" style="padding: 10px 12px">Back to Capture</button>
      <button type="button" @click="switchUser" style="padding: 10px 12px">Switch User</button>
    </div>

    <div aria-live="polite" style="margin-bottom: 12px; color: #444">
      <template v-if="userSummaryQuery.data.value">
        User has {{ userSummaryQuery.data.value.datapoints_count }} datapoints.
      </template>
      <template v-else-if="userSummaryQuery.isFetching.value">Loading user…</template>
    </div>

    <div style="display: grid; gap: 12px">
      <div style="border: 1px solid #e5e5e5; border-radius: 10px; padding: 12px">
        <div style="display: flex; justify-content: space-between; align-items: center; gap: 10px">
          <h3 style="margin: 0; font-size: 16px">Datapoints</h3>
          <button type="button" @click="datapointsQuery.refetch()" style="padding: 8px 10px">Refresh</button>
        </div>

        <div v-if="datapointsQuery.isFetching.value" style="color: #444; margin-top: 8px">Loading…</div>
        <div v-else-if="(datapointsQuery.data.value?.length ?? 0) === 0" style="margin-top: 8px">
          No datapoints yet. Capture a circle first.
        </div>

        <ol v-else style="padding-left: 18px; margin: 10px 0 0 0">
          <li
            v-for="dp in datapointsQuery.data.value"
            :key="dp.id"
            style="margin-bottom: 8px"
          >
            <button
              type="button"
              @click="selectDatapoint(dp.id)"
              :aria-current="dp.id === selectedDatapointId ? 'true' : 'false'"
              style="width: 100%; text-align: left; padding: 10px; border-radius: 10px"
            >
              <div style="font-weight: 600">{{ dp.capture_label || '(no label)' }}</div>
              <div style="font-size: 13px; color: #444">{{ formatDate(dp.created_at) }}</div>
            </button>
          </li>
        </ol>
      </div>

      <div v-if="selectedDatapointId" style="border: 1px solid #e5e5e5; border-radius: 10px; padding: 12px">
        <h3 style="margin: 0 0 8px 0; font-size: 16px">Selected datapoint</h3>

        <div style="display: grid; gap: 10px">
          <div style="font-size: 14px; color: #444">
            <template v-if="datapointQuery.data.value">
              ID: {{ datapointQuery.data.value.id }}
            </template>
          </div>

          <div v-if="rawQuery.isFetching.value" style="color: #444">Loading raw stroke…</div>
          <div v-else-if="selectedPoints.length === 0" style="color: #444">
            No raw points available for preview.
          </div>
          <StrokePreviewCanvas v-else :points="selectedPoints" aria-label="Stroke preview" />

          <form @submit.prevent="addTag" style="display: grid; gap: 10px">
            <div>
              <label for="tag" style="display: block; font-weight: 600; margin-bottom: 6px">Tag</label>
              <input
                id="tag"
                v-model="tag"
                type="text"
                autocomplete="off"
                style="width: 100%; padding: 12px; font-size: 16px; box-sizing: border-box"
              />
            </div>

            <div>
              <label for="note" style="display: block; font-weight: 600; margin-bottom: 6px">Note</label>
              <textarea
                id="note"
                v-model="note"
                rows="3"
                style="width: 100%; padding: 12px; font-size: 16px; box-sizing: border-box"
              />
            </div>

            <button
              type="submit"
              :disabled="addTagMutation.isPending.value"
              style="width: 100%; padding: 12px; font-size: 16px"
            >
              {{ addTagMutation.isPending.value ? 'Saving…' : 'Add Tag/Note' }}
            </button>

            <p v-if="addTagMutation.isError.value" role="alert" style="color: #b00020; margin: 0">
              Failed to add tag.
            </p>
          </form>
        </div>
      </div>
    </div>
  </section>
</template>
