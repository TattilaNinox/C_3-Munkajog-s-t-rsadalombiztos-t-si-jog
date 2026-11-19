#!/usr/bin/env python3
"""S3: a jogszabálydobozok újraépítése a korpuszból – teljes bekezdésekkel, betűre. A §-os és a cikkre tagolt
forrás dobozára is (a forrás egysége a beállításból: kozos.egyseg; a bekezdésszerkezet a korpuszfájl soraiból).
Használat (a tárolóból): python3 tools/s5/doboz_javit.py [--sor] [--diff] [--ir] [tétel ...]
A doboz által érintett bekezdéseket (és a szögletes címet, ha a dobozban volt) a korpusz
sorrendjében, a korpusz soraiból írja újra; csak ott módosít, ahol a doboz eltér.
"""
import os, re, sys, difflib
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import kozos

IR = '--ir' in sys.argv
TETELEK = [int(a) for a in sys.argv[1:] if a.isdigit()]
F = kozos.forrasok()


def csillagtalan(l):
    l = kozos.nfc(l).replace(' ', ' ')
    l = re.sub(r'\s*\*(?=\s|$)', '', l)
    return re.sub(r'[ \t]+', ' ', l).strip()


def cimsor(l):
    if l.startswith('['):
        return False
    if re.match(r'^\(\d+[a-z]?\)', l) or re.match(r'^[a-z]{1,2}\) ', l):
        return False
    return not re.search(r'[.;:,]$', l) or (l.isupper() and len(l) > 3)


_CACHE = {}
CSUPASZ = r'(?:\(\d+[a-z]?\)(?:\s*[–-]\s*\(\d+[a-z]?\))?|[a-z]{1,2}\)(?:\s*[–-]\s*[a-z]{1,2}\))?)(?:\s+(?:\(\d+[a-z]?\)|[a-z]{1,2}\)))*'


def paragrafus_sorok(kod):
    if kod in _CACHE:
        return _CACHE[kod]
    p = kozos.korpusz_fajl(F[kod]['korpusz'][0])
    e = kozos.egyseg(kod)          # § vagy cikk, a beállításból; a fejsor szabálya: alapfelvetel.egyseg_sor
    d, cur = {}, None
    for l in open(p, encoding='utf-8').read().split('\n'):
        t = csillagtalan(l)
        m = kozos.egyseg_sor(t, e)
        if m:
            cur = m.group(1)
            if cur in d:
                cur = None; continue  # azonos számú második § (Itv.): az első számít
            d[cur] = []
            rest = t[m.end():].strip().lstrip('-–* ').strip()
            if rest and not (e != '§' and cimsor(rest)):
                d[cur].append(rest)       # a cikkfej utáni cím („3. cikk - Általános joghatóság”) nem normaszöveg
        elif cur is not None and t:
            d[cur].append(t)
    _CACHE[kod] = d
    return d


def csoportok(sorok):
    """[(kulcs, [sorok])] a korpusz sorrendjében; címsorok és üres hatályon kívüli egységek nélkül."""
    out, cur = [], None
    sorok = list(sorok)
    while sorok and cimsor(sorok[-1]):
        sorok.pop()  # a következő § előtti szerkezeti címek
    for l in sorok:
        if re.fullmatch(CSUPASZ, l):
            m = re.match(r'^\((\d+[a-z]?)\)', l)
            if m:
                cur = None; out.append(('hk' + m.group(1), [l]))  # hatályon kívül helyezett bekezdés
            elif out:
                out[-1][1].append(l)  # hatályon kívül helyezett pont
            continue
        if l.startswith('[') and l.endswith(']') and not out:
            out.append(('cim', [l])); continue
        m = re.match(r'^\((\d+[a-z]?)\) ', l)
        if m:
            cur = m.group(1); out.append((cur, [l])); continue
        if cur is None and (not out or out[-1][0] == 'cim'):
            cur = ''; out.append(('', [l])); continue
        if cur is None:
            continue
        out[-1][1].append(l)
    return out


def kulcs_keres(sor, cs):
    n = kozos.norm(re.sub(r'\((?:\.\.\.)\)|\[\.\.\.\]|…', ' ', sor))
    if sor.startswith('[') and sor.endswith(']'):
        return 'cim'
    m = re.match(r'^\((\d+[a-z]?)\) ', sor)
    if m and any(k == m.group(1) for k, _ in cs):
        return m.group(1)
    elso = n.split('  ')[0][:60]
    for k, ls in cs:
        if elso and elso in kozos.norm(' '.join(ls)):
            return k
    best = max(cs, key=lambda kv: difflib.SequenceMatcher(None, kozos.norm(' '.join(kv[1])), n, autojunk=False).ratio())
    return best[0]


