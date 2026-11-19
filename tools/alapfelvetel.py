#!/usr/bin/env python3
"""S1 – alapfelvétel: a hivatalos kiírás feldolgozása és a hivatkozások feloldása a korpuszban.

    python3 tools/alapfelvetel.py            # tetelsor/tetelsor.json + jelentesek/alapfelvetel.md
    python3 tools/alapfelvetel.py --tetel 7  # egy tétel előírt joganyaga a kimenetre (ellenőrzéshez)

Bemenet: tetelsor/beallitas.json, a kiírás szövege (pdftotext -layout), korpusz/, jegyzetek/manifest.json.
Csak olvas (a két kimeneti fájlt írja). Csak a standard könyvtárat használja; Python 3.9-től fut.
A kiindulás a publikált jegyzet (01_dontesek.md, 2026-11-19): a régi tételsor szövegét a program nem olvassa.
"""
import json, os, re, sys, unicodedata

GY = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
nfc = lambda s: unicodedata.normalize('NFC', s)
ROMAI = {'I': 1, 'V': 5, 'X': 10, 'L': 50, 'C': 100}


def be(ut):
    return open(os.path.join(GY, ut), encoding='utf-8').read()


def beallitas():
    return json.loads(be('tetelsor/beallitas.json'))


def korpusz_fajlok():
    return sorted(nfc(f) for f in os.listdir(os.path.join(GY, 'korpusz')) if f.endswith('.txt'))


def fajl_keres(kezdet, fajlok):
    t = [f for f in fajlok if f.startswith(nfc(kezdet))]
    return t[0] if len(t) == 1 else None


# ---------- a kiírás tételei ----------
def kiiras_tetelek(B):
    nyers = be(B['kiiras']['fajl'])
    sorok = [s.replace('\x0c', '') for s in nyers.split('\n')]
    sorok = [s for s in sorok if not re.fullmatch(r'\s*\d+\s*', s)]
    tetelek, csoport, akt = [], '', None
    for s in sorok:
        t = s.strip()
        if not t:
            continue
        m = re.match(r'^(\d{1,3})\.\s+(?=[A-ZÁÉÍÓÖŐÚÜŰ])(.*)$', t)
        if m and int(m.group(1)) == len(tetelek) + 1:
            akt = {'sorszam': int(m.group(1)), 'csoport': csoport, 'sorok': [m.group(2)]}
            tetelek.append(akt)
            continue
        # csoportfej: csupa nagybetűs sor (a tételek között)
        if tetelek and re.fullmatch(r'[A-ZÁÉÍÓÖŐÚÜŰ ,\-–]{6,}', t):
            csoport, akt = t, None
            continue
        if akt is not None:
            akt['sorok'].append(t)
    for t in tetelek:
        t['szoveg'] = ' '.join(' '.join(t.pop('sorok')).split())
    return tetelek


# ---------- hivatkozások ----------
def egyseg_index(fajl, egyseg):
    """A fájl szerkezeti egységeinek kezdősora: {'12': sor, '36/D': sor}, és a sorrend."""
    sorok = be('korpusz/' + fajl).split('\n')
    idx, rend = {}, []
    for i, s in enumerate(sorok):
        if egyseg == '§':
            m = re.match(r'^(\d+(?::\d+)?(?:/[A-Z])?)\. §', s)       # egyszerű („36/D”) és könyv:§ („6:105”) számozás
        elif egyseg == 'cikk':
            m = re.match(r'^(\d+)\. cikk\b', s, re.I)
        else:  # romaiCikk: az Alaptörvény betűs (A)–U)), római és arab számú cikkei
            m = re.match(r'^([IVXLC]+)\. cikk\s*\*?\s*$', s) or re.match(r'^(\d+)\. cikk\s*\*?\s*$', s) or re.match(r'^([A-Z]\))\s*cikk\s*\*?\s*$', s)
        if m and m.group(1) not in idx:
            idx[m.group(1)] = i
            rend.append(m.group(1))
    return sorok, idx, rend


_IDX = {}


def index(fajl, egyseg):
    if fajl not in _IDX:
        _IDX[fajl] = egyseg_index(fajl, egyseg)
    return _IDX[fajl]


