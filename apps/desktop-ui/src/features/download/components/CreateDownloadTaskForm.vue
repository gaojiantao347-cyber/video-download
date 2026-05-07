<script setup lang="ts">
import { computed, ref, watch } from 'vue';

import { createDownloadTask } from '../../../api/downloadApi';
import { mapErrorMessage, mapUnknownErrorMessage } from '../../../api/errorMapper';
import { useSettingsStore } from '../../../stores/settingsStore';
import type {
  CookiesFromBrowser,
  CreateDownloadTaskRequest,
  CreateDownloadTaskResponse,
} from '../../../types/download';
import DownloadOptions from './DownloadOptions.vue';
import PlatformBadge from './PlatformBadge.vue';
import UrlInput from './UrlInput.vue';
import { getSupportedPlatformText } from '../utils/platform';
import { validateDownloadUrl } from '../utils/urlValidation';

const emit = defineEmits<{
  created: [response: CreateDownloadTaskResponse, request: CreateDownloadTaskRequest];
  failed: [message: string];
}>();

type BrowserCookieOption = '' | CookiesFromBrowser;

const settingsStore = useSettingsStore();

const sourceUrl = ref('');
const removeWatermark = ref(settingsStore.removeWatermark);
const allowFallback = ref(settingsStore.removeWatermark ? settingsStore.allowFallback : false);
const cookiesFromBrowser = ref<BrowserCookieOption>('edge');
const submitting = ref(false);
const hasSubmitted = ref(false);
const optionsTouched = ref(false);
const submitError = ref<string | null>(null);

const removeWatermarkModel = computed({
  get: () => removeWatermark.value,
  set: (value: boolean) => {
    optionsTouched.value = true;
    removeWatermark.value = value;
    if (!value) {
      allowFallback.value = false;
    }
  },
});

const allowFallbackModel = computed({
  get: () => allowFallback.value,
  set: (value: boolean) => {
    optionsTouched.value = true;
    allowFallback.value = value;
  },
});

const validationResult = computed(() => validateDownloadUrl(sourceUrl.value));
const hasInput = computed(() => sourceUrl.value.trim().length > 0);
const validationMessage = computed(() => {
  if (validationResult.value.valid) {
    return null;
  }

  if (!hasSubmitted.value && !hasInput.value) {
    return null;
  }

  return mapErrorMessage(validationResult.value.errorCode);
});

const submitButtonText = computed(() => (submitting.value ? '正在创建任务' : '创建下载任务'));
const supportedPlatformText = getSupportedPlatformText();

watch(
  () => [settingsStore.loaded, settingsStore.removeWatermark, settingsStore.allowFallback] as const,
  ([loaded, defaultRemoveWatermark, defaultAllowFallback]) => {
    if (!loaded || optionsTouched.value) {
      return;
    }

    removeWatermark.value = defaultRemoveWatermark;
    allowFallback.value = defaultRemoveWatermark ? defaultAllowFallback : false;
  },
  { immediate: true },
);

async function submit(): Promise<void> {
  hasSubmitted.value = true;
  submitError.value = null;

  const result = validateDownloadUrl(sourceUrl.value);
  if (!result.valid) {
    submitError.value = mapErrorMessage(result.errorCode);
    return;
  }

  submitting.value = true;
  try {
    if (!settingsStore.loaded) {
      await settingsStore.loadSettings();
    }

    const outputDir = settingsStore.savedSettings.downloadDir.trim();
    if (!outputDir) {
      throw new Error('请先在基础设置中选择下载目录');
    }

    const request: CreateDownloadTaskRequest = {
      url: result.normalizedUrl,
      outputDir,
      removeWatermark: removeWatermark.value,
      allowFallback: removeWatermark.value ? allowFallback.value : false,
      cookiesFromBrowser:
        result.platform === 'DOUYIN' && cookiesFromBrowser.value ? cookiesFromBrowser.value : undefined,
    };

    const response = await createDownloadTask(request);
    emit('created', response, request);
  } catch (error) {
    const message = mapUnknownErrorMessage(error);
    submitError.value = message;
    emit('failed', message);
  } finally {
    submitting.value = false;
  }
}
</script>

<template>
  <el-card shadow="never" class="create-task-card">
    <template #header>
      <div class="card-header">
        <span>下载链接</span>
        <PlatformBadge :platform="validationResult.platform" :url="sourceUrl" />
      </div>
    </template>

    <el-form label-position="top" @submit.prevent="submit">
      <el-form-item label="公开视频分享链接">
        <UrlInput v-model="sourceUrl" :disabled="submitting" :error-message="validationMessage" />
      </el-form-item>

      <DownloadOptions
        v-model:remove-watermark="removeWatermarkModel"
        v-model:allow-fallback="allowFallbackModel"
        :disabled="submitting"
      />

      <el-form-item label="浏览器 Cookie（抖音可能需要）">
        <el-select
          v-model="cookiesFromBrowser"
          class="browser-cookie-select"
          :disabled="submitting || validationResult.platform !== 'DOUYIN'"
          placeholder="不读取浏览器 Cookie"
        >
          <el-option label="不读取" value="" />
          <el-option label="Microsoft Edge" value="edge" />
          <el-option label="Google Chrome" value="chrome" />
          <el-option label="Firefox" value="firefox" />
        </el-select>
        <p class="cookie-tip">
          请先用所选浏览器打开抖音；下载前关闭 Chrome/Edge 可避免 Cookie 数据库被锁。
        </p>
      </el-form-item>

      <el-alert
        v-if="submitError"
        class="submit-error"
        :title="submitError"
        type="error"
        :closable="false"
        show-icon
      />

      <div class="form-footer">
        <p>当前仅支持{{ supportedPlatformText }}公开视频链接。</p>
        <el-button type="primary" native-type="submit" :loading="submitting">
          {{ submitButtonText }}
        </el-button>
      </div>
    </el-form>
  </el-card>
</template>

<style scoped lang="scss">
.create-task-card {
  border-radius: 12px;
}

.card-header,
.form-footer {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 16px;
}

.card-header {
  font-weight: 600;
}

.browser-cookie-select {
  width: 240px;
}

.cookie-tip {
  margin: 6px 0 0;
  color: #909399;
  font-size: 12px;
  line-height: 1.5;
}

.submit-error {
  margin-top: 4px;
}

.form-footer {
  margin-top: 16px;
}

.form-footer p {
  margin: 0;
  color: #606266;
  font-size: 13px;
}

@media (max-width: 720px) {
  .form-footer {
    align-items: stretch;
    flex-direction: column;
  }
}
</style>
