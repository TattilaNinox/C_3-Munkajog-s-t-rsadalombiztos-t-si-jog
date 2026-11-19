/* tools/kommentar/betolto.js – a Jogkódex-kommentár (dok. 6512777; a kötet azonosítója a beállítás kommentar mezője) tartományának betöltése és olvasása a beépített böngészőben.
 * Folyamataudit 2026-11-15, B változat (Attila jóváhagyása 20:51): a KP-2 szabályzat 5. pontjában és a
 * kontroll/_kommentar_terkep.json „technika” részében prózában leírt eljárás rögzített kódja, hogy a tétel- és az
 * audit-alügynök ne írja meg minden tételnél újra.
 *
 * ÉLŐ OLDALON KIPRÓBÁLVA: 2026-11-15, a beépített böngészőben, háttérlapon, 1280×900-as nézettel, a #s14299-től induló
 * 40 elemes tartományon: tartomany → indit → allapot (15 mp alatt done, 0 hiányzó) → teljes (40/40 nem üres) → olvas
 * (szeletelve és {rovidit: true}-val) → toc. Nagy (több száz elemes) tartományon és a csak a szakasz közepére görgetve
 * betöltődő szakaszon élőben még nem futott. Ha nem működik (hiba, üres szöveg, a betöltés nem halad), a KP-2 szabályzat
 * 5. pontjának prózai technikája az irányadó; az alügynök a hibát (függvény, hívás, eredmény) a jelentésében leírja.
 *
 * HASZNÁLAT (minden lépés egy javascript_tool hívás a SAJÁT tabId-vel; előtte navigate + resize_window 1280×900):
 *   1. a fájl teljes tartalma (betölti a window.__kb objektumot; a már mentett window.__t-t nem törli);
 *   2. window.__kb.tartomany([["s14299","s14445"], ["s14330","s14334"]])
 *        – tartomány(ok) DOM-sorrend szerinti indexszelettel: [fej-azonosító, a következő fej azonosítója (ez már NEM
 *          része)]; a második elem helyett szám is adható (darabszám); a közbeszúrt s26xxx–s28xxx elemek a szelet részei.
 *        Visszaad: {elem, tartomanyok:[{tol, igElott, tolIndex, igIndex, elem}]}. A lista: window.__ids.
 *   3. window.__kb.indit()  – háttérben induló betöltő (await nélkül; a hívás azonnal visszatér). Opciók (mind elhagyható):
 *        {lepes: 2, varakozas: 450, maxVar: 8, elotte: 8, utana: 14, menet: 3, szakaszVar: 5000}
 *   4. window.__kb.allapot() – {done, pos, elem, kesz, hianyzo, menet, mp}; a done (window.__done) és a pos (window.__pos)
 *        jelzi a haladást. Időtúllépés nincs: néhány másodpercenként kérdezd.
 *   5. window.__kb.olvas(kezdoIndex, keret) – karakterkeret szerinti olvasás (keret alapérték 20000, legfeljebb 26000):
 *        a válasz első sora „KÖVETKEZŐ: <index> / <elemszám>” (ha kész: „KÖVETKEZŐ: VÉGE / …”), utána elemenként
 *        „[s123] szöveg”. Az első még nem betöltött elemnél megáll és jelzi („HIÁNYZIK: s… – várd meg a betöltőt”).
 *        Opció: window.__kb.olvas(k, keret, {rovidit: true}) – a szó szerinti normaszöveg-elemek (P.rt osztály, „(n)” vagy
 *        „a)” kezdetű szöveg) helyén csak az eleje és a hossza áll (a szabályzat szerint ezt nem kell kiolvasni); a nem
 *        „(n)”/„a)” kezdetű rt-elemet teljes hosszban adja (magyarázó szöveg is lehet rt osztályú).
 *   6. window.__kb.teljes() – teljességellenőrzés: {elem, nemUres, ures: [legfeljebb 50 azonosító], karakter, normaKarakter}.
 *        A tartomány akkor van kiolvasva, ha ures üres, és minden olvas()-szelet megjött.
 *   A tartalomjegyzék (címek, alcímek; betöltés nélkül): window.__kb.toc(szűrő) → [[#s azonosító, cím]] (a „[123]”
 *   alakú lábjegyzet-hivatkozások nélkül).
 * TILOS: alert, confirm, prompt; mentés, letöltés, képernyőkép. A kommentár szövege a lapon marad (window.__t), fájlba nem
 * kerül; a válaszokat csak elolvasásra használod. Az egyezésmérő (tools/kommentar/egyezes.js) ugyanezt a window.__t-t és
 * window.__ids-t használja.
 */
