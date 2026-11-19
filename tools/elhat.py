#!/usr/bin/env python3
"""Új szakasz (pl. Elhatárolások) beszúrása az összefoglalás elé a tételben és a hangszövegben.
Használat: elhat.py <tétel> <szakasz.txt> [--proba]
A szakasz.txt első sora a címsor a tétel számozása nélkül (pl. 'ELHATÁROLÁSOK'), utána üres sorral tagolt bekezdések.
A tételben az összefoglalás címsora elé kerül, az összefoglalás sorszáma eggyel nő (ha van római sorszáma).
A hangban az összefoglalás címsorát tartalmazó darab három részre bomlik: előtte / új szakasz / összefoglalás.
"""
import sys, os, re, glob, json
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import hangszoveg as h

ROMAI = ['I','II','III','IV','V','VI','VII','VIII','IX','X','XI','XII','XIII','XIV','XV','XVI']
SORSZ = ['első','második','harmadik','negyedik','ötödik','hatodik','hetedik','nyolcadik','kilencedik','tizedik','tizenegyedik','tizenkettedik','tizenharmadik','tizennegyedik','tizenötödik','tizenhatodik']

def main():
    n = int(sys.argv[1]); szak = open(sys.argv[2], encoding='utf-8').read().strip().split('\n\n')
    proba = '--proba' in sys.argv
    fajl = os.path.join(h.GYOKER, f'{n:02d}.txt')
    s = open(fajl, encoding='utf-8').read()
    m = list(re.finditer(r'^(?:([IVX]+)\. )?(ÖSSZEFOGLALÁS|ÖSSZEGZÉS)[^\n]*$', s, re.M))
    assert len(m) == 1, f'összefoglalás címsor: {len(m)} találat'
    m = m[0]; rom = m.group(1)
    if rom:
        k = ROMAI.index(rom); ujcim = f'{rom}. {szak[0]}'; ossz = f'{ROMAI[k+1]}. {m.group(2)}'
    else:
        k = None; ujcim = szak[0]; ossz = m.group(0)
    uj = ujcim + '\n\n' + '\n\n'.join(szak[1:]) + '\n\n'
    s2 = s[:m.start()] + uj + ossz + s[m.end():]
    # hang: az összefoglalás címsorát tartalmazó darab
    jel = []
    for tid, meta, lista in h.tetel_hang(n):
        for f, t in lista:
            for i, sor in enumerate(t.rstrip('\n').split('\n')):
                if re.search(r'(összefoglalás|összegzés)\s*\.{0,3}\s*$', sor, re.I) and len(sor) < 90:
                    jel.append((tid, f, i, sor))
    assert len(jel) == 1, f'hang összefoglalás-címsor: {jel}'
    tid, f, i, sor = jel[0]
    d = os.path.join(h.GYOKER, 'tts', tid)
    c = open(os.path.join(d, f), encoding='utf-8').read().rstrip('\n').split('\n')
    alap = f[:-4]
    letezo = [x for x in os.listdir(d) if x.startswith(alap + '_')]
    hang_uj = h.darabol([h.blokk_hang(b) for b in [ujcim] + szak[1:]], '[serious]', 4700)
    ujsor = sor
    if k is not None:
        for a, b in ((SORSZ[k], SORSZ[k+1]), (SORSZ[k].capitalize(), SORSZ[k+1].capitalize())):
            if re.search(r'\b' + a + r'\b', ujsor):
                ujsor = re.sub(r'\b' + a + r'\b', b, ujsor, count=1); break
    print(f'{n}. tétel: {tid}/{f} {i+1}. sora: {sor!r} -> {ujsor!r}; új szakasz: {[len(x) for x in hang_uj]} karakter; meglévő utódarabok: {letezo}')
    if proba: return
    assert not letezo or re.match(r'chunk_\d+_\d+$', alap) is None, 'kézi munka kell'
    if letezo:  # a darabnak már vannak _k utódai: toljuk őket
        szamok = sorted([int(re.search(r'_(\d+)\.txt$', x).group(1)) for x in letezo], reverse=True)
        for z in szamok:
            os.rename(os.path.join(d, f'{alap}_{z}.txt'), os.path.join(d, f'{alap}_{z+len(hang_uj)+1}.txt'))
    def ir(nev, sorok):
        open(os.path.join(d, nev), 'w', encoding='utf-8').write('\n'.join(sorok).rstrip() + '\n')
    eleje = c[:i]
    while eleje and not eleje[-1].strip(): eleje.pop()
    ir(f, eleje)
    for z, x in enumerate(hang_uj):
        open(os.path.join(d, f'{alap}_{2+z}.txt'), 'w', encoding='utf-8').write(x)
    veg = [ujsor] + c[i+1:]
    if not veg[0].startswith('['): veg = ['[serious]'] + veg
    ir(f'{alap}_{2+len(hang_uj)}.txt', veg)
    open(fajl, 'w', encoding='utf-8').write(s2)
    print('kész')

if __name__ == '__main__':
    main()
