#!/usr/bin/env python3
"""Korpusz-felmérés a kiírásból, beállítás nélkül (S2 előkészítése új tételsoron).

    python3 tools/korpusz_felmeres.py --kiiras=tetelsor/kiiras_2026.txt [--korpusz=korpusz] [--ki=jelentesek/korpusz_felmeres] [--gyoker=<tároló>]

A kiírás szövegéből kigyűjti a megnevezett forrásokat (törvény, rendelet, AB határozat, jogegységi határozat,
kollégiumi vélemény, közzétett eseti döntés, uniós jogi aktus, EUB-ügy), és a korpusz fájlneveihez köti őket.
Kimenet: <ki>.md és <ki>.json – megvan / hiányzik / a korpuszban van, de a kiírás nem nevezi meg.
Ez első felmérés: a kötelező eredményt az alapfelvetel.py adja a beállítás elkészülte után.
Utolsó sor: korpusz_felmeres: forrás N, megvan M, hiányzik H, nem hivatkozott korpuszfájl K
"""
import json, os, re, sys, unicodedata

GY = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


def arg(nev, alap=None):
    for a in sys.argv:
        if a.startswith('--%s=' % nev):
            return a.split('=', 1)[1]
    return alap


def nfc(s):
    return unicodedata.normalize('NFC', s)


def lapit(s):
    s = nfc(s).replace('\x0c', ' ').replace(' ', ' ').replace('−', '-')
    s = re.sub(r'[–—]', '-', s)
    return re.sub(r'\s+', ' ', s)


# A határozattípusok mintái (a kiírás alakjai szerint). A jogegységi határozat és a kollégiumi vélemény előtagja
# szabad sorrendű szólánc („Büntető-polgári”, „közigazgatási és polgári”, „Közigazgatási- munkaügyi-polgári”); a
# fajtát a valaszt() a megnevezésből képzett rövidítéssel (je_rov) különbözteti meg.
_JE_ELO = r'(?:(?:[Bb]üntető|[Pp]olgári|[Kk]özigazgatási|[Mm]unkaügyi|[Gg]azdasági)(?:\s*-\s*|\s+és\s+|\s+))'
HAT_TIPUS = [
    ('AB', r'AB\s*(?:határozat|végzés|hat\.)'),
    ('JE', r'(?:számú\s+)?' + _JE_ELO + r'*(?:jogegységi\s+határozat|KMPJE|BKPJE|BPJE|KPJE|KMJE|BJE|PJE|KJE|MJE|JEH)'),
    ('VELEMENY', r'(?:LB\s+)?PK-KK\.?\s+(?:közös\s+)?vélemény|' + _JE_ELO + r'+kollégiumi\s+vélemény|'
                 r'(?:BK|PK|GK|KK|MK|KMK|BKv|PKv)\.?\s*(?:vélemény|kollégiumi vélemény|állásfoglalás)?'),
    ('RENDELET', r'(?:Korm\.?|[A-ZÁÉÍÓÖŐÚÜŰ][A-Za-zÁÉÍÓÖŐÚÜŰáéíóöőúüű]{0,7}M|MNB|NGM|IM|BM|EüM|PM|NM|HM|KüM|MT|ME|OBH|LÜ|ORFK)\.?\s*(?:rendelet|r\.|utasítás|határozat)'),
]
# A dátum hónapja a kiírásban elírva is állhat („(X1. 15.)” = „(XI. 15.)”), és a zárójel előtt a pont, a nap után a
# pont hiányozhat („(XI.28)”, „1/2022 (VI. 8.)”). A szám „137/B/1991” alakú is lehet (az AB „B” ügyszáma).
SZAMEV = re.compile(r'(?<![\d/])(\d{1,4}(?:/[A-Z])?)/(\d{4})\.?\s*(?:\(\s*([IVXL1]+)\.\s*(\d{1,2})\.?\s*\)\s*)?(?:számú\s+)?(' + '|'.join(t for _, t in HAT_TIPUS) + r')')
KOLL = re.compile(r'\b(?:(BK|PK|GK|KK|MK|KMK)\s+(\d{1,3})\.(?!\s*\d)|(\d{1,3})\.\s*(?:számú\s+)?(BK|PK|GK|KK|MK|KMK)\s*(?:vélemény|állásfoglalás)|(BKv|PKv)\.?\s*(\d{1,3})\.?)')
TORVENY = re.compile(r'(\d{4})\.\s*évi\s+([IVXLCDM]+)\.\s*(törvény|törvényerejű rendelet|tvr\.?)')
ESETI = re.compile(r'\b(BH|EBH|EH|BDT|EBD|KGD|ÍH|KJD)[\s.]{0,2}(\d{4})[./]\s?([0-9A-Z]+(?:[./][0-9A-Z]+)*)\.?')
EUX = re.compile(r'\b(\d{1,4})[/_](\d{1,4})[/_ ]\s?(EU|EK|EGK|Euratom|IB|KKBP)\b')


