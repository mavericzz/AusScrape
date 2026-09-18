const state = { card: null, meeting: 0, race: 0, date: pageDate(), dates: [] };

const $ = (id) => document.getElementById(id);

function pageDate() {
  const match = location.pathname.match(/\/day\/(\d{4}-\d{2}-\d{2})\/?$/);
  return match ? match[1] : null;
}

function prettyDate(iso) {
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
function fmtMoney(v) {
  if (v == null || v === "") return "—";
  const n = Number(v);
  if (Number.isNaN(n)) return "—";
  return n.toLocaleString("en-AU", { style: "currency", currency: "AUD", maximumFractionDigits: 0 });
}
function moneyLine(row) {
  if (!row) return "—";
  if (row.money_bet == null && row.money_pct == null) return "—";
  const pct = row.money_pct == null ? "" : ` · ${(Number(row.money_pct) * 100).toFixed(0)}%`;
  return `${fmtMoney(row.money_bet)}${pct}`;
}
function pct(v) {
  if (v == null) return "—";
  return `${(Number(v) * 100).toFixed(1)}%`;
}
function money(stakePct) {
  const bank = Number($("bankroll").value || 0);
  if (!stakePct) return "—";
  return `$${((bank * Number(stakePct)) / 100).toFixed(2)}`;
}
function fmtTime(iso) {
  if (!iso) return "";
  const d = new Date(iso);
  if (Number.isNaN(d.getTime())) return String(iso);
  return d.toLocaleTimeString("en-AU", { hour: "numeric", minute: "2-digit", timeZone: "Australia/Sydney" });
}

function lastLine(runner) {
  const last = runner.last_run || {};
  const bits = [];
  if (last.finish) bits.push(`${last.finish}${last.beaten_lengths != null ? ` beaten ${last.beaten_lengths}L` : ""}`);
  if (last.track) bits.push(last.track);
  if (last.weight_kg) bits.push(`${last.weight_kg}kg last`);
  if (last.going) bits.push(last.going);
  if (runner.form_string) bits.push(runner.form_string);
  return bits.join(" · ") || "No last-run line";
}

function jumpTo(venue, raceNumber) {
  const mi = (state.card.meetings || []).findIndex((m) => m.venue === venue);
  if (mi < 0) return;
  state.meeting = mi;
  state.race = (state.card.meetings[mi].races || []).findIndex((r) => r.race_number === raceNumber);
  if (state.race < 0) state.race = 0;
  render();
}

function renderDays() {
  const nav = $("days-strip");
  if (!nav) return;
  nav.innerHTML = (state.dates || []).map((row) =>
    `<a class="${row.date === state.date ? "active" : ""}" href="${row.href || `day/${row.date}/`}">${prettyDate(row.date)}</a>`
  ).join("") + `<a href="./">All dates</a>`;
}

function renderBest() {
  const el = $("best-bet");
  const bet = state.card.best_bet;
  if (!bet) {
    el.className = "best empty";
    el.innerHTML = `<b>BEST BET OF THE DAY</b><div class="horse">Waiting on the card</div>`;
    return;
  }
  el.className = "best";
  el.innerHTML = `
    <b>${bet.label || "BEST BET OF THE DAY"}</b>
    <div>
      <div class="horse">${bet.name} <span class="bet-money">${moneyLine(bet)}</span></div>
      <div class="why">${bet.venue || ""} R${bet.race_number} · fig ${bet.figure ?? "—"} · ${fmtOdds(bet.odds)} · model ${pct(bet.p_model)}</div>
    </div>
    <button type="button" id="open-best">Open race</button>
  `;
  $("open-best").onclick = () => jumpTo(bet.venue, bet.race_number);
}

function renderPlays() {
  const plays = state.card.plays || [];
  const el = $("plays-strip");
  if (!plays.length) {
    el.innerHTML = `<div class="play-chip"><b>NO OVERLAY PLAYS</b><span>Rank-1 figures still fill the sheet.</span></div>`;
    return;
  }
  el.innerHTML = plays.map((p, i) => `
    <div class="play-chip" data-i="${i}">
      <b>PLAY · ${p.venue || ""} R${p.race_number}</b>
      <span>${p.name} <small class="bet-money">${fmtMoney(p.money_bet)}</small></span>
      <small>${fmtOdds(p.odds)} · edge ${p.edge == null ? "—" : `${(p.edge * 100).toFixed(0)}%`} · ${money(p.stake_pct)}</small>
    </div>
  `).join("");
  el.querySelectorAll(".play-chip").forEach((chip) => {
    chip.addEventListener("click", () => {
      const play = plays[Number(chip.dataset.i)];
      jumpTo(play.venue, play.race_number);
    });
  });
}

function renderMeetings() {
  const nav = $("meetings");
  nav.innerHTML = (state.card.meetings || []).map((m, i) =>
    `<button class="${i === state.meeting ? "active" : ""}" data-i="${i}">${m.venue}</button>`
  ).join("");
  nav.querySelectorAll("button").forEach((btn) => {
    btn.addEventListener("click", () => {
      state.meeting = Number(btn.dataset.i);
      state.race = 0;
      render();
    });
  });
}

function renderRaces() {
  const meeting = (state.card.meetings || [])[state.meeting];
  const box = $("races");
  if (!meeting) { box.innerHTML = ""; return; }
  box.innerHTML = (meeting.races || []).map((r, i) => `
    <button class="${i === state.race ? "active" : ""}" data-i="${i}">
      R${r.race_number} ${fmtTime(r.off_time)}
      <small>${r.name || ""} · ${(r.runners || []).length} runners</small>
    </button>
  `).join("");
  box.querySelectorAll("button").forEach((btn) => {
    btn.addEventListener("click", () => {
      state.race = Number(btn.dataset.i);
      render();
    });
  });
}

function renderSheet() {
  const meeting = (state.card.meetings || [])[state.meeting];
  const race = meeting && (meeting.races || [])[state.race];
  const sheet = $("sheet");
  if (!race) {
    sheet.innerHTML = `<div class="empty">No race loaded for ${state.date || "this date"}.</div>`;
    return;
  }
  const rows = (race.runners || []).map((r) => `
    <tr class="${(r.action || "").toLowerCase()}">
      <td class="num">${r.rank || ""}</td>
      <td class="num">${r.number || ""}</td>
      <td>
        <div class="horse">${r.name} <span class="bet-money">${fmtMoney(r.money_bet)}</span></div>
        <details><summary>${lastLine(r)}</summary>
          <div>Figure ${r.figure ?? "—"} · base ${r.base ?? "—"} · sectional ${r.sectional ?? "—"} · jockey ${r.jockey || "—"} · ${r.comments || "no comment"}</div>
        </details>
      </td>
      <td class="num">${r.barrier ?? "—"}</td>
      <td class="num">${r.weight_kg ?? "—"}</td>
      <td class="num">${r.rating ?? "—"}</td>
      <td class="num">${r.figure ?? "—"}</td>
      <td class="num">${pct(r.p_model)}</td>
      <td class="num">${fmtOdds(r.odds)}</td>
      <td class="num">${fmtMoney(r.money_bet)}</td>
      <td class="num ${r.edge > 0 ? "edge-pos" : ""}">${r.edge == null ? "—" : `${(r.edge * 100).toFixed(0)}%`}</td>
      <td class="num">${money(r.stake_pct)}</td>
      <td class="action">${r.action || ""}</td>
    </tr>
  `).join("");
  sheet.innerHTML = `
    <h2>R${race.race_number} · ${race.name}</h2>
    <div class="meta">${meeting.venue} · ${race.going || ""} · ${race.distance_m || ""}m · ${fmtTime(race.off_time)} · Money is each horse’s share of a $10,000 win book from current odds</div>
    <table>
      <thead>
        <tr>
          <th>#</th><th>No</th><th>Horse / last run</th><th>Dr</th><th>Wgt kg</th>
          <th>Rtg</th><th>Fig</th><th>Model</th><th>Odds</th><th>Money</th><th>Edge</th><th>Stake</th><th></th>
        </tr>
      </thead>
      <tbody>${rows}</tbody>
    </table>
  `;
}

function render() {
  const iso = state.card.date || state.date;
  const nMeet = (state.card.meetings || []).length;
  const nPlay = (state.card.plays || []).length;
  document.title = `AU Desk — ${iso || "card"}`;
  const title = $("page-title");
  if (title && iso) title.textContent = prettyDate(iso);
  $("card-meta").textContent = `${iso || ""} · ${nMeet} meetings · ${nPlay} win plays`;
  const jev = (state.card.jev || []).map((j) => `${j.source}:${j.ok ? "ok" : (j.status || "blocked")}`).join(" · ");
  if (jev) $("card-meta").textContent += ` · jev ${jev}`;
  renderDays();
  renderBest();
  renderPlays();
  renderMeetings();
  renderRaces();
  renderSheet();
}

async function fetchCard(iso) {
  return loadCardPayload(iso);
}

async function load() {
  if (!state.date) {
    location.replace(assetUrl("./"));
    return;
  }
  const dates = await loadDatesPayload();
  state.dates = dates.dates || [];
  state.card = await fetchCard(state.date);
  state.meeting = 0;
  state.race = 0;
  const scrape = $("rescrape");
  if (scrape) scrape.hidden = location.hostname.endsWith("github.io");
  render();
}

$("bankroll").addEventListener("input", render);
$("rescrape").addEventListener("click", async () => {
  $("card-meta").textContent = `Scraping ${state.date}…`;
  await fetch(`/api/scrape?date=${encodeURIComponent(state.date)}`, { method: "POST" });
  const poll = setInterval(async () => {
    const st = await fetch("/api/status").then((r) => r.json());
    if (!st.running) {
      clearInterval(poll);
      await load();
    }
  }, 4000);
});

load().catch((err) => {
  $("card-meta").textContent = `Failed to load card: ${err}`;
});
