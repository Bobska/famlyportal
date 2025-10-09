(function () {
    "use strict";

    const storageKey = "budget-basic-dashboard-theme";
    const themeClassMap = {
        aurora: "dashboard-theme-aurora",
        quantum: "dashboard-theme-quantum",
        celestial: "dashboard-theme-celestial"
    };

    const bodyThemeClassMap = {
        aurora: "dashboard-shell-aurora",
        quantum: "dashboard-shell-quantum",
        celestial: "dashboard-shell-celestial"
    };

    function supportsLocalStorage() {
        try {
            const testKey = "bb-theme-test";
            window.localStorage.setItem(testKey, "1");
            window.localStorage.removeItem(testKey);
            return true;
        } catch (error) {
            return false;
        }
    }

    function getSavedTheme() {
        if (!supportsLocalStorage()) {
            return null;
        }

        return window.localStorage.getItem(storageKey);
    }

    function persistTheme(theme) {
        if (!supportsLocalStorage()) {
            return;
        }

        window.localStorage.setItem(storageKey, theme);
    }

    function applyTheme(viewport, theme) {
        if (!themeClassMap[theme]) {
            theme = "aurora";
        }

        Object.values(themeClassMap).forEach((className) => {
            viewport.classList.remove(className);
        });

        Object.values(bodyThemeClassMap).forEach((className) => {
            document.body.classList.remove(className);
        });

        viewport.dataset.dashboardTheme = theme;
        viewport.classList.add(themeClassMap[theme]);
        document.body.dataset.dashboardTheme = theme;
        document.body.classList.add(bodyThemeClassMap[theme]);
        viewport.style.setProperty("--dashboard-transition-opacity", "1");
        viewport.classList.add("dashboard-theme-active");

        if (viewport.animate) {
            viewport.animate(
                [
                    { filter: "saturate(0.75) brightness(0.95)", opacity: 0.85 },
                    { filter: "saturate(1.05) brightness(1)", opacity: 1 }
                ],
                {
                    duration: 320,
                    easing: "ease-out"
                }
            );
        }
    }

    function initThemeControls() {
        const viewport = document.querySelector("[data-dashboard-theme]");
        const themeSelect = document.getElementById("dashboardThemeSelect");

        if (!viewport || !themeSelect) {
            return;
        }

        const defaultTheme = viewport.dataset.dashboardTheme || "aurora";
        const savedTheme = getSavedTheme();
        const initialTheme = savedTheme || defaultTheme;

        if (themeSelect.value !== initialTheme) {
            themeSelect.value = initialTheme;
        }

        applyTheme(viewport, initialTheme);

        themeSelect.addEventListener("change", (event) => {
            const nextTheme = event.target.value;
            applyTheme(viewport, nextTheme);
            persistTheme(nextTheme);
        });
    }

    function initMissionClock() {
        const clockRoot = document.querySelector("[data-dashboard-clock]");
        if (!clockRoot) {
            return;
        }

        const timeTarget = clockRoot.querySelector(".dashboard-nav__clock-time");
        if (!timeTarget) {
            return;
        }

        const formatter = new Intl.DateTimeFormat(undefined, {
            hour: "2-digit",
            minute: "2-digit",
            second: "2-digit"
        });

        const updateTime = () => {
            timeTarget.textContent = formatter.format(new Date());
        };

        updateTime();
        setInterval(updateTime, 1000 * 30);
    }

    if (document.readyState === "loading") {
        document.addEventListener("DOMContentLoaded", () => {
            initThemeControls();
            initMissionClock();
        });
    } else {
        initThemeControls();
        initMissionClock();
    }
})();
