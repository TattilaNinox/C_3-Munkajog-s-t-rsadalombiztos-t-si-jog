#!/usr/bin/env python3
"""A kattintható hatály-felület (korpusz/hatalyok.html) generálása. A tároló gyökeréből:

    python3 tools/ellenorzes.py      # előbb az ellenőrzés
    python3 tools/hatalyok.py

Bemenet: tetelsor/tetelsor.json, tetelsor/forrasok.json, korpusz/manifest.json,
korpusz/ellenorzes.json és korpusz/allapot.json (az időállapotokat Attila tölti ki).
Ha az allapot.json hiányzik vagy új forrás jelent meg, a szkript kiegészíti üres mezőkkel;
a már kitöltött értékekhez nem nyúl.
"""
import datetime, html, json, os, sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import kozos

ALLAPOT = os.path.join(kozos.KORPUSZ, 'allapot.json')
MEZOK = ['hatalyosNapjan', 'kovetkezoIdoallapot', 'kovetkezoValtozas', 'ellenorizve', 'megjegyzes']
REGI = ['idoallapotKezdete', 'idoallapotVege']


def allapot_frissit(F):
    if os.path.exists(ALLAPOT):
        A = json.load(open(ALLAPOT, encoding='utf-8'))
    else:
        A = {'forrasok': {}}
    A['_kitoltes'] = (
        'hatalyosNapjan: az a nap, amelyen a korpuszban lévő szöveg a hatályos szöveg volt. Ha a szöveget a '
        'Jogszabálytárból azon a napon töltöd le és töltöd fel, amikor a korpuszba kerül, ez a feltöltés napja '
        '(ÉÉÉÉ-HH-NN). kovetkezoIdoallapot: a következő ismert időállapot kezdete, ha a Jogszabálytár már mutatja; '
        'kovetkezoValtozas: egy mondat, mi változik. ellenorizve: mikor nézted meg utoljára. Bírósági '
        'iránymutatásnál csak az ellenorizve és a megjegyzes kell. Ami nem ismert: null, nincs találgatás.')
    for kod in F:
        rec = A['forrasok'].setdefault(kod, {})
        for m in REGI:
            if rec.get(m) is None:
                rec.pop(m, None)
        for m in MEZOK:
            rec.setdefault(m, None)
    with open(ALLAPOT, 'w', encoding='utf-8') as f:
        json.dump(A, f, ensure_ascii=False, indent=1); f.write('\n')
    return A['forrasok']


def main():
    F = kozos.forrasok(); TS = kozos.tetelsor()
    E = json.load(open(os.path.join(kozos.KORPUSZ, 'ellenorzes.json'), encoding='utf-8'))
    M = {kozos.nfc(os.path.basename(i['file'])): i for i in json.load(open(os.path.join(kozos.KORPUSZ, 'manifest.json'), encoding='utf-8'))['items']}
    A = allapot_frissit(F)

    # érintett tételek forrásonként: az előírás és a dobozok alapján
    erintett = {k: {} for k in F}
    for t in TS['tetelek']:
        for e in t['eloirasok']:
            erintett[e['forras']].setdefault(t['sorszam'], {'eloiras': [], 'doboz': 0})['eloiras'].append(e)
        for kod, par, fej, sorok in kozos.dobozok(kozos.tetel_szoveg(t['sorszam'])):
            erintett[kod].setdefault(t['sorszam'], {'eloiras': [], 'doboz': 0})['doboz'] += 1
    for k in TS['altalanosEloiras']['forrasok']:
        erintett[k].setdefault(0, {'eloiras': [{'forras': k, 'teljes': True}], 'doboz': 0})

    doboz_elter = {}
    for h in E['dobozok']['elteres']:
        doboz_elter.setdefault(h['tetel'], []).append(h)

    adat = {
        'generalva': datetime.date.today().isoformat(),
        'tetelsor': TS['tetelsor'],
        'forrasok': [],
        'tetelek': [],
        'osszesites': {'dobozok': E['dobozok']['osszes'], 'dobozElteres': len(E['dobozok']['elteres']),
                       'hianyzoForras': E['korpusz']['hianyzoForras'], 'duplikalt': E['korpusz']['duplikalt']},
    }
    for kod, f in F.items():
        fajlok = []
        for x in f.get('korpusz') or []:
            m = M.get(kozos.nfc(x))
            fajlok.append({'nev': kozos.nfc(x), 'storageFrissitve': (m or {}).get('storageFrissitve'), 'bajt': (m or {}).get('bytes')})
        adat['forrasok'].append({
            'kod': kod, 'nev': f['nev'], 'tipus': f['tipus'], 'link': f.get('jogszabalytar'), 'jogtar': f.get('jogtar'), 'jogkodex': f.get('jogkodex'),
            'megjegyzesForras': f.get('megjegyzes'), 'fajlok': fajlok, 'hianyzik': not fajlok,
            'allapot': A.get(kod, {}),
            'tetelek': sorted([{'n': n, 'doboz': v['doboz'], 'eloiras': v['eloiras']} for n, v in erintett[kod].items()], key=lambda x: x['n']),
        })
    for t in TS['tetelek']:
        n = t['sorszam']; lf = E['lefedettseg'][str(n)]
        adat['tetelek'].append({'n': n, 'csoport': t['csoport'], 'cim': t['cim'], 'eloirasSzoveg': t['eloirasSzoveg'],
                                'eloirasok': t['eloirasok'], 'hiany': lf['hiany'], 'info': lf['info'],
                                'dobozElteres': doboz_elter.get(n, []), 'megjegyzes': t.get('tetelsorMegjegyzes')})

    sablon = open(os.path.join(os.path.dirname(os.path.abspath(__file__)), 'hatalyok_sablon.html'), encoding='utf-8').read()
    ki = sablon.replace('/*ADAT*/null', json.dumps(adat, ensure_ascii=False).replace('</', '<\\/'))
    ki = ki.replace('{{TETELSOR}}', html.escape(TS['tetelsor']))
    with open(os.path.join(kozos.KORPUSZ, 'hatalyok.html'), 'w', encoding='utf-8') as f:
        f.write(ki)
    print(f"korpusz/hatalyok.html: {len(adat['forrasok'])} forrás, {len(adat['tetelek'])} tétel")


main()