def igazit(fajl, egyseg, tol, ig):
    """A tartomány végpontjai a korpuszban meglévő egységekre igazítva, vagy (None, None).
    A korpusz a teljes egészében hatályon kívül helyezett szakaszt nem tartalmazza: ilyenkor a végpont a
    tartományon belüli legközelebbi meglévő szakasz."""
    sorok, idx, rend = index(fajl, egyseg)
    if (tol not in idx or ig not in idx) and egyseg == '§' and tol != ig:
        def kulcs(x):
            m = re.match(r'(?:(\d+):)?(\d+)(?:/([A-Z]))?$', x)
            return (int(m.group(1) or 0), int(m.group(2)), m.group(3) or '') if m else None
        a, b = kulcs(tol), kulcs(ig)
        belul = [r for r in rend if a and b and kulcs(r) and a <= kulcs(r) <= b]
        if not belul:
            return None, None
        tol, ig = belul[0], belul[-1]
    if tol not in idx or ig not in idx or rend.index(ig) < rend.index(tol):
        return None, None
    return tol, ig


def tartomany_szoveg(fajl, egyseg, tol, ig):
    tol, ig = igazit(fajl, egyseg, tol, ig)
    if tol is None:
        return None
    sorok, idx, rend = index(fajl, egyseg)
    veg = rend.index(ig) + 1
    return '\n'.join(sorok[idx[tol]:(idx[rend[veg]] if veg < len(rend) else len(sorok))]).strip()


SZAM = r'\d+(?::\d+)?(?:/?[A-Z](?![a-záéíóöőúüűA-Z]))?'


def egysegek(szakasz, egyseg):
    """A szakasz §- vagy cikk-kifejezései: [(tol, ig)]. Kezeli: '8-11. §', '1. §-31. §', '197-198 §', '108-109.§', '79 -89. §'."""
    ki = []
    if egyseg == 'romaiCikk':
        # „XXVIII. cikk”, „E) és Q) cikk”, „25. és 27. cikk”, „38-39. cikk”, „I., II. cikk”
        for m in re.finditer(r'((?:(?:[IVXLC]+\.|\d+\.?|[A-Z]\))\s*(?:,|és|valamint|[-–])?\s*)+)cikk', szakasz):
            elemek = re.findall(r'([IVXLC]+(?=\.)|\d+|[A-Z]\))\s*\.?\s*([-–])?', m.group(1))
            i = 0
            while i < len(elemek):
                e, kot = elemek[i]
                if kot and i + 1 < len(elemek):
                    ki.append((e, elemek[i + 1][0])); i += 2
                else:
                    ki.append((e, e)); i += 1
        return ki
    jel = '§' if egyseg == '§' else 'cikk'
    minta = re.compile(r'(%s)\s*\.?\s*(?:%s)?\s*[-–]\s*(%s)\s*\.?\s*%s|(%s)\s*\.?\s*%s' % (SZAM, jel, SZAM, jel, SZAM, jel))
    def n(x):      # „291A” -> „291/A” (a kiírás olykor perjel nélkül írja)
        return re.sub(r'(?<=\d)(?=[A-Z]$)', '/', x)
    for m in minta.finditer(szakasz):
        ki.append((n(m.group(1)), n(m.group(2))) if m.group(1) else (n(m.group(3)), n(m.group(3))))
    return ki


def hatarozatok(szoveg, fajlok):
    """A bírói gyakorlat hivatkozásai: [(megnevezés, fájl vagy None)]."""
    ki = []

    def fel(nev, fajl):
        if (nev, fajl) not in ki:
            ki.append((nev, fajl))
    for m in re.finditer(r'PK-GK\.\s*(\d+)\.', szoveg):
        f = 'PK-GK_%s.txt' % m.group(1)
        fel('PK-GK %s.' % m.group(1), f if f in fajlok else None)
    # „PK 152., 154., 157. számú állásfoglalás”, „PK 13-15. számú állásfoglalás”, „PK 133., PK 134.”
    for m in re.finditer(r'(?<![-\w])PK\s+((?:\d+(?:-\d+)?\.?\s*,?\s*(?:PK\s+)?)+)', szoveg):
        for sz in re.finditer(r'(\d+)(?:-(\d+))?', m.group(1)):
            a, b = int(sz.group(1)), int(sz.group(2) or sz.group(1))
            for n in range(a, b + 1):
                f = 'PK_%d.txt' % n
                fel('PK %d.' % n, f if f in fajlok else None)
    for m in re.finditer(r'(?<!\w)MK\s+(\d+)\.', szoveg):
        fel('MK %s.' % m.group(1), fajl_keres('MK %s.' % m.group(1), fajlok))
    for m in re.finditer(r'(\d+)/(\d{4})\.?\s*(?:\([IVXL]+\.\s*\d+\.\)\s*)?'
                         r'(PK vélemény|KMK vélemény|Polgári jogegységi határozat|PJE határozat|'
                         r'Közigazgatási-\s*munkaügyi-\s*polgári jogegységi határozat|Közigazgatási-\s*polgári jogegységi határozat|'
                         r'IM rendelet)', szoveg):
        nev = '%s/%s. %s' % (m.group(1), m.group(2), ' '.join(m.group(3).split()))
        fel(nev, fajl_keres('%s%s_' % (m.group(1), m.group(2)), fajlok))
    return ki


