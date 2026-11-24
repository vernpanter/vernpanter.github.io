// Slides the light on the home page along its rail, following the mouse.
(() => {
  const hero = document.querySelector(".hero");
  const still = matchMedia("(prefers-reduced-motion: reduce)");
  if (!hero || !matchMedia("(hover: hover) and (pointer: fine)").matches) return;

  const home = parseFloat(getComputedStyle(hero).getPropertyValue("--x"));
  let x = home;
  let target = home;
  let frame = 0;

  function step() {
    x += (target - x) * 0.07;
    const there = Math.abs(target - x) < 0.05;
    if (there) x = target;
    hero.style.setProperty("--x", `${x}%`);
    frame = there ? 0 : requestAnimationFrame(step);
  }

  function aim(value) {
    if (still.matches) return;
    target = value;
    if (!frame) frame = requestAnimationFrame(step);
  }

  hero.addEventListener("pointermove", (event) => {
    const box = hero.getBoundingClientRect();
    aim(Math.min(94, Math.max(6, ((event.clientX - box.left) / box.width) * 100)));
  });
  hero.addEventListener("pointerleave", () => aim(home));
})();
