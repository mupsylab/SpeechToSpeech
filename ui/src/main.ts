import '@/assets/css/reset.css';
import '@/assets/css/color.css';
import '@/assets/css/style.css';

import ElementPlus from 'element-plus';
import 'element-plus/dist/index.css';
import 'element-plus/theme-chalk/dark/css-vars.css';
import { createApp } from 'vue';
import { createPinia } from 'pinia';

import App from './App.vue';
import router from './router/index';

const pinia = createPinia();
const app = createApp(App);

app.use(ElementPlus);
app.use(pinia);
app.use(router);

app.mount('#app');
