async function getSettings() {
  return await chrome.storage.local.get(["baseUrl","apiKey","autoExport"]);
}

async function postPayload(baseUrl, apiKey, payload){
  const url = baseUrl.replace(/\/$/,"") + "/api/ingest/chat";
  const headers = { "Content-Type": "application/json" };
  if (apiKey) headers["X-API-Key"] = apiKey;
  const r = await fetch(url, { method: "POST", headers, body: JSON.stringify(payload) });
  return await r.json();
}

chrome.runtime.onMessage.addListener((msg, sender, sendResponse) => {
  (async () => {
    if (msg?.action === "EXPORT_PAYLOAD") {
      const { baseUrl, apiKey } = await getSettings();
      if (!baseUrl) return sendResponse({ ok:false, error:"Backend URL not set" });
      try{
        const j = await postPayload(baseUrl, apiKey, msg.payload);
        return sendResponse({ ok:true, result:j });
      } catch(e){
        return sendResponse({ ok:false, error:String(e) });
      }
    }

    if (msg?.action === "BATCH_EXPORT_URLS") {
      const { baseUrl, apiKey } = await getSettings();
      if (!baseUrl) return sendResponse({ ok:false, error:"Backend URL not set" });

      const urls = (msg.urls || []).slice(0, 50);
      let done = 0, failed = 0;
      for (const u of urls){
        try{
          const tab = await chrome.tabs.create({ url: u, active: false });
          await new Promise(res => setTimeout(res, 6500));
          const resp = await chrome.tabs.sendMessage(tab.id, { action: "SCRAPE_CHAT" });
          if (resp?.ok){
            await postPayload(baseUrl, apiKey, resp.payload);
            done++;
          } else {
            failed++;
          }
          try { await chrome.tabs.remove(tab.id); } catch(_e) {}
          await new Promise(res => setTimeout(res, 1200));
        } catch(e){
          failed++;
        }
      }
      return sendResponse({ ok:true, done, failed, total: urls.length });
    }
  })();
  return true;
});
