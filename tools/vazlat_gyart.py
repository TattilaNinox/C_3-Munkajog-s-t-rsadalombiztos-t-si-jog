#!/usr/bin/env python3
"""Hangos vázlat gyártása: a tétel magyarázó szövegének kulcsmondatai, szó szerint, a tétel tagolásában.

    python3 tools/vazlat_gyart.py            # mind a 85 tétel -> termekek/hangos_vazlat/NN.json
    python3 tools/vazlat_gyart.py 23 --lista # egy tétel, a kijelölés kiírásával (K = kulcsmondat)

A gép előjelöl (lásd elojelolt()), a végleges kijelölést tételenként a kézi felülbírálás adja a
termekek/hangos_vazlat/kezi.json fájlban: {"23": {"kesz": true, "be": [mondatkezdetek], "ki": [mondatkezdetek]}}.
A kézi kijelölést a tools/vazlat_kezi.py írja (mondatsorszámokból), és a mondat elejével azonosítja a mondatot,
hogy a tétel későbbi változása ne csúsztassa el; ha egy mondatkezdet már nem található, a gyártó hibával megáll.
"""
import json, os, re, sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import kozos

KI = os.path.join(kozos.GYOKER, 'termekek', 'hangos_vazlat')
SEMA = 1
ROV = r'(?:' + ('|'.join(kozos.beallitas()['mondatRovidites']) or '(?!)') + ')'   # üres lista: semmi sem rövidítés (különben minden szóvég az lenne)
NAGY = 'A-ZÁÉÍÓÖŐÚÜŰ'


def mondatok(bek):
    """A bekezdés mondatai; nem vág rövidítés, sorszám (XX. Fejezet, III/A. Fejezet, 113. számú) után.
    Kivétel (2026-11-18): a jogszabály-rövidítéssel záruló mondat után vág, ha névelővel kezdődő mondat következik
    („A Ptk. és a Csvt. A Ptk. alapelvei …” – az elhatárolás címe külön mondat)."""
    out = []; kezd = 0
    for m in re.finditer(r'(?<=[.!?])\s+(?=[„(]?[' + NAGY + r'])', bek):
        elotte = bek[kezd:m.start()]
        if re.search(r'(?:\b' + ROV + r'|\b(?:[IVXLC]+|\d+)(?:/[A-Z])?|\([^)]*)\.$', elotte) and not re.search(r'\)\.$', elotte):
            # rövidítés, szám vagy lezáratlan zárójel után nem vágunk
            jogszabaly = re.search(r'\b(?:' + ('|'.join(kozos.beallitas()['jogszabalyRovidites']) or '(?!)') + r')\.$', elotte) and re.match(r'(?:A|Az) ', bek[m.end():])
            if not re.search(r'\bstb\.$', elotte) and not jogszabaly:
                continue
        out.append(elotte.strip()); kezd = m.end()
    out.append(bek[kezd:].strip())
    return [s for s in out if s]


def szerkezet(n):
    """A tétel elemei sorrendben: ('F', főcím) | ('A', alcím) | ('D', dobozfejléc) | ('M', sorszám, mondat)."""
    txt = kozos.tetel_szoveg(n); L = [l.strip() for l in txt.split('\n')]
    doboz = set(); fej = {}
    H = [i for i, l in enumerate(L) if kozos.doboz_fej(l)]
    for (kod, par, f, sorok), h in zip(kozos.dobozok(txt), H):
        doboz.add(h); fej[h] = f; x = h + 1; k = 0
        while x < len(L) and k < len(sorok):
            if L[x]:
                doboz.add(x); k += 1
            x += 1
        # a felsorolás záró sora (kisbetűvel kezdődő folytatás) is a normaszöveg része
        while x < len(L) and not L[x]:
            x += 1
        if x < len(L) and sorok and re.match(r'^[a-z]{1,2}\) ', sorok[-1]) and L[x] and L[x][0].islower() and not re.match(r'^[a-z]{1,2}\) ', L[x]):
            doboz.add(x)
    out = []; i = 0; elso = True
    for x, l in enumerate(L):
        if not l:
            continue
        if elso:
            elso = False; continue          # a tétel címe
        if x in fej:
            out.append(('D', fej[x])); continue
        if x in doboz:
            continue
        if re.match(r'^[IVX]+\. [' + NAGY + ']', l) and l.upper() == l or l in ('ÖSSZEFOGLALÁS', 'ÖSSZEGZÉS', 'ELHATÁROLÁSOK'):
            out.append(('F', l)); continue
        if l.upper() == l and re.search('[' + NAGY + ']{4}', l):
            out.append(('A', l)); continue
        if re.match(r'^[a-z]\) [' + NAGY + ']', l) and not re.search(r'[.;,:]$', l) and len(l) < 120:
            out.append(('A', l)); continue      # „a) Házastárs öröklése …” típusú alcím
        for s in mondatok(re.sub(r'^[-–•]\s+', '', l)):
            i += 1; out.append(('M', i, s))
    return out


# Előjelölés: alapesetben minden magyarázó mondat kulcsmondat, kivéve a töltelékmondatokat (indokolás,
# méltatás, példa, átvezetés) és az összefoglalás mondatait. A végleges kijelölést tételenként a kezi.json adja.
ELEJE = re.compile(r'^(Ez a |Ez az |Ez |Ezzel (?!szemben)|Ezáltal |Ezen |E rendelkezés|E szabály|E norma|E jogintézmény|E szakasz|Ennek |Ilyen |Mivel |A jogalkotó |A törvényalkotó |A szabályozás |Mindkét jogintézmény|Mindezek|Összefoglal|Fontos hangsúlyozni|Kiemelendő|Megjegyzendő|Például|Így például|A cél |A jogszabály |A törvény itt |A jogrend )')
BELUL = re.compile(r'\b(szolgálja|szolgálják|tükrözi|tükrözik|hangsúlyozza|jogpolitikai|megteremt\w*|teremti meg|garantál\w*|megerősítve|ösztönözve|lefedve|elkerülve|védve|biztosítva|megakadályozva|elismerve|ezzel is|kiemelt jelentőség\w*|kiemelkedő jelentőség\w*|vívmány\w*|koherens|kifinomult|rendszertani szempontból|dogmatikai alapot|szervesen|ratio legis|például)\b')


