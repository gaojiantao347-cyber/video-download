import { useQuery } from '@tanstack/vue-query';
import { computed, type Ref } from 'vue';

import { getDownloadTask } from '../api/downloadApi';
import { isRunningTaskStatus } from '../features/download/taskStatusMap';
import type { DownloadTask } from '../types/download';

const DOWNLOAD_TASK_REFETCH_INTERVAL_MS = 1_000;

export function useDownloadTask(taskId: Ref<string | null>) {
  return useQuery<DownloadTask>({
    queryKey: computed(() => ['download', 'task', taskId.value] as const),
    queryFn: () => {
      if (!taskId.value) {
        throw new Error('任务 ID 不能为空');
      }
      return getDownloadTask(taskId.value);
    },
    enabled: computed(() => Boolean(taskId.value)),
    refetchInterval: (query) => {
      const task = query.state.data;
      return task && isRunningTaskStatus(task.status) ? DOWNLOAD_TASK_REFETCH_INTERVAL_MS : false;
    },
    retry: 0,
  });
}
