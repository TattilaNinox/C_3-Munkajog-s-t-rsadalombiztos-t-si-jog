#!/usr/bin/env python3
"""A tételsor tools/ mappáját összeveti a tools/eszkozok.lock zárral.

    python3 tools/eszkoz_ellenor.py

Kilépési kód: 0, ha nincs eltérés; 1, ha van; 2, ha a zár hiányzik.
Utolsó sor mindig: eszkoz_ellenor: fájl N, eltérés M
"""
import hashlib, json, os, sys

GY = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
TOOLS = os.path.join(GY, 'tools')
ZAR = os.path.join(TOOLS, 'eszkozok.lock')


def sha256(ut):
    h = hashlib.sha256()
    with open(ut, 'rb') as f:
        for darab in iter(lambda: f.read(65536), b''):
            h.update(darab)
    return h.hexdigest()


def lemez_fajlok():
    ki = []
    for gy, mappak, nevek in os.walk(TOOLS):
        mappak[:] = [m for m in mappak if m != '__pycache__']
        for n in nevek:
            if n.endswith('.pyc') or n == '.DS_Store':
                continue
            rel = os.path.relpath(os.path.join(gy, n), TOOLS).replace(os.sep, '/')
            ki.append(rel)
    return ki


def main():
    if not os.path.isfile(ZAR):
        sys.stderr.write('eszkoz_ellenor: hiányzik a tools/eszkozok.lock\n')
        sys.exit(2)
    z = json.load(open(ZAR, encoding='utf-8'))
    fajlok = z.get('fajlok') or {}
    helyi = set(z.get('helyi') or [])
    hibak = []
    lemez = set(lemez_fajlok())
    lemez.discard('eszkozok.lock')
    for rel, vart in sorted(fajlok.items()):
        ut = os.path.join(TOOLS, rel.replace('/', os.sep))
        if not os.path.isfile(ut):
            hibak.append('hiányzik: %s' % rel)
            continue
        if sha256(ut) != vart:
            hibak.append('eltérés: %s' % rel)
        lemez.discard(rel)
    for rel in sorted(lemez):
        if rel in helyi:
            continue
        hibak.append('záron kívül: %s' % rel)
    for h in hibak:
        print(h)
    print('eszkoz_ellenor: fájl %d, eltérés %d' % (len(fajlok), len(hibak)))
    sys.exit(1 if hibak else 0)


if __name__ == '__main__':
    main()
