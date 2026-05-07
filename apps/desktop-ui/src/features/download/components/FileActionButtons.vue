<script setup lang="ts">
import { computed, ref } from 'vue';
import { ElMessage } from 'element-plus';

import { mapUnknownErrorMessage } from '../../../api/errorMapper';
import { openDownloadFile, revealDownloadFile } from '../../../api/fileApi';

const props = withDefaults(
  defineProps<{
    taskId: string;
    disabled?: boolean;
  }>(),
  {
    disabled: false,
  },
);

const openingFile = ref(false);
const revealingFile = ref(false);
const canUseTask = computed(() => Boolean(props.taskId) && !props.disabled);

async function openFile(): Promise<void> {
  if (!props.taskId) {
    return;
  }

  openingFile.value = true;
  try {
    await openDownloadFile(props.taskId);
  } catch (error) {
    ElMessage.error(mapUnknownErrorMessage(error));
  } finally {
    openingFile.value = false;
  }
}

async function revealFile(): Promise<void> {
  if (!props.taskId) {
    return;
  }

  revealingFile.value = true;
  try {
    await revealDownloadFile(props.taskId);
  } catch (error) {
    ElMessage.error(mapUnknownErrorMessage(error));
  } finally {
    revealingFile.value = false;
  }
}
</script>

<template>
  <div class="file-action-buttons">
    <el-button :disabled="!canUseTask" :loading="openingFile" @click="openFile">
      打开文件
    </el-button>
    <el-button :disabled="!canUseTask" :loading="revealingFile" @click="revealFile">
      打开所在目录
    </el-button>
  </div>
</template>

<style scoped lang="scss">
.file-action-buttons {
  display: flex;
  flex-wrap: wrap;
  gap: 8px;
}
</style>
