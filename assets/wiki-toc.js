document.addEventListener("DOMContentLoaded", function () {
  var main = document.querySelector("main#content");
  if (!main) return;

  var headings = Array.from(main.querySelectorAll("h2, h3"));
  if (headings.length < 2) return;

  var idCounts = {};
  function slugify(text) {
    var base = text.toLowerCase().trim()
      .replace(/[\u2019\u2018\u201C\u201D]/g, "")
      .replace(/[^a-z0-9\s-]/g, "")
      .replace(/\s+/g, "-")
      .replace(/-+/g, "-");
    var count = (idCounts[base] || 0) + 1;
    idCounts[base] = count;
    return count > 1 ? base + "-" + count : base;
  }

  headings.forEach(function (h) {
    if (!h.id || h.id.trim() === "") {
      var text = h.textContent || h.innerText || "section";
      h.id = slugify(text);
    }
  });

  var tocRoot = document.getElementById("toc-root");
  if (!tocRoot) {
    tocRoot = document.createElement("div");
    tocRoot.id = "toc-root";
    var mainContainer = document.querySelector(".site-main") || document.body;
    mainContainer.insertBefore(tocRoot, mainContainer.firstChild);
  }

  var nav = document.createElement("nav");
  nav.className = "toc";

  var title = document.createElement("h2");
  title.textContent = "Contents";
  nav.appendChild(title);

  var ul = document.createElement("ul");
  nav.appendChild(ul);

  headings.forEach(function (h) {
    var level = h.tagName.toLowerCase() === "h3" ? 3 : 2;
    var li = document.createElement("li");
    if (level === 3) li.className = "lvl-2";
    var a = document.createElement("a");
    a.href = "#" + h.id;
    a.textContent = h.textContent || h.innerText || "";
    li.appendChild(a);
    ul.appendChild(li);
  });

  tocRoot.innerHTML = "";
  tocRoot.appendChild(nav);
});