def ev_e(x):
    return len(x) == 4 and 1957 <= int(x) <= 2030

EU3 = re.compile(r'\((EU|EK|EU, Euratom)\)\s*(\d{4})/(\d{1,4})\b')
EU4 = re.compile(r'\b(20\d{2})/(\d{2,4})\s+(irányelv|rendelet)')
# EUB-ügyszám: „C-518/15”, négyjegyű évvel „C-303/1998”, tartománnyal „C-13-24/66” (= C-13/66 … C-24/66)
EUB = re.compile(r'\b([CT])-\s?(\d{1,4})(?:\s*-\s*(\d{1,4}))?/(\d{4}|\d{2})(?!\d)')
# Az EUB véleménye: „2/94. sz. vélemény”, „2/13. vélemény”, „2/94. sz. és 2/13. sz. véleménye”
EUBVEL = re.compile(r'(?<![\d/])((?:\d{1,2}/\d{2}(?!\d)\.?\s*(?:sz\.|számú)?\s*(?:,|és)?\s*)+)(?:EUB[- ]?|[Bb]írósági\s+)?vélemény', re.I)
# A Kúria (Legfelsőbb Bíróság) ügyszáma: „Jpe.II.60.036/2024/23.”, „Kfv.III.37.598/2020/4.”, „Kfv. 37.173/2024/7.”,
# „Legf. Bír. Kfv. I. 35.055/2007.” – a kulcs a lajstromjel, a szám (pont nélkül) és az év; a tanács nem része
UGYSZAM = re.compile(r'\b(Jpe|Kfv|Pfv|Gfv|Mfv|Bfv|Kpkf|Kpk|Pkf|Gpkf|Kf|Pf|Gf|Mf|Bf)\.?\s*(?:([IVX]+)\.?\s*)?(\d{1,3}\.\d{3}|\d{1,6})[/_](\d{4})(?:[/_](\d{1,4}))?\.?')
CELEX = re.compile(r'\b6(\d{4})(CJ|TJ|CO|CC|CN|TO)(\d{4})(?!\d)')
ROVID_DEF = re.compile(r'(\d{4})\.\s*évi\s*([IVXLCDM]+)\.\s*törvény\s*(?:\((?:a\s+)?(?:továbbiakban:?\s*)?([^()]{2,16}?)\)|\s-\s([A-ZÁÉÍÓÖŐÚÜŰ][^\s,;]{1,12}\.?(?:\s?tv\.)?))')
ROVID_HASZN = re.compile(r'\b([A-ZÁÉÍÓÖŐÚÜŰ][A-Za-zÁÉÍÓÖŐÚÜŰáéíóöőúüű]{0,9}\.(?:\s?tv\.)?)\s+(?:[IVXLC]+\.\s*[Ff]ejezet|\d+(?::\d+)?(?:/[A-Z])?[.\-, \d/A-Z:]{0,30}?§)')
NEM_ROVID = {'Az', 'A', 'Lásd', 'És', 'Ld.', 'Pl.', 'Vö.', 'Kúria', 'BH', 'EBH', 'EH', 'BDT', 'EBD', 'BK', 'PK', 'GK', 'KK', 'MK', 'KMK', 'Különös',
             'Általános', 'Rész', 'Könyv', 'Fejezet', 'Cím', 'Tanács', 'Európai', 'Bizottság', 'Jegyzőkönyv', 'Egyezmény', 'Charta', 'C', 'T'}


