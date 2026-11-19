#!/usr/bin/env python3
"""A termekek/ mappa gépi termékeinek ellenőrzése a korpusszal szemben.

§-jegyzék: minden sor szó szerint megvan a megjelölt § korpusz-szövegében.
Felsorolás: a bevezető, minden elem, alpont és a záró szöveg szó szerint megvan a §-ban, a korpuszbeli
sorrendben; a lista teljes (a korpuszban az utolsó elem után nem következik további pont).
Kilépési kód: 0, ha nincs eltérés.
"""
import glob, json, os, re, sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import kozos


def main():
    J = kozos.korpusz_jogszabalyok(); hibak = []; nd = nl = ne = 0
    T = os.path.join(kozos.GYOKER, 'termekek')
    for f in sorted(glob.glob(os.path.join(T, 'paragrafus_jegyzek', '[0-9]*.json'))):
        d = json.load(open(f, encoding='utf-8'))
        for e in d['elemek']:
            nd += 1
            szov = J.get(e['forras'], ({}, []))[0].get(e['par'])
            if szov is None:
                hibak.append((d['tetel'], e['fejlec'], 'nincs meg a § a korpuszban')); continue
            for s in e['sorok']:
                if s.startswith('[') or 'Hatályon kívül helyezve' in s:
                    continue
                if kozos.norm(s) not in szov:
                    hibak.append((d['tetel'], e['fejlec'], 'sor nincs a korpuszban: ' + s[:60]))
    for f in sorted(glob.glob(os.path.join(T, 'felsorolas', '[0-9]*.json'))):
        d = json.load(open(f, encoding='utf-8'))
        for l in d['listak']:
            nl += 1
            szov = J.get(l['forras'], ({}, []))[0].get(l['par'])
            if szov is None:
                hibak.append((d['tetel'], l['id'], 'nincs meg a § a korpuszban')); continue
            poz = szov.find(kozos.norm(l['bevezeto']) + ' a) ')
            if poz < 0:
                hibak.append((d['tetel'], l['id'], 'bevezető nincs a korpuszban')); continue
            poz += len(kozos.norm(l['bevezeto']))
            for i, e in enumerate(l['elemek']):
                ne += 1
                assert e['jel'] == chr(ord('a') + i)
                for jel, sz in [(e['jel'], e['szoveg'])] + [(a['jel'], a['szoveg']) for a in e['alpontok']]:
                    minta = kozos.norm(f'{jel}) {sz}')
                    p = szov.find(minta, poz)
                    if p < 0 or szov[poz:p].strip():
                        hibak.append((d['tetel'], l['id'], f'{jel}) pont nem következik szó szerint: ' + sz[:50])); break
                    poz = p + len(minta)
                if kozos.norm(e['tiszta']) not in kozos.norm(e['szoveg']):
                    hibak.append((d['tetel'], l['id'], 'a tisztított elem eltér'))
            maradek = szov[poz:].strip()
            if l['zaro']:
                z = kozos.norm(l['zaro'])
                if not maradek.startswith(z):
                    hibak.append((d['tetel'], l['id'], 'záró szöveg nem következik szó szerint'))
                maradek = maradek[len(z):].strip()
            kov = chr(ord('a') + len(l['elemek']))
            if re.match(rf'^{kov}[a-z]?\) ', maradek) or (not l['zaro'] and maradek and maradek[0].islower()):
                hibak.append((d['tetel'], l['id'], 'a lista a korpuszban folytatódik: ' + maradek[:50]))
    print(f'§-jegyzék: {nd} doboz; felsorolás: {nl} lista, {ne} elem; eltérés: {len(hibak)}')
    for h in hibak:
        print('  ', *h)
    return 1 if hibak else 0


if __name__ == '__main__':
    sys.exit(main())
