#!/usr/bin/env python3
"""A döntési fák gépi ellenőrzése:  python3 tools/fa_ellenor.py

Forrás: termekek/dontesi_fa/*.json (az index.json kivételével). Minden fára:
 1. szerkezet: a gyökér létezik; a kérdésnek legalább két, eltérő feliratú ága van; minden ág létező csomópontra mutat;
    az eredménynek nincs ága; nincs kör; minden csomópont elérhető a gyökérből (nincs zsákutca és nincs árva csomópont);
 2. jogalap: minden csomópontnak van legalább egy jogalapja (forrás, §, szó szerinti idézet); a § megvan a korpuszban,
    az idézet szó szerint benne van a § szövegében, és a § szerepel a fa tételeinek valamelyik jogszabálydobozában;
 3. számok: a csomópont szövegében csak olyan szám állhat, amely az idézett jogszabályszövegben is benne van;
    számított értéket a fa nem közöl, hanem a `szamolo` mezővel a számolóra utal (a számolónak léteznie kell);
 4. példák: minden példa válaszsorozata végigjárható, és a megadott eredményhez vezet; minden eredményhez van példa.
Kilépési kód: 0, ha nincs hiba. Az index.json-t a program írja.
"""
import glob, json, os, re, sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import kozos

KI = os.path.join(kozos.GYOKER, 'termekek', 'dontesi_fa')


_EGYES = 'kettő|két|három|négy|öt|hat|hét|nyolc|kilenc'
_SZAM = (r'(?:másfél|' + _EGYES + r'|tíz|tizen(?:egy|' + _EGYES + r')|húsz|huszon(?:egy|' + _EGYES + r')|harminc|negyven|ötven|hatvan|hetven|nyolcvan|kilencven|száz|ezer|egy(?=negyed|nyolcad|harmad|tized|ötöd|hatod))'
         r'(?:negyed|nyolcad|harmad|tized|ötöd|hatod|szeres\w*|szor|szer|ször|éves|évi|napos|hetes|hónapos|havi|edik|adik|ödik|odik)?')
SZAMSZO = re.compile(r'(?<![\wáéíóöőúüű])(?:\d+|' + _SZAM + r')(?![\wáéíóöőúüű])', re.I)



_NYERS = None


def gondolatjeles(idezet):
    """Igaz, ha az idézet kötőjeles alakja nincs a korpuszban, a gondolatjeles alakja viszont megvan
    (a kozos.norm a kétféle jelet összemossa, ezért a szó szerintiség próbája ezt nem veszi észre)."""
    global _NYERS
    if _NYERS is None:
        import glob
        _NYERS = ' '.join(re.sub(r'\s+', ' ', open(f, encoding='utf-8').read())
                          for f in glob.glob(os.path.join(kozos.GYOKER, 'korpusz', '*.txt')))
    a = re.sub(r'\s+', ' ', idezet)
    return a not in _NYERS and a.replace(' - ', ' – ') in _NYERS

def szamok(s):
    """A szövegben álló számok (számjegy vagy betűvel írt számnév); a puszta „egy” névelőként nem számít."""
    return {m.group(0).lower() for m in SZAMSZO.finditer(s)}


