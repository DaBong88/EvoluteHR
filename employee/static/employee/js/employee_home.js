(function () {
  function initializeEmployeeHome() {
    const root = document.querySelector("[data-employee-home]");
    if (!root || root.dataset.navigationReady === "true") return;
    root.dataset.navigationReady = "true";

    const tabs = Array.from(root.querySelectorAll("[data-eh-tab]"));
    const panels = Array.from(root.querySelectorAll("[data-eh-panel]"));
    const rail = root.querySelector(".eh-rail");
    const menu = root.querySelector("[data-eh-menu]");

    function show(name, updateHash) {
      const valid = panels.some((panel) => panel.dataset.ehPanel === name)
        ? name
        : "summary";
      tabs.forEach((tab) =>
        tab.classList.toggle("is-active", tab.dataset.ehTab === valid)
      );
      panels.forEach((panel) =>
        panel.classList.toggle("is-active", panel.dataset.ehPanel === valid)
      );
      if (updateHash !== false) history.replaceState(null, "", `#${valid}`);
      rail.classList.remove("is-open");
      if (menu) menu.setAttribute("aria-expanded", "false");
      window.scrollTo({ top: 0, behavior: "smooth" });
    }

    window.employeeHomeShow = show;
    tabs.forEach((tab) =>
      tab.addEventListener("click", () => show(tab.dataset.ehTab))
    );
    if (menu) {
      menu.addEventListener("click", () => {
        const open = rail.classList.toggle("is-open");
        menu.setAttribute("aria-expanded", String(open));
      });
    }
    window.addEventListener("hashchange", () => show(location.hash.slice(1), false));
    show(location.hash.slice(1), false);
  }

  if (document.readyState === "loading") {
    document.addEventListener("DOMContentLoaded", initializeEmployeeHome);
  } else {
    initializeEmployeeHome();
  }
  document.body.addEventListener("htmx:afterSwap", initializeEmployeeHome);
})();
