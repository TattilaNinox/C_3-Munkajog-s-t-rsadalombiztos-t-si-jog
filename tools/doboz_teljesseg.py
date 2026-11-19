#!/usr/bin/env python3
"""A jogszabálydobozok teljessége: a dobozban idézett bekezdés (vagy bekezdés nélküli §) szövegéből
maradt-e ki rész a korpuszhoz képest (csonka felsorolás, levágott mondat).
Használat: python3 tools/doboz_teljesseg.py [tétel]
A szerkezeti címek (CÍM, Fejezet, alcím) és a hatályon kívül helyezett részek nem számítanak hiánynak.
"""
import os, re, sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import kozos


def bekezdesek(szov):
    s = re.sub(r'^\[[^\]]*\]\s*', '', szov)
    parts = re.split(r'(?:^|(?<=[.;:\]] ))\((\d+[a-z]?)\) ', s)
    if len(parts) == 1:
        return {'': s.strip()}
    d = {}
    if parts[0].strip():
        d[''] = parts[0].strip()
    for i in range(1, len(parts), 2):
        d.setdefault(parts[i], parts[i + 1].strip())
    return d


def cim_e(m):
    """Szerkezeti cím vagy zárójeles utalás maradéka-e (nem normaszöveg)."""
    m = re.sub(r'\([^)]*§[^)]*\)', ' ', m)
    m = re.sub(r'\b[IVXLC]+\. (CÍM|Fejezet)\b|\b[A-ZÁÉÍÓÖŐÚÜŰ]+ (RÉSZ|KÖNYV)\b', ' ', m)
    m = re.sub(r'\b\d+\. (?=[A-ZÁÉÍÓÖŐÚÜŰ])', ' ', m).strip()
    if not m:
        return True
    return not re.search(r'[.;:,]$', m) and not re.search(r'(^| )[a-z]{1,2}\) ', m) and (m.upper() == m or len(m) < 90 and m[0].isupper() and not re.search(r'\b(ha|hogy|kell|lehet|köteles|jogosult|nem)\b', m))


def hianyok(n, J):
    out = []
    txt = kozos.tetel_szoveg(n); L = [l.strip() for l in txt.split('\n')]
    H = [i for i, l in enumerate(L) if kozos.FEJLEC.match(l)]
    for (kod, par, fej, sorok), h in zip(kozos.dobozok(txt), H):
        # a doboz utáni legfeljebb három nem üres sor: ha a korpusz szerint a bekezdés folytatása
        # (a felsorolás záró szövege), a tételben megvan, csak a dobozfelismerő nem sorolja a dobozhoz
        x = h + 1; latott = 0; utana = []
        while x < len(L) and len(utana) < 3:
            if L[x]:
                if latott < len(sorok):
                    latott += 1
                else:
                    utana.append(L[x])
            x += 1
        szov = J.get(kod, ({}, []))[0].get(par)
        if not szov or not sorok:
            continue
        B = bekezdesek(szov); cur = None; D = {}
        for s in sorok:
            if s.startswith('['):
                continue
            m = re.match(r'^\((\d+[a-z]?)\)\s*(.*)$', s)
            if m:
                cur = m.group(1); D[cur] = [m.group(2)]
            else:
                if cur is None:
                    cur = ''; D[cur] = []
                D[cur].append(s)
        for b, ls in D.items():
            if b not in B:
                continue
            mar = B[b]
            for l in ls + utana:
                x = kozos.norm(l); p = mar.find(x) if len(x) > 12 else -1
                if p >= 0:
                    mar = mar[:p] + ' ¦ ' + mar[p + len(x):]
            reszek = [r.strip() for r in mar.split('¦') if len(r.strip()) > 12]
            reszek = [r for r in reszek if 'Hatályon kívül' not in r and not cim_e(r)]
            if reszek:
                out.append((n, fej, b, sum(map(len, reszek)), ' … '.join(r[:70] for r in reszek)))
    return out


def main():
    J = kozos.korpusz_jogszabalyok()
    tetelek = [int(sys.argv[1])] if len(sys.argv) > 1 else range(1, kozos.beallitas().get('tetelDb', len(kozos.tetelsor()['tetelek'])) + 1)
    H = [h for n in tetelek for h in hianyok(n, J)]
    print(f'hiányos bekezdés: {len(H)}')
    for h in H:
        print(f'  {h[0]:>2}. {h[1]} ({h[2]}) [{h[3]} kar.] {h[4]}')
    return 1 if H else 0


if __name__ == '__main__':
    sys.exit(main())
