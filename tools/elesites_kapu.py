#!/usr/bin/env python3
"""Élesítés előtti kapu: az elhalasztott teendők listája (termekek/_elesites_elott.json) és a gyártásra váró
tételek listája (termekek/_gyartasra_var.json).   python3 tools/elesites_kapu.py
0-val csak akkor lép ki, ha minden teendő kész, a gyártásra váró lista üres, és a mátrixellenőr szigorú módban is hibátlan.
A tools/kapuk.sh NEM futtatja (a kötegek közben a lista szándékosan nyitott); az élesítés előtt külön, kötelezően futtatandó."""
import json, os, subprocess, sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import kozos

T = os.path.join(kozos.GYOKER, 'termekek')
d = json.load(open(os.path.join(T, '_elesites_elott.json'), encoding='utf-8'))
nyitott = [t for t in d['teendok'] if not t.get('kesz')]
vf = os.path.join(T, '_gyartasra_var.json')
var = json.load(open(vf, encoding='utf-8')).get('tetelek', []) if os.path.exists(vf) else []
for t in nyitott:
    print(f"NYITOTT {t['id']}: {t['mi']}")
if var:
    print('GYÁRTÁSRA VÁR:', ', '.join(str(x) for x in var))
r = subprocess.run([sys.executable, os.path.join(os.path.dirname(os.path.abspath(__file__)), 'matrix_ellenor.py'), '--szigoru'], capture_output=True, text=True)
utolso = (r.stdout.strip().splitlines() or [''])[-1]
subprocess.run(['git', 'checkout', '--', 'termekek/fogalommatrix/index.json'], cwd=kozos.GYOKER, capture_output=True)
print('mátrixellenőr (szigorú):', utolso)
print(f'élesítés előtti teendők: {len(d["teendok"])}, nyitott: {len(nyitott)}; gyártásra váró tétel: {len(var)}')
sys.exit(1 if (nyitott or var or r.returncode) else 0)
