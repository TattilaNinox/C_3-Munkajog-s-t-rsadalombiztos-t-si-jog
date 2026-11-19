#!/usr/bin/env python3
"""Az API-körök összesítője tételenként: első olvasás → ellenőrző olvasás, alkalmazott és elvetett műveletek, költség.

    python3 tools/s5/osszesito.py

Bemenet (a tároló jelentesek/ mappájából, ami megvan):
- jelentesek/api/elso_olvasas/elso-NN.json   – az első olvasás leletei (allitasok[].tipus, lefedettseg[].allapot)
- jelentesek/api/ellenorzo/ell-NN.json        – az ellenőrző olvasás leletei (a legutóbbi kör; a korábbiak: ellenorzo_kN/)
- jelentesek/api/atiras_alkalmazas.json      – az alkalmaz.py kimenete (alkalmazva, elvetve)
- jelentesek/api/api_koltseg.csv vagy jelentesek/api_koltseg.csv – a kötegek költsége (feladat, usd)
Kimenet: jelentesek/api/osszesito.md. Csak olvas (a kimeneti fájlt írja). Utolsó sor:
osszesito: tétel N, ELLENTMOND a→b, ELAVULT_GYANU a→b, PONTATLAN a→b, költség X.XX USD
(ha az egyik kör nem futott, annak oldalán „–” áll)
"""
import csv, glob, json, os, re, sys


def _gyoker():
    """A tételsor-tároló gyökere: az első szülőmappa, amelyben van tetelsor/beallitas.json."""
    d = os.path.dirname(os.path.abspath(__file__))
    while d != os.path.dirname(d):
        if os.path.isfile(os.path.join(d, 'tetelsor', 'beallitas.json')):
            return d
        d = os.path.dirname(d)
    raise SystemExit('nem találom a tételsor-tároló gyökerét (tetelsor/beallitas.json)')


GY = _gyoker()
API = os.path.join(GY, 'jelentesek', 'api')
TIPUSOK = ('ELLENTMOND', 'ELAVULT_GYANU', 'PONTATLAN', 'NEM_IGAZOLHATO', 'KIIRASON_KIVUL')


def olvasas(mappa, elotag):
    """{tétel: {'tipus': {TÍPUS: db}, 'hianyzik': db, 'reszben': db}} a mappa NN.json fájljaiból."""
    ki = {}
    for p in sorted(glob.glob(os.path.join(API, mappa, elotag + '-*.json'))):
        m = re.search(r'-(\d+)\.json$', p)
        if not m:
            continue
        try:
            d = json.load(open(p, encoding='utf-8'))
        except (OSError, ValueError):
            continue
        n = int(d.get('tetel') or m.group(1))
        tip = {t: 0 for t in TIPUSOK}
        for a in d.get('allitasok') or []:
            t = (a.get('tipus') or '').strip().upper()
            if t in tip:
                tip[t] += 1
        lef = [(x.get('allapot') or '').strip().lower() for x in d.get('lefedettseg') or []]
        ki[n] = {'tipus': tip, 'hianyzik': lef.count('hianyzik'), 'reszben': lef.count('reszben')}
    return ki


def alkalmazas():
    p = os.path.join(API, 'atiras_alkalmazas.json')
    if not os.path.exists(p):
        return {}
    try:
        return {j['tetel']: j for j in json.load(open(p, encoding='utf-8'))}
    except (OSError, ValueError, KeyError, TypeError):
        return {}


def koltseg():
    """{feladat: usd} a költségnaplóból (az első meglévő helyen)."""
    for p in (os.path.join(API, 'api_koltseg.csv'), os.path.join(GY, 'jelentesek', 'api_koltseg.csv')):
        if os.path.exists(p):
            ki = {}
            for r in csv.DictReader(open(p, encoding='utf-8')):
                try:
                    ki[r.get('feladat') or '?'] = ki.get(r.get('feladat') or '?', 0.0) + float(r.get('usd') or 0)
                except ValueError:
                    continue
            return ki, os.path.relpath(p, GY)
    return {}, None


def nyil(a, b):
    if a is None and b is None:
        return '–'
    return '%s→%s' % ('–' if a is None else a, '–' if b is None else b)


def main():
    E = olvasas('elso_olvasas', 'elso')
    V = olvasas('ellenorzo', 'ell')
    A = alkalmazas()
    K, kforras = koltseg()
    tetelek = sorted(set(E) | set(V) | set(A))
    L = ['# API-körök összesítője', '',
         'Gépi kimenet: `python3 tools/s5/osszesito.py`. A nyíl bal oldala az első olvasás (`jelentesek/api/elso_olvasas/`), '
         'jobb oldala az ellenőrző olvasás (`jelentesek/api/ellenorzo/`); „–”: nincs adat. Az alkalmazott és az elvetett '
         'műveletek az `atiras_alkalmazas.json` szerint.', '',
         '| Tétel | ' + ' | '.join(TIPUSOK) + ' | Lefedettség: hiányzik / részben | Alkalmazva | Elvetve |',
         '|---|' + '---|' * (len(TIPUSOK) + 3)]
    ossz = {t: [0, 0] for t in TIPUSOK}
    for n in tetelek:
        e, v, a = E.get(n), V.get(n), A.get(n)
        cellak = []
        for t in TIPUSOK:
            x = e['tipus'][t] if e else None
            y = v['tipus'][t] if v else None
            ossz[t][0] += x or 0; ossz[t][1] += y or 0
            cellak.append(nyil(x, y))
        lef = '%s / %s' % (nyil(e and e['hianyzik'], v and v['hianyzik']), nyil(e and e['reszben'], v and v['reszben'])) if (e or v) else '–'
        alk = str(a['alkalmazva']) if a else '–'
        elv = str(len(a.get('elvetve') or [])) if a else '–'
        L.append('| %d | %s | %s | %s | %s |' % (n, ' | '.join(cellak), lef, alk, elv))
    def ossz_nyil(t):     # ha egyik oldalon sincs adat, „–” (nem 0)
        return nyil(ossz[t][0] if E else None, ossz[t][1] if V else None)
    L.append('| **össz.** | %s | | %s | %s |' % (' | '.join(ossz_nyil(t) for t in TIPUSOK),
                                                  sum(a['alkalmazva'] for a in A.values()), sum(len(a.get('elvetve') or []) for a in A.values())))
    L += ['', '## Költség (%s)' % ('`%s`' % kforras if kforras else 'nincs költségnapló'), '', '| Feladat | USD |', '|---|---|']
    for f, usd in K.items():
        L.append('| %s | %.2f |' % (f, usd))
    osszes = sum(K.values())
    L.append('| **összesen** | **%.2f** |' % osszes)
    utolso = 'osszesito: tétel %d, ELLENTMOND %s, ELAVULT_GYANU %s, PONTATLAN %s, költség %.2f USD' % (
        len(tetelek), ossz_nyil('ELLENTMOND'), ossz_nyil('ELAVULT_GYANU'), ossz_nyil('PONTATLAN'), osszes)
    L += ['', utolso]
    os.makedirs(API, exist_ok=True)
    open(os.path.join(API, 'osszesito.md'), 'w', encoding='utf-8').write('\n'.join(L) + '\n')
    print(utolso)


if __name__ == '__main__':
    main()
