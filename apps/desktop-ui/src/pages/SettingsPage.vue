<script setup lang="ts">
import { computed, onMounted } from 'vue';
import { ElMessage, ElMessageBox } from 'element-plus';

import { mapUnknownErrorMessage } from '../api/errorMapper';
import { ensureNotificationPermission } from '../api/notificationApi';
import { useSettingsStore } from '../stores/settingsStore';
import { MAX_CONCURRENT_DOWNLOADS, MIN_CONCURRENT_DOWNLOADS } from '../types/settings';

const settingsStore = useSettingsStore();

const maxConcurrentDownloads = computed({
  get: () => settingsStore.draftSettings.maxConcurrentDownloads,
  set: (value: number | undefined) => {
    settingsStore.patchDraft({
      maxConcurrentDownloads: value ?? MIN_CONCURRENT_DOWNLOADS,
    });
  },
});

const removeWatermark = computed({
  get: () => settingsStore.draftSettings.removeWatermark,
  set: (value: boolean) => {
    settingsStore.patchDraft({
      removeWatermark: value,
      allowFallback: value ? settingsStore.draftSettings.allowFallback : false,
    });
  },
});

const allowFallback = computed({
  get: () => settingsStore.draftSettings.allowFallback,
  set: (value: boolean) => {
    settingsStore.patchDraft({ allowFallback: value });
  },
});

const enableSystemNotifications = computed({
  get: () => settingsStore.draftSettings.enableSystemNotifications,
  set: (value: boolean) => {
    settingsStore.patchDraft({ enableSystemNotifications: value });
  },
});

onMounted(() => {
  if (settingsStore.loaded) {
    return;
  }

  void settingsStore.loadSettings().catch((error) => {
    ElMessage.error(mapUnknownErrorMessage(error));
  });
});

async function chooseDownloadDir(): Promise<void> {
  try {
    await settingsStore.selectDownloadDir();
  } catch (error) {
    ElMessage.error(mapUnknownErrorMessage(error));
  }
}

function resetDraft(): void {
  settingsStore.resetDraft();
  ElMessage.info('已放弃未保存修改');
}

function restoreDefaultDraft(): void {
  settingsStore.restoreDefaultDraft();
  ElMessage.info('已恢复默认草稿，保存后生效');
}

async function beforeNotificationChange(): Promise<boolean> {
  if (settingsStore.draftSettings.enableSystemNotifications) {
    return true;
  }

  try {
    const granted = await ensureNotificationPermission();
    if (!granted) {
      ElMessage.warning('未获得系统通知权限，已保持关闭');
      return false;
    }

    return true;
  } catch (error) {
    ElMessage.error(mapUnknownErrorMessage(error));
    return false;
  }
}

function isMessageBoxCancel(error: unknown): boolean {
  return error === 'cancel' || error === 'close';
}

async function saveSettings(): Promise<void> {
  const downloadDirChanged = settingsStore.downloadDirChanged;
  const runtimeSettingsChanged = settingsStore.runtimeSettingsChanged;

  try {
    if (downloadDirChanged) {
      await ElMessageBox.confirm(
        '修改下载目录会影响后续任务保存位置，当前任务不会迁移。是否继续保存？',
        '确认修改下载目录',
        {
          type: 'warning',
          confirmButtonText: '继续保存',
          cancelButtonText: '取消',
        },
      );
    }

    await settingsStore.saveSettings();
    if (runtimeSettingsChanged) {
      ElMessage.success('设置已保存，下载目录和并发限制将在重启引擎后生效');
      return;
    }

    ElMessage.success('设置已保存');
  } catch (error) {
    if (isMessageBoxCancel(error)) {
      return;
    }

    ElMessage.error(settingsStore.errorMessage || mapUnknownErrorMessage(error));
  }
}
</script>

<template>
  <div class="app-page settings-page">
    <el-card v-loading="settingsStore.loading" shadow="never" class="settings-card">
      <template #header>
        <span>基础设置</span>
      </template>

      <el-alert
        v-if="settingsStore.errorMessage"
        class="settings-alert"
        :title="settingsStore.errorMessage"
        type="error"
        :closable="false"
        show-icon
      />

      <el-form label-position="top" class="settings-form">
        <el-form-item label="下载目录" required>
          <div class="path-row">
            <el-input
              :model-value="settingsStore.draftSettings.downloadDir"
              readonly
              placeholder="请选择下载目录"
            />
            <el-button :disabled="settingsStore.saving" @click="chooseDownloadDir">
              选择目录
            </el-button>
          </div>
          <div class="form-tip">修改下载目录会影响后续任务保存位置，保存后需重启引擎生效。</div>
        </el-form-item>

        <el-form-item label="并发下载数" required>
          <el-input-number
            v-model="maxConcurrentDownloads"
            :min="MIN_CONCURRENT_DOWNLOADS"
            :max="MAX_CONCURRENT_DOWNLOADS"
            :step="1"
            step-strictly
            :disabled="settingsStore.saving"
          />
          <div class="form-tip">
            允许范围 {{ MIN_CONCURRENT_DOWNLOADS }}-{{
              MAX_CONCURRENT_DOWNLOADS
            }}，保存后需重启引擎生效。
          </div>
        </el-form-item>

        <el-form-item label="默认优先无水印">
          <el-switch
            v-model="removeWatermark"
            :disabled="settingsStore.saving"
            active-text="开启"
            inactive-text="关闭"
          />
        </el-form-item>

        <el-form-item label="无水印不可用时允许降级">
          <el-switch
            v-model="allowFallback"
            :disabled="settingsStore.saving || !removeWatermark"
            active-text="允许"
            inactive-text="不允许"
          />
        </el-form-item>

        <el-form-item label="系统通知">
          <el-switch
            v-model="enableSystemNotifications"
            :before-change="beforeNotificationChange"
            :disabled="settingsStore.saving"
            active-text="开启"
            inactive-text="关闭"
          />
          <div class="form-tip">开启后，下载成功或失败时发送系统通知。</div>
        </el-form-item>

        <div class="action-row">
          <el-button
            type="primary"
            :loading="settingsStore.saving"
            :disabled="!settingsStore.dirty"
            @click="saveSettings"
          >
            保存设置
          </el-button>
          <el-button :disabled="settingsStore.saving || !settingsStore.dirty" @click="resetDraft">
            放弃修改
          </el-button>
          <el-button :disabled="settingsStore.saving" @click="restoreDefaultDraft">
            恢复默认草稿
          </el-button>
        </div>
      </el-form>
    </el-card>
  </div>
</template>

<style scoped lang="scss">
.settings-page {
  display: grid;
  gap: 16px;
}

.settings-card {
  max-width: 760px;
  border-radius: 12px;
}

.settings-alert {
  margin-bottom: 16px;
}

.settings-form {
  max-width: 640px;
}

.path-row {
  width: 100%;
  display: flex;
  gap: 12px;
}

.path-row .el-input {
  flex: 1;
}

.form-tip {
  width: 100%;
  margin-top: 6px;
  color: #909399;
  font-size: 12px;
}

.action-row {
  display: flex;
  flex-wrap: wrap;
  gap: 12px;
}
</style>
