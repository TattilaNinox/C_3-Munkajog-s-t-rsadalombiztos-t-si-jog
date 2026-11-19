#!/usr/bin/env python3
"""A termekek/ mappa gépi termékeinek ellenőrzése a korpusszal szemben.

§-jegyzék: minden sor szó szerint megvan a megjelölt § korpusz-szövegében.
Felsorolás: a bevezető, minden elem, alpont és a záró szöveg szó szerint megvan a §-ban, a korpuszbeli
sorrendben; a lista teljes (a korpuszban az utolsó elem után nem következik további pont). A hatályon kívül
helyezett, üres pont („j) k) …”) és a jelölésből kihagyható betű (p) → r), w) → z)) nem hézag (kozos.pont_kovetkezo).
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
            utolso = None   # az utolsó pont jele (a hatályon kívül helyezett, üres pont is: kozos.pont_kovetkezo)
            for i, e in enumerate(l['elemek']):
                ne += 1
                for k, (jel, sz) in enumerate([(e['jel'], e['szoveg'])] + [(a['jel'], a['szoveg']) for a in e['alpontok']]):
                    minta = kozos.norm(f'{jel}) {sz}')
                    p = szov.find(minta, poz)
                    kozte = szov[poz:p].strip() if p >= 0 else ''
                    jo = p >= 0 and not kozte
                    if p >= 0 and kozte and re.fullmatch(r'(?:[a-z]{1,2}\)\s*)+', kozte):   # üres (hatályon kívül helyezett) pontok
                        u = utolso; jo = True
                        for x in re.findall(r'([a-z]{1,2})\)', kozte):
                            if k == 0 and x in kozos.pont_kovetkezo(u):
                                u = x
                            elif not (k > 0 and len(x) == 2 and x[0] == e['jel']):
                                jo = False
                        if k == 0:
                            utolso = u
                    if k == 0 and jo and jel not in kozos.pont_kovetkezo(utolso):
                        hibak.append((d['tetel'], l['id'], f'{jel}) pont jele nem a következő pont jele')); break
                    if not jo:
                        hibak.append((d['tetel'], l['id'], f'{jel}) pont nem következik szó szerint: ' + sz[:50])); break
                    if k == 0:
                        utolso = jel
                    poz = p + len(minta)
                if kozos.norm(e['tiszta']) not in kozos.norm(e['szoveg']):
                    hibak.append((d['tetel'], l['id'], 'a tisztított elem eltér'))
            maradek = szov[poz:].strip()
            while True:   # a lista végén álló üres (hatályon kívül helyezett) pontok
                m = re.match(r'^([a-z]{1,2})\) ?', maradek)
                if not (m and m.group(1) in kozos.pont_kovetkezo(utolso)):
                    break
                tovabb = maradek[m.end():]
                if tovabb and not re.match(r'[a-z]{1,2}\) |\(\d', tovabb):
                    break
                utolso = m.group(1); maradek = tovabb.strip()
            if l['zaro']:
                z = kozos.norm(l['zaro'])
                if not maradek.startswith(z):
                    hibak.append((d['tetel'], l['id'], 'záró szöveg nem következik szó szerint'))
                maradek = maradek[len(z):].strip()
            kov = '|'.join(kozos.pont_kovetkezo(utolso)) or '(?!)'
            if re.match(rf'^(?:{kov})[a-z]?\) ', maradek) or (not l['zaro'] and maradek and maradek[0].islower()):
                hibak.append((d['tetel'], l['id'], 'a lista a korpuszban folytatódik: ' + maradek[:50]))
    print(f'§-jegyzék: {nd} doboz; felsorolás: {nl} lista, {ne} elem; eltérés: {len(hibak)}')
    for h in hibak:
        print('  ', *h)
    return 1 if hibak else 0


if __name__ == '__main__':
    sys.exit(main())
