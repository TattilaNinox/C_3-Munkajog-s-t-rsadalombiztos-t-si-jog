#!/usr/bin/env python3
"""Az „Elhatárolások” szakaszok kigyűjtése (a fogalommátrix nyersanyaga):  python3 tools/elhatarolas_gyart.py

Kimenet: termekek/elhatarolasok/NN.json (tételenként az elhatárolások) és index.json (fogalom -> előfordulások).
Egy elhatárolás = a szakasz egy bekezdése: az első mondat a cím (az összevetett fogalmak), a többi a kifejtés.
Minden mondat szó szerint a tétel mondata; a program ezt a végén ellenőrzi. A fogalmakra bontás gépi (vessző, „és”,
„valamint” mentén), és csak akkor történik meg, ha a cím egyszerű felsorolás; különben a cím egyetlen fogalomként marad.
A szakaszban álló jogszabálydoboz (fejléc és normasorok) nem elhatárolás. A doboz utáni bekezdés az előző elhatárolás
folytatása (mondatai és §-ai ahhoz kerülnek), ha első mondata nem fogalompár-cím (a fogalmak() nem bontja); ha az,
új elhatárolás kezdődik (2026-11-18: 59. tétel, Bét. 1. § doboza után; a 37. tétel dobozai után új elhatárolás jön).
"""
import json, os, re, sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import kozos
import vazlat_gyart as v

KI = os.path.join(kozos.GYOKER, 'termekek', 'elhatarolasok')
CIM = re.compile(r'^(?:(?:[IVX]+|\d+)\. )?(?:KAPCSOLÓDÓ JOGINTÉZMÉNYEK ÉS )?ELHATÁROLÁSOK$')
FOCIM = re.compile(r'^(?:[IVX]+\. )?[A-ZÁÉÍÓÖŐÚÜŰ0-9 ,:().–\-/„”§]+$')
# elhatarolasPar: egy minta (régi alak) vagy kódonkénti minták listája / objektuma ({"Bvtv": "Bv\\. tv\\. \\d+…§",
# "EUMSZ": "EUMSZ \\d+\\. cikk"}); a minták csoport nélküliek (a findall a teljes találatot adja)
_EP = kozos.beallitas()['elhatarolasPar']
_EP = list(_EP.values()) if isinstance(_EP, dict) else _EP if isinstance(_EP, list) else [_EP]
PAR = re.compile('|'.join('(?:%s)' % x for x in _EP))


def fogalmak(cim):
    if re.search(r'[:;?]| ami | amely | hogy | ha ', cim):
        return [cim], False
    r = [x.strip() for x in re.split(r', valamint |, illetve |, és | és |, ', cim) if x.strip()]
    if len(r) < 2 or any(len(x.split()) > 7 for x in r):
        return [cim], False
    # „Osztott és egyetemleges kötelezettség”: a közös főnév csak az utolsó tagnál áll – ilyenkor nem bontunk
    if any(len(x.split()) == 1 and re.search(r'(tt|ő|ű|ú|ó|i|os|es|ös|on|en|ön|al|el|ív)$', x) for x in r[:-1]) and len(r[-1].split()) > 1:
        return [cim], False
    r = [x[0].upper() + x[1:] for x in r]
    return r, True


def doboz_sorok(txt, L):
    """A jogszabálydobozok sorainak indexei (fejléc és normasorok), a tetel_blokk.blokkok() szerint."""
    doboz = set()
    H = [i for i, l in enumerate(L) if kozos.doboz_fej(l)]
    for (kod, par, f, sorok), h in zip(kozos.dobozok(txt), H):
        doboz.add(h); x = h + 1; k = 0
        while x < len(L) and k < len(sorok):
            if L[x]:
                doboz.add(x); k += 1
            x += 1
        while x < len(L) and not L[x]:
            x += 1
        if x < len(L) and sorok and re.match(r'^[a-z]{1,2}\) ', sorok[-1]) and L[x] and L[x][0].islower() and not re.match(r'^[a-z]{1,2}\) ', L[x]):
            doboz.add(x)
    return doboz


def tetel(n):
    txt = kozos.tetel_szoveg(n); L = [l.strip() for l in txt.split('\n')]
    doboz = doboz_sorok(txt, L)
    out = []; benn = False; utana = False
    for x, l in enumerate(L):
        if not l:
            continue
        if CIM.match(l):
            benn = True; continue
        if benn and FOCIM.match(l) and l.upper() == l:
            break
        if benn:
            if x in doboz:
                utana = True; continue
            m = v.mondatok(l)
            if utana and out and m and not fogalmak(m[0].rstrip('.'))[1]:
                # a doboz utáni, címmel nem kezdődő bekezdés az előző elhatárolás folytatása
                out[-1]['mondatok'] += m; out[-1]['par'] = sorted(set(out[-1]['par']) | set(PAR.findall(l)))
                utana = False; continue
            utana = False
            if len(m) < 2:
                continue
            cim = m[0] if re.search(r'\b' + v.ROV + r'\.$', m[0]) else m[0].rstrip('.')   # „A Ptk. és a Csvt.”: a rövidítés pontja marad
            f, egyszeru = fogalmak(cim)
            out.append({'cim': cim, 'fogalmak': f, 'bontva': egyszeru, 'mondatok': m[1:], 'par': sorted(set(PAR.findall(l)))})
    return out


def main():
    os.makedirs(KI, exist_ok=True)
    T = kozos.tetelsor()['tetelek']; index = {}; ossz = 0; tt = 0
    for t in T:
        n = t['sorszam']; e = tetel(n)
        p = os.path.join(KI, f'{n:02d}.json')
        if not e:
            if os.path.exists(p):
                os.remove(p)
            continue
        txt = kozos.tetel_szoveg(n)
        for x in e:
            assert all(m in txt for m in x['mondatok']) and x['cim'] in txt, (n, x['cim'])
            for f in x['fogalmak']:
                index.setdefault(f, []).append({'tetel': n, 'cim': x['cim']})
        json.dump({'sema': 1, 'termek': 'elhatarolasok', 'tetel': n, 'cim': t['cim'], 'elhatarolasok': e}, open(p, 'w', encoding='utf-8'), ensure_ascii=False, indent=1)
        ossz += len(e); tt += 1
    json.dump({'sema': 1, 'termek': 'elhatarolasok', 'fogalmak': dict(sorted(index.items()))}, open(os.path.join(KI, 'index.json'), 'w', encoding='utf-8'), ensure_ascii=False, indent=1)
    tobb = {k: len(x) for k, x in index.items() if len({y['tetel'] for y in x}) > 1}
    print(f'elhatárolások: {tt} tétel, {ossz} elhatárolás, {len(index)} fogalom; több tételben is szerepel: {len(tobb)}')


if __name__ == '__main__':
    main()
