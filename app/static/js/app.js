/**
 * Mini CRM client-side helpers.
 */
(function () {
  "use strict";

  const toggle = document.getElementById("sidebarToggle");
  const sidebar = document.getElementById("appSidebar") || document.querySelector(".sidebar");
  const backdrop = document.getElementById("sidebarBackdrop");

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
})();
