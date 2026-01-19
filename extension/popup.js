async function load() {
  const { baseUrl, apiKey, autoExport } = await chrome.storage.local.get(["baseUrl","apiKey","autoExport"]);
  if (baseUrl) document.getElementById("baseUrl").value = baseUrl;
  if (apiKey) document.getElementById("apiKey").value = apiKey;
  document.getElementById("autoExport").checked = !!autoExport;
}
load();

function out(x){ document.getElementById("out").textContent = x; }

document.getElementById("save").addEventListener("click", async () => {
  const baseUrl = document.getElementById("baseUrl").value.trim();
  const apiKey = document.getElementById("apiKey").value.trim();
  const autoExport = document.getElementById("autoExport").checked;
  await chrome.storage.local.set({ baseUrl, apiKey, autoExport });
  out("Saved.");
});

document.getElementById("autoExport").addEventListener("change", async (e) => {
  const autoExport = e.target.checked;
  await chrome.storage.local.set({ autoExport });
  out(autoExport ? "Auto-export enabled." : "Auto-export disabled.");
});

document.getElementById("connect").addEventListener("click", async () => {
  const { baseUrl } = await chrome.storage.local.get(["baseUrl"]);
  if (!baseUrl) return out("Set Backend URL first.");
  chrome.tabs.create({ url: baseUrl.replace(/\/$/,"") + "/api/auth/dropbox/start" });
});

document.getElementById("status").addEventListener("click", async () => {
  const { baseUrl } = await chrome.storage.local.get(["baseUrl"]);
  if (!baseUrl) return out("Set Backend URL first.");
  const r = await fetch(baseUrl.replace(/\/$/,"") + "/api/auth/dropbox/status");
  const j = await r.json();
  out(j.connected_dropbox ? "Dropbox: Connected" : "Dropbox: Not connected");
});

async function scrapeActiveTab(){
  const [tab] = await chrome.tabs.query({ active: true, currentWindow: true });
  const resp = await chrome.tabs.sendMessage(tab.id, { action: "SCRAPE_CHAT" });
  if (!resp?.ok) throw new Error("Could not scrape chat.");
  return resp.payload;
}

document.getElementById("export").addEventListener("click", async () => {
  try{
    const payload = await scrapeActiveTab();
    const r = await chrome.runtime.sendMessage({ action:"EXPORT_PAYLOAD", payload });
    if (!r?.ok) return out("Export failed: " + (r?.error || "unknown"));
    out(JSON.stringify(r.result, null, 2));
  } catch(e){
    out(String(e));
  }
});

document.getElementById("recent").addEventListener("click", async () => {
  try{
    const [tab] = await chrome.tabs.query({ active: true, currentWindow: true });
    const list = await chrome.tabs.sendMessage(tab.id, { action:"GET_RECENT_CHAT_URLS", limit: 50 });
    const urls = (list?.urls || []).slice(0, 50);
    if (!urls.length) return out("Could not find recent chats in sidebar. Open ChatGPT home with sidebar visible.");
    out("Batch exporting " + urls.length + " chats...");
    const r = await chrome.runtime.sendMessage({ action:"BATCH_EXPORT_URLS", urls });
    out(JSON.stringify(r, null, 2));
  } catch(e){
    out(String(e));
  }
});
