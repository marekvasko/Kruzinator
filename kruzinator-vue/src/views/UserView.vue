<script setup lang="ts">
import { computed, ref } from 'vue'
import { useRouter } from 'vue-router'
import { useMutation, useQuery } from '@tanstack/vue-query'
import { kruzinatorApi } from '@/api/kruzinatorApi'
import { useWorkflowStore } from '@/stores/workflow'

const router = useRouter()
const workflow = useWorkflowStore()

const existingUserId = ref(workflow.userId ?? '')

const uuidLike = computed(() => {
  const v = existingUserId.value.trim()
  return /^[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}$/i.test(v)
})

const userSummaryQuery = useQuery({
  queryKey: computed(() => ['user', existingUserId.value.trim()]),
  enabled: computed(() => uuidLike.value),
  queryFn: async () => kruzinatorApi.getUser(existingUserId.value.trim()),
})

const createUserMutation = useMutation({
  mutationFn: async () => kruzinatorApi.createUser(),
  onSuccess: (user) => {
    workflow.setUser(user.id)
    router.push({ name: 'capture' })
  },
})

function useExistingUser() {
  if (!uuidLike.value) return
  workflow.setUser(existingUserId.value.trim())
  router.push({ name: 'capture' })
}

const deleteConfirm = ref(false)
const deleteUserMutation = useMutation({
  mutationFn: async () => {
    if (!workflow.userId) return
    await kruzinatorApi.deleteUser(workflow.userId)
  },
  onSuccess: () => {
    deleteConfirm.value = false
    workflow.userId = null
    workflow.sessionId = null
    workflow.promptIndex = 0
    router.push({ name: 'user' })
  },
})
</script>

<template>
  <section aria-labelledby="user-title">
    <h2 id="user-title" style="margin-top: 0">User</h2>

    <p style="margin-top: 0">
      Create a pseudonymous user for this device, or enter an existing user ID.
    </p>

    <div style="display: grid; gap: 12px; margin: 16px 0">
      <button
        type="button"
        @click="createUserMutation.mutate()"
        :disabled="createUserMutation.isPending.value"
        style="width: 100%; padding: 14px 12px; font-size: 16px"
      >
        {{ createUserMutation.isPending.value ? 'Creating…' : 'Create New User' }}
      </button>

      <div style="border: 1px solid #e5e5e5; border-radius: 10px; padding: 12px">
        <label for="existing-user" style="display: block; font-weight: 600; margin-bottom: 6px">
          Existing user ID
        </label>
        <input
          id="existing-user"
          v-model="existingUserId"
          type="text"
          inputmode="text"
          autocomplete="off"
          autocapitalize="off"
          spellcheck="false"
          placeholder="xxxxxxxx-xxxx-xxxx-xxxx-xxxxxxxxxxxx"
          style="width: 100%; padding: 12px; font-size: 16px; box-sizing: border-box"
        />
        <div
          aria-live="polite"
          style="margin-top: 8px; font-size: 14px; color: #444"
        >
          <template v-if="uuidLike && userSummaryQuery.isFetching.value">Checking user…</template>
          <template v-else-if="uuidLike && userSummaryQuery.data.value">
            Found user with {{ userSummaryQuery.data.value.datapoints_count }} datapoints.
          </template>
          <template v-else-if="existingUserId.trim().length > 0 && !uuidLike">Enter a UUID.</template>
        </div>

        <button
          type="button"
          @click="useExistingUser"
          :disabled="!uuidLike"
          style="margin-top: 10px; width: 100%; padding: 12px; font-size: 16px"
        >
          Use This User
        </button>
      </div>
    </div>

    <div v-if="workflow.userId" style="border-top: 1px solid #e5e5e5; padding-top: 16px">
      <h3 style="margin: 0 0 8px 0; font-size: 16px">Data governance</h3>
      <p style="margin: 0 0 12px 0; color: #444; font-size: 14px">
        Delete removes this user and associated data from the backend.
      </p>

      <label style="display: flex; gap: 10px; align-items: flex-start; margin-bottom: 10px">
        <input v-model="deleteConfirm" type="checkbox" style="margin-top: 3px" />
        <span>I understand this cannot be undone.</span>
      </label>

      <button
        type="button"
        @click="deleteUserMutation.mutate()"
        :disabled="!deleteConfirm || deleteUserMutation.isPending.value"
        style="width: 100%; padding: 12px; font-size: 16px"
      >
        {{ deleteUserMutation.isPending.value ? 'Deleting…' : 'Delete Current User' }}
      </button>
    </div>

    <p v-if="createUserMutation.isError.value" role="alert" style="color: #b00020">
      Failed to create user.
    </p>
    <p v-if="deleteUserMutation.isError.value" role="alert" style="color: #b00020">
      Failed to delete user.
    </p>
  </section>
</template>
