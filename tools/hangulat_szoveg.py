#!/usr/bin/env python3
"""Hangulatcímkék azokra a hangdokumentumokra, amelyek nincsenek az újraíró tervben (tts/_ujra_terv.json) – ezek
szövegét a tts_ujra.py nem állítja elő újra, ezért a címkézés a darabfájl bekezdésein történik, ugyanazzal a szabállyal
(hangszoveg.hangulat). Idempotens. A darab nem nőhet 4600 karakter fölé (a már hosszabb darab nem nőhet tovább): ilyenkor
a darab végéről marad el címke.

Csak az a darab kap címkét, amely az élő hanghoz képest egyébként is változik (Attila döntése, 2026-11-18): az a darab,
amelynek szövege a címkéktől eltekintve azonos az alappal (--alap, az élő hang ága), az alap szövegére áll vissza – a
terv szerinti dokumentumokban is –, így miatta hang nem generálódik újra. Futási sorrend: tts_ujra.py (8–85.) →
hangulat_szoveg.py → hangmeta.py.

  python3 tools/hangulat_szoveg.py --alap=origin/hangpotlas-2-2026-11-12          próba
  python3 tools/hangulat_szoveg.py --alap=origin/hangpotlas-2-2026-11-12 --ir     megírja
"""
import glob, json, os, re, subprocess, sys
import hangszoveg as h
import kozos

MAX = 4600


def cimkez(t):
    m = re.match(r'\s*(\[[a-z ]+\])\n\n', t)
    fej, torzs = (m.group(1), t[m.end():]) if m else (None, t)
    egys = torzs.rstrip('\n').split('\n\n')
    alap = [re.sub(r'^(?:' + h.HANGULAT.pattern[1:] + ')+', '', e) for e in egys]
    keret = max(MAX, len(t))
    uj = h.hangulat(alap, kezdo=fej[1:-1] if fej else None)
    def ossze(L):
        return (fej + '\n\n' if fej else '') + '\n\n'.join(L) + '\n'
    i = len(uj)
    while len(ossze(uj)) > keret and i > 0:
        i -= 1; uj[i] = alap[i]
    return ossze(uj)


def main():
    kozos.beallitas()['hangAlapAgak']  # kulcs-ellenőrzés; az --alap kötelező marad, nincs csendes alapérték
    ir = '--ir' in sys.argv
    terv = json.load(open(os.path.join(h.GYOKER, 'tts', '_ujra_terv.json'), encoding='utf-8'))
    tervben = {d['ttsId'] for L in terv['tetelek'].values() for d in L}
    alap = next((a.split('=', 1)[1] for a in sys.argv if a.startswith('--alap=')), None)
    if not alap:
        sys.exit('HIBA: kötelező az --alap=<az élő hang ága> kapcsoló')
    cimke = re.compile(r'\[(?:serious|calm|emphatic|thoughtful|curious|short pause)\] ?')
    mag = lambda t: re.sub(r'\s+', ' ', cimke.sub('', t)).strip()
    db = valt = vissza = 0
    def elo(ut):
        r = subprocess.run(['git', '-C', h.GYOKER, 'show', f'{alap}:{os.path.relpath(ut, h.GYOKER)}'], capture_output=True, text=True)
        return r.stdout if r.returncode == 0 else None
    for mf in sorted(glob.glob(os.path.join(h.GYOKER, 'tts', '*', '_meta.json'))):
        m = json.load(open(mf, encoding='utf-8'))
        if m['ttsId'] in tervben:
            continue
        for c in m['chunks']:
            ut = os.path.join(os.path.dirname(mf), c['file']); t = open(ut, encoding='utf-8').read(); db += 1
            u = t if elo(ut) == t else cimkez(t)        # az élő hanggal azonos darab érintetlen marad
            if u != t:
                valt += 1
                if ir:
                    open(ut, 'w', encoding='utf-8').write(u)
    for ut in sorted(glob.glob(os.path.join(h.GYOKER, 'tts', '*', 'chunk_*.txt'))):
        e = elo(ut); t = open(ut, encoding='utf-8').read()
        if e is not None and e != t and mag(e) == mag(t):
            vissza += 1
            if ir:
                open(ut, 'w', encoding='utf-8').write(e)
    print(f'{"megírva" if ir else "próba"}: {db} darab a terven kívül, változik {valt}; az élő hanggal azonos szövegű, visszaállított darab: {vissza}')


if __name__ == '__main__':
    main()
