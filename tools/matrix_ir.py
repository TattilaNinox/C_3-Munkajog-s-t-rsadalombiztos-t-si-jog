#!/usr/bin/env python3
"""A szakvizsga-fogalommátrixok kézi leírása → termekek/fogalommatrix/<id>.json.   python3 tools/matrix_ir.py [tétel …]

Egy mátrix: mx(azonosító, tétel, cím, bevezető, sorcímke, sorok, oszlopok, cellák, összegzés).
 sorok:    [(id, név)]            oszlopok: [(id, kérdés, rövid név)]
 cellák:   soronként egy lista, benne oszloponként (címke, forrásmondat eleje); a forrásmondatot a program
           a tétel mondatai közül a megadott kezdet alapján keresi ki (pontosan egy találat kell), így a
           forrás mindig a tétel teljes, szó szerinti mondata.
A kész fájlokat a tools/matrix_ellenor.py ellenőrzi.
"""
import json, os, sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import kozos
import vazlat_gyart as v

KI = os.path.join(kozos.GYOKER, 'termekek', 'fogalommatrix')
_M = {}
HIBA = []
# Tételszűrő (központi chat, 2026-11-17): `python3 tools/matrix_ir.py 39 40` csak a megadott tételek mátrixát írja újra.
# Szűrő nélkül minden tétel mátrixa újraíródik, KIVÉVE a gyártásra váró tételekét (termekek/_gyartasra_var.json):
# azok elavult forrásmondata miatt a program korábban üres forrással írta felül a fájlt.
SZURO = {int(a) for a in sys.argv[1:] if a.isdigit()} if os.path.basename(sys.argv[0]) == 'matrix_ir.py' else set()
_vf = os.path.join(kozos.GYOKER, 'termekek', '_gyartasra_var.json')
VAR = set(int(x) for x in json.load(open(_vf, encoding='utf-8')).get('tetelek', [])) if os.path.exists(_vf) else set()


def irando(n):
    return (n in SZURO) if SZURO else (n not in VAR)


def mondat(n, eleje):
    if n not in _M:
        _M[n] = [e[2] for e in v.szerkezet(n) if e[0] == 'M']
    t = sorted({m for m in _M[n] if m.startswith(eleje)})
    if len(t) != 1:
        HIBA.append(f'{n}. tétel: {len(t)} mondat kezdődik így: {eleje}' + ''.join('\n      ' + x[:150] for x in t))
        return ''
    return t[0]


def mx(az, n, cim, bev, sorcimke, sorok, oszlopok, cellak, ossz=None):
    if not irando(n):
        return
    d = {'id': f"{kozos.beallitas()['azon']}_{n:02d}_{az}", 'targy': kozos.beallitas()['targyKod'], 'tetelek': [n], 'title': cim, 'bevezeto': bev, 'sorCimke': sorcimke,
         'sorok': [{'id': i, 'nev': nev} for i, nev in sorok],
         'oszlopok': [{'id': i, 'kerdes': k, 'rovid': r} for i, k, r in oszlopok], 'cellak': []}
    assert len(cellak) == len(sorok), az
    for (si, _), sor in zip(sorok, cellak):
        assert len(sor) == len(oszlopok), (az, si)
        for (oi, _, _), (cimke, eleje) in zip(oszlopok, sor):
            d['cellak'].append({'sor': si, 'oszlop': oi, 'cimke': cimke,
                                'forrasok': [{'tetel': n, 'szoveg': mondat(n, eleje), 'tipus': 'mondat'}], 'feloldas': None})
    d['osszegzes'] = mondat(n, ossz) if ossz else ''
    d['audit'] = {'megjegyzes': None, 'mikor': None}
    json.dump(d, open(os.path.join(KI, d['id'] + '.json'), 'w', encoding='utf-8'), ensure_ascii=False, indent=1)


def main():
    import re
    os.makedirs(KI, exist_ok=True)   # új tételsor: üres mappa
    for f in os.listdir(KI):
        m = re.match(re.escape(kozos.beallitas()['azon']) + r'_(\d+)_', f)
        if f.endswith('.json') and m and irando(int(m.group(1))):
            os.remove(os.path.join(KI, f))
    import matrix_adat  # noqa: F401  (a mátrixok leírása)
    import matrix_ir
    if matrix_ir.HIBA:
        raise SystemExit('\n'.join(matrix_ir.HIBA))
    print('kiírva:', len([f for f in os.listdir(KI) if f.endswith('.json')]))


if __name__ == '__main__':
    main()
