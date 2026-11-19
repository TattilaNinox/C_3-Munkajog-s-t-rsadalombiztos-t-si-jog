#!/usr/bin/env python3
"""A hivatalos tételsor szöveges kivonatából tételenkénti, gépileg olvasható előírásjegyzék.

Használat (a tároló gyökeréből):
    python3 tools/tetelsor_feldolgoz.py tetelsor/A1_tetelsor_2026.txt tetelsor/forrasok.json > tetelsor/tetelsor.json

Bemenet: a PDF `pdftotext -layout` kimenete. A forráskódok a forrasok.json-ból jönnek.
A részleges pontokat (pl. „PK 9. III., IV., VII. pontja”) a RESZLEGES tábla rögzíti, mert a
tételsor szövege ezeket nem egységesen írja; a táblát a PDF-fel egyeztetve kell karbantartani.
A szkript leáll, ha egy előírás-szöveg részét nem tudja forráshoz rendelni.
"""
import re, sys, json

SZOVEG, FORRASOK = sys.argv[1], sys.argv[2]
KODOK = {f['kod'] for f in json.load(open(FORRASOK, encoding='utf-8'))['forrasok']}

# Hosszú jogszabálynevek a tételsorban -> forráskód (a sorrend számít: a hosszabb elöl).
NEVEK = [
    (r'a gondnokoltak és előzetes jognyilatkozatok nyilvántartásáról szóló 2013\. évi CLXXV\. törvény', 'Gnytv'),
    (r'a szerzői jogról szóló 1999\. évi LXXVI\. törvény', 'Szjt'),
    (r'a szomszédjogok és a tulajdonjog korlátainak különös szabályairól szóló 2013\. évi CLXXIV\. törvény', 'Sztv'),
    (r'a kisajátításról szóló 2007\. évi CXXIII\. törvény', 'Kstv'),
    (r'a társasházakról szóló 2003\. évi CXXXIII\. törvény', 'Tht'),
    (r'a Polgári Törvénykönyvről szóló 2013\. évi V\. törvény módosításáról szóló 2016\. évi LXXVII\. törvény', 'PtkMod2016'),
    (r'az ingatlan-nyilvántartásról szóló 2021\. évi C\. törvény', 'Inytv'),
    (r'a fogyasztó és a vállalkozás közötti szerződések részletes szabályairól szóló 45/2014\. \(II\. 26\.\) Korm\. rendelet', 'FgyR'),
    (r'A családok védelméről szóló 2011\. évi CCXI\. törvény \(Csvt\)\.', 'Csvt'),
    (r'Csvt\.', 'Csvt'),
    (r'\bBét\b', 'Bét'),
    (r'Ptké\.', 'Ptké'),
    (r'Ptk\.', 'Ptk'),
]
BIROSAGI = [
    (r'(\d)/(\d{4})\.(?:\s*\([^)]*\))?\s*PK vélemény', lambda m: f'{m.group(1)}/{m.group(2)}. PK vélemény'),
    (r'(\d)/(\d{4})\.\s*KPJE', lambda m: f'{m.group(1)}/{m.group(2)}. KPJE'),
    (r'(\d)/(\d{4})\.?\s*PJE', lambda m: f'{m.group(1)}/{m.group(2)}. PJE'),
    (r'\b(PK|GK) (\d+)\.', lambda m: f'{m.group(1)} {m.group(2)}'),
    (r'XXV\. számú Polgári Elvi Döntés', lambda m: 'XXV. PED'),
]
PAR = r'(\d+(?::\d+)?(?:/[A-Z])?)\.\s?§'
PAR_RX = re.compile(PAR + r'(?:\s*\((\d+)\)\s*bekezdése)?(?:\s*-\s*' + PAR + r')?')

# Részleges körök: (tétel, forráskód) -> a tételsor szövege szerinti terjedelem.
RESZLEGES = {
    (6, 'IHRA'): {'resz': 'az antiszemitizmus definíciója (a tételsorban szó szerint idézve)'},
    (7, 'Szjt'): {'fejezetek': ['I', 'II', 'III', 'IV', 'XI']},
    (13, 'PK 9'): {'pontok': ['III', 'IV', 'VII']},
    (31, '1/2010. PK vélemény'): {'pontok': ['10']},
    (32, '1/2011. PK vélemény'): {'pontok': ['1', '2', '3', '4', '5', '6', '7', '9', '10', '11', '12']},
    (48, 'XXV. PED'): {'pontok': ['I', 'II', 'IV', 'V'], 'kiveve': 'az I. pont utolsó mondata és az ahhoz kapcsolódó indokolás'},
    (73, 'PK 279'): {'pontok': ['II']},
    (74, 'PK 298'): {'pontok': ['I', 'III']},
}
# Ahol a tételsor nem a teljes jogszabályt, hanem csak felsorolt §-okat jelöl, az egész-törvény
# tétel nem keletkezik; ahol a jogszabály neve § nélkül áll, a teljes jogszabály előírt.

ELOIRAS_KEZD = re.compile(r'\s(?=(?:Ptk\.|Ptké\.|Bét;|a szerzői jogról szóló|a gondnokoltak és|'
                          r'a szomszédjogok és a tulajdonjog|a kisajátításról szóló))')


