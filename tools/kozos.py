"""Közös segédfüggvények a tételsor-tároló ellenőrző szkriptjeihez (csak a standard könyvtár).

A tároló gyökeréből futtatandó szkriptek importálják:
    sys.path.insert(0, 'tools'); import kozos
"""
import json, os, re, sys, unicodedata

GYOKER = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
KORPUSZ = os.path.join(GYOKER, 'korpusz')

BEKEZDES = r'(?:\s*\(\d+\)(?:\s*[–-]\s*\(\d+\))?(?:,\s*\(\d+\)(?:\s*[–-]\s*\(\d+\))?)*(?:\s*bekezdés)?)?'

_BEALLITAS = None
_KOTELEZO = (
    'sema', 'azon', 'cim', 'targyKod', 'celag', 'foKodex', 'parMinta',
    'dobozRovidites', 'beagyazott', 'kiejtes', 'mondatRovidites',
    'jogszabalyRovidites', 'kontroll', 'kiirasRovidites', 'biroRx',
    'kommentar', 'mintaTetelek', 'rt2Alap', 'hangAlapAgak', 'emlites',
    'elhatarolasPar', 'rt2PontKivetel', 'regiAuditFoMinta', 'regiAuditKod',
)
_KONTROLL = ('jelzok', 'iranymutatasRx', 'paragrafusForrasok')


def beallitas():
    """A tetelsor/beallitas.json egyszeri beolvasása. Hiányzó fájl, érvénytelen JSON
    vagy hiányzó kötelező kulcs: érthető hiba a stderr-re, kilépés 2-vel."""
    global _BEALLITAS
    if _BEALLITAS is not None:
        return _BEALLITAS
    ut = os.path.join(GYOKER, 'tetelsor', 'beallitas.json')
    if not os.path.isfile(ut):
        sys.stderr.write('beallitas: hiányzik a tetelsor/beallitas.json\n')
        raise SystemExit(2)
    try:
        d = json.load(open(ut, encoding='utf-8'))
    except ValueError as e:
        sys.stderr.write('beallitas: érvénytelen JSON a tetelsor/beallitas.json fájlban: %s\n' % e)
        raise SystemExit(2)
    except OSError as e:
        sys.stderr.write('beallitas: a tetelsor/beallitas.json nem olvasható: %s\n' % e)
        raise SystemExit(2)
    if not isinstance(d, dict):
        sys.stderr.write('beallitas: a tetelsor/beallitas.json nem objektum\n')
        raise SystemExit(2)
    for k in _KOTELEZO:
        if k not in d:
            sys.stderr.write('beallitas: hiányzik a kötelező kulcs: %s\n' % k)
            raise SystemExit(2)
    kontroll = d['kontroll']
    if not isinstance(kontroll, dict):
        sys.stderr.write('beallitas: a kontroll kulcs nem objektum\n')
        raise SystemExit(2)
    for k in _KONTROLL:
        if k not in kontroll:
            sys.stderr.write('beallitas: hiányzik a kötelező kulcs: kontroll.%s\n' % k)
            raise SystemExit(2)
    _BEALLITAS = d
    return d


def konyves(kod):
    """Igaz, ha a parMinta könyves (§ 5:44) és a kod a fő kódex (A/1-en: kod == 'Ptk')."""
    B = beallitas()
    return B['parMinta'] == 'konyv' and kod == B['foKodex']


# A tételek jogszabálydobozainak fejlécében használt rövidítések -> forráskód (tetelsor/forrasok.json).
# Tárgyanként a beállítás dobozRovidites tömbje (A/1: Ptk., Ptké., …).
_B = beallitas()
DOBOZ_RÖVIDITES = [(minta, kod) for minta, kod in _B['dobozRovidites']]
BEAGYAZOTT = {kod: tuple(par) for kod, par in _B['beagyazott'].items()}
if _B['parMinta'] == 'konyv':
    PAR = r'(\d+(?::\d+)?(?:/[A-Z])?)'
else:
    PAR = r'(\d+(?:/[A-Z])?)'
FEJLEC = re.compile(r'^(' + '|'.join(r for r, _ in DOBOZ_RÖVIDITES) + r')\s*' + PAR + r'\.\s?§' + BEKEZDES + r'$')


def nfc(s):
    return unicodedata.normalize('NFC', s)


def norm(s):
    """Összevetéshez: NFC, nem törő szóköz, csillagos lábjegyzet-jel, idézőjel, gondolatjel, szóköz."""
    s = nfc(s).replace(' ', ' ')
    s = re.sub(r'\s*\*\s*(?=\s|$)', ' ', s)
    s = re.sub(r'[„”"]', '"', s)
    s = re.sub(r'[–—]', '-', s)
    return re.sub(r'\s+', ' ', s).strip()