_FK = None


def hatarozatok_altalanos(szoveg, fajlok):
    """Általános feloldás (beallitas.json: "hatarozatMod": "altalanos"): a kiírás minden nem §-os forrása
    (AB határozat, jogegységi határozat, kollégiumi vélemény, közzétett eseti döntés, rendelet, uniós jogi aktus,
    EUB-ügy, törvény teljes megnevezéssel) a korpuszfájlok nevéből és első sorából képzett kulcsokhoz kötve
    (korpusz_felmeres.py). Vissza: [(megnevezés, fájl vagy None)]. A beállítás "forrasok" mintái által lefedett
    törvényeket a hívó kiszűri."""
    global _FK
    import korpusz_felmeres as kf
    if _FK is None:
        _FK = {}
        for f in fajlok:
            elso = next((l for l in be('korpusz/' + f)[:3000].split('\n') if l.strip()), '')[:300]
            nev = re.sub(r'\.txt$', '', f)
            _FK[f] = kf.fajl_kulcsok(nev) | kf.fajl_kulcsok(elso) | {k for k, _ in kf.hivatkozasok(kf.lapit(nev.replace('_', '/')))} | {k for k, _ in kf.hivatkozasok(kf.lapit(elso))}
    ki, latott = [], set()
    for kulcs, nev in kf.hivatkozasok(kf.lapit(szoveg)):
        if kulcs[0] == 'nev':
            continue
        talalt = [fn for fn, ks in _FK.items() if kulcs in ks]
        if not talalt and kulcs[0] == 'szamev':
            talalt = [fn for fn, ks in _FK.items() if any(k[0] == 'szamev' and k[1:3] == kulcs[1:3] and k[3] == '?' for k in ks)]
        if not talalt and kulcs[0] == 'koll':
            talalt = []
        talalt = kf.valaszt(nev, talalt)
        egyedi = (kulcs, talalt[0] if talalt else None)
        if egyedi in latott:
            continue
        latott.add(egyedi)
        ki.append((nev, kulcs, talalt[0] if talalt else None))
    return ki


