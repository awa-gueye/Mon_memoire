/* ============================================================================
   countup.js — anime les statistiques de l'accueil (.sn-stat-val) en comptant
   de 0 jusqu'a la valeur finale. Charge automatiquement par Dash (dossier assets).
   - gere le separateur de milliers  : "60 000"
   - gere un suffixe                  : "40 ans"
   - laisse les plages statiques      : "2027-2066"
   - se declenche a l'entree a l'ecran (IntersectionObserver)
   - se re-anime quand Dash re-rend la page d'accueil
   - respecte prefers-reduced-motion
   ========================================================================== */
(function () {
  var REDUCE = window.matchMedia &&
               window.matchMedia('(prefers-reduced-motion: reduce)').matches;
  var DUREE = 1500;                 // duree de l'animation (ms)

  function parse(txt) {
    txt = txt.trim();
    if (/\d\s*[-\u2013]\s*\d/.test(txt)) return null;      // "2027-2066" -> statique
    var m = txt.match(/\d[\d\s\u202f]*\d|\d/);
    if (!m) return null;
    var num = m[0];
    var val = parseInt(num.replace(/[\s\u202f]/g, ''), 10);
    if (isNaN(val)) return null;
    return {
      value:  val,
      sep:    /[\s\u202f]/.test(num.trim()),               // milliers presents ?
      suffix: txt.slice(m.index + num.length)              // ex : " ans"
    };
  }

  function fmt(n, sep, suffix) {
    var s = Math.round(n).toString();
    if (sep) s = s.replace(/\B(?=(\d{3})+(?!\d))/g, ' ');  // espace tous les 3 chiffres
    return s + suffix;
  }

  function animate(el) {
    if (el.dataset.counted) return;
    var info = parse(el.textContent);
    el.dataset.counted = '1';
    if (!info) return;                                     // valeur non numerique : on laisse
    if (REDUCE) { el.textContent = fmt(info.value, info.sep, info.suffix); return; }

    var start = null;
    function step(ts) {
      if (!start) start = ts;
      var p = Math.min((ts - start) / DUREE, 1);
      var eased = 1 - Math.pow(1 - p, 3);                  // easeOutCubic (rapide puis ralentit)
      el.textContent = fmt(info.value * eased, info.sep, info.suffix);
      if (p < 1) requestAnimationFrame(step);
      else el.textContent = fmt(info.value, info.sep, info.suffix);
    }
    requestAnimationFrame(step);
  }

  var io = ('IntersectionObserver' in window)
    ? new IntersectionObserver(function (entries) {
        entries.forEach(function (e) {
          if (e.isIntersecting) { animate(e.target); io.unobserve(e.target); }
        });
      }, { threshold: 0.35 })
    : null;

  function scan() {
    document.querySelectorAll('.sn-stat-val:not([data-counted])').forEach(function (el) {
      if (io) io.observe(el); else animate(el);
    });
  }

  // scan initial + a chaque re-rendu de page par Dash (avec petit debounce)
  var t;
  function schedule() { clearTimeout(t); t = setTimeout(scan, 60); }
  if (document.readyState !== 'loading') scan();
  document.addEventListener('DOMContentLoaded', scan);
  new MutationObserver(schedule).observe(document.documentElement,
                                         { childList: true, subtree: true });
})();