def ellenoriz(d, J, DOBOZ):
    h = []; C = d.get('csomopontok', {})
    for k in ('id', 'cim', 'kerdes', 'tetel', 'gyoker', 'csomopontok', 'peldak'):
        if k not in d:
            h.append(f'hiányzó mező: {k}')
    if h:
        return h
    if d['gyoker'] not in C:
        return ['a gyökér nem létezik']
    tetel_par = set()
    for n in d['tetel']:
        tetel_par |= DOBOZ[n]
    for cid, c in C.items():
        if c['tipus'] == 'kerdes':
            ag = c.get('agak', [])
            if len(ag) < 2:
                h.append(f'{cid}: kevesebb mint két ág')
            if len({a['felirat'] for a in ag}) != len(ag):
                h.append(f'{cid}: azonos feliratú ágak')
            for a in ag:
                if a['kov'] not in C:
                    h.append(f'{cid}: nem létező csomópontra mutat: {a["kov"]}')
        elif c['tipus'] == 'eredmeny':
            if c.get('agak'):
                h.append(f'{cid}: eredménynek ága van')
        else:
            h.append(f'{cid}: ismeretlen típus')
        if not c.get('szoveg', '').strip():
            h.append(f'{cid}: üres szöveg')
        if not c.get('alap'):
            h.append(f'{cid}: nincs jogalap')
        # szám csak az idézett jogszabályszövegből jöhet; számított érték a számolóból
        idez = ' '.join(a['idezet'] for a in c.get('alap', [])).lower()
        for sz in sorted(szamok(c.get('szoveg', ''))):
            if not re.search(r'(?<![\wáéíóöőúüű])' + re.escape(sz), idez):
                h.append(f'{cid}: a szövegben olyan szám áll, amely nincs az idézett jogszabályszövegben: {sz}')
        if c.get('szamolo') and not os.path.exists(os.path.join(kozos.GYOKER, 'termekek', 'szamolo', c['szamolo'] + '.json')):
            h.append(f'{cid}: nem létező számolóra hivatkozik: {c["szamolo"]}')
        for a in c.get('alap', []):
            szov = J.get(a['forras'], ({}, []))[0].get(a['par'])
            if szov is None:
                h.append(f'{cid}: nincs meg a korpuszban: {a["forras"]} {a["par"]}'); continue
            if kozos.norm(a['idezet']) not in szov:
                h.append(f'{cid}: az idézet nem szó szerinti ({a["forras"]} {a["par"]}): {a["idezet"][:50]}')
            elif ' - ' in a['idezet'] and gondolatjeles(a['idezet']):
                h.append(f'{cid}: az idézetben kötőjel áll a korpusz gondolatjele helyett ({a["forras"]} {a["par"]}): {a["idezet"][:50]}')
            if (a['forras'], a['par']) not in tetel_par:
                h.append(f'{cid}: a § nincs a tétel(ek) dobozai között: {a["forras"]} {a["par"]}')
            elif not any(kozos.norm(a['idezet']) in kozos.doboz_szoveg(n).get((a['forras'], a['par']), '') for n in d['tetel']):
                h.append(f'{cid}: az idézet nincs a tétel dobozának szövegében (a doboz a § más részét tartalmazza): {a["forras"]} {a["par"]}: {a["idezet"][:50]}')
    if h:
        return h
    # elérhetőség és körmentesség
    latott = set(); uton = set()

    def bejar(x):
        if x in uton:
            h.append(f'kör: {x}'); return
        if x in latott:
            return
        latott.add(x); uton.add(x)
        for a in C[x].get('agak', []):
            bejar(a['kov'])
        uton.discard(x)
    bejar(d['gyoker'])
    for cid in C:
        if cid not in latott:
            h.append(f'{cid}: a gyökérből nem érhető el')
    # példák
    elert = set()
    for i, p in enumerate(d['peldak'], 1):
        x = d['gyoker']; ok = True
        for v in p['valaszok']:
            ag = {a['felirat']: a['kov'] for a in C[x].get('agak', [])}
            if v not in ag:
                h.append(f'{i}. példa: nincs „{v}” ág a(z) {x} csomópontnál'); ok = False; break
            x = ag[v]
        if ok:
            if C[x]['tipus'] != 'eredmeny':
                h.append(f'{i}. példa: nem jut el eredményig ({x})')
            elif x != p['eredmeny']:
                h.append(f'{i}. példa: {x} lett, a várt {p["eredmeny"]}')
            elert.add(x)
    for cid, c in C.items():
        if c['tipus'] == 'eredmeny' and cid not in elert:
            h.append(f'{cid}: nincs hozzá példa')
    return h


def main():
    J = kozos.korpusz_jogszabalyok()
    DOBOZ = {t['sorszam']: {(k, p) for k, p, _, _ in kozos.dobozok(kozos.tetel_szoveg(t['sorszam']))} for t in kozos.tetelsor()['tetelek']}
    index = []; hibas = 0; cs = pe = 0
    for f in sorted(glob.glob(os.path.join(KI, '*.json'))):
        if os.path.basename(f) == 'index.json':
            continue
        d = json.load(open(f, encoding='utf-8'))
        h = ellenoriz(d, J, DOBOZ)
        if d.get('id') != os.path.basename(f)[:-5]:
            h.append('az id nem egyezik a fájlnévvel')
        cs += len(d.get('csomopontok', {})); pe += len(d.get('peldak', []))
        if h:
            hibas += 1; print(f'HIBA {os.path.basename(f)}'); [print('   ', x) for x in h]
        index.append({'id': d.get('id'), 'cim': d.get('cim'), 'tetel': d.get('tetel'), 'csomopont': len(d.get('csomopontok', {})), 'pelda': len(d.get('peldak', []))})
    os.makedirs(KI, exist_ok=True)   # új tételsor: a mappa és az üres index.json kiinduló állapot
    json.dump({'sema': 1, 'termek': 'dontesi_fa', 'fak': index}, open(os.path.join(KI, 'index.json'), 'w', encoding='utf-8'), ensure_ascii=False, indent=1)
    print(f'döntési fák: {len(index)}, csomópont: {cs}, példa: {pe}, hibás fa: {hibas}')
    sys.exit(1 if hibas else 0)


if __name__ == '__main__':
    main()
