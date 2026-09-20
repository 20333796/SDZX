(() => {
  "use strict";

  const tabs = Array.from(document.querySelectorAll('[role="tab"]'));
  const activateTab = (selectedTab, moveFocus = false) => {
    tabs.forEach((tab) => {
      const selected = tab === selectedTab;
      tab.setAttribute("aria-selected", String(selected));
      tab.tabIndex = selected ? 0 : -1;
      tab.classList.toggle("active", selected);
      document.getElementById(tab.getAttribute("aria-controls")).hidden = !selected;
    });
    if (moveFocus) selectedTab.focus();
  };

  tabs.forEach((tab, index) => {
    tab.addEventListener("click", () => activateTab(tab));
    tab.addEventListener("keydown", (event) => {
      const positions = {
        ArrowRight: (index + 1) % tabs.length,
        ArrowLeft: (index - 1 + tabs.length) % tabs.length,
        Home: 0,
        End: tabs.length - 1
      };
      if (Object.hasOwn(positions, event.key)) {
        event.preventDefault();
        activateTab(tabs[positions[event.key]], true);
      }
    });
  });

  const experienceLink = document.getElementById("experience-link");
  const pendingDialog = document.getElementById("experience-pending");
  const experienceUrl = window.GEO_MODEL_CONFIG?.experienceUrl?.trim();
  let destination = null;

  if (experienceUrl) {
    try {
      const parsed = new URL(experienceUrl, window.location.href);
      if (["http:", "https:"].includes(parsed.protocol) ||
          (window.location.protocol === "file:" && parsed.protocol === "file:")) {
        destination = parsed.href;
      }
    } catch {
      // 未填写或地址无效时，保留准备中提示，避免跳转到错误页面。
    }
  }

  if (destination) {
    experienceLink.href = destination;
    experienceLink.removeAttribute("aria-haspopup");
  } else {
    experienceLink.addEventListener("click", (event) => {
      event.preventDefault();
      pendingDialog.showModal();
    });
  }

  pendingDialog.querySelectorAll("button").forEach((button) => {
    button.addEventListener("click", () => pendingDialog.close());
  });
  pendingDialog.addEventListener("click", (event) => {
    if (event.target !== pendingDialog) return;
    const rect = pendingDialog.getBoundingClientRect();
    if (event.clientX < rect.left || event.clientX > rect.right ||
        event.clientY < rect.top || event.clientY > rect.bottom) pendingDialog.close();
  });
  pendingDialog.addEventListener("close", () => experienceLink.focus());
})();
