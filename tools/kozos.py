"""Közös segédfüggvények a tételsor-tároló ellenőrző szkriptjeihez (csak a standard könyvtár).

A tároló gyökeréből futtatandó szkriptek importálják:
    sys.path.insert(0, 'tools'); import kozos
"""
import json, os, re, sys, unicodedata

GYOKER = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
KORPUSZ = os.path.join(GYOKER, 'korpusz')

# A bekezdésszám betűs is lehet: „Btk. 29. § (1a)”, „Btk. 459. § (1a)–(2)”.
BEKEZDES = r'(?:\s*\(\d+[a-z]?\)(?:\s*[–-]\s*\(\d+[a-z]?\))?(?:,\s*\(\d+[a-z]?\)(?:\s*[–-]\s*\(\d+[a-z]?\))?)*(?:\s*(?:bekezdés|bek\.?))?(?:\s*[a-z]{1,2}\)\s*pont)?)?'

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


_EGYSEG = {}


def egyseg(kod):
    """A forrás egysége a beállításból (forrasok[].egyseg, tetelForras): '§', 'cikk', 'romaiCikk'. A beállításban nem
    szereplő forrásé (az általános feloldás rekordja, pl. „(EU) 2016/679”) a korpuszfájlból: a „N. cikk” és a „N. §”
    fejsorok közül a gyakoribb; ha egyik sincs: '§'."""
    for f in beallitas()['forrasok']:
        if f.get('kod') == kod:
            return f.get('egyseg') or '§'
    for lista in (beallitas().get('tetelForras') or {}).values():
        for f in lista:
            if f.get('kod') == kod and f.get('egyseg'):
                return f['egyseg']
    if kod not in _EGYSEG:
        _EGYSEG[kod] = '§'
        try:
            f = forrasok().get(kod) or {}
            p = korpusz_fajl(f['korpusz'][0]) if f.get('korpusz') else None
            if p:
                t = open(p, encoding='utf-8').read()
                c = len(re.findall(r'(?mi)^\s*\d+(?-i:[a-z])?\. cikk\b', t)); par = len(re.findall(r'(?m)^\s*\d+(?::\d+)?(?:/[A-Z])?\. §', t))
                _EGYSEG[kod] = 'cikk' if c > par else '§'
        except (OSError, ValueError, KeyError):
            pass
    return _EGYSEG[kod]


def konyves(kod):
    """Igaz, ha a forrás §-számozása könyves (Ptk. 6:105. §). Forrásonként: a forrás saját parMinta kulcsa
    (forrasok[].parMinta: 'konyv' | 'egyszeru') dönt; ha nincs, az alapérték: a beállítás parMinta kulcsa a fő kódexre
    (A/1: kod == 'Ptk'), illetve a korpuszfájl maga (van-e benne „N:M. §” sor)."""
    B = beallitas()
    f = next((x for x in B['forrasok'] if x.get('kod') == kod), {})
    if f.get('parMinta'):
        return f['parMinta'] == 'konyv'
    if B['parMinta'] == 'konyv' and kod == B['foKodex']:
        return True
    return _konyves_korpusz(kod)


_KONYVES = {}


def _konyves_korpusz(kod):
    if kod not in _KONYVES:
        _KONYVES[kod] = False
        try:
            f = forrasok().get(kod) or {}
            p = korpusz_fajl(f['korpusz'][0]) if f.get('korpusz') else None
            if p:
                _KONYVES[kod] = bool(re.search(r'(?m)^\s*\d+:\d+(?:/[A-Z])?\. §', open(p, encoding='utf-8').read()))
        except (OSError, ValueError, KeyError):
            pass
    return _KONYVES[kod]


