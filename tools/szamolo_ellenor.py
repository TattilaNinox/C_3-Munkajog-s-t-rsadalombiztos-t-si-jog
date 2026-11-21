#!/usr/bin/env python3
"""A számolók (szabálytáblák) gépi ellenőrzése:  python3 tools/szamolo_ellenor.py

Forrás: termekek/szamolo/*.json (az index.json kivételével). Minden számolóra:
 1. hézag- és átfedésmentesség: a bemenetek minden lehetséges kombinációjára pontosan egy szabály illik;
 2. hányadok: minden szabályban, vagyonrészenként a tulajdoni hányadok összege pontosan 1 (törtekkel számolva);
 3. jogalap: minden szabályhoz van forrás, § és szó szerinti idézet; az idézet benne van a korpuszban, a § a tétel dobozai között;
 4. számok: a szabály szövegében csak olyan szám állhat, amely az idézett jogszabályszövegben is benne van
    (a számított hányad a `hanyad` mezőben van, azt a 2. pont ellenőrzi);
 5. megnevezés: minden vagyonrész (`targy`) megjelenített neve szerepel a számoló `targyak` mezőjében;
 6. példák: minden példa bemenete a megadott szabályra illik, és a kiszámított hányadok egyeznek a várt értékekkel;
    minden szabályhoz van példa.
A hányad kifejezés: egész számok, a bemenet egész változói, + - * / és zárójel (pl. "1/(gyermekagak+1)").
"""
import glob, itertools, json, os, re, sys
from fractions import Fraction
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import kozos
import fa_ellenor

KI = os.path.join(kozos.GYOKER, 'termekek', 'szamolo')


def ertek(kif, b):
    if not re.fullmatch(r'[\w\s+\-*/()]+', kif):
        raise ValueError('tiltott karakter a kifejezésben: ' + kif)
    k = re.sub(r'\b(\d+)\b', r'F(\1)', kif)
    nevek = {n: Fraction(v) for n, v in b.items() if isinstance(v, int) and not isinstance(v, bool)}
    return Fraction(eval(k, {'__builtins__': {}, 'F': Fraction}, nevek))


def illik(sz, b):
    for f in sz['ha']:
        v = b[f['valtozo']]; e = f['ertek']
        if not {'==': v == e, '!=': v != e, '>=': v >= e, '<=': v <= e}[f['op']]:
            return False
    return True


def tartomany(be):
    if be['tipus'] == 'logikai':
        return [True, False]
    if be['tipus'] == 'egesz':
        return list(range(be['min'], be['max'] + 1))
    return [x['ertek'] for x in be['ertekek']]


def szamol(d, b):
    """A bemenetre illő szabályok és a kiszámított részek: [(szabály, [(tárgy, ki, db, fejenkénti hányad, jog)])]."""
    out = []
    for sz in d['szabalyok']:
        if illik(sz, b):
            r = [(v['targy'], x['ki'], int(ertek(str(x.get('db', 1)), b)), ertek(x['hanyad'], b), x.get('jog', 'tulajdon'))
                 for v in sz.get('vagyonreszek', []) for x in v['reszek']]
            out.append((sz, r))
    return out


