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


HAT_TIPUS = [
    ('AB', r'AB\s*(?:határozat|végzés|hat\.)'),
    ('JE', r'(?:számú\s+)?(?:Büntető-polgári|Büntető-\s*polgári|Büntető|Polgári|Közigazgatási|Munkaügyi|Közigazgatási-munkaügyi|közigazgatási-munkaügyi-polgári|polgári)?\s*(?:jogegységi határozat|BJE|PJE|KJE|KPJE|KMJE|MJE|BPJE|BKPJE|JEH)'),
    ('VELEMENY', r'(?:BK|PK|GK|KK|MK|KMK|BKv|PKv)\.?\s*(?:vélemény|kollégiumi vélemény|állásfoglalás)?'),
    ('RENDELET', r'(?:Korm\.?|[A-ZÁÉÍÓÖŐÚÜŰ][A-Za-zÁÉÍÓÖŐÚÜŰáéíóöőúüű]{0,7}M|MNB|NGM|IM|BM|EüM|PM|NM|HM|KüM|MT|ME|OBH|LÜ|ORFK)\.?\s*(?:rendelet|r\.|utasítás|határozat)'),
]
SZAMEV = re.compile(r'(\d{1,4})/(\d{4})\.?\s*(?:\(\s*([IVXL]+)\.\s*(\d{1,2})\.?\s*\)\s*)?(?:számú\s+)?(' + '|'.join(t for _, t in HAT_TIPUS) + r')')
KOLL = re.compile(r'\b(?:(BK|PK|GK|KK|MK|KMK)\s+(\d{1,3})\.(?!\s*\d)|(\d{1,3})\.\s*(?:számú\s+)?(BK|PK|GK|KK|MK|KMK)\s*(?:vélemény|állásfoglalás)|(BKv|PKv)\.?\s*(\d{1,3})\.?)')
TORVENY = re.compile(r'(\d{4})\.\s*évi\s+([IVXLCDM]+)\.\s*(törvény|törvényerejű rendelet|tvr\.?)')
ESETI = re.compile(r'\b(BH|EBH|EH|BDT|EBD|KGD|ÍH|KJD)[\s.]{0,2}(\d{4})\.\s?([0-9A-Z]+(?:\.[0-9A-Z]+)*)\.?')
EUX = re.compile(r'\b(\d{1,4})[/_](\d{1,4})[/_ ]\s?(EU|EK|EGK|Euratom|IB|KKBP)\b')


def ev_e(x):
    return len(x) == 4 and 1957 <= int(x) <= 2030

EU3 = re.compile(r'\((EU|EK|EU, Euratom)\)\s*(\d{4})/(\d{1,4})\b')
EU4 = re.compile(r'\b(20\d{2})/(\d{2,4})\s+(irányelv|rendelet)')
EUB = re.compile(r'\b([CT])-\s?(\d{1,4})/(\d{2})\b')
ROVID_DEF = re.compile(r'(\d{4})\.\s*évi\s+([IVXLCDM]+)\.\s*törvény\s*(?:\((?:a\s+)?(?:továbbiakban:?\s*)?([^()]{2,16}?)\)|\s-\s([A-ZÁÉÍÓÖŐÚÜŰ][^\s,;]{1,12}\.?(?:\s?tv\.)?))')
ROVID_HASZN = re.compile(r'\b([A-ZÁÉÍÓÖŐÚÜŰ][A-Za-zÁÉÍÓÖŐÚÜŰáéíóöőúüű]{0,9}\.(?:\s?tv\.)?)\s+(?:[IVXLC]+\.\s*[Ff]ejezet|\d+(?::\d+)?(?:/[A-Z])?[.\-, \d/A-Z:]{0,30}?§)')
NEM_ROVID = {'Az', 'A', 'Lásd', 'És', 'Ld.', 'Pl.', 'Vö.', 'Kúria', 'BH', 'EBH', 'EH', 'BDT', 'EBD', 'BK', 'PK', 'GK', 'KK', 'MK', 'KMK', 'Különös',
             'Általános', 'Rész', 'Könyv', 'Fejezet', 'Cím', 'Tanács', 'Európai', 'Bizottság', 'Jegyzőkönyv', 'Egyezmény', 'Charta', 'C', 'T'}


def eseti_kulcs(fajta, ev, kod):
    """EBH 2017.B.5 = EH 2017.02.B5; BH 2019.8.220 -> a sorszám az utolsó elem."""
    fajta = {'EBH': 'EH'}.get(fajta, fajta)
    reszek = [r for r in kod.strip('.').split('.') if r]
    veg = reszek[-1]
    if veg.isdigit() and len(reszek) > 1 and re.fullmatch(r'[A-Z]', reszek[-2]):
        veg = reszek[-2] + veg
    return ('eseti', fajta, ev, veg.lstrip('0') or '0')


