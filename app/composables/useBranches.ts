export const MAIN_BRANCH_ID = 'main'

export interface Branch {
  branchId: string
  parentBranchId: string | null
  forkMessageIndex: number | null
  createdAt: string | null
}

interface BranchesResponse {
  branches: Branch[]
  activeBranchId: string
}

interface ForkResponse {
  branchId: string
  activeBranchId: string
}

export function useBranches() {
  const branches = ref<Branch[]>([
    { branchId: MAIN_BRANCH_ID, parentBranchId: null, forkMessageIndex: null, createdAt: null },
  ])
  const activeBranchId = ref<string>(MAIN_BRANCH_ID)

  async function loadBranches(threadId: string): Promise<void> {
    if (!threadId) {
      branches.value = [{ branchId: MAIN_BRANCH_ID, parentBranchId: null, forkMessageIndex: null, createdAt: null }]
      activeBranchId.value = MAIN_BRANCH_ID
      return
    }
    try {
      const data = await $fetch<BranchesResponse>(`/api/chat/branches`, {
        params: { threadId },
      })
      branches.value = data.branches
      activeBranchId.value = data.activeBranchId
    } catch {
      branches.value = [{ branchId: MAIN_BRANCH_ID, parentBranchId: null, forkMessageIndex: null, createdAt: null }]
      activeBranchId.value = MAIN_BRANCH_ID
    }
  }

  async function setActiveBranch(threadId: string, branchId: string): Promise<void> {
    activeBranchId.value = branchId
    try {
      await $fetch(`/api/threads/${threadId}/settings`, {
        method: 'PUT',
        body: { activeBranchId: branchId },
      })
    } catch {
      // 永続化失敗時もメモリ上は切替済み。次回リロードで DB 状態に戻る
    }
  }

  async function fork(params: {
    threadId: string
    fromBranchId: string
    forkMessageIndex: number
  }): Promise<string> {
    const data = await $fetch<ForkResponse>(`/api/chat/fork`, {
      method: 'POST',
      body: params,
    })
    activeBranchId.value = data.activeBranchId
    await loadBranches(params.threadId)
    return data.branchId
  }

  return { branches, activeBranchId, loadBranches, setActiveBranch, fork }
}
