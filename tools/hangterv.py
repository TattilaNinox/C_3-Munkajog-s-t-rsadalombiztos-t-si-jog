#!/usr/bin/env python3
"""Betöltési terv a hangszöveg-változásokhoz: az alaphoz (az élő állapotot tükröző commithoz) képest eltérő hangdokumentumok.

    python3 tools/hangmeta.py --alap=<ref>      # előbb a _meta.json-ok rendbetétele
    python3 tools/hangterv.py --alap=<ref> [--ki=hangpotlas/terv.json]

A darab helye (index) a _meta.json sorrendje, 1-től. Művelet (hely és szöveg szerint, a fájlnév nem számít):
valtozatlan (ugyanaz a szöveg ugyanazon a helyen), elmozdult (a szöveg az alapban más helyen áll – a hangfájl neve a
helyhez kötött, ezért újra kell generálni), modositott (ezen a helyen az alapban más szöveg áll), uj (az alapnak ennyi
darabja nincs). Élesítéskor az alap a friss élő export ága (elo-…), mert a hang állapota az élő adatban a mérvadó. A betöltő: orlomed_admin_web/functions/scripts/hangpotlas_betolt.js.
"""
import glob, hashlib, json, os, re, subprocess, sys

GYOKER = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sha = lambda s: hashlib.sha256(s.encode('utf-8')).hexdigest()


def show(ref, ut):
    r = subprocess.run(['git', 'show', f'{ref}:{ut}'], cwd=GYOKER, capture_output=True)
    return r.stdout.decode('utf-8') if r.returncode == 0 else None


def main():
    arg = dict(a[2:].split('=', 1) for a in sys.argv[1:] if a.startswith('--') and '=' in a)
    ref = arg.get('alap') or sys.exit('Kötelező: --alap=<git-hivatkozás>')
    ki = arg.get('ki', 'hangpotlas/terv.json')
    commit = subprocess.run(['git', 'rev-parse', ref], cwd=GYOKER, capture_output=True, text=True).stdout.strip()
    terv = {'alap_commit': commit, 'leiras': arg.get('leiras', ''), 'dokumentumok': []}
    ossz = {'uj': 0, 'modositott': 0, 'elmozdult': 0}; db = {'uj': 0, 'modositott': 0, 'elmozdult': 0}
    for mf in sorted(glob.glob(os.path.join(GYOKER, 'tts', '*', '_meta.json'))):
        rel = os.path.relpath(os.path.dirname(mf), GYOKER)
        m = json.load(open(mf, encoding='utf-8'))
        am = show(ref, rel + '/_meta.json')
        if am is None:
            continue
        regi_fajlok = [c['file'] for c in json.loads(am)['chunks']]
        regi_szoveg = {f: show(ref, f'{rel}/{f}') for f in regi_fajlok}
        regi_hely = {f: i for i, f in enumerate(regi_fajlok, 1)}
        regi_lista = [regi_szoveg[f] for f in regi_fajlok]
        hasznalt = set()
        uj = []
        for i, c in enumerate(m['chunks'], 1):
            t = open(os.path.join(GYOKER, rel, c['file']), encoding='utf-8').read()
            f = c['file']
            # Hely és szöveg szerinti egyeztetés (2026-11-18, IM-2): a hangfájl neve a helyhez kötött, a darabfájl neve
            # viszont az élő exportban (chunk_NNN) és a tárolóban (chunk_NNN_2) eltér – a név nem lehet a kulcs.
            if i <= len(regi_lista) and regi_lista[i - 1] == t:
                mit, ri = 'valtozatlan', i
            else:
                ri = next((j for j, x in enumerate(regi_lista, 1) if x == t and j not in hasznalt and j != i), None)
                if ri is not None:
                    mit = 'elmozdult'
                elif i <= len(regi_lista):
                    mit, ri = 'modositott', i
                else:
                    mit = 'uj'
            if ri is not None:
                hasznalt.add(ri)
            e = {'index': i, 'muvelet': mit, 'regiIndex': ri, 'charCount': len(t), 'fajl': f'{rel}/{f}'}
            if mit == 'valtozatlan':
                e['sha256'] = sha(t)
            else:
                e['fullText'] = t; ossz[mit] += len(t); db[mit] += 1
            uj.append(e)
        if all(e['muvelet'] == 'valtozatlan' for e in uj) and len(uj) == len(regi_fajlok):
            continue
        n = re.search(r'> (\d+)\. ', m['tagPath'] + ' ') or re.match(r'(\d+)\. ', m['title'])
        terv['dokumentumok'].append({
            'ttsId': m['ttsId'], 'noteId': m.get('noteId'), 'tetel': int(n.group(1)) if n else None, 'cim': m['title'],
            'regi': [{'index': regi_hely[f], 'sha256': sha(regi_szoveg[f]), 'charCount': len(regi_szoveg[f])} for f in regi_fajlok],
            'uj': uj})
    terv['osszesites'] = {'dokumentum': len(terv['dokumentumok']), 'generalando_karakter': sum(ossz.values()),
                          **{k + '_karakter': v for k, v in ossz.items()}, **{k + '_darab': v for k, v in db.items()}}
    os.makedirs(os.path.dirname(os.path.join(GYOKER, ki)), exist_ok=True)
    with open(os.path.join(GYOKER, ki), 'w', encoding='utf-8') as f:
        json.dump(terv, f, ensure_ascii=False, indent=1); f.write('\n')
    print(json.dumps(terv['osszesites'], ensure_ascii=False))
    for d in terv['dokumentumok']:
        print(d['tetel'], d['ttsId'], len(d['regi']), '→', len(d['uj']), [(e['index'], e['muvelet'][:3], e['charCount']) for e in d['uj'] if e['muvelet'] != 'valtozatlan'])


if __name__ == '__main__':
    main()
