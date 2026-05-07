import { VueQueryPlugin } from '@tanstack/vue-query';
import ElementPlus from 'element-plus';
import 'element-plus/dist/index.css';
import { createPinia } from 'pinia';
import { createApp } from 'vue';

import App from '../App.vue';
import '../assets/styles/global.scss';
import router from '../router';
import { queryClient } from './queryClient';

export function bootstrapApp(): void {
  const app = createApp(App);

  app.use(createPinia());
  app.use(router);
  app.use(ElementPlus);
  app.use(VueQueryPlugin, { queryClient });

  app.mount('#app');
}