JE_ROV = (('Büntető-polgári', 'BPJE'), ('Büntető- polgári', 'BPJE'), ('Közigazgatási-munkaügyi-polgári', 'KMPJE'), ('Közigazgatási-munkaügyi', 'KMJE'),
          ('Közigazgatási-polgári', 'KPJE'), ('Büntető', 'BJE'), ('Polgári', 'PJE'), ('Közigazgatási', 'KJE'), ('Munkaügyi', 'MJE'))


def valaszt(nev, talalt):
    """Több egyező korpuszfájl közül a megnevezés fajtájához illő (1/2005. BJE és 1/2005. BPJE külön határozat)."""
    talalt = sorted(talalt)
    if len(talalt) < 2:
        return talalt
    rov = next((r for teljes, r in JE_ROV if teljes.lower() in nev.lower()), None) or next((r for _, r in JE_ROV if re.search(r'\\b%s\\b' % r, nev)), None)
    if rov:
        illo = [f for f in talalt if re.search(r'(?<![A-Z])%s(?![A-Z])' % rov, f)]
        if illo:
            return illo
    return talalt


def tetelek(nyers):
    """A kiírás tételei (az alapfelvetel.py szabálya szerint) – a hivatkozó tétel megnevezéséhez."""
    sorok = [s.replace('\x0c', '') for s in nyers.split('\n')]
    sorok = [s for s in sorok if not re.fullmatch(r'\s*\d+\s*', s)]
    out, akt = [], None
    for s in sorok:
        t = s.strip()
        if not t:
            continue
        m = re.match(r'^(\d{1,3})\.\s+(?=[A-ZÁÉÍÓÖŐÚÜŰ„])(.*)$', t)
        if m and int(m.group(1)) == len(out) + 1:
            akt = {'n': int(m.group(1)), 'sorok': [m.group(2)]}
            out.append(akt)
        elif akt is not None:
            akt['sorok'].append(t)
        else:
            out.append({'n': 0, 'sorok': [t]}) if not out else out[0]['sorok'].append(t) if out[0]['n'] == 0 else None
    for t in out:
        t['szoveg'] = lapit(' '.join(t.pop('sorok')))
    return out


def hivatkozasok(szoveg):
    """[(kulcs, megnevezés)] – a kulcs alapján kötjük a korpuszfájlhoz."""
    ki = []
    for m in SZAMEV.finditer(szoveg):
        tip = next(k for k, t in HAT_TIPUS if re.fullmatch(t, m.group(5)))
        ki.append((('szamev', m.group(1), m.group(2), tip), re.sub(r'\s+', ' ', m.group(0)).strip()))
    for m in KOLL.finditer(szoveg):
        koll, szam = (m.group(1), m.group(2)) if m.group(1) else (m.group(4), m.group(3)) if m.group(3) else (m.group(5)[:2], m.group(6))
        if re.search(r'/\d{4}', szoveg[m.end():m.end() + 6]) or szoveg[max(0, m.start() - 1):m.start()] == '/':
            continue
        ki.append((('koll', koll, szam), '%s %s.' % (koll, szam)))
    for m in TORVENY.finditer(szoveg):
        ki.append((('tv', m.group(1), m.group(2)), '%s. évi %s. %s' % (m.group(1), m.group(2), 'törvény' if m.group(3) == 'törvény' else 'tvr.')))
    for m in ESETI.finditer(szoveg):
        ki.append((eseti_kulcs(m.group(1), m.group(2), m.group(3)), '%s %s.%s' % (m.group(1), m.group(2), m.group(3))))
    for m in EUX.finditer(szoveg):
        x, y = m.group(1), m.group(2)
        if ev_e(y):
            szam, ev = x, y
        elif ev_e(x) or len(x) == 2:
            szam, ev = y, x
        else:
            continue
        ev = ev if len(ev) == 4 else ('19' + ev if int(ev) > 50 else '20' + ev)
        ki.append((('eu', str(int(szam)), ev), m.group(0)))
    for rx, f in ((EU3, lambda m: (m.group(3), m.group(2))), (EU4, lambda m: (m.group(2), m.group(1)))):
        for m in rx.finditer(szoveg):
            szam, ev = f(m)
            ki.append((('eu', str(int(szam)), ev), m.group(0)))
    for m in EUB.finditer(szoveg):
        ki.append((('eub', m.group(1), str(int(m.group(2))), m.group(3)), '%s-%s/%s' % (m.group(1), m.group(2), m.group(3))))
    if re.search(r'Alaptörvény', szoveg):
        ki.append((('nev', 'Alaptörvény'), 'Alaptörvény'))
    return ki


