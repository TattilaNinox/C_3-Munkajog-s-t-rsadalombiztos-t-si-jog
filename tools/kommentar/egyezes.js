/* tools/kommentar/egyezes.js – egyezésmérő, 2. fél: a böngészőlapon (Jogkódex-kommentár) futó, függőség nélküli kód.
 * A kommentárkötet azonosítója a beállítás kommentar mezője.
 * Folyamataudit 2026-11-15, B változat (Attila jóváhagyása 20:51). Párja: tools/egyezes_elokeszit.py.
 *
 * MIT CSINÁL: a lapon belüli window.__t térképből (azonosító → a kommentárelem szövege; a tools/kommentar/betolto.js
 * tölti) indexet épít a kommentár MINDEN szó-ötöséről (ritkítás nélkül; az elemhatáron átnyúló ötös az első szava
 * elemé), majd a tétel lenyomatcsomagjának bekezdéseire bekezdésenként csak SZÁMOKAT és #s azonosítót ad vissza.
 * SEMMILYEN kommentárszöveget nem ad vissza, és nem ír sehova.
 *
 * HASZNÁLAT a lapon (javascript_tool):
 *   1. a fájl teljes tartalma egy hívásban (betölti a window.__egy objektumot);
 *   2. window.__egy.hozzaad(<a csomag vagy egy darabja, JSON-szövegként vagy objektumként>) – darabonként, egymás után;
 *   3. window.__egy.eredmeny() → [[azonosító, arány, találatsor, "s<szám>"|null, jel], …]
 *      arány: a bekezdés lenyomatai közül hány található meg a kommentárban (0–1, két tizedes; 0.15 = 15%);
 *      találatsor: a leghosszabb egymást követő találatsor (a bekezdés lenyomatainak sorrendjében), amelynek tagjai
 *        ugyanabban vagy szomszédos (DOM-sorrend szerint ±1) kommentárelemben találhatók;
 *      "s<szám>": a legtöbb találatot adó kommentárelem azonosítója (találat nélkül null);
 *      jel: 1, ha arány >= KUSZOB_ARANY vagy találatsor >= KUSZOB_SOR; különben 0.
 *   Továbbá: window.__egy.kuszob(arany, sor) – a küszöbök átállítása; window.__egy.allapot() – {elem, otos, bekezdes,
 *   lenyomat} (csak számok); window.__egy.torol() – a betöltött csomag törlése; window.__egy.ujraindex() – az index
 *   újraépítése (ha a window.__t időközben bővült).
 *   Az elemek sorrendje: window.__ids (a betolto.js DOM-sorrendű azonosítólistája), ennek hiányában a window.__t kulcsainak
 *   sorrendje. Csak a sorrendben szereplő és a window.__t-ben szöveggel bíró elemek kerülnek az indexbe.
 *
 * NORMALIZÁLÁS ÉS LENYOMAT (betűre azonos az egyezes_elokeszit.py-jal): NFC, kisbetű; szó = betűk és számjegyek
 * (\p{L}, \p{N}) összefüggő sorozata, minden más elválaszt; a számok megmaradnak; szó az első 6 karakterére vágva;
 * ötös = 5 egymást követő szó egy szóközzel; lenyomat = 32 bites FNV-1a az UTF-8 bájtokon; a csomagban base36.
 *
 * KORLÁT: előszűrő, nem ítélet. A szinonimacserés, átrendezett vagy átfogalmazott gondolatmenetet nem (vagy csak
 * részben) jelzi; a jel hiánya nem bizonyítja, hogy nincs átvétel. A jelet kapott bekezdést meg kell nyitni és össze kell
 * vetni a kommentár megjelölt helyével.
 *
 * Node alatt is betölthető (próbához): const egy = require('./egyezes.js'); egy.__tAllit({...}, [...]).
 */
