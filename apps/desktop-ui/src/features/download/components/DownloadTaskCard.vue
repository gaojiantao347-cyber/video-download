<script setup lang="ts">
import { computed } from 'vue';

import StatusTag from '../../../components/StatusTag.vue';
import { mapErrorMessage } from '../../../api/errorMapper';
import type { DownloadTask } from '../../../types/download';
import DownloadProgress from './DownloadProgress.vue';
import FileActionButtons from './FileActionButtons.vue';
import PlatformBadge from './PlatformBadge.vue';
import TaskErrorAlert from './TaskErrorAlert.vue';
import WatermarkStatusTag from './WatermarkStatusTag.vue';

const props = withDefaults(
  defineProps<{
    task: DownloadTask;
    headerLabel?: string;
    retryLoading?: boolean;
  }>(),
  {
    headerLabel: '当前任务',
    retryLoading: false,
  },
);

const emit = defineEmits<{
  retry: [];
}>();

const title = computed(() => props.task.title || '视频信息解析中');
const author = computed(() => props.task.author || '作者信息待解析');
const fileName = computed(() => props.task.fileName || '文件名待生成');
const showError = computed(
  () => props.task.status === 'FAILED' || Boolean(props.task.errorCode || props.task.errorMessage),
);
const errorTitle = computed(() => mapErrorMessage(props.task.errorCode, props.task.errorMessage));
</script>

<template>
  <el-card shadow="never" class="download-task-card">
    <template #header>
      <div class="task-card-header">
        <div>
          <span class="task-card-header__label">{{ headerLabel }}</span>
          <p>{{ task.taskId }}</p>
        </div>
        <StatusTag :status="task.status" />
      </div>
    </template>

    <div class="task-body">
      <el-image v-if="task.coverUrl" class="task-cover" :src="task.coverUrl" fit="cover" />
      <div v-else class="task-cover task-cover--empty">暂无封面</div>

      <div class="task-content">
        <div class="task-title-row">
          <div>
            <h3>{{ title }}</h3>
            <p>{{ author }}</p>
          </div>
          <PlatformBadge :platform="task.platform" :url="task.sourceUrl" />
        </div>

        <div class="task-meta-grid">
          <div>
            <span>文件名</span>
            <strong>{{ fileName }}</strong>
          </div>
          <div>
            <span>去水印</span>
            <WatermarkStatusTag :status="task.watermarkStatus" />
          </div>
        </div>

        <DownloadProgress :status="task.status" :progress="task.progress" />

        <TaskErrorAlert
          v-if="showError"
          :error-code="task.errorCode"
          :error-message="errorTitle"
          :retry-loading="retryLoading"
          @retry="emit('retry')"
        />

        <div v-if="task.status === 'SUCCESS'" class="task-actions">
          <FileActionButtons :task-id="task.taskId" />
        </div>
      </div>
    </div>
  </el-card>
</template>

<style scoped lang="scss">
.download-task-card {
  border-radius: 12px;
}

.task-card-header,
.task-title-row {
  display: flex;
  align-items: flex-start;
  justify-content: space-between;
  gap: 16px;
}

.task-card-header__label {
  font-weight: 600;
}

.task-card-header p,
.task-title-row p {
  margin: 4px 0 0;
  color: #909399;
  font-size: 12px;
}

.task-body {
  display: grid;
  grid-template-columns: 180px minmax(0, 1fr);
  gap: 16px;
}

.task-cover {
  width: 180px;
  height: 112px;
  overflow: hidden;
  border-radius: 10px;
  background: #f5f7fa;
}

.task-cover--empty {
  display: grid;
  place-items: center;
  color: #909399;
  font-size: 13px;
}

.task-content {
  display: grid;
  gap: 14px;
  min-width: 0;
}

.task-title-row h3 {
  margin: 0;
  color: #303133;
  font-size: 18px;
}

.task-meta-grid {
  display: grid;
  grid-template-columns: repeat(2, minmax(0, 1fr));
  gap: 12px;
}

.task-meta-grid div {
  display: grid;
  gap: 6px;
  min-width: 0;
}

.task-meta-grid span {
  color: #909399;
  font-size: 12px;
}

.task-meta-grid strong {
  overflow: hidden;
  color: #303133;
  font-size: 13px;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.task-actions {
  display: flex;
  justify-content: flex-end;
}

@media (max-width: 820px) {
  .task-body {
    grid-template-columns: 1fr;
  }

  .task-cover {
    width: 100%;
    height: 180px;
  }

  .task-meta-grid {
    grid-template-columns: 1fr;
  }
}
</style>
