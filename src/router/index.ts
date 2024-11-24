import { createRouter, createWebHashHistory } from 'vue-router'

import view from '../view/default.vue';

const router = createRouter({
  history: createWebHashHistory(import.meta.env.BASE_URL),
  routes: [
    {
      path: "/",
      name: "experment",
      component: view
    }
  ]
});

export default router;
