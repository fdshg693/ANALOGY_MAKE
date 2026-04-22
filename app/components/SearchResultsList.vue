<script setup lang="ts">
import type { SearchResult } from '~/composables/useChat'

defineProps<{ results: SearchResult[] }>()

function getDomain(url: string): string {
  try {
    return new URL(url).hostname.replace(/^www\./, '')
  } catch {
    return url
  }
}
</script>

<template>
  <details class="search-results">
    <summary>参考にした Web 検索結果 ({{ results.length }} 件)</summary>
    <ul>
      <li v-for="(r, i) in results" :key="i">
        <a :href="r.url" target="_blank" rel="noopener noreferrer">{{ r.title }}</a>
        <span class="domain">{{ getDomain(r.url) }}</span>
        <p class="snippet">{{ r.content }}</p>
      </li>
    </ul>
  </details>
</template>

<style scoped>
.search-results {
  margin: 0.5rem 0 0.75rem 0;
  padding: 0.5rem 0.75rem;
  background-color: #f9fafb;
  border: 1px solid #e5e7eb;
  border-radius: 0.5rem;
  font-size: 0.875rem;
  align-self: flex-start;
  max-width: 80%;
}
.search-results summary {
  cursor: pointer;
  font-weight: 500;
  color: #4b5563;
}
.search-results ul {
  list-style: none;
  padding: 0;
  margin: 0.5rem 0 0 0;
}
.search-results li {
  padding: 0.5rem 0;
  border-bottom: 1px solid #e5e7eb;
}
.search-results li:last-child {
  border-bottom: none;
}
.search-results a {
  color: #2563eb;
  text-decoration: none;
  font-weight: 500;
}
.search-results a:hover {
  text-decoration: underline;
}
.search-results .domain {
  color: #6b7280;
  font-size: 0.75rem;
  margin-left: 0.5rem;
}
.search-results .snippet {
  color: #4b5563;
  margin: 0.25rem 0 0 0;
  line-height: 1.4;
}
</style>
