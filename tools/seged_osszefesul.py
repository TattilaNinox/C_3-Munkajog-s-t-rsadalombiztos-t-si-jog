#!/usr/bin/env python3
"""A tétel-alügynök átadó fájljának (NN_seged.json) összefésülése a közös segédfájlokba.   python3 tools/seged_osszefesul.py <NN_seged.json>
kontroll/_kommentar_terkep.json (paragrafusok, reszek, technika), _ijoten_jegyzek.json (kesz_szocikkek cím szerint, nincs_megirva),
_bovites.json (tétel + forrás szerint). Meglévő kulcsot nem ír felül: a §-nál és a résznél a megjegyzést bővíti, a többit kihagyja és kiírja.
KE-3/7: a hiányzó _bovites.json üres listával jön létre; a kommentar_terkep „kotet” kulcsa is összefésülődik (a meglévő,
nem üres mező nem íródik felül); az IJOTEN-jegyzék „nincs_megirva” csoportjának kulcsa a tételsor beállításából jön
(tetelsor/beallitas.json: cim), de ha a régi (A/1-es) kulcs már szerepel a fájlban, azt használja tovább.
"""
import json, os, sys
GY = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
RÉGI_KULCS = 'Dologi jog és egyéb (az alügynökök átadó fájljaiból)'      # A/1 (visszafelé kompatibilitás)
def be(n, alap=None):
    ut = os.path.join(GY, 'kontroll', n)
    if alap is not None and not os.path.exists(ut):
        return alap
    return json.load(open(ut, encoding='utf-8'))
def tetelsor_kulcs():
    """A „nincs_megirva” csoport kulcsa: a régi (A/1) kulcs, ha a jegyzékben már szerepel; különben a tételsor címe a
    beállításból („A/2 – Polgári eljárásjog (az alügynökök átadó fájljaiból)”)."""
    try:
        b = json.load(open(os.path.join(GY, 'tetelsor', 'beallitas.json'), encoding='utf-8'))
        nev = b.get('cim') or b.get('azon')
    except (OSError, ValueError):
        nev = None
    return '%s (az alügynökök átadó fájljaiból)' % nev if nev else RÉGI_KULCS
def ki(n, d): json.dump(d, open(os.path.join(GY, 'kontroll', n), 'w', encoding='utf-8'), ensure_ascii=False, indent=1); open(os.path.join(GY, 'kontroll', n), 'a').write('\n')
s = json.load(open(sys.argv[1], encoding='utf-8')); sz = {'par': 0, 'resz': 0, 'tech': 0, 'kotet': 0, 'ij': 0, 'nincs': 0, 'bov': 0, 'kihagyva': []}
t = be('_kommentar_terkep.json'); k = s.get('kommentar_terkep', {})
for x in ('paragrafusok', 'reszek'): t.setdefault(x, {})
t.setdefault('technika', [])
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
kv = k.get('kotet')
if isinstance(kv, dict):
    if not isinstance(t.get('kotet'), dict):
        if t.get('kotet'): sz['kihagyva'].append('kötet (a meglévő nem objektum)')
        else: t['kotet'] = {}
    if isinstance(t.get('kotet'), dict):
        for n, v in kv.items():
            if v in (None, '', [], {}): continue
            if t['kotet'].get(n) in (None, '', [], {}): t['kotet'][n] = v; sz['kotet'] += 1
            elif t['kotet'][n] != v: sz['kihagyva'].append('kötet: ' + n)
elif isinstance(kv, list):
    if not isinstance(t.get('kotet'), list): t['kotet'] = ([t['kotet']] if t.get('kotet') else [])
    for v in kv:
        if v not in t['kotet']: t['kotet'].append(v); sz['kotet'] += 1
ki('_kommentar_terkep.json', t)
j = be('_ijoten_jegyzek.json', {'kesz_szocikkek': [], 'nincs_megirva': {}}); i = s.get('ijoten', {})
j.setdefault('kesz_szocikkek', []); j.setdefault('nincs_megirva', {})
cimek = {x.get('cim') for x in j['kesz_szocikkek']}
for x in i.get('kesz_szocikkek', []):
    if x.get('cim') in cimek:
        r = next(y for y in j['kesz_szocikkek'] if y.get('cim') == x['cim'])
        if x.get('targy') and x['targy'] not in (r.get('targy') or ''): r['targy'] = ((r.get('targy') or '') + '; ' + x['targy']).strip('; ')
    else: j['kesz_szocikkek'].append(x); sz['ij'] += 1
nm = i.get('nincs_megirva', [])
if nm:
    kulcs = RÉGI_KULCS if isinstance(j['nincs_megirva'], dict) and RÉGI_KULCS in j['nincs_megirva'] else tetelsor_kulcs()
    if isinstance(j['nincs_megirva'], dict):
        l = j['nincs_megirva'].setdefault(kulcs, [])
    else: l = j['nincs_megirva']
    for x in nm:
        if x not in l: l.append(x); sz['nincs'] += 1
ki('_ijoten_jegyzek.json', j)
b = be('_bovites.json', []); van = {(x['tetel'], x['forras']) for x in b}
for x in s.get('bovites', []):
    if (x['tetel'], x['forras']) not in van: b.append(x); sz['bov'] += 1
ki('_bovites.json', b)
print(json.dumps(sz, ensure_ascii=False))