# A tételek jogszabálydobozainak fejlécében használt rövidítések -> forráskód (tetelsor/forrasok.json).
# Tárgyanként a beállítás dobozRovidites tömbje (A/1: Ptk., Ptké., …). A fejléc egysége forrásonként a beállításból
# jön (forrasok[].egyseg): „Pp. 8. §”, „Ptk. 6:518. §” (könyves számozás bármely §-os forrásnál), „EUMSZ 223. cikk”,
# „GDPR 5. cikk (1) bekezdés”, „Alaptörvény XXVIII. cikk”, „Alaptörvény T) cikk”, „Alaptörvény 25. cikk”.
# A csoportok: 1 = rövidítés, 2 = az egység azonosítója, 3 = az egység jele (§ / cikk). Az egység és a forrás
# összeillését a dobozok() ellenőrzi (fejlec_kod).
_B = beallitas()
DOBOZ_RÖVIDITES = [(minta, kod) for minta, kod in _B['dobozRovidites']]
BEAGYAZOTT = {kod: tuple(par) for kod, par in _B['beagyazott'].items()}
PAR = r'(\d+(?::\d+)?(?:/[A-Z])?|\d+[a-z](?=\.)|[IVXLC]+|[A-Z]\))'     # „4a. cikk”: betűs cikkszám (KE-3/3)
# Az uniós jogi aktus preambulumbekezdése is doboz: „2005/36/EK irányelv (1) preambulumbekezdés” – a 4. csoport a
# preambulumbekezdés száma, az egység azonosítója 'preambulum' (a korpuszban az első cikk előtti szöveg).
FEJLEC = re.compile(r'^(' + '|'.join(r for r, _ in DOBOZ_RÖVIDITES) + r')\s*(?:' + PAR + r'(?:\.|(?<=\)))\s?(§|[Cc]ikk)' + BEKEZDES
                    + r'|\((\d+)\)(?:\s*[–-]\s*\(\d+\))?\s*preambulumbekezdés)$')
PREAMBULUM = 'preambulum'


def doboz_fej(sor):
    """A sor jogszabálydoboz feje-e: a FEJLEC-találat, ha az egysége a forráséval egyezik, különben None. A dobozok()
    pontosan ezeket a sorokat veszi fejnek – a fejsorok indexét ezzel kell képezni (zip a dobozok()-kal)."""
    m = FEJLEC.match(sor.strip())
    return m if m and fejlec_kod(m)[0] is not None else None


def fejlec_kod(m):
    """A FEJLEC-találat forráskódja és egységazonosítója, ha a fejléc egysége a forráséval egyezik: (kod, azonosító),
    különben (None, None). „Pp. 8. §” -> ('Pp', '8'); „EUMSZ 223. cikk” -> ('EUMSZ', '223'); „Alaptörvény T) cikk” ->
    ('Alaptv', 'T)')."""
    kod = rovid_kod(m.group(1))
    e = egyseg(kod)
    if m.group(4):
        # preambulumbekezdés: csak cikkre tagolt (uniós) forrásnál
        return (kod, PREAMBULUM) if e == 'cikk' else (None, None)
    jel = m.group(3).lower()
    azon = m.group(2)
    if e == '§':
        ok = jel == '§' and re.fullmatch(r'\d+(?::\d+)?(?:/[A-Z])?', azon)
    elif e == 'cikk':
        ok = jel == 'cikk' and re.fullmatch(r'\d+[a-z]?', azon)       # „4a. cikk” is (KE-3/3)
    else:
        ok = jel == 'cikk'
    return (kod, azon) if ok else (None, None)


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


def egyseg_sor(s, e):
    """A korpuszsor egységfeje (match) – az alapfelvetel.egyseg_sor szabálya (egy helyen megírva)."""
    import alapfelvetel
    return alapfelvetel.egyseg_sor(s, e)


