#!/usr/bin/env python3
"""A felolvasószöveg-készítő (tools/hangszoveg.py) regressziós tesztje.   python3 tools/hangszoveg_teszt.py

Bemenet → elvárt kimenet párok a hangra / blokk_hang / darabol függvényeken. A csoportok:
  M     a mai, helyes viselkedés rögzítése (a javítás ezt nem ronthatja el);
  1–11  a termekek/_elesites_elott.json „hangszoveg-sorszamnev” teendőjének hibái (az olvasati döntések Attiláéi,
        2026-11-18: a magánhangzós betűjel minden helyzetben „a.:”, „e.:” alakú, a mássalhangzós a nevével olvasandó).
Kilépési kód: 0, ha minden eset helyes; 1, ha bármelyik hibás. Az utolsó sor: „hangszöveg-teszt: N eset, hibás: M”.
A statikus hangra/blokk_hang esetek a tetelsor/hangszoveg_esetek.json-ban vannak (A/1: Ptk.-számozás).
"""
import json, os, sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import hangszoveg as h
import kozos

ESETEK_FAJL = os.path.join(kozos.GYOKER, 'tetelsor', 'hangszoveg_esetek.json')
_FN = {'hangra': h.hangra, 'blokk_hang': h.blokk_hang}


def esetek_betolt():
    """[[csoport, "hangra"|"blokk_hang", bemenet, várt], …] a tételsor esetfájljából."""
    return json.load(open(ESETEK_FAJL, encoding='utf-8'))


def darab_esetek():
    """11. daraboló: a darabhatár nem esik egy bekezdés pontjai közé, ha a bekezdés elfér; a mai garanciák maradnak."""
    ki = []
    bev = 'X' * 2000 + ' feltétellel, ha'
    a = 'a.: ' + 'y' * 1200 + ', és'
    b = 'bé.: ' + 'z' * 1200 + '...'
    elo = 'E' * 1500 + '...'
    d = h.darabol([elo, bev, a, b])
    ki.append(('11', 'pontok egy darabban', any(a in x and b in x for x in d), True))
    ki.append(('11', 'a bevezető a pontjaival', any(bev in x and a in x for x in d), True))
    ki.append(('11', 'darab legfeljebb 4600', all(len(x) <= 4600 for x in d), True))
    # ha a bekezdés a pontjaival együtt sem fér el egy darabban, a pontok között vághat (de a darab nem lépi túl a határt)
    nagy = [bev] + ['a.: ' + 'q' * 2000 + ';', 'bé.: ' + 'w' * 2000 + ';', 'cé.: ' + 'r' * 2000 + '.']
    d2 = h.darabol(nagy)
    ki.append(('11', 'túl hosszú bekezdés: határon belül', all(len(x) <= 4600 for x in d2) and len(d2) >= 2, True))
    # doboz: a fej az első résszel marad
    fej = 'A Polgári Törvénykönyv hatodik könyv első paragrafusa...'
    doboz = fej + '\n\n' + '\n'.join(f'{w}. ' + 'v' * 1400 + '...' for w in ('Egyes', 'Kettes', 'Hármas', 'Négyes', 'Ötös'))
    d3 = h.darabol([doboz])
    ki.append(('11', 'doboz feje az első résszel', d3[0].split('\n\n', 2)[1] == fej and 'Egyes.' in d3[0], True))
    # a doboz egy bekezdésének pontjai: a bekezdés (pontjaival) egy részben marad, ha elfér
    doboz2 = fej + '\n\nEgyes. ' + 'v' * 2500 + '...\nKettes. A feltételek:\na.: ' + 'p' * 900 + ';\nbé.: ' + 'k' * 900 + '...'
    d4 = h.darabol([doboz2])
    ki.append(('11', 'doboz bekezdése a pontjaival', any('a.: ' + 'p' in x and 'bé.: ' + 'k' in x for x in d4), True))
    return ki


def hangulat_esetek():
    """Hangulatcímkék (2026-11-18): címke csak hangulatváltásnál; a pont és a doboz normasora címkét nem kap; idempotens."""
    be = ['Első. A FOGALOM...', 'A szabály lényege a következő...', 'A Polgári Törvénykönyv hatodik könyv első paragrafusa...\n\nEgyes. A kötelem...',
          'A magyarázat folytatódik...', 'További magyarázat...', 'A szerződés semmis, ha jogszabályba ütközik...', 'a.: első pont;',
          'Így például a bérlő fizet...', 'Második. ELHATÁROLÁSOK...', 'A bérlet és a haszonbérlet közel áll egymáshoz...', 'Alcím...']
    vart = ['Első. A FOGALOM...', '[calm] A szabály lényege a következő...', '[serious] A Polgári Törvénykönyv hatodik könyv első paragrafusa...\n\nEgyes. A kötelem...',
            '[calm] A magyarázat folytatódik...', 'További magyarázat...', '[emphatic] A szerződés semmis, ha jogszabályba ütközik...', 'a.: első pont;',
            '[curious] Így például a bérlő fizet...', '[short pause] Második. ELHATÁROLÁSOK...', '[thoughtful] A bérlet és a haszonbérlet közel áll egymáshoz...', 'Alcím...']
    tip = [None] * 10 + ['alcim']
    kap = h.hangulat(be, tipusok=tip)
    return [('hangulat', 'alapeset', kap, vart), ('hangulat', 'idempotens', h.hangulat(kap, tipusok=tip), vart),
            ('hangulat', 'vázlat alaphang', h.hangulat(['Kulcsmondat...', 'Tilos a joggal való visszaélés...', 'Újabb mondat...'], alap='serious', kezdo='serious'),
             ['Kulcsmondat...', '[emphatic] Tilos a joggal való visszaélés...', '[serious] Újabb mondat...']),
            ('hangulat', 'hosszú bekezdés nem dobozfej', h.hangulat(['A szabály a hatodik könyvben áll... Ezt mondja ki az első paragrafus...'])[0][:6], '[calm]')]


def main():
    if not os.path.isfile(ESETEK_FAJL):
        print('hangszöveg-teszt: nincs esetfájl')
        sys.exit(0)
    hibas = 0; db = 0
    for csop, fajta, be, vart in esetek_betolt():
        db += 1
        try:
            kap = _FN[fajta](be)
        except SystemExit as e:
            kap = f'<SystemExit: {e}>'
        if kap != vart:
            hibas += 1
            print(f'HIBA [{csop}] {be!r}\n   várt: {vart!r}\n   kapott: {kap!r}')
    for csop, nev, kap, vart in darab_esetek() + hangulat_esetek():
        db += 1
        if kap != vart:
            hibas += 1
            print(f'HIBA [{csop}] {nev}')
    print(f'hangszöveg-teszt: {db} eset, hibás: {hibas}')
    sys.exit(1 if hibas else 0)


if __name__ == '__main__':
    main()
