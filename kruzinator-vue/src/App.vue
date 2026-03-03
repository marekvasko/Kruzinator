<script setup lang="ts">
import CircleCanvas from './components/CircleCanvas.vue'
</script>

<template>
  <main class="app">
    <section class="app__header">
      <h1>Circle Identification - Data Capture</h1>
      <p>Draw a smooth circle inside the guide ring to submit a datapoint.</p>
    </section>
    <CircleCanvas :width="320" :height="320" :show-debug="true" />
  </main>
</template>

<style scoped>
.app {
  min-height: 100vh;
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: flex-start;
  gap: 1.5rem;
  padding: 2rem 1.5rem 3rem;
  background: #f1f5f9;
  color: #0f172a;
}

.app__header {
  max-width: 520px;
  text-align: center;
}

.app__header h1 {
  font-size: 1.6rem;
  margin-bottom: 0.5rem;
}

.app__header p {
  margin: 0;
  color: #475569;
}
</style>