def zaro_cimek_le(sorok, cimsor):
    """A § (cikk) sorai a végén álló szerkezeti címsorok nélkül (a következő egység címe: „II. FEJEZET”, „A bíróság
    hatásköre”, puszta „133/C.”, hatályon kívül helyezett puszta „c)”, oldalláb-URL). A cimsor() a hívó szabálya (záró írásjel
    nélküli sor). KE-3/2: a pont nélkül végződő utolsó bekezdés tördelt folytatósora NEM cím – ha a sor kisbetűvel kezdődik,
    és az előtte álló sor nem zárul mondatzáró írásjellel (vesszővel, szóval végződik), a sor a bekezdés része, és a vágás
    itt megáll (EUMSZ 125. cikk (2) bekezdés: „… konzultációt” / „követően …” / „… fogalmakat”); a „Kelt …” záróformula
    utáni aláírássor („a Tanács részéről”, „az elnök”) nem folytatósor. Egy helyen megírva: az
    s5/doboz_javit.csoportok és a doboz_teljesseg.bekezdesek_sorokbol is ezt használja."""
    sorok = list(sorok)
    alairas = any(re.match(r'^Kelt \S', x.strip()) for x in sorok)     # az uniós aktus záróformulája után aláírás áll
    while sorok and cimsor(sorok[-1]):
        l = sorok[-1].strip()
        elozo = sorok[-2].strip() if len(sorok) > 1 else ''
        if (re.match(r'^[a-záéíóöőúüű]', l) and not re.match(r'^[a-z]{1,2}\)', l) and not re.match(r'^https?://', l)
                and not alairas and elozo and not re.search(r'[.;:!?…\]]["”’)]*\s*\*?$|\bs\.\s?k\.,?$', elozo)):
            break
        sorok.pop()
    return sorok


def jogszabaly_sorok(kod, fajl):
    """{egység: [a korpuszfájl nyers (csak szélein szóköztelenített) sorai a fej utáni szövegtől]} és a sorrend.
    Az egység a forrás egysége (§, cikk, romaiCikk); a fej sorának maradéka az első sor."""
    e = egyseg(kod)
    d, sorrend, cur = {}, [], None
    for l in open(fajl, encoding='utf-8').read().split('\n'):
        t = l.strip()
        m = egyseg_sor(t, e)
        if m:
            cur = m.group(1)
            if cur in d:
                cur = None; continue      # azonos számú második egység (Itv.): az első számít
            d[cur] = []; sorrend.append(cur)
            rest = t[m.end():].strip()
            if e != '§':
                rest = rest.lstrip('-–* ').strip()
                if not re.search(r'[.;:!?”"…)]$', rest):
                    rest = ''             # a cikkfej utáni cím („3. cikk - Általános joghatóság”) nem normaszöveg
            if rest:
                d[cur].append(rest)
        elif cur is not None and re.sub(r'\s*\*$', '', t).isupper() and len(t) > 3 and not re.search(r'[.;:,]\s*\*?$', t):
            cur = None        # nagybetűs szerkezeti cím („ZÁRÓ ÉS VEGYES RENDELKEZÉSEK *”): az egység itt véget ér
        elif cur is not None:
            d[cur].append(t)
    return d, sorrend


def jogszabaly_paragrafusok(kod, fajl):
    """{egység (§ vagy cikk): normalizált szöveg} és az egységek sorrendje a korpusz-fájlban."""
    if kod in BEAGYAZOTT:
        return beagyazott_paragrafusok(fajl, *BEAGYAZOTT[kod])
    e = egyseg(kod)
    d, sorrend, cur, elotte = {}, [], None, []
    for l in open(fajl, encoding='utf-8').read().split('\n'):
        m = egyseg_sor(l.strip(), e)
        if m:
            cur = m.group(1)
            if cur not in d:
                d[cur] = []; sorrend.append(cur)
            rest = l.strip()[m.end():].strip()
            if rest:
                d[cur].append(rest)
        elif cur:
            d[cur].append(l)
        elif e == 'cikk':
            elotte.append(l)
    ki = {k: norm(' '.join(v)) for k, v in d.items()}
    if e == 'cikk' and elotte:
        # a preambulum (az első cikk előtti szöveg): a „… (1) preambulumbekezdés” doboz ezzel vethető össze; a sorrendben
        # nem szerepel (nem egység a lefedettség számára). A kétoszlopos PDF-ből vett preambulumban a bekezdések sorai
        # összefésülődhetnek, ezért a doboz sorait az egész preambulum szövegében keressük.
        ki[PREAMBULUM] = norm(' '.join(elotte))
    return ki, sorrend


