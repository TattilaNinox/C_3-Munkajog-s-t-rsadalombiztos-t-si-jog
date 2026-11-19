#!/usr/bin/env python3
"""Felolvasószöveg (hangszöveg) készítése és a hanglefedettség ellenőrzése. A tároló gyökeréből:

    python3 tools/hangszoveg.py lefed            # minden tétel: mely bekezdések nincsenek felolvasva → jelentesek/hanglefedettseg.md
    python3 tools/hangszoveg.py lefed 61         # egy tétel részletesen
    python3 tools/hangszoveg.py szoveg 61 12-15  # a 61. tétel 12–15. blokkjának hangszövege a kimenetre
    python3 tools/hangszoveg.py potol 61         # a csonka darabok befejezése, majd a hiányzó részek új darabokba (chunk_NNN_k.txt) + _meta.json

A hangszöveg a meglévő darabok szokásait követi: a számok betűvel, „Ptk. 6:120. § (2) bekezdés” →
„Polgári Törvénykönyv hatodik könyv százhuszadik paragrafus kettes bekezdés”, a mondatvég „...”,
a dobozok bekezdései „Egyes. …”, pontjai „a.: …”, „bé.: …”, „bé a.: …”. A betűjel (pont, betűs §, betűs bekezdés) olvasata
(Attila döntése, 2026-11-18): a mássalhangzó a nevével („bé”), a magánhangzó önmaga, a jel végén „.:”-tal („a.: pont”,
„ötvenötödik per a.: paragrafus”, „egy a.: bekezdés”), lásd pontbetu(). Regressziós teszt: tools/hangszoveg_teszt.py. A doboz fejét a `kozos.FEJLEC` ismeri fel (ugyanaz a minta, amellyel
a `kozos.dobozok` dolgozik). A szkript hibával leáll, ha a szövegben számjegy
vagy § marad. A tétel szövegét nem módosítja; csak a `potol` ír, és csak új hangdarabot.
"""
import glob, json, os, re, sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import kozos

GYOKER = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
EGY = ['', 'egy', 'kettő', 'három', 'négy', 'öt', 'hat', 'hét', 'nyolc', 'kilenc']
TIZ = ['', 'tíz', 'húsz', 'harminc', 'negyven', 'ötven', 'hatvan', 'hetven', 'nyolcvan', 'kilencven']



_ROMAI = re.compile(r'm{0,3}(?:cm|cd|d?c{0,3})(?:xc|xl|l?x{0,3})(?:ix|iv|v?i{0,3})')


def romai_token(x):
    """Római számnak látszó token a lefedettség-vizsgálat ötszavas ablakaihoz: a csak i, v, x, l betűből álló
    token (a korábbi szűrő), és a legalább hárombetűs, szabályos római szám c, d, m betűvel is (pl. „xcii”) –
    ezeket a felolvasószöveg sorszámnévre cseréli, ezért az ablakból ki kell hagyni őket. A kétbetűs alakok
    („mi”, „dc”) szavak vagy betűjelek lehetnek, azok maradnak."""
    x = x.lower()
    return bool(re.fullmatch(r'[ivxl]+', x)) or (len(x) >= 3 and bool(x) and bool(_ROMAI.fullmatch(x)))

def szam(n):
    """Tőszámnév betűvel (0–999 999)."""
    n = int(n)
    if n == 0:
        return 'nulla'
    def szaz_alatt(k, elol=False):
        t, e = divmod(k, 10)
        if t == 1 and e:
            return 'tizen' + EGY[e]
        if t == 2 and e:
            return 'huszon' + EGY[e]
        return TIZ[t] + EGY[e]
    def ezer_alatt(k):
        s, m = divmod(k, 100)
        out = ''
        if s:
            out += ('' if s == 1 else ('két' if s == 2 else EGY[s])) + 'száz'
        return out + szaz_alatt(m)
    e, m = divmod(n, 1000)
    if not e:
        return ezer_alatt(m)
    elo = ('' if e == 1 else ('két' if e == 2 else ezer_alatt(e))) + 'ezer'
    if not m:
        return elo
    return elo + ('-' if n > 2000 else '') + ezer_alatt(m)


SOR_VEG = [('kettő', 'kettedik'), ('három', 'harmadik'), ('négy', 'negyedik'), ('egy', 'egyedik'), ('öt', 'ötödik'),
           ('hat', 'hatodik'), ('hét', 'hetedik'), ('nyolc', 'nyolcadik'), ('kilencven', 'kilencvenedik'),
           ('kilenc', 'kilencedik'), ('tíz', 'tizedik'), ('húsz', 'huszadik'), ('harminc', 'harmincadik'),
           ('negyven', 'negyvenedik'), ('ötven', 'ötvenedik'), ('hatvan', 'hatvanadik'), ('hetven', 'hetvenedik'),
           ('nyolcvan', 'nyolcvanadik'), ('száz', 'századik'), ('ezer', 'ezredik')]
ES_VEG = [('kettő', 'kettes'), ('három', 'hármas'), ('négy', 'négyes'), ('egy', 'egyes'), ('öt', 'ötös'), ('hat', 'hatos'),
          ('hét', 'hetes'), ('nyolc', 'nyolcas'), ('kilencven', 'kilencvenes'), ('kilenc', 'kilences'), ('tíz', 'tízes'),
          ('húsz', 'húszas'), ('harminc', 'harmincas'), ('negyven', 'negyvenes'), ('ötven', 'ötvenes'),
          ('hatvan', 'hatvanas'), ('hetven', 'hetvenes'), ('nyolcvan', 'nyolcvanas'), ('száz', 'százas'), ('ezer', 'ezres')]


def _vegcsere(n, tabla):
    s = szam(n)
    for a, b in sorted(tabla, key=lambda x: -len(x[0])):
        if s.endswith(a):
            return s[:-len(a)] + b
    raise ValueError(n)


def sorszam(n):
    n = int(n)
    return {1: 'első', 2: 'második'}.get(n) or _vegcsere(n, SOR_VEG)


def es(n):
    return _vegcsere(int(n), ES_VEG)


BETU = {'a': 'a', 'b': 'bé', 'c': 'cé', 'd': 'dé', 'e': 'e', 'f': 'ef', 'g': 'gé', 'h': 'há', 'i': 'i', 'j': 'jé', 'k': 'ká',
        'l': 'el', 'm': 'em', 'n': 'en', 'o': 'o', 'p': 'pé', 'q': 'kú', 'r': 'er', 's': 'es', 't': 'té', 'u': 'u', 'v': 'vé',
        'w': 'dupla vé', 'x': 'iksz', 'y': 'ipszilon', 'z': 'zé'}
MGH = 'aeiou'
KOZ = '\x02'        # a kétbetűs jel betűi között: a névelő-igazítás ne vegye az „a” betűt névelőnek; a hangra végén szóköz


def pontbetu(x):
    """Betűjel (pont, betűs §, betűs bekezdés) felolvasott alakja – Attila döntése (2026-11-18): a mássalhangzó a nevével
    („b” → „bé”), a magánhangzó önmaga; a jel végén álló magánhangzó után „.:” áll („a.:”, „e.:”), mert a felolvasó a
    csupasz „a”-t „á”-nak mondaná. Többbetűs jel (Attila döntése, 2026-11-18): a betűk vesszővel, minden magánhangzó „.:” alakban:
    „ba” → „bé, a.:”, „ac” → „a.:, cé”, „aa” → „a.:, a.:”."""
    x = x.lower()
    return (',' + KOZ).join(BETU[c] + ('.:' if c in MGH else '') for c in x)


def sor_pontbetu(x):
    """A doboz sor eleji pontjele: „a.: ”, „bé.: ”, „bé, a.: ”, „a.:, cé.: ”."""
    p = pontbetu(x)
    return p + ('' if p.endswith('.:') else '.:') + ' '


HONAP = ['január', 'február', 'március', 'április', 'május', 'június', 'július', 'augusztus', 'szeptember', 'október',
         'november', 'december']
