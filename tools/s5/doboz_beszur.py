#!/usr/bin/env python3
"""Egy jogszabálydoboz beszúrása a tételbe a korpuszból (KE-3/5).

    python3 tools/s5/doboz_beszur.py NN "<forráskód> <egység> [(bek.)…]" --utan "<a tételfájl egy sorának pontos kezdete>" [--ir]

Példák: "Pp 8. § (1)-(2)", "Vht 47. §", "EUMSZ 288. cikk", "(EU) 2016/679 5. cikk (1)"; a dobozfejléc alakja („Pp. 8. §”,
„GDPR 5. cikk”) is elfogadott. A doboz fejléce a forrás dobozfejléc-rövidítésével készül (a tételsor dobozaiban
leggyakoribb alak, ennek hiányában a beállítás dobozRovidites első alakja).

A doboz a korpuszból épül, ugyanazzal a kóddal, mint a doboz_javit újraépítése és az s5/alkalmaz.py @DOBOZ eleme
(s5/doboz_javit.doboz_epit), és a megadott sor UTÁN kerül a tételfájlba, a meglévő dobozok formájában (fejléc, üres sor,
bekezdésenként egy sor üres sorokkal elválasztva; előtte és utána üres sor). --ir nélkül csak megmutatja.

Hiba (kilépési kód 1, írás nélkül): ismeretlen forrás; a korpuszban nem létező egység vagy bekezdés; nem található vagy
nem egyértelmű --utan sor; a --utan sor doboz belsejében áll; a doboz (ugyanaz az egység, átfedő bekezdésekkel) már
szerepel a tételben; a beszúrt doboz visszaolvasva (kozos.dobozok) nem pontosan a beszúrt sorokat adja.
"""
import os, re, sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import kozos
import doboz_javit as dj
import koteg


def hiba(uzenet):
    print('doboz_beszur: HIBA: ' + uzenet)
    raise SystemExit(1)


def argumentumok(argv):
    ir, utan, poz = False, None, []
    i = 0
    while i < len(argv):
        a = argv[i]
        if a == '--ir':
            ir = True
        elif a == '--utan':
            if i + 1 >= len(argv):
                hiba('a --utan után hiányzik a sor kezdete')
            utan = argv[i + 1]; i += 1
        elif a.startswith('--utan='):
            utan = a.split('=', 1)[1]
        elif a in ('-h', '--help'):
            print(__doc__); raise SystemExit(0)
        else:
            poz.append(a)
        i += 1
    if len(poz) != 2 or not poz[0].isdigit() or utan is None or not utan.strip():
        print('használat: python3 tools/s5/doboz_beszur.py NN "<forráskód> <egység> [(bek.)…]" --utan "<sor kezdete>" [--ir]')
        raise SystemExit(1)
    return int(poz[0]), poz[1].strip(), utan, ir


def rovidites(kod):
    """A forrás dobozfejléc-rövidítése: a tételsor dobozaiban leggyakoribb alak, vagy a beállítás első mintájából."""
    db = {}
    for f in sorted(os.listdir(kozos.GYOKER)):
        if re.fullmatch(r'\d{2}\.txt', f):
            for l in open(os.path.join(kozos.GYOKER, f), encoding='utf-8').read().split('\n'):
                m = kozos.doboz_fej(l)
                if m and kozos.fejlec_kod(m)[0] == kod:
                    db[m.group(1)] = db.get(m.group(1), 0) + 1
    if db:
        return max(db, key=lambda x: (db[x], -len(x)))
    for rx, k in kozos.DOBOZ_RÖVIDITES:
        if k == kod:
            alak = re.sub(r'\\(.)', r'\1', rx)
            if re.fullmatch(rx, alak):
                return alak
    return None


def fejlec(kert):
    """A kért doboz fejléce: „<forráskód> <egység> …” vagy maga a dobozfejléc. Vissza: (fejléc, forráskód)."""
    kert = re.sub(r'\s+', ' ', kert)
    m = kozos.doboz_fej(kert)
    if m:
        return kert, kozos.fejlec_kod(m)[0]
    F = kozos.forrasok()
    kodok = set(F) | {k for _, k in kozos.DOBOZ_RÖVIDITES}
    kod = next((k for k in sorted(kodok, key=len, reverse=True) if kert.startswith(k + ' ')), None)
    if kod is None:
        hiba('ismeretlen forrás: ' + kert)
    rov = rovidites(kod)
    if rov is None:
        hiba('a forrásnak (%s) nincs dobozfejléc-rövidítése a beállításban (dobozRovidites)' % kod)
    fej = rov + ' ' + kert[len(kod) + 1:].strip()
    if not kozos.doboz_fej(fej):
        hiba('a fejléc nem értelmezhető, vagy az egysége nem a forrásé (%s): %s' % (kozos.egyseg(kod), fej))
    return fej, kod