(function () {
  'use strict';
  var W = window;
  W.__t = W.__t || {};
  W.__c = W.__c || {};
  var ALL = null;

  function osszesId() {
    // az összes #s<szám> azonosító DOM-sorrendben (betöltés nélkül is olvasható)
    var a = document.querySelectorAll('[id^="s"]'), out = [];
    for (var i = 0; i < a.length; i++) if (/^s\d+$/.test(a[i].id)) out.push(a[i].id);
    ALL = out;
    return out;
  }
  function el(id) { return document.getElementById(id); }
  function szoveg(id) {
    var e = el(id);
    return e ? (e.textContent || '').replace(/\s+/g, ' ').trim() : '';
  }
  function alszik(ms) { return new Promise(function (r) { setTimeout(r, ms); }); }

  function tartomany(lista) {
    var all = osszesId(), pos = {}, ids = [], info = [];
    for (var i = 0; i < all.length; i++) pos[all[i]] = i;
    for (var k = 0; k < lista.length; k++) {
      var tol = lista[k][0], ig = lista[k][1];
      if (!(tol in pos)) throw new Error('nincs ilyen azonosító a lapon: ' + tol);
      var a = pos[tol], b;
      if (typeof ig === 'number') b = a + ig;
      else { if (!(ig in pos)) throw new Error('nincs ilyen azonosító a lapon: ' + ig); b = pos[ig]; }
      if (b <= a) throw new Error('üres tartomány: ' + tol + '–' + ig);
      var szelet = all.slice(a, b);
      for (var j = 0; j < szelet.length; j++) if (ids.indexOf(szelet[j]) < 0) ids.push(szelet[j]);
      info.push({ tol: tol, igElott: typeof ig === 'number' ? all[b] || null : ig, tolIndex: a, igIndex: b, elem: szelet.length });
    }
    W.__ids = ids;
    W.__done = false; W.__pos = 0;
    return { elem: ids.length, osszesAzonosito: all.length, tartomanyok: info };
  }

  function ment(i0, elotte, utana, halmaz) {
    var ids = W.__ids, db = 0;
    for (var i = Math.max(0, i0 - elotte); i <= Math.min(ids.length - 1, i0 + utana); i++) {
      var id = ids[i];
      if (W.__t[id]) continue;
      var e = el(id);
      if (!e) continue;
      var s = (e.textContent || '').replace(/\s+/g, ' ').trim();
      if (s) { W.__t[id] = s; W.__c[id] = e.className || ''; db++; }
    }
    return db;
  }

  function szakaszKozepre(id) {
    var e = el(id);
    var sz = e && e.closest ? e.closest('section[data-page]') : null;
    if (!sz) { if (e) e.scrollIntoView({ block: 'center' }); return false; }
    var r = sz.getBoundingClientRect();
    W.scrollTo(0, W.scrollY + r.top + sz.offsetHeight / 2 - 450);
    return true;
  }

  var start = 0, menetSzam = 0, fut = false;
  async function betolt(o) {
    var ids = W.__ids;
    for (var m = 1; m <= o.menet; m++) {
      menetSzam = m;
      var hiany = 0;
      for (var i = 0; i < ids.length; i += o.lepes) {
        W.__pos = i;
        var id = ids[i];
        if (W.__t[id] && (i + o.lepes - 1 >= ids.length || W.__t[ids[Math.min(ids.length - 1, i + o.lepes - 1)]])) continue;
        var e = el(id);
        if (e) e.scrollIntoView({ block: 'center' });
        var v = 0;
        while (v < o.maxVar && !szoveg(id)) { await alszik(o.varakozas); v++; }
        if (!szoveg(id)) {
          // a szakasz nem töltött be lépésenként: a szakasz (section[data-page]) közepére görgetés, várakozás
          szakaszKozepre(id);
          await alszik(o.szakaszVar);
        }
        ment(i, o.elotte, o.utana);
        if (!W.__t[id]) hiany++;
      }
      // hiányzók külön, egyenként
      for (var j = 0; j < ids.length; j++) {
        if (W.__t[ids[j]]) continue;
        var e2 = el(ids[j]);
        if (e2) e2.scrollIntoView({ block: 'center' });
        var v2 = 0;
        while (v2 < o.maxVar && !szoveg(ids[j])) { await alszik(o.varakozas); v2++; }
        if (!szoveg(ids[j])) { szakaszKozepre(ids[j]); await alszik(o.szakaszVar); }
        ment(j, o.elotte, o.utana);
      }
      if (ids.every(function (x) { return W.__t[x]; })) break;
    }
    W.__pos = ids.length;
    W.__done = true;
    fut = false;
  }

  function indit(opt) {
    if (!W.__ids || !W.__ids.length) throw new Error('előbb: window.__kb.tartomany([...])');
    if (fut) return 'már fut';
    var o = { lepes: 2, varakozas: 450, maxVar: 8, elotte: 8, utana: 14, menet: 3, szakaszVar: 5000 };
    for (var k in (opt || {})) o[k] = opt[k];
    W.__done = false; W.__pos = 0; start = Date.now(); fut = true;
    betolt(o).catch(function (err) { W.__hiba = String(err); W.__done = true; fut = false; });
    return 'elindult: ' + W.__ids.length + ' elem';
  }

  function allapot() {
    var ids = W.__ids || [], kesz = 0;
    for (var i = 0; i < ids.length; i++) if (W.__t[ids[i]]) kesz++;
    return { done: !!W.__done, pos: W.__pos || 0, elem: ids.length, kesz: kesz, hianyzo: ids.length - kesz, menet: menetSzam,
             mp: start ? Math.round((Date.now() - start) / 1000) : 0, hiba: W.__hiba || null };
  }

  function normaElem(id, s) {
    return /(^|\s)rt(\s|$)/.test(W.__c[id] || '') && /^(\(\d+[a-z]?\)|[a-z]{1,2}\))\s/.test(s);
  }

  function olvas(k, keret, opt) {
    var ids = W.__ids || [];
    keret = Math.min(keret || 20000, 26000);
    k = k || 0;
    var rov = opt && opt.rovidit, out = [], n = 0, i = k;
    for (; i < ids.length; i++) {
      var s = W.__t[ids[i]];
      if (!s) { out.push('HIÁNYZIK: ' + ids[i] + ' – várd meg a betöltőt (allapot), majd olvass innen'); break; }
      var sor = '[' + ids[i] + '] ' + (rov && normaElem(ids[i], s) ? s.slice(0, 60) + ' … [normaszöveg, ' + s.length + ' karakter]' : s);
      if (n + sor.length + 1 > keret && out.length) break;
      out.push(sor); n += sor.length + 1;
    }
    return 'KÖVETKEZŐ: ' + (i >= ids.length ? 'VÉGE' : i) + ' / ' + ids.length + '\n' + out.join('\n');
  }

  function teljes() {
    var ids = W.__ids || [], ures = [], kar = 0, norma = 0;
    for (var i = 0; i < ids.length; i++) {
      var s = W.__t[ids[i]];
      if (!s) { ures.push(ids[i]); continue; }
      kar += s.length;
      if (normaElem(ids[i], s)) norma += s.length;
    }
    return { elem: ids.length, nemUres: ids.length - ures.length, ures: ures.slice(0, 50), uresDb: ures.length, karakter: kar, normaKarakter: norma };
  }

  function toc(szuro) {
    var a = document.querySelectorAll('a[href*="#s"]'), out = [];
    for (var i = 0; i < a.length; i++) {
      var t = (a[i].textContent || '').replace(/\s+/g, ' ').trim();
      if (/^\[\d+\]$/.test(t)) continue;     // lábjegyzet-hivatkozás
      var m = (a[i].getAttribute('href') || '').match(/#(s\d+)/);
      if (!m) continue;
      if (szuro && t.toLowerCase().indexOf(String(szuro).toLowerCase()) < 0) continue;
      out.push([m[1], t.slice(0, 120)]);
    }
    return out;
  }

  W.__kb = { osszesId: osszesId, tartomany: tartomany, indit: indit, allapot: allapot, olvas: olvas, teljes: teljes, toc: toc };
  return 'window.__kb betöltve (hiba esetén a szabályzat 5. pontjának prózai technikája az irányadó)';
})();
