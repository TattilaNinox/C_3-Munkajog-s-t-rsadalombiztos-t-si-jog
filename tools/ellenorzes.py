#!/usr/bin/env python3
"""A tételsor 0. lépésének ellenőrzései. A tároló gyökeréből:

    python3 tools/ellenorzes.py

Kimenet: korpusz/ellenorzes.json (gépi) és korpusz/ellenorzes.md (emberi összefoglaló).
1. Korpusz-teljesség: minden előírt forrás megvan-e a korpuszban; mely korpusz-fájl nincs forráshoz kötve.
2. Dobozellenőrzés: minden jogszabálydoboz sora betűre (normalizálva) benne van-e a korpusz §-ában.
3. Lefedettség: a tételsor előírt §-tartományainak minden hatályos §-a szerepel-e a tételben
   (dobozban vagy hivatkozásként); a bírósági iránymutatások említése.
A szkript csak olvas; a tárolót nem módosítja, csak a két kimeneti fájlt írja.
"""
import json, os, re, sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import kozos

EMLITES = kozos.beallitas()['emlites']
BIROSAGI_RX = {
    'PK': lambda n: rf'PK\s*{n}\b(?!/)', 'GK': lambda n: rf'GK\s*{n}\b',
}


def biro_minta(kod):
    m = re.match(r'^(PK|GK) (\d+)$', kod)
    if m:
        return BIROSAGI_RX[m.group(1)](m.group(2))
    m = re.match(r'^(\d)/(\d{4})\.', kod)
    if m:
        return rf'{m.group(1)}/{m.group(2)}'
    return {'XXV. PED': r'XXV\.\s*(?:számú\s*)?(?:Polgári Elvi Döntés|PED)', 'IHRA': r'IHRA|antiszemitizmus'}[kod]


def hatalyos(szoveg):
    s = szoveg.strip()
    return bool(s) and not re.match(r'^(?:\(\d+\)\s*)?Hatályon kívül helyezve', s)


def emlitett_paragrafusok(txt, kod):
    """A tételben hivatkozott §-ok az adott jogszabályból (egyedi § és tartomány)."""
    out = set()
    if kozos.konyves(kod):
        for m in re.finditer(r'(?<![\d:/])(\d+:\d+(?:/[A-Z])?)\.?\s?(?:§|[–-]\s*(\d+:\d+(?:/[A-Z])?)\.\s?§)', txt):
            out.add(m.group(1))
            if m.group(2):
                out.add(('tartomany', m.group(1), m.group(2)))
        return out
    rx = EMLITES.get(kod)
    if not rx:
        return out
    for sor in txt.split('\n'):
        if not re.search(rx, sor):
            continue
        for m in re.finditer(r'(?<![\d:/])(\d+(?:/[A-Z])?)\.\s?§(?:\s*[–-]\s*(\d+(?:/[A-Z])?)\.\s?§)?', sor):
            out.add(m.group(1))
            if m.group(2):
                out.add(('tartomany', m.group(1), m.group(2)))
    return out


def tartomany(sorrend, tol, ig):
    if tol not in sorrend or ig not in sorrend:
        return None
    a, b = sorrend.index(tol), sorrend.index(ig)
    return sorrend[a:b + 1]


