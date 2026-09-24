// Botão "abrir uma página qualquer": sorteia um morador de /data/members.json.
// Sem JS o botão fica escondido; a lista ls -lt continua com todos os links.
(function () {
  var btn = document.getElementById("aleatorio");
  if (!btn || !window.fetch) return;
  fetch("/data/members.json", { cache: "no-store" })
    .then(function (r) { return r.ok ? r.json() : []; })
    .then(function (list) {
      var paths = (Array.isArray(list) ? list : [])
        .map(function (m) { return m && m.path; })
        .filter(function (p) { return typeof p === "string" && /^\/~[a-z][a-z0-9_-]{1,31}\/$/.test(p); });
      if (!paths.length) return;
      btn.hidden = false;
      btn.addEventListener("click", function () {
        location.href = paths[Math.floor(Math.random() * paths.length)];
      });
    })
    .catch(function () {});
})();
