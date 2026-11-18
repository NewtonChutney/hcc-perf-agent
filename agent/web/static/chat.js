// Chat panel: keeps the conversation in sessionStorage, posts it to /api/chat each turn.
(function () {
  const root = document.getElementById("chat");
  if (!root) return;
  const log = root.querySelector(".chat-log");
  const form = root.querySelector(".chat-form");
  const input = form.querySelector("textarea");
  const send = form.querySelector("button:not([type])");
  const job = root.dataset.job, build = root.dataset.build;
  const key = "hpa-chat:" + (job ? job + "#" + build : "global");
  let messages = JSON.parse(sessionStorage.getItem(key) || "[]");

  function esc(s) {
    return s.replace(/[&<>"']/g, c => ({"&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;", "'": "&#39;"}[c]));
  }

  // Small markdown subset on escaped text: tables, headings, lists, bold, code.
  function render(md) {
    const lines = esc(md).split("\n");
    let html = "", i = 0;
    const inline = s => s.replace(/`([^`]+)`/g, "<code>$1</code>").replace(/\*\*([^*]+)\*\*/g, "<b>$1</b>");
    const cells = l => l.trim().replace(/^\||\|$/g, "").split("|").map(c => c.trim());
    while (i < lines.length) {
      const l = lines[i];
      if (/^\s*\|/.test(l) && i + 1 < lines.length && /^\s*\|?\s*:?-{3,}/.test(lines[i + 1])) {
        html += "<table class='compact'><thead><tr>" + cells(l).map(c => "<th>" + inline(c) + "</th>").join("") + "</tr></thead><tbody>";
        i += 2;
        while (i < lines.length && /^\s*\|/.test(lines[i])) {
          html += "<tr>" + cells(lines[i]).map(c => "<td>" + inline(c) + "</td>").join("") + "</tr>";
          i++;
        }
        html += "</tbody></table>";
        continue;
      }
      if (/^#{1,4}\s/.test(l)) html += "<p><b>" + inline(l.replace(/^#+\s/, "")) + "</b></p>";
      else if (/^\s*[-*]\s/.test(l)) html += "<div class='li'>• " + inline(l.replace(/^\s*[-*]\s/, "")) + "</div>";
      else if (l.trim() === "") html += "<div class='gap'></div>";
      else html += "<div>" + inline(l) + "</div>";
      i++;
    }
    return html;
  }

  function add(role, content, tools) {
    const div = document.createElement("div");
    div.className = "msg " + role;
    div.innerHTML = role === "user" ? esc(content) : render(content);
    if (tools && tools.length) {
      const t = document.createElement("div");
      t.className = "tools";
      t.textContent = "Tools used: " + tools.map(x => x.name + "(" + (x.arguments || "") + ")" + (x.ok ? "" : " ✗")).join(", ");
      div.appendChild(t);
    }
    log.appendChild(div);
    log.scrollTop = log.scrollHeight;
    return div;
  }

  messages.forEach(m => add(m.role, m.content, m.tools));

  async function ask(q) {
    q = q.trim();
    if (!q || send.disabled) return;
    messages.push({role: "user", content: q});
    add("user", q);
    input.value = "";
    send.disabled = true;
    const pending = add("assistant pending", "Looking at the data…");
    try {
      const r = await fetch("/api/chat", {
        method: "POST",
        headers: {"Content-Type": "application/json"},
        body: JSON.stringify({messages: messages.map(m => ({role: m.role, content: m.content})), job, build}),
      });
      const data = await r.json().catch(() => ({error: "HTTP " + r.status}));
      pending.remove();
      if (!r.ok || data.error) {
        messages.pop();
        add("assistant error", "Error: " + (data.error || data.detail || r.status));
      } else {
        messages.push({role: "assistant", content: data.reply, tools: data.tools});
        add("assistant", data.reply, data.tools);
      }
    } catch (e) {
      pending.remove();
      messages.pop();
      add("assistant error", "Error: " + e);
    } finally {
      send.disabled = false;
      sessionStorage.setItem(key, JSON.stringify(messages));
    }
  }

  form.addEventListener("submit", e => { e.preventDefault(); ask(input.value); });
  input.addEventListener("keydown", e => {
    if (e.key === "Enter" && !e.shiftKey) { e.preventDefault(); ask(input.value); }
  });
  root.querySelectorAll(".chat-suggestions button").forEach(b => b.addEventListener("click", () => ask(b.textContent)));
  root.querySelector(".chat-reset").addEventListener("click", () => {
    messages = [];
    sessionStorage.removeItem(key);
    log.innerHTML = "";
  });
})();