def eseti_kulcs(fajta, ev, kod):
    """EBH 2017.B.5 = EH 2017.02.B5; BH 2019.8.220 -> a sorszám az utolsó elem; EBH 2008/1/1815 = EH 2008.1815."""
    fajta = {'EBH': 'EH'}.get(fajta, fajta)
    reszek = [r for r in re.split(r'[./]', kod.strip('./')) if r]
    veg = reszek[-1]
    if veg.isdigit() and len(reszek) > 1 and re.fullmatch(r'[A-Z]', reszek[-2]):
        veg = reszek[-2] + veg
    return ('eseti', fajta, ev, veg.lstrip('0') or '0')


def je_rov(nev):
    """A jogegységi határozat vagy kollégiumi vélemény fajtájának rövidítése a megnevezésből: „1/2005. Büntető-polgári
    jogegységi határozat” -> BPJE, „1/2022. közigazgatási és polgári jogegységi határozat” -> KPJE, „1/2019. KMPJE” ->
    KMPJE, „1/2022. közigazgatási kollégiumi vélemény” -> KK, „LB PK-KK közös vélemény” -> PK-KK; más esetben None."""
    m = re.search(r'(?<![A-Z])(KMPJE|BKPJE|BPJE|KPJE|KMJE|BJE|PJE|KJE|MJE)(?![A-Z])', nev)
    if m:
        return m.group(1)
    m = re.search(r'(?<![A-Z])(PK-KK|KMK|KK|PK|BK|GK|MK)(?![A-Z])\.?\s*(?:közös\s+)?(?:vélemény|állásfoglalás)', nev)
    if m:
        return m.group(1)
    kis = nev.lower()
    betuk = ''.join(b for szo, b in (('közigazgatási', 'K'), ('munkaügyi', 'M'), ('büntető', 'B'), ('polgári', 'P'), ('gazdasági', 'G')) if szo in kis)
    if 'jogegységi' in kis and betuk:
        return betuk + 'JE'
    if 'kollégiumi vélemény' in kis:
        return {'K': 'KK', 'KM': 'KMK', 'P': 'PK', 'B': 'BK', 'G': 'GK', 'M': 'MK'}.get(betuk)
    return None


MASOD = re.compile(r'tárgyalási jelentés|fellebbezés|indítvány|összefoglal|ismertet|sajtóközlemény|kérelem|\(EN\)|_SUM\b|\b6\d{4}(?:CC|CN)\d{4}', re.I)


def torveny_fajl(f, kulcs, elso=''):
    """Igaz, ha a fájl maga a törvény (a neve vagy az első sora a törvény címével kezdődik, legfeljebb rövidítés-előtaggal:
    „Kit. - 2018. évi CXXV. törvény”), és nem olyan irat (AB határozat), amely a törvényt a címében említi."""
    for s in (re.sub(r'\.txt$', '', f), elso or ''):
        m = re.match(r'^(?:[^-\d][^-]{0,29}?\s-\s+)?(?:Magyarország\s+)?(\d{4})\.\s*évi\s+([IVXLCDM]+)\.', lapit(s).strip())
        if m and (m.group(1), m.group(2)) == tuple(kulcs[1:3]):
            return True
    return False


