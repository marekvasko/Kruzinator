<script setup lang="ts">
import { RouterView } from 'vue-router'
</script>

<template>
  <div class="app">
    <header class="app__header">
      <h1 class="app__title">Kruzinator</h1>
    </header>

    <main class="app__main" role="main">
      <RouterView />
    </main>
  </div>
</template>

<style>
html,
body {
  height: 100%;
}

body {
  margin: 0;
  font-family: system-ui, -apple-system, Segoe UI, Roboto, Helvetica, Arial, sans-serif;
  color: #111;
  background: #fff;
}

a {
  color: inherit;
}

.app {
  min-height: 100vh;
  display: flex;
  flex-direction: column;
}

.app__header {
  padding: 12px 16px;
  border-bottom: 1px solid #e5e5e5;
}

.app__title {
  margin: 0;
  font-size: 18px;
  line-height: 1.2;
}

.app__main {
  flex: 1;
  padding: 16px;
}

@media (min-width: 768px) {
  .app__main {
    max-width: 720px;
    margin: 0 auto;
  }
}
</style>
