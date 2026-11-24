// Slides the light on the home page along its rail, following the mouse.
(() => {
  const hero = document.querySelector(".hero");
  const still = matchMedia("(prefers-reduced-motion: reduce)");
  if (!hero || !matchMedia("(hover: hover) and (pointer: fine)").matches) return;

  const lamp = hero.querySelector(".lamp");
  let x = 0;
  let target = 0;
  let frame = 0;
  let home = 0;

  // The stylesheet decides where the light rests, and that changes with the
  // window, so drop the moved position before measuring.
  function rest() {
    cancelAnimationFrame(frame);
    frame = 0;
    hero.style.removeProperty("--x");
    x = target = home = (lamp.offsetLeft / hero.clientWidth) * 100;
  }

  function step() {
    x += (target - x) * 0.07;
    if (Math.abs(target - x) >= 0.05) {
      hero.style.setProperty("--x", `${x}%`);
      frame = requestAnimationFrame(step);
    } else if (target === home) {
      rest();
    } else {
      x = target;
      hero.style.setProperty("--x", `${x}%`);
      frame = 0;
    }
  }

  function aim(value) {
    if (still.matches) return;
    target = value;
    if (!frame) frame = requestAnimationFrame(step);
  }

  rest();
  addEventListener("resize", rest);
  hero.addEventListener("pointermove", (event) => {
    const box = hero.getBoundingClientRect();
    aim(Math.min(94, Math.max(6, ((event.clientX - box.left) / box.width) * 100)));
  });
  hero.addEventListener("pointerleave", () => aim(home));
})();
