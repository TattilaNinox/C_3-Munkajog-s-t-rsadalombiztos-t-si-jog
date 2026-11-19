#!/usr/bin/env python3
"""A termékek egyetlen csomagfájlba fűzése a megjelenítő (admin előnézet, később kliens) számára.

    python3 tools/csomag_gyart.py                          # ki/a1_termekcsomag.json (a teljes tételsor)
    python3 tools/csomag_gyart.py --tetelek 12,38,64 --ki <fájl>   # szűkített minta (tesztadat)

A csomag csak a termekek/ mappa ellenőrzött fájljaiból áll; futás előtt a program lefuttatja a kapukat
(termek_ellenor, fa_ellenor, szamolo_ellenor, matrix_ellenor), és hibánál nem ír csomagot.
A `ki/` mappa nincs verziókezelve.

Szerkezet (sema 1):
  tetelsor, cim, commit, forrasok{kód: név}, fejlecek{"kód|§": fejléc},
  tetelek[{sorszam, cim, csoport, paragrafus, felsorolas, vazlatMondat, fak[], szamolok[], matrixok[]}],
  paragrafus_jegyzek{"NN": [elem]}, felsorolas{"NN": [lista]}, hangos_vazlat{"NN": {mondatokSzama, karakter, fopontok, hang}},
  dontesi_fa{id: fa}, szamolo{id: számoló}, fogalommatrix{id: mátrix},
  tetelszoveg{"NN": [blokk]} (a tétel teljes szövege a „Teljes tétel” panelhez: tools/tetel_blokk.py),
  tetelhang{"NN": [{cim, path}]} (a tétel élő felolvasása részenként, olvasási sorrendben: a hangos vázlat terve szerinti
  jegyzetek hangjának Storage-útvonala az élő exportból, egyeb/notes/; az aláírt címet lejátszáskor a szülő adja),
  osszesites{…darabszámok…}, sha256 (a csomag tartalmának lenyomata az `sha256` mező nélkül, kanonikus JSON-ból)
"""
import argparse, glob, hashlib, json, os, re, subprocess, sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import kozos
import tetel_blokk

T = os.path.join(kozos.GYOKER, 'termekek')
HANG_ELO = 'https://storage.googleapis.com/orlomed-f8f9f.firebasestorage.app/'


def be(*r):
    return json.load(open(os.path.join(T, *r), encoding='utf-8'))


