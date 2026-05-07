<script setup lang="ts">
import { computed } from 'vue';

import { mapErrorMessage } from '../../../api/errorMapper';
import type { DownloadTask } from '../../../types/download';

const props = withDefaults(
  defineProps<{
    errorCode?: DownloadTask['errorCode'];
    errorMessage?: string | null;
    retryLoading?: boolean;
  }>(),
  {
    errorCode: null,
    errorMessage: null,
    retryLoading: false,
  },
);

const emit = defineEmits<{
  retry: [];
}>();

const message = computed(() => mapErrorMessage(props.errorCode, props.errorMessage));
</script>

<template>
  <el-alert type="error" :closable="false" show-icon>
    <div class="task-error-alert">
      <div>
        <strong>{{ message }}</strong>
        <p v-if="errorCode">错误码：{{ errorCode }}</p>
      </div>
      <el-button type="danger" plain size="small" :loading="retryLoading" @click="emit('retry')">
        重试
      </el-button>
    </div>
  </el-alert>
</template>

<style scoped lang="scss">
.task-error-alert {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 16px;
  width: 100%;
}

.task-error-alert p {
  margin: 4px 0 0;
  font-size: 12px;
}
</style>
