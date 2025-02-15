import { createRouter, createWebHashHistory } from 'vue-router'

import view from '../view/manual.vue';

const router = createRouter({
  history: createWebHashHistory(import.meta.env.BASE_URL),
  routes: [
    {
      path: "/",
      name: "sts-manual",
      component: view
    }
  ]
});

export default router;