def kapuk():
    for k in ('termek_ellenor.py', 'fa_ellenor.py', 'szamolo_ellenor.py', 'matrix_ellenor.py'):
        r = subprocess.run([sys.executable, os.path.join(kozos.GYOKER, 'tools', k)], capture_output=True, text=True)
        if r.returncode != 0:
            raise SystemExit(f'A(z) {k} kapu hibát jelzett, csomag nem készült:\n{r.stdout[-2000:]}{r.stderr[-2000:]}')


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--tetelek', default='')
    B = kozos.beallitas()
    ap.add_argument('--ki', default=os.path.join(kozos.GYOKER, 'ki', B['azon'] + '_termekcsomag.json'))
    a = ap.parse_args()
    kapuk()
    ts = kozos.tetelsor()
    szuk = {int(x) for x in a.tetelek.split(',') if x.strip()}
    kell = lambda n: not szuk or n in szuk
    forr = {f['kod']: f['nev'] for f in json.load(open(os.path.join(kozos.GYOKER, 'tetelsor', 'forrasok.json'), encoding='utf-8'))['forrasok']}
    cs = {'sema': 1, 'tetelsor': B['azon'], 'cim': B['cim'],
          'commit': subprocess.run(['git', '-C', kozos.GYOKER, 'rev-parse', 'HEAD'], capture_output=True, text=True).stdout.strip(),
          'szukitett': sorted(szuk), 'forrasok': {}, 'fejlecek': {}, 'tetelek': [],
          'paragrafus_jegyzek': {}, 'felsorolas': {}, 'hangos_vazlat': {}, 'dontesi_fa': {}, 'szamolo': {}, 'fogalommatrix': {}, 'tetelszoveg': {}, 'tetelhang': {}}
    fejlec = {}
    for t in ts['tetelek']:
        n = t['sorszam']
        for e in be('paragrafus_jegyzek', f'{n:02d}.json')['elemek']:
            fejlec.setdefault(f"{e['forras']}|{e['par']}", e['fejlec'])
    hasznalt = set()

    def alapok(lista):
        for x in lista:
            hasznalt.add(f"{x['forras']}|{x['par']}"); cs['forrasok'][x['forras']] = forr[x['forras']]

    for f in sorted(glob.glob(os.path.join(T, 'dontesi_fa', '*.json'))):
        d = json.load(open(f, encoding='utf-8'))
        if 'csomopontok' in d and any(kell(n) for n in d['tetel']):
            cs['dontesi_fa'][d['id']] = d
            for c in d['csomopontok'].values():
                alapok(c.get('alap', []))
    for f in sorted(glob.glob(os.path.join(T, 'szamolo', '*.json'))):
        d = json.load(open(f, encoding='utf-8'))
        if 'szabalyok' in d and any(kell(n) for n in d['tetel']):
            cs['szamolo'][d['id']] = d
            for s in d['szabalyok']:
                alapok(s.get('alap', []))
    # a fák számoló-hivatkozása a szűkített csomagban is feloldható legyen
    for d in list(cs['dontesi_fa'].values()):
        for c in d['csomopontok'].values():
            sz = c.get('szamolo')
            if sz and sz not in cs['szamolo']:
                x = be('szamolo', sz + '.json'); cs['szamolo'][sz] = x
                for s in x['szabalyok']:
                    alapok(s.get('alap', []))
    for f in sorted(glob.glob(os.path.join(T, 'fogalommatrix', B['azon'] + '_*.json'))):
        d = json.load(open(f, encoding='utf-8'))
        if any(kell(n) for n in d['tetelek']):
            cs['fogalommatrix'][d['id']] = d
    terv = {d['sorszam']: d for d in json.load(open(os.path.join(T, 'hangos_vazlat', 'tts_terv.json'), encoding='utf-8'))['dokumentumok']}
    for t in ts['tetelek']:
        n = t['sorszam']
        if not kell(n):
            continue
        reszek = []
        for nid in terv[n]['jegyzet']:
            j = json.load(open(os.path.join(kozos.GYOKER, 'egyeb', 'notes', f'{n:02d}', nid + '.json'), encoding='utf-8'))
            # A hang Storage-útvonala (audio/…): lejátszáskor a szülő kér hozzá aláírt címet (a nyilvános elérés megszűnik).
            ut = (j.get('audioPath') or '').strip().lstrip('/').split('?')[0]
            if not ut and j.get('audioUrl', '').startswith(HANG_ELO):
                ut = j['audioUrl'][len(HANG_ELO):].split('?')[0]
            if ut:
                m = re.match(r'^(\d+)\)\.?\s*(.*)$', j.get('title', ''))
                reszek.append((int(m.group(1)) if m else 0, m.group(2) if m else j.get('title', ''), ut))
        if not reszek or not all(re.match(r'^audio/[\w./-]+\.mp3$', r[2]) and '..' not in r[2] for r in reszek):
            raise SystemExit(f'{n}. tétel: nincs vagy szokatlan a felolvasás hangfájlja')
        cs['tetelhang'][f'{n:02d}'] = [{'cim': c, 'path': u} for _, c, u in sorted(reszek, key=lambda r: r[0])]
        k = f'{n:02d}'
        pj = be('paragrafus_jegyzek', k + '.json')['elemek']
        cs['paragrafus_jegyzek'][k] = pj
        cs['tetelszoveg'][k] = tetel_blokk.blokkok(n)
        for e in pj:
            cs['forrasok'][e['forras']] = e['forrasNev']
        fl = []
        if os.path.exists(os.path.join(T, 'felsorolas', k + '.json')):
            fl = be('felsorolas', k + '.json')['listak']
        if fl:
            cs['felsorolas'][k] = fl
        hv = be('hangos_vazlat', k + '.json')
        hang = be('hangos_vazlat', 'hang', k, '_meta.json')
        cs['hangos_vazlat'][k] = {'mondatokSzama': hv['mondatokSzama'], 'karakter': hv['karakter'], 'fopontok': hv['fopontok'],
                                  'hang': [{'fopont': x['fopont'], 'darabok': [y['fajl'] for y in x['darabok']], 'mondatok': x['mondatok']} for x in hang['fopontok']]}
        cs['tetelek'].append({'sorszam': n, 'cim': t['cim'], 'csoport': hv['csoport'], 'paragrafus': len(pj), 'felsorolas': len(fl),
                              'vazlatMondat': hv['mondatokSzama'],
                              'fak': [i for i, d in cs['dontesi_fa'].items() if n in d['tetel']],
                              'szamolok': [i for i, d in cs['szamolo'].items() if n in d['tetel']],
                              'matrixok': [i for i, d in cs['fogalommatrix'].items() if n in d['tetelek']]})
    for h in sorted(hasznalt):
        if h not in fejlec:
            raise SystemExit('Nincs fejléc a hivatkozott §-hoz: ' + h)
        cs['fejlecek'][h] = fejlec[h]
    cs['forrasok'] = dict(sorted(cs['forrasok'].items()))
    cs['osszesites'] = {'tetel': len(cs['tetelek']), 'paragrafusDoboz': sum(len(v) for v in cs['paragrafus_jegyzek'].values()),
                        'felsorolasLista': sum(len(v) for v in cs['felsorolas'].values()),
                        'felsorolasElem': sum(len(l['elemek']) for v in cs['felsorolas'].values() for l in v),
                        'vazlatMondat': sum(v['mondatokSzama'] for v in cs['hangos_vazlat'].values()),
                        'fa': len(cs['dontesi_fa']), 'faCsomopont': sum(len(d['csomopontok']) for d in cs['dontesi_fa'].values()),
                        'faPelda': sum(len(d['peldak']) for d in cs['dontesi_fa'].values()),
                        'szamolo': len(cs['szamolo']), 'szamoloSzabaly': sum(len(d['szabalyok']) for d in cs['szamolo'].values()),
                        'szamoloPelda': sum(len(d['peldak']) for d in cs['szamolo'].values()),
                        'matrix': len(cs['fogalommatrix']), 'matrixCella': sum(len(d['cellak']) for d in cs['fogalommatrix'].values())}
    # a lenyomat a tartalomé: a 'commit' mező kimarad belőle, hogy azonos tartalom minden commiton azonos lenyomatot adjon
    kanon = json.dumps({k: v for k, v in cs.items() if k != 'commit'}, ensure_ascii=False, sort_keys=True, separators=(',', ':')).encode('utf-8')
    cs['sha256'] = hashlib.sha256(kanon).hexdigest()
    os.makedirs(os.path.dirname(os.path.abspath(a.ki)), exist_ok=True)
    json.dump(cs, open(a.ki, 'w', encoding='utf-8'), ensure_ascii=False, separators=(',', ':'))
    print(a.ki, os.path.getsize(a.ki), 'bájt'); print(json.dumps(cs['osszesites'], ensure_ascii=False)); print('sha256', cs['sha256'])
    import kontroll  # a szakmai kontroll állapota: a csomag nem blokkolódik (admin-próba), de mindig látszik
    k = kontroll.osszegzes()
    if k['lezart'] < k['tetel']:
        print(f"FIGYELEM: szakmai kontroll {k['lezart']}/{k['tetel']} tétel lezárva – a csomag csak admin-próbára jó, élesítésre nem.")


if __name__ == '__main__':
    main()
