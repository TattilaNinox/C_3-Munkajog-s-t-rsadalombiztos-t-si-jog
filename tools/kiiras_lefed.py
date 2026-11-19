#!/usr/bin/env python3
"""A hivatalos kiírás lefedettsége a tételben – tájékoztató eszköz, nem lezáró kapu (kilépési kód mindig 0).
(Folyamataudit 2026-11-15, B változat, Attila jóváhagyása 20:51: „gépi kiírás-lefedettség”.)

    python3 tools/kiiras_lefed.py NN [NN…]               # az előírt §-ok a tételben: dobozban / csak hivatkozva / hiányzik
    python3 tools/kiiras_lefed.py --korpusz-hiany [tól ig] # a kiírás forrásai közül mi nincs a korpuszban (alapérték: 22–85)

A kiírás a tetelsor/tetelsor.json „eloirasok” mezőjéből jön (forrás + tol/ig, „teljes”, „fejezetek”, „bekezdes”, bírósági
iránymutatásnál „pontok”). A §-tagolás, a dobozok és a szöveges hivatkozások felismerése a meglévő függvényekkel történik:
kozos.korpusz_jogszabalyok, kozos.dobozok, ellenorzes.tartomany / emlitett_paragrafusok / hatalyos / biro_minta,
doboz_teljesseg.bekezdesek. A hatályon kívül helyezett § nem számít előírtnak.

1. mód, tételenként:
  - előírt §: a kiírás §-tartományainak, a teljes jogszabálynak, illetve a megnevezett fejezeteknek minden hatályos §-a;
  - dobozban: a § szövege a tétel jogszabálydobozában áll; csak hivatkozva: a tétel §-számmal hivatkozik rá (egyedi
    §-ként vagy tartományban), doboz nélkül; hiányzik: egyik sem (felsorolva). Nem Ptk.-beli §-nál a jogszabálynév
    nélküli „(87. §)” hivatkozást a szövegben utoljára megnevezett jogszabályhoz számítja, és ezeket külön megszámolja
    („jogszabálynév nélkül, a szövegkörnyezet szerint”) – ez becslés, a felsorolt §-t ellenőrizni kell;
  - bekezdés-hiány (tájékoztató): a dobozban álló §-nak az a hatályos bekezdése, amely sem a dobozban, sem „N. § (b)”
    alakú szöveges hivatkozásban nem szerepel (a „(2) bekezdés szerint” típusú, §-szám nélküli utalást nem ismeri fel);
  - bírósági iránymutatás: a tétel említi-e (a pontszintű egyezést gépileg nem vizsgálja – ezt kiírja);
  - nem elemezhető kiírás-elem: amit az eszköz nem tud §-okra bontani (pl. szó szerint idézett dokumentum, ismeretlen
    fejezet), vagy ami a kiírás szövegében (eloirasSzoveg) áll, de a gépi kiírásban (eloirasok) nincs megfelelője.
  Utolsó sor: összegzés.
2. mód (--korpusz-hiany): tételenként a kiírás forrásai, amelyek nincsenek a korpuszban (tetelsor/forrasok.json „korpusz”
  mezője üres, a fájl hiányzik a korpusz/ mappából, nincs a korpusz/manifest.json-ban, vagy a §-tartomány határa / a
  fejezet nincs a korpuszfájlban), majd forrásonként összesítve.
"""
import json, os, re, sys, unicodedata
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import kozos
import ellenorzes as E
import doboz_teljesseg as DT

ROV = kozos.beallitas()['kiirasRovidites']
BIRO_RX = kozos.beallitas()['biroRx']


def rov(kod):
    return ROV.get(kod, kod)


