#!/usr/bin/env python3
"""A korábban (az élő rendszerben) készült tartalmak gépi átvilágítása:  python3 tools/regi_audit.py

Nem módosít semmit; a jelentesek/regi_tartalom_audit.md és .json fájlt írja. Amit vizsgál:
 - kvíz, tanulókártya: darabszámok; a szövegben hivatkozott „Ptk. X:Y. §” megvan-e a korpuszban, és szerepel-e az adott tétel
   jogszabálydobozai között;
 - hézagpótló: a kitöltött szöveg (a hiányok helyére a megoldást írva) szó szerint egyezik-e a címkében megjelölt § szövegével;
 - memóriaútvonal: az állomások mondatai közül mennyi található meg szó szerint a tétel MAI szövegében (a javítási körök után).
A tartalmi helyességet (jó-e a kvízkérdés) a program nem ítéli meg.
"""
import glob, html, json, os, re, sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import kozos
import vazlat_gyart as v

PTK = re.compile(kozos.beallitas()['regiAuditFoMinta'])
G = kozos.GYOKER


def tiszta(s):
    return re.sub(r'\s+', ' ', html.unescape(re.sub(r'<[^>]+>', ' ', s or ''))).strip()


def szoveg_minden(o):
    if isinstance(o, str):
        yield o
    elif isinstance(o, dict):
        for x in o.values():
            yield from szoveg_minden(x)
    elif isinstance(o, list):
        for x in o:
            yield from szoveg_minden(x)


