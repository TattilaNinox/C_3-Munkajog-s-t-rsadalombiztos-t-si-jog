#!/usr/bin/env python3
"""Az élő export (EX-1, `elo-…` ág) átvétele a tételsor munkaágára: a publikált jegyzetek, a hangszöveg és a régi termékek
a MAI élő állapotra kerülnek, hogy a feldolgozás és a későbbi csere viszonyítási alapja az élő tartalom legyen.

    python3 tools/elo_atvesz.py --alap=origin/elo-2026-11-20-1835          # próbafutás: csak számol és kiír
    python3 tools/elo_atvesz.py --alap=origin/elo-2026-11-20-1835 --ir     # átveszi (a munkafába és az indexbe; commit nincs)
    … --csak=tts,kviz        # csak a megadott egységek (jegyzetek, tts, kviz, tanulokartyak, hezagpotlok, memoriautvonal, export)

Mit vesz át:
  jegyzetek/   – a `jegyzetek/manifest.json` minden eleméhez az élő jegyzet (`egyeb/notes/NN/<id>.json`, `pages[0]`) HTML-je a
                 meglévő fájl helyére; a jegyzék `chars` és `sha256` mezője frissül. A jegyzékben nem szereplő élő szöveges
                 jegyzetet és az élőből hiányzó jegyzékelemet NEM veszi fel és nem törli: kiírja (a döntés a központi chaté).
  tts/, kviz/, tanulokartyak/, hezagpotlok/, memoriautvonal/ – a mappa teljes tartalma az alap állapotára (ami az élőben
                 nincs meg, az a mappából is törlődik).
  EXPORT.json  – az export leírója (tetelsorId, az export ideje).
Mit NEM vesz át: a tételfájlokat (NN.txt), a korpuszt, a `tetelsor/`, `kontroll/`, `termekek/`, `tools/` mappát.
A program az adatbázishoz nem nyúl; csak a tároló fájljait írja, és csak `--ir` kapcsolóval.
"""
import hashlib, json, os, shutil, subprocess, sys

GY = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
MAPPAK = ['tts', 'kviz', 'tanulokartyak', 'hezagpotlok', 'memoriautvonal']


def git(*a, szoveg=True):
    r = subprocess.run(['git', '-C', GY] + list(a), capture_output=True)
    if r.returncode != 0:
        return None
    return r.stdout.decode('utf-8', 'replace') if szoveg else r.stdout


def main():
    alap = next((a.split('=', 1)[1] for a in sys.argv[1:] if a.startswith('--alap=')), None)
    if not alap or git('rev-parse', '--verify', '-q', alap + '^{commit}') is None:
        sys.exit('használat: python3 tools/elo_atvesz.py --alap=<az élő export ága vagy commitja> [--ir] [--csak=…]')
    ir = '--ir' in sys.argv
    csak = next((a.split('=', 1)[1].split(',') for a in sys.argv[1:] if a.startswith('--csak=')), None)
    kell = lambda x: csak is None or x in csak
    ki = {}

    if kell('jegyzetek'):
        mp = os.path.join(GY, 'jegyzetek', 'manifest.json')
        m = json.load(open(mp, encoding='utf-8'))
        valt = azonos = 0; hianyzik = []
        ismert = set()
        for it in m['items']:
            ismert.add(it['id'])
            nyers = git('show', '%s:egyeb/notes/%02d/%s.json' % (alap, int(it['sorszam']), it['id']))
            if nyers is None:
                hianyzik.append('%s (%s. tétel)' % (it['id'], it['sorszam'])); continue
            d = json.loads(nyers)
            pages = d.get('pages')
            if not isinstance(pages, list) or len(pages) != 1 or not isinstance(pages[0], str):
                hianyzik.append('%s (%s. tétel): a pages nem egyelemű szöveglista' % (it['id'], it['sorszam'])); continue
            uj = pages[0].encode('utf-8')
            f = os.path.join(GY, it['file'])
            regi = open(f, 'rb').read() if os.path.exists(f) else b''
            if regi == uj:
                azonos += 1; continue
            valt += 1
            if ir:
                open(f, 'wb').write(uj)
                it['chars'] = len(pages[0]); it['sha256'] = hashlib.sha256(uj).hexdigest()
        # az élőben meglévő, a jegyzékben nem szereplő szöveges jegyzetek
        uj_elo = []
        for sor in (git('ls-tree', '-r', '--name-only', alap, '--', 'egyeb/notes') or '').split('\n'):
            if not sor.endswith('.json'):
                continue
            nid = os.path.basename(sor)[:-5]
            if nid in ismert:
                continue
            d = json.loads(git('show', '%s:%s' % (alap, sor)))
            if d.get('type') == 'text':
                uj_elo.append('%s – %s' % (sor, str(d.get('title'))[:70]))
        if ir and valt:
            json.dump(m, open(mp, 'w', encoding='utf-8'), ensure_ascii=False, indent=1); open(mp, 'a').write('\n')
            subprocess.run(['git', '-C', GY, 'add', 'jegyzetek'], check=True)
        ki['jegyzetek'] = {'jegyzek': len(m['items']), 'valtozik': valt, 'azonos': azonos,
                           'az_elobol_hianyzik': hianyzik, 'elo_szoveges_jegyzet_a_jegyzeken_kivul': uj_elo}

    for mp_ in MAPPAK:
        if not kell(mp_):
            continue
        st = (git('diff', '--name-status', 'HEAD', alap, '--', mp_) or '').strip().split('\n')
        sz = {}
        for s in st:
            if s:
                sz[s[0]] = sz.get(s[0], 0) + 1
        ki[mp_] = {'modosul': sz.get('M', 0), 'uj': sz.get('A', 0), 'torlodik': sz.get('D', 0), 'atnevezve': sz.get('R', 0)}
        if ir and st != ['']:
            subprocess.run(['git', '-C', GY, 'rm', '-r', '-q', '--ignore-unmatch', mp_], check=True)
            shutil.rmtree(os.path.join(GY, mp_), ignore_errors=True)
            subprocess.run(['git', '-C', GY, 'checkout', alap, '--', mp_], check=True)

    if kell('export'):
        e = git('show', alap + ':EXPORT.json')
        ki['export'] = 'nincs EXPORT.json az alapon' if e is None else {k: json.loads(e).get(k) for k in ('tetelsorId', 'exportIdeje', 'ag')}
        if ir and e is not None:
            open(os.path.join(GY, 'EXPORT.json'), 'w', encoding='utf-8').write(e)
            subprocess.run(['git', '-C', GY, 'add', 'EXPORT.json'], check=True)

    print(json.dumps({'alap': alap, 'mod': 'ÁTVÉVE (commit nincs)' if ir else 'próbafutás', **ki}, ensure_ascii=False, indent=1))


if __name__ == '__main__':
    main()
