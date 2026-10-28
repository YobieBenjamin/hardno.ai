/* ==========================================================================================================
   site.js: the only script on hardno.ai, and the only motion on the site.

   What it does: the four mottos sit in the page as a plain list. This script turns that list into a slow
   rotation, one motto at a time, fading to the next every 5 seconds, like a slide carousel.

   It is deliberately small and harmless:
     - It reads nothing about the visitor, stores nothing, sends nothing anywhere, and loads nothing else.
     - The page's security policy (in each page's <head>) only allows script from this site's own files,
       so this file is the only code a browser will run here.
     - If the script doesn't run at all (blocked, old browser, a search crawler), all four mottos simply
       show as a list. Nothing on the site depends on it.

   Courtesy rules it follows:
     - Pauses while the mouse is over the mottos or keyboard focus is inside them, so nobody loses a line
       mid-read.
     - Has a Pause/Play button for anyone who wants it still (screen readers are told whether it's pressed).
     - If the device asks for reduced motion (an accessibility setting), it shows all four and never rotates.

   It runs inside a function wrapper (function () { ... })(); so none of its names leak into the page.
   ========================================================================================================== */
(function () {
  /* Does this visitor's device ask for less motion? (Settings > Accessibility on phones and computers.) */
  var still = window.matchMedia && window.matchMedia("(prefers-reduced-motion: reduce)").matches;

  /* Tell the stylesheet the script is running; site.css only hides the other mottos when <html> has class "js". */
  document.documentElement.classList.add("js");

  /* Set up every motto box on the page (today there is one; the loop keeps it working if more are added). */
  [].slice.call(document.querySelectorAll(".mottos")).forEach(function (box) {
    var items = [].slice.call(box.querySelectorAll("li")),  /* the motto lines */
        btn = box.querySelector("button"),                  /* the Pause/Play button */
        k = 0,                                              /* which motto is showing now */
        held = false,                                       /* true while the mouse or keyboard focus is on the box */
        paused = false;                                     /* true after the visitor presses Pause */
    if (!items.length) return;

    /* Reduced motion: show every line and stop here. */
    if (still) { items.forEach(function (li) { li.classList.add("on"); }); return; }

    /* Show motto number n and hide the rest (the "on" class makes a line visible and fades it in). */
    function show(n) { items.forEach(function (li, j) { li.classList.toggle("on", j === n); }); }
    show(0);

    /* Every 5 seconds, move to the next motto, wrapping from the last back to the first, unless held or paused. */
    setInterval(function () { if (held || paused) return; k = (k + 1) % items.length; show(k); }, 5000);

    /* Hold still while someone is pointing at or tabbed into the mottos. */
    box.addEventListener("mouseenter", function () { held = true; });
    box.addEventListener("mouseleave", function () { held = false; });
    box.addEventListener("focusin", function () { held = true; });
    box.addEventListener("focusout", function () { held = false; });

    /* The Pause/Play button flips the paused state, its label, and what it tells screen readers. */
    if (btn) btn.addEventListener("click", function () {
      paused = !paused;
      btn.textContent = paused ? "Play" : "Pause";
      btn.setAttribute("aria-pressed", paused ? "true" : "false");
    });
  });
})();
