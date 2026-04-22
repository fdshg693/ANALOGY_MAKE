export const MAIN_BRANCH_ID = 'main'

export function toLangGraphThreadId(threadId: string, branchId: string = MAIN_BRANCH_ID): string {
  if (branchId === MAIN_BRANCH_ID) return threadId
  return `${threadId}::${branchId}`
}