def forrasok():
    d = json.load(open(os.path.join(GYOKER, 'tetelsor', 'forrasok.json'), encoding='utf-8'))
    return {f['kod']: f for f in d['forrasok']}


def tetelsor():
    return json.load(open(os.path.join(GYOKER, 'tetelsor', 'tetelsor.json'), encoding='utf-8'))


def rovid_kod(rov):
    for rx, kod in DOBOZ_RÖVIDITES:
        if re.fullmatch(rx, rov):
            return kod
    return None


def korpusz_fajl(nev):
    """A korpusz-fájl útvonala; a tárolóban a nevek NFC-k."""
    p = os.path.join(KORPUSZ, nfc(nev))
    if os.path.exists(p):
        return p
    for f in os.listdir(KORPUSZ):
        if nfc(f) == nfc(nev):
            return os.path.join(KORPUSZ, f)
    return None


# Módosító törvénybe ágyazott, idézőjelben közölt kódex-szöveg: forráskód -> (a módosító törvény első és az utána
# következő §-ának száma). A doboz fejléce A/1-en: „Módosított Ptk. 6:550. §”. A BEAGYAZOTT a beállításból épül.


def beagyazott_sorok(fajl, tol, ig):
    """A módosító törvény [tol, ig) §-ainak sorai."""
    L = open(fajl, encoding='utf-8').read().split('\n')
    a = next(i for i, l in enumerate(L) if l.strip().startswith(tol + '. §'))
    b = next(i for i, l in enumerate(L) if i > a and l.strip().startswith(ig + '. §'))
    return L[a:b]


def beagyazott_paragrafusok(fajl, tol, ig):
    if beallitas()['parMinta'] == 'konyv':
        rx = re.compile(r'^„(\d+:\d+(?:/[A-Z])?)\. §|^(\d+:\d+(?:/[A-Z])?)\. § \[')
    else:
        rx = re.compile(r'^„(\d+(?:/[A-Z])?)\. §|^(\d+(?:/[A-Z])?)\. § \[')
    d, sorrend, cur = {}, [], None
    for l in beagyazott_sorok(fajl, tol, ig):
        t = l.strip(); m = rx.match(t)
        if m:
            cur = m.group(1) or m.group(2); d[cur] = []; sorrend.append(cur)
            rest = t[t.index('§') + 1:].strip()
            if rest:
                d[cur].append(rest)
        elif cur and not re.match(r'^\d+\. §', t):
            d[cur].append(l)
        else:
            cur = None
    return {k: re.sub(r'"$', '', norm(' '.join(v))).strip() for k, v in d.items()}, sorrend


def jogszabaly_paragrafusok(kod, fajl):
    """{§-szám: normalizált szöveg} és a §-ok sorrendje a korpusz-fájlban."""
    if kod in BEAGYAZOTT:
        return beagyazott_paragrafusok(fajl, *BEAGYAZOTT[kod])
    ptk = konyves(kod)
    rx = re.compile(r'^(\d+:\d+(?:/[A-Z])?)\. §' if ptk else r'^(\d+(?:/[A-Z])?)\. §')
    d, sorrend, cur = {}, [], None
    for l in open(fajl, encoding='utf-8').read().split('\n'):
        m = rx.match(l.strip())
        if m:
            cur = m.group(1)
            if cur not in d:
                d[cur] = []; sorrend.append(cur)
            rest = l.strip()[m.end():].strip()
            if rest:
                d[cur].append(rest)
        elif cur:
            d[cur].append(l)
    return {k: norm(' '.join(v)) for k, v in d.items()}, sorrend


def korpusz_jogszabalyok():
    """Forráskód -> ({§: szöveg}, sorrend) azokra a jogszabályokra, amelyek §-okra tagolódnak."""
    out = {}
    for kod, f in forrasok().items():
        # A típus nélküli, de korpuszfájllal bíró forrás is jogszabály (új tételsor, ahol a beállítás
        # nem ad tipust). Az A/1 minden forrása tipust ad, ezért ott a feltétel a régivel azonos.
        if f.get('tipus') not in ('törvény', 'rendelet', None) or not f.get('korpusz'):
            continue
        p = korpusz_fajl(f['korpusz'][0])
        if p:
            out[kod] = jogszabaly_paragrafusok(kod, p)
    return out


def tetel_szoveg(n):
    return nfc(open(os.path.join(GYOKER, f'{n:02d}.txt'), encoding='utf-8').read())


def SZAMOZOTT_CIM(s):
    """Számozott címsor-e a sor („2. A TÁRSASHÁZ ALAPÍTÁSA”): a szám után csupa nagybetűs szöveg áll."""
    t = re.sub(r'^\d+(?:\.\d+)*\.\s*', '', s)
    return bool(t) and t.upper() == t and bool(re.search(r'[A-ZÁÉÍÓÖŐÚÜŰ]', t))


