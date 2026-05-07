<script setup lang="ts">
import { computed } from 'vue';

const props = withDefaults(
  defineProps<{
    modelValue: string;
    disabled?: boolean;
    errorMessage?: string | null;
  }>(),
  {
    disabled: false,
    errorMessage: null,
  },
);

const emit = defineEmits<{
  'update:modelValue': [value: string];
}>();

const value = computed({
  get: () => props.modelValue,
  set: (nextValue: string) => emit('update:modelValue', nextValue),
});
</script>

<template>
  <div class="url-input">
    <el-input
      v-model="value"
      type="textarea"
      :rows="4"
      maxlength="1000"
      show-word-limit
      :disabled="disabled"
      placeholder="请粘贴抖音或快手公开视频链接"
    />
    <p v-if="errorMessage" class="url-input__error">
      {{ errorMessage }}
    </p>
  </div>
</template>

<style scoped lang="scss">
.url-input {
  display: grid;
  gap: 6px;
}

.url-input__error {
  margin: 0;
  color: var(--app-color-danger);
  font-size: 12px;
}
</style>
