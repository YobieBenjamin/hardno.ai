/* ==========================================================================================================
   gate.js: the temporary "coming soon" entry gate for hardno.ai (added 30 October 2026).

   Why it exists: the site is being reworked to focus on banks. Until that is done, the front page (index.html)
   says "coming soon" and asks for a password, and the existing pages sit behind it. The password is HELLNO.

   This is a courtesy curtain, NOT security, and is meant to be obvious about it:
     - The password is written in this file, which anyone can read.
     - The pages behind the gate are still ordinary public files. Anyone who turns script off, and every search
       crawler, still sees them. Nothing private belongs behind this gate.
   Like a velvet rope at a gallery: it says "not open yet", it does not lock a door.

   What it does, on the two kinds of page:
     - Inside pages (home, use cases, methodology, case against) carry <meta name="hardno-gate" content="inside">.
       If this browser has not entered the password, the visitor is sent to the front page straight away.
     - The front page carries <meta name="hardno-gate" content="door">. When its form is sent, this script checks
       the password; on a match it remembers that in this browser and opens home.html, otherwise it says so.

   It stores one small flag in this browser only (localStorage, or sessionStorage if that is blocked), sends
   nothing anywhere and loads nothing else. Every storage call is wrapped, because private windows can refuse it.
   ========================================================================================================== */
(function () {
  /* The password, and the name of the flag this browser keeps once it has been entered. */
  var PASSWORD = "HELLNO";
  var FLAG = "hardno-entered";

  /* Read the flag. Storage can be switched off or throw in private windows, so every call is wrapped. */
  function entered() {
    try { if (window.localStorage.getItem(FLAG) === "yes") return true; } catch (e) { /* storage blocked */ }
    try { if (window.sessionStorage.getItem(FLAG) === "yes") return true; } catch (e) { /* storage blocked */ }
    return false;
  }

  /* Remember the flag: in localStorage if allowed (stays after the tab closes), else for this tab only. */
  function remember() {
    try { window.localStorage.setItem(FLAG, "yes"); return; } catch (e) { /* fall through */ }
    try { window.sessionStorage.setItem(FLAG, "yes"); } catch (e) { /* nothing more we can do; the visitor re-enters next time */ }
  }

  /* Which kind of page is this? The meta tag sits above this script in <head>, so it can be read already. */
  var meta = document.querySelector('meta[name="hardno-gate"]');
  var kind = meta ? meta.getAttribute("content") : "";

  /* Inside page and no password yet: go to the front page. replace() keeps the gated page out of the Back history. */
  if (kind === "inside" && !entered()) {
    window.location.replace("./");
    return;
  }

  /* The front page: wire up the password form once the page has loaded. */
  if (kind === "door") {
    document.addEventListener("DOMContentLoaded", function () {
      var form = document.getElementById("gate-form");
      var input = document.getElementById("gate-password");
      var note = document.getElementById("gate-note");
      if (!form || !input) return;

      /* Already entered in this browser: offer the way in without asking again. */
      if (entered() && note) note.textContent = "You are already in. Press Enter to continue.";

      form.addEventListener("submit", function (ev) {
        /* Never let the form actually post anywhere (the page's security policy forbids it anyway). */
        ev.preventDefault();
        /* Spaces around the word are forgiven; the word itself must match, in capitals. */
        if (entered() || input.value.trim() === PASSWORD) {
          remember();
          window.location.href = "home.html";
        } else if (note) {
          note.textContent = "Not quite. Try again.";
          input.select();
        }
      });
    });
  }
})();
