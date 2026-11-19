#!/usr/bin/env python3
"""S1 – a publikált jegyzetek (jegyzetek/NN/<noteId>.html) → a tétel munkaszövege (NN.txt).

    python3 tools/jegyzet_txt.py            # mind: NN.txt + tetelsor/jegyzet_megfeleltetes.json, majd ellenőrzés
    python3 tools/jegyzet_txt.py --ellenor  # csak ellenőrzés: a meglévő NN.txt betűre a jegyzetek szövegét adja-e
    python3 tools/jegyzet_txt.py 7 12       # csak a megadott tételek

A kiindulás a publikált jegyzet (01_dontesek.md, 2026-11-19); a régi tételsor szövegét a program nem olvassa.
Az NN.txt az A/1 tételszövegeinek alakját követi, mert a közös eszközök (kozos.dobozok, ellenorzes.py,
doboz_teljesseg.py, kontroll.py, termek_gyart.py) ezt értik:
  - bekezdésenként egy sor, a bekezdések között üres sor;
  - a címsor (h1–h4) csupa nagybetűs sor;
  - a jogszabálydoboz: a fejléc külön sor („Pp. 8. §”), utána a normasorok soronként (a <br> és a <p> sort tör);
  - a felsorolás elemei „- ” kezdetű sorok.
A tétel a jegyzetrészek összefűzése a jegyzetek/manifest.json sorrendjében; a részek határát és a noteId-t a
tetelsor/jegyzet_megfeleltetes.json őrzi (az élesítéskor a javított szöveg ugyanazokra a jegyzetekre kerül vissza).

Zárókapu (--ellenor, és minden írás után): részenként a jegyzet HTML-jének szövege és az NN.txt megfelelő
sortartománya betű- és számjegysorozatként (kis- és nagybetűt nem különböztetve) azonos. Utolsó sor:
  jegyzet_txt: tétel N, rész M, karakter K, eltérés E
Csak a standard könyvtárat használja; Python 3.9-től fut.
"""
import html.parser, json, os, re, sys, unicodedata

GY = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
CIM = ('h1', 'h2', 'h3', 'h4', 'h5', 'h6')
BLOKK = ('p', 'li', 'div', 'tr', 'blockquote') + CIM


class Atalakito(html.parser.HTMLParser):
    """A jegyzet HTML-je → sorok. Egy sor = egy bekezdés, címsor, dobozfejléc, normasor vagy listaelem."""

    def __init__(self):
        super().__init__(convert_charrefs=True)
        self.sorok = []          # (típus, szöveg): 'cim' | 'p' | 'li' | 'fej' | 'norma'
        self.puffer = []
        self.tipus = 'p'
        self.doboz = 0           # a nyitott jogszabaly-doboz div mélysége (0 = nincs)
        self.melyseg = 0
        self.cimke = False
        self.osszes = []         # minden szövegcsomó (az ellenőrzéshez)
        self.spanok = []         # a nyitott span-ek: True, ha blokkszintű (jogszabaly-pont vagy display:block)

    def zar(self):
        s = re.sub(r'\s+', ' ', ''.join(self.puffer).replace('\xa0', ' ')).strip()
        self.puffer = []
        if not s:
            return
        t = self.tipus
        if self.doboz and t not in ('fej',):
            t = 'norma'
        self.sorok.append((t, s))

    def handle_starttag(self, tag, attrs):
        osztaly = dict(attrs).get('class') or ''
        if tag == 'div':
            self.melyseg += 1
            if 'jogszabaly-doboz' in osztaly and not self.doboz:
                self.zar()
                self.doboz = self.melyseg
                return
        if tag == 'span':
            if 'jogszabaly-cimke' in osztaly:
                self.zar()
                self.cimke, self.tipus = True, 'fej'
                self.spanok.append(False)
                return
            # A felsorolás pontja a jegyzetben blokkszintű span (class jogszabaly-pont, style display:block):
            # előtte és utána sort kell törni, különben a pontok egybefolynak („haa) …,b) …(4) …”).
            stilus = re.sub(r'\s+', '', dict(attrs).get('style') or '')
            blokk = 'jogszabaly-pont' in osztaly or 'display:block' in stilus
            if blokk:
                self.zar()
            self.spanok.append(blokk)
            return
        if tag == 'br':
            if self.doboz:
                self.zar()          # a dobozban a sortörés új normasor
            else:
                self.puffer.append(' ')
            return
        if tag in BLOKK:
            self.zar()
            self.tipus = 'cim' if tag in CIM else 'li' if tag == 'li' else 'p'

    def handle_endtag(self, tag):
        if tag == 'span':
            blokk = self.spanok.pop() if self.spanok else False
            if self.cimke:
                self.zar()
                self.cimke, self.tipus = False, 'p'
            elif blokk:
                self.zar()
            return
        if tag in BLOKK:
            self.zar()
            self.tipus = 'p'
        if tag == 'div':
            if self.doboz and self.melyseg == self.doboz:
                self.doboz = 0
            self.melyseg -= 1

    def handle_data(self, d):
        self.puffer.append(d)
        self.osszes.append(d)

    def close(self):
        super().close()
        self.zar()


