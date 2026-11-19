#!/usr/bin/env python3
"""Átírt tétel felolvasószövegének újragyártása a meglévő hangdokumentumok darabjaiba.

    python3 tools/tts_ujra.py 10            # próba: kiírja a darabokat és az eltérést, nem ír
    python3 tools/tts_ujra.py 10 --ir       # megírja a tts/<ttsId>/chunk_NNN[_k].txt fájlokat
    python3 tools/tts_ujra.py 10 --szoveg   # a darabok teljes szövege a kimenetre (ellenőrző olvasáshoz)
    python3 tools/tts_ujra.py 10 --reszletes  # a tétel egyetlen darabjára sem illeszkedő kiejtési sorok listája is

Bemenet: tts/_ujra_terv.json (tételenként a hangdokumentumok és a darabok horgonyai, továbbá a kiejtési pótlások).
A hangszöveget a tools/hangszoveg.py szabályai adják (blokk_hang, darabol; legfeljebb 4600 karakter; a doboz fejléce
– a kozos.FEJLEC szerinti fej – a normaszöveggel egy egységben marad; a 4600 karakternél hosszabb dobozt a darabol
bekezdéshatáron, ennek hiányában pont-, illetve sorhatáron több darabra vágja, a fej az első résszel marad). A darab hangcímkéje (pl. [serious]) a régi darab első sorából öröklődik (akkor is, ha a címke után a sorban más is áll).
A futás végén (az utolsó sor előtt) a „nem illeszkedő kiejtési sor: N” összesítés áll: a tts/_ujra_terv.json „kiejtes”
táblájának azok a sorai, amelyek a tétel egyik darabjára sem illeszkedtek; a --reszletes kapcsoló ezeket fel is sorolja.
A program megáll, ha egy horgony nem pontosan egy blokkra illik, ha a horgonyok nem növekvő sorrendben állnak,
ha az első horgony nem a tétel első felolvasandó blokkja, vagy ha a kész szövegben számjegy vagy § marad.
A _meta.json fájlokat nem ez írja: utána `python3 tools/hangmeta.py --alap=<hivatkozás>` kell.
Régi darabfájlt nem töröl. Ha az új tagolás kevesebb darabot adna, mint ahány darabfájl (chunk_NNN, chunk_NNN_k) van,
a darabhatárt 50 karakterenként csökkenti, amíg a darabszám el nem éri a régit (a kimenet „szűkített darabhatár” sora
jelzi); ha így is maradna fölösleges régi folytatódarab, hibával megáll.
"""
import glob, json, os, re, sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import hangszoveg as h

TERV = os.path.join(h.GYOKER, 'tts', '_ujra_terv.json')
h_MAX = 4600


def egysegek(B, a, b):
    out = []; i = a
    while i < b:
        if h.dobozfej(B[i]) and i + 1 < b:
            out.append((f'{i}–{i + 1}', h.blokk_hang(B[i]) + '\n\n' + h.blokk_hang(B[i + 1]))); i += 2
        else:
            out.append((str(i), h.blokk_hang(B[i]))); i += 1
    return out


