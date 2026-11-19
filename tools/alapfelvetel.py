#!/usr/bin/env python3
"""S1 – alapfelvétel: a hivatalos kiírás feldolgozása és a hivatkozások feloldása a korpuszban.

    python3 tools/alapfelvetel.py            # tetelsor/tetelsor.json + jelentesek/alapfelvetel.md
    python3 tools/alapfelvetel.py --tetel 7  # egy tétel előírt joganyaga a kimenetre (ellenőrzéshez)

Bemenet: tetelsor/beallitas.json, a kiírás szövege (pdftotext -layout), korpusz/, jegyzetek/manifest.json.
Csak olvas (a két kimeneti fájlt írja). Csak a standard könyvtárat használja; Python 3.9-től fut.
A kiindulás a publikált jegyzet (01_dontesek.md, 2026-11-19): a régi tételsor szövegét a program nem olvassa.

Alapelv (KE-1, 2026-11-19): néma kihagyás nincs. Ami a kiírásban forráshivatkozásnak látszik, az vagy feloldott, vagy
feloldatlan, vagy név szerint kihagyott. A maradékvizsgálat (maradek) a fel nem használt szövegrész hivatkozásgyanús
elemeit „fel nem ismert hivatkozás: …” sorként a tétel feloldatlan listájára teszi.
A beállítás nem kötelező kulcsai: kiirasElirasok.kihagy (megnevezések, amelyeket az általános ág kihagy),
kiirasElirasok.megfeleltet (megnevezés -> fájl), kiirasElirasok.nemHivatkozas (szövegrészek, amelyek nem hivatkozások:
a maradékvizsgálat hamis jelzése ellen), kizartJegyzetSorszam (a kiírásban nem szereplő jegyzet-sorszámok),
tetelForras (tételszintű forrásmegfeleltetés). A tételcsoport bevezetőjének forrásai a tetelsor.json csoportEloiras
kulcsába és a csoport tételeinek hivatkozásai közé („csoport”: true) kerülnek; az eloirt_szoveg a teljes fájlként
előírt forrást (a csoportszintűt is) legfeljebb 120 000 karakterig szó szerint, e fölött csak megnevezéssel teszi a
kérésbe; az átfogó ismeretet (atfogo) teljes fájlként soha.
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
CSOPORTFEJ = re.compile(r'[A-ZÁÉÍÓÖŐÚÜŰ ,\-–]{6,}')


def kiiras_reszek(nyers):
    """A kiírás szövegének tagolása (egyetlen szabály; a korpusz_felmeres.py is ezt használja).
    Vissza: (tételek, csoportok, bevezető). Tétel: {'sorszam', 'csoport', 'szoveg'}; csoportok: {csoportfej: a fej és a
    csoport első tétele közötti szöveg (a csoport közös előírása, pl. „A fejezetnél következő jogszabályok … ismerete
    szükséges”)}; bevezető: az első tétel előtti szöveg (az egész tételsor átfogó előírása – a beállítás atfogo kulcsa)."""
    sorok = [s.replace('\x0c', '') for s in nyers.split('\n')]
    sorok = [s for s in sorok if not re.fullmatch(r'\s*\d+\s*', s)]
    tetelek, csoportok, elotte, csoport, akt, bev = [], {}, [], '', None, None
    for s in sorok:
        t = s.strip()
        if not t:
            continue
        m = re.match(r'^(\d{1,3})\.\s+(?=[A-ZÁÉÍÓÖŐÚÜŰ])(.*)$', t)
        if m and int(m.group(1)) == len(tetelek) + 1:
            akt = {'sorszam': int(m.group(1)), 'csoport': csoport, 'sorok': [m.group(2)]}
            tetelek.append(akt)
            bev = None
            continue
        # csoportfej: csupa nagybetűs sor (a tételek között)
        if tetelek and CSOPORTFEJ.fullmatch(t):
            csoport, akt = t, None
            bev = csoportok.setdefault(t, [])
            continue
        if akt is not None:
            akt['sorok'].append(t)
        elif bev is not None:
            bev.append(t)
        elif not tetelek:
            elotte.append(t)
    for t in tetelek:
        t['szoveg'] = ' '.join(' '.join(t.pop('sorok')).split())
    return tetelek, {k: ' '.join(' '.join(v).split()) for k, v in csoportok.items()}, ' '.join(' '.join(elotte).split())


def kiiras_tetelek(B):
    return kiiras_reszek(be(B['kiiras']['fajl']))[0]


# ---------- hivatkozások ----------
def egyseg_sor(s, egyseg):
    """A korpuszsor egységfeje-e (match, group(1) = az egység azonosítója), vagy None. EGYETLEN szabály: az alapfelvétel
    indexe, a kozos.jogszabaly_paragrafusok (ellenorzes, doboz_teljesseg, kontroll) és az s5/doboz_javit is ezt használja.
    - '§': egyszerű („36/D”) és könyv:§ („6:105”) számozás – forrásonként, nem tételsoronként;
    - 'cikk': „12. cikk”, „6. Cikk – …” (kis- és nagybetű);
    - 'romaiCikk': az Alaptörvény betűs (A)–U)), római és arab számú cikkei (a sor csak a cikkfej)."""
    if egyseg == '§':
        return re.match(r'^(\d+(?::\d+)?(?:/[A-Z])?)\. §', s)
    if egyseg == 'cikk':
        return re.match(r'^(\d+)\. cikk\b', s, re.I)
    return re.match(r'^([IVXLC]+)\. cikk\s*\*?\s*$', s) or re.match(r'^(\d+)\. cikk\s*\*?\s*$', s) or re.match(r'^([A-Z]\))\s*cikk\s*\*?\s*$', s)


def egyseg_index(fajl, egyseg):
    """A fájl szerkezeti egységeinek kezdősora: {'12': sor, '36/D': sor}, és a sorrend."""
    sorok = be('korpusz/' + fajl).split('\n')
    idx, rend = {}, []
    for i, s in enumerate(sorok):
        m = egyseg_sor(s, egyseg)
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
        if a and b and a[0] != b[0]:
            return None, None       # könyvhatáron átnyúló tartomány: nem találgatunk
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
_ROMAI_ELEM = r'(?:[A-Z]\)|[IVXLC]+(?![\w)])|\d+)'


def hossztarto(szakasz):
    """A kiírás elírásainak és zárójeleinek semlegesítése HOSSZTARTÓ módon (a maradékvizsgálat a helyekre épül):
    - „3: 322. §” -> „3:322 . §” (szóköz a kettőspont után);
    - „42./G. §” -> „42/G . §” (pont a betű előtt);
    - a LEZÁRT zárójeles rész (belülről kifelé) szóközzé válik: a zárójeles határozatlista, bekezdésszám nem §-hivatkozás;
      a lezáratlan zárójel („39. cikk (átláthatóság, 41-44. cikk (…)”) nem nyel el hivatkozást."""
    szakasz = szakasz.replace('−', '-')                       # „200−202. §” (mínuszjel a kötőjel helyén)
    szakasz = re.sub(r'(\d+):(\s+)(\d+)', lambda m: m.group(1) + ':' + m.group(3) + m.group(2), szakasz)
    szakasz = re.sub(r'(\d+)\./([A-Z])(?![a-záéíóöőúüűA-Z])', r'\1/\2 ', szakasz)
    while True:
        uj = re.sub(r'\([^()]*\)', lambda m: ' ' * len(m.group(0)), szakasz)
        if uj == szakasz:
            return szakasz
        szakasz = uj


def egysegek(szakasz, egyseg, helyek=None):
    """A szakasz §- vagy cikk-kifejezései: [(tol, ig)]. Kezeli: '8-11. §', '1. §-31. §', '197-198 §', '108-109.§',
    '79 -89. §', '6:15-17. §' (a végpont a kezdőpont könyvét örökli), '42./G. §', felsorolás közös egységjellel
    ('5; 6-22.§', '7. és 8. §'), római tartomány ('XX-XXI. cikk', 'I-II. cikk'). Ha a helyek lista adott, a felismert
    kifejezések (kezdet, vég) helyét is beleírja (a szakasz koordinátáiban)."""
    ki = []
    szakasz = hossztarto(szakasz)
    if egyseg == 'romaiCikk':
        # „XXVIII. cikk”, „E) és Q) cikk”, „25. és 27. cikk”, „38-39. cikk”, „I., II. cikk”, „XX-XXI. cikk”, „V-XIII. cikk”
        for m in re.finditer(r'(?<![\w)])((?:%s\s*\.?\s*(?:,|és|valamint|[-–])?\s*)+)cikk' % _ROMAI_ELEM, szakasz):
            elemek = re.findall(r'(%s)\s*\.?\s*([-–])?' % _ROMAI_ELEM, m.group(1))
            i = 0
            while i < len(elemek):
                e, kot = elemek[i]
                if kot and i + 1 < len(elemek):
                    ki.append((e, elemek[i + 1][0])); i += 2
                else:
                    ki.append((e, e)); i += 1
            if helyek is not None:
                helyek.append((m.start(), m.end()))
        return ki
    jel = '§' if egyseg == '§' else '[Cc]ikk'
    veg = r'%s|[A-Z](?![\w])' % SZAM          # „352/A-B. §”, „86/A-C. §”: a végpont csak a betű
    elem = r'(%s)(?:\s*\.?\s*(?:%s)?\s*[-–]\s*(%s))?' % (SZAM, jel, veg)
    elem_nc = r'(?:%s)(?:\s*\.?\s*(?:%s)?\s*[-–]\s*(?:%s))?' % (SZAM, jel, veg)
    lista = re.compile(r'(?<![\d:/])(%s(?:\s*\.?\s*(?:,|;|és|valamint|illetve)\s*%s)*)\s*\.{0,2}\s*%s' % (elem_nc, elem_nc, jel))

    def n(x):      # „291A” -> „291/A” (a kiírás olykor perjel nélkül írja)
        return re.sub(r'(?<=\d)(?=[A-Z]$)', '/', x)
    for ml in lista.finditer(szakasz):
        for m in re.finditer(elem, ml.group(1)):
            if m.group(2):
                a, b = n(m.group(1)), n(m.group(2))
                if re.fullmatch(r'[A-Z]', b):
                    b = re.sub(r'/?[A-Z]$', '', a) + '/' + b
                if ':' in b and ':' not in a:
                    a = b.split(':')[0] + ':' + a          # „3:322–3:323”, ha a könyvszám csak a végponton áll
                elif ':' in a and ':' not in b:
                    b = a.split(':')[0] + ':' + b          # „6:15-17. §” = 6:15–6:17
                ki.append((a, b))
            else:
                ki.append((n(m.group(1)), n(m.group(1))))
        if helyek is not None:
            helyek.append((ml.start(), ml.end()))
    return ki


RESZ_SORSZAM = {'első': 1, 'második': 2, 'harmadik': 3, 'negyedik': 4, 'ötödik': 5, 'hatodik': 6, 'hetedik': 7, 'nyolcadik': 8,
                'kilencedik': 9, 'tizedik': 10, 'tizenegyedik': 11, 'tizenkettedik': 12, 'tizenharmadik': 13, 'tizennegyedik': 14,
                'tizenötödik': 15, 'tizenhatodik': 16, 'általános': 'Á', 'különös': 'K'}
_ROMAI_LISTA = r'((?:[IVXLC]+\.?(?:\s*[-–]\s*[IVXLC]+\.?)?\s*(?:,|és|valamint)?\s*)+)'
_SZAM_LISTA = r'((?:\d+(?:/[A-Z])?\.?(?:\s*[-–]\s*\d+(?:/[A-Z])?\.?)?\s*(?:,|és|valamint)?\s*)+)'
_SZINT = {'resz': 1, 'cim': 2, 'fejezet': 3, 'alcim': 4}
_SZERK = {}


def romai(x):
    v = [ROMAI[c] for c in x]
    return sum(-a if i + 1 < len(v) and a < v[i + 1] else a for i, a in enumerate(v))


def szerkezet_index(fajl):
    """A korpuszfájl szerkezeti címsorai: [(sor, szint, azonosító)] – rész („ELSŐ RÉSZ”, „ÁLTALÁNOS RÉSZ”), cím
    („II. CÍM”), fejezet („IV. FEJEZET”, „IV. Fejezet”), számozott alcím („32. A Kúria elnöke”: szám után nagybetűs,
    záró írásjel nélküli sor, amelyet egység vagy újabb címsor követ)."""
    if fajl in _SZERK:
        return _SZERK[fajl]
    sorok = be('korpusz/' + fajl).split('\n')
    ki, utolso_alcim = [], 0
    egys = re.compile(r'^\s*(?:\d+(?::\d+)?(?:/[A-Z])?\.\s*§|\d+\.\s*[Cc]ikk|[IVXLC]+\.\s*[Cc]ikk)')
    for i, s in enumerate(sorok):
        t = s.strip().replace(' ', ' ')
        m = re.match(r'^(\w+)\s+R[ÉE]SZ\b', t, re.I)
        if m and m.group(1).lower() in RESZ_SORSZAM and (t.split(' -')[0].isupper() or 'rész' in t.lower()):
            ki.append((i, 'resz', RESZ_SORSZAM[m.group(1).lower()])); continue
        m = re.match(r'^([IVXLC]+)(?:/[A-Z])?\.\s*\*?\s*(FEJEZET|Fejezet|fejezet)\b', t)
        if m:
            ki.append((i, 'fejezet', romai(m.group(1)))); continue
        m = re.match(r'^([IVXLC]+)\.\s*CÍM\b', t)
        if m:
            ki.append((i, 'cim', romai(m.group(1)))); continue
        m = re.match(r'^(\d{1,3})\.\s+(?!§)[A-ZÁÉÍÓÖŐÚÜŰ]', t)
        if m and len(t) < 250 and not re.search(r'[.;:,]$', t) and int(m.group(1)) > utolso_alcim:
            kov = next((x.strip() for x in sorok[i + 1:i + 6] if x.strip()), '')
            if egys.match(kov) or re.match(r'^\d{1,3}\.\s+[A-ZÁÉÍÓÖŐÚÜŰ]', kov) and not re.search(r'[.;:,]$', kov) or re.match(r'^\[', kov):
                ki.append((i, 'alcim', int(m.group(1)))); utolso_alcim = int(m.group(1))
    _SZERK[fajl] = ki
    return ki


def szerkezet_tartomany(fajl, szakasz, egyseg):
    """A szakasz rész-, cím-, fejezet- és alcímhivatkozásai („II-VI. fejezet”, „I-IV. és VIII-IX. Fejezet”, „Harmadik rész”,
    „1-2., 6-12. és 35. alcím”) a korpuszfájl címsorai alapján: [(első egység, utolsó egység, megnevezés, kezdet, vég)];
    ha a címsor nincs meg, első/utolsó None. A közvetlenül egység előtt álló fejezet („Kbt. II. fejezet 3. § a) pont”)
    csak helymegjelölés: tartományt nem ad (a § maga a hivatkozás), de a helyét visszaadja (None, None, None, …)."""
    szakasz = hossztarto(szakasz)
    talalat = []
    for m in re.finditer(r'(?<![\w.])' + _ROMAI_LISTA + r'(?:[Ff]ejezet|FEJEZET)(?:e|ei|ében|ének|eiben)?\b', szakasz):
        talalat.append(('fejezet', m))
    for m in re.finditer(r'(?<![\w.])' + _ROMAI_LISTA + r'(?:CÍM|[Cc]ím)(?:e|ei)?\b(?!\w)', szakasz):
        if not re.search(r'[a-záéíóöőúüű]', szakasz[max(0, m.start() - 2):m.start()]):
            talalat.append(('cim', m))
    for m in re.finditer(r'(?<![\w.:/])' + _SZAM_LISTA + r'alcím(?:e|ei|ben)?\b', szakasz):
        talalat.append(('alcim', m))
    for m in re.finditer(r'\b(%s)\s+[Rr]ész(?:e|ei|ében)?\b' % '|'.join(k.capitalize() + '|' + k for k in RESZ_SORSZAM), szakasz):
        talalat.append(('resz', m))
    if not talalat:
        return []
    cimek = szerkezet_index(fajl)
    sorok, idx, rend = index(fajl, egyseg)
    egys_sor = sorted((i, u) for u, i in idx.items())
    ki = []
    for szint, m in sorted(talalat, key=lambda x: x[1].start()):
        if szint in ('fejezet', 'cim') and re.match(r'\s*(?:\d+(?::\d+)?(?:/[A-Z])?\.?\s*(?:§|-|–|[Cc]ikk)|\d+\.\s*§)', szakasz[m.end():m.end() + 14]):
            ki.append((None, None, None, m.start(), m.end()))     # helymegjelölés („II. fejezet 3. §”)
            continue
        nevek = {'resz': 'rész', 'fejezet': 'fejezet', 'cim': 'cím', 'alcim': 'alcím'}
        if szint == 'resz':
            v = RESZ_SORSZAM[m.group(1).lower()]
            elemek = [(v, v, m.group(1).lower(), m.group(1).lower())]
        else:
            elemek = []
            for x in re.finditer(r'([IVXLC]+|\d+(?:/[A-Z])?)\.?(?:\s*[-–]\s*([IVXLC]+|\d+(?:/[A-Z])?))?', m.group(1)):
                a_, b_ = x.group(1), x.group(2) or x.group(1)
                f = (lambda v: int(re.sub(r'\D', '', v))) if szint == 'alcim' else romai
                elemek.append((f(a_), f(b_), a_, b_))
        for tol, ig, ts, igs in elemek:
            nev = ('%s rész' % ts) if szint == 'resz' else '%s%s. %s' % (ts, ('–' + igs) if igs != ts else '', nevek[szint])
            # a tartomány a korpuszban meglévő címsorokra igazodik (a teljes egészében hatályon kívül helyezett fejezet
            # címsora hiányozhat); a vége az utolsó tartománybeli címsor utáni első azonos vagy magasabb szintű címsor
            benne_c = [c for c in cimek if c[1] == szint and isinstance(c[2], type(tol)) and tol <= c[2] <= ig]
            kezd = benne_c[0] if benne_c else None
            utol = benne_c[-1] if benne_c else None
            if not kezd:
                ki.append((None, None, nev, m.start(), m.end()))
                continue
            veg = next((c[0] for c in cimek if c[0] > utol[0] and _SZINT[c[1]] <= _SZINT[szint]), len(sorok))
            benne = [u for i, u in egys_sor if kezd[0] < i < veg]
            ki.append((benne[0] if benne else None, benne[-1] if benne else None, nev, m.start(), m.end()))
    return ki


def fejezet_tartomany(fajl, szakasz):
    """Visszafelé kompatibilis felület: [(első §, utolsó §, megnevezés)] a feloldható szerkezeti hivatkozásokra."""
    return [(a, b, n) for a, b, n, _, _ in szerkezet_tartomany(fajl, szakasz, '§') if a]


def hatarozatok(szoveg, fajlok, helyek=None):
    """A bírói gyakorlat hivatkozásai: [(megnevezés, fájl vagy None)]. Ha a helyek lista adott, a felismert
    megnevezések (kezdet, vég) helyét is beleírja."""
    ki = []
    helyek = [] if helyek is None else helyek

    def fel(nev, fajl):
        if (nev, fajl) not in ki:
            ki.append((nev, fajl))
    for m in re.finditer(r'PK-GK\.\s*(\d+)\.', szoveg):
        helyek.append(m.span())
        f = 'PK-GK_%s.txt' % m.group(1)
        fel('PK-GK %s.' % m.group(1), f if f in fajlok else None)
    # „PK 152., 154., 157. számú állásfoglalás”, „PK 13-15. számú állásfoglalás”, „PK 133., PK 134.”
    for m in re.finditer(r'(?<![-\w])PK\s+((?:\d+(?:-\d+)?\.?\s*,?\s*(?:PK\s+)?)+)', szoveg):
        helyek.append(m.span())
        for sz in re.finditer(r'(\d+)(?:-(\d+))?', m.group(1)):
            a, b = int(sz.group(1)), int(sz.group(2) or sz.group(1))
            for n in range(a, b + 1):
                f = 'PK_%d.txt' % n
                fel('PK %d.' % n, f if f in fajlok else None)
    for m in re.finditer(r'(?<!\w)MK\s+(\d+)\.', szoveg):
        helyek.append(m.span())
        fel('MK %s.' % m.group(1), fajl_keres('MK %s.' % m.group(1), fajlok))
    for m in re.finditer(r'(\d+)/(\d{4})\.?\s*(?:\([IVXL]+\.\s*\d+\.\)\s*)?'
                         r'(PK vélemény|KMK vélemény|Polgári jogegységi határozat|PJE határozat|'
                         r'Közigazgatási-\s*munkaügyi-\s*polgári jogegységi határozat|Közigazgatási-\s*polgári jogegységi határozat|'
                         r'IM rendelet)', szoveg):
        helyek.append(m.span())
        nev = '%s/%s. %s' % (m.group(1), m.group(2), ' '.join(m.group(3).split()))
        fel(nev, fajl_keres('%s%s_' % (m.group(1), m.group(2)), fajlok))
    return ki


_FK = None
_ELSO = {}


def hatarozatok_altalanos(szoveg, fajlok):
    """Általános feloldás (beallitas.json: "hatarozatMod": "altalanos"): a kiírás minden nem §-os forrása
    (AB határozat, jogegységi határozat, kollégiumi vélemény, közzétett eseti döntés, rendelet, uniós jogi aktus,
    EUB-ügy és -vélemény, kúriai ügyszám, törvény teljes megnevezéssel) a korpuszfájlok nevéből és első sorából képzett
    kulcsokhoz kötve (korpusz_felmeres.py). Vissza: [(megnevezés, kulcs, fájl vagy None, [minden jelölt fájl], kezdet, vég)]
    – a hely a szöveg kf.lapit() alakjában értendő (ez a tétel szövegével azonos hosszú). A beállítás "forrasok" mintái
    által lefedett fájlokat a hívó kiszűri (ha bármelyik jelölt ilyen)."""
    global _FK
    import korpusz_felmeres as kf
    if _FK is None:
        _FK = {}
        for f in fajlok:
            elso = next((l for l in be('korpusz/' + f)[:3000].split('\n') if l.strip()), '')[:300]
            _ELSO[f] = elso
            nev = re.sub(r'\.txt$', '', f)
            _FK[f] = kf.fajl_kulcsok(nev) | kf.fajl_kulcsok(elso) | {k for k, _ in kf.hivatkozasok(kf.lapit(nev.replace('_', '/')))} | {k for k, _ in kf.hivatkozasok(kf.lapit(elso))}
    # azonos megnevezés és hely több kulccsal (tartományos EUB-ügyszám): egy hivatkozás, a jelöltek uniójával
    csop = {}
    for kulcs, nev, a, b in kf.hivatkozasok_hely(kf.lapit(szoveg)):
        if kulcs[0] == 'nev':
            continue
        csop.setdefault((nev, a, b), []).append(kulcs)
    ki, latott = [], set()
    for (nev, a, b), kulcsok in sorted(csop.items(), key=lambda x: x[0][1]):
        talalt = []
        for kulcs in kulcsok:
            t = [fn for fn, ks in _FK.items() if kulcs in ks]
            if not t and kulcs[0] == 'szamev':
                t = [fn for fn, ks in _FK.items() if any(k[0] == 'szamev' and k[1:3] == kulcs[1:3] and k[3] == '?' for k in ks)]
            talalt += [f for f in kf.valaszt(nev, t, kulcs, _ELSO) if f not in talalt]
        talalt = kf.valaszt(nev, talalt, kulcsok[0], _ELSO) if len(kulcsok) == 1 else talalt
        fajl = talalt[0] if talalt else None
        egyedi = fajl if fajl else (kulcsok[0], None)
        if egyedi in latott:
            ki.append((nev, kulcsok[0], None, talalt, a, b, 'ismetles'))
            continue
        latott.add(egyedi)
        ki.append((nev, kulcsok[0], fajl, talalt, a, b, ''))
    return ki


# ---------- maradékvizsgálat ----------
# A feloldás által fel nem használt szövegrészben ezek az elemek hivatkozásgyanúsak (szám, évszám, §, cikk, ügyszám,
# névvel jelölt ügy); a kulcsszó (határozat, rendelet …) csak „… szóló” után, a címen és a zárójeles leíráson kívül.
# A római számú szerkezeti hivatkozás („Kódexe I- III. rész”, „II. fejezet”, „IV. cím”) is gyanús: ha nem forrás-
# jelölő után áll (szerkezet_tartomany), feloldatlanként jelenik meg, nem marad ki némán.
GYANUS = re.compile(r'\d|§|\b[Cc]ikk|\b[CT]-\s?\d|\b[A-ZÁÉÍÓÖŐÚÜŰ][\w]+[- ]ügy(?:ek)?\b'
                    r'|(?<![\w.])[IVXLC]+\.?\s*(?:[-–]\s*[IVXLC]+\.?\s*)?(?:[Rr]ész|RÉSZ|[Ff]ejezet|FEJEZET|[Cc]ím|CÍM)')
GYANUS_SZO = re.compile(r'\bszóló\s+(?:\w+\s+){0,2}(?:törvény|rendelet|irányelv|határozat|vélemény|ítélet|végzés|egyezmény)\w*', re.I)
# a hivatkozás minősítői (önmagukban nem hivatkozások): bekezdés, pont, alpont, mondat, indokolási pont, dátum
_HONAP = r'(?:január|február|március|április|május|június|július|augusztus|szeptember|október|november|december)'
MINOSITO = [re.compile(x, re.I) for x in (
    r'\(\s*\d+[a-z]?\s*[-–]\s*(?=\()',                                           # lezáratlan bekezdéstartomány: „(1-(5)”
    r'„[^”]{0,80}”',                                                                # idézett leírás: („egyházi 1%”)
    r'\bIndokolás(?:a|ának|ában)?\s*(?:[IVXLC]+\.?(?:\s*\d+\.?)*)?(?:\s*[-–]\s*[IVXLC]+\.?(?:\s*\d+\.?)*)?',
    r'\[\s*\d+\s*\](?:\s*[-–]\s*\[\s*\d+\s*\])?',
    r'\(\s*\d+[a-z]?\s*\)',
    r'(?<![\w/])(?:\d+(?:/[A-Z])?[a-z]?\.?(?:\s*[-–−]\s*\d+[a-z]?\.?)?\s*(?:,|és|valamint|illetve|vagy)?\s*(?:az?\s+)?)+'
    r'(?:(?:al)?(?:pont|mondat|fordulat|bekezdés|bek\b|albekezdés|preambulumbekezdés|francia\s*bekezdés)\w*\.?|p\.)',
    r'(?<!\w)[a-z]{1,2}\)(?:\s*[-–]\s*[a-z]{1,2}\))?',
    r'\b(?:\d{4}\.\s*)?' + _HONAP + r'\s*\d{1,2}(?:\.|-[a-záéíóöőúüű]+)?',
    r'\b\d{4}\.\s*(?:évi\s+)?[IVXLCDM]+\.\s*számú\b',
    r'(?<![\w/])[IVXLC]+/\d+\.?(?:\s*(?:,|és)\s*[IVXLC]+/\d+\.?)*',               # véleménypont: „56. BK vélemény III/5. és III/12.”
    r'(?<![\w.])[IVXLC]+\.\s*\d+(?:\.\d+)*\.?(?:\s*[-–]\s*\d+\.?)?(?![\w.]*\s*(?:§|[Cc]ikk))',   # indokolási pont: „III. 1-5.”
    r'\b(?:ECLI:)?EU:[CTF]:\d{4}:\d+\b',                                             # ECLI-azonosító
)]


def maradek(sz, hasznalt, cim_veg, kihagy=()):
    """A feloldás által fel nem használt szövegrész hivatkozásgyanús elemei: ['fel nem ismert hivatkozás: …'].
    hasznalt: [(kezdet, vég)] a tétel szövegében; kihagy: szövegrészek, amelyek nem hivatkozások
    (beállítás: kiirasElirasok.kihagy és kiirasElirasok.nemHivatkozas)."""
    r = list(sz)
    for a, b in hasznalt:
        r[a:b] = ' ' * (b - a)
    r = ''.join(r)
    for x in kihagy:
        if x:
            r = r.replace(x, ' ' * len(x))
    for rx in MINOSITO:
        r = rx.sub(lambda m: ' ' * len(m.group(0)), r)
    zarojel = hossztarto(r)            # a zárójeles leírás a kulcsszó-vizsgálatból kimarad (a szám-vizsgálatból nem)
    ki = []
    for m in re.finditer(r'[^;,\s][^;,]*?(?=\s{3,}|[;,]|$)', r):
        szel = m.group(0)
        # a közvetlenül utána álló, felhasznált hivatkozás leírása („a foglalkoztatás alsó korhatáráról szóló ILO
        # egyezmény (kihirdetve: 2000. évi LXIX. törvénnyel)”, „… gyűlés biztosításával kapcsolatos … szóló [rendelet]”)
        k = m.end()
        while k < len(sz) and sz[k] == ' ':
            k += 1
        leiras = k < len(sz) and r[k] == ' ' and sz[k] != ' '
        k = m.start() - 1
        while k >= 0 and sz[k] == ' ':
            k -= 1
        elotte = k >= 0 and r[k] == ' ' and sz[k] not in ' ,;'
        g = GYANUS.search(szel)
        if g and leiras and re.search(r'\bszóló(?:\s+\d{4}\.)?(?:\s+\S+\s+\d{1,2}-i)?\s*\(?$', szel.rstrip()):
            continue          # a közvetlenül utána álló, felhasznált hivatkozás leírása („… szóló”)
        if elotte and (not re.search(r'\d|§|[Cc]ikk', szel) or re.fullmatch(r'(?:az?)\s.*(?:ról|ről|ra|re)', szel.strip())):
            continue          # a felhasznált hivatkozás után álló neve vagy címe („C-106/77. sz. Simmenthal-ügy”,
                              # „… rendelet a 2024. évi munkaszüneti napok körüli munkarendről”)
        if not g:
            if leiras:
                continue
            g = GYANUS_SZO.search(zarojel[m.start():m.end()])
            if not g or m.start() + g.start() < cim_veg:
                continue
        resz = sz[m.start():m.end()].strip(' -–.([')
        if len(resz) > 120:
            resz = resz[:117] + '…'
        sor = 'fel nem ismert hivatkozás: %s' % resz
        if resz and sor not in ki:
            ki.append(sor)
    return ki


SZOLO_VEG = r'\bszóló(?:\s+\d{4}\.)?(?:\s*\S+\s+\d{1,2}-i)?$'


def cim_kepez(sz, elso):
    """A tétel címe: a szöveg az első hivatkozásig; a végéről a „ -”, „[”, „;” és a forrás leírása („… szóló”,
    „… szóló 2016. április 27-i”) lekerül."""
    cim = sz[:elso]
    cim = re.sub(r'[\s;,:\-–\[(]+$', '', cim)
    szolo = re.search(SZOLO_VEG, cim)
    if szolo:
        hatarok = [m.end() for m in re.finditer(r'[.;:]\s|[\[(]|\s[-–]\s', cim)]
        hatarok += [m.start() for m in re.finditer(r'(?<=[a-záéíóöőúüű,])\s+(?=Az?\s)', cim)]
        hatarok = [h for h in hatarok if 0 < h <= szolo.start()]
        if hatarok:
            uj = re.sub(r'[\s;,:\-–\[(]+$', '', cim[:max(hatarok)])
            if uj:
                cim = uj
    return cim.strip()


def felold(t, B, fajlok):
    """A tétel (vagy a tételcsoport bevezetőjének) hivatkozásai. Minden, ami a szövegben forráshivatkozásnak látszik,
    vagy feloldott (hivatkozasok), vagy feloldatlan (feloldatlan), vagy név szerint kihagyott (kiirasElirasok.kihagy,
    kiirasElirasok.nemHivatkozas) – a maradékvizsgálat (maradek) ezt gépileg őrzi."""
    import korpusz_felmeres as kf
    sz = t['szoveg']
    elirasok = B.get('kiirasElirasok', {}) or {}
    kihagy = set(elirasok.get('kihagy', []))
    nem_hiv = list(elirasok.get('nemHivatkozas', []))
    # A nemHivatkozas szövegrészei a feloldás ELŐTT kikerülnek (hossztartó kitöltéssel): a bennük álló forrásjelölő és
    # egység sem oldódik fel (C/1 14. tétel: a 43/2012. AB határozat címében említett „Csvt. 7. és 8. §”). A cím az
    # eredeti szövegből készül; a kitöltő jel (¤) se nem betű, se nem szóköz, így a helyek nem tolódnak el.
    szf = sz
    for x in nem_hiv:
        if x:
            szf = szf.replace(x, '¤' * len(x))
    jelolok = []
    for f in B['forrasok']:
        for minta in f['mintak']:
            for m in re.finditer(minta, szf):
                jelolok.append((m.start(), m.end(), f))
    jelolok.sort(key=lambda x: x[0])
    # a cím az első olyan forrásmegnevezésig tart, amelyet szerkezeti egység követ („Be. 1. §”), vagy az első felismert
    # határozat-, ügy- vagy jogszabályszámig; a mondatban álló megnevezés („A Be. szerkezeti felépítése”) a cím része
    hivatkozo = [j[0] for j in jelolok if re.match(r'\s*(?:\d|[IVXLC]+\s*[.\-–]|[A-Z]\)|Nemzeti|Alapvetés|Szabadság|Az állam)', szf[j[1]:j[1] + 14])]
    talalatok = [(k, n, a, b) for k, n, a, b in kf.hivatkozasok_hely(kf.lapit(szf)) if k[0] != 'nev' and n not in kihagy]
    # a határozat-, ügy- és uniós jogiaktus-szám is címhatár (a törvény teljes neve nem: az a címben leíró is lehet);
    # a jelölőn belüli találat helyett a jelölő eleje; a forráslistát nyitó „[” is címhatár
    def jelolo_eleje(x):
        return next((j[0] for j in jelolok if j[0] <= x < j[1]), x)
    zarojel = [m.start() for m in re.finditer(r'\[', sz) if any(m.start() < j[0] <= m.start() + 2 for j in jelolok)
               or any(m.start() < a <= m.start() + 2 for _, _, a, _ in talalatok)]
    jeloltek = sorted(set(hivatkozo + [jelolo_eleje(a) for k, _, a, _ in talalatok if k[0] != 'tv'] + zarojel[:1]
                          + [m.start() for m in re.finditer(r'\((?:PK|MK|\d+/\d{4})', sz)]))
    if not jeloltek:
        # egység nélküli forrásmegnevezés, amely nem a mondat része (utána nem kisbetűs folytatás áll): címhatár
        jeloltek = [j[0] for j in jelolok if not re.match(r'\s*[a-záéíóöőúüű]', szf[j[1]:j[1] + 3])]
    t['cim'] = sz.strip(' ;,')
    for elso in jeloltek:
        cim = cim_kepez(sz, elso)
        if cim and not re.search(SZOLO_VEG, cim):
            t['cim'] = cim
            break
        # a cím maga a forrás neve („… költségekről szóló 32/2003. (VIII. 22.) IM rendelet”): a következő jelölt dönt
    hasznalt = [(0, len(t['cim']))] if t['cim'] else []
    hiv, gond = [], []
    for i, (a, b, f) in enumerate(jelolok):
        hasznalt.append((a, b))
        vege = jelolok[i + 1][0] if i + 1 < len(jelolok) else len(szf)
        szakasz = szf[b:vege] if vege > b else ''
        fajl = f.get('fajl') or fajl_keres(f['fajlKezdet'], fajlok)
        if not fajl or nfc(fajl) not in fajlok:
            gond.append('%s: a korpuszban nincs fájl' % f['kod'])
            continue
        helyek = []
        tart = egysegek(szakasz, f['egyseg'], helyek)
        szerk = szerkezet_tartomany(fajl, szakasz, f['egyseg']) if f['egyseg'] in ('§', 'cikk') else []
        hasznalt += [(b + x, b + y) for x, y in helyek] + [(b + x, b + y) for _, _, _, x, y in szerk]
        for tol, ig, nev, _, _ in szerk:
            if nev is None:
                continue          # helymegjelölés („II. fejezet 3. §”): a § maga a hivatkozás
            szov = tartomany_szoveg(fajl, f['egyseg'], tol, ig) if tol else None
            if szov is None:
                gond.append('%s %s: a korpusz-fájlban nem található' % (f['kod'], nev))
                continue
            hiv.append({'forras': f['kod'], 'fajl': fajl, 'egyseg': f['egyseg'], 'tol': tol, 'ig': ig, 'karakter': len(szov), 'kiirasSzerint': nev})
        if not tart and not any(x[2] for x in szerk):
            # egység nélküli jelölő: teljes fájl – de csak ha ugyanez a forrás a tételben máshol nem áll egységgel
            # (jelölőből vagy tetelForras-ból); ezt a tetelForras feldolgozása után döntjük el (_feltetel)
            hiv.append({'forras': f['kod'], 'fajl': fajl, 'egyseg': f['egyseg'], 'tol': None, 'ig': None, 'karakter': len(be('korpusz/' + fajl)), '_feltetel': True})
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
    def utana_egysegek(sz, kb, hatarok):
        """A teljes fájlként feloldott forrás után álló egység-, fejezet- és pontmegjelölés („GDPR … 5-7. cikk,
        12-22. cikk”, „… rendelet XVI. fejezet”) a teljes fájlba esik: felhasználtnak számít (a következő jelölőig)."""
        vege = min([h for h in hatarok if h > kb] + [len(sz)])
        x = sz[kb:vege]
        x = x[:next((m.start() for m in re.finditer(r'\s[-–]\s|;', x)), len(x))]
        helyek = []
        for e in ('§', 'cikk', 'romaiCikk'):
            egysegek(x, e, helyek)
        for m in re.finditer(r'(?<![\w.])' + _ROMAI_LISTA + r'(?:[Ff]ejezet|FEJEZET|[Rr]ész|RÉSZ|[Cc]ím|CÍM)\w*', hossztarto(x)):
            helyek.append(m.span())
        return [(kb + a, kb + b) for a, b in helyek]

    if B.get('hatarozatMod') == 'altalanos':
        kotott = {nfc(f.get('fajl') or fajl_keres(f.get('fajlKezdet', '\x00'), fajlok) or '') for f in B['forrasok']}
        hl = []
        for nev, kulcs, fajl, jeloltek, ka, kb, jel in hatarozatok_altalanos(szf, fajlok):
            if jel == 'ismetles':
                hasznalt.append((ka, kb))
                continue          # ugyanaz a fájl más megnevezéssel (pl. „3/2025. JEH (Jpe.III.60.053/2024/12.)”) már felvéve
            if fajl is None and kulcs[0] == 'tv' and nev not in kihagy:
                continue          # törvény, amely nincs a korpuszban és a forrasok sem köti: a maradékvizsgálat jelzi
            hasznalt.append((ka, kb))
            if any(nfc(j) in kotott for j in jeloltek):
                continue          # a beállítás forrasok mintái már kezelik (törvény a teljes nevével, kötött határozat)
            if fajl is None and nev in kihagy:
                continue          # a kiírás rögzített elírása, illetve név szerint kihagyott hivatkozás
            fajl = elirasok.get('megfeleltet', {}).get(nev, fajl)
            hl.append((nev, fajl))
            if fajl:
                hasznalt += utana_egysegek(szf, kb, [j[0] for j in jelolok] + [a for _, _, a, _ in talalatok])
    else:
        helyek = []
        hl = hatarozatok(szf, fajlok, helyek)
        hasznalt += helyek
    for nev, fajl in hl:
        if fajl:
            hiv.append({'forras': nev, 'fajl': fajl, 'egyseg': 'egesz', 'tol': None, 'ig': None, 'karakter': len(be('korpusz/' + fajl))})
        else:
            gond.append('%s: a korpuszban nincs fájl' % nev)
    # Tételszintű forrásmegfeleltetés (beallitas.json: tetelForras): ha a kiírás hatályon kívül helyezett vagy a
    # korpuszban másként szereplő forrást nevez meg, a tétel a megadott forrás(oka)t kapja; a megnevezett, de fel nem
    # oldható hivatkozás ettől nem hiány (Attila tételenkénti döntése alapján).
    for f in (B.get('tetelForras') or {}).get(str(t.get('sorszam')), []):
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
    # az egység nélküli jelölő teljes-fájl hivatkozása elmarad, ha ugyanez a forrás a tételben egységgel is szerepel
    # (B/2 52. tétel: „Be. 348-355, Be. 358-368. §” – a § jel nélküli „Be.” nem adja a teljes Be.-t a tetelForras mellett)
    egysegben = {h['forras'] for h in hiv if h.get('tol') is not None}
    hiv = [h for h in hiv if not (h.get('_feltetel') and h['forras'] in egysegben)]
    for h in hiv:
        h.pop('_feltetel', None)
    # maradékvizsgálat: ami hivatkozásnak látszik, de a feloldás nem használta fel
    gond += maradek(sz, hasznalt, len(t['cim']), sorted(kihagy) + nem_hiv)
    if not hiv and not gond and 'sorszam' in t:
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


TELJES_KORLAT = 120000      # a teljes fájlként előírt forrás eddig a terjedelemig kerül a kérésbe szó szerint


def atfogo_kodok():
    return {f['kod'] for f in beallitas()['forrasok'] if f.get('atfogo')}


def eloirt_szoveg(t):
    """A tétel előírt joganyaga egy szövegben (az API-kötegek és az ellenőrzés számára).
    - A §-/cikk-tartomány szövege mindig bekerül (a csoportszintű előírásé is).
    - A teljes fájlként előírt forrás (a csoportszintű is, „csoport”: true) szó szerint bekerül, ha legfeljebb
      TELJES_KORLAT (120 000) karakter; e fölött csak a megnevezése és a „teljes szöveg terjedelmi okból nem szerepel”
      megjegyzés.
    - Az átfogó ismeret (beállítás: atfogo) teljes fájlként soha nem kerül be (csak a megnevezése)."""
    reszek = []
    nevek = forras_nevek()
    atfogo = atfogo_kodok()
    for h in t['hivatkozasok']:
        if h['egyseg'] == 'egesz' or h['tol'] is None:
            nev = (' — ' + nevek[h['forras']]) if nevek.get(h['forras']) else ''
            csop = ' (tételcsoport-előírás)' if h.get('csoport') else ''
            if h['forras'] in atfogo:
                reszek.append('### %s%s%s\n(átfogó ismeret: a teljes szöveg nem szerepel)' % (h['forras'], csop, nev))
                continue
            szov = be('korpusz/' + h['fajl']).strip()
            if len(szov) > TELJES_KORLAT:
                reszek.append('### %s%s (%s)%s\n(a teljes szöveg terjedelmi okból nem szerepel: %d karakter)'
                              % (h['forras'], csop, h['fajl'], nev, len(szov)))
                continue
            fej = '### %s%s (teljes szöveg: %s)%s' % (h['forras'], csop, h['fajl'], nev)
        else:
            szov = tartomany_szoveg(h['fajl'], h['egyseg'], h['tol'], h['ig'])
            fej = egyseg_fej(h['forras'], h['tol'], h['ig'], h['egyseg'], nevek.get(h['forras'], ''))
        reszek.append(fej + '\n' + szov)
    return '\n\n'.join(reszek)


def main():
    B = beallitas()
    fajlok = korpusz_fajlok()
    tl, csoportok, _ = kiiras_reszek(be(B['kiiras']['fajl']))
    tetelek = [felold(t, B, fajlok) for t in tl]
    # A tételcsoport bevezetőjének forráslistája („A fejezetnél következő jogszabályok … ismerete szükséges”) a csoport
    # minden tételének előírása: csoportEloiras, és a tételek hivatkozásai között „csoport”: true jelöléssel.
    csoport_eloiras = []
    for cim, bev in csoportok.items():
        if not bev:
            continue
        c = felold({'szoveg': bev}, B, fajlok)
        c['cim'] = cim          # a bevezetőnek nincs saját címe: a csoportfej
        egyedi, latott = [], set()
        for h in c['hivatkozasok']:       # a rövidítés és a teljes név ugyanazt a forrást jelöli („Kit.” – „2018. évi CXXV. törvény”)
            k = (h['forras'], h['fajl'], h['tol'], h['ig'])
            if k not in latott:
                latott.add(k); egyedi.append(h)
        c['hivatkozasok'] = egyedi
        csoport_eloiras.append({'csoport': cim, 'szoveg': bev, 'hivatkozasok': c['hivatkozasok'], 'feloldatlan': c['feloldatlan']})
        for t in tetelek:
            if t['csoport'] == cim:
                for h in c['hivatkozasok']:
                    t['hivatkozasok'].append(dict(h, csoport=True))
                    t['eloirasok'].append({'forras': h['forras'], 'tol': h['tol'], 'ig': h['ig'], 'csoport': True})
    hibak = []
    if len(tetelek) != B['tetelDb']:
        hibak.append('a kiírás tételszáma %d, a beállításé %d' % (len(tetelek), B['tetelDb']))
    man = json.loads(be('jegyzetek/manifest.json'))
    # a kiírásban nem szereplő (kizárt) jegyzet-sorszámok (beallitas.json: kizartJegyzetSorszam, nem kötelező)
    kizart = sorted(int(x) for x in (B.get('kizartJegyzetSorszam') or []))
    jegyz = {}
    for x in man['items']:
        if x['sorszam'] not in kizart:
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
          'csoportEloiras': csoport_eloiras,
          'tetelek': tetelek}
    json.dump(ki, open(os.path.join(GY, 'tetelsor', 'tetelsor.json'), 'w', encoding='utf-8'), ensure_ascii=False, indent=1)
    forrasok_ir(B, fajlok, tetelek)
    hasznalt = {h['fajl'] for t in tetelek for h in t['hivatkozasok']} | {a['fajl'] for a in atfogo if a['fajl']}
    nem_hasznalt = [f for f in fajlok if f not in hasznalt]
    gondok = [('%d. tétel' % t['sorszam'], g) for t in tetelek for g in t['feloldatlan']]
    gondok += [('„%s” csoport bevezetője' % c['csoport'], g) for c in csoport_eloiras for g in c['feloldatlan']]
    L = ['# S1 – alapfelvétel: %s' % B['cim'], '',
         '- kiírás: %d tétel (%s); jegyzet: %d rész %d tételben' % (len(tetelek), B['kiiras']['fajl'], len(man['items']), len(jegyz)),
         '- feloldott hivatkozás: %d; feloldatlan: %d; a kiírás által nem hivatkozott korpusz-fájl: %d' % (sum(len(t['hivatkozasok']) for t in tetelek), len(gondok), len(nem_hasznalt)),
         '- alapfelvételi hiba: %d' % len(hibak)]
    if kizart:
        L.append('- kiíráson kívüli, kizárt jegyzet: %s' % ', '.join(map(str, kizart)))
    if csoport_eloiras:
        L.append('- tételcsoport-előírás: %s' % '; '.join('%s (%d hivatkozás)' % (c['csoport'], len(c['hivatkozasok'])) for c in csoport_eloiras))
    L.append('')
    L += ['- HIBA: ' + h for h in hibak]
    L += ['', '## Feloldatlan hivatkozások (hiánylista a korpuszhoz)', '']
    L += ['- %s: %s' % g for g in gondok] or ['- nincs']
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
