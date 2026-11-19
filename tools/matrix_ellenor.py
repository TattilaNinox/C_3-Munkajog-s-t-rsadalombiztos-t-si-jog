#!/usr/bin/env python3
"""A szakvizsga-fogalommátrixok gépi kapuja:  python3 tools/matrix_ellenor.py

Forrás: termekek/fogalommatrix/*.json (az index.json kivételével), az admin fogalommátrix-formátumában
(sorok, oszlopok, cellak[{sor, oszlop, cimke, forrasok[{tetel, szoveg, tipus}], feloldas}]). Minden mátrixra:
 1. teljesség: minden (sor, oszlop) párhoz pontosan egy cella tartozik, nem üres címkével és legalább egy forrással;
 2. forrás: minden forrás a megjelölt tétel egy teljes mondata, szó szerint (mondathatártól mondathatárig);
 3. szóhasználat: a címke minden legalább hat betűs szavának első öt betűje valamelyik forrásszó elején áll; ha nem,
    a cellának `feloldas` mezőben indokolt feloldás kell (ezt Attila adja meg);
 4. tiltott szavak: a felhasználónak szóló szövegekben nem szerepel a „tananyag” karaktersor (a „jegyzet” szó tilalmát Attila 2026-11-15-én feloldotta);
 5. az összegzés – ha van – a tétel egy vagy több teljes mondata, szó szerint.
"""
import glob, json, os, re, sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import kozos
import vazlat_gyart as v

KI = os.path.join(kozos.GYOKER, 'termekek', 'fogalommatrix')
SZO = re.compile(r'[^\W\d_]+', re.UNICODE)
_M = {}


def mondatok(n):
    if n not in _M:
        _M[n] = {e[2] for e in v.szerkezet(n) if e[0] == 'M'}
    return _M[n]


def ellenoriz(d):
    h = []
    sorok = [s['id'] for s in d['sorok']]; oszl = [o['id'] for o in d['oszlopok']]
    C = {}
    for c in d['cellak']:
        C.setdefault((c['sor'], c['oszlop']), []).append(c)
    for s in sorok:
        for o in oszl:
            cs = C.get((s, o), [])
            if len(cs) != 1:
                h.append(f'({s}, {o}): {len(cs)} cella'); continue
            c = cs[0]
            if not c.get('cimke', '').strip():
                h.append(f'({s}, {o}): üres címke')
            if not c.get('forrasok'):
                h.append(f'({s}, {o}): nincs forrás'); continue
            fszavak = []
            for f in c['forrasok']:
                if f['szoveg'] not in mondatok(f['tetel']):
                    h.append(f'({s}, {o}): a forrás nem a {f["tetel"]}. tétel teljes mondata: {f["szoveg"][:60]}')
                fszavak += [x.lower() for x in SZO.findall(f['szoveg'])]
            if not c.get('feloldas'):
                for x in SZO.findall(c.get('cimke', '')):
                    if len(x) >= 6 and not any(y.startswith(x.lower()[:5]) for y in fszavak):
                        h.append(f'({s}, {o}): szóhasználati eltérés, feloldás kell: {x}')
    for k in C:
        if k[0] not in sorok or k[1] not in oszl:
            h.append(f'{k}: nem létező sorra vagy oszlopra hivatkozó cella')
    latszo = [d.get('title', ''), d.get('bevezeto', ''), d.get('sorCimke', ''), d.get('osszegzes', '')] + [s['nev'] for s in d['sorok']] + \
             [o['kerdes'] + ' ' + o['rovid'] for o in d['oszlopok']] + [c.get('cimke', '') for c in d['cellak']]
    for t in latszo:
        for tilos in ('tananyag',):
            if tilos in t.lower():
                h.append(f'tiltott szó ({tilos}): {t[:50]}')
    if d.get('osszegzes'):
        for m in v.mondatok(d['osszegzes']):
            if not any(m in mondatok(n) for n in d['tetelek']):
                h.append(f'az összegzés nem a tétel teljes mondata: {m[:60]}')
    return h


def gyartasra_var():
    """A KP-2-ben lezárt, de a TG-1-ben még nem gyártott tételek (termekek/_gyartasra_var.json). Az ilyen tételhez
    tartozó mátrix elavult forrásmondata nem hiba, hanem figyelmeztetés (Attila döntése, 2026-11-16, 15:30 és 19:12);
    a --szigoru kapcsoló a listát figyelmen kívül hagyja (élesítés előtt a listának üresnek kell lennie)."""
    if '--szigoru' in sys.argv:
        return set()
    f = os.path.join(os.path.dirname(KI), '_gyartasra_var.json')
    if not os.path.exists(f):
        return set()
    return set(int(x) for x in json.load(open(f, encoding='utf-8')).get('tetelek', []))


def main():
    index = []; hibas = 0; cella = 0; var = gyartasra_var(); varo = 0
    for f in sorted(glob.glob(os.path.join(KI, '*.json'))):
        if os.path.basename(f) == 'index.json':
            continue
        d = json.load(open(f, encoding='utf-8')); h = ellenoriz(d)
        if d['id'] != os.path.basename(f)[:-5]:
            h.append('az id nem egyezik a fájlnévvel')
        if h and any(int(n) in var for n in d['tetelek']) and d['id'] == os.path.basename(f)[:-5]:
            varo += 1; print('GYÁRTÁSRA VÁR (elavult, nem hiba)', os.path.basename(f))
        elif h:
            hibas += 1; print('HIBA', os.path.basename(f)); [print('   ', x) for x in h]
        cella += len(d['cellak'])
        index.append({'id': d['id'], 'title': d['title'], 'tetelek': d['tetelek'], 'sor': len(d['sorok']), 'oszlop': len(d['oszlopok'])})
    json.dump({'sema': 1, 'termek': 'fogalommatrix', 'matrixok': index}, open(os.path.join(KI, 'index.json'), 'w', encoding='utf-8'), ensure_ascii=False, indent=1)
    print(f'fogalommátrixok: {len(index)}, cella: {cella}, hibás: {hibas}; gyártásra vár (elavult): {varo}')
    sys.exit(1 if hibas else 0)


if __name__ == '__main__':
    main()
