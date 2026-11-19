#!/usr/bin/env python3
"""A tétel szövegéből (NN.txt) a publikált rész-jegyzetek HTML-je, determinisztikusan, AI nélkül.

    python3 tools/jegyzet_html.py NN          # egy tétel: termekek/jegyzet_html/NN.json (+ index.json frissítése)
    python3 tools/jegyzet_html.py --mind      # mind a 85 tétel + termekek/jegyzet_html/index.json
    python3 tools/jegyzet_html.py --reszcim   # a részcímek kimérése (táblázat a kimenetre; nem ír fájlt)

Részek. Egy rész = egy jegyzet (`notes`, type=text, audioSource = a hangdokumentum) = egy hangdokumentum; a
jegyzetazonosítók maradnak. A részek a bázis `egyeb/notes/NN/` jegyzetei (a hangpotlas-2-2026-11-12 ág állapota, a
munkafában változatlan), partIndex szerint; a jegyzet hangdokumentumait a `tts/*/_meta.json` `noteId` mezője köti hozzá.
Ha egy rész jegyzetazonosítója nem állapítható meg egyértelműen, a program megáll és listáz.
Új tételsor-szerkezet (a tárolóban nincs `egyeb/notes/`; kozos.jegyzet_megfeleltetes): a részek a
`tetelsor/jegyzet_megfeleltetes.json` sorrendjében (noteId, cim), a rész hangdokumentuma az a `tts/*/_meta.json`, amelynek
noteId-je a részé és `via: audioSource`. Hangdokumentum nélküli rész nem megálló: hang nélkül készül el (ttsId: null,
a kimeneten „hang nélküli rész” sor); a kezdőblokkja az első olyan címsor, amely a rész címével kezdődik vagy az
iránymutatás-azonosítóját tartalmazza (horgony); ha nincs ilyen, a rész tartalom nélküli (blokkok: null, html: ""). A
hanggal bíró részek határa a horgonyok közötti szakaszban a lent leírt módszerrel dől el.
Az `egyeb/notes/` szerkezetében (A/1) a kódút változatlan.

Részhatár. A tétel blokkjait (tools/tetel_blokk.py) a hangdokumentumok darabjai osztják részekre, a
`tools/hangszoveg.py lefedettseg` módszerével: a bekezdésből (a szöveg `\\n\\n`-nel elválasztott egysége) vett ötszavas
mintaablakok közül hány van meg az egyes részek darabjaiban. A blokk pontszáma részenként a hozzá tartozó bekezdések
pontszámainak összege; a blokkok sorrendben, folytonosan, minden részbe legalább egy jusson (monoton felosztás),
és a felosztás a pontszámok összegét maximalizálja (dinamikus programozás). A pontszám nélküli blokk (címsor,
dobozfej, fel nem olvasott bekezdés) a részhatáron a következő részhez kerül (a címsor a tartalmával megy).
Bizonytalan a blokk, ha más rész darabjaiban több ablaka van meg, mint a sajátjáéban: ezeket a `bizonytalan` mező
sorolja fel.

HTML (az élő jegyzetek szerkezete; a szabályok a modul végén, a `html_*` függvényekben):
  egyrészes tétel: <h1>tétel címe (tetelsor.json)</h1> az elején; főcím <h2>; alcím <h3> (mondatkezdő írással:
  cimsor/mondatkezdo, a szavak alakja a tétel törzsszövegéből); bekezdés <p>;
  a „- ”/„– ” jeles egymást követő bekezdések <ul><li>…</li></ul>; jogszabálydoboz:
  <div class="jogszabaly-doboz"><span class="jogszabaly-cimke">fejléc</span><p>…</p></div>, a dobozban a sorok
  <br>-rel, a betűs pont <span class="jogszabaly-pont" style="display:block;padding-left:28px">, a kétbetűs alpont és
  a ponton belüli gondolatjeles tag <span class="jogszabaly-alpont" style="display:block;padding-left:42px">; a pont-
  és alpont-span előtt és után nincs <br>. Elemek között nincs szóköz/sortörés. Színes kiemelés nincs.
A szöveg HTML-escape-elve (&, <, >); idézőjel, gondolatjel, § változatlan.
"""
import argparse, glob, hashlib, html, json, os, re, sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import kozos
import tetel_blokk
import hangszoveg as hs

GY = kozos.GYOKER
KI = os.path.join(GY, 'termekek', 'jegyzet_html')
PONT_STILUS = 'display:block;padding-left:28px'
ALPONT_STILUS = 'display:block;padding-left:42px'
FELSOROLASJEL = re.compile(r'^[-–•]\s+')


class Megall(Exception):
    pass


# ---------- részek (jegyzetek) ----------
_META = None


def tts_meta():
    global _META
    if _META is None:
        _META = {}
        for f in sorted(glob.glob(os.path.join(GY, 'tts', '*', '_meta.json'))):
            m = json.load(open(f, encoding='utf-8'))
            _META[m['ttsId']] = (m, os.path.dirname(f))
    return _META


