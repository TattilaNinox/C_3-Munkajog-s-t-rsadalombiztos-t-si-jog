#!/usr/bin/env python3
"""Két korpusz-állapot §-onkénti összevetése és az érintett tételek listája. A tároló gyökeréből:

    python3 tools/korpusz_valtozas.py <régi commit> [<új commit vagy munkafa: .>] > korpusz/valtozas_<dátum>.md

A szóköz-, gondolatjel- és idézőjel-eltérést nem tekinti változásnak. Érintett egy tétel, ha a változott
§ a tétel előírt tartományába esik, dobozban szerepel, vagy a tétel hivatkozik rá.
"""
import os, re, subprocess, sys, tempfile, difflib
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import kozos
from ellenorzes import emlitett_paragrafusok, tartomany  # noqa: E402

REGI = sys.argv[1]
KUL = lambda s: re.sub(r'[\s\-–—"„”]', '', s)


def regi_szoveg(kod, fajl):
    nev = 'korpusz/' + kozos.nfc(fajl)
    try:
        b = subprocess.check_output(['git', 'show', f'{REGI}:{nev}'], cwd=kozos.GYOKER)
    except subprocess.CalledProcessError:
        return None
    with tempfile.NamedTemporaryFile('wb', suffix='.txt', delete=False) as t:
        t.write(b)
    try:
        return kozos.jogszabaly_paragrafusok(kod, t.name)
    finally:
        os.unlink(t.name)


def main():
    F = kozos.forrasok(); TS = kozos.tetelsor()
    L = [f'# Korpusz-változás: `{REGI[:8]}` → munkafa', '',
         'Változás = a § szövege eltér (szóköz, gondolatjel, idézőjel nem számít). Új § = a régi szövegben nem volt ilyen fejléc '
         '(ez lehet a régi fájl tagolási hibája is). Érintett tétel: a § az előírt tartományba esik, dobozban szerepel vagy hivatkozott.', '']
    for kod, f in F.items():
        if f['tipus'] not in ('törvény', 'rendelet') or not f.get('korpusz'):
            continue
        uj_f = kozos.korpusz_fajl(f['korpusz'][0])
        r = regi_szoveg(kod, f['korpusz'][0])
        if not uj_f or not r:
            continue
        (regi, rs), (uj, us) = r, kozos.jogszabaly_paragrafusok(kod, uj_f)
        valt = [p for p in rs if p in uj and KUL(regi[p]) != KUL(uj[p])]
        ujp = [p for p in us if p not in regi]
        if not valt and not ujp:
            continue
        L.append(f'## {kod} – {f["nev"]}')
        L.append(f'- változott §: {len(valt)}; új §: {len(ujp)} ({", ".join(ujp[:20])})')
        for p in valt:
            a, b = regi[p].split(' '), uj[p].split(' ')
            d = [(' '.join(a[i1:i2]), ' '.join(b[j1:j2])) for t, i1, i2, j1, j2 in difflib.SequenceMatcher(None, a, b).get_opcodes() if t != 'equal']
            erint = []
            for t in TS['tetelek']:
                n = t['sorszam']; txt = kozos.tetel_szoveg(n)
                benne = any(e['forras'] == kod and 'tol' in e and (tartomany(us, e['tol'], e['ig']) or []) and p in tartomany(us, e['tol'], e['ig']) for e in t['eloirasok'])
                dob = any(k == kod and q == p for k, q, _, _ in kozos.dobozok(txt))
                eml = p in emlitett_paragrafusok(txt, kod)
                if benne or dob or eml:
                    erint.append(f'{n}' + (' (doboz)' if dob else ''))
            minta = '; '.join(f'„{x[:80]}” → „{y[:80]}”' for x, y in d[:2])
            L.append(f'  - **{p}. §** — érintett tétel: {", ".join(erint) or "nincs"} — {minta}')
        L.append('')
    print('\n'.join(L))


main()