def dobozok(txt):
    """A tétel jogszabálydobozai: [(forráskód, §, fejléc, [sorok])].

    A doboz a fejléc utáni első nem üres sor, és az azt követő normasorok: bekezdés („(1)”),
    pont („a)”, „aa)”), számozott pont („1. Társasház: …”, „1.1. Lakóépület: …” – az értelmező
    rendelkezések pontjai) vagy szögletes zárójeles cím. Az első nem normasor (magyarázó bekezdés,
    címsor, „ÖSSZEFOGLALÁS”, „b) Házastárs öröklése …” típusú alcím) lezárja a dobozt.
    A számozott címsor („2. A TÁRSASHÁZ ALAPÍTÁSA”) csupa nagybetűs, ezért nem normasor.
    """
    L = [l.strip() for l in txt.split('\n')]

    def normasor(s):
        if re.match(r'^[a-z]{1,2}\) [A-ZÁÉÍÓÖŐÚÜŰ]', s) and not re.search(r'[.;,:]$', s) and len(s) < 120:
            return False  # alcím, nem pont
        if re.match(r'^\d{1,3}(?:\.\d{1,2})*\.(?:\s|$)', s):
            return not SZAMOZOTT_CIM(s)  # számozott pont (értelmező rendelkezés), nem címsor
        return bool(s.startswith('[') or re.match(r'^\(\d+[a-z]?\)', s) or re.match(r'^[a-z]{1,2}\)', s))

    out, i = [], 0
    while i < len(L):
        m = FEJLEC.match(L[i])
        if not m:
            i += 1; continue
        kod = rovid_kod(m.group(1)); par = m.group(2); j = i + 1; sorok = []
        while j < len(L):
            s = L[j]
            if not s:
                j += 1; continue
            if FEJLEC.match(s) or s.isupper():
                break
            if not sorok:
                if not normasor(s) and re.match(r'^([IVX]+|\d+)\. [A-ZÁÉÍÓÖŐÚÜŰ]', s):
                    break
                sorok.append(re.sub(r'^\d+(?::\d+)?(?:/[A-Z])?\. §\s*', '', s)); j += 1; continue
            if not normasor(s):
                if len(sorok) == 1 and sorok[0].startswith('[') and sorok[0].endswith(']'):
                    # szögletes zárójeles cím után a bekezdésszám nélküli normaszöveg következik
                    sorok.append(s); j += 1; continue
                # számozatlan sor, amely után a soron következő bekezdés jön: a doboz része
                kov = next((x for x in L[j + 1:] if x), '')
                mk = re.match(r'^\((\d+)([a-z]?)\)', kov)
                elozo = [int(x.group(1)) for x in (re.match(r'^\((\d+)[a-z]?\)', y) for y in sorok) if x]
                if mk and elozo and int(mk.group(1)) - elozo[-1] in ((0, 1) if mk.group(2) else (1,)) and not FEJLEC.match(s):
                    sorok.append(s); j += 1; continue
                msz = re.match(r'^(\d{1,3}(?:\.\d{1,2})*)\.(?:\s|$)', sorok[-1])
                if msz and re.match(r'^' + re.escape(msz.group(1)) + r'\.\d{1,2}\.(?:\s|$)', kov) and not FEJLEC.match(s):
                    # számozott ponton belüli számozatlan sor („A karbantartás lehet:”), amely után a pont alpontja jön
                    sorok.append(s); j += 1; continue
                if re.match(r'^[–-] ', s) and re.match(r'^([a-z]{1,2}\)|[–-]) ', sorok[-1]):
                    # a ponton belüli gondolatjeles alfelsorolás
                    sorok.append(s); j += 1; continue
                if re.match(r'^[a-z]{1,2}\) ', sorok[-1]) and re.match(r'^[a-záéíóöőúüű]', s):
                    # a felsorolást lezáró szöveg („esetén.”, „kérheti.”), utána a doboz folytatódhat. Hosszkorlát nincs
                    # (2026-11-18): a korábbi 300 karakteres korlát a 77. tétel 4:136. §-ának 355 karakteres lezáró sorát
                    # levágta; kisbetűs, nem pontjeles sor a tételekben csak lezáró sorként fordul elő, és a doboz
                    # szövegét az ellenorzes.py a korpusszal veti össze, így magyarázó bekezdés nem kerülhet be észrevétlenül
                    sorok.append(s); j += 1; continue
                break
            sorok.append(s); j += 1
        out.append((kod, par, L[i], sorok))
        i = j
    return out
