import { createRouter, createWebHashHistory } from 'vue-router'

import index from '../view/index.vue';

const router = createRouter({
  history: createWebHashHistory(import.meta.env.BASE_URL),
  routes: [
    {
      path: "/",
      name: "index",
      component: index
    }, {
      path: "/manual",
      name: "sts-manual",
      component: () => import("../view/sts/manual.vue")
    }, {
      path: "/auto",
      name: "sts-auto",
      component: () => import("../view/sts/auto.vue")
    }
  ]
});

export default router;