def fejezet_parok(kod):
    """{fejezet (pl. 'IV', 'IV/A'): [§…]} a korpuszfájl sorrendjében; a §-felismerés a kozos.jogszabaly_paragrafusok
    mintája szerint."""
    f = kozos.forrasok().get(kod) or {}
    p = kozos.korpusz_fajl((f.get('korpusz') or [''])[0]) if f.get('korpusz') else None
    if not p:
        return None
    rx = re.compile(r'^(\d+:\d+(?:/[A-Z])?)\. §' if kozos.konyves(kod) else r'^(\d+(?:/[A-Z])?)\. §')
    fx = re.compile(r'^(?:\(\d+[a-z]?\)\s*)?([IVXLC]+(?:/[A-Z])?)\. Fejezet\b')
    out, cur = {}, None
    for l in open(p, encoding='utf-8').read().split('\n'):
        l = l.strip()
        m = fx.match(l)
        if m:
            cur = m.group(1); out.setdefault(cur, []); continue
        m = rx.match(l)
        if m and cur and m.group(1) not in out[cur]:
            out[cur].append(m.group(1))
    return out


def bek_kulcsok(fej, sorok):
    """A dobozban szereplő bekezdések: a fejléc bekezdés-kijelölése és a „(n)” kezdetű sorok."""
    k = set()
    resz = re.sub(r'^.*?§', '', fej)
    for a, b in re.findall(r'\((\d+[a-z]?)\)(?:\s*[–-]\s*\((\d+[a-z]?)\))?', resz):
        k |= kifejt(a, b)
    for s in sorok:
        m = re.match(r'^\((\d+[a-z]?)\)', s)
        if m:
            k.add(m.group(1))
    return k


def kifejt(a, b):
    if b and a.isdigit() and b.isdigit():
        return {str(i) for i in range(int(a), int(b) + 1)}
    return {a} | ({b} if b else set())


RX_TART = re.compile(r'(?<![\d:/])(\d+(?:/[A-Z])?)\.?(?:\s?§)?\s*[–-]\s*(\d+(?:/[A-Z])?)\.\s?§')
RX_PAR = re.compile(r'(?<![\d:/])(\d+(?:/[A-Z])?)\.\s?§((?:\s*\(\d+[a-z]?\)(?:\s*[–-]\s*\(\d+[a-z]?\))?(?:,|\s+és)?)*)')


def hivatkozasok(txt):
    """A tétel nem Ptk.-beli §-hivatkozásai jogszabályonként: {kód: {'par': {§}, 'tart': [(tól, ig)], 'bek': {§: {bek.}},
    'nevtelen': {§}}}. Egy „N. §” hivatkozás jogszabálya: (1) a sorban előtte álló legközelebbi megnevezés
    (ellenorzes.EMLITES), (2) ennek hiányában a sorban utána álló megnevezés (mint az ellenorzes.emlitett_paragrafusok),
    (3) ennek hiányában a szövegben utoljára megnevezett, nem Ptk.-beli jogszabály – ez a „névtelen” (szövegkörnyezet
    szerinti) hivatkozás, külön jelölve. A Ptk. (kettőspontos §-szám) hivatkozásait az ellenorzes.emlitett_paragrafusok
    adja."""
    out = {}
    utolso = None

    def tesz(kod, mezo, ertek, nevtelen):
        d = out.setdefault(kod, {'par': set(), 'tart': [], 'bek': {}, 'nevtelen': set()})
        if mezo == 'tart':
            d['tart'].append(ertek)
        elif mezo == 'par':
            d['par'].add(ertek)
            if nevtelen:
                d['nevtelen'].add(ertek)
        else:
            d['bek'].setdefault(ertek[0], set()).update(ertek[1])

    for sor in txt.split('\n'):
        nevek = sorted((m.start(), kod) for kod, rx in E.EMLITES.items() for m in re.finditer(rx, sor))

        def kie(poz):
            elotte = [k for p, k in nevek if p < poz]
            if elotte:
                return elotte[-1], False
            if nevek:
                return nevek[0][1], False
            return utolso, True

        for m in RX_TART.finditer(sor):
            kod, nt = kie(m.start())
            if kod:
                tesz(kod, 'tart', (m.group(1), m.group(2)), nt)
        for m in RX_PAR.finditer(sor):
            kod, nt = kie(m.start())
            if not kod:
                continue
            tesz(kod, 'par', m.group(1), nt)
            bk = set()
            for a, b in re.findall(r'\((\d+[a-z]?)\)(?:\s*[–-]\s*\((\d+[a-z]?)\))?', m.group(2) or ''):
                bk |= kifejt(a, b)
            if bk:
                tesz(kod, 'bek', (m.group(1), bk), nt)
        if nevek:
            utolso = nevek[-1][1]
    return out


