const { chromium, devices } = require('playwright');
const fs = require('fs');
const A = JSON.parse(fs.readFileSync('szolg/csomag.json', 'utf8'));
const M = JSON.parse(fs.readFileSync('minta.json', 'utf8'));
const ket = n => (n < 10 ? '0' : '') + n;
let hibak = [], ell = 0;
const var_ = (felt, uz) => { ell++; if (!felt) { hibak.push(uz); if (hibak.length <= 40) console.log('HIBA', uz); } };
(async () => {
  const b = await chromium.launch();
  const p = await b.newPage({ viewport: { width: 1100, height: 900 } });
  p.on('pageerror', e => hibak.push('pageerror: ' + e.message));
  p.on('console', m => { if (m.type() === 'error') hibak.push('console: ' + m.text()); });
  await p.goto('http://localhost:8765/szakvizsga/termekek.html');
  await p.evaluate(async () => { const a = await (await fetch('/csomag.json')).json(); window.SzakvizsgaTermekek.betolt(a, 'admin'); });
  // 1. önellenőrzés
  const e = await p.evaluate(() => window.SzakvizsgaTermekek.onellenorzes());
  console.log('önellenőrzés:', e.rendben, JSON.stringify(e.szamok), 'kombináció', e.kombinacio, e.hibak.slice(0, 5));
  var_(e.rendben, 'önellenőrzés hibás'); var_(e.sha256 === A.sha256, 'lenyomat eltér');
  // kifejezés-értékelő
  for (const [k, v, vart] of [['1/(gyermekagak+1)', { gyermekagak: 2 }, '1/3'], ['1/2/szulok', { szulok: 2 }, '1/4'], ['(1-1/2)*1/3', {}, '1/6'], ['2*3-4', {}, '2'], ['-(1/2)+1', {}, '1/2']])
    var_(await p.evaluate(([k, v]) => window.SzakvizsgaTermekek.kifejezes(k, v), [k, v]) === vart, 'kifejezés: ' + k);
  for (const rossz of ['1/0', 'alert(1)', '1+', 'a.b', '2**3'])
    var_(await p.evaluate(k => { try { window.SzakvizsgaTermekek.kifejezes(k, {}); return false; } catch (e) { return true; } }, rossz), 'a hibás kifejezést el kell utasítani: ' + rossz);
  // tipográfia
  await p.evaluate(k => window.SzakvizsgaTermekek.tetel(k), M.vazlat); await p.click('#fulek [data-ful="vazlat"]');
  const tip = await p.evaluate(() => { const s = x => { const c = getComputedStyle(document.querySelector(x)); return [c.fontFamily, c.fontSize, c.lineHeight, c.textAlign, c.hyphens || c.webkitHyphens]; }; return { p: s('#lap p.km'), h1: s('#lap h1'), h2: s('#lap h2'), h3: s('#lap h3'), gomb: s('#fulek button') }; });
  console.log('tipográfia', JSON.stringify(tip));
  // Bootstrap-megjelenés (Attila döntése, 2026-11-13): rendszer-betűkészlet, 15 px törzsszöveg
  var_(/^system-ui/.test(tip.p[0]) && tip.p[1] === '15px' && tip.p[2] === '24px' && tip.p[3] === 'justify' && tip.p[4] === 'auto', 'törzsszöveg tipográfia (sorkizárt, elválasztás)');
  var_(tip.h1[1] === '20.8px' && tip.h2[1] === '17.6px' && tip.h3[1] === '16px', 'címméretek'); var_(/^system-ui/.test(tip.gomb[0]), 'vezérlők betűtípusa');
  var_(await p.evaluate(() => getComputedStyle(document.querySelector('#fulek .nav-link.active')).backgroundColor === 'rgb(30, 58, 138)'), 'aktív fül színe');
  // Az „Újra” gomb a lista előtt áll (felidézés és sorrend)
  await p.evaluate(k => window.SzakvizsgaTermekek.tetel(k), M.felsorolas); await p.click('#fulek [data-ful="felsorolas"]');
  for (const mod of ['felidez', 'sorrend']) {
    await p.click(`[data-mod="${mod}"]`);
    var_(await p.evaluate(() => { const u = document.querySelector('[data-muvelet="ujra"]'), l = document.querySelector('ul.lista'); return !!(u && l && (u.compareDocumentPosition(l) & Node.DOCUMENT_POSITION_FOLLOWING)); }), 'az Újra gomb a lista előtt: ' + mod);
  }
  // zárható szakaszok
  await p.evaluate(k => window.SzakvizsgaTermekek.tetel(k), M.paragrafus); await p.click('#fulek [data-ful="paragrafus"]');
  var_(await p.locator('details.szakasz').count() > 1 && await p.locator('details.szakasz:not([open])').count() > 0, 'a §-jegyzék szakaszai zárhatók, nem mind nyitott');
  await p.fill('#lap input[type="search"]', M.parKereses || '5:44'); var_(await p.locator('details.szakasz[open] details.norma:not([hidden])').count() > 0, 'keresésnél a találat szakasza kinyílik');
  await p.fill('#lap input[type="search"]', '');
  await p.click('#fulek [data-ful="vazlat"]'); var_(await p.locator('details.szakasz').count() > 1, 'a vázlat főpontjai zárhatók');
  var_(await p.locator('#lap .cimke').count() === 0, 'a vázlatban nincs §-címkesor');
  var_(await p.locator('details.vjog').count() > 0 && await p.locator('details.vjog[open]').count() === 0, 'a vázlat §-ai zárt sorban');
  await p.evaluate(() => document.querySelectorAll('details.szakasz').forEach(d => { d.open = true; })); await p.locator('details.vjog > summary').first().click();
  var_(await p.locator('details.vjog[open] blockquote p').count() > 0, 'koppintásra megnyílik a normaszöveg');
  // tételválasztó: kereshető lista, csoportokkal
  await p.click('#tetelgomb'); var_(await p.locator('#tetelpanel').isVisible() && await p.locator('#tetellista .titem').count() === A.tetelek.length, 'a tételválasztó minden tételt mutat');
  var_(await p.locator('#tetellista .tcsop').count() === new Set(A.tetelek.map(t => t.csoport)).size, 'a tételválasztó csoportfejei');
  await p.fill('#tetelkereso', M.kereses); var_(await p.locator('#tetellista .titem').count() === 1, 'számra keresés');
  await p.press('#tetelkereso', 'Enter'); var_(await p.locator('#lap').getAttribute('data-tetel') === M.kereses && await p.locator('#tetelpanel').isHidden(), 'Enterre a találat nyílik meg');
  await p.click('#tetelgomb'); await p.fill('#tetelkereso', M.cimKereses || 'zalog'); var_(await p.locator('#tetellista .titem').count() >= 3, 'címrészletre keresés ékezet nélkül');
  await p.keyboard.press('Escape'); var_(await p.locator('#tetelpanel').isHidden(), 'Esc bezárja a tételválasztót');
  await p.click('#tetelgomb'); await p.click('#tetelzar'); var_(await p.locator('#tetelpanel').isHidden(), 'a ✕ gomb bezárja a tételválasztót');
  // a tétel teljes szövege: becsúszó panel, a vázlat nyitott főpontjánál
  await p.evaluate(k => window.SzakvizsgaTermekek.tetel(k), M.olvaso); await p.click('#fulek [data-ful="vazlat"]');
  const masodik = p.locator('#lap details.szakasz:not(.alszakasz) > summary').nth(2); const mcim = await p.locator('#lap details.szakasz:not(.alszakasz)').nth(2).getAttribute('data-cim'); await masodik.click();
  await p.click('#teljesgomb'); await p.waitForTimeout(400);
  var_(await p.locator('#olvaso').isVisible(), 'a teljes tétel panel megnyílik');
  var_(await p.locator('#olvasotorzs details.norma').count() === A.paragrafus_jegyzek[String(M.olvaso).padStart(2, "0")].length, 'a panelben minden §-doboz');
  var_(await p.locator('#olvasotorzs details.norma[open]').count() === 0, 'a panelben a §-dobozok zárva nyílnak');
  var_(await p.locator('#olvasohang .lgomb').count() === 5 && await p.locator('#olvasohang .lseb').count() === 1 && !(await p.locator('#olvasohang .lgomb.lfo').isDisabled()), 'a panelben a kliens lejátszója (5 ikongomb + sebesség, a lejátszás elérhető)');
  var_((await p.locator('#olvasohang .lreszszam').textContent()) === '1 / ' + A.tetelhang[String(M.olvaso).padStart(2, "0")].length, 'a lejátszó részléptetője');
  var_(await p.locator('#olvasotorzs details.szakasz').count() === A.tetelszoveg[String(M.olvaso).padStart(2, "0")].filter(b => b[0] === 'f').length, 'a teljes tétel főcímenként zárható');
  var_(await p.locator('#olvasotorzs details.szakasz[open]').count() === 0, 'a teljes tétel szakaszai zárva nyílnak');
  await p.click('#olvasohang .lseb'); var_((await p.locator('#olvasohang .lseb').textContent()) === '1.25x', 'sebességváltás (0,75 / 1,0 / 1,25)');
  var_(JSON.stringify(await p.locator('#olvasotorzs .szbelso > p, #olvasotorzs > p').allTextContents()) === JSON.stringify(A.tetelszoveg[String(M.olvaso).padStart(2, "0")].filter(b => b[0] === 'p').map(b => b[1])), 'a panel szövege betűre a tétel');
  var_(await p.evaluate(c => { const t = document.getElementById('olvasotorzs'), h = t.querySelector(`details.szakasz[data-cim="${CSS.escape(c)}"]`); if (!h) return false; const a = t.getBoundingClientRect(), b = h.getBoundingClientRect(); return b.top >= a.top - 1 && b.top < a.bottom - 20; }, mcim), 'a panel a vázlat nyitott főpontjánál nyílik');
  await p.keyboard.press('Escape'); await p.waitForTimeout(400); var_(await p.locator('#olvaso').isHidden(), 'Esc bezárja a panelt');
  // 2. minden tétel, minden fül
  for (const t of A.tetelek) {
    const k = ket(t.sorszam);
    await p.evaluate(k => window.SzakvizsgaTermekek.tetel(k), k);
    for (const [ful, db] of [['paragrafus', t.paragrafus], ['felsorolas', t.felsorolas], ['vazlat', t.vazlatMondat], ['fa', t.fak.length], ['szamolo', t.szamolok.length], ['matrix', t.matrixok.length]]) {
      const gomb = p.locator(`#fulek [data-ful="${ful}"]`);
      var_((await gomb.isDisabled()) === (db === 0), `${k} ${ful}: a fül tiltása`);
      if (!db) continue;
      await gomb.click();
      var_(await p.locator('#lap').getAttribute('data-ful') === ful, `${k} ${ful}: nem váltott`);
      if (ful === 'paragrafus') {
        var_(await p.locator('#lap details.norma').count() === db, `${k}: §-dobozok száma`);
        const szov = await p.locator('#lap details.norma .nszov p').allTextContents();
        var_(JSON.stringify(szov) === JSON.stringify(A.paragrafus_jegyzek[k].flatMap(x => (x.cim && x.sorok.length && x.sorok[0].trim() === '[' + x.cim + ']') ? x.sorok.slice(1) : x.sorok)), `${k}: §-szöveg eltér`);
      }
      if (ful === 'vazlat') {
        const szov = await p.locator('p.km').allTextContents();
        var_(JSON.stringify(szov) === JSON.stringify(A.hangos_vazlat[k].fopontok.flatMap(f => f.alpontok.flatMap(a => a.mondatok.map(m => m.szoveg)))), `${k}: vázlatmondatok eltérnek`);
      }
      if (ful === 'felsorolas') {
        const listak = A.felsorolas[k];
        for (let i = 0; i < listak.length; i++) {
          const l = listak[i];
          if (listak.length > 1) await p.selectOption('#lap select', String(i));
          // teljes szöveg
          await p.click('[data-mod="olvas"]');
          var_(JSON.stringify(await p.locator('ul.lista > li .torzs').evaluateAll(x => x.map(y => y.firstChild.textContent))) === JSON.stringify(l.elemek.map(x => x.szoveg)), `${k} ${l.id}: teljes szöveg`);
          // felidézés
          await p.click('[data-mod="felidez"]');
          var_(await p.locator('ul.lista > li.takart').count() === l.elemek.length, `${k} ${l.id}: takart elemek`);
          for (let j = 0; j < l.elemek.length; j++) await p.locator('ul.lista > li').nth(j).click();
          var_(await p.locator('ul.lista > li.takart').count() === 0, `${k} ${l.id}: felfedés`);
          await p.locator('ul.lista > li').first().locator('button', { hasText: 'Tudtam' }).first().click();
          var_(await p.locator('ul.lista > li.tudta').count() === 1, `${k} ${l.id}: tudtam`);
          // sorrend
          await p.click('[data-mod="sorrend"]');
          var_(await p.locator('ul.lista > li').count() === l.elemek.length, `${k} ${l.id}: sorrend elemszám`);
          await p.click('[data-muvelet="ellenoriz"]');
          var_(await p.locator('ul.lista > li.jo, ul.lista > li.rossz').count() === l.elemek.length, `${k} ${l.id}: sorrend értékelés`);
          var_(await p.locator('ul.lista > li.jo').count() < l.elemek.length, `${k} ${l.id}: a kevert sorrend nem lehet az eredeti`);
          const kap = await p.locator('[data-mod="kapcsolat"]').count();
          var_((kap === 1) === (l.kapcsolo === 'és' || l.kapcsolo === 'vagy'), `${k} ${l.id}: kapcsolat mód`);
          if (kap) { await p.click('[data-mod="kapcsolat"]'); await p.click(`[data-kapcsolo="${l.kapcsolo}"]`); var_((await p.locator('.sav.ok').textContent()).startsWith('Helyes'), `${k} ${l.id}: kapcsolat`); }
        }
      }
      if (ful === 'fa') {
        for (const id of t.fak) {
          const fa = A.dontesi_fa[id];
          if (t.fak.length > 1) await p.selectOption('#lap select', id);
          for (let i = 0; i < fa.peldak.length; i++) {
            const pl = fa.peldak[i];
            await p.click(`[data-pelda="${i}"]`);
            var_(await p.locator('.csomo.eredmeny').getAttribute('data-csomopont') === pl.eredmeny, `fa ${id} ${i + 1}. példa gombbal`);
            // kézzel végigkattintva
            await p.locator('button', { hasText: 'Elölről' }).click();
            for (const v of pl.valaszok) await p.locator('.csomo.most .agak button').filter({ hasText: new RegExp('^' + v.replace(/[.*+?^${}()|[\]\\]/g, '\\$&') + '$') }).click();
            var_(await p.locator('.csomo.eredmeny').getAttribute('data-csomopont') === pl.eredmeny, `fa ${id} ${i + 1}. példa kattintva`);
            var_(await p.locator('.csomo.eredmeny .kerdes').textContent() === fa.csomopontok[pl.eredmeny].szoveg, `fa ${id} ${i + 1}. példa szövege`);
            var_(await p.locator('.csomo').count() === pl.valaszok.length + 1, `fa ${id} ${i + 1}. példa: út hossza`);
          }
          const idez = await p.locator('.csomo').last().locator('blockquote').count();
          var_(idez >= 1, `fa ${id}: jogalap hiányzik`);
        }
      }
      if (ful === 'szamolo') {
        for (const id of t.szamolok) {
          const d = A.szamolo[id];
          if (t.szamolok.length > 1) await p.selectOption('#lap select', id);
          for (let i = 0; i < d.peldak.length; i++) {
            const pl = d.peldak[i];
            await p.click(`[data-pelda="${i}"]`);
            var_(await p.locator('.csomo.eredmeny').getAttribute('data-szabaly') === pl.szabaly, `számoló ${id} ${i + 1}. példa`);
            const tortek = (await p.locator('.csomo.eredmeny .tort').allTextContents()).sort();
            var_(JSON.stringify(tortek) === JSON.stringify(pl.vart.map(x => x.hanyad).sort()), `számoló ${id} ${i + 1}. példa hányadai: ${tortek}`);
          }
        }
      }
      if (ful === 'matrix') {
        for (const id of t.matrixok) {
          const m = A.fogalommatrix[id];
          if (t.matrixok.length > 1) await p.selectOption('#lap select', id);
          var_(await p.locator('td.cella').count() === m.cellak.length, `mátrix ${id}: cellaszám`);
          for (const c of m.cellak) {
            const td = p.locator(`td.cella[data-cella="${c.sor}|${c.oszlop}"]`);
            var_(await td.textContent() === c.cimke, `mátrix ${id}: címke`);
            await td.click();
            var_((await p.locator('.kartya[aria-live] p').allTextContents()).join('|').includes(c.forrasok[0].szoveg), `mátrix ${id}: forrás`);
          }
          await p.click('[data-muvelet="takar"]');
          var_(await p.locator('td.cella.takart').count() === m.cellak.length, `mátrix ${id}: takarás`);
          await p.locator('td.cella').first().click();
          var_(await p.locator('td.cella.takart').count() === m.cellak.length - 1, `mátrix ${id}: felfedés`);
          await p.click('[data-muvelet="takar"]');
        }
      }
    }
  }
  // fa → számoló ugrás
  await p.evaluate(k => window.SzakvizsgaTermekek.tetel(k), M.fa); await p.click('#fulek [data-ful="fa"]');
  const elb = A.tetelek.find(t => t.sorszam === Number(M.fa)).fak;
  await p.selectOption('#lap select', 'elbirtoklas');
  const fa = A.dontesi_fa['elbirtoklas']; const pl = fa.peldak.find(x => fa.csomopontok[x.eredmeny].szamolo || true);
  let ugrott = false;
  for (let i = 0; i < fa.peldak.length && !ugrott; i++) { await p.click(`[data-pelda="${i}"]`); if (await p.locator('[data-szamolo]').count()) { await p.locator('[data-szamolo]').first().click(); ugrott = await p.locator('#lap').getAttribute('data-ful') === 'szamolo'; } }
  var_(ugrott, 'fa → számoló ugrás');
  // 3. képek (asztali)
  const kepek = [[M.vazlat, 'paragrafus'], [M.vazlat, 'felsorolas'], [M.vazlat, 'vazlat'], [M.vazlat, 'fa'], [M.szamolo, 'szamolo'], [M.matrix, 'matrix']];
  for (const [k, ful] of kepek) { await p.evaluate(k => window.SzakvizsgaTermekek.tetel(k), k); await p.click(`#fulek [data-ful="${ful}"]`); if (ful === 'fa' || ful === 'szamolo') await p.click('[data-pelda="0"]'); await p.screenshot({ path: `kepek/asztal_${ful}.png` }); }
  await p.click('#onellgomb'); await p.waitForFunction(() => window.__onellenorzes); await p.locator('#admin').scrollIntoViewIfNeeded(); await p.screenshot({ path: 'kepek/asztal_admin.png' });
  // 4. telefon: nincs vízszintes görgetés
  const m = await b.newPage({ viewport: { width: 390, height: 800 } });
  await m.goto('http://localhost:8765/szakvizsga/termekek.html');
  await m.evaluate(async () => { const a = await (await fetch('/csomag.json')).json(); window.SzakvizsgaTermekek.betolt(a, 'kliens'); });
  var_(await m.locator('#admin').isHidden(), 'kliens módban az admin rész rejtett');
  for (const t of A.tetelek) for (const ful of ['paragrafus', 'felsorolas', 'vazlat', 'fa', 'szamolo', 'matrix']) {
    await m.evaluate(k => window.SzakvizsgaTermekek.tetel(k), ket(t.sorszam));
    const g = m.locator(`#fulek [data-ful="${ful}"]`); if (await g.isDisabled()) continue;
    var_(await m.locator('#fulmenu').isVisible() && await g.isHidden(), 'telefon: a fülek a menüben'); await m.click('#fulmenu'); await g.click();
    var_(await g.isHidden(), 'telefon: a menü választás után bezárul');
    const sz = await m.evaluate(() => document.scrollingElement.scrollWidth - window.innerWidth);
    var_(sz <= 0, `telefon: vízszintes túlcsordulás ${t.sorszam} ${ful}: ${sz}px`);
  }
  for (const [k, ful] of kepek) { await m.evaluate(k => window.SzakvizsgaTermekek.tetel(k), k); await m.click('#fulmenu'); await m.click(`#fulek [data-ful="${ful}"]`); if (ful === 'fa' || ful === 'szamolo') await m.click('[data-pelda="0"]'); await m.screenshot({ path: `kepek/telefon_${ful}.png` }); }
  // 5. beágyazva: üzenetváltás
  const s = await b.newPage({ viewport: { width: 1000, height: 800 } });
  await s.goto('http://localhost:8765/szulo.html');
  await s.waitForFunction(() => window.uzenetek.some(u => u.type === 'nezet'));
  const fr = s.frameLocator('#f');
  var_(await fr.locator('#lap').getAttribute('data-tetel') === M.beagyazott && await fr.locator('#lap').getAttribute('data-ful') === 'fa', 'beágyazva: a kért nézet');
  var_(await fr.locator('#onallo').isHidden(), 'beágyazva: nincs fájlválasztó');
  await fr.locator('#onellgomb').click();
  await s.waitForFunction(() => window.uzenetek.some(u => u.type === 'onellenorzes'));
  const uz = await s.evaluate(() => window.uzenetek);
  var_(uz[0].type === 'kesz', 'első üzenet: kesz'); var_(uz.find(u => u.type === 'onellenorzes').rendben === true, 'beágyazott önellenőrzés');
  // a csomag újratöltése után a léptetés pontosan egy tételt lép
  await s.evaluate(t => fetch('/csomag.json').then(r => r.json()).then(a => document.getElementById('f').contentWindow.postMessage({ source: 'szakvizsga-termekek-szulo', type: 'csomag', adat: a, mod: 'admin', nezet: { tetel: t, ful: 'fa' } }, location.origin)), Number(M.beagyazott));
  await s.waitForFunction(() => window.uzenetek.filter(u => u.type === 'nezet').length >= 2);
  await fr.locator('#kovetkezo').click();
  var_(await fr.locator('#lap').getAttribute('data-tetel') === String(Number(M.beagyazott) + 1), 'újratöltés után a léptetés egyet lép: ' + await fr.locator('#lap').getAttribute('data-tetel'));
  await fr.locator('#elozo').click();
  await fr.locator('#fulek [data-ful="fa"]').click();
  // a tétel hangja: a megjelenítő aláírt címet kér a szülőtől (path), és azt tölti be
  await fr.locator('#tetelgomb').click(); await fr.locator('#tetelkereso').fill(M.olvaso); await fr.locator('#tetelkereso').press('Enter');
  await fr.locator('#teljesgomb').click(); await fr.locator('#olvasohang .lgomb.lfo').click();
  await s.waitForFunction(() => window.uzenetek.some(u => u.type === 'hang-keres'));
  const hk = (await s.evaluate(() => window.uzenetek)).find(u => u.type === 'hang-keres');
  var_(/^audio\/notes\/[\w-]+\.mp3$/.test(hk.path), 'beágyazva: hangcím-kérés Storage-útvonallal: ' + hk.path);
  await s.waitForFunction(() => { const a = document.getElementById('f').contentDocument.querySelector('#olvasohang audio'); return a && /proba\.mp3$/.test(a.src); });
  var_(true, 'beágyazva: az aláírt cím betöltődik a lejátszóba');
  await fr.locator('#olvasozar').click(); await s.waitForTimeout(400);
  await fr.locator('#tetelgomb').click(); await fr.locator('#tetelkereso').fill(M.beagyazott); await fr.locator('#tetelkereso').press('Enter'); await fr.locator('#fulek [data-ful="fa"]').click();
  // idegen forrású üzenetet nem fogad el
  await s.evaluate(() => document.getElementById('f').contentWindow.postMessage({ source: 'valami-mas', type: 'hiba', uzenet: 'x' }, location.origin));
  var_(await fr.locator('#lap').getAttribute('data-ful') === 'fa', 'idegen forrású üzenet figyelmen kívül');
  // hibás csomag
  await s.evaluate(() => document.getElementById('f').contentWindow.postMessage({ source: 'szakvizsga-termekek-szulo', type: 'csomag', adat: { sema: 2 } }, location.origin));
  await fr.locator('.ures.hiba').waitFor();
  var_((await fr.locator('.ures.hiba').textContent()).includes('sema'), 'hibás csomag üzenete');
  // tiltott szavak a felületen
  const szoveg = fs.readFileSync('szolg/szakvizsga/termekek.html', 'utf8').replace(/<!--[\s\S]*?-->/g, '');
  var_(!/tananyag|zh-felkészítő/i.test(szoveg), 'tiltott szó a megjelenítőben');
  var_(!/https?:\/\//.test(szoveg), 'külső hivatkozás a megjelenítőben');
  console.log(`ellenőrzések: ${ell}, hiba: ${hibak.length}`);
  if (hibak.length) console.log(hibak.slice(0, 40).join('\n'));
  await b.close(); process.exit(hibak.length ? 1 : 0);
})();
