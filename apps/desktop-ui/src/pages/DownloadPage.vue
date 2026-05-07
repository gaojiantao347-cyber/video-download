<script setup lang="ts">
import { computed, ref, watch } from 'vue';
import { ElMessage, ElNotification } from 'element-plus';

import { retryDownloadTask } from '../api/downloadApi';
import { mapErrorMessage, mapUnknownErrorMessage } from '../api/errorMapper';
import {
  sendDownloadFailureNotification,
  sendDownloadSuccessNotification,
} from '../api/notificationApi';
import CreateDownloadTaskForm from '../features/download/components/CreateDownloadTaskForm.vue';
import DownloadTaskCard from '../features/download/components/DownloadTaskCard.vue';
import TaskSessionList from '../features/download/components/TaskSessionList.vue';
import { useDownloadTaskSessionStore } from '../features/download/taskSessionStore';
import { isTerminalTaskStatus } from '../features/download/taskStatusMap';
import { useDownloadTask } from '../queries/useDownloadTask';
import { useSettingsStore } from '../stores/settingsStore';
import type {
  CreateDownloadTaskRequest,
  CreateDownloadTaskResponse,
  DownloadTask,
  DownloadTaskStatus,
} from '../types/download';

const taskSessionStore = useDownloadTaskSessionStore();
const settingsStore = useSettingsStore();
const currentTaskId = computed(() => taskSessionStore.activeTaskId);
const retryingTaskId = ref<string | null>(null);
const retryError = ref<string | null>(null);
const notifiedStatusByTaskId = new Map<string, DownloadTaskStatus>();

const downloadTaskQuery = useDownloadTask(currentTaskId);

const queriedTask = computed(() => downloadTaskQuery.data.value ?? null);
const currentTask = computed(() => {
  const task = queriedTask.value;
  if (task?.taskId === currentTaskId.value) {
    return task;
  }

  return taskSessionStore.activeTask;
});
const sessionItems = computed(() => taskSessionStore.items);
const isLoadingTask = computed(
  () => Boolean(currentTaskId.value) && downloadTaskQuery.isLoading.value,
);
const taskQueryError = computed(() => {
  const error = downloadTaskQuery.error.value;
  return error ? mapUnknownErrorMessage(error) : null;
});

function handleTaskCreated(
  response: CreateDownloadTaskResponse,
  request: CreateDownloadTaskRequest,
): void {
  retryError.value = null;
  taskSessionStore.addCreatedTask(response, request);
  ElMessage.success('下载任务已创建');
}

function handleTaskCreateFailed(message: string): void {
  ElMessage.error(message);
}

function selectTask(taskId: string): void {
  retryError.value = null;
  taskSessionStore.setActiveTask(taskId);
}

async function retryTask(taskId?: string): Promise<void> {
  const sourceTaskId = taskId ?? currentTaskId.value;
  if (!sourceTaskId) {
    retryError.value = '缺少任务 ID，无法重试';
    return;
  }

  const request = taskSessionStore.getRequest(sourceTaskId);
  if (!request) {
    retryError.value = '缺少原始任务参数，无法重试';
    return;
  }

  retryingTaskId.value = sourceTaskId;
  retryError.value = null;
  try {
    const response = await retryDownloadTask(request);
    taskSessionStore.addCreatedTask(response, request);
    ElMessage.success('已重新创建下载任务');
  } catch (error) {
    retryError.value = mapUnknownErrorMessage(error);
    ElMessage.error(retryError.value);
  } finally {
    if (retryingTaskId.value === sourceTaskId) {
      retryingTaskId.value = null;
    }
  }
}

function getTaskDisplayName(task: DownloadTask): string {
  return task.title || task.fileName || '视频下载任务';
}

function notifyTerminalTask(task: DownloadTask): void {
  if (!isTerminalTaskStatus(task.status)) {
    return;
  }

  const lastNotifiedStatus = notifiedStatusByTaskId.get(task.taskId);
  if (lastNotifiedStatus === task.status) {
    return;
  }

  notifiedStatusByTaskId.set(task.taskId, task.status);

  if (task.status === 'SUCCESS') {
    const message = getTaskDisplayName(task);
    ElNotification.success({
      title: '下载完成',
      message,
    });
    sendSystemTerminalNotification(task, message);
    return;
  }

  if (task.status === 'FAILED') {
    const message = mapErrorMessage(task.errorCode, task.errorMessage);
    ElNotification.error({
      title: '下载失败',
      message,
    });
    sendSystemTerminalNotification(task, message);
    return;
  }

  ElNotification.warning({
    title: '任务已取消',
    message: getTaskDisplayName(task),
  });
}

