<script setup lang="ts">
import { computed } from 'vue';
import { ElMessage } from 'element-plus';

import { mapUnknownErrorMessage } from '../api/errorMapper';
import { useEngineStore } from '../stores/engineStore';
import type { EngineConnectionStatus } from '../types/engine';

type TagType = 'primary' | 'success' | 'warning' | 'info' | 'danger';

const TAG_TYPE_MAP: Record<EngineConnectionStatus, TagType> = {
  starting: 'warning',
  ready: 'success',
  disconnected: 'info',
  error: 'danger',
};

const engineStore = useEngineStore();

const tagType = computed(() => TAG_TYPE_MAP[engineStore.status]);
const title = computed(() => engineStore.errorMessage || engineStore.statusText);
const canRestart = computed(
  () => engineStore.status === 'disconnected' || engineStore.status === 'error',
);

async function restartEngine(): Promise<void> {
  try {
    await engineStore.restartEngine();
    ElMessage.success('已请求重启引擎');
  } catch (error) {
    ElMessage.error(engineStore.errorMessage || mapUnknownErrorMessage(error));
  }
}
</script>

<template>
  <div class="engine-status">
    <el-tooltip :content="title" placement="bottom">
      <el-tag :type="tagType" effect="light" round>
        {{ engineStore.statusText }}
      </el-tag>
    </el-tooltip>

    <el-button
      v-if="canRestart"
      type="primary"
      size="small"
      text
      :loading="engineStore.restarting"
      @click="restartEngine"
    >
      重启引擎
    </el-button>
  </div>
</template>

<style scoped lang="scss">
.engine-status {
  display: inline-flex;
  align-items: center;
  gap: 8px;
}
</style>
