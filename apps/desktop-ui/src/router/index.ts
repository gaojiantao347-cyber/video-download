import { createRouter, createWebHashHistory, type RouteRecordRaw } from 'vue-router';

import MainLayout from '../layouts/MainLayout.vue';

const routes: RouteRecordRaw[] = [
  {
    path: '/',
    component: MainLayout,
    redirect: '/download',
    children: [
      {
        path: 'download',
        name: 'Download',
        component: () => import('../pages/DownloadPage.vue'),
      },
      {
        path: 'settings',
        name: 'Settings',
        component: () => import('../pages/SettingsPage.vue'),
      },
    ],
  },
];

const router = createRouter({
  history: createWebHashHistory(),
  routes,
});

export default router;
