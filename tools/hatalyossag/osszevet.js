/* S2 – a korpusz összevetése a hatályos egységes szöveggel (a tools/hatalyossag.py párja).
 *
 * Hol fut: a net.jogtar.hu bármely megnyitott oldalán, a böngésző JavaScript-konzoljában (vagy a Claude böngészőeszközével).
 * A korpusz TXT-fájljai ugyanebből a forrásból készültek, ezért a bekezdésszerkezet egyezik.
 * Mit ad vissza: csak szakaszszámokat (eltérő, csak az oldalon, csak a korpuszban). Szöveg nem hagyja el az oldalt,
 * letöltés és mentés nincs; jogszabályonként egy lekérés.
 *
 * Használat:
 *   1. python3 tools/hatalyossag.py ujjlenyomat Pp.txt            -> az ujjlenyomat-sor (és a 0. szakasz adatai)
 *   2. a konzolban:  await HAT.betolt('a1600130.tv', '20261209')  // időállapot nélkül: await HAT.betolt('a1700128.tv')
 *                    HAT.osszevet('<ujjlenyomat-sor>')            // Alaptörvénynél: HAT.osszevet('<sor>', true)
 *                    HAT.nulladik(617, '4l6em0')                  // a cím és a preambulum (0. szakasz) egyezése
 *                    HAT.labjegyzet(['427', '631'])               // mely módosító törvény, mikortól érinti a szakaszt
 *
 * A jogtar-azonosítók (docid): Pp a1600130.tv, Vht 99400053.tv, Itv 99000093.tv, Kmtv a1700128.tv, Nmjtv a1700028.tv,
 * Fmhtv a0900050.tv, Hetv a1000038.tv, Kjnp a0800045.tv, Bpnp a1700118.tv, Ánytv a1700043.tv, Alaptörvény a1100425.atv,
 * Ptk a1300005.tv.
 *
 * A korpusz-átalakító két szokása, amelyet az összevetés követ:
 *  - a teljes egészében hatályon kívül helyezett, üres szakasz („72. § *”) sora a korpuszban nincs benne;
 *  - az alcímek a megelőző szakasz végére kerülnek.
 * Ismert hibája: az azonos számú második szakaszt (Itv. 99/A. és 99/Q. §) elhagyja – ez „csak az oldalon” találatként jelenik meg.
 */
window.HAT = (() => {
  let doc = null;
  const norm = s => s.toLowerCase().replace(/[^0-9a-záéíóöőúüű]/g, '');
  const fnv = s => { let h = 0x811c9dc5; for (let i = 0; i < s.length; i++) { h ^= s.charCodeAt(i); h = Math.imul(h, 0x01000193) >>> 0; } return h; };
  const b36 = (n, k = 4) => (n % Math.pow(36, k)).toString(36).padStart(k, '0');
  const RE = /^\s*((?:\d+:)?\d+(?:\/[A-Z])?)\.\s*§/, REC = /^\s*([A-Z]|[IVXL]+|\d+)\.\s*cikk/, TART = /^\s*\d+(\/[A-Z])?\s*[–-]\s*\d+(\/[A-Z])?\.\s*§/;

  async function betolt(docid, ido) {
    const r = await fetch('/jogszabaly?docid=' + docid + (ido ? '&timeshift=' + ido : ''));
    if (!r.ok) throw new Error('nincs ilyen dokumentum vagy időállapot: ' + r.status);
    doc = new DOMParser().parseFromString(await r.text(), 'text/html');
    const hataly = (doc.body.textContent.match(/Hatály:[^\n]*/) || [''])[0].trim();
    const kov = [...doc.querySelectorAll('a')].filter(a => /időállapot|hatályos állapot/i.test(a.textContent)).map(a => a.textContent.trim());
    return { cim: doc.title, hataly, valtas: kov };
  }

  function szakaszok(cikk) {
    const d = doc.cloneNode(true);
    d.querySelectorAll('footer,nav,script,style').forEach(e => e.remove());
    d.querySelectorAll('li[id^=lbj]').forEach(e => e.remove());
    const info = [...d.querySelectorAll('p,h1,h2,h3,h4,h5,h6')].map(p => {
      const csillag = !!p.querySelector('sup');
      const c = p.cloneNode(true); c.querySelectorAll('sup').forEach(e => e.remove());
      const t = c.textContent;
      const m = cikk ? t.match(REC) : (p.tagName === 'P' && t.match(RE));
      const ures = !cikk && m && norm(t.replace(RE, '')) === '';
      return { tag: p.tagName, t, m, csillag, ures };
    });
    const seg = [['0', []]];
    for (let i = 0; i < info.length; i++) {
      const x = info[i];
      if (x.m) {
        const k = info[i + 1];
        const tartalomJon = k && k.tag === 'P' && !k.m && !TART.test(k.t);
        if (x.ures && x.csillag && !tartalomJon) continue;   // üres, hatályon kívül helyezett szakasz
        seg.push([x.m[1], []]);
      }
      seg[seg.length - 1][1].push(x.t);
    }
    return seg.map(([k, v]) => [k, norm(v.join(' '))]);
  }

  const indexel = arr => { const m = {}, n = {}; arr.forEach(([k, v]) => { n[k] = (n[k] || 0) + 1; m[k + (n[k] > 1 ? '#' + n[k] : '')] = v; }); return m; };

  function osszevet(ujjlenyomat, cikk) {
    const o = indexel(szakaszok(cikk).map(([k, t]) => [k, b36(fnv(t))]));
    const c = indexel(ujjlenyomat.trim().split(',').map(x => x.split('=')));
    const ki = { oldal: Object.keys(o).length, korpusz: Object.keys(c).length, eltero: [], csakOldalon: [], csakKorpuszban: [] };
    for (const k in o) { if (k === '0') continue; if (!(k in c)) ki.csakOldalon.push(k); else if (o[k] !== c[k]) ki.eltero.push(k); }
    for (const k in c) if (!(k in o)) ki.csakKorpuszban.push(k);
    return ki;
  }

  // a 0. szakasz (cím, preambulum) az oldalon fejléccel bővül: a végéről mért egyezés a mérce
  function nulladik(hossz, ujj, cikk) {
    const p = szakaszok(cikk)[0][1];
    return b36(fnv(p.slice(-(hossz - 150))), 6) === ujj;
  }

  function labjegyzet(kulcsok) {
    const ki = {}; let akt = '0';
    for (const p of doc.querySelectorAll('p,h1,h2,h3,h4,h5,h6')) {
      const c = p.cloneNode(true); c.querySelectorAll('sup').forEach(e => e.remove());
      const m = p.tagName === 'P' && c.textContent.match(RE); if (m) akt = m[1];
      if (!kulcsok.includes(akt)) continue;
      for (const a of p.querySelectorAll('a[href^="#lbj"]')) {
        const li = doc.getElementById(a.getAttribute('href').slice(1)); if (!li) continue;
        const t = li.textContent.replace(/\s+/g, ' ').trim();
        const mm = t.match(/(\d{4}\. évi [IVXLC]+)\. törvény/);
        const dd = t.match(/(?:Hatályos|Hatálytalan): (\d{4}\. [IVX]+\. \d+)/);
        if (mm) (ki[akt] = ki[akt] || new Set()).add(mm[1] + (dd ? ' @' + dd[1] : ''));
      }
    }
    for (const k in ki) ki[k] = [...ki[k]];
    return ki;
  }

  return { betolt, osszevet, nulladik, labjegyzet };
})();