function sendSystemTerminalNotification(task: DownloadTask, message: string): void {
  if (!settingsStore.enableSystemNotifications) {
    return;
  }

  if (task.status === 'SUCCESS') {
    void sendDownloadSuccessNotification(message).catch((error) => {
      console.warn('发送下载成功系统通知失败', error);
    });
    return;
  }

  if (task.status === 'FAILED') {
    void sendDownloadFailureNotification(message).catch((error) => {
      console.warn('发送下载失败系统通知失败', error);
    });
  }
}

watch(
  queriedTask,
  (task) => {
    if (!task) {
      return;
    }

    taskSessionStore.upsertTask(task);
    notifyTerminalTask(task);
  },
  { immediate: true },
);

watch(taskQueryError, (message) => {
  if (message) {
    ElMessage.error(message);
  }
});
</script>

<template>
  <div class="app-page download-page">
    <el-card shadow="never" class="hero-card">
      <div class="hero-content">
        <div>
          <el-tag type="primary" effect="plain">桌面端 MVP</el-tag>
          <h2>单链接公开视频下载</h2>
          <p>粘贴抖音或快手公开视频链接，由 Tauri 转发到 Python 下载引擎创建下载任务。</p>
        </div>
        <el-alert
          title="合规提示：不支持私密、付费、DRM、验证码绕过或 Cookie/Token 输入。"
          type="warning"
          :closable="false"
          show-icon
        />
      </div>
    </el-card>

    <CreateDownloadTaskForm @created="handleTaskCreated" @failed="handleTaskCreateFailed" />

    <DownloadTaskCard
      v-if="currentTask"
      :task="currentTask"
      :retry-loading="retryingTaskId === currentTask.taskId"
      @retry="retryTask"
    />

    <el-card v-else shadow="never" class="status-card">
      <template #header>当前任务</template>

      <el-alert
        v-if="retryError || taskQueryError"
        class="status-alert"
        :title="retryError || taskQueryError || ''"
        type="error"
        :closable="false"
        show-icon
      />

      <div v-if="isLoadingTask" class="task-loading">
        <el-skeleton :rows="4" animated />
        <p>任务已创建，正在加载任务详情。</p>
      </div>
      <el-empty
        v-else-if="!currentTaskId"
        description="暂无下载任务。请先粘贴公开视频链接并创建任务。"
      />
      <el-empty v-else description="暂未获取到任务详情，请检查下载引擎是否正常运行。" />
    </el-card>

    <el-alert
      v-if="retryError && currentTask"
      class="status-alert"
      :title="retryError"
      type="error"
      :closable="false"
      show-icon
    />

    <TaskSessionList
      :items="sessionItems"
      :active-task-id="currentTaskId"
      :retrying-task-id="retryingTaskId"
      @select="selectTask"
      @retry="retryTask"
    />

    <el-card shadow="never" class="guide-card">
      <template #header>使用说明</template>
      <ul>
        <li>仅支持抖音、快手公开视频分享链接。</li>
        <li>不支持私密、付费、DRM、验证码绕过或 Cookie/Token 输入。</li>
        <li>下载失败时会展示错误码对应文案，可使用重试入口重新创建任务。</li>
      </ul>
    </el-card>
  </div>
</template>

<style scoped lang="scss">
.download-page {
  display: grid;
  gap: 16px;
}

.hero-card,
.status-card,
.guide-card {
  border-radius: 12px;
}

.hero-content {
  display: grid;
  gap: 16px;
}

.hero-content h2 {
  margin: 12px 0 8px;
  font-size: 24px;
}

.hero-content p {
  max-width: 720px;
  margin: 0;
  color: #606266;
}

.status-alert {
  margin-bottom: 16px;
}

.task-loading {
  display: grid;
  gap: 12px;
}

.task-loading p {
  margin: 0;
  color: #606266;
  font-size: 13px;
}

.guide-card ul {
  margin: 0;
  padding-left: 20px;
  color: #606266;
  line-height: 1.8;
}
</style>
