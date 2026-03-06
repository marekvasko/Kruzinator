<script setup lang="ts">
import { computed, ref } from 'vue'
import { useRouter } from 'vue-router'
import { useWorkflowStore } from '@/stores/workflow'

const router = useRouter()
const workflow = useWorkflowStore()

const accepted = ref(workflow.consented)

const canContinue = computed(() => accepted.value)

function continueNext() {
  if (!accepted.value) return
  workflow.consented = true
  if (workflow.userId) {
    router.push({ name: 'capture' })
  } else {
    router.push({ name: 'user' })
  }
}
</script>

<template>
  <section aria-labelledby="consent-title">
    <h2 id="consent-title" style="margin-top: 0">Consent</h2>

    <p>
      Kruzinator collects circle-drawing gesture telemetry (timing and pointer movement) to build a
      dataset for later analysis.
    </p>

    <ul>
      <li>What we collect: stroke points (x/y/time) and optional pressure/tilt when available.</li>
      <li>What it’s for: creating a behavioral signature dataset (not account identity).</li>
      <li>Controls: you can stop, and you can delete your user data via the app.</li>
    </ul>

    <div style="margin: 16px 0">
      <label style="display: flex; gap: 10px; align-items: flex-start">
        <input
          v-model="accepted"
          type="checkbox"
          aria-describedby="consent-help"
          style="margin-top: 3px"
        />
        <span>
          I understand and consent to collecting gesture telemetry for dataset creation.
          <span id="consent-help" style="display: block; color: #444; font-size: 14px; margin-top: 4px">
            This app is intended for data collection. Avoid entering personal information.
          </span>
        </span>
      </label>
    </div>

    <button
      type="button"
      :disabled="!canContinue"
      @click="continueNext"
      style="width: 100%; padding: 14px 12px; font-size: 16px"
    >
      Continue
    </button>
  </section>
</template>