def bekezdesek(fej, m):
    """A fejlécben kért bekezdések halmaza, vagy None (a teljes egység)."""
    ki = set()
    for a, b in re.findall(r'\((\d+[a-z]?)\)(?:\s*[–-]\s*\((\d+[a-z]?)\))?', fej[m.end(3):]):
        if b and a.isdigit() and b.isdigit():
            ki.update(str(x) for x in range(int(a), int(b) + 1))
        else:
            ki.update(x for x in (a, b) if x)
    return ki or None


def main():
    n, kert, utan, ir = argumentumok(sys.argv[1:])
    ut = os.path.join(kozos.GYOKER, '%02d.txt' % n)
    if not os.path.isfile(ut):
        hiba('nincs ilyen tétel: %s' % os.path.basename(ut))
    fej, kod = fejlec(kert)
    if kod not in kozos.forrasok():
        hiba('ismeretlen forrás (nincs a tetelsor/forrasok.json-ban): ' + kod)
    sorok, ok = dj.doboz_epit(fej)
    if sorok is None:
        hiba(ok)
    m = kozos.doboz_fej(fej)
    _, par = kozos.fejlec_kod(m)
    txt = open(ut, encoding='utf-8').read()
    L = txt.split('\n')
    # a doboz már szerepel-e: ugyanaz az egység, átfedő bekezdésekkel (bekezdés nélküli fejléc: a teljes egység)
    uj_bek = bekezdesek(fej, m)
    for k, p, f, _ in kozos.dobozok(txt):
        if (k, p) == (kod, par):
            regi_bek = bekezdesek(f, kozos.doboz_fej(f))
            if uj_bek is None or regi_bek is None or uj_bek & regi_bek:
                hiba('a doboz már szerepel a tételben: %s' % f)
    # a --utan sor
    talalt = [i for i, l in enumerate(L) if l.strip() and l.strip().startswith(utan.strip())]
    if not talalt:
        hiba('nem található --utan sor: %s' % utan[:80])
    if len(talalt) > 1:
        hiba('nem egyértelmű --utan sor (%d találat: %s. sor): %s' % (len(talalt), ', '.join(str(i + 1) for i in talalt[:8]), utan[:80]))
    i = talalt[0]
    for h, idx in koteg.doboz_sorok(txt):
        if idx and h <= i < idx[-1]:
            hiba('a --utan sor (%d.) doboz belsejében áll (a doboz: %d–%d. sor)' % (i + 1, h + 1, idx[-1] + 1))
    blokk = []
    for k, s in enumerate(sorok):
        if k:
            blokk.append('')
        blokk.append(s)
    elotte = [''] if L[i].strip() else []
    utana = [''] if i + 1 < len(L) and L[i + 1].strip() else []
    uj_L = L[:i + 1] + elotte + blokk + utana + L[i + 1:]
    uj_txt = re.sub(r'\n{3,}', '\n\n', '\n'.join(uj_L))
    # visszaolvasás: a beszúrt doboz pontosan a beszúrt sorokat adja-e (a doboz utáni szöveggel együtt)
    vissza = [d for d in kozos.dobozok(uj_txt) if d[2] == fej]
    if len(vissza) != 1 or vissza[0][3] != sorok[1:]:
        tobb = vissza and len(vissza[0][3]) > len(sorok) - 1
        hiba('a beszúrt doboz visszaolvasva eltér%s – nem beszúrva' % (' (a doboz utáni szöveg is a dobozhoz kerülne)' if tobb else ''))
    print('%02d.txt, a %d. sor után („%s”):' % (n, i + 1, L[i].strip()[:70]))
    print('')
    for s in blokk:
        print('  ' + s if s else '')
    print('')
    if ir:
        open(ut, 'w', encoding='utf-8').write(uj_txt)
        print('doboz_beszur: beszúrva: %s (%d sor, %d karakter)' % (fej, len(sorok) - 1, sum(len(s) for s in sorok[1:])))
    else:
        print('doboz_beszur: próbafutás (--ir nélkül): %s (%d sor, %d karakter)' % (fej, len(sorok) - 1, sum(len(s) for s in sorok[1:])))


if __name__ == '__main__':
    main()