def felold(t, B, fajlok):
    sz = t['szoveg']
    jelolok = []
    for f in B['forrasok']:
        for minta in f['mintak']:
            for m in re.finditer(minta, sz):
                jelolok.append((m.start(), m.end(), f))
    jelolok.sort(key=lambda x: x[0])
    # a cím az első olyan forrásmegnevezésig tart, amelyet szerkezeti egység követ („Be. 1. §”); a mondatban álló
    # megnevezés („A Be. szerkezeti felépítése”) a cím része
    hivatkozo = [j[0] for j in jelolok if re.match(r'\s*(?:\d|[IVXLC]+\.|[A-Z]\)|Nemzeti|Alapvetés|Szabadság|Az állam)', sz[j[1]:j[1] + 14])]
    elso = min((hivatkozo or [j[0] for j in jelolok]) + [m.start() for m in re.finditer(r'\((?:PK|MK|\d+/\d{4})', sz)] + [len(sz)])
    t['cim'] = sz[:elso].strip(' ;,')
    hiv, gond = [], []
    for i, (a, b, f) in enumerate(jelolok):
        szakasz = sz[b:(jelolok[i + 1][0] if i + 1 < len(jelolok) else len(sz))]
        szakasz = re.sub(r'\([^)]*\)', ' ', szakasz)          # a zárójeles határozatlista nem §-hivatkozás
        fajl = f.get('fajl') or fajl_keres(f['fajlKezdet'], fajlok)
        if not fajl or nfc(fajl) not in fajlok:
            gond.append('%s: a korpuszban nincs fájl' % f['kod'])
            continue
        tart = egysegek(szakasz, f['egyseg'])
        if not tart:
            hiv.append({'forras': f['kod'], 'fajl': fajl, 'egyseg': f['egyseg'], 'tol': None, 'ig': None, 'karakter': len(be('korpusz/' + fajl))})
            continue
        for tol, ig in tart:
            szov = tartomany_szoveg(fajl, f['egyseg'], tol, ig)
            if szov is None:
                gond.append('%s %s–%s: a tartomány a korpusz-fájlban nem található' % (f['kod'], tol, ig))
                continue
            itol, iig = igazit(fajl, f['egyseg'], tol, ig)
            h = {'forras': f['kod'], 'fajl': fajl, 'egyseg': f['egyseg'], 'tol': itol, 'ig': iig, 'karakter': len(szov)}
            if (itol, iig) != (tol, ig):
                h['kiirasSzerint'] = '%s–%s' % (tol, ig)      # a kiírás végpontja a korpuszban nincs meg (hatályon kívül)
            hiv.append(h)
    if B.get('hatarozatMod') == 'altalanos':
        kotott = {nfc(f.get('fajl') or fajl_keres(f.get('fajlKezdet', '\x00'), fajlok) or '') for f in B['forrasok']}
        kihagy = set(B.get('kiirasElirasok', {}).get('kihagy', []))
        hl = []
        for nev, kulcs, fajl in hatarozatok_altalanos(sz, fajlok):
            if fajl and nfc(fajl) in kotott:
                continue          # a beállítás forrasok mintái már kezelik (törvény a teljes nevével)
            if fajl is None and (kulcs[0] == 'tv' or nev in kihagy):
                continue          # más törvény említése a szövegben, illetve a kiírás rögzített elírása
            fajl = B.get('kiirasElirasok', {}).get('megfeleltet', {}).get(nev, fajl)
            hl.append((nev, fajl))
    else:
        hl = hatarozatok(sz, fajlok)
    for nev, fajl in hl:
        if fajl:
            hiv.append({'forras': nev, 'fajl': fajl, 'egyseg': 'egesz', 'tol': None, 'ig': None, 'karakter': len(be('korpusz/' + fajl))})
        else:
            gond.append('%s: a korpuszban nincs fájl' % nev)
    # Tételszintű forrásmegfeleltetés (beallitas.json: tetelForras): ha a kiírás hatályon kívül helyezett vagy a
    # korpuszban másként szereplő forrást nevez meg, a tétel a megadott forrás(oka)t kapja; a megnevezett, de fel nem
    # oldható hivatkozás ettől nem hiány (Attila tételenkénti döntése alapján).
    for f in (B.get('tetelForras') or {}).get(str(t['sorszam']), []):
        fajl = f.get('fajl')
        if not fajl or nfc(fajl) not in fajlok:
            gond.append('%s: a tetelForras fájlja nincs a korpuszban' % f.get('kod'))
            continue
        if f.get('tol'):
            szov = tartomany_szoveg(fajl, f.get('egyseg', '§'), f['tol'], f.get('ig', f['tol']))
            if szov is None:
                gond.append('%s %s–%s: a tartomány a korpusz-fájlban nem található' % (f['kod'], f['tol'], f.get('ig', f['tol'])))
                continue
            hiv.append({'forras': f['kod'], 'fajl': fajl, 'egyseg': f.get('egyseg', '§'), 'tol': f['tol'], 'ig': f.get('ig', f['tol']), 'karakter': len(szov)})
        else:
            hiv.append({'forras': f['kod'], 'fajl': fajl, 'egyseg': 'egesz', 'tol': None, 'ig': None, 'karakter': len(be('korpusz/' + fajl))})
        gond = [g for g in gond if 'a korpuszban nincs fájl' not in g]
        t['forrasMegfeleltetes'] = f.get('indok', '')
    if not hiv and not gond:
        gond.append('a kiírásban nincs feloldható hivatkozás')
    t['hivatkozasok'], t['feloldatlan'] = hiv, gond
    t['eloirasSzoveg'] = t['szoveg']
    t['eloirasok'] = [{'forras': h['forras'], 'tol': h['tol'], 'ig': h['ig']} for h in hiv]
    return t