def fajl_kulcsok(nev):
    """A korpuszfájl nevéből képezhető kulcsok."""
    n = lapit(nev)
    k = set()
    m = re.match(r'^(\d{1,4})[_/](\d{4})(?!\d)(.*)$', n)
    if m:
        maradek = m.group(3).replace('_', ' ')
        tip = 'AB' if re.search(r'\bAB\b', maradek, re.I) else 'JE' if re.search(r'BJE|PJE|KJE|KPJE|MJE|BPJE|JEH|jogegységi', maradek) else \
              'VELEMENY' if re.search(r'vélemény|állásfoglalás', maradek) else 'RENDELET' if re.search(r'rendelet|utasítás', maradek) else '?'
        k.add(('szamev', m.group(1), m.group(2), tip))
    m = re.match(r'^(\d{1,3})\.\s*(BK|PK|GK|KK|MK|KMK)\b', n) or re.match(r'^(?:)(BK|PK|GK|KK|MK|KMK)[ _](\d{1,3})\b', n)
    if m:
        a, b = m.group(1), m.group(2)
        k.add(('koll', b, a) if a.isdigit() else ('koll', a, b))
    for m in TORVENY.finditer(n):
        k.add(('tv', m.group(1), m.group(2)))
        break
    m = re.match(r'^(BH|EBH|EH|BDT|EBD|KGD|ÍH|KJD)\s?(\d{4})\.?\s?([0-9A-Z]+(?:\.[0-9A-Z]+)*)', n)
    if m:
        k.add(eseti_kulcs(m.group(1), m.group(2), m.group(3)))
    for m in re.finditer(r'\b3(\d{4})[RLD](\d{4})\b', n):
        k.add(('eu', str(int(m.group(2))), m.group(1)))
    for m in re.finditer(r'\b([CT])-\s?(\d{1,4})[_/](\d{2})\b', n):
        k.add(('eub', m.group(1), str(int(m.group(2))), m.group(3)))
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
    FK = {}
    for f in fajlok:
        elso = next((l for l in open(os.path.join(korpusz, f), encoding='utf-8', errors='replace').read(3000).split('\n') if l.strip()), '')[:300]
        nev = re.sub(r'\.txt$', '', f)
        FK[f] = fajl_kulcsok(nev) | fajl_kulcsok(elso) | {k for k, _ in hivatkozasok(lapit(nev.replace('_', '/')))} | {k for k, _ in hivatkozasok(lapit(elso))}
    # rövidítések: a kiírás saját meghatározásai + a korpuszfájlok előtagjai
    rov_tv = {}
    for m in ROVID_DEF.finditer(egesz):
        r = (m.group(3) or m.group(4) or '').strip()
        if r and len(r) <= 14 and r[0].isupper():
            rov_tv[re.sub(r'\s', '', r).rstrip('.').lower()] = ('tv', m.group(1), m.group(2))
    forrasok = {}

    def felvesz(kulcs, nev, n):
        f = forrasok.setdefault(kulcs, {'nev': nev, 'tetelek': set()})
        f['tetelek'].add(n)

    for t in T:
        for kulcs, nev in hivatkozasok(t['szoveg']):
            felvesz(kulcs, nev, t['n'])
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
        talalt = [fn for fn, ks in FK.items() if kulcs in ks]
        if not talalt and kulcs[0] == 'szamev':
            talalt = [fn for fn, ks in FK.items() if any(k[:3] == kulcs[:3] and k[3] == '?' for k in ks if k[0] == 'szamev')]
        if not talalt and kulcs[0] == 'rov':
            talalt = [fn for fn, ks in FK.items() if any(k[0] == 'rov' and (k[1].startswith(kulcs[1]) or kulcs[1].startswith(k[1])) for k in ks)]
        talalt = valaszt(f['nev'], talalt)
        hasznalt.update(talalt)
        sorok.append({'tipus': kulcs[0], 'kulcs': list(kulcs), 'nev': f['nev'], 'tetelek': sorted(f['tetelek']), 'fajl': talalt})
    rend = {'tv': 0, 'rov': 1, 'nev': 2, 'szamev': 3, 'koll': 4, 'eseti': 5, 'eu': 6, 'eub': 7}
    sorok.sort(key=lambda s: (bool(s['fajl']), rend[s['tipus']], s['nev']))
    nem_hiv = [f for f in fajlok if f not in hasznalt]
    json.dump({'kiiras': kiiras, 'tetel': len([t for t in T if t['n']]), 'forrasok': sorok, 'nemHivatkozottFajl': nem_hiv},
              open(ki + '.json', 'w', encoding='utf-8'), ensure_ascii=False, indent=1)
    hi = [s for s in sorok if not s['fajl']]
    md = ['# Korpusz-felmérés a kiírásból', '', '- Kiírás: `%s`, tétel: %d; korpuszfájl: %d' % (kiiras, len([t for t in T if t['n']]), len(fajlok)),
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
