function pretty(iso) {
  const d = new Date(`${iso}T00:00:00+10:00`);
  return d.toLocaleDateString("en-AU", {
    weekday: "long",
    day: "numeric",
    month: "long",
    year: "numeric",
    timeZone: "Australia/Sydney",
  });
}

function fmtOdds(v) {
  if (v == null) return "—";
  return Number(v).toFixed(2);
}

async function load() {
  const box = document.getElementById("days");
  const payload = await loadDatesPayload();
  const rows = payload.dates || [];
  if (!rows.length) {
    box.innerHTML = `<p class="empty">No day cards yet. Run scrape_au.py --date 2026-09-19</p>`;
    return;
  }
  box.innerHTML = rows.map((row) => {
    const bet = row.best_bet;
    const betLine = bet
      ? `${bet.name} · ${bet.venue || ""} R${bet.race_number} · ${fmtOdds(bet.odds)}`
      : "No best bet published";
    return `
      <a class="day-card" href="${row.href || `day/${row.date}/`}">
        <b>${pretty(row.date)}</b>
        <span class="horse">${bet ? bet.name : "Open desk"}</span>
        <small>${row.meetings} meetings · ${row.plays} plays</small>
        <small>${betLine}</small>
      </a>
    `;
  }).join("");
}

load().catch((err) => {
  document.getElementById("days").textContent = `Failed to load dates: ${err}`;
});
