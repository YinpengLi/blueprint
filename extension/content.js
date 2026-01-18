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
  // dedup
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
chrome.runtime.onMessage.addListener((msg,_sender,sendResponse)=>{
  if (msg?.action !== "SCRAPE_CHAT") return;
  const payload = {
    title: guessTitle(),
    source_url: location.href,
    captured_at: new Date().toISOString(),
    messages: collectMessages(),
    ui_files: collectFileHints()
  };
  sendResponse({ ok:true, payload });
  return true;
});
