/**
 * Mini CRM client-side helpers.
 */
(function () {
  "use strict";

  // Mobile sidebar toggle
  const toggle = document.getElementById("sidebarToggle");
  const sidebar = document.querySelector(".sidebar");
  if (toggle && sidebar) {
    toggle.addEventListener("click", function () {
      sidebar.classList.toggle("open");
    });

    document.addEventListener("click", function (event) {
      if (
        sidebar.classList.contains("open") &&
        !sidebar.contains(event.target) &&
        !toggle.contains(event.target)
      ) {
        sidebar.classList.remove("open");
      }
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
})();