def tetelek_olvas(path):
    L = open(path, encoding='utf-8').read().split('\n')
    out, cur, csoport = [], None, None
    for raw in L:
        s = raw.strip()
        if not s or re.fullmatch(r'\d+', s):
            continue
        if s.isupper() and len(s) > 8 and not re.search(r'\d', s):
            csoport = s
            continue
        m = re.match(r'^(\d{1,2})\.\s+(\S.*)$', s)
        if m and (cur is None and m.group(1) == '1' or cur and int(m.group(1)) == cur['sorszam'] + 1):
            cur = {'sorszam': int(m.group(1)), 'csoport': csoport, 'sorok': [m.group(2)]}
            out.append(cur)
            continue
        if cur:
            cur['sorok'].append(s)
    return out


def bontas(sorszam, szoveg):
    """Az előírás-szöveg tokenekre bontása sorrendben: jogszabály-jelzés, §, bírósági iránymutatás."""
    tokenek = []
    for rx, kod in NEVEK:
        for m in re.finditer(rx, szoveg):
            tokenek.append((m.start(), m.end(), 'jog', kod))
    for rx, f in BIROSAGI:
        for m in re.finditer(rx, szoveg):
            tokenek.append((m.start(), m.end(), 'bir', f(m)))
    for m in PAR_RX.finditer(szoveg):
        tokenek.append((m.start(), m.end(), 'par', m))
    # átfedések: a hosszabb, korábbi nyer
    tokenek.sort(key=lambda t: (t[0], -(t[1] - t[0])))
    tiszta, veg = [], -1
    for t in tokenek:
        if t[0] >= veg:
            tiszta.append(t); veg = t[1]
    eloirasok, kontextus, volt_par = [], None, {}
    for start, end, tip, ertek in tiszta:
        if tip == 'jog':
            kontextus = ertek
            volt_par.setdefault(ertek, False)
            eloirasok.append({'forras': ertek, '_jel': True})
        elif tip == 'bir':
            e = {'forras': ertek}
            e.update(RESZLEGES.get((sorszam, ertek), {}))
            eloirasok.append(e)
            kontextus = None
        else:
            if kontextus is None:
                raise SystemExit(f'{sorszam}. tétel: § forrás nélkül: {ertek.group(0)!r}')
            tol, bek, ig = ertek.group(1), ertek.group(2), ertek.group(3)
            e = {'forras': kontextus, 'tol': tol, 'ig': ig or tol}
            if bek:
                e['bekezdes'] = bek
            eloirasok.append(e)
            volt_par[kontextus] = True
    # jogszabály-jelzés §-ok nélkül = a teljes jogszabály (vagy a RESZLEGES szerinti rész)
    vegso = []
    for i, e in enumerate(eloirasok):
        if e.get('_jel'):
            kov = eloirasok[i + 1] if i + 1 < len(eloirasok) else None
            if kov and kov.get('forras') == e['forras'] and 'tol' in kov:
                if (sorszam, e['forras']) in RESZLEGES:
                    vegso.append({'forras': e['forras'], **RESZLEGES[(sorszam, e['forras'])]})
                continue
            k = {'forras': e['forras'], 'teljes': True}
            if (sorszam, e['forras']) in RESZLEGES:
                k = {'forras': e['forras'], **RESZLEGES[(sorszam, e['forras'])]}
            vegso.append(k)
        else:
            vegso.append(e)
    for e in vegso:
        if e['forras'] not in KODOK:
            raise SystemExit(f'{sorszam}. tétel: ismeretlen forráskód: {e["forras"]}')
    return vegso


def main():
    eredmeny = []
    for t in tetelek_olvas(SZOVEG):
        egesz = re.sub(r'\s+', ' ', ' '.join(t['sorok'])).strip()
        m = ELOIRAS_KEZD.search(egesz)
        if not m:
            raise SystemExit(f'{t["sorszam"]}. tétel: nem található az előírás kezdete')
        cim, eloiras = egesz[:m.start()].strip(), egesz[m.start():].strip()
        megj = None
        if t['sorszam'] == 6:
            i = eloiras.find('A Stockholmi Nyilatkozat')
            megj, eloiras = eloiras[i:], eloiras[:i].strip() + ' ' + 'IHRA'
        szoveg_bontashoz = eloiras.replace('IHRA', '') if t['sorszam'] != 6 else eloiras
        el = bontas(t['sorszam'], szoveg_bontashoz.replace(' IHRA', ''))
        if t['sorszam'] == 6:
            el.append({'forras': 'IHRA', **RESZLEGES[(6, 'IHRA')]})
            eloiras = eloiras[:-len(' IHRA')]
        rec = {'sorszam': t['sorszam'], 'csoport': t['csoport'], 'cim': cim,
               'eloirasSzoveg': eloiras, 'eloirasok': el}
        if megj:
            rec['tetelsorMegjegyzes'] = megj
        eredmeny.append(rec)
    if [r['sorszam'] for r in eredmeny] != list(range(1, len(eredmeny) + 1)):
        raise SystemExit('A tételek sorszáma nem folytonos')
    json.dump({'tetelsor': 'A/1. A polgári jog és a családjog', 'ev': 2026,
               'forras': 'tetelsor/A1_Ptk_Szobeli_tetelsor_2026.pdf',
               'altalanosEloiras': {'szoveg': 'Az alábbi jogszabályok átfogó ismerete szükséges (a felsorolás nem teljes körű)',
                                    'forrasok': ['Ptk', 'Ptké', 'Tht', 'Sztv', 'Bét']},
               'tetelek': eredmeny}, sys.stdout, ensure_ascii=False, indent=1)
    print()


main()
