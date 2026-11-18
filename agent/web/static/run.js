// Run page: save a review without leaving the page. The server answers a review posted
// with X-Partial: 1 with the refreshed review area, which replaces the old one, so there's
// no redirect and no extra history entry. Without JavaScript the form posts normally.
(function () {
  const section = document.getElementById("review-section");
  if (!section || !window.fetch) return;

  section.addEventListener("submit", async e => {
    const form = e.target.closest("form.review");
    if (!form) return;
    e.preventDefault();
    const body = new URLSearchParams(new FormData(form));
    if (e.submitter && e.submitter.name) body.set(e.submitter.name, e.submitter.value);  // Agree or Save correction
    const buttons = form.querySelectorAll("button");
    buttons.forEach(b => b.disabled = true);
    const label = e.submitter && e.submitter.textContent;
    if (e.submitter) e.submitter.textContent = "Saving…";
    section.classList.add("loading");
    try {
      const r = await fetch(form.action, {method: "POST", body, headers: {"X-Partial": "1"}});
      if (!r.ok) {
        let msg = r.status;
        try { msg = (await r.json()).detail || msg; } catch (_) {}
        throw new Error(msg);
      }
      section.innerHTML = await r.text();
      section.scrollIntoView({block: "nearest", behavior: "smooth"});
    } catch (err) {
      buttons.forEach(b => b.disabled = false);
      if (e.submitter) e.submitter.textContent = label;
      let note = form.querySelector(".save-error");
      if (!note) {
        note = document.createElement("p");
        note.className = "error save-error";
        form.appendChild(note);
      }
      note.textContent = "Not saved: " + err.message;
    } finally {
      section.classList.remove("loading");
    }
  });
})();