def valaszt(nev, talalt, kulcs=None, elsok=None):
    """Több egyező korpuszfájl közül a megnevezéshez illő, rangsorolva (az első a választott).
    - Törvény („tv” kulcs): csak az a fájl jöhet szóba, amelynek a neve vagy első sora a törvény címe; a törvényt a címében
      említő határozat vagy módosító törvény nem (egyetlen jelöltnél sem).
    - Jogegységi határozat, kollégiumi vélemény: a megnevezés fajtájához illő (1/2005. BJE és 1/2005. BPJE külön határozat).
    - A fájlnévben álló kulcs megelőzi az első sorban állót (T-18/10: a végzés fájlja, nem a rá hivatkozó fellebbezésé).
    - EUB-ügy több irata: az ítélet (vagy a fő dokumentum) megelőzi a tárgyalási jelentést, a fellebbezést, az indítványt,
      az összefoglalót, a CELEX szerinti indítványt (CN) és főtanácsnoki indítványt (CC); azonos rangúak között a rövidebb
      nevű az első."""
    talalt = sorted(talalt)
    elsok = elsok or {}
    if kulcs and kulcs[0] == 'tv':
        talalt = [f for f in talalt if torveny_fajl(f, kulcs, elsok.get(f, ''))]
    if len(talalt) < 2:
        return talalt
    rov = je_rov(nev)
    if rov:
        illo = [f for f in talalt if re.search(r'(?<![A-Z])%s(?![A-Z])' % re.escape(rov), f)]
        if illo:
            talalt = illo
            if len(talalt) < 2:
                return talalt

    def elsodleges(f):
        """Uniós jogi aktusnál: a fájl elsőként megnevezett aktusa a keresett (a „987/2009/EK rendelet a 883/2004/EK
        rendelet végrehajtásáról” fájl nem a 883/2004/EK rendeleté)."""
        if not kulcs or kulcs[0] != 'eu':
            return True
        for x in (re.sub(r'\.txt$', '', f).replace('_', '/'), elsok.get(f, '')):
            ks = [(a, k) for k, _, a, _ in hivatkozasok_hely(lapit(x)) if k[0] == 'eu']
            ks += [(m.start(), ('eu', str(int(m.group(2))), m.group(1))) for m in re.finditer(r'\b3(\d{4})[RLD](\d{4})\b', lapit(x))]
            if ks:
                return min(ks)[1] == kulcs
        return True

    def nevben(f):
        if not kulcs:
            return True
        n = re.sub(r'\.txt$', '', f)
        return kulcs in fajl_kulcsok(n) or kulcs in {k for k, _ in hivatkozasok(lapit(n.replace('_', '/')))}
    return sorted(talalt, key=lambda f: (not elsodleges(f), not nevben(f), bool(MASOD.search(f)), 'ítélet' not in f.lower() and 'ügy' not in f.lower(), len(f), f))


def tetelek(nyers):
    """A kiírás tételei az alapfelvetel.py szabálya szerint (egy helyen megírva: alapfelvetel.kiiras_reszek), a hivatkozó
    tétel megnevezéséhez. A „0” tétel a kiírás bevezetője; a tételcsoport bevezetőjének forrásai a csoport minden tételéhez."""
    sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
    import alapfelvetel
    tl, csoportok, elotte = alapfelvetel.kiiras_reszek(nyers)
    out = [{'n': 0, 'szoveg': lapit(elotte)}] if elotte.strip() else []
    for t in tl:
        out.append({'n': t['sorszam'], 'szoveg': lapit(t['szoveg'])})
        if csoportok.get(t['csoport']):
            out.append({'n': t['sorszam'], 'szoveg': lapit(csoportok[t['csoport']])})
    return out