def main():
    F = kozos.forrasok()
    TS = kozos.tetelsor()
    JOG = kozos.korpusz_jogszabalyok()
    eredmeny = {'korpusz': {}, 'dobozok': {}, 'lefedettseg': {}}

    # 1. korpusz-teljesség
    hasznalt = {e['forras'] for t in TS['tetelek'] for e in t['eloirasok']} | set(TS['altalanosEloiras']['forrasok'])
    hianyzo = sorted(k for k in hasznalt if not F[k].get('korpusz') or not any(kozos.korpusz_fajl(x) for x in F[k]['korpusz']))
    kotott = {kozos.nfc(x) for f in F.values() for x in (f.get('korpusz') or [])}
    fajlok = sorted(kozos.nfc(f) for f in os.listdir(kozos.KORPUSZ) if f.endswith('.txt'))
    kotetlen = [f for f in fajlok if f not in kotott]
    eredmeny['korpusz'] = {'hianyzoForras': hianyzo, 'forrashozNemKotottFajl': kotetlen,
                           'duplikalt': [k for k, f in F.items() if len(f.get('korpusz') or []) > 1]}

    # 2. dobozok
    dob_osszes, dob_hibak = 0, []
    tetel_dobozok = {}
    for t in TS['tetelek']:
        n = t['sorszam']; txt = kozos.tetel_szoveg(n)
        dl = kozos.dobozok(txt); tetel_dobozok[n] = dl
        for kod, par, fejlec, sorok in dl:
            dob_osszes += 1
            if kod not in JOG:
                dob_hibak.append({'tetel': n, 'fejlec': fejlec, 'hiba': 'a jogszabály nincs a korpuszban'}); continue
            forras = JOG[kod][0].get(par)
            if forras is None:
                dob_hibak.append({'tetel': n, 'fejlec': fejlec, 'hiba': 'a § nincs a korpuszban'}); continue
            rossz = []
            for s in sorok:
                ns = kozos.norm(re.sub(r'^\[[^\]]*\]\s*', '', s))
                # a korpusz a hatályon kívül helyezett egységet csillaggal jelöli, a tétel szövegesen
                ns = re.sub(r'\s*Hatályon kívül helyezve\.?', '', ns).strip()
                if ns and ns not in forras:
                    rossz.append(s[:200])
            if rossz:
                dob_hibak.append({'tetel': n, 'fejlec': fejlec, 'hiba': 'eltér a korpusztól', 'sor': rossz[0]})
    eredmeny['dobozok'] = {'osszes': dob_osszes, 'elteres': dob_hibak}

    # 3. lefedettség
    for t in TS['tetelek']:
        n = t['sorszam']; txt = kozos.tetel_szoveg(n)
        dob_par = {(k, p) for k, p, _, _ in tetel_dobozok[n]}
        hiany, info = [], []
        for e in t['eloirasok']:
            kod = e['forras']
            if 'tol' in e:
                if kod not in JOG:
                    hiany.append({'forras': kod, 'elem': f"{e['tol']}–{e['ig']}", 'ok': 'a jogszabály nincs a korpuszban'}); continue
                szoveg, sorrend = JOG[kod]
                lista = tartomany(sorrend, e['tol'], e['ig'])
                if lista is None:
                    hiany.append({'forras': kod, 'elem': f"{e['tol']}–{e['ig']}", 'ok': 'a tartomány határa nincs a korpuszban'}); continue
                eml = emlitett_paragrafusok(txt, kod)
                tart = [x for x in eml if isinstance(x, tuple)]
                for p in lista:
                    if not hatalyos(szoveg.get(p, '')):
                        continue
                    if (kod, p) in dob_par or p in eml:
                        continue
                    if any(tartomany(sorrend, a, b) and p in tartomany(sorrend, a, b) for _, a, b in tart):
                        continue
                    hiany.append({'forras': kod, 'elem': p, 'ok': 'nincs dobozban és nincs hivatkozva'})
            elif e.get('teljes') or 'fejezetek' in e:
                if kod in JOG:
                    eml = {x for x in emlitett_paragrafusok(txt, kod) if not isinstance(x, tuple)}
                    db = len([p for p in JOG[kod][1] if hatalyos(JOG[kod][0].get(p, ''))])
                    info.append({'forras': kod, 'megjegyzes': f'teljes jogszabály / fejezetek előírva; a tétel {len(eml | {p for k, p in dob_par if k == kod})} §-át említi a {db} hatályos §-ból'})
                elif not re.search(EMLITES.get(kod, re.escape(kod)), txt):
                    hiany.append({'forras': kod, 'elem': 'teljes', 'ok': 'a tétel nem említi'})
            else:
                if not re.search(biro_minta(kod), txt):
                    hiany.append({'forras': kod, 'elem': ','.join(e.get('pontok', [])) or 'egész', 'ok': 'a tétel nem említi'})
        eredmeny['lefedettseg'][str(n)] = {'hiany': hiany, 'info': info}

    with open(os.path.join(kozos.KORPUSZ, 'ellenorzes.json'), 'w', encoding='utf-8') as f:
        json.dump(eredmeny, f, ensure_ascii=False, indent=1); f.write('\n')

    # összefoglaló
    L = ['# Ellenőrzés – 0. lépés', '', 'Gépi kimenet: `korpusz/ellenorzes.json`. Újragenerálás: `python3 tools/ellenorzes.py`.', '',
         '## 1. Korpusz', '']
    L.append('- Hiányzó előírt forrás: ' + (', '.join(hianyzo) or 'nincs'))
    L.append('- Forráshoz nem kötött korpusz-fájl: ' + (', '.join(kotetlen) or 'nincs'))
    L.append('- Több fájlban szereplő forrás: ' + (', '.join(eredmeny['korpusz']['duplikalt']) or 'nincs'))
    L += ['', f'## 2. Dobozok ({dob_osszes} doboz, {len(dob_hibak)} eltérés)', '']
    for h in dob_hibak:
        L.append(f"- {h['tetel']}. tétel, `{h['fejlec']}`: {h['hiba']}" + (f" — „{h['sor'][:120]}…”" if 'sor' in h else ''))
    L += ['', '## 3. Lefedettség (az előírt körből hiányzó elemek)', '']
    for n, v in eredmeny['lefedettseg'].items():
        if v['hiany']:
            L.append(f"- **{n}. tétel:** " + '; '.join(f"{h['forras']} {h['elem']} ({h['ok']})" for h in v['hiany']))
    with open(os.path.join(kozos.KORPUSZ, 'ellenorzes.md'), 'w', encoding='utf-8') as f:
        f.write('\n'.join(L) + '\n')
    print(f'dobozok: {dob_osszes}, eltérés: {len(dob_hibak)}; hiányzó forrás: {hianyzo}; '
          f'lefedettségi hiány: {sum(len(v["hiany"]) for v in eredmeny["lefedettseg"].values())} elem '
          f'{sum(1 for v in eredmeny["lefedettseg"].values() if v["hiany"])} tételben')


if __name__ == "__main__":
    main()