def szoveg_elemek(t):
    """A kiírás szövegének azon elemei, amelyeknek a gépi kiírásban nincs megfelelője."""
    gepi = t['eloirasok']; hat = set(); kodok = set()
    for e in gepi:
        kodok.add(re.sub(r'[\s.]', '', e['forras']).lower())
        if 'tol' in e:
            hat |= {e['tol'], e['ig']}
    out = []
    sz = t['eloirasSzoveg']
    for m in re.finditer(r'(?<![\d:/])(\d+(?::\d+)?(?:/[A-Z])?)\.\s?§', sz):
        if m.group(1) not in hat:
            out.append(f'„{m.group(0)}” (a gépi kiírásban nincs ilyen tartományhatár)')
    for m in re.finditer(BIRO_RX, sz):
        k = re.sub(r'\([^)]*\)', '', m.group(0)).replace('számú Polgári Elvi Döntés', 'PED')
        k = re.sub(r'[\s.]', '', k).lower()
        if not any(k.startswith(x) or x.startswith(k) or x in k for x in kodok):
            out.append(f'„{m.group(0)}” (iránymutatás, a gépi kiírásban nincs megfelelője)')
    return out


def lefed(n, JOG, F):
    t = next(x for x in kozos.tetelsor()['tetelek'] if x['sorszam'] == n)
    txt = kozos.tetel_szoveg(n)
    dl = kozos.dobozok(txt)
    dob = {}
    for kod, par, fej, sorok in dl:
        dob.setdefault((kod, par), []).append((fej, sorok))
    eloirt, nem_elemz, biro, bek_hiany = [], [], [], []
    fej_cache = {}
    for e in t['eloirasok']:
        kod = e['forras']
        if 'tol' in e or e.get('teljes') or 'fejezetek' in e:
            if kod not in JOG:
                nem_elemz.append(f'{kod}: a jogszabály §-tagolása nincs a korpuszban'); continue
            szov, sorrend = JOG[kod]
            if 'tol' in e:
                lista = E.tartomany(sorrend, e['tol'], e['ig'])
                if lista is None:
                    nem_elemz.append(f"{rov(kod)} {e['tol']}–{e['ig']}. §: a tartomány határa nincs a korpuszban"); continue
            elif e.get('teljes'):
                lista = list(sorrend)
            else:
                fp = fej_cache.setdefault(kod, fejezet_parok(kod))
                lista = []
                for fz in e['fejezetek']:
                    if not fp or fz not in fp:
                        nem_elemz.append(f'{rov(kod)} {fz}. fejezet: a fejezet nincs a korpuszfájlban'); continue
                    lista += fp[fz]
            for p in lista:
                if E.hatalyos(szov.get(p, '')):
                    eloirt.append((kod, p, e.get('bekezdes')))
        elif 'resz' in e:
            nem_elemz.append(f"{kod}: {e['resz']}")
        else:
            try:
                rx = E.biro_minta(kod)
            except Exception:
                nem_elemz.append(f'{kod}: ismeretlen iránymutatás-azonosító'); continue
            emlit = bool(re.search(rx, txt))
            pont = (' – előírt pontok: ' + ', '.join(e['pontok']) + ' (pontszinten gépileg nem vizsgálva)') if e.get('pontok') else ''
            if e.get('kiveve'):
                pont += f"; kivéve: {e['kiveve']}"
            biro.append(f"{kod}: {'említve' if emlit else 'NINCS EMLÍTVE'}{pont}")
    nem_elemz += szoveg_elemek(t)
    # §-szintű besorolás
    eml = {}
    hiv = hivatkozasok(txt)
    dobozban, csak_hiv, hiany, nevtelen = [], [], [], []
    latott = set()
    for kod, p, bek in eloirt:
        if (kod, p, bek) in latott:
            continue
        latott.add((kod, p, bek))
        if kod not in eml:
            if kozos.konyves(kod):
                eml[kod] = E.emlitett_paragrafusok(txt, kod)
            else:
                h = hiv.get(kod) or {'par': set(), 'tart': []}
                eml[kod] = set(h['par']) | {('tartomany', a, b) for a, b in h['tart']}
                eml[kod] |= E.emlitett_paragrafusok(txt, kod)
        cimke = f'{rov(kod)} {p}. §' + (f' ({bek})' if bek else '')
        if (kod, p) in dob:
            dobozban.append(cimke)
            # bekezdés-szint
            B = DT.bekezdesek(JOG[kod][0][p])
            kell = {k for k, v in B.items() if k and not v.startswith('Hatályon kívül')}
            if bek:
                kell &= {bek}
            van = set()
            for fej, sorok in dob[(kod, p)]:
                bk = bek_kulcsok(fej, sorok)
                if not bk:      # bekezdés-kijelölés nélküli doboz: a teljes §
                    van |= kell
                van |= bk
            if kozos.konyves(kod):
                for m in re.finditer(r'(?<![\d:/])' + re.escape(p) + r'\.\s?§((?:\s*\(\d+[a-z]?\)(?:\s*[–-]\s*\(\d+[a-z]?\))?(?:,|\s+és)?)*)', txt):
                    for a, b in re.findall(r'\((\d+[a-z]?)\)(?:\s*[–-]\s*\((\d+[a-z]?)\))?', m.group(1)):
                        van |= kifejt(a, b)
            else:
                van |= (hiv.get(kod) or {'bek': {}})['bek'].get(p, set())
            hi = sorted(kell - van, key=lambda x: (int(re.match(r'\d+', x).group()), x))
            if hi:
                bek_hiany.append(f"{rov(kod)} {p}. § " + ', '.join(f'({x})' for x in hi))
        elif p in eml[kod] or any(E.tartomany(JOG[kod][1], a, b) and p in E.tartomany(JOG[kod][1], a, b)
                                  for x in eml[kod] if isinstance(x, tuple) for _, a, b in [x]):
            csak_hiv.append(cimke)
            if not kozos.konyves(kod) and p in (hiv.get(kod) or {}).get('nevtelen', set()) and p not in E.emlitett_paragrafusok(txt, kod):
                nevtelen.append(cimke)
        else:
            hiany.append(cimke)
    return {'tetel': n, 'kiiras': t['eloirasSzoveg'], 'eloirt': len(latott), 'dobozban': dobozban, 'csak_hiv': csak_hiv,
            'hiany': hiany, 'nevtelen': nevtelen, 'bek_hiany': bek_hiany, 'biro': biro, 'nem_elemz': nem_elemz}


