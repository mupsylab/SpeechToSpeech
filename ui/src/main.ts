import '@/assets/css/reset.css';
import '@/assets/css/color.css';
import '@/assets/css/style.css';

import { createApp } from 'vue';

import App from './App.vue';

import router from './router/index';

const app = createApp(App);
app.use(router);
app.mount('#app');
