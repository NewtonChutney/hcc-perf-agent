// CPT runs page: filters apply as you change them, without reloading the page.
// The server renders the results area on its own when asked with X-Partial: 1; the filter
// values stay in the URL (pushState), so links, refresh and Back/Forward keep working.
// Without JavaScript the form's Apply button does a normal GET.
(function () {
  const form = document.getElementById("run-filters");
  const results = document.getElementById("runs-results");
  if (!form || !results || !window.fetch) return;
  const note = form.querySelector(".loading-note");
  form.querySelector(".apply").hidden = true;
  let inflight = null, timer = null;

  // Empty values ("all") are left out of the URL.
  function queryFromForm() {
    const params = new URLSearchParams();
    for (const [k, v] of new FormData(form)) if (v !== "") params.append(k, v);
    return params.toString();
  }

  // Same defaults as runs_page() in app.py, for URLs without a parameter.
  const DEFAULTS = {days: "7"};

  function formFromQuery(query) {
    const params = new URLSearchParams(query);
    for (const el of form.elements) {
      if (!el.name) continue;
      if (el.type === "checkbox") el.checked = params.get(el.name) === el.value;
      else el.value = params.has(el.name) ? params.get(el.name) : (DEFAULTS[el.name] || "");
    }
  }

  async function load(query, push) {
    const url = location.pathname + (query ? "?" + query : "");
    if (inflight) inflight.abort();
    inflight = new AbortController();
    results.classList.add("loading");
    note.hidden = false;
    try {
      const r = await fetch(url, {headers: {"X-Partial": "1"}, signal: inflight.signal});
      if (!r.ok) throw new Error("HTTP " + r.status);
      results.innerHTML = await r.text();
      if (push && url !== location.pathname + location.search) history.pushState({query}, "", url);
    } catch (e) {
      if (e.name === "AbortError") return;
      location.href = url;  // fall back to a normal page load
      return;
    } finally {
      results.classList.remove("loading");
      note.hidden = true;
    }
  }

  // Selects and the checkbox apply at once; the days box waits until typing pauses.
  form.addEventListener("change", e => { if (e.target.name !== "days") load(queryFromForm(), true); });
  form.addEventListener("input", e => {
    if (e.target.name !== "days") return;
    clearTimeout(timer);
    timer = setTimeout(() => { if (form.days.checkValidity()) load(queryFromForm(), true); }, 500);
  });
  form.addEventListener("submit", e => { e.preventDefault(); load(queryFromForm(), true); });

  window.addEventListener("popstate", () => {
    const query = location.search.replace(/^\?/, "");
    formFromQuery(query);
    load(query, false);
  });

  results.addEventListener("click", e => {
    // "review pending" shortcut: set the Review filter instead of navigating.
    const link = e.target.closest("a.pending-link");
    if (link) {
      e.preventDefault();
      form.review.value = "pending";
      load(queryFromForm(), true);
    }
  });

  // Inline Agree: post in the background, then refresh the results in place.
  results.addEventListener("submit", async e => {
    const f = e.target.closest("form.inline-agree");
    if (!f) return;
    e.preventDefault();
    const button = f.querySelector("button");
    button.disabled = true;
    button.textContent = "Saving…";
    try {
      const r = await fetch(f.action, {method: "POST", body: new URLSearchParams(new FormData(f)), redirect: "manual"});
      // Success is a 303 redirect (opaque with redirect: "manual"); anything else is an error.
      if (r.type !== "opaqueredirect" && !r.ok) throw new Error((await r.text()).slice(0, 200) || r.status);
      await load(location.search.replace(/^\?/, ""), false);
    } catch (err) {
      button.disabled = false;
      button.textContent = "✓ Agree";
      alert("Review not saved: " + err.message);
    }
  });
})();
