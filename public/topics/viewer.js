(async function(){
  const qs = new URLSearchParams(location.search);
  const wanted = qs.get("slug");
  const listEl = document.getElementById("list");
  const articleEl = document.getElementById("article");

  const idxResp = await fetch("./topics.json", {cache:"no-store"});
  const topics = await idxResp.json();

  // render list
  listEl.innerHTML = "";
  topics.forEach(t=>{
    const a = document.createElement("a");
    a.href = `?slug=${encodeURIComponent(t.slug)}`;
    a.textContent = t.title;
    const div = document.createElement("div");
    div.className="item";
    div.appendChild(a);
    listEl.appendChild(div);
  });

  if (!wanted) return;

  const hit = topics.find(t=>t.slug===wanted);
  if (!hit){
    articleEl.innerHTML = `<strong>Not found:</strong> ${wanted}`;
    return;
  }

  const md = await (await fetch(`/${hit.path}`)).text();
  const cleaned = md.replace(/^---[\s\S]*?---\s*/, ""); // strip front matter
  articleEl.innerHTML = marked.parse(cleaned);

  // simple heading ids
  document.querySelectorAll("h2,h3,h4").forEach(h=>{
    if(!h.id){
      h.id = h.textContent.trim().toLowerCase()
        .replace(/[^a-z0-9]+/g,"-").replace(/(^-|-$)/g,"");
    }
  });
})();