def reszek(n):
    """A tétel részei partIndex szerint: [{noteId, ttsId, title, partIndex, partCount, docs:[ttsId…]}]."""
    jm = kozos.jegyzet_megfeleltetes()
    if jm is not None:
        return reszek_megfeleltetes(n, jm)
    hibak = []
    jegyzet = []
    for f in sorted(glob.glob(os.path.join(GY, 'egyeb', 'notes', f'{n:02d}', '*.json'))):
        d = json.load(open(f, encoding='utf-8'))
        if d.get('type') == 'text' and d.get('audioSource') and d.get('status') == 'Published' and not d.get('deletedAt'):
            jegyzet.append(d)
    if not jegyzet:
        raise Megall(f'{n}. tétel: nincs hanggal kötött szöveges jegyzet a bázisban')
    meta = tts_meta()
    if len(jegyzet) == 1:
        d = jegyzet[0]
        if d.get('partIndex') not in (None, 1) or d.get('partCount') not in (None, 1):
            hibak.append(f"{d['id']}: egyetlen rész, de partIndex/partCount = {d.get('partIndex')}/{d.get('partCount')}")
    else:
        idx = sorted(d.get('partIndex') or 0 for d in jegyzet)
        if idx != list(range(1, len(jegyzet) + 1)) or any(d.get('partCount') != len(jegyzet) for d in jegyzet):
            hibak.append('a partIndex/partCount nem folytonos: ' + ', '.join(f"{d['id']}={d.get('partIndex')}/{d.get('partCount')}" for d in jegyzet))
    out = []
    for d in sorted(jegyzet, key=lambda d: d.get('partIndex') or 1):
        tid = d['audioSource']
        if tid not in meta:
            hibak.append(f"{d['id']}: a hangdokumentum ({tid}) nincs a tts/ mappában"); continue
        if meta[tid][0]['noteId'] != d['id']:
            hibak.append(f"{d['id']}: a hangdokumentum ({tid}) más jegyzethez tartozik ({meta[tid][0]['noteId']})"); continue
        docs = [t for t, (m, _) in meta.items() if m['noteId'] == d['id']]
        out.append({'noteId': d['id'], 'ttsId': tid, 'title': d['title'], 'partIndex': d.get('partIndex') or 1,
                    'partCount': len(jegyzet), 'docs': sorted(docs, key=lambda t: (t != tid, t))})
    # a tétel minden hangdokumentuma valamelyik részhez kötődjön
    sajat = {t for r in out for t in r['docs']}
    for tid, _, _ in hs.tetel_hang(n):
        if tid not in sajat:
            hibak.append(f'{tid}: a tétel hangdokumentuma, de jegyzete ({meta[tid][0]["noteId"]}) nem része a tételnek')
    if hibak:
        raise Megall(f'{n}. tétel: a részek jegyzetazonosítója nem egyértelmű:\n  ' + '\n  '.join(hibak))
    return out


def reszek_megfeleltetes(n, jm):
    """Az új tételsor-szerkezet részei (tetelsor/jegyzet_megfeleltetes.json): a sorrend a megfeleltetésé, a rész
    hangdokumentuma a noteId-jéhez `via: audioSource`-szal kötött tts/*/_meta.json; ha nincs ilyen, ttsId: None
    (hang nélküli rész, nem megálló)."""
    lista = jm.get(n) or []
    if not lista:
        raise Megall(f'{n}. tétel: nincs jegyzet a tetelsor/jegyzet_megfeleltetes.json-ban')
    meta = tts_meta()
    hibak = []
    ids = [r['noteId'] for r in lista]
    if len(set(ids)) != len(ids):
        hibak.append('ismétlődő jegyzetazonosító: ' + ', '.join(sorted({x for x in ids if ids.count(x) > 1})))
    out = []
    for i, r in enumerate(lista, 1):
        docs = [t for t, (m, _) in meta.items() if m.get('noteId') == r['noteId']]
        fo = [t for t in docs if meta[t][0].get('via') == 'audioSource']
        if len(fo) > 1:
            hibak.append(f"{r['noteId']}: több audioSource-hangdokumentum: {', '.join(sorted(fo))}"); continue
        tid = fo[0] if fo else None
        out.append({'noteId': r['noteId'], 'ttsId': tid, 'title': r['cim'], 'partIndex': i, 'partCount': len(lista),
                    'docs': sorted(docs, key=lambda t: (t != tid, t))})
    sajat = {t for r in out for t in r['docs']}
    for tid, _, _ in hs.tetel_hang(n):
        if tid not in sajat:
            hibak.append(f'{tid}: a tétel hangdokumentuma, de jegyzete ({meta[tid][0]["noteId"]}) nem része a tételnek')
    if hibak:
        raise Megall(f'{n}. tétel: a részek jegyzetazonosítója nem egyértelmű:\n  ' + '\n  '.join(hibak))
    return out


_CIM_ELO = re.compile(r'^(?:\d+\)?\.\)?\s*)?(?:\([IVXL]+(?:-[IVXL]+)?\.\)\s*)?')


def _azonosito(s):
    """A rész címének iránymutatás-azonosítója regexként: „1/2019.” → számjel/év, „PK 13”, „PK-GK 2”, „MK 35”."""
    m = re.search(r'(?<![\d/])(\d+/\d{4})(?!\d)', s)
    if m:
        return r'(?<![\d/])' + re.escape(m.group(1)) + r'(?!\d)'
    m = re.search(r'\b(PK-GK|PK|GK|MK)\.?\s*(\d+)(?!\d)', s)
    if m:
        return r'(?<![\w-])' + re.escape(m.group(1)) + r'\.?\s*' + m.group(2) + r'(?!\d)'
    return None


