function assetUrl(path) {
  return new URL(String(path).replace(/^\//, ""), document.baseURI).href;
}

async function fetchJSON(path) {
  const res = await fetch(assetUrl(path));
  if (!res.ok) throw new Error(`${res.status} ${path}`);
  return res.json();
}

async function loadDatesPayload() {
  try {
    return await fetchJSON("api/dates");
  } catch {
    return fetchJSON("data/dates.json");
  }
}

async function loadCardPayload(iso) {
  try {
    return await fetchJSON(iso ? `api/card?date=${encodeURIComponent(iso)}` : "api/card");
  } catch {
    if (!iso) throw new Error("no date");
    return fetchJSON(`data/card_${iso}.json`);
  }
}