def korpusz_jogszabalyok():
    """Forráskód -> ({egység: szöveg}, sorrend) azokra a jogszabályokra, amelyek §-okra vagy cikkekre tagolódnak."""
    out = {}
    egysegesek = {f['kod'] for f in beallitas()['forrasok'] if f.get('egyseg') in ('§', 'cikk', 'romaiCikk')}
    egysegesek |= {kod for _, kod in DOBOZ_RÖVIDITES}      # amire dobozfejléc utal, az tagolt jogszabály
    for kod, f in forrasok().items():
        # A típus nélküli, de korpuszfájllal bíró forrás is jogszabály (új tételsor, ahol a beállítás
        # nem ad tipust). Az A/1 minden forrása tipust ad, ezért ott a feltétel a régivel azonos.
        # A beállításban egységgel (§, cikk, romaiCikk) megadott forrás a típusától függetlenül tagolt jogszabály.
        if (f.get('tipus') not in ('törvény', 'rendelet', None) and kod not in egysegesek) or not f.get('korpusz'):
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


_JOG = None


def cikk_szoveg(kod, par):
    """A cikkre tagolt forrás (egység: cikk, romaiCikk) cikkének normalizált szövege a korpuszból, vagy ''. A dobozok()
    ezzel ismeri fel a számozatlan bekezdést (az uniós cikk második, harmadik bekezdését) a doboz részeként."""
    global _JOG
    if egyseg(kod) == '§':
        return ''
    if _JOG is None:
        _JOG = korpusz_jogszabalyok()
    return (_JOG.get(kod) or ({}, []))[0].get(par) or ''


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
        if re.match(r'^(?:i|ii|iii|iv|v|vi|vii|viii|ix|x)\. \S', s):
            return True   # római alpont („i. legkésőbb …”, „v. annak a tagállamnak …”) – uniós rendeletek pontjain belül
        return bool(s.startswith('[') or re.match(r'^\(\d+[a-z]?\)', s) or re.match(r'^[a-z]{1,2}\)', s))

    out, i = [], 0
    while i < len(L):
        m = FEJLEC.match(L[i])
        if not m or fejlec_kod(m)[0] is None:
            i += 1; continue
        kod, par = fejlec_kod(m); j = i + 1; sorok = []
        while j < len(L):
            s = L[j]
            if not s:
                j += 1; continue
            if FEJLEC.match(s) or s.isupper():
                break
            if not sorok:
                if not normasor(s) and re.match(r'^([IVX]+|\d+)\. [A-ZÁÉÍÓÖŐÚÜŰ]', s):
                    break
                sorok.append(re.sub(r'^(?:\d+(?::\d+)?(?:/[A-Z])?\. §|(?:\d+[a-z]?|[IVXLC]+)\. [Cc]ikk|[A-Z]\) [Cc]ikk)\s*', '', s)); j += 1; continue
            if not normasor(s):
                if len(sorok) == 1 and (sorok[0].startswith('[') and sorok[0].endswith(']')
                                        or re.fullmatch(r'\((?!\d+[a-z]?\))[^\n]*\)', sorok[0])):
                    # szögletes zárójeles cím, illetve a cikk elején álló zárójeles megjegyzés („(az EKSz. korábbi
                    # 13. cikke)”) után a bekezdésszám nélküli normaszöveg következik
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
                ns = norm(s)
                if len(ns) >= 20 and re.match(r'^[A-ZÁÉÍÓÖŐÚÜŰ]', s) and ns in cikk_szoveg(kod, par):
                    # cikkre tagolt forrás számozatlan bekezdése („A rendelet általános hatállyal bír. …” az EUMSZ 288.
                    # cikkében): a doboz része, ha a cikk korpuszszövegében betűre megvan
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
