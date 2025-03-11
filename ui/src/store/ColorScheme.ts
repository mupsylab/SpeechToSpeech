import { defineStore } from "pinia";

type ColorScheme = "light" | "dark";
function switchScheme(colorScheme: ColorScheme) {
    document.documentElement.classList.forEach((className) => {
        document.documentElement.classList.remove(className);
    });
    document.documentElement.classList.add(colorScheme);
}

export const useColorScheme = defineStore("color-scheme", {
    state(): { colorScheme: ColorScheme } {
        let colorScheme: ColorScheme = "light";
        if (window.matchMedia("(prefers-color-scheme: dark)").matches) {
            colorScheme = "dark";
        }
        switchScheme(colorScheme);
        return {
            colorScheme: colorScheme
        }
    },
    getters: {
        currScheme(): ColorScheme {
            return this.colorScheme;
        },
        isDark(): boolean {
            return this.colorScheme === "dark";
        }
    },
    actions: {
        switch(colorScheme: ColorScheme) {
            switchScheme(colorScheme);
            this.colorScheme = colorScheme;
        }
    }
})