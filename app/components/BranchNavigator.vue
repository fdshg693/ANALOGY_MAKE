<script setup lang="ts">
import type { Branch } from '~/composables/useBranches'
import { MAIN_BRANCH_ID } from '~/composables/useBranches'

const props = defineProps<{
  branches: Branch[]
  activeBranchId: string
  forkMessageIndex: number
}>()

const emit = defineEmits<{
  'change-branch': [branchId: string]
}>()

const group = computed<Branch[]>(() => {
  const siblings = props.branches.filter(
    (b) => b.forkMessageIndex === props.forkMessageIndex,
  )
  const hasMainAlready = siblings.some((b) => b.branchId === MAIN_BRANCH_ID)
  if (hasMainAlready) return siblings
  const main = props.branches.find((b) => b.branchId === MAIN_BRANCH_ID)
  return main ? [main, ...siblings] : siblings
})

const activeIndex = computed<number>(() => {
  const idx = group.value.findIndex((b) => b.branchId === props.activeBranchId)
  return idx >= 0 ? idx : 0
})

const hasPrev = computed(() => activeIndex.value > 0)
const hasNext = computed(() => activeIndex.value < group.value.length - 1)

function go(delta: number) {
  const next = group.value[activeIndex.value + delta]
  if (next) emit('change-branch', next.branchId)
}
</script>

<template>
  <div v-if="group.length > 1" class="branch-nav">
    <button
      type="button"
      class="branch-nav-btn"
      :disabled="!hasPrev"
      aria-label="前の分岐"
      @click="go(-1)"
    >&#9664;</button>
    <span class="branch-nav-counter">{{ activeIndex + 1 }} / {{ group.length }}</span>
    <button
      type="button"
      class="branch-nav-btn"
      :disabled="!hasNext"
      aria-label="次の分岐"
      @click="go(1)"
    >&#9654;</button>
  </div>
</template>

<style scoped>
.branch-nav {
  display: inline-flex;
  align-items: center;
  gap: 0.25rem;
  margin-top: 0.25rem;
  font-size: 0.75rem;
  color: #6b7280;
  user-select: none;
}

.branch-nav-btn {
  background: none;
  border: 1px solid #d1d5db;
  border-radius: 0.25rem;
  padding: 0 0.4rem;
  line-height: 1.5;
  font-size: 0.7rem;
  cursor: pointer;
  color: #374151;
}

.branch-nav-btn:hover:not(:disabled) {
  background: #f3f4f6;
}

.branch-nav-btn:disabled {
  opacity: 0.4;
  cursor: not-allowed;
}

.branch-nav-counter {
  min-width: 2.5rem;
  text-align: center;
}
</style>
