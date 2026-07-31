/**
 * Mini CRM client-side helpers:
 * - responsive sidebar
 * - confirm destructive forms
 * - auto-dismiss alerts
 * - page/form loading animations
 */
(function () {
  "use strict";

  const toggle = document.getElementById("sidebarToggle");
  const sidebar = document.getElementById("appSidebar") || document.querySelector(".sidebar");
  const backdrop = document.getElementById("sidebarBackdrop");
  const loader = document.getElementById("pageLoader");

  function closeSidebar() {
    if (!sidebar) return;
    sidebar.classList.remove("open");
    if (backdrop) backdrop.classList.remove("show");
  }

  function openSidebar() {
    if (!sidebar) return;
    sidebar.classList.add("open");
    if (backdrop) backdrop.classList.add("show");
  }

  function showLoader() {
    if (!loader) return;
    loader.hidden = false;
    loader.setAttribute("aria-hidden", "false");
    document.body.classList.add("is-loading");
  }

  function hideLoader() {
    if (!loader) return;
    loader.hidden = true;
    loader.setAttribute("aria-hidden", "true");
    document.body.classList.remove("is-loading");
  }

  if (toggle && sidebar) {
    toggle.addEventListener("click", function () {
      if (sidebar.classList.contains("open")) {
        closeSidebar();
      } else {
        openSidebar();
      }
    });
  }

  if (backdrop) {
    backdrop.addEventListener("click", closeSidebar);
  }

  // Close sidebar after navigating on small screens
  if (sidebar) {
    sidebar.querySelectorAll("a.nav-link").forEach(function (link) {
      link.addEventListener("click", function () {
        if (window.matchMedia("(max-width: 991.98px)").matches) {
          closeSidebar();
        }
      });
    });
  }

  // Confirm destructive actions
  document.querySelectorAll("form[data-confirm]").forEach(function (form) {
    form.addEventListener("submit", function (event) {
      const message = form.getAttribute("data-confirm") || "Are you sure?";
      if (!window.confirm(message)) {
        event.preventDefault();
      }
    });
  });

  // Auto-dismiss alerts after a few seconds
  document.querySelectorAll(".alert-dismissible").forEach(function (alert) {
    setTimeout(function () {
      const instance = bootstrap.Alert.getOrCreateInstance(alert);
      instance.close();
    }, 5000);
  });

  // Show loading state on standard form submits / navigation links
  document.querySelectorAll("form").forEach(function (form) {
    form.addEventListener("submit", function () {
      if (form.getAttribute("data-no-loader") === "true") return;
      // Skip invalid HTML5 forms so users can fix errors without a stuck overlay
      if (typeof form.reportValidity === "function" && !form.reportValidity()) return;
      const submitter = form.querySelector("[type='submit']");
      if (submitter) {
        submitter.disabled = true;
        submitter.classList.add("is-loading-btn");
      }
      showLoader();
    });
  });

  document.querySelectorAll("a[data-loading='true']").forEach(function (link) {
    link.addEventListener("click", function () {
      showLoader();
    });
  });

  window.addEventListener("pageshow", hideLoader);
})();
