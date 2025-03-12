import { defineStore } from "pinia";

export const useUserInfo = defineStore("user-info", {
    state() {
        return {
            session_id: undefined,
            is_login: false
        }
    },
    actions: {
        login() {
            fetch("/api/account/login")
                .then(r => r.json())
                .then(r => {
                    this.is_login = true;
                    this.session_id = r.session_id
                });
        },
        logout() {
            fetch("/api/account/logout")
                .then(r => r.text())
                .then(_ => {
                    this.is_login = false;
                    this.session_id = undefined
                });
        },
        isLogin() {
            return new Promise<Boolean>((resolve) => {
                fetch(`/api/account/islogin`)
                    .then(r => r.json())
                    .then(r => {
                        if (r.is_login) {
                            this.is_login = true;
                            this.session_id = r.session_id;
                        } else {
                            this.is_login = false;
                            this.session_id = undefined;
                        }
                        resolve(r.is_login);
                    });
            });
        }
    }
});
