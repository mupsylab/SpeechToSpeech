import { createRouter, createWebHashHistory } from 'vue-router'

import index from '../view/index.vue';
import { useUserInfo } from '../store/UserInfo';
import { ElMessage } from 'element-plus';

const router = createRouter({
  history: createWebHashHistory(import.meta.env.BASE_URL),
  routes: [
    {
      path: "/",
      name: "index",
      component: index,
      meta: {
        requireAuth: false
      }
    }, {
      path: "/auto",
      name: "sts-auto",
      component: () => import("../view/app/auto.vue"),
      meta: {
        requireAuth: true
      }
    }
  ]
});

router.beforeEach((to, _, next) => {
  const userInfo = useUserInfo();

  if (to.meta.requireAuth) {
    userInfo.isLogin().then(r => {
      if (r) { next();}
      else {
        ElMessage.warning("请先登录");
        next("/");
      }
    })
  } else {
    next();
  }
});

export default router;
