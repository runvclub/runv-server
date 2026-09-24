/**
 * Carrega notícias de /news/data/news.json (gerado por site/news/publish_news.py).
 * Cada entrada recebe id="<id>" para bater com os links do feed.rss (/news/#<id>).
 */
(function () {
  async function run() {
    const root = document.getElementById("news-feed");
    const status = document.getElementById("news-status");
    if (!root) return;

    try {
      const r = await fetch("/news/data/news.json", { cache: "no-store" });
      if (!r.ok) throw new Error("HTTP " + r.status);
      const data = await r.json();
      const articles = Array.isArray(data.articles) ? data.articles : [];
      if (articles.length === 0) {
        if (status) status.textContent = "sem entradas";
        return;
      }
      if (status) status.hidden = true;

      const frag = document.createDocumentFragment();
      for (const a of articles) {
        const art = document.createElement("article");
        art.className = "entry prose";
        if (a.id) art.id = a.id;

        const time = document.createElement("time");
        time.className = "date";
        if (a.w3c_published) {
          time.dateTime = a.w3c_published;
          time.textContent = a.w3c_published.slice(0, 10);
        } else {
          time.textContent = a.date || "";
        }

        const h2 = document.createElement("h2");
        const link = document.createElement("a");
        link.href = "#" + (a.id || "");
        link.textContent = (a.title || "").replace(/^#+\s*/, "");
        h2.appendChild(link);

        const body = document.createElement("div");
        // body_html já vem saneado por publish_news.py (ver tests/test_news_rendering.py).
        body.innerHTML = a.body_html || "";

        art.appendChild(time);
        art.appendChild(h2);
        art.appendChild(body);
        frag.appendChild(art);
      }
      root.appendChild(frag);
      if (location.hash) {
        const target = document.getElementById(location.hash.slice(1));
        if (target) target.scrollIntoView();
      }
    } catch (e) {
      if (status) {
        status.textContent = "erro ao carregar /news/data/news.json (" + e.message + "). Use o feed RSS.";
      }
    }
  }

  run();
})();
