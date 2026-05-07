<script setup lang="ts">
import { computed } from 'vue';

const props = withDefaults(
  defineProps<{
    removeWatermark: boolean;
    allowFallback: boolean;
    disabled?: boolean;
  }>(),
  {
    disabled: false,
  },
);

const emit = defineEmits<{
  'update:removeWatermark': [value: boolean];
  'update:allowFallback': [value: boolean];
}>();

const removeWatermarkValue = computed({
  get: () => props.removeWatermark,
  set: (value: boolean) => emit('update:removeWatermark', value),
});

const allowFallbackValue = computed({
  get: () => props.allowFallback,
  set: (value: boolean) => emit('update:allowFallback', value),
});
</script>

<template>
  <div class="download-options">
    <el-form-item label="优先无水印">
      <el-switch
        v-model="removeWatermarkValue"
        :disabled="disabled"
        active-text="开启"
        inactive-text="关闭"
      />
    </el-form-item>
    <el-form-item label="无水印不可用时降级">
      <el-switch
        v-model="allowFallbackValue"
        :disabled="disabled || !removeWatermarkValue"
        active-text="允许"
        inactive-text="不允许"
      />
    </el-form-item>
  </div>
</template>

<style scoped lang="scss">
.download-options {
  display: grid;
  grid-template-columns: repeat(2, minmax(0, 1fr));
  gap: 16px;
}

@media (max-width: 900px) {
  .download-options {
    grid-template-columns: 1fr;
  }
}
</style>
