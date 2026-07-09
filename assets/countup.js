/* ============================================================================
   countup.js — compteurs animes (comptent de 0 -> valeur finale).
   Charge automatiquement par Dash (dossier assets). Aucune autre modif requise.

   Cibles :
     .sn-stat-val  (bandeau accueil)  -> valeur lue dans le texte
                      "60 000" (milliers), "40 ans" (suffixe), "2027-2066" (ignore)
     .kpi-val      (tableau de bord)  -> cible lue dans les attributs data-*
                      data-count-to / data-decimals / data-sep / data-suffix

   - declenchement a l'entree a l'ecran (IntersectionObserver)
   - re-animation quand Dash re-rend une page
   - respecte prefers-reduced-motion
   ========================================================================== */
(function () {
  var REDUCE = window.matchMedia &&
               window.matchMedia('(prefers-reduced-motion: reduce)').matches;
  var DUREE = 1500;                                  // duree de l'animation (ms)

  function fmt(n, decimals, sep, suffix) {
    var s = Number(n).toFixed(decimals);
    if (sep) {
      var parts = s.split('.');
      parts[0] = parts[0].replace(/\B(?=(\d{3})+(?!\d))/g, sep);
      s = parts.join('.');
    }
    return s + suffix;
  }

  // Anime l'element de 0 a target, en formatant chaque frame via formatter(v)
  function run(el, target, formatter) {
    if (REDUCE) { el.textContent = formatter(target); return; }
    var start = null;
    function step(ts) {
      if (!start) start = ts;
      var p = Math.min((ts - start) / DUREE, 1);
      var eased = 1 - Math.pow(1 - p, 3);            // easeOutCubic
      el.textContent = formatter(target * eased);
      if (p < 1) requestAnimationFrame(step);
      else el.textContent = formatter(target);
    }
    requestAnimationFrame(step);
  }

  // Cas 1 : cible fournie en data-* (KPI du tableau de bord)
  function fromData(el) {
    var target = parseFloat(el.getAttribute('data-count-to'));
    if (isNaN(target)) return false;
    var dec = parseInt(el.getAttribute('data-decimals') || '0', 10);
    var sep = el.getAttribute('data-sep') || '';
    var suf = el.getAttribute('data-suffix') || '';
    run(el, target, function (v) { return fmt(v, dec, sep, suf); });
    return true;
  }

  // Cas 2 : valeur lue dans le texte (bandeau accueil)
  function fromText(el) {
    var txt = el.textContent.trim();
    if (/\d\s*[-\u2013]\s*\d/.test(txt)) return;               // "2027-2066" -> statique
    var m = txt.match(/\d[\d\s\u202f]*\d|\d/);
    if (!m) return;
    var num = m[0];
    var val = parseInt(num.replace(/[\s\u202f]/g, ''), 10);
    if (isNaN(val)) return;
    var sep = /[\s\u202f]/.test(num.trim()) ? ' ' : '';        // milliers ?
    var suf = txt.slice(m.index + num.length);                 // ex : " ans"
    run(el, val, function (v) { return fmt(v, 0, sep, suf); });
  }

  function animate(el) {
    if (el.dataset.counted) return;
    el.dataset.counted = '1';
    if (el.hasAttribute('data-count-to')) { fromData(el); }
    else { fromText(el); }
  }

  var io = ('IntersectionObserver' in window)
    ? new IntersectionObserver(function (entries) {
        entries.forEach(function (e) {
          if (e.isIntersecting) { animate(e.target); io.unobserve(e.target); }
        });
      }, { threshold: 0.35 })
    : null;

  function scan() {
    document.querySelectorAll('.sn-stat-val:not([data-counted]), .kpi-val:not([data-counted])')
      .forEach(function (el) { if (io) io.observe(el); else animate(el); });
  }

  var t;
  function schedule() { clearTimeout(t); t = setTimeout(scan, 60); }
  if (document.readyState !== 'loading') scan();
  document.addEventListener('DOMContentLoaded', scan);
  new MutationObserver(schedule).observe(document.documentElement,
                                         { childList: true, subtree: true });
})();
