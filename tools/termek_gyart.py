#!/usr/bin/env python3
"""Gépi termékek gyártása a tételek jogszabálydobozaiból: §-jegyzék és felsorolás-tréner.

Használat (a tároló gyökeréből):  python3 tools/termek_gyart.py
Kimenet:
  termekek/paragrafus_jegyzek/NN.json, termekek/paragrafus_jegyzek/index.json
  termekek/felsorolas/NN.json,        termekek/felsorolas/index.json
Minden szöveg szó szerint a tétel jogszabálydobozából származik; a dobozokat a tools/ellenorzes.py
veti össze a korpusszal, a termékfájlokat a tools/termek_ellenor.py.
"""
import json, os, re, sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import kozos

KI = os.path.join(kozos.GYOKER, 'termekek')
SEMA = 1
# Felsorolások, amelyek nem kerülnek a trénerbe (azonosító -> ok). A gyártó ezen felül kihagyja
# azt a listát is, amelynek záró szövege nem mondatvéggel zárul (tördelt, csonka pont).
KIZARVA = {
    'PtkMod2016-24': 'hatályon kívül helyezett rendelkezések felsorolása, nem a tételek anyaga',
}


def cimek(kod, fajl):
    """{§: szögletes zárójeles cím} a korpusz-fájlból (ahol van)."""
    ptk = kozos.konyves(kod) or kod in kozos.BEAGYAZOTT
    rx = re.compile((r'^„?(\d+:\d+(?:/[A-Z])?)' if ptk else r'^(\d+(?:/[A-Z])?)') + r'\. §\s*(?:\[(.*?)\])?')
    d, cur = {}, None
    sorok = kozos.beagyazott_sorok(fajl, *kozos.BEAGYAZOTT[kod]) if kod in kozos.BEAGYAZOTT else open(fajl, encoding='utf-8').read().split('\n')
    for l in sorok:
        s = l.strip(); m = rx.match(s)
        if m:
            cur = m.group(1)
            if m.group(2) and cur not in d:
                d[cur] = kozos.nfc(m.group(2)).strip()
        elif cur and cur not in d and s.startswith('[') and s.endswith(']'):
            d[cur] = kozos.nfc(s[1:-1]).strip()
    return d


def szakaszok(txt):
    """Sorindex -> a legközelebbi megelőző római számos főcím és arab számos alcím."""
    fo = al = ''; out = []
    for l in txt.split('\n'):
        s = l.strip()
        if re.match(r'^[IVX]+\. [A-ZÁÉÍÓÖŐÚÜŰ]', s) and s.upper() == s:
            fo, al = s, ''
        elif re.match(r'^\d+\. [A-ZÁÉÍÓÖŐÚÜŰ]', s) and s.upper() == s:
            al = s
        out.append((fo, al))
    return out


def doboz_helyek(txt):
    """A dobozok fejlécének sorindexe, a kozos.dobozok sorrendjében."""
    L = [l.strip() for l in txt.split('\n')]
    return [i for i, l in enumerate(L) if kozos.doboz_fej(l)]


def tiszta(s):
    """A felsoroláselem a záró írásjel és kötőszó nélkül."""
    s = re.sub(r'\s*\*\s*$', '', s.strip())
    s = re.sub(r'[;,]?\s*(vagy|és|továbbá|illetve|valamint)$', '', s)
    return s.rstrip(';,.').strip()


def kapcsolo(elemek):
    if len(elemek) < 2:
        return ''
    m = re.search(r'[;,]?\s*(vagy|és|továbbá|illetve|valamint)$', elemek[-2].strip())
    return m.group(1) if m else ''


def felsorolasok(sorok, kovetkezo_sor):
    """A doboz soraiból a felsorolások: [(bekezdés, bevezető, [elem], záró)].
    Elem: {'jel','szoveg','alpontok':[{'jel','szoveg'}]}. Csak a legalább háromelemű, hézagtalan a), b), c)… sor számít."""
    out = []; i = 0
    while i < len(sorok):
        s = sorok[i]
        if re.match(r'^[a-z]{1,2}\)\s', s) or s.startswith('['):
            i += 1; continue
        j = i + 1; elemek = []
        while j < len(sorok):
            m = re.match(r'^([a-z]{1,2})\)\s+(.*)$', sorok[j])
            if not m:
                break
            jel, sz = m.group(1), m.group(2)
            if len(jel) == 1 and ord(jel) == ord('a') + len(elemek):
                elemek.append({'jel': jel, 'szoveg': sz, 'alpontok': []})
            elif len(jel) == 2 and elemek and jel[0] == elemek[-1]['jel']:
                elemek[-1]['alpontok'].append({'jel': jel, 'szoveg': sz})
            else:
                break
            j += 1
        if len(elemek) >= 3:
            bek = re.match(r'^\((\d+[a-z]?)\)\s*(.*)$', s)
            zaro = ''
            if j < len(sorok) and sorok[j][0].islower() and not re.match(r'^[a-z]{1,2}\)', sorok[j]):
                zaro = sorok[j]; j += 1
            elif j >= len(sorok) and kovetkezo_sor and kovetkezo_sor[0].islower() and not re.match(r'^[a-z]{1,2}\)', kovetkezo_sor):
                zaro = kovetkezo_sor
            out.append((bek.group(1) if bek else '', bek.group(2) if bek else s, elemek, zaro))
            i = j
        else:
            i += 1
    return out


