#!/usr/bin/env python3
"""Átfogó termék-lefedettségi audit (Attila döntése, 2026-11-13):   python3 tools/lefedettseg_audit.py

Ha minden termék elkészült, ez a kapu igazolja, hogy minden tételnél megvan minden termék, ahol az indokolt.
Minden (tétel, termék) párra pontosan egy eredmény születik:
  VAN          – a termék elkészült;
  NEM KELL     – a hiány gépileg igazolt oka (pl. nincs legalább háromelemű pontozott felsorolás a dobozokban);
  INDOKOLT     – a hiány okát kézzel rögzítették: termekek/lefedettseg_indok.json;
  NYITOTT      – a termék hiányzik, és nincs gépi vagy rögzített ok → a kapu bukik.

Termékek és szabályok:
  paragrafus  – minden tételnél kötelező (a tételben van jogszabálydoboz).
  vazlat      – minden tételnél kötelező.
  felsorolas  – kötelező, ha a tétel dobozaiban van legalább háromelemű a), b), c)… felsorolás; a hiányt
                csak a felsorolás-index `kihagyva` listája mentheti (ott indokkal).
  matrix      – az „Elhatárolások” szakasz (termekek/elhatarolasok/NN.json) minden bekezdésére: van-e mátrix,
                amelynek valamely forrásmondata a bekezdésből való; ha nincs, rögzített ok kell. Ha a tétel szövegében
                más elhatároló jel van (ELHATÁROL… címsor, „Elhatárolás …” kezdetű bekezdés), és mátrix nincs, szintén.
  fa, szamolo – gépi jel nem állapítható meg megbízhatóan, ezért minden hiányhoz rögzített ok kell.

Az indokfájl: {"sema": 1, "indokok": [{"tetel": 1, "termek": "fa", "kod": "...", "indok": "..."}]}; a matrix-indok
elhatárolás-bekezdésre is szólhat ("elhatarolas": "<a bekezdés címe>"). Megengedett kódok: KODOK.
Kimenet: jelentesek/lefedettseg_audit.md és .json. Kilépési kód: 0, ha nincs NYITOTT tétel; különben 1.
"""
import glob, json, os, re, sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import kozos

T = os.path.join(kozos.GYOKER, 'termekek')
KODOK = {
    'nincs-dontesi-helyzet': 'a tételben nincs olyan, feltételekből levezethető jogkövetkezmény, amelyhez kérdéssor kell',
    'nincs-szamithato-ertek': 'a tételben nincs számítható érték (hányad, határidő vége, összeg)',
    'korpuszbol-nem-vezetheto-le': 'a döntés a korpuszból nem vezethető le egyértelműen (vitatott értelmezés, bírói gyakorlat)',
    'nincs-kozos-szempont': 'az elhatárolás nem ugyanazon szempont szerint állítja szembe a fogalmakat',
    'mas-termekben': 'ugyanez a tartalom egy másik tétel termékében már szerepel (az indokban megnevezve)',
    'tiltott-szo': 'a termék felhasználói szövege tiltott karaktersort tartalmazna',
}
TERMEKEK = ['paragrafus', 'felsorolas', 'vazlat', 'fa', 'szamolo', 'matrix']
PONT = re.compile(r'^([a-z])\)\s')


def be(*r):
    return json.load(open(os.path.join(T, *r), encoding='utf-8'))


def felsorolas_jeloltek(elemek):
    """Legalább háromelemű a), b), c)… sorozatok száma a tétel dobozaiban."""
    db = 0
    for e in elemek:
        sor = [PONT.match(s.strip()).group(1) for s in e['sorok'] if PONT.match(s.strip())]
        hossz = 0; vart = 'a'
        for j in sor + ['#']:
            if j == vart:
                hossz += 1; vart = chr(ord(vart) + 1)
            else:
                if hossz >= 3:
                    db += 1
                hossz = 1 if j == 'a' else 0; vart = 'b' if j == 'a' else 'a'
    return db


