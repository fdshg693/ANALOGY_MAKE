import { ref } from 'vue'
import type { Ref } from 'vue'

export interface Thread {
  threadId: string
  title: string
  createdAt: string
  updatedAt: string
}

const ACTIVE_THREAD_KEY = 'analogy-threadId'

// モジュールスコープでシングルトン的に状態管理
const threads: Ref<Thread[]> = ref([])
const activeThreadId: Ref<string> = ref('')
const isLoadingThreads: Ref<boolean> = ref(false)

export function useThreads() {
  /** サーバーからスレッド一覧を取得 */
  async function loadThreads(): Promise<void> {
    isLoadingThreads.value = true
    try {
      const res = await fetch('/api/threads')
      const data = await res.json()
      threads.value = data.threads
    } catch {
      // サイレントに無視（空リストのまま）
    } finally {
      isLoadingThreads.value = false
    }
  }

  /** 新しいスレッドを作成し、アクティブにする。新しいthreadIdを返す */
  function createNewThread(): string {
    const newId = crypto.randomUUID()
    threads.value.unshift({
      threadId: newId,
      title: '新しいチャット',
      createdAt: new Date().toISOString(),
      updatedAt: new Date().toISOString(),
    })
    activeThreadId.value = newId
    if (import.meta.client) {
      localStorage.setItem(ACTIVE_THREAD_KEY, newId)
    }
    return newId
  }

  /** アクティブスレッドを切り替える */
  function setActiveThread(threadId: string): void {
    activeThreadId.value = threadId
    if (import.meta.client) {
      localStorage.setItem(ACTIVE_THREAD_KEY, threadId)
    }
  }

  /** 初期化: localStorageからアクティブスレッドを復元 */
  function initActiveThread(): void {
    if (import.meta.client) {
      const stored = localStorage.getItem(ACTIVE_THREAD_KEY)
      if (stored) {
        activeThreadId.value = stored
      }
    }
  }

  /** スレッドタイトルをローカルに更新（サーバーからの通知を反映） */
  function updateLocalTitle(threadId: string, title: string): void {
    const thread = threads.value.find(t => t.threadId === threadId)
    if (thread) {
      thread.title = title
    }
  }

  return {
    threads,
    activeThreadId,
    isLoadingThreads,
    loadThreads,
    createNewThread,
    setActiveThread,
    initActiveThread,
    updateLocalTitle,
  }
}
