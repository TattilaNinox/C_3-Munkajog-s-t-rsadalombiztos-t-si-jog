"""Segédfüggvények döntési fa írásához (a fák forrása a termekek/dontesi_fa/<id>.json)."""
import json, os, sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import kozos
KI = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 'termekek', 'dontesi_fa')
def P(par, idezet, forras=None):
    if forras is None:
        forras = kozos.beallitas()['foKodex']
    return {'forras': forras, 'par': par, 'idezet': idezet}
def K(szoveg, alap, *agak): return {'tipus': 'kerdes', 'szoveg': szoveg, 'alap': alap, 'agak': [{'felirat': f, 'kov': k} for f, k in agak]}
def E(szoveg, alap): return {'tipus': 'eredmeny', 'szoveg': szoveg, 'alap': alap}
def ir(id, cim, kerdes, tetel, gyoker, cs, peldak, megjegyzes=None):
    d = {'sema': 1, 'termek': 'dontesi_fa', 'id': id, 'cim': cim, 'kerdes': kerdes, 'tetel': tetel, 'gyoker': gyoker, 'csomopontok': cs,
         'peldak': [{'leiras': l, 'valaszok': v, 'eredmeny': e} for l, v, e in peldak]}
    if megjegyzes: d['megjegyzes'] = megjegyzes
    json.dump(d, open(os.path.join(KI, id + '.json'), 'w', encoding='utf-8'), ensure_ascii=False, indent=1)