def fo_mod(ns):
    JOG = kozos.korpusz_jogszabalyok(); F = kozos.forrasok()
    ossz = {'eloirt': 0, 'dobozban': 0, 'csak_hiv': 0, 'hiany': 0, 'bek_hiany': 0, 'nem_elemz': 0, 'biro_nincs': 0}
    for n in ns:
        r = lefed(n, JOG, F)
        print(f"{n}. tétel – kiírás: {r['kiiras']}")
        nt = f" (ebből jogszabálynév nélkül, a szövegkörnyezet szerint: {len(r['nevtelen'])})" if r['nevtelen'] else ''
        print(f"  előírt §: {r['eloirt']}; dobozban: {len(r['dobozban'])}; csak hivatkozva: {len(r['csak_hiv'])}{nt}; hiányzik: {len(r['hiany'])}")
        if r['hiany']:
            print('  hiányzik: ' + '; '.join(r['hiany']))
        if r['csak_hiv']:
            print('  csak hivatkozva: ' + '; '.join(r['csak_hiv']))
        if r['bek_hiany']:
            print('  bekezdés-hiány a dobozolt §-okban (tájékoztató): ' + '; '.join(r['bek_hiany']))
        for b in r['biro']:
            print('  iránymutatás: ' + b)
        for x in r['nem_elemz']:
            print('  nem elemezhető kiírás-elem: ' + x)
        ossz['eloirt'] += r['eloirt']; ossz['dobozban'] += len(r['dobozban']); ossz['csak_hiv'] += len(r['csak_hiv'])
        ossz['hiany'] += len(r['hiany']); ossz['bek_hiany'] += len(r['bek_hiany']); ossz['nem_elemz'] += len(r['nem_elemz'])
        ossz['biro_nincs'] += sum(1 for b in r['biro'] if 'NINCS EMLÍTVE' in b)
    print(f"ÖSSZESEN: {len(ns)} tétel; előírt §: {ossz['eloirt']}; dobozban: {ossz['dobozban']}; csak hivatkozva: {ossz['csak_hiv']}; "
          f"hiányzik: {ossz['hiany']}; bekezdés-hiányos §: {ossz['bek_hiany']}; nem említett iránymutatás: {ossz['biro_nincs']}; "
          f"nem elemezhető kiírás-elem: {ossz['nem_elemz']}")