def elhatarolo_jel(n):
    L = [l.strip() for l in kozos.tetel_szoveg(n).split('\n') if l.strip()]
    return [l[:90] for l in L if (l.upper() == l and 'ELHATÁROL' in l and len(l) < 120) or l.startswith('Elhatárolás')]


def main():
    ts = kozos.tetelsor()['tetelek']
    ind = {}
    p = os.path.join(T, 'lefedettseg_indok.json')
    hibak = []
    if os.path.exists(p):
        for x in json.load(open(p, encoding='utf-8'))['indokok']:
            if x['kod'] not in KODOK:
                hibak.append(f"ismeretlen indokkód: {x}")
            if not x.get('indok', '').strip():
                hibak.append(f"üres indok: {x}")
            ind[(x['tetel'], x['termek'], x.get('elhatarolas'))] = x
    fa_t = {}; sz_t = {}
    for f in glob.glob(os.path.join(T, 'dontesi_fa', '*.json')):
        if f.endswith('index.json'):
            continue
        for n in json.load(open(f, encoding='utf-8'))['tetel']:
            fa_t.setdefault(n, []).append(os.path.basename(f)[:-5])
    for f in glob.glob(os.path.join(T, 'szamolo', '*.json')):
        if f.endswith('index.json'):
            continue
        d = json.load(open(f, encoding='utf-8'))
        for n in d.get('tetel', d.get('tetelek', [])):
            sz_t.setdefault(n, []).append(os.path.basename(f)[:-5])
    mx = {}
    for f in glob.glob(os.path.join(T, 'fogalommatrix', '*.json')):
        if f.endswith('index.json'):
            continue
        d = json.load(open(f, encoding='utf-8'))
        for n in d['tetelek']:
            mx.setdefault(n, []).append(d)
    kihagyott = {}
    for k in be('felsorolas', 'index.json').get('kihagyva', []):
        kihagyott.setdefault(k['tetel'], []).append(k)

    sorok = []; nyitott = 0; osszes = {k: {'VAN': 0, 'NEM KELL': 0, 'INDOKOLT': 0, 'NYITOTT': 0} for k in TERMEKEK}

    def ir(n, termek, allapot, mi):
        nonlocal nyitott
        osszes[termek][allapot] += 1
        if allapot == 'NYITOTT':
            nyitott += 1
        sorok.append({'tetel': n, 'termek': termek, 'allapot': allapot, 'mi': mi})

    for t in ts:
        n = t['sorszam']
        pj = be('paragrafus_jegyzek', f'{n:02d}.json')['elemek']
        ir(n, 'paragrafus', 'VAN' if pj else 'NYITOTT', f'{len(pj)} doboz' if pj else 'a tételben nincs jogszabálydoboz')
        hv = os.path.join(T, 'hangos_vazlat', f'{n:02d}.json')
        ir(n, 'vazlat', 'VAN' if os.path.exists(hv) else 'NYITOTT', '' if os.path.exists(hv) else 'nincs hangos vázlat')
        fp = os.path.join(T, 'felsorolas', f'{n:02d}.json')
        van = len(be('felsorolas', f'{n:02d}.json')['listak']) if os.path.exists(fp) else 0
        jelolt = felsorolas_jeloltek(pj)
        if van:
            ir(n, 'felsorolas', 'VAN', f'{van} lista')
        elif not jelolt:
            ir(n, 'felsorolas', 'NEM KELL', 'a dobozokban nincs legalább háromelemű pontozott felsorolás')
        elif n in kihagyott and len(kihagyott[n]) >= jelolt:
            ir(n, 'felsorolas', 'INDOKOLT', '; '.join(k['ok'] for k in kihagyott[n]))
        else:
            ir(n, 'felsorolas', 'NYITOTT', f'{jelolt} felsorolás van a dobozokban, tréner nincs')
        for termek, tar in (('fa', fa_t), ('szamolo', sz_t)):
            if n in tar:
                ir(n, termek, 'VAN', ', '.join(sorted(tar[n])))
            elif (n, termek, None) in ind:
                x = ind[(n, termek, None)]; ir(n, termek, 'INDOKOLT', f"{x['kod']}: {x['indok']}")
            else:
                ir(n, termek, 'NYITOTT', 'nincs termék és nincs rögzített ok')
        # mátrix: elhatárolás-bekezdésenként
        ep = os.path.join(T, 'elhatarolasok', f'{n:02d}.json')
        forras = {f2['szoveg'] for d in mx.get(n, []) for c in d['cellak'] for f2 in c['forrasok']} | {d.get('osszegzes', '') for d in mx.get(n, [])}
        resz = []
        if os.path.exists(ep):
            for e in be('elhatarolasok', f'{n:02d}.json')['elhatarolasok']:
                if any(m in forras for m in e['mondatok']) or any(e['cim'] in s for s in forras):
                    continue
                k = (n, 'matrix', e['cim'])
                if k in ind:
                    continue
                resz.append(e['cim'])
        jel = elhatarolo_jel(n)
        if resz:
            ir(n, 'matrix', 'NYITOTT', 'mátrix vagy rögzített ok nélküli elhatárolás: ' + ' | '.join(resz))
        elif mx.get(n):
            ir(n, 'matrix', 'VAN', f'{len(mx[n])} mátrix')
        elif (n, 'matrix', None) in ind:
            x = ind[(n, 'matrix', None)]; ir(n, 'matrix', 'INDOKOLT', f"{x['kod']}: {x['indok']}")
        elif jel:
            ir(n, 'matrix', 'NYITOTT', 'elhatároló szakasz van, mátrix nincs: ' + ' | '.join(jel))
        else:
            ir(n, 'matrix', 'NEM KELL', 'a tételben nincs elhatároló szakasz')

    out = os.path.join(kozos.GYOKER, 'jelentesek', 'lefedettseg_audit')
    json.dump({'sema': 1, 'osszesites': osszes, 'nyitott': nyitott, 'hibak': hibak, 'sorok': sorok},
              open(out + '.json', 'w', encoding='utf-8'), ensure_ascii=False, indent=1)
    md = ['# Termék-lefedettségi audit', '', 'Gyártja: `python3 tools/lefedettseg_audit.py`. Szabály: `01_dontesek.md`, „Átfogó lefedettségi audit” (2026-11-13).', '',
          '| Termék | VAN | NEM KELL | INDOKOLT | NYITOTT |', '|---|---|---|---|---|']
    md += [f"| {k} | {v['VAN']} | {v['NEM KELL']} | {v['INDOKOLT']} | {v['NYITOTT']} |" for k, v in osszes.items()]
    md += ['', f'**Nyitott tétel–termék pár: {nyitott}**', '']
    if hibak:
        md += ['## Hibás indokok', ''] + [f'- {h}' for h in hibak] + ['']
    md += ['## Nyitott párok', '', '| Tétel | Termék | Mi hiányzik |', '|---|---|---|']
    md += [f"| {s['tetel']}. | {s['termek']} | {s['mi']} |" for s in sorok if s['allapot'] == 'NYITOTT']
    open(out + '.md', 'w', encoding='utf-8').write('\n'.join(md) + '\n')
    for k, v in osszes.items():
        print(f"{k:11s} VAN {v['VAN']:3d}  NEM KELL {v['NEM KELL']:3d}  INDOKOLT {v['INDOKOLT']:3d}  NYITOTT {v['NYITOTT']:3d}")
    print(f'nyitott: {nyitott}; hibás indok: {len(hibak)}; jelentés: jelentesek/lefedettseg_audit.md')
    sys.exit(1 if nyitott or hibak else 0)


if __name__ == '__main__':
    main()
