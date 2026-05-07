<script setup lang="ts">
import { computed } from 'vue';

import type { Platform } from '../../../types/download';
import { detectPlatformFromUrl, getPlatformLabel, getPlatformTagType } from '../utils/platform';

const props = defineProps<{
  platform?: Platform | null;
  url?: string;
}>();

const detectedPlatform = computed(() => props.platform ?? detectPlatformFromUrl(props.url ?? ''));
const label = computed(() => getPlatformLabel(detectedPlatform.value));
const tagType = computed(() => getPlatformTagType(detectedPlatform.value));
</script>

<template>
  <el-tag :type="tagType" effect="light">
    {{ label }}
  </el-tag>
</template>