def hivatkozasok_hely(szoveg):
    """[(kulcs, megnevezés, kezdet, vég)] – a kulcs alapján kötjük a korpuszfájlhoz; a hely a szövegbeli találat
    (az alapfelvetel.py maradékvizsgálata ebből tudja, mit használt fel a feloldás). Tartományos EUB-ügyszám
    („C-13-24/66”) tételenként egy kulcsot ad, azonos megnevezéssel és hellyel."""
    ki = []
    for m in SZAMEV.finditer(szoveg):
        tip = next(k for k, t in HAT_TIPUS if re.fullmatch(t, m.group(5)))
        ki.append((('szamev', m.group(1), m.group(2), tip), re.sub(r'\s+', ' ', m.group(0)).strip(), m.start(), m.end()))
    for m in KOLL.finditer(szoveg):
        koll, szam = (m.group(1), m.group(2)) if m.group(1) else (m.group(4), m.group(3)) if m.group(3) else (m.group(5)[:2], m.group(6))
        if re.search(r'/\d{4}', szoveg[m.end():m.end() + 6]) or szoveg[max(0, m.start() - 1):m.start()] == '/':
            continue
        ki.append((('koll', koll, szam), '%s %s.' % (koll, szam), m.start(), m.end()))
    for m in TORVENY.finditer(szoveg):
        ki.append((('tv', m.group(1), m.group(2)), '%s. évi %s. %s' % (m.group(1), m.group(2), 'törvény' if m.group(3) == 'törvény' else 'tvr.'), m.start(), m.end()))
    for m in ESETI.finditer(szoveg):
        ki.append((eseti_kulcs(m.group(1), m.group(2), m.group(3)), '%s %s.%s' % (m.group(1), m.group(2), m.group(3)), m.start(), m.end()))
    for m in EUX.finditer(szoveg):
        x, y = m.group(1), m.group(2)
        if ev_e(y):
            szam, ev = x, y
        elif ev_e(x) or len(x) == 2:
            szam, ev = y, x
        else:
            continue
        ev = ev if len(ev) == 4 else ('19' + ev if int(ev) > 50 else '20' + ev)
        ki.append((('eu', str(int(szam)), ev), m.group(0), m.start(), m.end()))
    for rx, f in ((EU3, lambda m: (m.group(3), m.group(2))), (EU4, lambda m: (m.group(2), m.group(1)))):
        for m in rx.finditer(szoveg):
            szam, ev = f(m)
            ki.append((('eu', str(int(szam)), ev), m.group(0), m.start(), m.end()))
    for m in EUB.finditer(szoveg):
        ev = m.group(4)[-2:]
        a = int(m.group(2))
        b = int(m.group(3)) if m.group(3) else a
        if not a <= b <= a + 50:
            b = a
        nev = '%s-%s%s/%s' % (m.group(1), m.group(2), ('-' + m.group(3)) if m.group(3) else '', m.group(4))
        for n in range(a, b + 1):
            ki.append((('eub', m.group(1), str(n), ev), nev, m.start(), m.end()))
    for m in EUBVEL.finditer(szoveg):
        for x in re.finditer(r'(\d{1,2})/(\d{2})', m.group(1)):
            ki.append((('eubvel', x.group(1), x.group(2)), '%s/%s. sz. vélemény' % (x.group(1), x.group(2)), m.start(), m.end()))
    for m in UGYSZAM.finditer(szoveg):
        ki.append((('ugyszam', m.group(1), m.group(3).replace('.', ''), m.group(4)), re.sub(r'\s+', ' ', m.group(0)).strip(), m.start(), m.end()))
    for m in CELEX.finditer(szoveg):
        ki.append((('eub', 'T' if m.group(2).startswith('T') else 'C', str(int(m.group(3))), m.group(1)[-2:]), m.group(0), m.start(), m.end()))
    for m in re.finditer(r'Alaptörvény', szoveg):
        ki.append((('nev', 'Alaptörvény'), 'Alaptörvény', m.start(), m.end()))
        break
    return ki


def hivatkozasok(szoveg):
    """[(kulcs, megnevezés)] – a kulcs alapján kötjük a korpuszfájlhoz."""
    return [(k, n) for k, n, _, _ in hivatkozasok_hely(szoveg)]