def be(ut):
    return open(os.path.join(GY, ut), encoding='utf-8').read()


def resz_sorok(fajl):
    a = Atalakito()
    a.feed(be(fajl))
    a.close()
    ki = []
    for tipus, s in a.sorok:
        s = unicodedata.normalize('NFC', s)
        if tipus == 'cim':
            ki.append(s.upper())
        elif tipus == 'li':
            ki.append('- ' + s)
        else:
            ki.append(s)
    return ki, ''.join(a.osszes)


def betuk(s):
    """Összevetéshez: csak betű és számjegy, kisbetűsítve (a címsor nagybetűsítése és a szóközök nem számítanak)."""
    return ''.join(c for c in unicodedata.normalize('NFC', s).casefold() if c.isalnum())


_R = {'I': 1, 'V': 5, 'X': 10, 'L': 50}
IRANYMUTATAS = re.compile(r'^(?:PK|MK|GK|PK-GK|KMK|\d+/\d{4})')


def romai(s):
    v = 0
    for i, c in enumerate(s):
        v += -_R[c] if i + 1 < len(s) and _R[s[i + 1]] > _R[c] else _R[c]
    return v


def sorrend_kulcs(x):
    """A jegyzetrész helye a tételen belül (a manifest sorrendje nem olvasási sorrend).
    1. a tartalom első római számos főcíme (h2: „III. …”); 2. ennek híján a cím római tartománya („(I-III.) …”)
    és a cím vezető sorszáma („2.) …”); 3. ennek híján a cím vezető sorszáma mint főpont („3. …” → a III. után);
    a bírói iránymutatás külön jegyzetei (PK, MK, n/éééé) a tétel végére kerülnek, név szerint.
    Vissza: (kulcs, alap) – az alap a megfeleltetésbe kerül, hogy a sorrend ellenőrizhető legyen."""
    cim = x['cim'].strip()
    if IRANYMUTATAS.match(cim):
        return (99, 0, 0, cim), 'iránymutatás (a tétel végén)'
    tn = re.match(r'^(\d+)\s*[.)]+', cim)
    tn = int(tn.group(1)) if tn else 0
    for m in re.finditer(r'<h2[^>]*>(.*?)</h2>', be(x['file']), re.S):
        r = re.match(r'^\s*([IVXL]+)\.\s', re.sub(r'<[^>]+>', '', m.group(1)))
        if r:
            return (romai(r.group(1)), 0, tn, cim), 'a tartalom főcíme: %s.' % r.group(1)
    r = re.match(r'^(?:\d+\s*[.)]+\s*)*\(([IVXL]+)(?:\s*-\s*[IVXL]+)?\.\)', cim)
    if r:
        return (romai(r.group(1)), 1, tn, cim), 'a cím római tartománya (a tartalomban nincs római főcím)'
    if tn:
        return (tn, 2, 0, cim), 'a cím vezető sorszáma (a tartalomban nincs római főcím)'
    return (50, 0, 0, cim), 'nem besorolható (cím szerint)'


