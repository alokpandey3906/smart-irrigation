"use strict";
const $ = id => document.getElementById(id);

$("form").addEventListener("submit", async event => {
  event.preventDefault();
  $("errors").innerHTML = "";
  const body = Object.fromEntries(new FormData(event.target));
  try {
    const res = await fetch("/api/recommend", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(body),
    });
    const data = await res.json();
    if (!res.ok) { showErrors(data.errors || ["Something went wrong."]); return; }
    show(data);
  } catch {
    showErrors(["Could not reach the server. Check that run.py is running."]);
  }
});

function showErrors(list) {
  $("errors").innerHTML = list.map(e => `<li>${e.replace(/[<>&]/g, "")}</li>`).join("");
}

function show(r) {
  $("empty").hidden = true;
  $("output").hidden = false;
  $("verdict").className = "verdict " + r.level;
  $("msg").textContent = r.message;
  $("fill").style.height = r.moisture_pct + "%";
  $("trigger").style.bottom = r.trigger_pct + "%";
  $("gpct").textContent = r.moisture_pct + "% of usable water left";
  $("litres").textContent = r.litres.toLocaleString();
  $("hours").textContent = r.hours;
  $("gross").textContent = r.gross_mm;
  $("etc").textContent = r.etc;
  $("et0").textContent = r.et0;
  $("kc").textContent = r.kc;
  $("depl").textContent = r.depletion;
  $("raw").textContent = r.raw;
  $("rain").textContent = r.rain_effective;
  $("days").textContent = r.days_left >= 30 ? "30+" : r.days_left;
}