def forrasok_ir(B, fajlok, tetelek):
    """tetelsor/forrasok.json az A/1 sémában a beállítás forrasok tömbjéből (határozatfájl külön rekord nélkül)."""
    ki = []
    for f in B['forrasok']:
        korpusz = []
        fajl = f.get('fajl')
        if fajl and nfc(fajl) in fajlok:
            korpusz = [nfc(fajl)]
        elif f.get('fajlKezdet'):
            meg = fajl_keres(f['fajlKezdet'], fajlok)
            if meg:
                korpusz = [meg]
        ki.append({
            'kod': f['kod'],
            'nev': f['nev'],
            'tipus': f['tipus'] if 'tipus' in f else None,
            'jogszabalytar': f['jogszabalytar'] if 'jogszabalytar' in f else None,
            'korpusz': korpusz,
            'jogtar': f['jogtar'] if 'jogtar' in f else None,
            'jogkodex': f['jogkodex'] if 'jogkodex' in f else None,
        })
    # A bírói gyakorlat fájljai külön forrásrekordot kapnak (az A/1 sémájában is így szerepelnek: kod = a megnevezés),
    # hogy a tételek eloirasok[].forras mezője mindig feloldható legyen a forrasok.json-ban.
    latott = {f['kod'] for f in ki}
    for t in tetelek:
        for h in t['hivatkozasok']:
            if h['egyseg'] == 'egesz' and h['forras'] not in latott:
                latott.add(h['forras'])
                nev = h['forras']
                tipus = 'PK-GK' if nev.startswith('PK-GK') else 'PK' if nev.startswith('PK') else 'MK' if nev.startswith('MK') else 'AB határozat' if 'AB' in nev.split() else 'rendelet' if 'rendelet' in nev else 'iránymutatás'
                tf = next((f for lista in (B.get('tetelForras') or {}).values() for f in lista if f.get('kod') == nev), None)
                if tf:   # tételszintű megfeleltetéssel felvett jogszabály (nem iránymutatás)
                    ki.append({'kod': nev, 'nev': tf.get('nev', nev), 'tipus': tf.get('tipus', 'rendelet'), 'jogszabalytar': None,
                               'korpusz': [h['fajl']], 'jogtar': None, 'jogkodex': None})
                    continue
                ki.append({'kod': nev, 'nev': nev, 'tipus': tipus, 'jogszabalytar': None, 'korpusz': [h['fajl']], 'jogtar': None, 'jogkodex': None})
    json.dump({'forrasok': ki}, open(os.path.join(GY, 'tetelsor', 'forrasok.json'), 'w', encoding='utf-8'),
              ensure_ascii=False, indent=1)


def forras_nevek():
    B = beallitas()
    d = {f['kod']: f.get('nev', '') for f in B['forrasok']}
    for lista in (B.get('tetelForras') or {}).values():
        for f in lista:
            d[f['kod']] = f.get('nev', '')
    return d


def egyseg_fej(kod, tol, ig, egyseg, nev):
    jel = '§' if egyseg == '§' else 'cikk'
    return '### %s %s%s. %s%s' % (kod, tol, ('–' + ig) if ig != tol else '', jel, (' — ' + nev) if nev else '')


def eloirt_szoveg(t):
    """A tétel előírt joganyaga egy szövegben (az API-kötegek és az ellenőrzés számára)."""
    reszek = []
    nevek = forras_nevek()
    for h in t['hivatkozasok']:
        if h['egyseg'] == 'egesz' or h['tol'] is None:
            szov = be('korpusz/' + h['fajl']).strip()
            fej = '### %s (teljes szöveg: %s)%s' % (h['forras'], h['fajl'], (' — ' + nevek[h['forras']]) if nevek.get(h['forras']) else '')
        else:
            szov = tartomany_szoveg(h['fajl'], h['egyseg'], h['tol'], h['ig'])
            fej = egyseg_fej(h['forras'], h['tol'], h['ig'], h['egyseg'], nevek.get(h['forras'], ''))
        reszek.append(fej + '\n' + szov)
    return '\n\n'.join(reszek)


