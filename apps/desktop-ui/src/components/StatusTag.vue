<script setup lang="ts">
import { computed } from 'vue';

import { getTaskStatusMeta } from '../features/download/taskStatusMap';
import type { DownloadTaskStatus } from '../types/download';

const props = defineProps<{
  status: DownloadTaskStatus;
}>();

const meta = computed(() => getTaskStatusMeta(props.status));
</script>

<template>
  <el-tooltip :content="meta.description" placement="bottom">
    <el-tag :type="meta.tagType" effect="light" round>
      <el-icon class="status-tag__icon">
        <component :is="meta.icon" />
      </el-icon>
      {{ meta.label }}
    </el-tag>
  </el-tooltip>
</template>

<style scoped lang="scss">
.status-tag__icon {
  margin-right: 4px;
}
</style>