def main():
    if len(sys.argv) < 2 or not sys.argv[1].isdigit():
        sys.exit(__doc__)
    n = int(sys.argv[1]); ir = '--ir' in sys.argv; szoveg = '--szoveg' in sys.argv; reszletes = '--reszletes' in sys.argv
    terv = json.load(open(TERV, encoding='utf-8'))
    doks = terv['tetelek'].get(str(n))
    if not doks:
        sys.exit(f'HIBA: a {n}. tételnek nincs terve a tts/_ujra_terv.json-ban')
    B = h.blokkok(n)

    def horgony(e):
        t = [i for i, x in enumerate(B) if x.strip().startswith(e)]
        if len(t) != 1:
            sys.exit(f'HIBA: a horgony nem pontosan egy blokkra illik ({len(t)} találat): {e!r}')
        return t[0]

    mind = [horgony(e) for d in doks for _, e in d['darabok']]
    if mind != sorted(set(mind)):
        sys.exit('HIBA: a horgonyok nem szigorúan növekvő sorrendben állnak')
    javitasok = []; szukitve = []; valtozott = uj = 0
    for di, d in enumerate(doks):
        kov = horgony(doks[di + 1]['darabok'][0][1]) if di + 1 < len(doks) else len(B)
        hor = [horgony(e) for _, e in d['darabok']] + [kov]
        mappa = os.path.join(h.GYOKER, 'tts', d['ttsId'])
        for k, (fajl, _) in enumerate(d['darabok']):
            regi_ut = os.path.join(mappa, fajl + '.txt')
            if not os.path.exists(regi_ut):
                sys.exit(f'HIBA: nincs ilyen darab: {regi_ut}')
            cm = re.match(r'\s*(\[[a-z ]+\])', open(regi_ut, encoding='utf-8').read())
            if not cm:
                sys.exit(f'HIBA: a régi darab nem hangcímkével kezdődik: {regi_ut}')
            cimke = cm.group(1)
            egy = []
            for blk, t in egysegek(B, hor[k], hor[k + 1]):
                for a, c in terv.get('kiejtes', []):
                    if a in t:
                        javitasok.append((d['ttsId'], fajl, blk, a, c)); t = t.replace(a, c)
                if re.search(r'[0-9§]', t):
                    sys.exit(f'HIBA: számjegy vagy § maradt a hangszövegben ({n}. tétel, {blk}. blokk)')
                egy.append(t)
            egy = h.hangulat(egy)                      # hangulatcímkék (2026-11-18)
            dar = h.darabol(egy, cimke=cimke)
            ism = lambda L: [re.sub(r'^(\[[a-z ]+\])\n\n(?:\[short pause\] )?(?:\1 )?', r'\1\n\n', y) for y in L]   # a darab címkéje után nincs szünet és ismételt címke
            dar = ism(dar)
            # régi folytatódarab nem válhat fölöslegessé: ha az új tagolás kevesebb darabot adna, mint ahány darabfájl van,
            # a program a darabhatárt (nem a doboz vágási határát) lépésenként csökkenti, amíg a darabszám el nem éri a régit
            regi_db = max([1] + [int(re.search(r'_(\d+)\.txt$', x).group(1)) for x in glob.glob(os.path.join(mappa, fajl + '_*.txt'))])
            if len(dar) < regi_db:
                for mx in range(h_MAX - 50, 1000, -50):
                    dar = ism(h.darabol(egy, cimke=cimke, max_kar=mx, doboz_max=h_MAX))
                    if len(dar) >= regi_db:
                        break
                szukitve.append(f'{d["ttsId"]}/{fajl}: {regi_db} régi darabfájl, a darabhatár {mx} karakter')
            nevek = [fajl + '.txt'] + [f'{fajl}_{j}.txt' for j in range(2, len(dar) + 1)]
            folos = sorted(set(os.path.basename(x) for x in glob.glob(os.path.join(mappa, fajl + '_*.txt'))) - set(nevek))
            if folos:
                sys.exit(f'HIBA: fölöslegessé vált régi folytatódarab: {d["ttsId"]}/{", ".join(folos)} – a tervet a központi chat igazítja')
            allapot = []
            for nev, y in zip(nevek, dar):
                ut = os.path.join(mappa, nev)
                if not os.path.exists(ut):
                    allapot.append(f'{nev}={len(y)} ÚJ'); uj += 1
                elif open(ut, encoding='utf-8').read() != y:
                    allapot.append(f'{nev}={len(y)} VÁLTOZIK'); valtozott += 1
                else:
                    allapot.append(f'{nev}={len(y)} azonos')
                if ir:
                    open(ut, 'w', encoding='utf-8').write(y)
                if szoveg:
                    print('#####', d['ttsId'], nev); print(y)
            print(f'{n}. tétel {d["ttsId"]} {fajl}: blokk {hor[k]}–{hor[k + 1] - 1}; ' + '; '.join(allapot))
    if hor and mind[0] != min(i for i, x in enumerate(B) if h.blokk_hang(x).strip()):
        print('FIGYELEM: az első horgony előtt felolvasandó blokk áll – ellenőrizd a hanglefedettséget')
    for x in szukitve:
        print('szűkített darabhatár (régi folytatódarab megtartása):', x)
    print('kiejtési pótlások:')
    for x in javitasok:
        print('  ', *x, sep=' | ')
    hasznalt = {x[3] for x in javitasok}
    nem_ill = [(a, c) for a, c in terv.get('kiejtes', []) if a not in hasznalt]
    if reszletes:
        for a, c in nem_ill:
            print(f'   nem illeszkedik: {a!r} → {c!r}')
    print(f'nem illeszkedő kiejtési sor: {len(nem_ill)} (a {len(terv.get("kiejtes", []))} sorból)')
    print(f'{"megírva" if ir else "próba (nem írt)"}: változó darab {valtozott}, új darab {uj}')


if __name__ == '__main__':
    main()
