async function load() {
  const { baseUrl, apiKey } = await chrome.storage.local.get(["baseUrl","apiKey"]);
  if (baseUrl) document.getElementById("baseUrl").value = baseUrl;
  if (apiKey) document.getElementById("apiKey").value = apiKey;
}
load();

document.getElementById("save").addEventListener("click", async () => {
  const baseUrl = document.getElementById("baseUrl").value.trim();
  const apiKey = document.getElementById("apiKey").value.trim();
  await chrome.storage.local.set({ baseUrl, apiKey });
  document.getElementById("out").textContent = "Saved.";
});

document.getElementById("connect").addEventListener("click", async () => {
  const { baseUrl } = await chrome.storage.local.get(["baseUrl"]);
  if (!baseUrl) return (document.getElementById("out").textContent = "Set Backend URL first.");
  chrome.tabs.create({ url: baseUrl.replace(/\/$/,"") + "/api/auth/onedrive/start" });
});

document.getElementById("status").addEventListener("click", async () => {
  const { baseUrl } = await chrome.storage.local.get(["baseUrl"]);
  if (!baseUrl) return (document.getElementById("out").textContent = "Set Backend URL first.");
  const r = await fetch(baseUrl.replace(/\/$/,"") + "/api/auth/onedrive/status");
  const j = await r.json();
  document.getElementById("out").textContent = j.connected_onedrive ? "OneDrive: Connected" : "OneDrive: Not connected";
});

document.getElementById("export").addEventListener("click", async () => {
  const { baseUrl, apiKey } = await chrome.storage.local.get(["baseUrl","apiKey"]);
  if (!baseUrl) return (document.getElementById("out").textContent = "Set Backend URL first.");

  const [tab] = await chrome.tabs.query({ active: true, currentWindow: true });
  const resp = await chrome.tabs.sendMessage(tab.id, { action: "SCRAPE_CHAT" });
  if (!resp?.ok) return (document.getElementById("out").textContent = "Could not scrape chat.");

  const url = baseUrl.replace(/\/$/,"") + "/api/ingest/chat";
  const headers = { "Content-Type": "application/json" };
  if (apiKey) headers["X-API-Key"] = apiKey;

  const r = await fetch(url, { method: "POST", headers, body: JSON.stringify(resp.payload) });
  const j = await r.json();
  document.getElementById("out").textContent = JSON.stringify(j, null, 2);
});