def main():
    J = kozos.korpusz_jogszabalyok(); fo = kozos.beallitas()['foKodex']; PT = J[fo][0]
    T = [t['sorszam'] for t in kozos.tetelsor()['tetelek']]
    DOBOZ = {n: {p for k, p, _, _ in kozos.dobozok(kozos.tetel_szoveg(n)) if k == fo} for n in T}
    TXT = {n: kozos.norm(kozos.tetel_szoveg(n)) for n in T}
    R = {'kviz': {}, 'tanulokartyak': {}, 'hezagpotlok': {}, 'memoriautvonal': {}}
    # kvíz és kártya
    for mappa, kulcs in (('kviz', 'questions'), ('tanulokartyak', 'flashcards')):
        for n in T:
            db = hiv = nincs = kivul = 0; rossz = set()
            for f in glob.glob(os.path.join(G, mappa, f'{n:02d}', '*.json')):
                d = json.load(open(f, encoding='utf-8')); db += len(d.get(kulcs, []))
                for s in szoveg_minden(d.get(kulcs, [])):
                    for p in PTK.findall(tiszta(s)):
                        hiv += 1
                        if p not in PT:
                            nincs += 1; rossz.add(p)
                        elif p not in DOBOZ[n]:
                            kivul += 1
            R[mappa][n] = {'elem': db, 'ptk_hivatkozas': hiv, 'nincs_a_korpuszban': nincs, 'nem_letezo': sorted(rossz), 'nincs_a_tetel_dobozaiban': kivul}
    # hézagpótló
    KOD = [(rx, k) for rx, k in kozos.beallitas()['regiAuditKod']]
    for n in T:
        db = egyezik = szokoz = elter = nem_vizsg = 0; pl = []
        for f in glob.glob(os.path.join(G, 'hezagpotlok', f'{n:02d}', '*.json')):
            for it in json.load(open(f, encoding='utf-8')).get('items', []):
                db += 1; c = it.get('cimke', '')
                kod = next((k for rx, k in KOD if re.search(rx, c)), None)
                m = re.search(r'(\d+(?::\d+)?(?:/[A-Z])?)\.\s*§', c)
                szov = J.get(kod, ({}, []))[0].get(m.group(1)) if kod and m else None
                if szov is None:
                    nem_vizsg += 1; continue
                t = it['text']
                for b in it.get('blanks', []):
                    t = t.replace(f'__[{b["id"]}]__', b['answer'])
                t = re.sub(r'^\[[^\]]*\]\s*', '', t)
                # bekezdésenként / pontonként vizsgálunk, mert a tétel a §-nak csak részeit idézi
                reszek = [x.strip() for x in re.split(r'(?=\(\d+[a-z]?\) )|\n', t) if x.strip()]
                tomor = lambda x: re.sub(r'\s+', '', kozos.norm(x))
                if all(kozos.norm(x) in szov for x in reszek):
                    egyezik += 1
                elif tomor(t) in tomor(szov) or all(tomor(x) in tomor(szov) for x in reszek):
                    szokoz += 1          # csak a szóközök hiányoznak vagy térnek el (pl. „ügyészkérheti”)
                else:
                    elter += 1
                    if len(pl) < 5:
                        pl.append(c)
        R['hezagpotlok'][n] = {'elem': db, 'egyezik': egyezik, 'csak_szokoz': szokoz, 'elter': elter, 'nem_vizsgalhato': nem_vizsg, 'elteres_peldak': pl}
    # memóriaútvonal
    for n in T:
        mon = megvan = 0; all_ = 0
        for f in sorted(glob.glob(os.path.join(G, 'memoriautvonal', f'{n:02d}', 'allomasok', '*.json'))):
            all_ += 1
            d = json.load(open(f, encoding='utf-8'))
            for bek in re.split(r'</p>|</h\d>|</li>', d.get('tartalom', '')):
                for s in v.mondatok(tiszta(bek)):
                    if len(s) < 40:
                        continue
                    mon += 1; megvan += kozos.norm(s) in TXT[n]
        R['memoriautvonal'][n] = {'allomas': all_, 'mondat': mon, 'megvan_a_mai_szovegben': megvan}
    json.dump(R, open(os.path.join(G, 'jelentesek', 'regi_tartalom_audit.json'), 'w', encoding='utf-8'), ensure_ascii=False, indent=1)
    S = lambda m, k: sum(x[k] for x in R[m].values())
    L = ['# A korábbi tartalmak gépi átvilágítása', '',
         'Készítette: `tools/regi_audit.py` (nem módosít semmit). A tartalmi helyességet nem ítéli meg; azt méri, ami géppel ellenőrizhető.', '',
         '## Összesítés', '',
         f'- **Kvíz:** {S("kviz","elem")} kérdés; {S("kviz","ptk_hivatkozas")} {fo}.-hivatkozás, ebből nem létező §: {S("kviz","nincs_a_korpuszban")}, a tétel dobozai között nem szereplő §: {S("kviz","nincs_a_tetel_dobozaiban")}.',
         f'- **Tanulókártya:** {S("tanulokartyak","elem")} kártya; {S("tanulokartyak","ptk_hivatkozas")} {fo}.-hivatkozás, ebből nem létező §: {S("tanulokartyak","nincs_a_korpuszban")}, a tétel dobozai között nem szereplő §: {S("tanulokartyak","nincs_a_tetel_dobozaiban")}.',
         f'- **Hézagpótló:** {S("hezagpotlok","elem")} elem; a kitöltött szöveg szó szerint egyezik a jogszabállyal: {S("hezagpotlok","egyezik")}, csak szóközhiba (összeírt szavak, pl. „ügyészkérheti”): {S("hezagpotlok","csak_szokoz")}, tartalmilag eltér: {S("hezagpotlok","elter")}, nem vizsgálható (a címkéből a § nem azonosítható): {S("hezagpotlok","nem_vizsgalhato")}.',
         f'- **Memóriaútvonal:** {S("memoriautvonal","allomas")} állomás, {S("memoriautvonal","mondat")} mondat; a tétel mai szövegében szó szerint megvan: {S("memoriautvonal","megvan_a_mai_szovegben")} ({100*S("memoriautvonal","megvan_a_mai_szovegben")//max(1,S("memoriautvonal","mondat"))}%).', '',
         '## Tételenként', '', '| Tétel | Kvíz: kérdés / nem létező § | Kártya: db / nem létező § | Hézagpótló: egyezik / szóközhiba / eltér / nem vizsg. | Memóriaútvonal: mondat / megvan |', '|---|---|---|---|---|']
    for n in T:
        k, c, h, m = R['kviz'][n], R['tanulokartyak'][n], R['hezagpotlok'][n], R['memoriautvonal'][n]
        L.append(f'| {n} | {k["elem"]} / {k["nincs_a_korpuszban"]} {",".join(k["nem_letezo"])} | {c["elem"]} / {c["nincs_a_korpuszban"]} {",".join(c["nem_letezo"])} | {h["egyezik"]} / {h["csak_szokoz"]} / {h["elter"]} {"; ".join(h["elteres_peldak"])} / {h["nem_vizsgalhato"]} | {m["mondat"]} / {m["megvan_a_mai_szovegben"]} |')
    open(os.path.join(G, 'jelentesek', 'regi_tartalom_audit.md'), 'w', encoding='utf-8').write('\n'.join(L) + '\n')
    print('\n'.join(L[6:10]))


if __name__ == '__main__':
    main()