def ellenoriz(d, J, DOBOZ):
    h = []
    tetel_par = set()
    for n in d['tetel']:
        tetel_par |= DOBOZ[n]
    nevek = [b['nev'] for b in d['bemenet']]
    for kombi in itertools.product(*[tartomany(b) for b in d['bemenet']]):
        b = dict(zip(nevek, kombi))
        try:
            t = szamol(d, b)
        except Exception as e:
            h.append(f'{b}: számítási hiba: {e}'); continue
        if len(t) != 1:
            h.append(f'{b}: {len(t)} szabály illik ({[x[0]["id"] for x in t]})'); continue
        ossz = {}
        for targy, ki, db, hany, jog in t[0][1]:
            if jog == 'tulajdon':
                ossz[targy] = ossz.get(targy, 0) + db * hany
            if hany <= 0 or hany > 1 or db < 1:
                h.append(f'{b}: értelmetlen hányad vagy darabszám ({ki})')
        for targy, o in ossz.items():
            if o != 1:
                h.append(f'{b}: a(z) {targy} hányadainak összege {o}, nem 1 ({t[0][0]["id"]})')
    for sz in d['szabalyok']:
        for v in sz.get('vagyonreszek', []):
            if v['targy'] not in d.get('targyak', {}):
                h.append(f'{sz["id"]}: a vagyonrésznek nincs megjelenített neve (targyak): {v["targy"]}')
        if not sz.get('alap'):
            h.append(f'{sz["id"]}: nincs jogalap')
        idez = ' '.join(a['idezet'] for a in sz.get('alap', [])).lower()
        for s in sorted(fa_ellenor.szamok(sz.get('szoveg', ''))):
            if not re.search(r'(?<![\wáéíóöőúüű])' + re.escape(s), idez):
                h.append(f'{sz["id"]}: a szövegben olyan szám áll, amely nincs az idézett jogszabályszövegben: {s}')
        for a in sz.get('alap', []):
            szov = J.get(a['forras'], ({}, []))[0].get(a['par'])
            if szov is None:
                h.append(f'{sz["id"]}: nincs meg a korpuszban: {a["forras"]} {a["par"]}'); continue
            if kozos.norm(a['idezet']) not in szov:
                h.append(f'{sz["id"]}: az idézet nem szó szerinti ({a["par"]}): {a["idezet"][:50]}')
            elif ' - ' in a['idezet'] and fa_ellenor.gondolatjeles(a['idezet']):
                h.append(f'{sz["id"]}: az idézetben kötőjel áll a korpusz gondolatjele helyett ({a["par"]}): {a["idezet"][:50]}')
            if (a['forras'], a['par']) not in tetel_par:
                h.append(f'{sz["id"]}: a § nincs a tétel(ek) dobozai között: {a["forras"]} {a["par"]}')
            elif not any(kozos.norm(a['idezet']) in kozos.doboz_szoveg(n).get((a['forras'], a['par']), '') for n in d['tetel']):
                h.append(f'{sz["id"]}: az idézet nincs a tétel dobozának szövegében (a doboz a § más részét tartalmazza): {a["forras"]} {a["par"]}: {a["idezet"][:50]}')
    volt = set()
    for i, p in enumerate(d['peldak'], 1):
        t = szamol(d, p['bemenet'])
        if len(t) != 1:
            h.append(f'{i}. példa: {len(t)} szabály illik'); continue
        volt.add(t[0][0]['id'])
        if t[0][0]['id'] != p['szabaly']:
            h.append(f'{i}. példa: {t[0][0]["id"]} illik, a várt {p["szabaly"]}')
        kap = sorted((targy, ki, db, str(hany), jog) for targy, ki, db, hany, jog in t[0][1])
        var = sorted((x['targy'], x['ki'], x.get('db', 1), x['hanyad'], x.get('jog', 'tulajdon')) for x in p['vart'])
        if kap != var:
            h.append(f'{i}. példa: a számított részek eltérnek a várttól: {kap} != {var}')
    for sz in d['szabalyok']:
        if sz['id'] not in volt:
            h.append(f'{sz["id"]}: nincs hozzá példa')
    return h


def main():
    J = kozos.korpusz_jogszabalyok()
    DOBOZ = {t['sorszam']: {(k, p) for k, p, _, _ in kozos.dobozok(kozos.tetel_szoveg(t['sorszam']))} for t in kozos.tetelsor()['tetelek']}
    index = []; hibas = 0
    for f in sorted(glob.glob(os.path.join(KI, '*.json'))):
        if os.path.basename(f) == 'index.json':
            continue
        d = json.load(open(f, encoding='utf-8'))
        h = ellenoriz(d, J, DOBOZ)
        if h:
            hibas += 1; print('HIBA', os.path.basename(f)); [print('   ', x) for x in h[:20]]
        index.append({'id': d['id'], 'cim': d['cim'], 'tetel': d['tetel'], 'szabaly': len(d['szabalyok']), 'pelda': len(d['peldak'])})
    os.makedirs(KI, exist_ok=True)   # új tételsor: a mappa és az üres index.json kiinduló állapot
    json.dump({'sema': 1, 'termek': 'szamolo', 'szamolok': index}, open(os.path.join(KI, 'index.json'), 'w', encoding='utf-8'), ensure_ascii=False, indent=1)
    print(f'számolók: {len(index)}, szabály: {sum(x["szabaly"] for x in index)}, példa: {sum(x["pelda"] for x in index)}, hibás: {hibas}')
    sys.exit(1 if hibas else 0)


if __name__ == '__main__':
    main()