def horgony(blokk, cim, tol):
    """A hang nélküli rész kezdőblokkja a tol. blokktól: az első címsor (főcím, alcím), amely a rész címével kezdődik (a
    cím sorszám- és tartomány-előtagja nélkül, kisbetűsítve; „PK 133” → „PK 133. SZÁM”); ha ilyen nincs, az első címsor,
    amely a cím iránymutatás-azonosítóját tartalmazza („1/2019. PJE” → „MELLÉKLET: AZ 1/2019. …”); None, ha egyik sincs."""
    c = kozos.norm(_CIM_ELO.sub('', cim)).casefold().rstrip('.')
    if c:
        for u in range(tol, len(blokk)):
            if blokk[u][0] in 'fa' and kozos.norm(ELOTAG.sub('', blokk[u][1])).casefold().startswith(c):
                return u
    rx = _azonosito(cim)
    if rx:
        for u in range(tol, len(blokk)):
            if blokk[u][0] in 'fa' and re.search(rx, kozos.norm(blokk[u][1]), re.I):
                return u
    return None


def felosztas_reszek(n, rr, blokk, ix, txt):
    """A felosztás, ha van hang nélküli rész (az új szerkezetben): a hang nélküli rész a horgony()-nyal talált címsornál
    kezdődik; ha a tételben nincs ilyen címsor, a rész tartalom nélküli (a tétel szövege nem tartalmazza; blokkot nem
    kap, a kimenet jelzi). A horgonyok közötti szakaszok hanggal bíró részeit a felosztas() osztja el. Ha minden résznek
    van hangja: felosztas(). Visszatér: ([részindex blokkonként], [bizonytalan blokkok]); a részindex az rr indexe."""
    if all(r['ttsId'] for r in rr):
        return felosztas(n, rr, blokk, ix, txt)
    U = len(blokk); m = len(rr)
    kezd = {0: 0}; ures = set(); utolso = 0
    for k in range(1, m):
        if not rr[k]['ttsId']:
            u = horgony(blokk, rr[k]['title'], utolso + 1)
            if u is None:
                ures.add(k); continue
            kezd[k] = utolso = u
    aktiv = [k for k in range(m) if k not in ures]
    L = txt.split('\n')
    hoz = [0] * U; bizonytalan = []
    horg = [i for i, k in enumerate(aktiv) if k in kezd]
    for j, i0 in enumerate(horg):
        i1 = horg[j + 1] if j + 1 < len(horg) else len(aktiv)
        resz = aktiv[i0:i1]
        a = kezd[aktiv[i0]]; b = kezd[aktiv[i1]] if i1 < len(aktiv) else U
        if b - a < len(resz):
            raise Megall(f'{n}. tétel: több rész, mint blokk ({", ".join(str(k + 1) for k in resz)}. rész)')
        h, bz = felosztas(n, [rr[k] for k in resz], blokk[a:b], ix[a:b], txt, vege=(ix[b] if b < U else len(L)))
        for u, x in enumerate(h):
            hoz[a + u] = resz[x]
        for x in bz:
            bizonytalan.append(dict(x, blokk=x['blokk'] + a, resz=resz[x['resz'] - 1] + 1))
    return hoz, bizonytalan


# ---------- blokk → rész ----------
def bekezdes_sorok(txt):
    """A `\\n\\n`-nel elválasztott bekezdések (a hangszoveg.blokkok indexelése) → sorindex → bekezdésindex."""
    L = txt.split('\n')
    sor2bek = {}
    pos = 0; k = 0
    for darab in txt.split('\n\n'):
        nl = darab.count('\n') + 1
        if darab.strip():
            for x in range(pos, pos + nl):
                sor2bek[x] = k
            k += 1
        pos += nl + 1
    return L, sor2bek, k