def tetelek_reszei():
    man = json.loads(be('jegyzetek/manifest.json'))
    t = {}
    for x in man['items']:
        t.setdefault(x['sorszam'], []).append(x)
    for n in t:
        if len(t[n]) == 1:
            t[n][0]['_alap'] = 'egyetlen rész'
            continue
        par = [(sorrend_kulcs(x), x) for x in t[n]]
        par.sort(key=lambda p: p[0][0])
        for (kulcs, alap), x in par:
            x['_alap'] = alap
        t[n] = [x for _, x in par]
    return t


def general(n, reszek):
    sorok, megf = [], []
    for r in reszek:
        rs, _ = resz_sorok(r['file'])
        kezdet = len(sorok) + 1
        for s in rs:
            sorok.extend([s, ''])
        megf.append({'noteId': r['id'], 'fajl': r['file'], 'cim': r['cim'], 'sorrendAlap': r.get('_alap', ''), 'sorTol': kezdet, 'sorIg': len(sorok),
                     'karakter': sum(len(s) for s in rs)})
    szoveg = '\n'.join(sorok).rstrip('\n') + '\n'
    return szoveg, megf


def ellenor(n, megf):
    """Részenként: az NN.txt sortartománya és a jegyzet HTML-szövege betűre azonos-e. Vissza: hibalista."""
    ut = '%02d.txt' % n
    if not os.path.exists(os.path.join(GY, ut)):
        return ['%d. tétel: nincs %s' % (n, ut)]
    L = be(ut).split('\n')
    hibak = []
    for r in megf:
        _, nyers = resz_sorok(r['fajl'])
        txt = '\n'.join(re.sub(r'^- ', '', s) for s in L[r['sorTol'] - 1:r['sorIg']])
        a, b = betuk(nyers), betuk(txt)
        if a != b:
            i = next((k for k in range(min(len(a), len(b))) if a[k] != b[k]), min(len(a), len(b)))
            hibak.append('%d. tétel, %s: eltérés a(z) %d. betűnél (jegyzet: …%s… / txt: …%s…)' % (n, r['noteId'], i, a[max(0, i - 20):i + 20], b[max(0, i - 20):i + 20]))
    return hibak


def main():
    csak_ellenor = '--ellenor' in sys.argv
    szuk = {int(a) for a in sys.argv[1:] if a.isdigit()}
    reszek = tetelek_reszei()
    mut = os.path.join(GY, 'tetelsor', 'jegyzet_megfeleltetes.json')
    regi = json.load(open(mut, encoding='utf-8')) if os.path.exists(mut) else {'sema': 1, 'tetelek': {}}
    hibak, db, kar = [], 0, 0
    for n in sorted(reszek):
        if szuk and n not in szuk:
            continue
        kulcs = '%02d' % n
        if csak_ellenor:
            megf = regi['tetelek'].get(kulcs)
            if megf is None:
                hibak.append('%d. tétel: nincs megfeleltetés (előbb a gyártás fusson)' % n)
                continue
        else:
            szoveg, megf = general(n, reszek[n])
            ut = os.path.join(GY, '%02d.txt' % n)
            if os.path.exists(ut) and '--felulir' not in sys.argv and open(ut, encoding='utf-8').read() != szoveg:
                hibak.append('%d. tétel: a %02d.txt már létezik és eltér (a tételmunka módosította?) – nem írtam felül; szándékos újragyártás: --felulir' % (n, n))
                continue
            open(ut, 'w', encoding='utf-8').write(szoveg)
            regi['tetelek'][kulcs] = megf
        hibak += ellenor(n, megf)
        db += len(megf)
        kar += sum(r['karakter'] for r in megf)
    if not csak_ellenor:
        json.dump(regi, open(mut, 'w', encoding='utf-8'), ensure_ascii=False, indent=1)
    bizonytalan = sorted(k for k, v in regi['tetelek'].items() if any('nincs római főcím' in r.get('sorrendAlap', '') or 'nem besorolható' in r.get('sorrendAlap', '') for r in v))
    if bizonytalan:
        print('ellenőrizendő részsorrend (a tartalomban nincs római főcím): ' + ', '.join(bizonytalan))
    for h in hibak:
        print('HIBA: ' + h)
    print('jegyzet_txt: tétel %d, rész %d, karakter %d, eltérés %d' % (len([n for n in reszek if not szuk or n in szuk]), db, kar, len(hibak)))
    sys.exit(1 if hibak else 0)


if __name__ == '__main__':
    main()
