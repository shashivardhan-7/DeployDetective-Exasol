const $ = (id) => document.getElementById(id);

function escapeHtml(s) {
  return String(s ?? "").replace(/[&<>\"]/g, (c) => ({"&":"&amp;","<":"&lt;",">":"&gt;","\"":"&quot;"}[c]));
}

function renderRows(columns, rows) {
  if (!rows || !rows.length) return "<div class='detail'>No rows returned.</div>";
  const head = columns.map(c => `<th>${escapeHtml(c)}</th>`).join("");
  const body = rows.slice(0, 8).map(r => `<tr>${r.map(x => `<td>${escapeHtml(x)}</td>`).join("")}</tr>`).join("");
  return `<div class='small-table'><table><thead><tr>${head}</tr></thead><tbody>${body}</tbody></table></div>`;
}

function renderTrace(trace) {
  if (!trace?.length) return "<div class='trace empty'>No trace.</div>";
  return trace.map(t => {
    const timing = t.elapsed_ms != null ? `${Number(t.elapsed_ms).toFixed(1)} ms` : (t.status || "");
    let body = "";
    if (t.detail) body += `<div class='detail'><b>Plan:</b> ${escapeHtml(JSON.stringify(t.detail))}</div>`;
    if (t.evidence) body += `<div class='detail'>${escapeHtml(t.evidence)}</div>`;
    if (t.decision) body += `<div class='decision-line'><b>Decision:</b> ${escapeHtml(t.decision)} <span class='confidence'>${t.confidence != null ? `${(Number(t.confidence)*100).toFixed(0)}% confidence` : ""}</span></div>`;
    if (t.message) body += `<div class='detail'>${escapeHtml(t.message)}</div>`;
    if (t.simulated) body += `<div class='simulated'>SIMULATED ACTION · NO PRODUCTION SYSTEM MODIFIED</div>`;
    if (t.sql) body += `<pre>${escapeHtml(t.sql)}</pre>${renderRows(t.columns, t.rows)}`;
    if (t.verified != null) body += `<div class='verification ${t.verified ? "pass" : "fail"}'>${t.verified ? '✓ RECOVERY CONFIRMED' : '✕ RECOVERY NOT CONFIRMED'}</div>`;
    return `<article class='card'><div class='card-head'><strong>${escapeHtml(String(t.step).padStart(2,'0'))} · ${escapeHtml(t.name)}</strong><span>${escapeHtml(timing)}</span></div><div class='card-body'>${body || '<div class="detail">Complete.</div>'}</div></article>`;
  }).join("");
}

async function refreshHealth() {
  try {
    const res = await fetch("/api/health");
    const data = await res.json();
    const badge = $("db-badge");
    if (data.exasol === "connected") {
      badge.className = "badge good-badge";
      badge.innerHTML = `<span class="dot"></span> Exasol connected · ${escapeHtml(data.schema)}`;
    } else {
      badge.className = "badge bad-badge";
      badge.innerHTML = `<span class="dot bad-dot"></span> Exasol unavailable`;
    }
  } catch {
    $("db-badge").className = "badge bad-badge";
    $("db-badge").innerHTML = `<span class="dot bad-dot"></span> API unavailable`;
  }
}

$("run").addEventListener("click", async () => {
  const message = $("request").value.trim();
  if (!message) return;
  $("run").disabled = true;
  $("status").className = "status run";
  $("status").textContent = "INVESTIGATING";
  $("trace").innerHTML = "<div class='trace empty'>The agent is querying Exasol and evaluating the evidence…</div>";
  const started = performance.now();
  try {
    const res = await fetch("/api/investigate", {
      method: "POST",
      headers: {"Content-Type":"application/json"},
      body: JSON.stringify({message})
    });
    const data = await res.json();
    if (!res.ok) throw new Error(data.detail || "Request failed");
    $("status").className = data.verified ? "status ok" : "status run";
    $("status").textContent = data.verified ? "VERIFIED RECOVERY" : "INVESTIGATION COMPLETE";
    $("narrative").textContent = data.narrative;
    $("service").textContent = data.service_id;
    $("action").textContent = data.action ? data.action.action_type : data.decision;
    $("verification").textContent = data.verified ? "PASS" : "CHECK";
    $("trace").innerHTML = renderTrace(data.trace);
    $("timing").textContent = `${((performance.now()-started)/1000).toFixed(2)} s end-to-end`;
  } catch (err) {
    $("status").className = "status run";
    $("status").textContent = "ERROR";
    $("narrative").textContent = err.message;
    $("trace").innerHTML = "";
  } finally {
    $("run").disabled = false;
  }
});

refreshHealth();
setInterval(refreshHealth, 10000);
