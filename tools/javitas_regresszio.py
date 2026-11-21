#!/usr/bin/env python3
"""Regressziós ellenőrzés a publikált jegyzetek korábbi javítási naplói ellen.

    python3 tools/javitas_regresszio.py --alap=origin/tartalom-javitas          # jelentés: jelentesek/javitas_regresszio.md
    python3 tools/javitas_regresszio.py --alap=origin/tartalom-javitas 51 77    # csak a megadott tételek

Mire való: ha a tételsor publikált jegyzeteit a feldolgozás előtt már auditálták és javították (a javítások a tároló egy
ágán, tételenként a kesz/NN/NN_javitasok.json fájlban állnak: [{file, old, new, hiba}, …]), ez a program megnézi, hogy a
jegyzetre (jegyzetek/…) vonatkozó javítások RÉGI, javítás előtti szövege szerepel-e a tétel mai szövegében (NN.txt).
Találat = a korábban már kijavított hibás szöveg ma is benne van a tételben; minden találatot el kell bírálni
(korpuszhű doboz, másutt pótolt tartalom vagy valódi visszaesés).

Korlát: a 30 karakternél rövidebb régi szöveg így nem vizsgálható (túl sok hamis találatot adna); ezek számát a jelentés
kiírja. A program csak olvas; a jelentésen kívül semmit nem ír. Kilépési kód: 0 (tájékoztató eszköz, nem kapu).
"""
import html as H, json, os, re, subprocess, sys

GY = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
MIN = 30


def norm(s):
    s = re.sub(r'<[^>]+>', ' ', s or '').replace('­', '')
    return re.sub(r'\s+', ' ', H.unescape(s)).strip()


def show(ref, ut):
    r = subprocess.run(['git', '-C', GY, 'show', '%s:%s' % (ref, ut)], capture_output=True)
    return r.stdout.decode('utf-8', 'replace') if r.returncode == 0 else None


def main():
    alap = next((a.split('=', 1)[1] for a in sys.argv[1:] if a.startswith('--alap=')), None)
    if not alap:
        sys.exit('használat: python3 tools/javitas_regresszio.py --alap=<ág vagy commit, amelyen a kesz/NN/NN_javitasok.json áll> [tétel…]')
    szuk = [int(a) for a in sys.argv[1:] if a.isdigit()]
    tetelek = sorted(int(f[:2]) for f in os.listdir(GY) if re.fullmatch(r'\d\d\.txt', f))
    ossz = jegyzet = rovid = vizsgalt = nincs = 0
    talalat = []
    for n in (szuk or tetelek):
        nyers = show(alap, 'kesz/%02d/%02d_javitasok.json' % (n, n))
        if nyers is None:
            nincs += 1
            continue
        txt = norm(open(os.path.join(GY, '%02d.txt' % n), encoding='utf-8').read())
        latott = set()
        for c in json.loads(nyers):
            ossz += 1
            if not str(c.get('file', '')).startswith('jegyzetek/'):
                continue
            jegyzet += 1
            o, u = norm(c.get('old')), norm(c.get('new'))
            if not o or o == u or (o, u) in latott:
                continue
            latott.add((o, u))
            if len(o) < MIN:
                rovid += 1
                continue
            vizsgalt += 1
            # a régi szöveg ma is szerepel, és nem csupán az új (javított) szöveg részeként
            if o in txt and not (u and o in u and u in txt):
                talalat.append((n, c.get('hiba'), o, u))
    sorok = ['# Regressziós ellenőrzés a korábbi jegyzetjavítások ellen', '',
             '- alap: `%s`; tételek: %d; javítási napló nélküli tétel: %d' % (alap, len(szuk or tetelek), nincs),
             '- a naplók összes cseréje: %d; ebből jegyzetre vonatkozik: %d; vizsgált (egyedi, legalább %d karakteres): %d; '
             'túl rövid, nem vizsgálható: %d' % (ossz, jegyzet, MIN, vizsgalt, rovid),
             '- **találat (a javítás előtti szöveg ma is szerepel a tételben): %d**' % len(talalat), '']
    for n, h, o, u in talalat:
        sorok += ['## %d. tétel – hiba: %s' % (n, h), '', '- régi: „%s”' % o[:400], '- javított: „%s”' % (u[:400] or '(törölve)'), '']
    os.makedirs(os.path.join(GY, 'jelentesek'), exist_ok=True)
    open(os.path.join(GY, 'jelentesek', 'javitas_regresszio.md'), 'w', encoding='utf-8').write('\n'.join(sorok) + '\n')
    print('javitas_regresszio: vizsgált csere %d, túl rövid %d, találat %d; jelentés: jelentesek/javitas_regresszio.md'
          % (vizsgalt, rovid, len(talalat)))


if __name__ == '__main__':
    main()