def main():
    JOG = kozos.korpusz_jogszabalyok()
    TS = kozos.tetelsor()
    osszes = 0
    for t in TS['tetelek']:
        n = t['sorszam']
        if TETELEK and n not in TETELEK:
            continue
        ut = os.path.join(kozos.GYOKER, f'{n:02d}.txt')
        txt = open(ut, encoding='utf-8').read()
        L = txt.split('\n')
        H = [i for i, l in enumerate(L) if kozos.doboz_fej(l)]
        cserek = []
        for (kod, par, fej, sorok), h in zip(kozos.dobozok(txt), H):
            if kod not in JOG or par not in paragrafus_sorok(kod) or not sorok or re.search(r'\)\s*pont$', fej):
                continue      # a pontot idéző doboz („Szabs. tv. 27. § (2) bek. a) pont”) szándékosan részleges
            cs = csoportok(paragrafus_sorok(kod)[par])
            if not cs:
                continue
            kell = set()
            for s in sorok:
                mc = re.match(r'^(\[[^\]]*\])\s+(\S.*)$', s)
                if mc:
                    kell.add('cim'); kell.add(kulcs_keres(mc.group(2), cs))
                else:
                    kell.add(kulcs_keres(s, cs))
            egyutt = kozos.norm(re.sub(r'\((?:\.\.\.)\)|\[\.\.\.\]|…', ' ', ' '.join(sorok)))
            for k, ls in cs:
                probe = kozos.norm(re.sub(r'^\(\d+[a-z]?\)\s*|^\[[^\]]*\]\s*', '', ls[0]))[:50]
                if len(probe) >= 30 and probe in egyutt:
                    kell.add(k)
            if not any(x.startswith('[') for x in sorok):
                kell.discard('cim')
            sor_k = [k for k, _ in cs]
            hely = [i for i, k in enumerate(sor_k) if k in kell and k != 'cim']
            if hely:
                kell |= {k for i, k in enumerate(sor_k) if k.startswith('hk') and hely[0] < i < hely[-1]}
            uj = [l for k, ls in cs if k in kell for l in ls]
            uj2 = []
            for i, x in enumerate(uj):
                if i and x.startswith('[') and uj2 and not uj2[-1].startswith('['):
                    uj2[-1] += ' ' + x  # a felsorolást lezáró, szögletes zárójellel kezdődő szöveg a pont sorában marad
                else:
                    uj2.append(x)
            uj = uj2
            hk = r'^\(?\d*[a-z]?\)?\s*Hatályon kívül helyezve\.?$|^[a-z]{1,2}\)\s*Hatályon kívül helyezve\.?$'
            tiszta = [s for s in sorok if not re.match(hk, s) and not re.fullmatch(CSUPASZ, s)]
            ujt = [s for s in uj if not re.fullmatch(CSUPASZ, s)]
            if [kozos.norm(x) for x in ujt] == [kozos.norm(x) for x in tiszta] or ('--sor' not in sys.argv and kozos.norm(' '.join(ujt)) == kozos.norm(' '.join(tiszta))):
                continue
            if '--diff' in sys.argv:
                a = kozos.norm(' '.join(tiszta)).split(); b = kozos.norm(' '.join(ujt)).split()
                for o, i1, i2, j1, j2 in difflib.SequenceMatcher(None, a, b, autojunk=False).get_opcodes():
                    if o != 'equal':
                        print('      ', o, '| tétel:', ' '.join(a[i1:i2])[:150], '| korpusz:', ' '.join(b[j1:j2])[:150])
            # a doboz sorai a fájlban: a fejléc után az első és az utolsó dobozsor
            idx, j = [], h + 1
            for s in sorok:
                while j < len(L) and L[j].strip() != s and not L[j].strip().endswith(s):
                    j += 1
                if j >= len(L):
                    break
                idx.append(j); j += 1
            if len(idx) != len(sorok):
                print(f'  !! {n}. {fej}: a dobozsorok nem találhatók'); continue
            elotag = re.match(r'^(?:\d+(?::\d+)?(?:/[A-Z])?\. §|(?:\d+|[IVXLC]+)\. [Cc]ikk|[A-Z]\) [Cc]ikk)\s*', L[idx[0]].strip())
            uj_sorok = list(uj)
            if elotag:
                uj_sorok[0] = elotag.group(0) + uj_sorok[0]
            cserek.append((idx[0], idx[-1], uj_sorok))
            regi = sum(len(s) for s in sorok); ujh = sum(len(s) for s in uj)
            print(f'{n:>3}. {fej:<26} {sorted(kell, key=str)} {regi} -> {ujh} kar.')
            osszes += 1
        if IR and cserek:
            for a, b, uj in sorted(cserek, reverse=True):
                blokk = []
                for k, s in enumerate(uj):
                    if k:
                        blokk.append('')
                    blokk.append(s)
                L[a:b + 1] = blokk
            open(ut, 'w', encoding='utf-8').write('\n'.join(L))
    print('módosítandó doboz:', osszes)


if __name__ == "__main__":
    main()
