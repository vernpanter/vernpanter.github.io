// Full screen viewer for the galleries. Without this script every picture is
// still a plain link to its image.
(() => {
  const viewer = document.getElementById("viewer");
  const items = [...document.querySelectorAll("a[data-view]")];
  if (!viewer || !viewer.showModal || items.length === 0) return;

  const stage = viewer.querySelector(".viewer-stage");
  const img = stage.querySelector("img");
  const part = (name) => viewer.querySelector(name);
  let current = 0;

  function show(index) {
    current = (index + items.length) % items.length;
    const { title, year, label, description, index: view, total } = items[current].dataset;
    img.src = items[current].href;
    img.alt = total > 1 ? `${title}, view ${view} of ${total}` : title;
    part("cite").textContent = title;
    part(".viewer-year").textContent = year ? `, ${year}` : "";
    const views = total > 1 ? `View ${view} of ${total}` : "";
    part(".viewer-detail").textContent = [label, views].filter(Boolean).join(". ");
    part(".viewer-description").textContent = description;
    if (items.length > 1) new Image().src = items[(current + 1) % items.length].href;
  }

  function open(event, index) {
    // Leave new tab and new window clicks to the browser
    if (event.metaKey || event.ctrlKey || event.shiftKey || event.altKey) return;
    event.preventDefault();
    show(index);
    viewer.showModal();
  }

  items.forEach((item, index) => item.addEventListener("click", (event) => open(event, index)));
  document.querySelectorAll("a[data-opens-first]").forEach((link) => {
    const frame = link.closest(".work").querySelector("a[data-view]");
    link.addEventListener("click", (event) => open(event, items.indexOf(frame)));
  });

  viewer.querySelectorAll("[data-go]").forEach((button) => {
    button.hidden = items.length < 2;
    button.addEventListener("click", () => show(current + Number(button.dataset.go)));
  });
  part("[data-close]").addEventListener("click", () => viewer.close());
  viewer.addEventListener("close", () => img.removeAttribute("src"));
  viewer.addEventListener("keydown", (event) => {
    if (event.key === "ArrowRight") show(current + 1);
    if (event.key === "ArrowLeft") show(current - 1);
  });

  let startX = null;
  stage.addEventListener("pointerdown", (event) => {
    startX = event.isPrimary ? event.clientX : null;
  });
  stage.addEventListener("pointercancel", () => { startX = null; });
  stage.addEventListener("pointerup", (event) => {
    if (startX === null) return;
    const moved = event.clientX - startX;
    startX = null;
    if (Math.abs(moved) > 50) show(current + (moved < 0 ? 1 : -1));
    else if (event.target === stage) viewer.close();
  });
})();
