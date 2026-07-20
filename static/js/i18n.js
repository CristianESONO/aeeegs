/**
 * AEEEGS — Moteur i18n (Internationalisation)
 * Gère la traduction de l'interface (data-i18n) ET du contenu dynamique (.translatable)
 * via l'API Google Translate non-officielle (gratuite, sans clé)
 */
(function () {
  'use strict';

  const DEFAULT_LANG = 'es';
  const SUPPORTED_LANGS = ['es', 'fr', 'en'];
  const LANG_FLAGS = { es: '🇪🇸', fr: '🇫🇷', en: '🇬🇧' };
  const LANG_NAMES = { es: 'Español', fr: 'Français', en: 'English' };
  const LOADER_TEXT = {
    es: 'Cargando traducción...',
    fr: 'Traduction en cours...',
    en: 'Translating...'
  };

  let currentLang = localStorage.getItem('aeeegs_lang') || DEFAULT_LANG;

  /* ============================================================
   *  TRADUCTION VIA API GOOGLE TRANSLATE (non-officielle)
   * ============================================================ */
  async function translateText(text, targetLang) {
    if (!text || !text.trim() || targetLang === DEFAULT_LANG) return text;

    // Clé de cache basée sur le texte (tronqué pour éviter les clés trop longues)
    const cacheKey = 'i18n_' + targetLang + '_' + simpleHash(text.trim());
    const cached = sessionStorage.getItem(cacheKey);
    if (cached) return cached;

    try {
      const url =
        'https://translate.googleapis.com/translate_a/single' +
        '?client=gtx' +
        '&sl=' + DEFAULT_LANG +
        '&tl=' + targetLang +
        '&dt=t' +
        '&q=' + encodeURIComponent(text.trim());

      const res = await fetch(url);
      if (!res.ok) throw new Error('HTTP ' + res.status);
      const data = await res.json();

      // Reconstitue le texte traduit depuis les chunks
      const translated = data[0].map(function (chunk) { return chunk[0]; }).join('');

      if (translated) {
        sessionStorage.setItem(cacheKey, translated);
        return translated;
      }
    } catch (e) {
      console.warn('[i18n] Translation failed for text:', text.substring(0, 40), e);
    }
    return text; // fallback : texte original
  }

  /* Hash simple pour les clés de cache */
  function simpleHash(str) {
    var hash = 0;
    for (var i = 0; i < Math.min(str.length, 120); i++) {
      hash = ((hash << 5) - hash) + str.charCodeAt(i);
      hash |= 0;
    }
    return Math.abs(hash).toString(36);
  }

  /* ============================================================
   *  TRADUCTIONS STATIQUES (dictionnaire)
   * ============================================================ */
  function applyStaticTranslations(lang) {
    if (typeof TRANSLATIONS === 'undefined') return;
    const dict = TRANSLATIONS[lang] || TRANSLATIONS[DEFAULT_LANG];

    // Textes (innerText)
    document.querySelectorAll('[data-i18n]').forEach(function (el) {
      const key = el.getAttribute('data-i18n');
      if (dict[key] !== undefined) el.textContent = dict[key];
    });

    // Placeholders d'inputs
    document.querySelectorAll('[data-i18n-placeholder]').forEach(function (el) {
      const key = el.getAttribute('data-i18n-placeholder');
      if (dict[key] !== undefined) el.placeholder = dict[key];
    });

    // Options de sélect contenant "Actual" / "Histórico"
    if (dict['directiva.current'] && dict['directiva.historical']) {
      document.querySelectorAll('select option').forEach(function (opt) {
        opt.textContent = opt.textContent
          .replace('Actual', dict['directiva.current'])
          .replace('Histórico', dict['directiva.historical'])
          // Reset to Spanish labels before re-applying (important for language switching)
          .replace('Actuel', dict['directiva.current'])
          .replace('Historique', dict['directiva.historical'])
          .replace('Current', dict['directiva.current'])
          .replace('Historical', dict['directiva.historical']);
      });
    }

    // Mise à jour de l'attribut lang du document
    document.documentElement.lang = lang;
  }

  /* ============================================================
   *  TRADUCTION DU CONTENU DYNAMIQUE (.translatable)
   * ============================================================ */
  async function translateDynamicContent(lang) {
    const elements = Array.from(document.querySelectorAll('.translatable'));
    if (elements.length === 0) return;

    if (lang === DEFAULT_LANG) {
      // Restaurer les textes originaux
      elements.forEach(function (el) {
        const orig = el.getAttribute('data-orig');
        if (orig !== null) el.textContent = orig;
      });
      return;
    }

    showLoader(lang);
    let done = 0;

    // Traitement par lots de 4 pour ne pas surcharger l'API
    for (let i = 0; i < elements.length; i += 4) {
      const batch = elements.slice(i, i + 4);

      await Promise.all(batch.map(async function (el) {
        // Sauvegarder le texte original (une seule fois)
        if (!el.hasAttribute('data-orig')) {
          el.setAttribute('data-orig', el.textContent.trim());
        }

        const origText = el.getAttribute('data-orig');
        if (!origText || !origText.trim()) return;

        const translated = await translateText(origText, lang);
        if (translated && translated !== origText) {
          el.textContent = translated;
        }
      }));

      done += batch.length;
      updateProgress(done, elements.length);
    }

    hideLoader();
  }

  /* ============================================================
   *  LOADER / INDICATEUR DE CHARGEMENT
   * ============================================================ */
  function showLoader(lang) {
    let loader = document.getElementById('i18n-loader');
    if (!loader) {
      loader = document.createElement('div');
      loader.id = 'i18n-loader';
      loader.style.cssText = [
        'position:fixed', 'inset:0', 'z-index:99999',
        'display:flex', 'flex-direction:column',
        'align-items:center', 'justify-content:center',
        'background:rgba(255,255,255,0.88)',
        'backdrop-filter:blur(8px)',
        '-webkit-backdrop-filter:blur(8px)'
      ].join(';');

      loader.innerHTML =
        '<div style="text-align:center;padding:32px;border-radius:20px;background:white;box-shadow:0 20px 60px rgba(0,0,0,0.12);min-width:240px;">' +
        '  <div class="spinner-border text-primary mb-3" role="status" style="width:2.8rem;height:2.8rem;"></div>' +
        '  <div class="fw-bold text-primary fs-6 mb-2" id="i18n-loader-msg">' + (LOADER_TEXT[lang] || 'Translating...') + '</div>' +
        '  <div class="progress" style="height:6px;border-radius:4px;background:#eee;">' +
        '    <div id="i18n-progress-bar" class="progress-bar bg-primary" role="progressbar" style="width:0%;transition:width 0.3s;border-radius:4px;"></div>' +
        '  </div>' +
        '  <div class="text-muted small mt-2" id="i18n-progress-pct">0%</div>' +
        '</div>';

      document.body.appendChild(loader);
    } else {
      loader.style.display = 'flex';
      const msg = loader.querySelector('#i18n-loader-msg');
      if (msg) msg.textContent = LOADER_TEXT[lang] || 'Translating...';
    }
  }

  function hideLoader() {
    const loader = document.getElementById('i18n-loader');
    if (loader) loader.style.display = 'none';
  }

  function updateProgress(done, total) {
    const pct = Math.round((done / total) * 100);
    const bar = document.getElementById('i18n-progress-bar');
    const label = document.getElementById('i18n-progress-pct');
    if (bar) bar.style.width = pct + '%';
    if (label) label.textContent = pct + '%';
  }

  /* ============================================================
   *  SÉLECTEUR DE LANGUE — mise à jour UI
   * ============================================================ */
  function updateSelector(lang) {
    const flagEl = document.getElementById('current-lang-flag');
    const labelEl = document.getElementById('current-lang-label');
    if (flagEl) flagEl.textContent = LANG_FLAGS[lang] || '🌐';
    if (labelEl) labelEl.textContent = lang.toUpperCase();

    document.querySelectorAll('.lang-option').forEach(function (el) {
      const isActive = el.getAttribute('data-lang') === lang;
      el.classList.toggle('active', isActive);
      const check = el.querySelector('.lang-check');
      if (check) check.classList.toggle('d-none', !isActive);
    });
  }

  /* ============================================================
   *  FONCTION PRINCIPALE : changer de langue
   * ============================================================ */
  async function setLanguage(lang) {
    if (!SUPPORTED_LANGS.includes(lang)) return;

    currentLang = lang;
    localStorage.setItem('aeeegs_lang', lang);

    // 1. Traductions statiques (instantané)
    applyStaticTranslations(lang);
    updateSelector(lang);

    // 2. Contenu dynamique (API)
    await translateDynamicContent(lang);
  }

  /* ============================================================
   *  INITIALISATION
   * ============================================================ */
  function init() {
    // Appliquer la langue au chargement
    applyStaticTranslations(currentLang);
    updateSelector(currentLang);

    // Attacher les listeners sur les boutons de langue
    document.querySelectorAll('.lang-option').forEach(function (el) {
      el.addEventListener('click', function (e) {
        e.preventDefault();
        var lang = this.getAttribute('data-lang');
        setLanguage(lang);
      });
    });

    // Si la langue sauvegardée n'est pas l'espagnol, traduire le contenu dynamique
    if (currentLang !== DEFAULT_LANG) {
      var translatables = document.querySelectorAll('.translatable');
      if (translatables.length > 0) {
        translateDynamicContent(currentLang);
      }
    }
  }

  // Lancer au bon moment
  if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', init);
  } else {
    init();
  }

  // Exposer globalement pour usage éventuel
  window.AEEEGSi18n = { setLanguage: setLanguage };

})();