ROMAI = {'I': 1, 'V': 5, 'X': 10, 'L': 50, 'C': 100}
RSZ = r'(?:C{0,3})(?:XC|XL|L?X{0,3})(?:IX|IV|V?I{0,3})'          # szabályos római szám (1–399)


def romai(s):
    t = 0
    for i, c in enumerate(s):
        v = ROMAI[c]
        t += -v if i + 1 < len(s) and ROMAI[s[i + 1]] > v else v
    return t


def napi(n):
    """„28.” → „huszonnyolcadikai”, „1.” → „elsejei” (a zárójeles dátum napja)."""
    d = sorszam(n)
    return 'elsejei' if str(n) == '1' else d + ('ai' if d.endswith('adik') or d.endswith('odik') else 'ei')


_K = kozos.beallitas().get('kiejtes') or {}
TORVENY = [tuple(x) for x in (_K.get('torveny') or [])]  # (minta, névelő nélküli alak); A/1: Ptk. → Polgári Törvénykönyv
ROVID = [tuple(x) for x in (_K.get('rovid') or [])]
LATIN = [tuple(x) for x in (_K.get('latin') or [])]
PER = lambda b: ' per ' + pontbetu(b) if b else ''
PAR = r'(\d+)(?::(\d+))?(?:/([A-Z]))?'
PARX = r'\d+(?::\d+)?(?:/[A-Z])?'                                  # ugyanaz csoport nélkül (felsoroláshoz)
KOTO = r'(?:,\s*|\s*[–-]\s*|\s+(?:és|vagy|illetve|valamint)\s+(?:az?\s+)?)'   # felsorolás tagjai között
KISBETU = 'a-záéíóöőúüű'
NAGYBETU = 'A-ZÁÉÍÓÖŐÚÜŰ'


def par_szoveg(a, b, betu):
    if b is not None:
        return f'{sorszam(a)} könyv {sorszam(b)}{PER(betu)} paragrafus'
    return f'{sorszam(a)}{PER(betu)} paragrafus'


def par_lista(m):
    """§-felsorolás: „6:77., 6:80. §” → „hatodik könyv hetvenhetedik, nyolcvanadik paragrafus”; azonos könyv csak egyszer."""
    tagok = re.split(r'(' + KOTO + r')', m.group(1))
    ki = []; konyv = None
    for i, t in enumerate(tagok):
        if i % 2:
            ki.append(t); continue
        g = re.fullmatch(r'(\d+)(?::(\d+))?(?:/([A-Z]))?\.?', t.strip())
        a, b, c = g.groups()
        if b is not None:
            ki.append((f'{sorszam(a)} könyv ' if a != konyv else '') + sorszam(b) + PER(c)); konyv = a
        else:
            ki.append(sorszam(a) + PER(c))
    return ''.join(ki) + ' paragrafus'


def bek_szam(x):
    """Bekezdésszám: „1” → „egyes”, „1a” → „egy a.:” (betűs bekezdés), „2b” → „kettő bé”."""
    g = re.fullmatch(r'(\d+)([a-z]?)', x)
    return es(g.group(1)) if not g.group(2) else szam(g.group(1)) + ' ' + pontbetu(g.group(2))


def bekezdesek(s):
    def lista(m):
        return re.sub(r'\((\d+[a-z]?)\)', lambda x: bek_szam(x.group(1)), m.group(0))
    s = re.sub(r'(?:\(\d+[a-z]?\)' + KOTO + r'?)+(?=\s*bekezd)', lista, s)
    return s


# a „§ (1)”, „§ (1)–(3)”, „§ (1), (3)” a „bekezdés” szó nélkül: „egyes bekezdés”, „egyes–hármas bekezdés”
# birtokos ismétlés (*+) nincs: a 3.11 előtti Python (Attila gépe) nem ismeri; a rövidebb illeszkedést előretekintés zárja ki
PAR_BEK = re.compile(r'(paragrafus(?:-?[a-záéíóöőúüű]+)?) (\(\d+[a-z]?\)(?:' + KOTO + r'\(\d+[a-z]?\))*)(?!' + KOTO + r'\(\d+[a-z]?\))(?!\s*bekezd)')
# a § vagy bekezdés után álló, „pont” szó nélküli pontbetű: „§ b)” → „bé pont”, „(1) d), e)” → „dé, e.: pont”
BEK_PONT = re.compile(r'\b(paragrafus|bekezdés) ((?:[a-z]{1,2}\)' + KOTO + r'(?=[a-z]{1,2}\)))*[a-z]{1,2}\))(?!' + KOTO + r'[a-z]{1,2}\))(?!\s*(?:pont|alpont))')
# névelő a betűvel kiírt szám, betűjel előtt: a kiejtett alak első hangja dönt
SZAM_MGH = r'(?:egy|első|öt|ezer|a\.:|e\.:|i\.:|o\.:|el|em|en|ef|er|es|iksz|ipszilon)'
SZAM_MSH = (r'(?:kettes|kettedik|hármas|harmadik|négyes|negyedik|hatos|hatodik|hetes|hetedik|nyolcas|nyolcadik|kilences|kilencedik|'
            r'tízes|tizedik|húszas|huszadik|második|bé|cé|dé|gé|há|jé|ká|pé|té|vé|zé)')
SZAM_MSH_TO = r'(?:tizen|huszon|harminc|negyven|hatvan|hetven|nyolcvan|kilencven|száz|kétszáz|háromszáz|négyszáz|hatszáz|hétszáz|nyolcszáz|kilencszáz|kétezer|háromezer)'


def nevelo(s):
    s = re.sub(r'(?<![\w.-])([Aa]) (?=' + SZAM_MGH + r'(?:[\w-]*)(?![\w]))', r'\1z ', s)
    s = re.sub(r'(?<![\w.-])([Aa])z (?=(?:' + SZAM_MSH + r'|' + SZAM_MSH_TO + r'[\w-]*)(?![\w-]))', r'\1 ', s)
    return s