def main():
    F = kozos.forrasok(); T = kozos.tetelsor()
    CIM = {}
    for kod, f in F.items():
        if f.get('korpusz'):
            p = kozos.korpusz_fajl(f['korpusz'][0])
            if p and f['tipus'] in ('törvény', 'rendelet'):
                CIM[kod] = cimek(kod, p)
    for d in ('paragrafus_jegyzek', 'felsorolas'):
        os.makedirs(os.path.join(KI, d), exist_ok=True)
    pj_index = {}; fs_index = {}; ossz_doboz = ossz_lista = 0; kihagyva = []
    for t in T['tetelek']:
        n = t['sorszam']; txt = kozos.tetel_szoveg(n); L = [l.strip() for l in txt.split('\n')]
        D = kozos.dobozok(txt); H = doboz_helyek(txt); SZ = szakaszok(txt)
        assert len(D) == len(H), (n, len(D), len(H))
        pj = []; fs = []
        for k, ((kod, par, fejlec, sorok), h) in enumerate(zip(D, H), 1):
            if not sorok:
                continue
            fo, al = SZ[h]
            cim = CIM.get(kod, {}).get(par, '')
            pj.append({'sorrend': k, 'forras': kod, 'forrasNev': F[kod]['nev'] if kod in F else kod, 'par': par,
                       'fejlec': fejlec, 'cim': cim, 'focim': fo, 'alcim': al, 'sorok': sorok})
            pj_index.setdefault(f'{kod} {par}', {'forras': kod, 'par': par, 'cim': cim, 'tetelek': []})
            if n not in pj_index[f'{kod} {par}']['tetelek']:
                pj_index[f'{kod} {par}']['tetelek'].append(n)
            # a doboz utáni első nem üres sor (a felsorolás záró szövegéhez)
            x = h + 1; latott = 0; kov = ''
            while x < len(L):
                if L[x]:
                    if latott < len(sorok):
                        latott += 1
                    else:
                        kov = L[x]; break
                x += 1
            for bek, bev, elemek, zaro in felsorolasok(sorok, kov):
                az = f'{kod}-{par}' + (f'-{bek}' if bek else '')
                e = {'id': az, 'forras': kod, 'par': par, 'bek': bek, 'fejlec': fejlec, 'cim': cim, 'focim': fo, 'alcim': al,
                     'bevezeto': bev, 'elemek': [dict(x, tiszta=tiszta(x['szoveg'])) for x in elemek],
                     'kapcsolo': kapcsolo([x['szoveg'] for x in elemek]), 'peldalozo': bool(re.search(r'különösen|így például', bev)),
                     'zaro': zaro}
                if any(y['id'] == az for y in fs):
                    continue
                if az in KIZARVA or (zaro and not zaro.rstrip().endswith('.')):
                    kihagyva.append({'id': az, 'tetel': n, 'ok': KIZARVA.get(az, 'a pont több sorra tördelt, a lista gépileg nem egyértelmű')})
                    continue
                fs.append(e)
                fs_index.setdefault(az, {'forras': kod, 'par': par, 'bek': bek, 'cim': cim, 'elemszam': len(elemek), 'tetelek': []})
                fs_index[az]['tetelek'].append(n)
        ossz_doboz += len(pj); ossz_lista += len(fs)
        fej = {'sema': SEMA, 'tetel': n, 'cim': t['cim'], 'csoport': t.get('csoport', '')}
        json.dump(dict(fej, termek='paragrafus_jegyzek', elemek=pj),
                  open(os.path.join(KI, 'paragrafus_jegyzek', f'{n:02d}.json'), 'w', encoding='utf-8'), ensure_ascii=False, indent=1)
        p = os.path.join(KI, 'felsorolas', f'{n:02d}.json')
        if fs:
            json.dump(dict(fej, termek='felsorolas', listak=fs), open(p, 'w', encoding='utf-8'), ensure_ascii=False, indent=1)
        elif os.path.exists(p):
            os.remove(p)
    json.dump({'sema': SEMA, 'termek': 'paragrafus_jegyzek', 'paragrafusok': sorted(pj_index.values(), key=lambda x: (x['forras'], [int(z) for z in re.findall(r'\d+', x['par'])]))},
              open(os.path.join(KI, 'paragrafus_jegyzek', 'index.json'), 'w', encoding='utf-8'), ensure_ascii=False, indent=1)
    json.dump({'sema': SEMA, 'termek': 'felsorolas', 'listak': fs_index, 'kihagyva': kihagyva},
              open(os.path.join(KI, 'felsorolas', 'index.json'), 'w', encoding='utf-8'), ensure_ascii=False, indent=1)
    print(f'§-jegyzék: {ossz_doboz} doboz, {len(pj_index)} különböző §; felsorolás: {ossz_lista} tételenkénti előfordulás, {len(fs_index)} különböző lista, '
          f'{len([1 for t in T["tetelek"] if os.path.exists(os.path.join(KI, "felsorolas", "%02d.json" % t["sorszam"]))])} tételben')


if __name__ == '__main__':
    main()
