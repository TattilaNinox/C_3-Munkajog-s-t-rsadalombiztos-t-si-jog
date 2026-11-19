#!/usr/bin/env python3
"""A közös szakvizsga-eszközkészlet másolása a tételsor-tároló tools/ mappájába.

    python3 tools/szakvizsga/szinkron.py --cel=<tételsor-tároló>

A szkript saját mappája a közös készlet. Nem commitol. A zárba az admin tároló
`git log -1 --format=%H -- tools/szakvizsga` commitját írja; ha nincs ilyen commit,
érthető hibával megáll.
"""
import hashlib, json, os, shutil, subprocess, sys

HELYI = ['matrix_adat.py', 'hang_ar.json']


def keszlet_mappa():
    return os.path.dirname(os.path.abspath(__file__))


def admin_gyoker(keszlet):
    return os.path.dirname(os.path.dirname(keszlet))


def admin_commit(keszlet):
    r = subprocess.run(
        ['git', 'log', '-1', '--format=%H', '--', 'tools/szakvizsga'],
        cwd=admin_gyoker(keszlet), capture_output=True, text=True,
    )
    h = (r.stdout or '').strip()
    if r.returncode != 0 or not h:
        sys.stderr.write(
            'szinkron: a tools/szakvizsga még nincs committolva az admin tárolóban; '
            'a szinkron a commit után futtatható\n'
        )
        raise SystemExit(2)
    return h


def sha256(ut):
    h = hashlib.sha256()
    with open(ut, 'rb') as f:
        for darab in iter(lambda: f.read(65536), b''):
            h.update(darab)
    return h.hexdigest()


def rel_fajlok(gyoker):
    ki = []
    for gy, mappak, nevek in os.walk(gyoker):
        mappak[:] = [m for m in mappak if m != '__pycache__']
        for n in nevek:
            if n.endswith('.pyc') or n == '.DS_Store':
                continue
            rel = os.path.relpath(os.path.join(gy, n), gyoker).replace(os.sep, '/')
            ki.append(rel)
    return ki


def main():
    cel = None
    for a in sys.argv[1:]:
        if a.startswith('--cel='):
            cel = a.split('=', 1)[1]
        elif a in ('-h', '--help'):
            sys.stdout.write('használat: python3 tools/szakvizsga/szinkron.py --cel=<tételsor-tároló>\n')
            raise SystemExit(0)
        else:
            sys.stderr.write('szinkron: ismeretlen argumentum: %s\n' % a)
            raise SystemExit(2)
    if not cel:
        sys.stderr.write('használat: python3 tools/szakvizsga/szinkron.py --cel=<tételsor-tároló>\n')
        raise SystemExit(2)
    keszlet = keszlet_mappa()
    commit = admin_commit(keszlet)
    cel_tools = os.path.join(os.path.abspath(cel), 'tools')
    if os.path.isdir(os.path.abspath(cel)) and not os.path.isdir(cel_tools):
        os.makedirs(cel_tools)      # új tételsor: a tools/ mappát a szinkron hozza létre
    if not os.path.isdir(cel_tools):
        sys.stderr.write('szinkron: nincs tools/ a célban: %s\n' % cel_tools)
        raise SystemExit(2)
    kozos = [r for r in rel_fajlok(keszlet) if r not in HELYI]
    hashes = {}
    for rel in kozos:
        src = os.path.join(keszlet, rel.replace('/', os.sep))
        dst = os.path.join(cel_tools, rel.replace('/', os.sep))
        os.makedirs(os.path.dirname(dst), exist_ok=True)
        shutil.copy2(src, dst)
        hashes[rel] = sha256(dst)
    kit = set(kozos)
    helyi = set(HELYI)
    for rel in rel_fajlok(cel_tools):
        if rel == 'eszkozok.lock':
            continue
        if rel in kit or rel in helyi:
            continue
        os.remove(os.path.join(cel_tools, rel.replace('/', os.sep)))
    zar = {
        'sema': 1,
        'adminCommit': commit,
        'fajlok': hashes,
        'helyi': HELYI,
    }
    ki = os.path.join(cel_tools, 'eszkozok.lock')
    json.dump(zar, open(ki, 'w', encoding='utf-8'), ensure_ascii=False, indent=1)
    open(ki, 'a', encoding='utf-8').write('\n')
    print('szinkron: %d fájl, adminCommit %s' % (len(hashes), commit))


if __name__ == '__main__':
    main()
