import { useQuery } from '@tanstack/vue-query';
import { ElNotification } from 'element-plus';
import { ref, watch } from 'vue';

import { callEngine } from '../api/engineClient';
import { mapUnknownErrorMessage } from '../api/errorMapper';
import { useEngineStore } from '../stores/engineStore';
import type { EngineHealthResponse } from '../types/engine';

const ENGINE_HEALTH_QUERY_KEY = ['engine', 'health'] as const;
const HEALTH_REFETCH_INTERVAL_MS = 3_000;

export function useEngineHealth() {
  const engineStore = useEngineStore();
  const lastEngineErrorMessage = ref<string | null>(null);
  engineStore.setStarting();

  const query = useQuery({
    queryKey: ENGINE_HEALTH_QUERY_KEY,
    queryFn: () => callEngine<EngineHealthResponse>('engine.healthCheck', {}),
    refetchInterval: HEALTH_REFETCH_INTERVAL_MS,
    retry: 0,
  });

  watch(
    () => query.data.value,
    (health) => {
      if (health) {
        engineStore.setHealth(health);
        lastEngineErrorMessage.value = null;
      }
    },
    { immediate: true },
  );

  watch(
    () => query.error.value,
    (error) => {
      if (error) {
        const message = mapUnknownErrorMessage(error);
        engineStore.setError(message);

        if (lastEngineErrorMessage.value !== message) {
          ElNotification.warning({
            title: '下载引擎不可用',
            message,
          });
          lastEngineErrorMessage.value = message;
        }
      }
    },
    { immediate: true },
  );

  return query;
}
