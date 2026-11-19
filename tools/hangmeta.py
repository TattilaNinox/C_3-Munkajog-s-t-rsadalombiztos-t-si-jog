#!/usr/bin/env python3
"""A hangdokumentumok _meta.json fájljának újraépítése a mappában lévő darabfájlokból.

    python3 tools/hangmeta.py --alap=<git-hivatkozás>      # pl. az élő állapotot tükröző ág vagy commit

A darabok sorrendje: chunk_NNN.txt, majd chunk_NNN_2.txt, chunk_NNN_3.txt … (az NNN. darab után következők).
A `valtozas` mező az alaphoz viszonyít: nincs (bájtra azonos), `modositott` (más a szöveg), `uj` (az alapban nincs ilyen fájl).
A többi mezőt (cím, noteId, a kész darabok audioFile-ja) megtartja. Csak a _meta.json fájlokat írja.
"""
import glob, json, os, re, subprocess, sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import kozos

GYOKER = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


def alap_fajl(ref, ut):
    r = subprocess.run(['git', 'show', f'{ref}:{ut}'], cwd=GYOKER, capture_output=True)
    return r.stdout.decode('utf-8') if r.returncode == 0 else None


def kulcs(nev):
    m = re.match(r'chunk_(\d+)(?:_(\d+))?\.txt$', nev)
    return (int(m.group(1)), int(m.group(2) or 1))


def main():
    kozos.beallitas()['hangAlapAgak']  # kulcs-ellenőrzés; az --alap kötelező marad, nincs csendes alapérték
    ref = next((a.split('=', 1)[1] for a in sys.argv[1:] if a.startswith('--alap=')), None)
    if not ref:
        raise SystemExit('Kötelező: --alap=<git-hivatkozás>')
    if subprocess.run(['git', '-C', GYOKER, 'rev-parse', '--verify', '--quiet', ref + '^{commit}'], capture_output=True).returncode != 0:
        raise SystemExit(f'Az --alap hivatkozás nem létezik: {ref} (előbb: git fetch origin <ág>); nem íródik át egyetlen _meta.json sem.')
    valt = 0
    for mf in sorted(glob.glob(os.path.join(GYOKER, 'tts', '*', '_meta.json'))):
        d = os.path.dirname(mf); rel = os.path.relpath(d, GYOKER)
        m = json.load(open(mf, encoding='utf-8'))
        regi = {c['file']: c for c in m['chunks']}
        am = alap_fajl(ref, rel + '/_meta.json')
        alap_meta = {c['file']: c for c in json.loads(am)['chunks']} if am else {}
        fajlok = sorted((os.path.basename(f) for f in glob.glob(os.path.join(d, 'chunk_*.txt'))), key=kulcs)
        uj = []
        for f in fajlok:
            sz = open(os.path.join(d, f), encoding='utf-8').read()
            a = alap_fajl(ref, f'{rel}/{f}')
            e = dict(alap_meta.get(f) or regi.get(f) or {'file': f, 'index': None, 'status': 'uj', 'audioFile': None})
            e['file'] = f; e['charCount'] = len(sz)
            ok = (regi.get(f) or {}).get('ok')
            e.pop('valtozas', None); e.pop('ok', None)
            if a is None:
                e.update(index=None, status='uj', audioFile=None, valtozas='uj')
            elif a != sz:
                e['valtozas'] = 'modositott'
            if e.get('valtozas') and ok:
                e['ok'] = ok
            uj.append(e)
        m2 = dict(m); m2['chunks'] = uj; m2['chunkCount'] = len(uj)
        ki = json.dumps(m2, ensure_ascii=False, indent=2) + '\n'
        if ki != open(mf, encoding='utf-8').read():
            open(mf, 'w', encoding='utf-8').write(ki); valt += 1
    print('átírt _meta.json:', valt)


if __name__ == '__main__':
    main()
