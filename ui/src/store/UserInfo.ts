import { defineStore } from "pinia";

export const useUserInfo = defineStore("user-info", {
    state() {
        return {
            session_id: undefined
        }
    },
    actions: {
        login() {
            fetch("/api/account/login")
                .then(r => r.json())
                .then(r => { this.session_id = r.session_id });
        },
        isLogin() {
            return new Promise<Boolean>((resolve) => {
                fetch(`/api/account/islogin`)
                    .then(r => r.json())
                    .then(r => {
                        if (r.is_login) {
                            this.session_id = r.session_id;
                        } else {
                            this.session_id = undefined;
                        }
                        resolve(r.is_login);
                    });
            });
        }
    }
});
