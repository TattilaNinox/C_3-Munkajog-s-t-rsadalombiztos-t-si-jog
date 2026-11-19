#!/usr/bin/env python3
"""A tétel-alügynök átadó fájljának (NN_seged.json) összefésülése a közös segédfájlokba.   python3 tools/seged_osszefesul.py <NN_seged.json>
kontroll/_kommentar_terkep.json (paragrafusok, reszek, technika), _ijoten_jegyzek.json (kesz_szocikkek cím szerint, nincs_megirva),
_bovites.json (tétel + forrás szerint). Meglévő kulcsot nem ír felül: a §-nál és a résznél a megjegyzést bővíti, a többit kihagyja és kiírja.
"""
import json, os, sys
GY = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
def be(n): return json.load(open(os.path.join(GY, 'kontroll', n), encoding='utf-8'))
def ki(n, d): json.dump(d, open(os.path.join(GY, 'kontroll', n), 'w', encoding='utf-8'), ensure_ascii=False, indent=1); open(os.path.join(GY, 'kontroll', n), 'a').write('\n')
s = json.load(open(sys.argv[1], encoding='utf-8')); sz = {'par': 0, 'resz': 0, 'tech': 0, 'ij': 0, 'nincs': 0, 'bov': 0, 'kihagyva': []}
t = be('_kommentar_terkep.json'); k = s.get('kommentar_terkep', {})
for p, v in k.get('paragrafusok', {}).items():
    if p in t['paragrafusok']:
        r = t['paragrafusok'][p]
        if r != v and v.get('megj') and v['megj'] not in (r.get('megj') or ''):
            r['megj'] = ((r.get('megj') or '') + ' | ' + v['megj']).strip(' |'); sz['kihagyva'].append('§ ' + p + ' (megjegyzés bővítve)')
    else:
        t['paragrafusok'][p] = v; sz['par'] += 1
for n, v in k.get('reszek', {}).items():
    if n in t['reszek']: sz['kihagyva'].append('rész: ' + n)
    else: t['reszek'][n] = v; sz['resz'] += 1
for x in k.get('technika', []):
    if x not in t['technika']: t['technika'].append(x); sz['tech'] += 1
ki('_kommentar_terkep.json', t)
j = be('_ijoten_jegyzek.json'); i = s.get('ijoten', {})
cimek = {x.get('cim') for x in j['kesz_szocikkek']}
for x in i.get('kesz_szocikkek', []):
    if x.get('cim') in cimek:
        r = next(y for y in j['kesz_szocikkek'] if y.get('cim') == x['cim'])
        if x.get('targy') and x['targy'] not in (r.get('targy') or ''): r['targy'] = ((r.get('targy') or '') + '; ' + x['targy']).strip('; ')
    else: j['kesz_szocikkek'].append(x); sz['ij'] += 1
nm = i.get('nincs_megirva', [])
if nm:
    kulcs = 'Dologi jog és egyéb (az alügynökök átadó fájljaiból)'
    if isinstance(j['nincs_megirva'], dict):
        l = j['nincs_megirva'].setdefault(kulcs, [])
    else: l = j['nincs_megirva']
    for x in nm:
        if x not in l: l.append(x); sz['nincs'] += 1
ki('_ijoten_jegyzek.json', j)
b = be('_bovites.json'); van = {(x['tetel'], x['forras']) for x in b}
for x in s.get('bovites', []):
    if (x['tetel'], x['forras']) not in van: b.append(x); sz['bov'] += 1
ki('_bovites.json', b)
print(json.dumps(sz, ensure_ascii=False))
