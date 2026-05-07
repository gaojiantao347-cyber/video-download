<script setup lang="ts">
import { computed } from 'vue';

import type { WatermarkStatus } from '../../../types/download';
import { getWatermarkStatusMeta } from '../watermarkStatusMap';

const props = defineProps<{
  status: WatermarkStatus;
}>();

const meta = computed(() => getWatermarkStatusMeta(props.status));
</script>

<template>
  <el-tooltip :content="meta.description" placement="bottom">
    <el-tag :type="meta.tagType" effect="light">
      {{ meta.label }}
    </el-tag>
  </el-tooltip>
</template>
