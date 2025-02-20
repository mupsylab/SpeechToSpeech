import { createRouter, createWebHashHistory } from 'vue-router'

import view from '../view/manual.vue';

const router = createRouter({
  history: createWebHashHistory(import.meta.env.BASE_URL),
  routes: [
    {
      path: "/manual",
      name: "sts-manual",
      component: view,
      alias: "/"
    }, {
      path: "/auto",
      name: "sts-auto",
      component: () => import("../view/auto.vue")
    }
  ]
});

export default router;