def elojelolt(s, osszefoglalo):
    if osszefoglalo:
        return False
    return not (ELEJE.search(s) or BELUL.search(s))


def vazlat(n, kezi):
    E = szerkezet(n)
    M = [(e[1], e[2]) for e in E if e[0] == 'M']

    def sorszamok(lista):
        out = set()
        for elo in lista:
            t = [i for i, s in M if s.startswith(elo)]
            assert len(t) == 1, f'{n}. tétel: a kézi kijelölés mondata {len(t)} helyen található (a tétel szövege változott?): {elo!r}'
            out.add(t[0])
        return out
    be = sorszamok(kezi.get('be', [])); ki = sorszamok(kezi.get('ki', []))
    fopontok = []; fo = al = None; elso = False; ossz = 0; jelolt = []
    for e in E:
        if e[0] == 'F':
            fo = {'cim': e[1], 'alpontok': []}; fopontok.append(fo); al = None; elso = True
        elif e[0] == 'A':
            if fo is None:
                fo = {'cim': '', 'alpontok': []}; fopontok.append(fo)
            al = {'cim': e[1], 'par': [], 'mondatok': []}; fo['alpontok'].append(al); elso = True
        else:
            if fo is None:
                fo = {'cim': '', 'alpontok': []}; fopontok.append(fo)
            if al is None:
                al = {'cim': '', 'par': [], 'mondatok': []}; fo['alpontok'].append(al)
            if e[0] == 'D':
                if e[1] not in al['par']:
                    al['par'].append(e[1])
            else:
                _, i, s = e; ossz += 1
                p = elojelolt(s, fo['cim'].endswith(('ÖSSZEFOGLALÁS', 'ÖSSZEGZÉS')))
                k = (p or i in be) and i not in ki
                jelolt.append((i, k, int(p), s))
                if k:
                    al['mondatok'].append({'sorszam': i, 'szoveg': s})
    for f in fopontok:
        f['alpontok'] = [a for a in f['alpontok'] if a['mondatok'] or a['par']]
    fopontok = [f for f in fopontok if f['alpontok']]
    return fopontok, jelolt, ossz


def main():
    lista = '--lista' in sys.argv; args = [a for a in sys.argv[1:] if not a.startswith('--')]
    os.makedirs(KI, exist_ok=True)
    kp = os.path.join(KI, 'kezi.json')
    KEZI = json.load(open(kp, encoding='utf-8')) if os.path.exists(kp) else {}
    T = {t['sorszam']: t for t in kozos.tetelsor()['tetelek']}
    stat = []
    vf = os.path.join(os.path.dirname(KI), '_gyartasra_var.json')
    var = set(int(x) for x in json.load(open(vf, encoding='utf-8')).get('tetelek', [])) if os.path.exists(vf) else set()
    for n in ([int(args[0])] if args else sorted(T)):
        if not args and n in var:        # gyártásra váró tétel: a kézi kijelölése elavult lehet, a teljes futás kihagyja
            print(f'{n}. tétel: gyártásra vár, kihagyva'); continue
        fop, jel, ossz = vazlat(n, KEZI.get(str(n), {}))
        kul = [j for j in jel if j[1]]
        if lista:
            for i, k, p, s in jel:
                print(f'{"K" if k else "-"} {i:>3} {s[:int(next((a.split("=")[1] for a in sys.argv if a.startswith("--hossz=")), 200))]}')
        txt = kozos.tetel_szoveg(n)
        assert all(s in txt for _, _, _, s in kul), f'{n}: nem szó szerinti mondat'
        kar = sum(len(j[3]) for j in kul); osszkar = sum(len(j[3]) for j in jel)
        stat.append((n, len(kul), ossz, kar, osszkar, bool(KEZI.get(str(n), {}).get('kesz'))))
        json.dump({'sema': SEMA, 'termek': 'hangos_vazlat', 'tetel': n, 'cim': T[n]['cim'], 'csoport': T[n].get('csoport', ''),
                   'veglegesitve': bool(KEZI.get(str(n), {}).get('kesz')), 'mondatokSzama': len(kul), 'karakter': kar, 'fopontok': fop},
                  open(os.path.join(KI, f'{n:02d}.json'), 'w', encoding='utf-8'), ensure_ascii=False, indent=1)
    a = sum(s[1] for s in stat); b = sum(s[2] for s in stat); c = sum(s[3] for s in stat); d = sum(s[4] for s in stat)
    print(f'kézzel véglegesítve: {sum(1 for x in stat if x[5])} tétel')
    if not b:      # minden tétel gyártásra vár (új tételsor megnyitása): nincs mit összesíteni
        print('0 tétel: nincs gyártott vázlat (minden tétel gyártásra vár, vagy nincs magyarázó mondat)'); return
    print(f'{len(stat)} tétel: {a} kulcsmondat a {b} magyarázó mondatból ({100*a//b}%), {c} karakter a {d}-ből ({100*c//d}%)')
    if len(stat) > 1:
        print('legkisebb arány:', sorted((100 * s[1] // s[2], s[0]) for s in stat)[:5], 'legnagyobb:', sorted((100 * s[1] // s[2], s[0]) for s in stat)[-5:])


if __name__ == '__main__':
    main()
