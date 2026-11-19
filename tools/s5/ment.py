#!/usr/bin/env python3
"""A csonka (max_tokens miatt félbeszakadt) átíró válaszból a teljes műveletek kimentése.

    python3 tools/s5/ment.py

A jelentesek/api/atiras/atir-NN.nyers.txt fájlokból atir-NN.json készül ("csonka": true jelöléssel): a „muveletek” tömb
utolsó, félbemaradt eleme kimarad, a „nyitott” lista hiányzik. A csonka tételt az átíró köteg újra megkapja (a már javított szövegre).
Utolsó sor: ment: csonka N, kimentett művelet M
"""
import glob, json, os, re
def _gyoker():
    """A tételsor-tároló gyökere: az első szülőmappa, amelyben van tetelsor/beallitas.json."""
    d = os.path.dirname(os.path.abspath(__file__))
    while d != os.path.dirname(d):
        if os.path.isfile(os.path.join(d, 'tetelsor', 'beallitas.json')):
            return d
        d = os.path.dirname(d)
    raise SystemExit('nem találom a tételsor-tároló gyökerét (tetelsor/beallitas.json)')


GY = _gyoker()
db = ossz = 0
for p in sorted(glob.glob(os.path.join(GY, 'jelentesek', 'api', 'atiras', 'atir-*.nyers.txt'))):
    s = open(p, encoding='utf-8').read()
    n = int(re.search(r'atir-(\d+)', p).group(1))
    i = s.find('"muveletek"')
    i = s.find('[', i) + 1 if i >= 0 else -1
    ops, dec = [], json.JSONDecoder()
    while i > 0:
        while i < len(s) and s[i] in ' \t\r\n,':
            i += 1
        if i >= len(s) or s[i] != '{':
            break
        try:
            o, j = dec.raw_decode(s, i)
        except ValueError:
            break
        ops.append(o); i = j
    cel = p.replace('.nyers.txt', '.json')
    arch = os.path.join(os.path.dirname(p), 'alkalmazva')
    os.makedirs(arch, exist_ok=True)
    if not os.path.exists(cel):      # kész (teljes) választ soha nem ír felül
        json.dump({'tetel': n, 'csonka': True, 'muveletek': ops, 'nyitott': [], 'osszegzes': ''},
                  open(cel, 'w', encoding='utf-8'), ensure_ascii=False, indent=1)
        db += 1; ossz += len(ops)
    # a nyers válasz az archívumba kerül: a következő körben nem dolgozható fel újra (2026-11-19-i hiba: a régi nyers
    # fájl felülírta az új kör teljes válaszát, és elavult sorszámú műveletek kerültek alkalmazásra)
    k = 1
    while os.path.exists(os.path.join(arch, 'atir-%02d.ny%d.txt' % (n, k))):
        k += 1
    os.replace(p, os.path.join(arch, 'atir-%02d.ny%d.txt' % (n, k)))
print('ment: csonka %d, kimentett művelet %d' % (db, ossz))
