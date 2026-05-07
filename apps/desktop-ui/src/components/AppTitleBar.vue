<script setup lang="ts">
import {
  minimizeWindow as minimizeAppWindow,
  requestWindowClose,
  startWindowDrag,
  toggleMaximizeWindow as toggleAppMaximizeWindow,
} from '../api/windowApi';

function logWindowActionError(actionName: string, error: unknown): void {
  console.warn(`窗口${actionName}失败`, error);
}

async function startDragging(): Promise<void> {
  try {
    await startWindowDrag();
  } catch (error) {
    logWindowActionError('拖拽', error);
  }
}

async function minimizeWindow(): Promise<void> {
  try {
    await minimizeAppWindow();
  } catch (error) {
    logWindowActionError('最小化', error);
  }
}

async function toggleMaximizeWindow(): Promise<void> {
  try {
    await toggleAppMaximizeWindow();
  } catch (error) {
    logWindowActionError('最大化', error);
  }
}

async function closeWindow(): Promise<void> {
  try {
    await requestWindowClose();
  } catch (error) {
    logWindowActionError('关闭', error);
  }
}
</script>

<template>
  <div class="app-title-bar">
    <div class="title-drag-region" @mousedown.left="startDragging">
      <span class="app-mark">VD</span>
      <span class="app-title">Video Download</span>
    </div>

    <div class="window-actions">
      <button class="window-action" type="button" aria-label="最小化" @click="minimizeWindow">
        —
      </button>
      <button
        class="window-action"
        type="button"
        aria-label="最大化或还原"
        @click="toggleMaximizeWindow"
      >
        □
      </button>
      <button class="window-action close" type="button" aria-label="关闭" @click="closeWindow">
        ×
      </button>
    </div>
  </div>
</template>

<style scoped lang="scss">
.app-title-bar {
  height: var(--app-title-bar-height);
  display: flex;
  align-items: center;
  justify-content: space-between;
  color: #303133;
  background: #ffffff;
  border-bottom: 1px solid var(--app-color-border);
}

.title-drag-region {
  flex: 1;
  height: 100%;
  display: flex;
  align-items: center;
  gap: 8px;
  padding: 0 12px;
}

.app-mark {
  width: 24px;
  height: 24px;
  display: inline-flex;
  align-items: center;
  justify-content: center;
  border-radius: 6px;
  color: #ffffff;
  background: var(--app-color-primary);
  font-size: 12px;
  font-weight: 700;
}

.app-title {
  font-size: 13px;
  font-weight: 600;
}

.window-actions {
  height: 100%;
  display: flex;
}

.window-action {
  width: 46px;
  height: 100%;
  border: 0;
  color: #606266;
  background: transparent;
  cursor: pointer;
}

.window-action:hover {
  background: #ecf5ff;
}

.window-action.close:hover {
  color: #ffffff;
  background: var(--app-color-danger);
}
</style>
