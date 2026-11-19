#!/usr/bin/env python3
"""A hangos vázlat kézi kijelölésének rögzítése mondatsorszámokból.

    python3 tools/vazlat_kezi.py 23 be=9,25,47 ki=1,8,11-13

A sorszám a `vazlat_gyart.py 23 --lista` kiírása szerinti. A tétel korábbi kézi kijelölését felülírja,
és a tételt véglegesítettnek jelöli. A kezi.json a mondatok elejét tárolja (a legrövidebb egyértelmű kezdetet).
"""
import json, os, sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import vazlat_gyart as v


def szamok(s):
    out = []
    for r in s.split(','):
        if not r:
            continue
        if '-' in r:
            a, b = r.split('-'); out += list(range(int(a), int(b) + 1))
        else:
            out.append(int(r))
    return out


def main():
    n = int(sys.argv[1]); be = ki = []
    for a in sys.argv[2:]:
        if a.startswith('be='): be = szamok(a[3:])
        if a.startswith('ki='): ki = szamok(a[3:])
    M = {e[1]: e[2] for e in v.szerkezet(n) if e[0] == 'M'}

    def kezdet(i):
        s = M[i]
        for h in list(range(40, len(s), 20)) + [len(s)]:  # a 40 karakternél rövidebb mondat a teljes szövegével azonosítható (2026-11-15)
            if sum(1 for x in M.values() if x.startswith(s[:h])) == 1:
                return s[:h]
        print(f'  ({i}. mondat többször szerepel azonos szöveggel: az előjelölés marad)')
        return None
    kp = os.path.join(v.KI, 'kezi.json')
    K = json.load(open(kp, encoding='utf-8')) if os.path.exists(kp) else {}
    ujbe = [k for k in map(kezdet, be) if k]; ujki = [k for k in map(kezdet, ki) if k]
    if '--hozza' in sys.argv and str(n) in K:
        # a korábbi kézi kijelölés megmarad; az új döntés felülírja az ugyanarra a mondatra vonatkozó régit
        regi = K[str(n)]
        egyezik = lambda a, b: a.startswith(b) or b.startswith(a)
        ujbe = [k for k in regi.get('be', []) if not any(egyezik(k, x) for x in ujki + ujbe)] + ujbe
        ujki = [k for k in regi.get('ki', []) if not any(egyezik(k, x) for x in ujbe + ujki)] + ujki
    K[str(n)] = {'kesz': True, 'be': ujbe, 'ki': ujki}
    json.dump(dict(sorted(K.items(), key=lambda x: int(x[0]))), open(kp, 'w', encoding='utf-8'), ensure_ascii=False, indent=1)
    fop, jel, ossz = v.vazlat(n, K[str(n)])
    kul = [j for j in jel if j[1]]
    print(f'{n}. tétel véglegesítve: {len(kul)} kulcsmondat a {ossz}-ből ({100*len(kul)//ossz}%), {sum(len(j[3]) for j in kul)} karakter a {sum(len(j[3]) for j in jel)}-ből')


if __name__ == '__main__':
    main()