def hangra(szoveg, doboz=False):
    """Egy blokk (bekezdés, címsor vagy doboz) hangszövege."""
    kiejtes_kell()
    s = szoveg
    # nagybetűs címsorban álló fejezethivatkozás, pl. „(SZJT. XI. FEJEZET)” (központi chat, 2026-11-15)
    s = re.sub(r'\(SZJT\. ([IVXL]+)\. FEJEZET\)', lambda m: '(A SZERZŐI JOGI TÖRVÉNY ' + sorszam(romai(m.group(1))).upper() + ' FEJEZETE)', s)
    s = re.sub(r'(\d{4})\. évi (' + RSZ + r')\. törvén', lambda m: f'{szam(m.group(1))} évi {sorszam(romai(m.group(2)))} törvén', s)
    s = re.sub(r'(\d{4})\. ÉVI (' + RSZ + r')\. TÖRVÉN', lambda m: f'{szam(m.group(1))} ÉVI {sorszam(romai(m.group(2)))} TÖRVÉN'.upper(), s)
    # a teljes név után zárójelben megismételt rövidítés nem kettőződik: „… törvény (Csvt.)”, „(a továbbiakban: Ptk.)”
    s = re.sub(r'((?:törvén|Törvénykönyv)[a-záéíóöőúüű]*)\s*\((?:a továbbiakban:\s*)?[A-ZÁÉ][a-záéíóöőúüű]{1,6}\.(?:\s?tv\.|\d\.)?\)', r'\1', s)
    s = re.sub(r'\bMódtv\.2\.', 'második módosító törvény', s)
    # a Kúria jogegységi panasztanácsának határozatszáma (a 31. tétel alakja): „Jpe.I.60.015/2021/15.”
    s = re.sub(r'\bJpe\.(' + RSZ + r')\.(\d+)\.(0*)(\d+)/(\d{4})/(\d+)\.?',
               lambda m: f'jé-pé-e {es(romai(m.group(1)))} {szam(m.group(2))} pont ' + 'nulla ' * len(m.group(3))
               + f'{szam(m.group(4))} per {szam(m.group(5))} per {sorszam(m.group(6))}', s)
    # sor eleji bekezdés- és pontjelek (dobozban)
    s = re.sub(r'(?m)^\((\d+)([a-z])\)[^\S\n]+', lambda m: f'{szam(m.group(1)).capitalize()} {pontbetu(m.group(2))} bekezdés. ', s)
    s = re.sub(r'(?m)^\((\d+)\)[^\S\n]+', lambda m: es(m.group(1)).capitalize() + '. ', s)
    s = re.sub(r'(?m)^([a-z]{1,2})\)[^\S\n]+', lambda m: sor_pontbetu(m.group(1)), s)
    # szöveg nélküli (üres) bekezdés- vagy pontjel a sor végén
    s = re.sub(r'(?m)^\((\d+)\)$', lambda m: es(m.group(1)).capitalize() + '.', s)
    s = re.sub(r'(?m)^([a-z]{1,2})\)$', lambda m: sor_pontbetu(m.group(1)).rstrip(), s)
    s = re.sub(r'(?m)^([A-Z])\)[^\S\n]+(?=[' + NAGYBETU + r']{2})', lambda m: sor_pontbetu(m.group(1)), s)   # „A) SZERZŐDÉS…” címsor
    s = re.sub(r'(?m)^(\d+)\.[^\S\n]+(?=[a-záéíóöőúüű])', lambda m: sorszam(m.group(1)) + ' pont: ', s)
    # címsorok
    s = re.sub(r'(?m)^(' + RSZ + r')\.[^\S\n]+(?=[A-ZÁÉÍÓÖŐÚÜŰ])', lambda m: sorszam(romai(m.group(1))).capitalize() + '. ' if m.group(1) else m.group(0), s)
    s = re.sub(r'(?m)^(\d+)\.[^\S\n]+(?=[A-ZÁÉÍÓÖŐÚÜŰ])', lambda m: es(m.group(1)).capitalize() + '. ', s)
    # bírósági iránymutatások
    def iranymutatas(m):
        szam_, ev, ho, nap_, faj = m.groups()
        if ho:
            koz = f' ({HONAP[romai(ho) - 1]} {napi(nap_)})'
        else:
            koz = ' számú'
        return f'{szam(szam_)} per {szam(ev)}{koz} ' + {'PK vélemény': 'pé-ká vélemény', 'PJE': 'Polgári jogegységi határozat',
               'KPJE': 'Közigazgatási-polgári jogegységi határozat',
               'BKMPJE': 'büntető-közigazgatási-munkaügyi-polgári jogegységi határozat'}[faj]
    s = re.sub(r'(\d+)/(\d{4})\.(?:\s*\(([IVX]+)\.\s*(\d+)\.\))?\s*(PK vélemény|PJE|KPJE|BKMPJE)(?: határozat)?', iranymutatas, s)
    PKGK = {'PK': 'pé-ká', 'GK': 'gé-ká'}
    RAG_HATSO = {'et': 't', 'at': 't', 't': 't', 'ben': 'ban', 'ban': 'ban', 'nek': 'nak', 'nak': 'nak', 're': 'ra', 'ra': 'ra',
                 'hez': 'hoz', 'hoz': 'hoz', 'ből': 'ból', 'ból': 'ból', 'től': 'tól', 'tól': 'tól', 'ről': 'ról', 'ról': 'ról',
                 'vel': 'sal', 'val': 'sal', 'ig': 'ig'}
    # toldalékos alak: „PK 40.-et” → „pé-ká negyvenes számú állásfoglalást”
    s = re.sub(r'\b(PK|GK)\s*(\d+)\.-([a-záéíóöőúüű]+)\b',
               lambda m: f'{PKGK[m.group(1)]} {es(m.group(2))} számú állásfoglalás' + RAG_HATSO.get(m.group(3), m.group(3)), s)
    # mondatvég: „GK 54. A Gazdasági Kollégium …” – a szám utáni nagybetűs folytatás új mondat
    s = re.sub(r'\b(PK|GK)\s*(\d+)\.(?=\s+[' + NAGYBETU + r'](?:\s|[' + KISBETU + r']))',
               lambda m: f'{PKGK[m.group(1)]} {es(m.group(2))} számú állásfoglalás.', s)
    s = re.sub(r'\b(PK|GK)\s*(\d+)\.(?:\s*(?:számú|SZÁMÚ))?', lambda m: PKGK[m.group(1)] + ' ' + es(m.group(2)) + ' számú', s)
    s = re.sub(r'\b([IVX]+)\.\s*számú Polgári Elvi Döntés', lambda m: es(romai(m.group(1))) + ' számú Polgári Elvi Döntés', s)
    # dátumok (a §-felsorolás előtt: „2014. március 15., 8:4. §”)
    HN = '|'.join(HONAP)
    def nap(m):
        ev, ho, n, rag = m.group(1), m.group(2), m.group(3), (m.group(4) or '')
        d = sorszam(n)
        mely = d.endswith('adik') or d.endswith('odik')
        if n == '1':
            to, mely = 'elsej', False
        else:
            to = d
        kul = {'n': ('án', 'én'), 'tól': ('ától', 'étől'), 'ig': ('áig', 'éig'), 'i': ('ai', 'ei'), 'val': ('ával', 'ével'), '': ('a', 'e'),
               'ra': ('ára', 'ére'), 'hez': ('ához', 'éhez')}
        oszt = {'án': 'n', 'én': 'n', 'jén': 'n', 'től': 'tól', 'tól': 'tól', 'jétől': 'tól', 'ig': 'ig', 'jéig': 'ig', 'i': 'i', 'ei': 'i', 'ai': 'i',
                'jei': 'i', 'ával': 'val', 'ével': 'val', 'a': '', 'e': '', 'je': '', '': '', 'ára': 'ra', 'ére': 'ra', 'jére': 'ra'}.get(rag)
        if oszt is None:
            return m.group(0)
        return (szam(ev) + ' ' if ev else '') + ho + ' ' + to + kul[oszt][0 if mely else 1]
    s = re.sub(r'(?:(\d{4})\. )?(' + HN + r') (\d{1,2})\.?(?:-([a-záéíóöőúüű]+))?', nap, s)
    # jogszabályhelyek
    def tartomany(m):
        a1, b1, c1, a2, b2, c2 = m.groups()
        if b1 is not None:
            v = f'{sorszam(a1)} könyv {sorszam(b1)}{PER(c1)}–' + (f'{sorszam(b2)}{PER(c2)}' if b2 is not None else f'{sorszam(a2)}{PER(c2)}')
        else:
            v = f'{sorszam(a1)}{PER(c1)}–{sorszam(a2)}{PER(c2)}'
        return v + ' paragrafus'
    s = re.sub(PAR + r'\.?\s*(?:§\s*)?[–-]\s*' + PAR + r'\.\s?§', tartomany, s)
    # felsorolás: „6:77., 6:80. §”, „4:99., 4:100., 4:101. és 4:103. §”, „35., 36. és 39. §”
    s = re.sub(r'(?<![\d:/])(' + PARX + r'\.(?:(?:,\s*|\s+(?:és|vagy|illetve|valamint)\s+(?:az?\s+)?)' + PARX + r'\.)+)\s?§', par_lista, s)
    s = re.sub(PAR + r'\.\s?§', lambda m: par_szoveg(m.group(1), m.group(2), m.group(3)), s)
    s = re.sub(r'paragrafus-(?:[aáeé]\b|j[ae]\b)', 'paragrafusa', s)
    s = re.sub(r'paragrafus-([a-záéíóöőúüű]+)', lambda m: 'paragrafus' + {'ának': 'ának', 'ában': 'ában', 'ához': 'ához', 'át': 'át', 'ából': 'ából',
               'ára': 'ára', 'ai': 'ai', 'aiban': 'aiban', 'ban': 'ban', 'ra': 'ra', 'hoz': 'hoz', 'ból': 'ból', 'nak': 'nak', 'ával': 'ával',
               'ától': 'ától', 'áig': 'áig', 'ánál': 'ánál', 'áról': 'áról', 'ain': 'ain', 'ait': 'ait'}.get(m.group(1), m.group(1)), s)
    s = bekezdesek(s)
    s = PAR_BEK.sub(lambda m: m.group(1) + ' ' + re.sub(r'\((\d+[a-z]?)\)', lambda x: bek_szam(x.group(1)), m.group(2)) + ' bekezdés', s)
    s = re.sub(r'\((\d+)\)(?=\s*(?:[–-]|és|,)\s*\(?\d*\)?\s*bekezd)', lambda m: es(m.group(1)), s)
    s = BEK_PONT.sub(lambda m: m.group(1) + ' ' + re.sub(r'\b([a-z]{1,2})\)', lambda x: pontbetu(x.group(1)), m.group(2)) + ' pont', s)
    s = re.sub(r'\b([a-z]{1,2})\)(?=\s*(?:pont|alpont|[–-])|,?\s+(?:(?:és|vagy|illetve|valamint)\s+)?(?:az? )?[a-z]{1,2}\))', lambda m: pontbetu(m.group(1)), s)
    s = re.sub(r'\b([a-z])\)[–-]([a-z])\)', lambda m: pontbetu(m.group(1)) + '–' + pontbetu(m.group(2)), s)
    s = re.sub(r'\b(' + RSZ + r')/(\d+)\.(?=\s|[,;)])', lambda m: sorszam(romai(m.group(1))) + ' per ' + sorszam(m.group(2)) if m.group(1) else m.group(0), s)
    s = re.sub(r'\b(\d+)[–-](\d+)\.\s*(?=pont)', lambda m: sorszam(m.group(1)) + '–' + sorszam(m.group(2)) + ' ', s)
    s = re.sub(r'\b(\d+)\.\s*(?=pont)', lambda m: sorszam(m.group(1)) + ' ', s)
    # római szám: tagolási egység előtt, a mondat belsejében (kisbetűs folytatás, vessző, pontosvessző, zárójel előtt) is
    s = re.sub(r'\b(' + RSZ + r')/([A-Z])\.(?=\s|[,;)])', lambda m: sorszam(romai(m.group(1))) + ' per ' + pontbetu(m.group(2)) if m.group(1) else m.group(0), s)
    s = re.sub(r'\b(' + RSZ + r')[–-](' + RSZ + r')\.(?=\s*(?:pont|főpont|alpont|[Ff]ejezet|[Cc]ím|[Rr]ész|[Kk]önyv|cikk))',
               lambda m: sorszam(romai(m.group(1))) + '–' + sorszam(romai(m.group(2))) if m.group(1) and m.group(2) else m.group(0), s)
    s = re.sub(r'\b(' + RSZ + r')\.(?=\s*(?:(?:és|vagy|,|[–-])\s*(?:az? )?' + RSZ + r'\.\s*)*(?:pont|főpont|alpont|[Ff]ejezet|[Cc]ím|[Kk]önyv|[Rr]ész|cikk))',
               lambda m: sorszam(romai(m.group(1))) if m.group(1) else m.group(0), s)
    s = re.sub(r'\b(' + RSZ + r')\.(?=\s+(?:TÖRVÉN|FEJEZET|CÍM|KÖNYV|RÉSZ|CIKK))', lambda m: sorszam(romai(m.group(1))).upper() if m.group(1) else m.group(0), s)
    s = re.sub(r'(?<![\w.])(' + RSZ + r')\.(?=\s+[' + KISBETU + r']|[,;)])', lambda m: sorszam(romai(m.group(1))) if m.group(1) else m.group(0), s)
    # a szövegközi felsorolás betűjele („a hatóság a) a végrehajtási jog, b) a jelzálogjog …”, „a b) eset, a c) eset”):
    # ha a blokkban legalább két különböző betűjel áll így
    BELSO = r'(?<=[\s(])([a-z])\) (?=[' + KISBETU + r'])'
    if len(set(re.findall(BELSO, s))) >= 2:
        s = re.sub(BELSO, lambda m: pontbetu(m.group(1)) + ' ', s)
    # sorszámnév után álló pontbetű a tagolási hivatkozásban: „(II/3. b))” → „(második per harmadik bé)”
    s = re.sub(r'(?:(?<=dik )|(?<=első ))([a-z]{1,2})\)', lambda m: pontbetu(m.group(1)), s)
    # az Alaptörvény betűvel jelölt cikke: „L) cikk” → „el cikk”
    s = re.sub(r'\b([A-Z])\)(?=\s*(?:(?:és|vagy|,)\s*(?:az?\s+)?(?:[A-Z]\)|' + RSZ + r'\.|[a-záéíóöőúüű]+)\s*)*cikk)', lambda m: pontbetu(m.group(1)), s)
    # jogszabálynevek
    RAG = {'ban': 'ben', 'ben': 'ben', 'ba': 'be', 'be': 'be', 'nak': 'nek', 'nek': 'nek', 'ból': 'ből', 'ből': 'ből', 'ra': 're', 're': 're',
           'tól': 'től', 'től': 'től', 'ról': 'ről', 'ről': 'ről', 'hoz': 'höz', 'hez': 'höz', 'val': 'vel', 'vel': 'vel', 't': 'et', 'et': 'et'}
    s = re.sub(r'\bPtk\.-([a-záéíóöőúüű]+)', lambda m: 'Polgári Törvénykönyv' + RAG.get(m.group(1), m.group(1)), s)
    s = re.sub(r'\bPTK\.-([A-ZÁÉÍÓÖŐÚÜŰ]+)', lambda m: 'POLGÁRI TÖRVÉNYKÖNYV' + RAG.get(m.group(1).lower(), m.group(1).lower()).upper(), s)
    s = re.sub(r'\bPTK\.', 'POLGÁRI TÖRVÉNYKÖNYV', s)
    for rx, nev in TORVENY:
        s = re.sub(r'\b([Aa])z? ' + rx, lambda m: m.group(1) + ('z ' if nev[0].lower() in 'aáeéiíoóöőuúüű' else ' ') + nev, s)
        s = re.sub(rx, nev, s)
    s = re.sub(r'törvény-(t|et|ben|be|nek|re|ből|től|ről|hez|höz|nél|ig)\b', r'törvény\1', s)
    s = re.sub(r'törvény-(?:vel|nyel)\b', 'törvénnyel', s)
    s = re.sub(r'(\d{4})\. évi ([IVXLC]+)\. törvén', lambda m: f'{szam(m.group(1))} évi {sorszam(romai(m.group(2)))} törvén', s)
    s = re.sub(r'(\d+)/(\d{4})\.\s*(?:\(([IVX]+)\. (\d+)\.\)\s*)?(Korm\.\s*rendelet|KORM\.\s*RENDELET)',
               lambda m: f'{szam(m.group(1))} per {szam(m.group(2))} ' + ('kormányrendelet' if m.group(5)[0] == 'K' and m.group(5)[1] == 'o' else 'KORMÁNYRENDELET'), s)
    s = re.sub(r'(\d+)/(\d+)/(EGK|EK|EU)', lambda m: f'{szam(m.group(1))} per {szam(m.group(2))} per ' + {'EGK': 'e-gé-ká', 'EK': 'e-ká', 'EU': 'e-u'}[m.group(3)], s)
    # zárójeles dátum: „(II. 18.)” → „(február tizennyolcadikai)”
    s = re.sub(r'(?<=\d\d\d\d\. )\((' + RSZ + r')\.\s*(\d{1,2})\.\)', lambda m: f'({HONAP[romai(m.group(1)) - 1]} {napi(m.group(2))})' if m.group(1) and romai(m.group(1)) <= 12 else m.group(0), s)
    # határozat- és jogszabályszám: „10/2025. jogegységi határozata” → „tíz per kétezer-huszonöt számú …”; a „/” jele „per”
    s = re.sub(r'(\d+)/(\d{4})\.(\s+)(?!számú)(?=[' + KISBETU + r']|Polgári|Közigazgatási)', lambda m: f'{szam(m.group(1))} per {szam(m.group(2))} számú' + m.group(3), s)
    s = re.sub(r'(\d+)/(\d{4})\.(?=\s+(?:számú|\())', lambda m: f'{szam(m.group(1))} per {szam(m.group(2))}', s)
    s = re.sub(r'(\d+)/(\d+)(?:-([a-záéíóöőúüű]+))?', lambda m: f'{szam(m.group(1))} per {szam(m.group(2))}' + (m.group(3) or ''), s)
    # százalék, számok (a dátum a jogszabályhelyek előtt)
    s = re.sub(r'(\d{4})-(ben|ban|től|tól|ig|es|as|ös|ra|re)\b', lambda m: szam(m.group(1)) + m.group(2), s)
    s = re.sub(r'(\d{4})\.(?= évi| év\b| ÉVI)', lambda m: szam(m.group(1)), s)
    s = re.sub(r'(\d+)\s?%(?:-([a-záéíóöőúüű]+))?', lambda m: szam(m.group(1)) + ' százalék' + (m.group(2) or ''), s)
    s = re.sub(r'(\d{1,3})[  ](\d{3})\b', r'\1\2', s)
    # sorszámnév: tartomány és egyes szám kisbetűs folytatás, vessző, pontosvessző, zárójel előtt („a 69., a 70. és”, „a 76.)”, „82–83.”)
    s = re.sub(r'\b(\d+)[–-](\d+)\.(?=\s+[' + KISBETU + r']|[,;)])', lambda m: sorszam(m.group(1)) + '–' + sorszam(m.group(2)), s)
    s = re.sub(r'\b(\d+):(\d+)(?:/([A-Z]))?\.(?=\s+[' + KISBETU + r']|[,;)])', lambda m: par_szoveg(*m.groups())[:-len(' paragrafus')], s)
    s = re.sub(r'\b(\d+):(\d+)(?:/([A-Z]))?(?=\.)', lambda m: par_szoveg(*m.groups())[:-len(' paragrafus')], s)
    s = re.sub(r'\b(\d+)\.(?=\s+[' + KISBETU + r']|[,;)])', lambda m: sorszam(m.group(1)), s)
    s = re.sub(r'\b(\d+)-(es|as|ös)\b', lambda m: es(m.group(1)), s)
    s = re.sub(r'\b(\d+)(?:-([a-záéíóöőúüű]+))?', lambda m: szam(m.group(1)) + (m.group(2) or ''), s)
    for rx, v in ROVID:
        s = re.sub(rx, v, s)
    for a, b in LATIN:
        s = re.sub(r'\b' + a + r'\b', b, s, flags=re.I)
    s = s.replace('§', 'paragrafus')
    # szám nélkül álló, ragozott vagy többes § („a következő §-ok”, „külön §-ban”): a rag kötőjel nélkül, egybeírva
    s = re.sub(r'paragrafus-(?:[aáeé]\b|j[ae]\b)', 'paragrafusa', s)
    s = re.sub(r'paragrafus-(?=[a-záéíóöőúüű])', 'paragrafus', s)
    s = nevelo(s).replace(KOZ, ' ')
    # szögletes zárójel a folyó szövegben (a hangmodell a szögletes zárójelet hangcímkének veszi, a tartalmát nem olvassa fel):
    # a sort kitöltő §-cím önálló mondat, a szövegközi betoldás kerek zárójelbe kerül
    s = re.sub(r'(?m)^\[([^\]\n]+)\]$', r'\1.', s)
    s = re.sub(r'\[([^\]\n]*)\]', r'(\1)', s)
    # mondatvég
    s = re.sub(r'(?<![.\d])\.(?=\s|$|[)”"])', '...', s)
    s = re.sub(r'(?m)^(Egyes|Kettes|Hármas|Négyes|Ötös|Hatos|Hetes|Nyolcas|Kilences|Tízes|[A-ZÁÉÍÓÖŐÚÜŰ][a-záéíóöőúüű]*(?:dik|ső|es|as|ös))\.\.\. ', r'\1. ', s)
    s = re.sub(r'(?m)^([A-ZÁÉÍÓÖŐÚÜŰ][a-záéíóöőúüű]* (?:[a-záéíóöőúüű]+ )?[a-záéíóöőúüű]+(?:\.:)? bekezdés)\.\.\. ', r'\1. ', s)
    return s


