#!/usr/bin/env python3
"""A hangos vázlat hangszövege főpontonként.

    python3 tools/vazlat_hang.py            # mind a 85 tétel
    python3 tools/vazlat_hang.py 23         # egy tétel

Bemenet: termekek/hangos_vazlat/NN.json (a tools/vazlat_gyart.py kimenete).
Kimenet:
  termekek/hangos_vazlat/hang/NN/fKK_D.txt   – a KK. főpont D. hangdarabja (legfeljebb 4600 karakter, [serious] címkével)
  termekek/hangos_vazlat/hang/NN/_meta.json  – főpontonként a darabok, és mondatonként az, hogy melyik darab hányadik sora

A hangszöveg a tools/hangszoveg.py szabályai szerint készül (számok, §-hivatkozások, rövidítések betűvel),
ugyanúgy, mint a tételek hangszövege. Egy sor = egy cím vagy egy kulcsmondat; a darabhatár mindig sorhatár.
A program a végén ellenőrzi, hogy minden kulcsmondatnak van sora, és hogy a hangszövegben nem maradt számjegy vagy §.
"""
import json, os, shutil, sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import hangszoveg as h
import vazlat_gyart as v

HANG = os.path.join(v.KI, 'hang')
MAX = 4580


_KIEJTES = None


def kiejtes(n):
    """A felolvasószöveg kiejtési táblája (tts/_ujra_terv.json közös pótlásai) – a címsorokra is."""
    global _KIEJTES
    if _KIEJTES is None:
        ut = os.path.join(h.GYOKER, 'tts', '_ujra_terv.json')
        _KIEJTES = json.load(open(ut, encoding='utf-8')) if os.path.exists(ut) else {}
    return list(_KIEJTES.get('kiejtes') or [])


def cimsor(s, n=None):
    x = h.blokk_hang(s)
    for a, c in (kiejtes(n) if n is not None else []):
        if a in x:
            x = x.replace(a, c)
    return x


def mondat(s):
    x = h.hangra(s)
    for a, c in kiejtes(None):          # a kiejtési tábla a mondatokra is (központi chat, 2026-11-17)
        if a in x:
            x = x.replace(a, c)
    hi = h.hianyos(x)
    if hi:
        raise SystemExit(f'Számjegy vagy § maradt a hangszövegben: {hi[:5]} | {s[:80]}')
    return x


def tetel(n):
    d = json.load(open(os.path.join(v.KI, f'{n:02d}.json'), encoding='utf-8'))
    ki = os.path.join(HANG, f'{n:02d}')
    if os.path.isdir(ki):
        shutil.rmtree(ki)
    os.makedirs(ki)
    meta = {'sema': 1, 'termek': 'hangos_vazlat_hang', 'tetel': n, 'cim': d['cim'], 'fopontok': []}
    ossz = 0; mondatok = 0
    for k, f in enumerate(d['fopontok'], 1):
        sorok = []          # (típus, sorszám vagy None, hangszöveg)
        if f['cim']:
            sorok.append(('focim', None, cimsor(f['cim'], n)))
        for a in f['alpontok']:
            if not a['mondatok']:
                continue
            if a['cim']:
                sorok.append(('alcim', None, cimsor(a['cim'], n)))
            for m in a['mondatok']:
                sorok.append(('mondat', m['sorszam'], mondat(m['szoveg'])))
        if not any(t == 'mondat' for t, _, _ in sorok):
            continue
        # hangulatcímkék (2026-11-18): a kulcsmondat alaphangja [serious], a darab címkéje is az
        cimkezett = h.hangulat([x[2] for x in sorok], alap='serious', kezdo='serious',
                               tipusok=[{'focim': 'cim', 'alcim': 'alcim'}.get(x[0]) for x in sorok])
        sorok = [(a, b, c) for (a, b, _), c in zip(sorok, cimkezett)]
        # darabolás sorhatáron
        darabok = [[]]; hossz = 0
        for s in sorok:
            if darabok[-1] and hossz + len(s[2]) + 2 > MAX:
                darabok.append([]); hossz = 0
            darabok[-1].append(s); hossz += len(s[2]) + 2
        fm = {'fopont': k, 'cim': f['cim'], 'darabok': [], 'mondatok': []}
        for di, dar in enumerate(darabok, 1):
            fajl = f'f{k:02d}_{di}.txt'
            szoveg = '[serious]\n\n' + '\n\n'.join(s[2] for s in dar) + '\n'
            open(os.path.join(ki, fajl), 'w', encoding='utf-8').write(szoveg)
            fm['darabok'].append({'fajl': fajl, 'karakter': len(szoveg), 'sorok': len(dar)})
            ossz += len(szoveg)
            for si, (t, sorsz, _) in enumerate(dar, 1):
                if t == 'mondat':
                    fm['mondatok'].append({'sorszam': sorsz, 'darab': di, 'sor': si}); mondatok += 1
        meta['fopontok'].append(fm)
    meta['karakter'] = ossz; meta['mondatokSzama'] = mondatok
    assert mondatok == d['mondatokSzama'], (n, mondatok, d['mondatokSzama'])
    json.dump(meta, open(os.path.join(ki, '_meta.json'), 'w', encoding='utf-8'), ensure_ascii=False, indent=1)
    return ossz, mondatok, sum(len(x['darabok']) for x in meta['fopontok'])


def main():
    import kozos
    args = [a for a in sys.argv[1:] if not a.startswith('--')]
    T = [t['sorszam'] for t in kozos.tetelsor()['tetelek']]
    o = m = db = 0
    for n in ([int(args[0])] if args else T):
        a, b, c = tetel(n); o += a; m += b; db += c
    print(f'hangszöveg: {db} darab, {m} kulcsmondat, {o} karakter')


if __name__ == '__main__':
    main()
