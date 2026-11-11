(function () {
    var body = document.body;

    // ------------------------------------------------
    // Sidebar Menu
    // ------------------------------------------------

    function setMenu(open) {
        body.classList.toggle("menu-open", open);
    }

    document.addEventListener("click", function (e) {
        if (e.target.closest("[data-menu-toggle]")) {
            setMenu(!body.classList.contains("menu-open"));
        } else if (e.target.closest("[data-menu-close]")) {
            setMenu(false);
        }
    });


    // ------------------------------------------------
    // Back Button
    // ------------------------------------------------

    var back = document.getElementById("back-btn");

    if (back) {
        back.addEventListener("click", function () {
            var sameSite =
                document.referrer &&
                document.referrer.indexOf(location.origin) === 0;

            if (sameSite && history.length > 1) {
                history.back();
            } else {
                location.href = back.getAttribute("data-home-url");
            }
        });
    }


    // ------------------------------------------------
    // Theme Preferences
    // ------------------------------------------------

    window.setTheme = function (t) {
        try {
            localStorage.setItem("bs-theme", t);
        } catch (e) {}

        document.documentElement.setAttribute("data-theme", t);

        document.querySelectorAll("[data-theme-pick]").forEach(function (b) {
            b.classList.toggle(
                "on",
                b.getAttribute("data-theme-pick") === t
            );
        });
    };

    document.addEventListener("click", function (e) {
        var b = e.target.closest("[data-theme-pick]");

        if (b) {
            window.setTheme(b.getAttribute("data-theme-pick"));
        }
    });

    window.setTheme(
        document.documentElement.getAttribute("data-theme") || "light"
    );


    // ------------------------------------------------
    // Profile Dropdown
    // ------------------------------------------------

    function closeProfileMenus() {
        document.querySelectorAll("[data-profile-menu]").forEach(function (menu) {
            var dropdown = menu.querySelector("[data-profile-dropdown]");
            var button = menu.querySelector("[data-profile-toggle]");

            if (dropdown) {
                dropdown.hidden = true;
            }

            if (button) {
                button.setAttribute("aria-expanded", "false");
            }
        });
    }

    document.addEventListener("click", function (e) {
        var toggle = e.target.closest("[data-profile-toggle]");

        if (toggle) {
            var menu = toggle.closest("[data-profile-menu]");
            var dropdown = menu.querySelector("[data-profile-dropdown]");

            if (!dropdown) {
                return;
            }

            var isOpen = !dropdown.hidden;

            closeProfileMenus();

            if (!isOpen) {
                dropdown.hidden = false;
                toggle.setAttribute("aria-expanded", "true");
            }

            return;
        }

        // Close when clicking outside the profile menu.
        if (!e.target.closest("[data-profile-menu]")) {
            closeProfileMenus();
        }
    });


    // ------------------------------------------------
    // Keyboard Controls
    // ------------------------------------------------

    document.addEventListener("keydown", function (e) {
        if (e.key === "Escape") {
            setMenu(false);
            closeProfileMenus();
        }
    });


    // ------------------------------------------------
    // Dashboard Live Updates
    // ------------------------------------------------

    var path = window.location.pathname;

    var isDashboard =
        path === "/customer/" ||
        path === "/partner/" ||
        path === "/assigner/";

    if (!isDashboard) {
        return;
    }

    var apiUrl = "/api/dashboard-live/";
    var lastSignature = null;
    var checking = false;
    var reloadPending = false;

    function isEditing() {
        var active = document.activeElement;

        if (!active) {
            return false;
        }

        return (
            active.matches("input, select, textarea") ||
            active.isContentEditable
        );
    }

    function checkDashboard() {
        if (checking || document.hidden) {
            return;
        }

        checking = true;

        fetch(apiUrl, {
            method: "GET",
            credentials: "same-origin",
            cache: "no-store",
            headers: {
                "X-Requested-With": "XMLHttpRequest"
            }
        })
        .then(function (response) {
            if (!response.ok) {
                throw new Error("Dashboard update check failed");
            }

            return response.json();
        })
        .then(function (data) {
            if (!data.ok) {
                return;
            }

            if (lastSignature === null) {
                lastSignature = data.signature;
                return;
            }

            if (lastSignature !== data.signature) {
                reloadPending = true;

                if (!isEditing()) {
                    window.location.reload();
                }
            }
        })
        .catch(function (error) {
            console.error("Bluestork live update:", error);
        })
        .finally(function () {
            checking = false;
        });
    }

    // Check every three seconds.
    setInterval(checkDashboard, 3000);

    // Avoid losing form input while editing.
    document.addEventListener("focusout", function () {
        if (reloadPending) {
            setTimeout(function () {
                if (!isEditing()) {
                    window.location.reload();
                }
            }, 300);
        }
    });

    // Check when returning to the browser tab.
    document.addEventListener("visibilitychange", function () {
        if (!document.hidden) {
            checkDashboard();
        }
    });

    // Initial check.
    checkDashboard();

})();