(function (root) {
  'use strict';
  // Küszöbök: 0,10 és 2 (Attila döntése, 2026-11-15, 22:31, a 22–24. tételes próbaköteg után; előtte 0,15 és 3). A mérő csak a közel
  // szó szerinti egyezést jelzi; az átfogalmazott átvételt nem – a jel hiánya nem bizonyíték.
  var KUSZOB_ARANY = 0.10;
  var KUSZOB_SOR = 2;
  var SZOHOSSZ = 6, OTOS = 5;

  var enc = (typeof TextEncoder !== 'undefined') ? new TextEncoder() : null;
  function utf8(s) {
    if (enc) return enc.encode(s);
    var u = unescape(encodeURIComponent(s)), a = new Array(u.length);
    for (var i = 0; i < u.length; i++) a[i] = u.charCodeAt(i);
    return a;
  }
  function fnv1a(s) {
    var b = utf8(s), h = 0x811c9dc5;
    for (var i = 0; i < b.length; i++) { h ^= b[i]; h = Math.imul(h, 0x01000193) >>> 0; }
    return h >>> 0;
  }
  var SZO = /[\p{L}\p{N}]+/gu;
  function szavak(s) {
    var m = String(s).normalize('NFC').toLowerCase().match(SZO) || [];
    return m.map(function (w) { return Array.from(w).slice(0, SZOHOSSZ).join(''); });
  }
  function otosok(s) {
    var w = szavak(s), out = [];
    for (var i = 0; i + OTOS <= w.length; i++) out.push(fnv1a(w.slice(i, i + OTOS).join(' ')));
    return out;
  }

  var T = null, IDS = null;        // Node-próbához felülírható forrás
  var index = null, elemDb = 0, otosDb = 0;
  var bek = [], bekPoz = {};       // [[azonosító, [lenyomat…]]], azonosító → index

  function forras() {
    var t = T || root.__t || {};
    var ids = IDS || root.__ids || Object.keys(t);
    return { t: t, ids: ids };
  }
  function ujraindex() {
    var f = forras(), folyam = [], elemek = [];
    index = new Map(); elemDb = 0; otosDb = 0;
    for (var i = 0; i < f.ids.length; i++) {
      var id = f.ids[i], sz = f.t[id];
      if (typeof sz !== 'string' || !sz.trim()) continue;
      var w = szavak(sz), e = elemek.length;
      elemek.push(id); elemDb++;
      for (var k = 0; k < w.length; k++) folyam.push([w[k], e]);
    }
    for (var j = 0; j + OTOS <= folyam.length; j++) {
      var s = [];
      for (var q = 0; q < OTOS; q++) s.push(folyam[j + q][0]);
      var h = fnv1a(s.join(' ')), e0 = folyam[j][1];
      var l = index.get(h);
      if (!l) { l = []; index.set(h, l); }
      if (l[l.length - 1] !== e0) l.push(e0);
      otosDb++;
    }
    index.__elemek = elemek;
    return { elem: elemDb, otos: otosDb };
  }
  function hozzaad(cs) {
    if (typeof cs === 'string') cs = JSON.parse(cs);
    if (!cs || cs.v !== 1 || !Array.isArray(cs.b)) throw new Error('ismeretlen csomag (v:1 kell)');
    for (var i = 0; i < cs.b.length; i++) {
      var id = cs.b[i][0], l = cs.b[i][1].map(function (x) { return parseInt(x, 36); });
      if (bekPoz.hasOwnProperty(id)) bek[bekPoz[id]][1] = bek[bekPoz[id]][1].concat(l);
      else { bekPoz[id] = bek.length; bek.push([id, l]); }
    }
    return { bekezdes: bek.length, darab: cs.d || 1, db: cs.db || 1 };
  }
  function eredmeny() {
    if (!index) ujraindex();
    var elemek = index.__elemek, out = [];
    for (var i = 0; i < bek.length; i++) {
      var id = bek[i][0], l = bek[i][1], talalt = 0, szaml = {}, legjobb = 0, elozo = null;
      for (var k = 0; k < l.length; k++) {
        var hl = index.get(l[k]);
        if (!hl) { elozo = null; continue; }
        talalt++;
        var most = {};
        for (var a = 0; a < hl.length; a++) {
          var e = hl[a], hossz = 1;
          szaml[e] = (szaml[e] || 0) + 1;
          if (elozo) {
            for (var d = -1; d <= 1; d++) if (elozo[e + d] && elozo[e + d] + 1 > hossz) hossz = elozo[e + d] + 1;
          }
          most[e] = hossz;
          if (hossz > legjobb) legjobb = hossz;
        }
        elozo = most;
      }
      var maxE = null, maxDb = 0;
      for (var key in szaml) if (szaml[key] > maxDb) { maxDb = szaml[key]; maxE = +key; }
      var arany = l.length ? Math.round(100 * talalt / l.length) / 100 : 0;
      var jel = (arany >= KUSZOB_ARANY || legjobb >= KUSZOB_SOR) ? 1 : 0;
      out.push([id, arany, legjobb, maxE === null ? null : elemek[maxE], jel]);
    }
    return out;
  }
  var api = {
    hozzaad: hozzaad,
    eredmeny: eredmeny,
    ujraindex: ujraindex,
    kuszob: function (a, s) { if (a != null) KUSZOB_ARANY = a; if (s != null) KUSZOB_SOR = s; return [KUSZOB_ARANY, KUSZOB_SOR]; },
    allapot: function () {
      if (!index) ujraindex();
      var n = 0; for (var i = 0; i < bek.length; i++) n += bek[i][1].length;
      return { elem: elemDb, otos: otosDb, bekezdes: bek.length, lenyomat: n };
    },
    torol: function () { bek = []; bekPoz = {}; return true; },
    // próbához (Node): a forrás felülírása és a lenyomatfüggvény; szöveget nem ad vissza
    __tAllit: function (t, ids) { T = t; IDS = ids || null; index = null; return true; },
    __otosok: otosok
  };
  if (typeof module !== 'undefined' && module.exports) module.exports = api;
  if (root) root.__egy = api;
})(typeof window !== 'undefined' ? window : (typeof globalThis !== 'undefined' ? globalThis : this));