def hianyos(s):
    return re.findall(r'.{0,25}(?:\d|§).{0,15}', s)


# ---------- lefedettség ----------
KIZART = set(_K.get('kizart') or [])


def kiejtes_kell():
    """Ha nincs kiejtési tábla, stdout-ra az üzenet, kilépés 2-vel, fájlírás nélkül."""
    k = kozos.beallitas().get('kiejtes') or {}
    if not (k.get('torveny') or k.get('rovid') or k.get('latin') or k.get('kizart')):
        print('Nincs kiejtési tábla a beállításban (kiejtes): a felolvasószöveg nem gyártható.')
        raise SystemExit(2)


def tokenek(s):
    return re.findall(r'[a-záéíóöőúüű]+|\d+', s.lower())


def tetel_hang(n):
    """A tétel hangdokumentumai: [(ttsId, meta, [(fájl, szöveg)])]. A tétel a tagPath első „> NN. ” tagjából; az új
    tételsor-szerkezetben (nincs egyeb/notes/, van tetelsor/jegyzet_megfeleltetes.json) a meta noteId-jéből, mert ott a
    tagPath tételcsoportot is tartalmaz („A/2 … > 14. A Bírósági Végrehajtás > 79. …”)."""
    out = []
    jt = kozos.jegyzet_tetel()
    for f in sorted(glob.glob(os.path.join(GYOKER, 'tts', '*', '_meta.json'))):
        m = json.load(open(f, encoding='utf-8'))
        if jt is not None:
            talalt = jt.get(m.get('noteId')) == n
        else:
            mm = re.search(r'> (\d+)\. ', m['tagPath'] + ' ') or re.match(r'(\d+)\. ', m['title'])
            talalt = bool(mm and int(mm.group(1)) == n)
        if talalt:
            d = os.path.dirname(f)
            out.append((m['ttsId'], m, [(c['file'], open(os.path.join(d, c['file']), encoding='utf-8').read()) for c in m['chunks']]))
    return out


