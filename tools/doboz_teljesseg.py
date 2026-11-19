#!/usr/bin/env python3
"""A jogszabálydobozok teljessége: a dobozban idézett bekezdés (vagy bekezdés nélküli §) szövegéből
maradt-e ki rész a korpuszhoz képest (csonka felsorolás, levágott mondat).
Használat: python3 tools/doboz_teljesseg.py [tétel]
A szerkezeti címek (CÍM, Fejezet, alcím) és a hatályon kívül helyezett részek nem számítanak hiánynak. A § (cikk) sorait
a korpuszfájl sortöréseiből veszi (kozos.jogszabaly_sorok); a § végén álló, záró írásjel nélküli címsorok (a következő
szerkezeti egység címe) nem a § részei; a bekezdéshatár a „(n)”-nel kezdődő sor (a puszta „(3)” is). A cikkre tagolt
forrás dobozát is vizsgálja (kozos.FEJLEC, a forrás egysége a beállításból).
"""
import os, re, sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import kozos


def bekezdesek(szov):
    """Visszafelé kompatibilis: a normalizált §-szöveg bekezdései (csak ott, ahol a korpusz sorai nem érhetők el)."""
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


def cimsor(l):
    """Szerkezeti címsor-e a § végén álló sor (a következő szerkezeti egység címe): záró írásjel nélküli sor – nagybetűs
    „FEJEZET”, számozott („157. Elektronikus kapcsolattartás”, „7/A. …”) vagy csillagos alcím, „202-204. §” maradék,
    a hatályon kívül helyezett puszta „(3)”, „(3)-(4) Mérsékelt illeték”."""
    t = kozos.norm(l).strip()
    if re.fullmatch(r'\d+(?::\d+)?(?:/[A-Z])?\.', t):
        return True      # a következő alcím puszta sorszáma („133/C. *”)
    return bool(t) and not re.search(r'[.;:!?”"…]$|\.\)$', t)


def bekezdesek_sorokbol(sorok):
    """A § bekezdései a korpuszfájl sortöréseiből: {'(n)' kulcs nélkül: normalizált szöveg}. A bekezdés határa a „(n)”-nel
    kezdődő sor (a hatályon kívül helyezett puszta „(3)” is határ); a § végéről a záró írásjel nélküli címsorok lekerülnek;
    az első sor szögletes zárójeles címe („[A bíróság]”) nem bekezdésszöveg."""
    sorok = [l for l in sorok if l.strip()]
    while sorok and cimsor(sorok[-1]):
        sorok.pop()
    # a § elején álló cím („[A bíróság]”); a cikkfej utáni címet („3. cikk - Általános joghatóság”) a
    # kozos.jogszabaly_sorok már elhagyta (a cikk további sorai tördelt normaszöveg lehetnek: azokat nem vágjuk)
    if len(sorok) > 1 and re.fullmatch(r'\[[^\]]*\]', sorok[0].strip()):
        sorok = sorok[1:]
    d, cur, elozo = {}, '', ''
    for l in sorok:
        m = re.match(r'^\((\d+[a-z]?)\)\s*(.*)$', l.strip())
        if m and re.match(r'^[a-záéíóöőúüű]', m.group(2)) and elozo and not re.search(r'[.;:!?…,\]]["”’)]*$', elozo):
            m = None             # tördelt sor: „… 20. cikke” / „(2) bekezdésében …” – nem új bekezdés
        elozo = l.strip() or elozo
        if m:
            cur = m.group(1)
            while cur in d:
                cur = cur + '#'          # azonos számú második bekezdés: nem írja felül az elsőt
            d[cur] = [m.group(2)]
        else:
            d.setdefault(cur, []).append(l)
    return {k: kozos.norm(re.sub(r'^\[[^\]]*\]\s*', '', ' '.join(v))) for k, v in d.items()}


_SOROK = {}


def korpusz_sorok(kod):
    """{egység: [sorok]} a forrás korpuszfájljából (kozos.jogszabaly_sorok), vagy None (beágyazott kódex, nincs fájl)."""
    if kod not in _SOROK:
        _SOROK[kod] = None
        f = kozos.forrasok().get(kod) or {}
        p = kozos.korpusz_fajl(f['korpusz'][0]) if f.get('korpusz') and kod not in kozos.BEAGYAZOTT else None
        if p:
            _SOROK[kod] = kozos.jogszabaly_sorok(kod, p)[0]
    return _SOROK[kod]


def cim_e(m):
    """Szerkezeti cím vagy zárójeles utalás maradéka-e (nem normaszöveg)."""
    m = re.sub(r'\([^)]*§[^)]*\)', ' ', m)
    m = re.sub(r'\b[IVXLC]+(?:/[A-Z])?\.\s*\*?\s*(CÍM|Fejezet|FEJEZET)\b|\b[A-ZÁÉÍÓÖŐÚÜŰ]+ (RÉSZ|KÖNYV)\b', ' ', m)
    m = re.sub(r'\b\d+(?:/[A-Z])?\. (?=[A-ZÁÉÍÓÖŐÚÜŰ])', ' ', m)
    m = re.sub(r'\b\d+(?:/[A-Z])?(?:\s*[-–]\s*\d+(?:/[A-Z])?)?\.\s*§', ' ', m).strip(' -–*')
    if not m:
        return True
    return not re.search(r'[.;:,]$', m) and not re.search(r'(^| )[a-z]{1,2}\) ', m) and (m.upper() == m or len(m) < 90 and m[0].isupper() and not re.search(r'\b(ha|hogy|kell|lehet|köteles|jogosult|nem)\b', m))


def hianyok(n, J):
    out = []
    txt = kozos.tetel_szoveg(n); L = [l.strip() for l in txt.split('\n')]
    H = [i for i, l in enumerate(L) if kozos.doboz_fej(l)]
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
        if not szov or not sorok or re.search(r'\)\s*pont$', fej) or par == kozos.PREAMBULUM:
            continue          # a pontot idéző doboz („Mt. 294. § (1) bek. i) pont”) szándékosan részleges; a preambulum-
                              # bekezdés határa a kétoszlopos korpuszban nem állapítható meg (az ellenorzes.py betűre veti össze)
        ks = korpusz_sorok(kod)
        B = bekezdesek_sorokbol(ks[par]) if ks and par in ks else bekezdesek(szov)
        cur = None; D = {}
        for i, s in enumerate(sorok):
            if i == 0:
                # „[cím] szöveg” egysoros doboz: a cím után a szöveg számít. Csak a doboz ELSŐ sorában álló szögletes
                # zárójeles rész cím; máshol a „[…]” a normaszöveg része (Kjnp. 27/N. § (2): „[az a)–e) pontban …].”)
                s = re.sub(r'^\[[^\]]*\]\s*', '', s)
            if not s:
                continue
            m = re.match(r'^\((\d+[a-z]?)\)\s*(.*)$', s)
            if m:
                cur = m.group(1)
                while cur in D:
                    cur += '#'           # azonos számú második bekezdés (mint a korpusz oldalán): nem írja felül az elsőt
                D[cur] = [m.group(2)]
            else:
                if cur is None:
                    cur = ''; D[cur] = []
                D[cur].append(s)
        for b, ls in D.items():
            if b not in B:
                continue
            mar = B[b]
            for l in ls + utana:
                # a rövid sor csak pontjellel együtt („b) ipar,”) keresendő: a puszta rövid szó máshol is előfordulhat
                x = kozos.norm(l); p = mar.find(x) if len(x) > 12 or re.match(r'^(?:\(\d+[a-z]?\)|[a-z]{1,2}\)) \S', x) else -1
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
