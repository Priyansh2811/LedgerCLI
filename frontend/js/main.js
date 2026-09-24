// LedgerCLI Frontend Client Engine
const API_URL = "http://localhost:8000";

// 1. Zero-dependency Site Analytics telemetry logger
function initAnalytics() {
    try {
        fetch(`${API_URL}/api/analytics`, {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({
                page_path: window.location.pathname,
                referrer: document.referrer || null,
                user_agent: navigator.userAgent
            })
        }).catch(() => {}); // silent fail for offline/privacy blockers
    } catch (e) {}
}

// 2. Cookie Consent Management
function initCookieConsent() {
    const banner = document.getElementById("cookie-banner");
    const acceptBtn = document.getElementById("accept-cookie-btn");
    if (!banner || !acceptBtn) return;

    if (!localStorage.getItem("ledgercli_consent")) {
        banner.style.display = "block";
    }

    acceptBtn.addEventListener("click", () => {
        localStorage.setItem("ledgercli_consent", "granted");
        banner.style.display = "none";
    });
}

document.addEventListener("DOMContentLoaded", () => {
    initAnalytics();
    initCookieConsent();
});
