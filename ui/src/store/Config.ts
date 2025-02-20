import { defineStore } from "pinia";

export const useSystemConfig = defineStore("system-config", {
    state() {
        return {
            baseURL: "http://127.0.0.1:8000",
            wsURL: "ws://127.0.0.1:8000"
        }
    },
    actions: {
        getURL(path: string) {
            if (!path.startsWith("/")) throw new Error("path should start with `/`");
            return `${this.baseURL}${path}`;
        },
        getWS(path: string) {
            if (!path.startsWith("/")) throw new Error("path should start with `/`");
            return `${this.wsURL}${path}`;
        }
    }
});