def main():
    B = beallitas()
    fajlok = korpusz_fajlok()
    tetelek = [felold(t, B, fajlok) for t in kiiras_tetelek(B)]
    hibak = []
    if len(tetelek) != B['tetelDb']:
        hibak.append('a kiírás tételszáma %d, a beállításé %d' % (len(tetelek), B['tetelDb']))
    man = json.loads(be('jegyzetek/manifest.json'))
    jegyz = {}
    for x in man['items']:
        jegyz.setdefault(x['sorszam'], []).append(x)
    if sorted(jegyz) != list(range(1, B['tetelDb'] + 1)):
        hibak.append('a jegyzetek sorszámai nem 1..%d' % B['tetelDb'])
    for t in tetelek:
        r = jegyz.get(t['sorszam'], [])
        t['jegyzetek'] = [{'id': x['id'], 'fajl': x['file'], 'cim': x['cim'], 'karakter': x['chars']} for x in r]
    if '--tetel' in sys.argv:
        n = int(sys.argv[sys.argv.index('--tetel') + 1])
        t = tetelek[n - 1]
        print(json.dumps({k: v for k, v in t.items() if k != 'szoveg'}, ensure_ascii=False, indent=1))
        print(eloirt_szoveg(t)[:3000])
        return
    atfogo = []
    for f in B['forrasok']:
        if f.get('atfogo'):
            fajl = f.get('fajl') or fajl_keres(f['fajlKezdet'], fajlok)
            atfogo.append({'forras': f['kod'], 'nev': f['nev'], 'fajl': fajl if fajl and nfc(fajl) in fajlok else None})
    ki = {'sema': 1, 'azon': B['azon'], 'cim': B['cim'], 'kiiras': B['kiiras'], 'atfogoIsmeret': atfogo,
          # az A/1 sémájának kulcsai (a közös eszközök ezeket olvassák: ellenorzes.py, hatalyok.py)
          'tetelsor': B.get('kategoria', B['cim']), 'ev': B['kiiras'].get('ev'), 'forras': B['kiiras'].get('pdf'),
          'altalanosEloiras': {'szoveg': 'Az alábbi jogszabályok átfogó ismerete szükséges (a felsorolás nem teljes körű)',
                               'forrasok': [a['forras'] for a in atfogo]},
          'tetelek': tetelek}
    json.dump(ki, open(os.path.join(GY, 'tetelsor', 'tetelsor.json'), 'w', encoding='utf-8'), ensure_ascii=False, indent=1)
    forrasok_ir(B, fajlok, tetelek)
    hasznalt = {h['fajl'] for t in tetelek for h in t['hivatkozasok']} | {a['fajl'] for a in atfogo if a['fajl']}
    nem_hasznalt = [f for f in fajlok if f not in hasznalt]
    gondok = [(t['sorszam'], g) for t in tetelek for g in t['feloldatlan']]
    L = ['# S1 – alapfelvétel: %s' % B['cim'], '',
         '- kiírás: %d tétel (%s); jegyzet: %d rész %d tételben' % (len(tetelek), B['kiiras']['fajl'], len(man['items']), len(jegyz)),
         '- feloldott hivatkozás: %d; feloldatlan: %d; a kiírás által nem hivatkozott korpusz-fájl: %d' % (sum(len(t['hivatkozasok']) for t in tetelek), len(gondok), len(nem_hasznalt)),
         '- alapfelvételi hiba: %d' % len(hibak), '']
    L += ['- HIBA: ' + h for h in hibak]
    L += ['', '## Feloldatlan hivatkozások (hiánylista a korpuszhoz)', '']
    L += ['- %d. tétel: %s' % g for g in gondok] or ['- nincs']
    L += ['', '## Átfogó ismeret (a kiírás elején)', '']
    L += ['- %s (%s): %s' % (a['forras'], a['nev'], a['fajl'] or 'NINCS A KORPUSZBAN') for a in atfogo]
    L += ['', '## A kiírás által nem hivatkozott korpusz-fájlok (tájékoztató)', '']
    L += ['- ' + f for f in nem_hasznalt] or ['- nincs']
    L += ['', '## Tételenként', '', '| # | Cím | Jegyzetrész | Jegyzet (karakter) | Előírt joganyag (karakter) | Feloldatlan |', '|---|---|---|---|---|---|']
    for t in tetelek:
        L.append('| %d | %s | %d | %d | %d | %d |' % (t['sorszam'], t['cim'][:70].replace('|', '/'), len(t['jegyzetek']), sum(j['karakter'] for j in t['jegyzetek']),
                                                    sum(h['karakter'] for h in t['hivatkozasok']), len(t['feloldatlan'])))
    open(os.path.join(GY, 'jelentesek', 'alapfelvetel.md'), 'w', encoding='utf-8').write('\n'.join(L) + '\n')
    print('alapfelvetel: tétel %d, feloldott %d, feloldatlan %d, hiba %d' % (len(tetelek), sum(len(t['hivatkozasok']) for t in tetelek), len(gondok), len(hibak)))
    sys.exit(1 if hibak else 0)


if __name__ == '__main__':
    main()
