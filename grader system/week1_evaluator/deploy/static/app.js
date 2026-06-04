// ── Drop zone helper ──────────────────────────────────────────────────────────
function setupDrop(dropId, inputId, nameId, multi, onFiles) {
  const drop = document.getElementById(dropId);
  const inp  = document.getElementById(inputId);
  const nm   = document.getElementById(nameId);
  if (!drop) return;
  const handle = files => {
    if (!files || !files.length) return;
    if (nm) nm.textContent = files.length === 1 ? files[0].name : `${files.length} files selected`;
    onFiles(files);
  };
  inp.addEventListener("change", () => handle(inp.files));
  drop.addEventListener("dragover",  e => { e.preventDefault(); drop.classList.add("drag-over"); });
  drop.addEventListener("dragleave", () => drop.classList.remove("drag-over"));
  drop.addEventListener("drop", e => { e.preventDefault(); drop.classList.remove("drag-over"); handle(e.dataTransfer.files); });
}

// ── Upload .eep1 to server ────────────────────────────────────────────────────
async function uploadEep1(file) {
  const form = new FormData();
  form.append("file", file);
  const resp = await fetch("/api/grade", { method: "POST", body: form });
  const data = await resp.json();
  if (!resp.ok) throw new Error(data.error || "Server error");
  return data;
}

// ═══════════════════════════════════════════════════════════════════════════════
// PAGE: index.html — Student submission + grading
// ═══════════════════════════════════════════════════════════════════════════════
if (document.getElementById("submitBtn")) {
  const btn       = document.getElementById("submitBtn");
  const errMsg    = document.getElementById("errorMsg");
  const loadCard  = document.getElementById("loadingCard");
  const resultSec = document.getElementById("resultSection");
  let selectedFile = null;

  setupDrop("dropZone", "fileInput", "fileName", false, files => {
    selectedFile = files[0];
    btn.disabled = false;
    errMsg.style.display = "none";
  });

  btn.addEventListener("click", async () => {
    if (!selectedFile) return;
    errMsg.style.display  = "none";
    resultSec.style.display = "none";
    loadCard.style.display  = "block";
    btn.disabled = true;
    btn.textContent = "Grading…";

    try {
      const data = await uploadEep1(selectedFile);
      loadCard.style.display = "none";
      renderResult(data);
      btn.textContent = "Submit & Grade →";
      btn.disabled = false;
    } catch (e) {
      loadCard.style.display = "none";
      errMsg.textContent = "❌ " + e.message;
      errMsg.style.display = "block";
      btn.textContent = "Submit & Grade →";
      btn.disabled = false;
    }
  });

  function renderResult(data) {
    const g = data.grading;

    // Grade banner
    const banner = document.getElementById("gradeBanner");
    const circle = document.getElementById("gradeCircle");
    const cls    = g.grade.replace("+", "-plus");
    circle.className = `grade-circle ${cls}`;
    circle.textContent = g.grade;

    document.getElementById("gradeStudent").textContent = `Student: ${data.student_id}`;
    document.getElementById("gradeScore").textContent   = `Score: ${g.earned}/${g.total} (${g.pct}%)`;
    document.getElementById("gradeTime").textContent    = `Submitted: ${data.timestamp}`;

    // Passed
    const passedList = document.getElementById("passedList");
    passedList.innerHTML = "";
    g.passed.forEach(c => {
      const d = document.createElement("div");
      d.className = "check-row pass";
      d.innerHTML = `<div class="check-icon">✅</div>
        <div class="check-body">
          <div class="check-name">${c.name}</div>
          <div class="check-pts">+${c.points} point${c.points !== 1 ? "s" : ""}</div>
        </div>`;
      passedList.appendChild(d);
    });

    // Failed
    const failedCard = document.getElementById("failedCard");
    const failedList = document.getElementById("failedList");
    failedList.innerHTML = "";
    if (g.failed.length > 0) {
      g.failed.forEach(c => {
        const d = document.createElement("div");
        d.className = "check-row fail";
        d.innerHTML = `<div class="check-icon">❌</div>
          <div class="check-body">
            <div class="check-name">${c.name}</div>
            ${c.reason ? `<div class="check-hint" style="color:#fca5a5;margin-bottom:.4rem">${c.reason}</div>` : ""}
            <div class="check-hint">💡 How to fix:\n${c.hint}</div>
            <div class="check-pts">-${c.points} point${c.points !== 1 ? "s" : ""} missed</div>
          </div>`;
        failedList.appendChild(d);
      });
      failedCard.style.display = "block";
    } else {
      failedCard.style.display = "none";
    }

    document.getElementById("resultSection").style.display = "block";
    document.getElementById("resultSection").scrollIntoView({ behavior: "smooth" });
  }
}

// ═══════════════════════════════════════════════════════════════════════════════
// PAGE: dashboard.html — Batch grading
// ═══════════════════════════════════════════════════════════════════════════════
if (document.getElementById("batchBtn")) {
  const btn = document.getElementById("batchBtn");
  let files = [];

  setupDrop("dropZone", "fileInput", "fileName", true, f => {
    files = Array.from(f);
    btn.disabled = files.length === 0;
  });

  btn.addEventListener("click", async () => {
    btn.disabled = true;
    btn.textContent = `Grading ${files.length} submissions…`;

    const results = await Promise.all(files.map(async f => {
      try {
        const data = await uploadEep1(f);
        return { ...data, fileName: f.name, error: null };
      } catch (e) {
        return { fileName: f.name, error: e.message, student_id: f.name };
      }
    }));

    renderDashboard(results);
    btn.textContent = "Grade All Submissions →";
    btn.disabled = false;
  });

  function renderDashboard(results) {
    const total   = results.length;
    const pass    = results.filter(r => !r.error && r.overall === "PASS").length;
    const fail    = results.filter(r => !r.error && r.overall === "FAIL").length;
    const errors  = results.filter(r => r.error).length;

    document.getElementById("sTotal").textContent = total;
    document.getElementById("sPass").textContent  = pass;
    document.getElementById("sFail").textContent  = fail;
    document.getElementById("sError").textContent = errors;
    document.getElementById("statsRow").style.display  = "grid";
    document.getElementById("tableWrap").style.display = "block";

    const tbody = document.getElementById("tableBody");
    tbody.innerHTML = "";
    results.forEach(r => {
      const tr = document.createElement("tr");
      if (r.error) {
        tr.innerHTML = `
          <td><strong>${r.student_id}</strong></td>
          <td style="color:var(--muted)">—</td>
          <td>—</td>
          <td><span class="badge error">Error</span></td>
          <td style="color:#fca5a5;font-size:.8rem">${r.error}</td>`;
      } else {
        const g = r.grading;
        tr.innerHTML = `
          <td><strong>${r.student_id}</strong></td>
          <td style="color:var(--muted);font-size:.8rem">${r.timestamp || "—"}</td>
          <td>${g.earned}/${g.total} (${g.pct}%)</td>
          <td><span class="badge ${r.overall === "PASS" ? "pass" : "fail"}">${g.grade} — ${r.overall}</span></td>
          <td style="font-size:.8rem;color:var(--muted)">${g.failed.length} issue${g.failed.length !== 1 ? "s" : ""}</td>`;
      }
      tbody.appendChild(tr);
    });
  }
}