def fajl_kulcsok(nev):
    """A korpuszfájl nevéből képezhető kulcsok."""
    n = lapit(nev)
    k = set()
    m = re.match(r'^(\d{1,4}(?:[_/][A-Z])?)[_/](\d{4})(?!\d)(.*)$', n)
    if m:
        maradek = m.group(3).replace('_', ' ')
        tip = 'AB' if re.search(r'\bAB\b', maradek, re.I) else 'JE' if re.search(r'BJE|PJE|KJE|KPJE|MJE|BPJE|JEH|jogegységi', maradek) else \
              'VELEMENY' if re.search(r'vélemény|állásfoglalás', maradek) else 'RENDELET' if re.search(r'rendelet|utasítás', maradek) else '?'
        k.add(('szamev', m.group(1).replace('_', '/'), m.group(2), tip))
    m = re.match(r'^(\d{1,3})\.\s*(BK|PK|GK|KK|MK|KMK)\b', n) or re.match(r'^(?:)(BK|PK|GK|KK|MK|KMK)[ _](\d{1,3})\b', n)
    if m:
        a, b = m.group(1), m.group(2)
        k.add(('koll', b, a) if a.isdigit() else ('koll', a, b))
    for m in TORVENY.finditer(n):
        k.add(('tv', m.group(1), m.group(2)))
        break
    m = re.match(r'^(BH|EBH|EH|BDT|EBD|KGD|ÍH|KJD)\s?(\d{4})[./]?\s?([0-9A-Z]+(?:[./][0-9A-Z]+)*)', n)
    if m:
        k.add(eseti_kulcs(m.group(1), m.group(2), m.group(3)))
    for m in re.finditer(r'\b3(\d{4})[RLD](\d{4})\b', n):
        k.add(('eu', str(int(m.group(2))), m.group(1)))
    # CELEX-szám: 6ÉÉÉÉCJNNNN (ítélet), TJ (törvényszéki ítélet), CO/TO (végzés), CC (főtanácsnoki indítvány), CN (kérelem)
    for m in CELEX.finditer(n):
        k.add(('eub', 'T' if m.group(2).startswith('T') else 'C', str(int(m.group(3))), m.group(1)[-2:]))
    for m in re.finditer(r'\b([CT])-\s?(\d{1,4})[_/](\d{2})\b', n):
        k.add(('eub', m.group(1), str(int(m.group(2))), m.group(3)))
    # a régi (előtag nélküli) EUB-ügyszám a fájlnévben: „5_7-24_66 Kampffmeyer egyesített ügyek” = 5/66, 7/66 … 24/66
    m = re.match(r'^(\d{1,4}(?:[-_]\d{1,4})*)_(\d{2})\s.*\bügy', n)
    if m:
        for elem in m.group(1).split('_'):
            x = elem.split('-')
            a, b = int(x[0]), int(x[-1])
            for i in range(a, b + 1 if a <= b <= a + 50 else a + 1):
                k.add(('eub', 'C', str(i), m.group(2)))
    if n.startswith('Alaptörvény'):
        k.add(('nev', 'Alaptörvény'))
    m = re.match(r'^([A-ZÁÉÍÓÖŐÚÜŰ][^\s]{0,12}\.?(?:\s?tv\.)?)(?:\s*\(új\))?\s+-\s', n)
    if m:
        k.add(('rov', re.sub(r'\s', '', m.group(1)).rstrip('.').lower()))
    return k