def blokkok(n):
    return [b for b in kozos.tetel_szoveg(n).split('\n\n') if b.strip()]


def lefedettseg(n):
    """Blokkonként: (index, blokk, találat) – találat = (ttsId, fájl) vagy None."""
    hang = tetel_hang(n)
    darabok = [(tid, fajl, ' ' + ' '.join(t for t in tokenek(re.sub(r'\[[a-z ]+\]', ' ', sz)) if not t.isdigit()) + ' ') for tid, _, lista in hang for fajl, sz in lista]
    eredm = []
    for i, b in enumerate(blokkok(n)):
        # a „§-ban”, „§-ához” ragja a felolvasószövegben a „paragrafus” szóval egybeírva áll, önálló szóként nem kereshető:
        # számként kezeljük, így a ragot tartalmazó ablak kimarad (2026-11-15, a 12. tétel 96–97. blokkjának hamis jelzése)
        tk = tokenek(re.sub(r'§-[a-záéíóöőúüű]+', '§ 0', b.lower()))
        ablakok = []
        for j in range(0, max(len(tk) - 4, 0)):
            w = tk[j:j + 5]
            if any(x.isdigit() or x in KIZART or len(x) < 2 or romai_token(x) for x in w):
                continue
            ablakok.append(' ' + ' '.join(w) + ' ')
        if not ablakok or i == 0:      # tételcím, rövid címsor, dobozfejléc: a szomszédok döntenek
            eredm.append((i, b, 'rovid'))
            continue
        minta = ablakok[::max(1, len(ablakok) // 6)]
        # a legjobb darab: ahol a mintaablakok legnagyobb része megvan; legalább a minta fele (és ha van, legalább két ablak) kell
        legjobb, db = None, 0
        for tid, fajl, sz in darabok:
            k = sum(1 for a in minta if a in sz)
            if k > db:
                legjobb, db = (tid, fajl), k
        kuszob = max(min(2, len(minta)), (len(minta) + 1) // 2)
        if db < kuszob and '\n' in b.strip() and len(b) > 4000:
            # hosszú doboz, amelyet a darabol több darabra vágott: a mintaablakok a hangdokumentum darabjaiban együtt
            # vannak meg; a találat az a darab, amelyben a doboz kezdődik (az első megtalált ablak darabja)
            for tid0 in dict.fromkeys(t for t, _, _ in darabok):
                sajat = [(fajl, sz) for t, fajl, sz in darabok if t == tid0]
                hol = [next((fajl for fajl, sz in sajat if a in sz), None) for a in minta]
                if sum(1 for x in hol if x) >= kuszob:
                    legjobb, db = (tid0, next(x for x in hol if x)), kuszob
                    break
        eredm.append((i, b, legjobb if db >= kuszob else None))
    # a rövid blokk sorsa: hiányzik, ha a következő érdemi blokk hiányzik
    for k in range(len(eredm) - 1, -1, -1):
        if eredm[k][2] == 'rovid':
            kov = next((e[2] for e in eredm[k + 1:] if e[2] != 'rovid'), ('', ''))
            eredm[k] = (eredm[k][0], eredm[k][1], kov if kov is None else ('~', '~'))
    return eredm


def sorrend_hibak(n):
    """Ugyanazon hangdokumentumon belül visszafelé lépő darabsorrend: [(blokkindex, előző darab, ez a darab)]."""
    def kulcs(f):
        m = re.match(r'chunk_(\d+)(?:_(\d+))?', f)
        return (int(m.group(1)), int(m.group(2) or 1))
    hibak, utolso = [], {}
    elozo_tid = None
    for i, b, t in lefedettseg(n):
        if t is None or t == ('~', '~'):
            continue
        tid, f = t
        if tid in utolso and kulcs(f) < kulcs(utolso[tid]):
            hibak.append((i, utolso[tid], f, tid))
        else:
            utolso[tid] = f
        if elozo_tid is not None and tid != elozo_tid and tid in utolso and utolso.get('_lezart_' + tid):
            hibak.append((i, 'dokumentumváltás vissza', f, tid))
        if elozo_tid is not None and tid != elozo_tid:
            utolso['_lezart_' + elozo_tid] = True
        elozo_tid = tid
    return hibak


def hianyzo_futamok(n, reszletes=False):
    """A fel nem olvasott blokkok futamai: (előző találat, [(index, blokk)]); részletesen a következő találat és blokk is."""
    e = lefedettseg(n)
    futam, cur, elozo = [], [], None
    for i, b, t in e:
        if t is None:
            cur.append((i, b))
        else:
            if cur:
                futam.append((elozo, cur, t, b)); cur = []
            if t != ('~', '~'):
                elozo = t
    if cur:
        futam.append((elozo, cur, None, None))
    # a futam végéről a rövid (címsor) blokkok lekerülnek, ha utánuk felolvasott rész jön
    # egyetlen címsorból álló „hiány” többnyire hamis jelzés (pl. a latin kifejezés kiejtés szerinti átírása miatt)
    futam = [f for f in futam if not (len(f[1]) == 1 and len(f[1][0][1]) < 130 and '\n' not in f[1][0][1].strip()
                                      and re.match(r'^(?:[IVXL]+|\d+)\. [A-ZÁÉÍÓÖŐÚÜŰ]', f[1][0][1].strip()))]
    # a következő találat: a futam utáni első érdemi, felolvasott blokk
    ki = []
    for a, c, kt, kb in futam:
        if kt == ('~', '~'):
            ut = c[-1][0]
            kov = next(((t2, b2) for i2, b2, t2 in e if i2 > ut and t2 not in (None, ('~', '~'))), (None, None))
            kt, kb = kov
        ki.append((a, c, kt, kb))
    return ki if reszletes else [(a, c) for a, c, _, _ in ki]


def dobozfej(b):
    """A blokk jogszabálydoboz feje-e. Egyetlen forrás: a kozos.FEJLEC, amellyel a kozos.dobozok is dolgozik – így a
    bekezdéses fej („Th. tv. 10. § (1)–(5) bekezdés”, „Ptk. 6:216. § (4)”) és az évszámos törvénynév
    („2016. évi LXXVII. törvény 29. §”) is fej."""
    return kozos.doboz_fej(b)


def fej_hang(b):
    """A dobozfej felolvasott alakja: „A … paragrafusa...”; bekezdéses fejnél „A … paragrafusának egyes–ötös bekezdése...”."""
    b = b.strip(); k = b.index('§') + 1
    s = hangra(b[:k]).rstrip('.')
    bek = [es(m.group(1)) + ('–' + es(m.group(2)) if m.group(2) else '')
           for m in re.finditer(r'\((\d+)\)(?:\s*[–-]\s*\((\d+)\))?', b[k:])]
    if bek:
        s += 'ának ' + (', '.join(bek[:-1]) + ' és ' + bek[-1] if len(bek) > 1 else bek[0]) + ' bekezdése...'
    else:
        s += 'a...'
    return ('Az ' if s[0].lower() in 'aáeéiíoóöőuúüű' else 'A ') + s


def blokk_hang(b):
    kiejtes_kell()
    b = b.strip()
    if dobozfej(b):
        s = fej_hang(b)
    elif re.fullmatch(r'\[[^\]\n]+\]', b):
        s = b[1:-1] + '...'
    else:
        s = hangra(b)
        # címsor (nagybetűs, mondatvégi írásjel nélkül): a végére szünet kerül; a zárójeles betoldás (pl. „(Ptk. 6:550. §)”,
        # amelynek felolvasott alakja kisbetűs) a címsor felismerését nem zavarja, és a „)”-re végződő cím is szünetet kap
        cim = re.sub(r'\([^()\n]*\)', '', s.split('. ', 1)[-1])
        if '\n' not in s and not re.search(r'[.!?:;…]$', s) and re.search(r'[A-ZÁÉÍÓÖŐÚÜŰ]{4}', cim) and not re.search(r'[a-záéíóöőúüű]{4}', cim):
            s += '...'
    h = hianyos(s)
    if h:
        raise SystemExit(f'Számjegy vagy § maradt a hangszövegben: {h[:5]}')
    return s


BEKEZDESJEL = re.compile(r'^[A-ZÁÉÍÓÖŐÚÜŰ][a-záéíóöőúüű-]*(?:(?:es|as|ös)| (?:[a-záéíóöőúüű]+ )?[a-záéíóöőúüű]+(?:\.:)? bekezdés)\. ')
# „Egyes. ”, „Tizenkettes. ”, „Egy a.: bekezdés. ” (betűs bekezdés): a doboz bekezdésének kezdete
PONTJEL = re.compile(r'^(?:[a-záéíóöőúüű]+|dupla vé)\.: ')                       # „a.: ”, „bé.: ”: pont (az alpont „dé-á.: ”)


def doboz_reszek(s, keret):
    """A keretnél hosszabb, több sorból álló egység (jogszabálydoboz a fejével) részei. A vágás rangsora: bekezdéshatár
    („Kettes. …” kezdetű sor); ha egy bekezdés maga is hosszabb a keretnél, azon belül ponthatár („bé.: …”, a pont az
    alpontjaival együtt marad); ha egy pont is hosszabb, sorhatár; ha egyetlen sor is hosszabb, mondathatár. A doboz feje
    (fej, üres sor) az első normasorral egy részben marad; mondat közepén nincs vágás. A részek sortöréssel összefűzve
    az eredeti egységet adják (a mondathatáron kettévágott sorban a szóköz helyére kerül sortörés)."""
    sorok = s.split('\n')
    if len(sorok) > 2 and not sorok[1].strip():                    # fej + üres sor: az első normasorhoz tartozik
        sorok = ['\n'.join(sorok[:3])] + sorok[3:]

    def vag(elemek, szint):
        if len('\n'.join(elemek)) <= keret:
            return ['\n'.join(elemek)]
        if szint == 2:                                             # sorhatár; a keretnél hosszabb sor mondathatáron
            ki = []
            for r in elemek:
                cur = ''
                for m in re.split(r'(?<=\.\.\.) (?=[A-ZÁÉÍÓÖŐÚÜŰ])', r) if len(r) > keret else [r]:
                    if cur and len(cur) + 1 + len(m) > keret:
                        ki.append(cur); cur = m
                    else:
                        cur = cur + ' ' + m if cur else m
                ki.append(cur)
            return ki
        jel = (BEKEZDESJEL, PONTJEL)[szint]
        csoportok = []
        for i, sor in enumerate(elemek):
            if i == 0 or jel.match(sor):
                csoportok.append([sor])
            else:
                csoportok[-1].append(sor)
        return [x for c in csoportok for x in vag(c, szint + 1)]

    return vag(sorok, 0)


def darabol(szovegek, cimke='[serious]', max_kar=4600, doboz_max=None):
    """Az egységek darabokba rendezése (legfeljebb max_kar karakter). Az egység (bekezdés, címsor, doboz a fejével) nem
    szakad ketté; kivétel a doboz_max-nál (alapértelmezésben max_kar-nál) hosszabb, több sorból álló egység (doboz):
    ezt a doboz_reszek vágja szét, a részei a darabon belül sortöréssel követik egymást."""
    keret = (doboz_max or max_kar) - len(cimke) - 2
    elemek = []                                                    # (szöveg, elválasztó utána)
    for s in szovegek:
        if len(s) > keret and '\n' in s:
            r = doboz_reszek(s, keret)
            elemek += [(x, '\n') for x in r[:-1]] + [(r[-1], '\n\n')]
        else:
            elemek.append((s, '\n\n'))
    # egy bekezdés pontjai („a.: …”, „bé.: …”) a bevezető mondatukkal együtt egy csoport: a darabhatár nem esik közéjük,
    # ha a csoport egy darabban elfér (különben a pontok között vághat, mint eddig)
    csoportok = []
    for s, el in elemek:
        if csoportok and PONTJEL.match(s):
            csoportok[-1].append((s, el))
        else:
            csoportok.append([(s, el)])
    out, cur = [], ''
    for cs in csoportok:
        teljes = sum(len(s) + len(el) for s, el in cs)
        if cur and len(cs) > 1 and len(cur) + teljes > max_kar and len(cimke) + 2 + teljes <= max_kar:
            out.append(cur.rstrip() + '\n'); cur = ''
        for s, el in cs:
            if cur and len(cur) + len(s) > max_kar:
                out.append(cur.rstrip() + '\n'); cur = ''
            cur += ('' if cur else cimke + '\n\n') + s + el
    if cur.strip():
        out.append(cur.rstrip() + '\n')
    return out


# ---------- hangulatcímkék (Attila döntése, 2026-11-18) ----------
# A hosszú felolvasószöveg egyhangúságát hangulatcímkék törik meg. A címke szabályalapú, az egység (bekezdés, doboz,
# címsor) elejére kerül, és csak akkor, ha a hangulat az előző címkéhez képest változik. Készlet: [serious] (normaszöveg),
# [calm] (magyarázat), [emphatic] (tilalom, jogvesztés, kivétel, vizsgahiba), [thoughtful] (elhatárolás, szembeállítás),
# [curious] (kérdés, példa), [short pause] (nagybetűs címsor előtt). Hangeffektus (sóhaj, suttogás) jogi szövegbe nem kerül.
HANGULAT = re.compile(r'^\[(?:serious|calm|emphatic|thoughtful|curious|short pause)\] ')
_H_FEJ = re.compile(r'(?:paragrafus\S*|bekezdése|pontja)\.\.\.$')
_H_KIEMELT = re.compile(r'^(?:Fontos|Figyelem|Lényeges|Kivétel|Kivételesen|Tilos|Semmis|Nem lehet|Nincs helye|Jogvesztő|'
                        r'Gyakori hiba|Vizsgahiba|Nem téveszthető|Nem tévesztendő|Hangsúlyozni kell|Kiemelendő)\b'
                        r'|\bjogvesztő|\bjogvesztéssel jár|\bsemmis\b|\btilos\b|\b[Nn]em lehet\b|\bkizárt\b|\bcsak akkor\b|\bkizárólag\b|\bgyakori hiba\b|\bgyakori tévedés\b')
_H_MERLEGELO = re.compile(r'^(?:Ezzel szemben|Ugyanakkor|Más a helyzet|Ettől eltér|Ettől meg kell különböztetni|El kell határolni|'
                          r'Elhatárolandó|A különbség|Az elhatárolás|Közös|Eltérő|Eltérés|Hasonló|Hasonlóság|Kérdéses|Vitatott|'
                          r'Ellenben|Mindkét|Míg )'
                          r'|\b(?:[Ee]zzel szemben|azonban|viszont|ugyanakkor|különbség|nem azonos|kivétel)')
_H_KIVANCSI = re.compile(r'^(?:Például|Példa|Ha például|Így például|Tegyük fel|Képzeljük el)\b|\bpéldául\b|\?')


def _h_tipus(s):
    elso = s.split('\n')[0].strip()
    if _H_FEJ.search(elso) and len(elso) < 220 and '... ' not in elso and '. ' not in elso[:-3]:
        return 'doboz'
    cim = re.sub(r'\([^()\n]*\)', '', elso.split('. ', 1)[-1])
    if '\n' not in s.strip() and elso.endswith('...') and re.search(r'[A-ZÁÉÍÓÖŐÚÜŰ]{4}', cim) and not re.search(r'[a-záéíóöőúüű]{4}', cim):
        return 'cim'
    return 'bek'


def hangulat(egysegek, alap='calm', kezdo=None, szunet=True, tipusok=None):
    """Az egységek (hangszöveg-bekezdések) elejére hangulatcímkét tesz, ahol a hangulat változik. A pontok („a.: …”), a
    doboz feje utáni normasorok és (ha a hívó a típust megadja: tipusok) az alcímek címkét nem kapnak. Idempotens: a korábbi hangulatcímkét előbb leveszi."""
    ki = []; akt = kezdo; szakasz = None; fej_utan = False
    for sorsz, nyers in enumerate(egysegek):
        s = nyers
        while HANGULAT.match(s):
            s = s[HANGULAT.match(s).end():]
        t = (tipusok[sorsz] if tipusok else None) or _h_tipus(s)
        if not s.strip() or re.fullmatch(r'\s*\[[a-z ]+\]\s*', s) or PONTJEL.match(s) or t == 'alcim' or (fej_utan and BEKEZDESJEL.match(s)):
            ki.append(s); fej_utan = False if s.strip() else fej_utan
            continue
        fej_utan = False
        if t == 'cim':
            szakasz = 'thoughtful' if 'ELHATÁROL' in s else 'calm' if 'ÖSSZEFOGLAL' in s else None
            ki.append(('[short pause] ' if szunet and ki else '') + s)
            continue
        if t == 'doboz':
            h = 'serious'; fej_utan = '\n' not in s.strip()
        elif _H_KIEMELT.search(s):
            h = 'emphatic'
        elif _H_KIVANCSI.search(s):
            h = 'curious'
        elif szakasz == 'thoughtful' or _H_MERLEGELO.search(s):
            h = 'thoughtful'
        else:
            h = alap
        ki.append((f'[{h}] ' if h != akt else '') + s); akt = h
    return ki


def _tiszta_szavak(s):
    return [x for x in re.findall(r'[A-Za-zÁÉÍÓÖŐÚÜŰáéíóöőúüű]+|\d+', s)]


def _beszur_darabba(tid, fajl, szovegek, elozo_blokk, n, irj):
    """Darabon belüli hiány: a hangszöveg beszúrása az előző felolvasott blokk bekezdése után. Siker esetén a karakterszám."""
    d = os.path.join(GYOKER, 'tts', tid); ut = os.path.join(d, fajl)
    c = open(ut, encoding='utf-8').read()
    tk = _tiszta_szavak(elozo_blokk)
    jo = lambda x: not x.isdigit() and len(x) > 1 and x.lower() not in KIZART and not romai_token(x)
    talalat = None
    for veg in range(len(tk), 4, -1):          # a blokk végéhez legközelebbi, öt tiszta szóból álló ablak
        w = tk[veg - 5:veg]
        if not all(jo(x) for x in w):
            continue
        mm = list(re.finditer(r'[^\w\n]+'.join(re.escape(x) for x in w), c))
        if len(mm) == 1:
            talalat = mm[0]
        break
    if talalat is None:
        return None
    sorveg = c.find('\n', talalat.end())
    sorveg = len(c) if sorveg < 0 else sorveg
    betet = '\n\n'.join(szovegek)
    uj = c[:sorveg].rstrip() + '\n\n' + betet + '\n' + ('\n' + c[sorveg:].lstrip('\n') if c[sorveg:].strip() else '')
    if irj:
        open(ut, 'w', encoding='utf-8').write(uj)
        m = json.load(open(os.path.join(d, '_meta.json'), encoding='utf-8'))
        for x in m['chunks']:
            if x['file'] == fajl:
                x.update(charCount=len(uj), valtozas=x.get('valtozas') or 'modositott',
                         ok=(x.get('ok', '') + '; ' if x.get('ok') else '') + f'{n}. tétel: darabon belül kimaradt rész pótolva')
        with open(os.path.join(d, '_meta.json'), 'w', encoding='utf-8') as f:
            json.dump(m, f, ensure_ascii=False, indent=2); f.write('\n')
    return len(uj)


def potol(n, irj=True):
    kiejtes_kell()
    hang = {tid: (m, lista) for tid, m, lista in tetel_hang(n)}
    osszes = 0
    for elozo, blk, kov, kov_blokk in hianyzo_futamok(n, reszletes=True):
        if elozo is None:
            elozo = next(iter((tid, lista[0][0]) for tid, (m, lista) in hang.items()))
        tid, fajl = elozo
        szovegek = [blokk_hang(b) for _, b in blk]
        if kov is not None and kov == elozo and sum(len(s) for s in szovegek) < 2500:
            B = blokkok(n)
            kar = _beszur_darabba(tid, fajl, szovegek, B[blk[0][0] - 1], n, irj) if blk[0][0] > 0 else None
            if kar:
                print(f'{n}. tétel: {tid}/{fajl} darabon belül pótolva ({blk[0][0]}–{blk[-1][0]}. blokk), a darab most {kar} karakter')
                osszes += kar
                continue
        d = os.path.join(GYOKER, 'tts', tid)
        m = json.load(open(os.path.join(d, '_meta.json'), encoding='utf-8'))
        alap = re.match(r'(chunk_\d+)', fajl).group(1)
        letezo = [c['file'] for c in m['chunks'] if c['file'].startswith(alap + '_')]
        k = max([int(re.search(r'_(\d+)\.txt$', x).group(1)) for x in letezo] + [1])
        uj = []
        for dar in darabol(szovegek):
            k += 1
            nev = f'{alap}_{k}.txt'
            if irj:
                open(os.path.join(d, nev), 'w', encoding='utf-8').write(dar)
            uj.append({'file': nev, 'index': None, 'charCount': len(dar), 'status': 'uj', 'audioFile': None, 'valtozas': 'uj',
                       'ok': f'{n}. tétel: eddig fel nem olvasott rész pótlása ({blk[0][0]}–{blk[-1][0]}. blokk)'})
            osszes += len(dar)
        poz = max(i for i, c in enumerate(m['chunks']) if c['file'] == alap + '.txt' or c['file'].startswith(alap + '_'))
        m['chunks'][poz + 1:poz + 1] = uj
        if irj:
            with open(os.path.join(d, '_meta.json'), 'w', encoding='utf-8') as f:
                json.dump(m, f, ensure_ascii=False, indent=2); f.write('\n')
        print(f'{n}. tétel: {tid} {alap} után {len(uj)} új darab, {sum(u["charCount"] for u in uj)} karakter ({blk[0][0]}–{blk[-1][0]}. blokk)'
              + ('' if kov is None or kov != elozo else '  [FIGYELEM: a következő felolvasott rész ugyanebben a darabban van – a sorrendet ellenőrizni kell]'))
    return osszes


def csonka_javit(n, irj=True):
    """A mondat közepén véget érő hangdarabok kiegészítése a megszakadt blokk végéig."""
    kiejtes_kell()
    e = lefedettseg(n); B = blokkok(n); db = 0
    for tid, m, lista in tetel_hang(n):
        for fajl, sz in lista:
            torzs = re.sub(r'(\s*\[[a-z ]+\])+\s*$', '', sz.rstrip()).rstrip()
            if re.search(r'(\.\.\.|[.!?:;]|[)”"])$', torzs):
                continue
            utolso = [i for i, b, t in e if t == (tid, fajl)]
            if not utolso:
                print(f'  ! {tid}/{fajl}: csonka, de nincs hozzá blokk'); continue
            k = torzs.rfind('...')
            fej, toredek = (torzs[:k + 3], torzs[k + 3:].strip()) if k >= 0 else ('', torzs)
            kesz = None
            for i in (utolso[-1], utolso[-1] + 1):
                if i >= len(B):
                    continue
                gen = blokk_hang(B[i])
                kulcs = toredek[:30] if len(toredek) >= 12 else None
                q = gen.find(kulcs) if kulcs else -1
                if q >= 0:
                    kesz = (fej + (' ' if fej and not fej.endswith('\n') else '') + gen[q:]).rstrip() + '\n'; break
            if kesz is None:
                print(f'  ! {tid}/{fajl}: a töredék nem azonosítható: {toredek[:60]!r}'); continue
            d = os.path.join(GYOKER, 'tts', tid)
            if irj:
                open(os.path.join(d, fajl), 'w', encoding='utf-8').write(kesz)
                mm = json.load(open(os.path.join(d, '_meta.json'), encoding='utf-8'))
                for c in mm['chunks']:
                    if c['file'] == fajl:
                        c.update(charCount=len(kesz), valtozas='modositott', ok=(c.get('ok', '') + '; ' if c.get('ok') else '') + f'{n}. tétel: a mondat közepén megszakadt darab befejezve')
                with open(os.path.join(d, '_meta.json'), 'w', encoding='utf-8') as f:
                    json.dump(mm, f, ensure_ascii=False, indent=2); f.write('\n')
            db += 1
            print(f'{n}. tétel: {tid}/{fajl} befejezve (+{len(kesz) - len(sz)} karakter)')
    return db


def main():
    kiejtes_kell()
    cmd = sys.argv[1]
    if cmd == 'lefed' and len(sys.argv) == 2:
        L = ['# Hanglefedettség', '', 'Újragenerálás: `python3 tools/hangszoveg.py lefed`. Blokk = a tétel üres sorral elválasztott egysége.', '',
             '| tétel | blokk | fel nem olvasott blokk | fel nem olvasott karakter | hol (blokkindexek) |', '|---|---|---|---|---|']
        ossz = 0
        for t in kozos.tetelsor()['tetelek']:
            n = t['sorszam']; fut = hianyzo_futamok(n)
            db = sum(len(b) for _, b in fut); kar = sum(len(x) for _, b in fut for _, x in b); ossz += kar
            if db:
                L.append(f'| {n} | {len(blokkok(n))} | {db} | {kar} | ' + ', '.join(f'{b[0][0]}–{b[-1][0]}' for _, b in fut) + ' |')
        L += ['', f'Összesen fel nem olvasott tételszöveg: {ossz} karakter.']
        open(os.path.join(GYOKER, 'jelentesek', 'hanglefedettseg.md'), 'w', encoding='utf-8').write('\n'.join(L) + '\n')
        print('\n'.join(L[4:]))
    elif cmd == 'lefed':
        for elozo, blk in hianyzo_futamok(int(sys.argv[2])):
            print('--- előző találat:', elozo)
            for i, b in blk:
                print(f'  [{i}] {b[:110]!r}')
    elif cmd == 'szoveg':
        n = int(sys.argv[2]); a, b = (int(x) for x in sys.argv[3].split('-'))
        B = blokkok(n)
        for i in range(a, b + 1):
            print(blokk_hang(B[i]) + '\n')
    elif cmd == 'potol':
        n = int(sys.argv[2])
        csonka_javit(n)
        print('összesen', potol(n), 'új karakter')


if __name__ == '__main__':
    main()