def bekezdes_pont(n, rr):
    """Bekezdésenként és részenként a megtalált mintaablakok száma (a hangszoveg.lefedettseg ablakai)."""
    meta = tts_meta()
    darabok = []   # (részindex, darabszöveg)
    for ri, r in enumerate(rr):
        for tid in r['docs']:
            m, d = meta[tid]
            for c in m['chunks']:
                sz = open(os.path.join(d, c['file']), encoding='utf-8').read()
                darabok.append((ri, ' ' + ' '.join(t for t in hs.tokenek(re.sub(r'\[[a-z ]+\]', ' ', sz)) if not t.isdigit()) + ' '))
    pont = []
    for i, b in enumerate(hs.blokkok(n)):
        tk = hs.tokenek(re.sub(r'§-[a-záéíóöőúüű]+', '§ 0', b.lower()))
        ablak = []
        for j in range(0, max(len(tk) - 4, 0)):
            w = tk[j:j + 5]
            if any(x.isdigit() or x in hs.KIZART or len(x) < 2 or hs.romai_token(x) for x in w):
                continue
            ablak.append(' ' + ' '.join(w) + ' ')
        p = [0] * len(rr)
        if ablak and i > 0:
            minta = ablak[::max(1, len(ablak) // 6)]
            for ri in range(len(rr)):
                p[ri] = sum(1 for a in minta if any(a in sz for r2, sz in darabok if r2 == ri))
        pont.append(p)
    return pont


def felosztas(n, rr, blokk, ix, txt, vege=None):
    """[részindex blokkonként], [bizonytalan blokkok]. vege: az utolsó blokk utáni sorindex (a tétel egy szakaszának
    felosztásakor, felosztas_reszek); alapértéke a tétel vége."""
    m = len(rr)
    if m == 1:
        return [0] * len(blokk), []
    L, sor2bek, nbek = bekezdes_sorok(txt)
    if nbek != len(hs.blokkok(n)):
        raise Megall(f'{n}. tétel: a bekezdés-indexelés eltér a hangszoveg.blokkok indexelésétől')
    bp = bekezdes_pont(n, rr)
    # a blokk sorai: a kezdősorától a következő blokk kezdősoráig
    hatar = ix[1:] + [len(L) if vege is None else vege]
    pont = []
    for u in range(len(blokk)):
        beks = sorted({sor2bek[x] for x in range(ix[u], hatar[u]) if x in sor2bek})
        pont.append([sum(bp[k][ri] for k in beks) for ri in range(m)])
    U = len(blokk)
    NEG = float('-inf')
    # dp[u][k]: az első u+1 blokk legjobb pontszáma, ha az u. blokk a k. részben van
    dp = [[NEG] * m for _ in range(U)]
    el = [[0] * m for _ in range(U)]
    dp[0][0] = pont[0][0]
    for u in range(1, U):
        for k in range(m):
            a = dp[u - 1][k]
            b = dp[u - 1][k - 1] if k > 0 else NEG
            if b >= a:    # egyenlőségnél a határ a lehető legkésőbbre kerül (utána a címsorok visszatolódnak)
                dp[u][k], el[u][k] = b + pont[u][k], k - 1
            else:
                dp[u][k], el[u][k] = a + pont[u][k], k
    if dp[U - 1][m - 1] == NEG:
        raise Megall(f'{n}. tétel: több rész, mint blokk')
    hoz = [0] * U; k = m - 1
    for u in range(U - 1, -1, -1):
        hoz[u] = k; k = el[u][k]
    # a rész végén álló, az előző részre nem egyértelmű (pontszám nélküli vagy döntetlen) blokkok futamából az első címsortól (főcím, alcím) kezdve minden a következő
    # részhez kerül (a címsor a tartalmával megy); a futam címsor előtti bekezdése, doboza az előző részben marad;
    # a részben legalább egy blokk marad
    for k in range(1, m):
        b = hoz.index(k)
        v = b
        while v - 2 >= 0 and hoz[v - 2] == k - 1 and pont[v - 1][k - 1] <= pont[v - 1][k]:
            v -= 1
        cs = next((w for w in range(v, b) if blokk[w][0] in 'fa'), None)
        if cs is not None:
            for w in range(cs, b):
                hoz[w] = k
    bizonytalan = []
    for u in range(U):
        sajat = pont[u][hoz[u]]
        mas = max((pont[u][k] for k in range(m) if k != hoz[u]), default=0)
        if mas > sajat:
            bizonytalan.append({'blokk': u, 'resz': hoz[u] + 1, 'ok': f'más rész darabjaiban több ablak ({mas} > {sajat})',
                                'szoveg': (blokk[u][1] if blokk[u][0] != 'd' else f'[doboz {blokk[u][1]}]')[:90]})
    # a határzóna: az előző rész utolsó egyértelmű blokkja és a következő rész első egyértelmű blokkja között csak
    # címsor vagy ablak nélküli blokk állhat; más blokk helye a határon nem dönthető el
    for k in range(1, m):
        b = hoz.index(k)
        a = max([u for u in range(b) if pont[u][k - 1] > pont[u][k]], default=-1)
        c = min([u for u in range(b, U) if pont[u][k] > pont[u][k - 1]], default=U)
        for u in range(a + 1, c):
            if blokk[u][0] not in 'fa':
                bizonytalan.append({'blokk': u, 'resz': hoz[u] + 1, 'ok': f'a {k}./{k + 1}. rész határzónájában, ' + ('döntetlen ablakszámmal' if any(pont[u]) else 'felolvasott ablak nélkül'),
                                    'szoveg': (blokk[u][1] if blokk[u][0] != 'd' else f'[doboz {blokk[u][1]}]')[:90]})
    if sorted(set(hoz)) != list(range(m)):
        raise Megall(f'{n}. tétel: üres rész a felosztásban')
    return hoz, bizonytalan


# ---------- HTML ----------
def e(s):
    return html.escape(s, quote=False)


def html_doboz(fejlec, sorok):
    """A doboz: cimke + egy <p>; a sorok <br>-rel, a pontok blokk-spanként (előttük és utánuk nincs <br>)."""
    belso = []
    elozo_span = True   # a <p> elején nincs <br>
    for s in sorok:
        if re.match(r'^[a-z]\) ', s):
            belso.append(f'<span class="jogszabaly-pont" style="{PONT_STILUS}">{e(s)}</span>'); elozo_span = True
        elif re.match(r'^[a-z]{2}\) ', s) or re.match(r'^[–-] ', s):
            belso.append(f'<span class="jogszabaly-alpont" style="{ALPONT_STILUS}">{e(s)}</span>'); elozo_span = True
        else:
            belso.append(('' if elozo_span else '<br>') + e(s)); elozo_span = False
    return f'<div class="jogszabaly-doboz"><span class="jogszabaly-cimke">{e(fejlec)}</span><p>{"".join(belso)}</p></div>'


def tetel_html(n):
    txt = kozos.tetel_szoveg(n)
    blokk, ix = tetel_blokk.blokkok_sorral(n)
    assert len(blokk) == len(ix)
    L = txt.split('\n')
    dob = kozos.dobozok(txt)
    pj = json.load(open(os.path.join(GY, 'termekek', 'paragrafus_jegyzek', f'{n:02d}.json'), encoding='utf-8'))['elemek']
    for (kod, par, fej, sorok), elem in zip(dob, pj):
        if fej != elem['fejlec'] or sorok != elem['sorok']:
            raise Megall(f'{n}. tétel: a(z) {fej} doboz eltér a §-jegyzéktől')
    dsor = doboz_sorok(n, txt, blokk, ix, dob)
    rr = reszek(n)
    hoz, bizonytalan = felosztas_reszek(n, rr, blokk, ix, txt)
    cim = next(t['cim'] for t in kozos.tetelsor()['tetelek'] if t['sorszam'] == n)
    terv = reszcim_terv()
    nagybetus = []
    out = []
    for ri, r in enumerate(rr):
        us = [u for u in range(len(blokk)) if hoz[u] == ri]
        if not us:      # tartalom nélküli (hang nélküli) rész az új szerkezetben: a tétel szövege nem tartalmazza
            out.append({'partIndex': r['partIndex'], 'partCount': r['partCount'], 'noteId': r['noteId'], 'ttsId': r['ttsId'],
                        'title': terv.get(r['noteId'], r['title']), 'blokkok': None, 'html': '',
                        'sha256': hashlib.sha256(b'').hexdigest()})
            continue
        h = []
        if len(rr) == 1:
            h.append(f'<h1>{e(cim)}</h1>')
        lista = []

        def lezar():
            if lista:
                h.append('<ul>' + ''.join(f'<li>{e(x)}</li>' for x in lista) + '</ul>'); lista.clear()
        for u in us:
            t, v = blokk[u]
            if t == 'p' and FELSOROLASJEL.match(L[ix[u]].strip()):
                lista.append(v); continue
            lezar()
            if t in 'fa':
                cs, ng = cimsor(v, n)
                for w in ng:
                    if w not in nagybetus:
                        nagybetus.append(w)
                h.append(f'<h2>{e(cs)}</h2>' if t == 'f' else f'<h3>{e(cs)}</h3>')
            elif t == 'p':
                h.append(f'<p>{e(v)}</p>')
            elif t == 'd':
                h.append(html_doboz(dob[v][2], dsor[v]))
        lezar()
        x = ''.join(h)
        title = terv.get(r['noteId'], r['title'])
        out.append({'partIndex': r['partIndex'], 'partCount': r['partCount'], 'noteId': r['noteId'], 'ttsId': r['ttsId'],
                    'title': title, 'blokkok': [us[0], us[-1]], 'html': x,
                    'sha256': hashlib.sha256(x.encode('utf-8')).hexdigest()})
    return {'sema': 1, 'tetel': n, 'cim': cim, 'htmlContent': ''.join(r['html'] for r in out), 'reszek': out,
            'bizonytalan': bizonytalan, 'nagybetus': nagybetus}


def doboz_sorok(n, txt, blokk, ix, dob):
    """A doboz sorai a tétel szövegéből: a fejléc utáni nem üres sorok a következő blokkig (ezeket rendeli a
    tools/tetel_blokk.py a dobozhoz). A kozos.dobozok sorai ezek eleje; ha a tetel_blokk a doboz után még egy
    lezáró sort is a dobozhoz számít (a kozos.dobozok 300 karakternél hosszabb lezáró sort nem vesz fel), az is
    a dobozba kerül, hogy szöveg ne vesszen el (FIGYELEM-sor a kimeneten)."""
    L = txt.split('\n')
    hatar = ix[1:] + [len(L)]
    out = {}
    for u, (t, v) in enumerate(blokk):
        if t != 'd':
            continue
        sorok = [l.strip() for l in L[ix[u] + 1:hatar[u]] if l.strip()]
        k = dob[v][3]
        if sorok[:len(k)] != k:
            raise Megall(f'{n}. tétel: a(z) {dob[v][2]} doboz sorai eltérnek a kozos.dobozok soraitól')
        if len(sorok) > len(k):
            print(f'FIGYELEM: {n}. tétel {dob[v][2]}: a kozos.dobozok (és a §-jegyzék) {len(sorok) - len(k)} lezáró sort nem tartalmaz, '
                  f'a HTML-be bekerül: {sorok[len(k)][:70]}…')
        out[v] = sorok
    return out


def reszcim_terv():
    f = os.path.join(GY, 'tts', '_reszcim_terv.json')
    if not os.path.exists(f):
        return {}      # új tételsor: még nincs részcím-terv, a rész címe a jegyzeté
    d = json.load(open(f, encoding='utf-8'))
    return {m['noteId']: m['uj_cim'] for m in d['modositasok']}


# ---------- részcím-kimérés ----------
ROMAI_FO = re.compile(r'^([IVXL]+)\. ')


def reszcim_meres(n):
    """Részenként: a rész főpont-tartománya a blokkokból („(első-utolsó.)”), és ha a rész főpont közepén kezdődik,
    annak jelzése."""
    txt = kozos.tetel_szoveg(n)
    blokk, ix = tetel_blokk.blokkok_sorral(n)
    rr = reszek(n)
    hoz, biz = felosztas_reszek(n, rr, blokk, ix, txt)
    aktualis = None
    out = []
    for ri, r in enumerate(rr):
        us = [u for u in range(len(blokk)) if hoz[u] == ri]
        if not us:
            continue
        fok = []
        for u in range(us[-1] + 1):
            if blokk[u][0] == 'f':
                m = ROMAI_FO.match(blokk[u][1])
                if m:
                    aktualis = (m.group(1), blokk[u][1])
            if u >= us[0] and blokk[u][0] == 'f' and ROMAI_FO.match(blokk[u][1]):
                fok.append(aktualis)
        elozo_fo = any(blokk[u][0] == 'f' and ROMAI_FO.match(blokk[u][1]) for u in range(us[0]))
        kozep = blokk[us[0]][0] != 'f' and elozo_fo
        # a rész első főpontja: ha a rész főpont közepén kezdődik, a folytatott főpont
        elso = None
        for u in range(us[0], -1, -1):
            if blokk[u][0] == 'f' and ROMAI_FO.match(blokk[u][1]):
                elso = (ROMAI_FO.match(blokk[u][1]).group(1), blokk[u][1]); break
        if elso is None and fok:
            elso = fok[0]
        utolso = fok[-1] if fok else elso
        out.append({'noteId': r['noteId'], 'ttsId': r['ttsId'], 'title': r['title'], 'partIndex': r['partIndex'],
                    'elso': elso, 'utolso': utolso, 'kozep': kozep, 'elsoBlokk': blokk[us[0]]})
    return out, len(rr)


import collections as _col


_GYAK = {}
BETU = 'a-zA-ZÁÉÍÓÖŐÚÜŰáéíóöőúüű'


def _gyakorisag(n):
    """A tétel törzsszövegének (nem csupa nagybetűs sorainak) szóalakjai: kisbetűsített szó → {alak: db}; a mondat
    elején álló, csak kezdőbetűjében nagy alak nem számít (az nem mutatja a szó írásmódját)."""
    if n not in _GYAK:
        gyak = _col.defaultdict(_col.Counter)
        for l in [l.strip() for l in kozos.tetel_szoveg(n).split('\n')][1:]:
            if not l or l.upper() == l:
                continue
            elozo = '.'
            for t in re.findall(r'\S+', l):
                t2 = t.strip('.,;:()„”"–')
                mondatelso = elozo.endswith(('.', ':', '!', '?')) or elozo in ('–', '-')
                if t2 and not (mondatelso and t2[:1].isupper() and t2[1:] == t2[1:].lower()):
                    gyak[t2.casefold()][t2] += 1
                elozo = t
        _GYAK[n] = gyak
    return _GYAK[n]


def _osszes_gyak():
    if 'mind' not in _GYAK:
        g = _col.defaultdict(_col.Counter)
        for t in kozos.tetelsor()['tetelek']:
            for k, v in _gyakorisag(t['sorszam']).items():
                g[k].update(v)
        _GYAK['mind'] = g
    return _GYAK['mind']


def mondatkezdo(cim, n):
    """A csupa nagybetűs cím mondatkezdő írásmódja, gépileg (a központi chat döntése, 2026-11-18): minden szó a tétel
    törzsszövegében előforduló alakját kapja – ha van kisbetűs előfordulása, kisbetűs; különben a mondat belsejében
    látott alakja (Ptk., PK, KPJE, tulajdonnév); a római és az arab szám (a ponttal) változatlan. A törzsszövegben elő
    nem forduló szó kisbetűs, kivéve a rövidítés-gyanúsat (legfeljebb öt betű, pont nélkül): ennek alakját a tételsor
    többi tételének törzsszövege adja, ha ott előfordul; ha ott sem, nagybetűs marad, és a második visszatérési érték
    sorolja fel. Az első betűs szó nagy kezdőbetűs. Próba: a 7. és a 20. tétel kézzel írt
    részcímét betűre adja. Visszatér: (szöveg, [nagybetűsen hagyott szavak])."""
    gyak = _gyakorisag(n)
    out = []; elso = True; nagy = []
    for m in re.finditer(r'\S+', cim):
        w = m.group(0)
        pre = re.match(r'^[(„"]*', w).group(0)
        post = re.search(r'[.,;:)”"]*$', w[len(pre):]).group(0)
        core = w[len(pre):len(w) - len(post)]
        if not re.search('[' + BETU + ']', core) or (re.fullmatch(r'[IVXLC]+', core) and post.startswith('.')) \
                or re.fullmatch(r'[\d/.:–-]+[a-z]?', core):
            out.append(w); continue          # szám, római szám, jel
        mk = re.fullmatch('([' + BETU + ']{2,5})-([' + BETU + ']+)', core)
        if mk and core == core.upper() and len(re.findall('[AÁEÉIÍOÓÖŐUÚÜŰ]', mk.group(1))) <= 1:
            out.append(pre + mk.group(1) + '-' + mk.group(2).lower() + post); elso = False
            continue                         # ragozott betűszó („ÁSZF-EK” → „ÁSZF-ek”)
        c = gyak.get(core.casefold())
        if not c and len(re.sub('[^' + BETU + ']', '', core)) <= 5:
            # rövid szó, amely a tételben nem fordul elő: a tételsor többi tételének törzsszövege dönt
            c = _osszes_gyak().get(core.casefold())
        if c:
            kis = [k for k in c if k == k.lower()]
            rep = kis[0] if kis else c.most_common(1)[0][0]
            if rep == rep.upper() and len(re.findall('[AÁEÉIÍOÓÖŐUÚÜŰ]', rep)) > 1:
                rep = rep.lower()        # csak csupa nagybetűs előfordulás (kereszthivatkozás egy főcímre): közszó
        elif len(re.sub('[^' + BETU + ']', '', core)) <= 5 and not post.startswith('.') and core == core.upper() \
                and len(re.findall('[AÁEÉIÍOÓÖŐUÚÜŰ]', core)) <= 1:
            rep = core; nagy.append(core)    # legfeljebb egy magánhangzó: betűszó (ÁSZF, PK); a többi (DÍJAI) kisbetűs
        else:
            rep = core.lower()
        if elso:
            rep = rep[0].upper() + rep[1:]
        elso = False
        out.append(pre + rep + post)
    return ' '.join(out), nagy


ELOTAG = re.compile(r'^((?:[IVXL]+\.|\d+(?:\.\d+)*\.|[a-z]\))\s+)')


def cimsor(szoveg, n):
    """A fő- vagy alcím HTML-beli alakja: a sorszám-előtag („IV. ”, „3. ”, „a) ”) marad, a csupa nagybetűs szöveg
    mondatkezdő írást kap (mondatkezdo); a nem csupa nagybetűs cím változatlan. Visszatér: (alak, [nagybetűs szavak])."""
    m = ELOTAG.match(szoveg)
    elo = m.group(1) if m else ''
    tobbi = szoveg[len(elo):]
    if tobbi.upper() != tobbi or not re.search('[' + BETU + ']', tobbi):
        return szoveg, []
    x, nagy = mondatkezdo(tobbi, n)
    return elo + x, nagy


def _tartomany(a, b):
    return f'({a}-{b}.) ' if a != b else f'{a}. '


def _cim_bont(t):
    """(sorszám-előtag, tartomány-előtag, szöveg) a régi részcímből („2). (I-III.) 3. Az …”)."""
    m = re.match(r'^(\d+\)\.\s*)?(\(([IVXL]+)-([IVXL]+)\.\)\s*|([IVXL]+)\.\s+)?(.*)$', t)
    return m.group(1) or '', m.group(2) or '', m.group(6)


def reszcim_terv_gyart(ns):
    """A részcím-szabály gépi alkalmazása (Attila, 2026-11-15): „(első–utolsó főpont) + az első főpont fejezetcíme”.
    A tartomány a rész blokkjaiból (a hangdokumentum darabjainak tényleges tartalmából) kimérve; a szöveg marad, ha
    a régi cím szövege az első főpont címe (kisbetűsítve egyezik), különben az első főpont címe mondatkezdő írással
    (mondatkezdo). A főpont közepén (alpontnál) kezdődő rész: ha a régi cím az alpont címe, változatlan (a 12. tétel
    mintája), különben döntésre vár. Egyrészes tétel: változatlan."""
    mod, valt, dont = [], [], []
    for n in ns:
        mer, db = reszcim_meres(n)
        if db == 1:
            continue
        fo = [b[1] for b in tetel_blokk.blokkok(n) if b[0] == 'f' and ROMAI_FO.match(b[1])]
        fonev = {ROMAI_FO.match(c).group(1): c for c in fo}
        for m in mer:
            elo, tart, szoveg = _cim_bont(m['title'])
            a, b = m['elso'][0], m['utolso'][0]
            focim = re.sub(r'^[IVXL]+\.\s*', '', m['elso'][1])
            alap = {'tetel': n, 'ttsId': m['ttsId'], 'noteId': m['noteId']}
            if m['kozep']:
                eb = m['elsoBlokk'][1]
                if szoveg.casefold() == eb.casefold() or re.sub(r'^\(?[IVXL-]+\.\)?\s*', '', szoveg).casefold() == eb.casefold():
                    tov = [x for x in fo if fo.index(x) > fo.index(m['elso'][1]) and ROMAI_FO.match(x).group(1) in _kozott(fo, a, b)]
                    valt.append(dict(alap, cim=m['title'], megjegyzes=f'a rész a {a}. főpont {eb.split(".")[0]}. alpontjánál kezdődik, ezért alpontcímet visel'
                                     + (f'; a {", ".join(tov)} főcímet is tartalmazza' if tov else '') + '; a darabhatár nem változik (gépi kimérés, 2026-11-18)'))
                    continue
                # a rész alpontnál kezdődik, de a régi cím nem az alpont címe: a tartomány a darabok tényleges
                # tartalmából, a kezdő (folytatott) főponttal indul (a központi chat döntése, 2026-11-18)
                uj = _tartomany(a, b) + mondatkezdo(focim, n)[0]
                if uj != m['title']:
                    mod.append(dict(alap, regi_cim=m['title'], uj_cim=uj,
                                    indok=f'a rész a {a}. főpont „{eb}” alpontjánál kezdődik és a {b}. főpontig tart; a tartomány a darabok '
                                          f'tényleges tartalmából, a cím a {a}. főpont fejezetcíme (gépi kimérés, 2026-11-18)'))
                continue
            ok = []
            if szoveg.casefold().rstrip('.') == focim.casefold().rstrip('.'):
                uj_szoveg = szoveg
            else:
                uj_szoveg, _ = mondatkezdo(focim, n)
                ok.append(f'a cím az első főpont ({a}.) fejezetcíme; a régi szöveg („{szoveg}”) nem az')
            uj = _tartomany(a, b) + uj_szoveg      # a sorszám-előtag („4). ”) elmarad, mint az 1–21. tétel tervében
            if uj == m['title'] or (elo and uj == m['title'][len(elo):]):
                continue
            regi_t = re.match(r'^\(([IVXL]+)-([IVXL]+)\.\)', tart) or re.match(r'^([IVXL]+)\.', tart)
            if regi_t and (regi_t.group(1), regi_t.group(regi_t.lastindex)) != (a, b):
                ra, rb = regi_t.group(1), regi_t.group(regi_t.lastindex)
                tobb = [fonev[r] for r in _kozott(fo, a, b) if r not in _kozott(fo, ra, rb)]
                kev = [fonev[r] for r in _kozott(fo, ra, rb) if r in fonev and r not in _kozott(fo, a, b)]
                if tobb:
                    ok.insert(0, 'a rész a ' + ' és a '.join(tobb) + ' főpontot is tartalmazza')
                if kev:
                    ok.insert(0, 'a rész a ' + ' és a '.join(kev) + ' főpontot nem tartalmazza')
                if not tobb and not kev:
                    ok.insert(0, f'a rész a {a}–{b}. főpontot tartalmazza')
            mod.append(dict(alap, regi_cim=m['title'], uj_cim=uj, indok='; '.join(ok) + ' (gépi kimérés, 2026-11-18)'))
    return mod, valt, dont


def _kozott(fo, a, b):
    r = [ROMAI_FO.match(c).group(1) for c in fo]
    if a not in r or b not in r:
        return []
    return r[r.index(a):r.index(b) + 1]


def reszcim_terv_ir(ns):
    """A tts/_reszcim_terv.json kiegészítése a megadott tételekkel (a korábbi, kézi bejegyzések maradnak)."""
    ns = list(ns)
    f = os.path.join(GY, 'tts', '_reszcim_terv.json')
    d = json.load(open(f, encoding='utf-8'))
    d['modositasok'] = [m for m in d['modositasok'] if m['tetel'] not in ns]
    d['valtozatlan_megjegyzessel'] = [m for m in d['valtozatlan_megjegyzessel'] if m['tetel'] not in ns]
    mod, valt, dont = reszcim_terv_gyart(ns)
    d['modositasok'] += mod; d['valtozatlan_megjegyzessel'] += valt
    if dont:
        raise Megall('döntésre váró részcím: ' + json.dumps(dont, ensure_ascii=False))
    d.pop('dontesre_var', None)
    json.dump(d, open(f, 'w', encoding='utf-8'), ensure_ascii=False, indent=1)
    open(f, 'a', encoding='utf-8').write('\n')
    print(f'részcím-terv: {min(ns)}–{max(ns)}. tétel: {len(mod)} módosítás, {len(valt)} változatlan megjegyzéssel')


# ---------- főprogram ----------
def kiir(d):
    os.makedirs(KI, exist_ok=True)
    x = {k: v for k, v in d.items() if k not in ('bizonytalan', 'nagybetus')}
    json.dump(x, open(os.path.join(KI, f"{d['tetel']:02d}.json"), 'w', encoding='utf-8'), ensure_ascii=False, indent=1)


def index_ir():
    tetelek = []
    for f in sorted(glob.glob(os.path.join(KI, '[0-9][0-9].json'))):
        d = json.load(open(f, encoding='utf-8'))
        tetelek.append({'tetel': d['tetel'], 'cim': d['cim'], 'reszek': len(d['reszek']), 'karakter': len(d['htmlContent']),
                        'sha256': hashlib.sha256(d['htmlContent'].encode('utf-8')).hexdigest(),
                        'reszLista': [{'partIndex': r['partIndex'], 'noteId': r['noteId'], 'ttsId': r['ttsId'], 'title': r['title'],
                                       'blokkok': r['blokkok'], 'karakter': len(r['html']), 'sha256': r['sha256']} for r in d['reszek']]})
    osz = {'tetel': len(tetelek), 'resz': sum(t['reszek'] for t in tetelek), 'karakter': sum(t['karakter'] for t in tetelek)}
    kanon = json.dumps(tetelek, ensure_ascii=False, sort_keys=True, separators=(',', ':')).encode('utf-8')
    idx = {'sema': 1, 'osszesites': osz, 'tetelek': tetelek, 'sha256': hashlib.sha256(kanon).hexdigest()}
    json.dump(idx, open(os.path.join(KI, 'index.json'), 'w', encoding='utf-8'), ensure_ascii=False, indent=1)
    return idx


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('tetel', nargs='?', type=int)
    ap.add_argument('--mind', action='store_true')
    ap.add_argument('--reszcim', action='store_true')
    ap.add_argument('--reszcim-terv', action='store_true', help='a 22–85. tétel részcímeinek gépi kimérése a tts/_reszcim_terv.json-ba')
    a = ap.parse_args()
    if a.reszcim_terv:
        reszcim_terv_ir(range(22, 86)); return
    ns = [t['sorszam'] for t in kozos.tetelsor()['tetelek']] if (a.mind or (a.reszcim and not a.tetel)) else [a.tetel]
    if ns == [None]:
        ap.error('tételszám vagy --mind kell')
    if a.reszcim:
        for n in ns:
            mer, db = reszcim_meres(n)
            for m in mer:
                print(n, db, m['partIndex'], m['noteId'], m['elso'] and m['elso'][0], m['utolso'] and m['utolso'][0],
                      'KÖZÉP' if m['kozep'] else '', '|', m['title'])
        return
    hibak = []; kesz = []
    for n in ns:
        try:
            d = tetel_html(n)
        except Megall as x:
            hibak.append(str(x)); continue
        kesz.append(d)
    if hibak:
        print('MEGÁLLT – nem írtam fájlt:\n' + '\n'.join(hibak))
        sys.exit(1)
    for d in kesz:
        kiir(d)
        if d['nagybetus']:
            print(f"nagybetűs marad (a törzsszövegben nincs, rövidítés-gyanús): {d['tetel']}. tétel: {', '.join(d['nagybetus'])}")
        for b in d['bizonytalan']:
            print(f"bizonytalan: {d['tetel']}. tétel {b['blokk']}. blokk → {b['resz']}. rész ({b['ok']}): {b['szoveg']}")
        for r in d['reszek']:
            if not r['ttsId']:
                print(f"hang nélküli rész: {d['tetel']}. tétel {r['partIndex']}. rész ({r['noteId']}, {r['title']}): "
                      + (f"blokk {r['blokkok'][0]}–{r['blokkok'][1]}" if r['blokkok'] else 'TARTALOM NÉLKÜL (a tételben nincs a címével egyező címsor; HTML nem készült)'))
    idx = index_ir()
    o = idx['osszesites']
    hn = sum(1 for d in kesz for r in d['reszek'] if not r['ttsId'])
    print(f"jegyzet_html: {len(kesz)} tétel kiírva; összesen {o['tetel']} tétel, {o['resz']} rész, {o['karakter']} karakter; "
          f"bizonytalan blokk: {sum(len(d['bizonytalan']) for d in kesz)}" + (f"; hang nélküli rész: {hn}" if hn else ''))


if __name__ == '__main__':
    main()