def main():
    global GY
    GY = arg('gyoker', GY)
    kiiras = arg('kiiras', 'tetelsor/kiiras_2026.txt')
    korpusz = os.path.join(GY, arg('korpusz', 'korpusz'))
    ki = os.path.join(GY, arg('ki', 'jelentesek/korpusz_felmeres'))
    nyers = open(os.path.join(GY, kiiras), encoding='utf-8').read()
    T = tetelek(nyers)
    egesz = lapit(nyers)
    fajlok = sorted(nfc(f) for f in os.listdir(korpusz) if f.endswith('.txt'))
    FK, ELSO = {}, {}
    for f in fajlok:
        elso = next((l for l in open(os.path.join(korpusz, f), encoding='utf-8', errors='replace').read(3000).split('\n') if l.strip()), '')[:300]
        ELSO[f] = elso
        nev = re.sub(r'\.txt$', '', f)
        FK[f] = fajl_kulcsok(nev) | fajl_kulcsok(elso) | {k for k, _ in hivatkozasok(lapit(nev.replace('_', '/')))} | {k for k, _ in hivatkozasok(lapit(elso))}
    # rövidítések: a kiírás saját meghatározásai + a korpuszfájlok előtagjai
    rov_tv = {}
    for m in ROVID_DEF.finditer(egesz):
        r = (m.group(3) or m.group(4) or '').strip()
        if r and len(r) <= 14 and r[0].isupper():
            rov_tv[re.sub(r'\s', '', r).rstrip('.').lower()] = ('tv', m.group(1), m.group(2))
    forrasok = {}

    def felvesz(kulcs, nev, n, tobbi=()):
        f = forrasok.setdefault(kulcs, {'nev': nev, 'tetelek': set(), 'kulcsok': [kulcs] + [k for k in tobbi if k != kulcs]})
        f['tetelek'].add(n)

    for t in T:
        csop = {}
        for kulcs, nev, a, b in hivatkozasok_hely(t['szoveg']):
            csop.setdefault((nev, a, b), []).append(kulcs)     # tartományos EUB-ügyszám: egy sor
        for (nev, a, b), kulcsok in csop.items():
            felvesz(kulcsok[0], nev, t['n'], kulcsok)
        for m in ROVID_HASZN.finditer(t['szoveg']):
            r = m.group(1).strip()
            if r in NEM_ROVID or r.rstrip('.') in NEM_ROVID or re.fullmatch(r'[IVXLC]+', r.rstrip('.')):
                continue
            rk = re.sub(r'\s', '', r).rstrip('.').lower()
            if rk in rov_tv:
                felvesz(rov_tv[rk], '%s. évi %s. törvény (%s)' % (rov_tv[rk][1], rov_tv[rk][2], r), t['n'])
            else:
                felvesz(('rov', rk), r, t['n'])
    sorok, hasznalt = [], set()
    for kulcs, f in forrasok.items():
        talalt = [fn for fn, ks in FK.items() if any(k in ks for k in f.get('kulcsok', [kulcs]))]
        if not talalt and kulcs[0] == 'szamev':
            talalt = [fn for fn, ks in FK.items() if any(k[:3] == kulcs[:3] and k[3] == '?' for k in ks if k[0] == 'szamev')]
        if not talalt and kulcs[0] == 'rov':
            talalt = [fn for fn, ks in FK.items() if any(k[0] == 'rov' and (k[1].startswith(kulcs[1]) or kulcs[1].startswith(k[1])) for k in ks)]
        talalt = valaszt(f['nev'], talalt, kulcs, ELSO)
        hasznalt.update(talalt)
        sorok.append({'tipus': kulcs[0], 'kulcs': list(kulcs), 'nev': f['nev'], 'tetelek': sorted(f['tetelek']), 'fajl': talalt})
    rend = {'tv': 0, 'rov': 1, 'nev': 2, 'szamev': 3, 'koll': 4, 'eseti': 5, 'eu': 6, 'eub': 7, 'eubvel': 8, 'ugyszam': 9}
    sorok.sort(key=lambda s: (bool(s['fajl']), rend[s['tipus']], s['nev']))
    nem_hiv = [f for f in fajlok if f not in hasznalt]
    json.dump({'kiiras': kiiras, 'tetel': len({t['n'] for t in T if t['n']}), 'forrasok': sorok, 'nemHivatkozottFajl': nem_hiv},
              open(ki + '.json', 'w', encoding='utf-8'), ensure_ascii=False, indent=1)
    hi = [s for s in sorok if not s['fajl']]
    md = ['# Korpusz-felmérés a kiírásból', '', '- Kiírás: `%s`, tétel: %d; korpuszfájl: %d' % (kiiras, len({t['n'] for t in T if t['n']}), len(fajlok)),
          '- Megnevezett forrás: %d; megvan: %d; **hiányzik: %d**; a kiírás által nem megnevezett korpuszfájl: %d' % (len(sorok), len(sorok) - len(hi), len(hi), len(nem_hiv)),
          '- A „0” tétel a kiírás bevezetője (átfogóan előírt joganyag).', '', '## Hiányzik a korpuszból', '', '| Forrás | Típus | Tétel |', '|---|---|---|']
    md += ['| %s | %s | %s |' % (s['nev'], s['tipus'], ', '.join(map(str, s['tetelek']))) for s in hi]
    md += ['', '## Megvan', '', '| Forrás | Fájl | Tétel |', '|---|---|---|']
    md += ['| %s | %s | %s |' % (s['nev'], '; '.join(x[:70] for x in s['fajl']), ', '.join(map(str, s['tetelek']))) for s in sorok if s['fajl']]
    md += ['', '## Korpuszfájl, amelyet a kiírás nem nevez meg (ellenőrizendő: kell-e)', ''] + ['- ' + f for f in nem_hiv]
    open(ki + '.md', 'w', encoding='utf-8').write('\n'.join(md) + '\n')
    print('korpusz_felmeres: forrás %d, megvan %d, hiányzik %d, nem hivatkozott korpuszfájl %d' % (len(sorok), len(sorok) - len(hi), len(hi), len(nem_hiv)))


if __name__ == '__main__':
    main()
