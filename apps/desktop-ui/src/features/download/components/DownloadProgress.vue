<script setup lang="ts">
import { computed } from 'vue';

import type { DownloadTaskStatus } from '../../../types/download';
import { getTaskStatusMeta } from '../taskStatusMap';

const props = defineProps<{
  status: DownloadTaskStatus;
  progress: number;
}>();

const meta = computed(() => getTaskStatusMeta(props.status));
const percentage = computed(() => Math.min(100, Math.max(0, Math.round(props.progress || 0))));
const indeterminate = computed(() => props.status === 'DOWNLOADING' && percentage.value === 0);
</script>

<template>
  <div class="download-progress">
    <div class="download-progress__header">
      <span>{{ meta.label }}</span>
      <span>{{ percentage }}%</span>
    </div>
    <el-progress
      :percentage="percentage"
      :status="meta.progressStatus"
      :indeterminate="indeterminate"
      :duration="3"
    />
    <p>{{ meta.description }}</p>
  </div>
</template>

<style scoped lang="scss">
.download-progress {
  display: grid;
  gap: 6px;
}

.download-progress__header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  color: #303133;
  font-size: 13px;
}

.download-progress p {
  margin: 0;
  color: #909399;
  font-size: 12px;
}
</style>