def korpusz_hiany(tol, ig):
    F = kozos.forrasok(); JOG = kozos.korpusz_jogszabalyok()
    man = json.load(open(os.path.join(kozos.GYOKER, 'korpusz', 'manifest.json'), encoding='utf-8'))
    manf = {unicodedata.normalize('NFC', x['file']) for x in man.get('items', [])}
    per_forras = {}; rendben = []; fej_cache = {}
    for t in kozos.tetelsor()['tetelek']:
        n = t['sorszam']
        if not tol <= n <= ig:
            continue
        gond = []
        for e in t['eloirasok']:
            kod = e['forras']; f = F.get(kod)
            ok = None
            if not f:
                ok = 'a forrás nincs a tetelsor/forrasok.json-ban'
            elif not f.get('korpusz'):
                ok = 'a forrasok.json szerint nincs a korpuszban'
            else:
                for fn in f['korpusz']:
                    if not kozos.korpusz_fajl(fn):
                        ok = f'a fájl hiányzik a korpusz/ mappából ({fn})'; break
                    if unicodedata.normalize('NFC', 'korpusz/' + fn) not in manf:
                        ok = f'a fájl nincs a korpusz/manifest.json-ban ({fn})'; break
            if ok is None and 'tol' in e:
                if kod not in JOG:
                    ok = 'a jogszabály §-tagolása nem olvasható'
                elif E.tartomany(JOG[kod][1], e['tol'], e['ig']) is None:
                    ok = f"a {e['tol']}–{e['ig']}. § határa nincs a korpuszfájlban"
            if ok is None and 'fejezetek' in e:
                fp = fej_cache.setdefault(kod, fejezet_parok(kod)) or {}
                hf = [x for x in e['fejezetek'] if x not in fp]
                if hf:
                    ok = 'a fejezet nincs a korpuszfájlban: ' + ', '.join(hf)
            if ok:
                gond.append(f'{kod}: {ok}')
                per_forras.setdefault(kod, {'ok': ok, 'tetelek': []})['tetelek'].append(n)
        for x in szoveg_elemek(t):
            gond.append('nem elemezhető kiírás-elem: ' + x)
        if gond:
            print(f'{n}. tétel: ' + '; '.join(gond))
        else:
            rendben.append(n)
    print(f'rendben (minden kiírt forrás a korpuszban): {len(rendben)} tétel' + (f" ({', '.join(map(str, rendben))})" if rendben else ''))
    print('forrásonként:')
    if not per_forras:
        print('  nincs hiányzó forrás')
    for kod, v in sorted(per_forras.items()):
        print(f"  {kod}: {v['ok']} – tételek: {', '.join(map(str, v['tetelek']))}")
    print(f'ÖSSZESEN: {tol}–{ig}. tétel; hiányzó forrás: {len(per_forras)}; érintett tétel: {ig - tol + 1 - len(rendben)}')


if __name__ == '__main__':
    a = sys.argv[1:]
    if not a or a[0] in ('-h', '--help'):
        print(__doc__); sys.exit(0)
    if a[0] == '--korpusz-hiany':
        tol, ig = (int(a[1]), int(a[2])) if len(a) >= 3 else (22, 85)
        korpusz_hiany(tol, ig)
    else:
        fo_mod([int(x) for x in a])
    sys.exit(0)
