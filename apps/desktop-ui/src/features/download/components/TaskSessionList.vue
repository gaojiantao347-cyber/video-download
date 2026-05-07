<script setup lang="ts">
import StatusTag from '../../../components/StatusTag.vue';
import { mapErrorMessage } from '../../../api/errorMapper';
import type { DownloadTaskSessionItem } from '../taskSessionStore';
import PlatformBadge from './PlatformBadge.vue';

const props = withDefaults(
  defineProps<{
    items: DownloadTaskSessionItem[];
    activeTaskId?: string | null;
    retryingTaskId?: string | null;
  }>(),
  {
    activeTaskId: null,
    retryingTaskId: null,
  },
);

const emit = defineEmits<{
  select: [taskId: string];
  retry: [taskId: string];
}>();

function getTaskTitle(item: DownloadTaskSessionItem): string {
  return item.task?.title || item.task?.fileName || item.request.url;
}

function getTaskError(item: DownloadTaskSessionItem): string | null {
  if (!item.task || item.status !== 'FAILED') {
    return null;
  }

  return mapErrorMessage(item.task.errorCode, item.task.errorMessage);
}

function formatUpdatedAt(value: string): string {
  const date = new Date(value);
  if (Number.isNaN(date.getTime())) {
    return value;
  }

  return date.toLocaleString();
}

function isActiveTask(taskId: string): boolean {
  return props.activeTaskId === taskId;
}
</script>

<template>
  <el-card v-if="items.length" shadow="never" class="task-session-card">
    <template #header>本次会话最近任务</template>

    <div class="task-session-list">
      <div
        v-for="item in items"
        :key="item.taskId"
        class="task-session-item"
        :class="{ 'task-session-item--active': isActiveTask(item.taskId) }"
      >
        <div class="task-session-item__main">
          <StatusTag :status="item.status" />
          <div class="task-session-item__content">
            <div class="task-session-item__title">{{ getTaskTitle(item) }}</div>
            <div class="task-session-item__meta">
              <PlatformBadge :platform="item.task?.platform" :url="item.request.url" />
              <span>{{ formatUpdatedAt(item.updatedAt) }}</span>
              <span>{{ item.taskId }}</span>
            </div>
            <p v-if="item.task && item.status === 'FAILED'" class="task-session-item__error">
              {{ getTaskError(item) }}
            </p>
          </div>
        </div>

        <div class="task-session-item__actions">
          <el-button
            size="small"
            :disabled="isActiveTask(item.taskId)"
            @click="emit('select', item.taskId)"
          >
            查看
          </el-button>
          <el-button
            v-if="item.status === 'FAILED'"
            size="small"
            type="danger"
            plain
            :loading="retryingTaskId === item.taskId"
            @click="emit('retry', item.taskId)"
          >
            重试
          </el-button>
        </div>
      </div>
    </div>
  </el-card>
</template>

<style scoped lang="scss">
.task-session-card {
  border-radius: 12px;
}

.task-session-list {
  display: grid;
  gap: 10px;
}

.task-session-item {
  display: flex;
  align-items: flex-start;
  justify-content: space-between;
  gap: 16px;
  padding: 12px;
  border: 1px solid #ebeef5;
  border-radius: 10px;
  background: #fff;
}

.task-session-item--active {
  border-color: var(--el-color-primary-light-5);
  background: var(--el-color-primary-light-9);
}

.task-session-item__main {
  min-width: 0;
  display: flex;
  align-items: flex-start;
  gap: 12px;
}

.task-session-item__content {
  min-width: 0;
  display: grid;
  gap: 6px;
}

.task-session-item__title {
  overflow: hidden;
  color: #303133;
  font-weight: 600;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.task-session-item__meta {
  display: flex;
  align-items: center;
  flex-wrap: wrap;
  gap: 8px;
  color: #909399;
  font-size: 12px;
}

.task-session-item__error {
  margin: 0;
  color: var(--el-color-danger);
  font-size: 12px;
}

.task-session-item__actions {
  display: flex;
  flex-shrink: 0;
  gap: 8px;
}

@media (max-width: 820px) {
  .task-session-item,
  .task-session-item__main,
  .task-session-item__actions {
    align-items: stretch;
    flex-direction: column;
  }
}
</style>
