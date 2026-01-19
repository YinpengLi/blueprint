\
function safeText(el){ return (el?.innerText || "").replace(/\r\n/g,"\n").trim(); }
function guessTitle(){
  const t = document.title || "chatgpt-chat";
  return t.replace(/\s*-\s*ChatGPT\s*$/i,"").trim() || "chatgpt-chat";
}
function collectMessages(){
  const out = [];
  const articles = document.querySelectorAll("article");
  for (const a of articles){
    const text = safeText(a);
    if (!text) continue;
    let role = "unknown";
    const r = a.querySelector("[data-message-author-role]")?.getAttribute("data-message-author-role");
    if (r) role = r;
    out.push({ role, text, md: text });
  }
  const dedup = [];
  for (const m of out){
    const prev = dedup[dedup.length-1];
    if (!prev || prev.text !== m.text) dedup.push(m);
  }
  return dedup;
}
function collectFileHints(){
  const hints = [];
  document.querySelectorAll("a,button,span").forEach(el=>{
    const t = (el.textContent || "").trim();
    if (/\.(pdf|docx|xlsx|pptx|csv|png|jpg|jpeg|zip)$/i.test(t)) hints.push({name:t,type:""});
  });
  const seen = new Set();
  return hints.filter(h => (seen.has(h.name) ? false : (seen.add(h.name), true)));
}
function buildPayload(){
  return {
    title: guessTitle(),
    source_url: location.href,
    captured_at: new Date().toISOString(),
    messages: collectMessages(),
    ui_files: collectFileHints()
  };
}

function getRecentChatUrls(limit=50){
  const urls = [];
  const anchors = document.querySelectorAll('a[href*="/c/"]');
  for (const a of anchors){
    const href = a.getAttribute("href");
    if (!href) continue;
    const u = href.startsWith("http") ? href : (location.origin + href);
    if (!urls.includes(u)) urls.push(u);
    if (urls.length >= limit) break;
  }
  return urls;
}

let lastSig = "";
let timer = null;

async function autoExportIfEnabled(){
  const { baseUrl, apiKey, autoExport } = await chrome.storage.local.get(["baseUrl","apiKey","autoExport"]);
  if (!autoExport || !baseUrl) return;
  if (!location.pathname.includes("/c/")) return;

  const payload = buildPayload();
  const lastText = (payload.messages && payload.messages.length) ? payload.messages[payload.messages.length-1].text : "";
  const sig = (payload.title || "") + "|" + (payload.messages?.length || 0) + "|" + (lastText || "").slice(0,80);
  if (sig === lastSig) return;
  lastSig = sig;

  chrome.runtime.sendMessage({ action:"EXPORT_PAYLOAD", payload }, () => {});
}

function scheduleAutoExport(){
  if (timer) clearTimeout(timer);
  timer = setTimeout(autoExportIfEnabled, 2500);
}

const observer = new MutationObserver(() => scheduleAutoExport());
observer.observe(document.documentElement, { childList: true, subtree: true });

setTimeout(() => scheduleAutoExport(), 4000);

chrome.runtime.onMessage.addListener((msg,_sender,sendResponse)=>{
  if (msg?.action === "SCRAPE_CHAT") {
    sendResponse({ ok:true, payload: buildPayload() });
    return true;
  }
  if (msg?.action === "GET_RECENT_CHAT_URLS") {
    const limit = msg.limit || 50;
    sendResponse({ ok:true, urls: getRecentChatUrls(limit) });
    return true;
  }
});
