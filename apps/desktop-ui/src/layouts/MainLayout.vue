<script setup lang="ts">
import { Download, Setting } from '@element-plus/icons-vue';
import { ElMessage, ElMessageBox } from 'element-plus';
import { computed, onBeforeUnmount, onMounted } from 'vue';
import { RouterView, useRoute } from 'vue-router';

import { mapUnknownErrorMessage } from '../api/errorMapper';
import { registerWindowCloseGuard, setCloseGuard } from '../api/windowApi';
import AppTitleBar from '../components/AppTitleBar.vue';
import EngineStatusTag from '../components/EngineStatusTag.vue';
import { useDownloadTaskSessionStore } from '../features/download/taskSessionStore';
import { useEngineHealth } from '../queries/useEngineHealth';
import { useSettingsStore } from '../stores/settingsStore';

const route = useRoute();
const settingsStore = useSettingsStore();
const taskSessionStore = useDownloadTaskSessionStore();
const activeRoute = computed(() => route.path);
const pageTitle = computed(() => (route.name === 'Settings' ? '基础设置' : '视频下载'));

let unlistenCloseGuard: (() => void) | null = null;

useEngineHealth();

onMounted(() => {
  loadSettings();
  registerCloseGuard();
});

onBeforeUnmount(() => {
  setCloseGuard(null);
  if (unlistenCloseGuard) {
    unlistenCloseGuard();
    unlistenCloseGuard = null;
  }
});

function loadSettings(): void {
  if (settingsStore.loaded) {
    return;
  }

  void settingsStore.loadSettings().catch((error) => {
    ElMessage.error(mapUnknownErrorMessage(error));
  });
}

function registerCloseGuard(): void {
  setCloseGuard(confirmCloseIfRunning);
  void registerWindowCloseGuard()
    .then((unlisten) => {
      unlistenCloseGuard = unlisten;
    })
    .catch((error) => {
      console.warn('注册窗口关闭确认失败', error);
    });
}

async function confirmCloseIfRunning(): Promise<boolean> {
  if (!taskSessionStore.hasRunningTasks) {
    return true;
  }

  try {
    await ElMessageBox.confirm(
      '当前有下载任务正在进行，关闭应用可能中断任务。是否继续关闭？',
      '确认关闭应用',
      {
        type: 'warning',
        confirmButtonText: '继续关闭',
        cancelButtonText: '取消',
      },
    );
    return true;
  } catch {
    return false;
  }
}
</script>

<template>
  <div class="app-layout">
    <AppTitleBar />

    <div class="app-shell">
      <aside class="app-sidebar">
        <div class="sidebar-header">
          <div class="sidebar-title">下载工具</div>
          <div class="sidebar-subtitle">单链接 MVP</div>
        </div>

        <el-menu :default-active="activeRoute" router class="sidebar-menu">
          <el-menu-item index="/download">
            <el-icon><Download /></el-icon>
            <span>视频下载</span>
          </el-menu-item>
          <el-menu-item index="/settings">
            <el-icon><Setting /></el-icon>
            <span>基础设置</span>
          </el-menu-item>
        </el-menu>
      </aside>

      <main class="app-main">
        <header class="content-header">
          <div>
            <h1>{{ pageTitle }}</h1>
            <p>仅支持抖音、快手公开视频链接</p>
          </div>
          <EngineStatusTag />
        </header>

        <section class="content-body">
          <RouterView />
        </section>
      </main>
    </div>
  </div>
</template>

<style scoped lang="scss">
.app-layout {
  height: 100vh;
  display: flex;
  flex-direction: column;
  overflow: hidden;
}

.app-shell {
  flex: 1;
  min-height: 0;
  display: flex;
  background: var(--app-color-bg);
}

.app-sidebar {
  width: var(--app-sidebar-width);
  display: flex;
  flex-direction: column;
  background: var(--app-color-surface);
  border-right: 1px solid var(--app-color-border);
}

.sidebar-header {
  padding: 20px 18px 16px;
  border-bottom: 1px solid #ebeef5;
}

.sidebar-title {
  font-size: 16px;
  font-weight: 700;
  color: #303133;
}

.sidebar-subtitle {
  margin-top: 4px;
  color: #909399;
  font-size: 12px;
}

.sidebar-menu {
  flex: 1;
  border-right: 0;
}

.app-main {
  flex: 1;
  min-width: 0;
  display: flex;
  flex-direction: column;
}

.content-header {
  height: 72px;
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 0 var(--app-page-padding);
  background: var(--app-color-surface);
  border-bottom: 1px solid var(--app-color-border);
}

.content-header h1 {
  margin: 0;
  font-size: 20px;
  line-height: 28px;
}

.content-header p {
  margin: 4px 0 0;
  color: #909399;
  font-size: 13px;
}

.content-body {
  flex: 1;
  min-height: 0;
  overflow: auto;
}
</style>
