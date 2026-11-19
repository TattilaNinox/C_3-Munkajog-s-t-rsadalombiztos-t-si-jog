#!/usr/bin/env python3
"""A tétel teljes szövege blokkokra bontva, a megjelenítő „Teljes tétel” paneljéhez.   python3 tools/tetel_blokk.py [sorszám]

Blokkok, sorrendben (a besorolás ugyanaz, mint a hangos vázlat szerkezeténél: vazlat_gyart.szerkezet):
  ["f", főcím] · ["a", alcím] · ["d", i] (a tétel i-edik §-doboza a paragrafus_jegyzek sorrendjében; a szöveg ott van,
  nem ismételjük) · ["p", bekezdés] (egy bekezdés szó szerint, a sor elején álló felsorolásjel nélkül).
A tétel címe (az első sor) nem blokk: a csomag `tetelek[].cim` mezője adja.

Ellenőrzés (a modul maga végzi, hibánál kivétel): a bekezdések, főcímek, alcímek és a dobozok együtt a tétel minden
nem üres sorát lefedik, a dobozok száma és sorrendje egyezik a §-jegyzékkel.
"""
import json, os, re, sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import kozos
import vazlat_gyart as v


def blokkok(n, kihagyott=None):
    return blokkok_sorral(n, kihagyott)[0]


def blokkok_sorral(n, kihagyott=None):
    """(blokkok, sorindexek): a blokkok mellett mindegyik kezdősorának indexe a tétel szövegének soraiban
    (a jegyzet-HTML a blokkokat ezen át rendeli a hangdokumentumok darabjaihoz: tools/jegyzet_html.py).
    kihagyott (KE-3/6): ha a hívó listát ad át, a még le nem gyártott termék (termekek/paragrafus_jegyzek/NN.json,
    termekek/hangos_vazlat/NN.json) elleni ellenőrzés kimarad, és a hiányzó fájl útja a listába kerül; lista nélkül
    (alapérték) a hiányzó termék hiba, mint eddig."""
    txt = kozos.tetel_szoveg(n); L = [l.strip() for l in txt.split('\n')]
    doboz = set(); fej = {}
    H = [i for i, l in enumerate(L) if kozos.doboz_fej(l)]
    for (kod, par, f, sorok), h in zip(kozos.dobozok(txt), H):
        doboz.add(h); fej[h] = f; x = h + 1; k = 0
        while x < len(L) and k < len(sorok):
            if L[x]:
                doboz.add(x); k += 1
            x += 1
        while x < len(L) and not L[x]:
            x += 1
        if x < len(L) and sorok and re.match(r'^[a-z]{1,2}\) ', sorok[-1]) and L[x] and L[x][0].islower() and not re.match(r'^[a-z]{1,2}\) ', L[x]):
            doboz.add(x)
    NAGY = v.NAGY
    out = []; ix = []; elso = True; di = 0; fedett = 0
    for x, l in enumerate(L):
        if not l:
            continue
        if elso:
            elso = False; fedett += 1; continue
        if x in fej:
            out.append(['d', di]); ix.append(x); di += 1; fedett += 1; continue
        if x in doboz:
            fedett += 1; continue
        fedett += 1; ix.append(x)
        if re.match(r'^[IVX]+\. [' + NAGY + ']', l) and l.upper() == l or l in ('ÖSSZEFOGLALÁS', 'ÖSSZEGZÉS', 'ELHATÁROLÁSOK'):
            out.append(['f', l]); continue
        if l.upper() == l and re.search('[' + NAGY + ']{4}', l):
            out.append(['a', l]); continue
        if re.match(r'^[a-z]\) [' + NAGY + ']', l) and not re.search(r'[.;,:]$', l) and len(l) < 120:
            out.append(['a', l]); continue
        out.append(['p', re.sub(r'^[-–•]\s+', '', l)])
    pj_ut = os.path.join(kozos.GYOKER, 'termekek', 'paragrafus_jegyzek', f'{n:02d}.json')
    if kihagyott is not None and not os.path.isfile(pj_ut):
        kihagyott.append(os.path.relpath(pj_ut, kozos.GYOKER))
    else:
        pj = json.load(open(pj_ut, encoding='utf-8'))['elemek']
        if di != len(pj):
            raise SystemExit(f'{n}. tétel: a dobozok száma ({di}) eltér a §-jegyzéktől ({len(pj)})')
    if fedett != sum(1 for l in L if l):
        raise SystemExit(f'{n}. tétel: a blokkok nem fedik le a teljes szöveget')
    # a főcímek egyeznek a hangos vázlat főpontjainak címével
    fc = [b[1] for b in out if b[0] == 'f']
    hv_ut = os.path.join(kozos.GYOKER, 'termekek', 'hangos_vazlat', f'{n:02d}.json')
    if kihagyott is not None and not os.path.isfile(hv_ut):
        kihagyott.append(os.path.relpath(hv_ut, kozos.GYOKER))
        return out, ix
    vf = [f['cim'] for f in json.load(open(hv_ut, encoding='utf-8'))['fopontok'] if f.get('cim')]
    if any(c not in fc for c in vf):
        raise SystemExit(f'{n}. tétel: a vázlat főpontcíme nincs a tétel főcímei között')
    return out, ix


if __name__ == '__main__':
    ns = [int(sys.argv[1])] if len(sys.argv) > 1 else [t['sorszam'] for t in kozos.tetelsor()['tetelek']]
    db = 0
    for n in ns:
        b = blokkok(n); db += len(b)
    print(f'tételek: {len(ns)}, blokkok: {db}')
