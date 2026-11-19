#!/usr/bin/env python3
"""S5 első kör az API-val, kötegben: a tételek átdolgozása (műveletlista) és az átdolgozott tétel ellenőrző olvasása.

A közös tools/api_koteg.py-t használja (keret, plafon, főkönyv, küldés, letöltés), azt nem módosítja: két feladatot ad hozzá.

    python3 tools/s5/koteg.py keszit atiras [--tetel=1,2,3]
    python3 tools/s5/koteg.py kuld atiras --plafon=60
    python3 tools/s5/koteg.py letolt atiras
    python3 tools/s5/alkalmaz.py --ir                    # a műveletek az NN.txt-be; a dobozokat a program írja a korpuszból
    python3 tools/s5/koteg.py keszit ellenorzo ; kuld ellenorzo --plafon=40 ; letolt ellenorzo

Attila döntése (2026-11-19, 14:37): az S5 első köre mind a 86 tételre kötegben fut; a kommentár és az IJOTEN ezután
tételenként csak eltéréslistát ad (az nem kerül API-kérésbe). A kérésbe csak a tároló saját tartalma megy: a kiírás,
a korpusz, a tétel munkaszövege (NN.txt) és az első olvasás lelete.
"""
import json, os, re, sys

def _gyoker():
    """A tételsor-tároló gyökere: az első szülőmappa, amelyben van tetelsor/beallitas.json."""
    d = os.path.dirname(os.path.abspath(__file__))
    while d != os.path.dirname(d):
        if os.path.isfile(os.path.join(d, 'tetelsor', 'beallitas.json')):
            return d
        d = os.path.dirname(d)
    raise SystemExit('nem találom a tételsor-tároló gyökerét (tetelsor/beallitas.json)')


GY = _gyoker()
sys.path.insert(0, os.path.join(GY, 'tools'))
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import api_koteg as ak
import alapfelvetel as af
import kozos
import doboz_javit as dj

MAX_KI = 64000          # a modell kimeneti korlátja 128 000 token (a gondolkodás is beleszámít); 32 000-nél 19 válasz csonkult
JEL = '⟦%d⟧ '          # ⟦n⟧ – a sor száma az NN.txt-ben (1-től)


def doboz_sorok(txt):
    """A dobozok sorai az NN.txt-ben: [(fejléc sorindexe, [a doboz sorainak indexei])], 0-tól."""
    L = txt.split('\n')
    H = [i for i, l in enumerate(L) if kozos.doboz_fej(l)]
    out = []
    for (kod, par, fej, sorok), h in zip(kozos.dobozok(txt), H):
        idx, j = [], h + 1
        for s in sorok:
            while j < len(L) and L[j].strip() != s and not L[j].strip().endswith(s):
                j += 1
            if j >= len(L):
                break
            idx.append(j); j += 1
        out.append((h, idx))
    return out


def szamozott(txt):
    """A tétel szövege sorszámozva; a dobozok fejléce és sorai megjelölve."""
    L = txt.split('\n')
    fej, test = set(), set()
    for h, idx in doboz_sorok(txt):
        fej.add(h); test.update(idx)
    ki = []
    for i, l in enumerate(L):
        if not l.strip():
            continue
        ki.append((JEL % (i + 1)) + ('[DOBOZ-FEJ] ' if i in fej else '[D] ' if i in test else '') + l.strip())
    return '\n'.join(ki)


def lelet(n):
    """A tétel lelete: ha van ellenőrző olvasás (az átdolgozott szövegre készült, a „hely” sorszám), az; különben az első olvasás."""
    for mappa, nev, fajta in (('ellenorzo', 'ell-%02d.json', 'ellenorzo'), ('elso_olvasas', 'elso-%02d.json', 'elso')):
        p = os.path.join(GY, 'jelentesek', 'api', mappa, nev % n)
        if os.path.exists(p) and not (fajta == 'ellenorzo' and '--elso-lelet' in sys.argv):
            d = json.load(open(p, encoding='utf-8'))
            d.pop('termekotletek', None); d.pop('dobozok', None); d.pop('elhatarolasok', None)
            if fajta == 'ellenorzo':
                # a javító körben a kiíráson kívüli pontok a kommentár-kör dolga: a kérésbe nem kellenek
                d['allitasok'] = [a for a in d.get('allitasok', []) if a.get('tipus') != 'KIIRASON_KIVUL']
            d['lelet_fajta'] = ('ellenőrző olvasás – a „hely” a (3) szöveg sorszáma' if fajta == 'ellenorzo'
                                else 'első olvasás – a „hely” címsor, az „idezet” a korábbi szövegből való')
            return d
    return None


def _roviditesek():
    """A §-okra és cikkekre tagolt források dobozfejléc-rövidítései a beállításból, egységgel és mintával:
    „Pp. (§: @DOBOZ Pp. 8. §)”, „EUMSZ (cikk: @DOBOZ EUMSZ 288. cikk)”, „Alaptörvény (cikk: @DOBOZ Alaptörvény XXVIII. cikk)”.
    Csak a beállítás forrasok tömbjében egységgel szereplő forrás kap rövidítést (a teljes fájlként előírt határozat nem)."""
    B = af.beallitas()
    egys = {f['kod']: f.get('egyseg') for f in B['forrasok'] if f.get('egyseg') in ('§', 'cikk', 'romaiCikk')}
    pelda = {'§': '%s 8. §', 'cikk': '%s 5. cikk', 'romaiCikk': '%s XXVIII. cikk'}
    ki, latott = [], set()
    for minta, kod in B.get('dobozRovidites', []):
        nev = re.sub(r'\\(.)', r'\1', minta)
        if kod in egys and re.fullmatch(r'[\w./() ]{2,40}', nev) and nev not in latott:
            latott.add(nev)
            ki.append('%s (%s: @DOBOZ %s)' % (nev, '§' if egys[kod] == '§' else 'cikk', pelda[egys[kod]] % nev))
    return ', '.join(ki)


ROVIDITESEK = _roviditesek()
TARGY = 'magyar polgári eljárásjog és kapcsolódó jogterületek' if af.beallitas().get('azon') == 'a2' else 'magyar jog – %s' % af.beallitas().get('kategoria', '')

RENDSZER_ATIRAS = """Jogi szakvizsga-felkészítő tétel szakmai kontrollját és mélyítését végzed (""" + TARGY + """). Négy szöveget kapsz: (1) a hivatalos kiírás tételét; (2) a tételhez előírt joganyag szövegét – ez a \
2026. december 9. utáni, HATÁLYOS állapot; (3) a tétel jelenlegi szövegét soronként számozva (⟦sorszám⟧); (4) a tétel \
leletét (a (2) ellen készült; a „lelet_fajta” mező mondja meg, hogy a „hely” címsor vagy sorszám).

A (3) szövegben a [DOBOZ-FEJ] sor egy jogszabálydoboz fejléce, az utána álló [D] sorok a doboz szövege. A dobozok szövege \
gépileg, betűre egyezik a hatályos joggal: a (2) rész mellett ez is mérce.

A FELADAT: műveletlistát adsz, amely a tételt a mérce szerint kijavítja és kiegészíti. A tételt NEM írod újra elölről: ami \
helyes és érdemi, az marad. Minden sorhoz, amelyhez nem adsz műveletet, a szöveg változatlan marad.

A MÉRCE – egy pont akkor kész, ha megvan benne:
1. a fogalom és a rendszertani hely;
2. a szabály magyarázata: hogyan működik, mi következik belőle (nem a normaszöveg megismétlése);
3. a joghatás, a kivételek, a határidők és a feltételek pontosan, a kapott joganyag szerint;
4. az elhatárolás a rokon intézményektől, ahol a kapott joganyag ezt megalapozza;
5. az előírt bírósági iránymutatás érdemi feldolgozása, ha a (2) részben szerepel;
6. a pontos normaszöveg dobozban;
7. csak hatályos jog; minden normatív állítás mögött doboz vagy a kapott joganyag egy helye áll.

MIT KELL TENNED:
- ELLENTMOND és ELAVULT_GYANU lelet: a hibás állítást javítsd a kapott joganyag szerint. Amit a hatályos szöveg már nem \
tartalmaz, azt töröld, és ha van helyébe lépő szabály, azt írd meg. Jogtörténeti vagy átmeneti megjegyzést ne írj, kivéve, \
ha a kapott szöveg maga tartalmaz átmeneti rendelkezést.
- PONTATLAN lelet: fogalmazd pontosra.
- Lefedettség „hianyzik” vagy „reszben”: írd meg a hiányzó részt a mérce szerint, dobozzal, a tétel logikájába illő helyre \
(szükség esetén új számozott alcímmel, a meglévő címek stílusában: csupa nagybetű).
- NEM_IGAZOLHATO és KIIRASON_KIVUL lelet: ha a kapott joganyag (a (2) rész és a dobozok) nem dönti el, NE nyúlj hozzá, és \
vedd fel a „nyitott” listára – ezeket később más forrásból ellenőrzik. Ha a kapott joganyag eldönti, javítsd.
- Távirati rész (jogszabály-felsorolás magyarázat nélkül), önjellemző vagy töltelék bevezetés: írd át érdemi magyarázattá, \
vagy töröld, ha nincs mögötte tartalom.
- A leleten túl is javíts minden olyan állítást, amely a kapott joganyaggal ellentétes.

SZIGORÚ SZABÁLYOK:
- Normatív állítást (ki, mit, mikor, milyen feltétellel, milyen joghatással) KIZÁRÓLAG a kapott joganyagból írhatsz. Saját \
tudásból nem egészítesz ki: bírósági gyakorlatot, határozatszámot, jogirodalmi álláspontot, más jogszabály tartalmát csak \
akkor említesz, ha a kapott anyagban szerepel. Ami nem igazolható, az nem kerül be.
- A magyarázat saját megfogalmazás; a normaszöveget nem ismétled prózában szó szerint (arra való a doboz).
- Példát csak a normából adj (a szabály alkalmazása egy egyszerű helyzetre), kitalált esetszámot, határozatot soha.
- Tilos szavak a szövegben: „korpusz”, „tananyag”, „ZH-felkészítő”, „kommentár”, „tankönyv”; a tétel nem beszél önmagáról \
(„ebben a tételben…”), és nem hivatkozik leletre, kiírásra, forrásfájlra.
- Dobozt NEM írsz ki szövegesen. Új dobozt így kérsz, külön elemként: „@DOBOZ Pp. 427. § (1)” vagy „@DOBOZ Vht. 92. §” vagy \
„@DOBOZ Pp. 500. § (2)-(3)” – a program a hatályos szöveget teszi a helyére. Csak teljes §-t vagy teljes bekezdés(eke)t \
kérhetsz, és csak olyat, amely a (2) részben szerepel. A cikkre tagolt forrásnál a fejléc „cikk” (pl. „@DOBOZ EUMSZ 288. cikk \
(2)”). Használható rövidítések (egységgel): """ + ROVIDITESEK + """. Más forrásból (bírósági iránymutatás, teljes \
fájlként előírt határozat vagy rendelet) új dobozt ne kérj; a meglévő dobozaik maradhatnak.
- Meglévő doboz sorait ([DOBOZ-FEJ], [D]) csak egyben törölheted (a fejléctől az utolsó [D] sorig); átírni nem lehet. \
Csonka idézés helyett kérj @DOBOZ-t, és töröld a régit.
- Egy bekezdés egy elem az „uj” tömbben; a bekezdésen belül nincs sortörés. Felsorolás helyett folyó szöveg, kivéve a \
meglévő szerkezetet követő rövid pontokat.
- A tartományok (tol–ig) nem fedhetik egymást; a sorszám a ⟦ ⟧ közötti szám.
- Terjedelem: annyi, amennyit a mérce megkíván; ne rövidíts jó részt, és ne írj tölteléket.

A válasz KIZÁRÓLAG egyetlen JSON-objektum, magyarázó szöveg nélkül:
{"tetel": <szám>,
 "muveletek": [
   {"tipus": "csere", "tol": 12, "ig": 12, "uj": ["új bekezdés", "@DOBOZ Pp. 8. § (1)"], "indok": "ELLENTMOND: …", "forras": "Pp. 8. § (1)"},
   {"tipus": "torles", "tol": 40, "ig": 44, "indok": "…", "forras": ""},
   {"tipus": "beszuras", "utan": 57, "uj": ["4. ÚJ ALCÍM", "bekezdés", "@DOBOZ Pp. 9. §"], "indok": "lefedettség: Pp. 9. § hiányzik", "forras": "Pp. 9. §"}],
 "nyitott": [{"sor": 33, "tipus": "NEM_IGAZOLHATO|KIIRASON_KIVUL", "kerdes": "mit kell ellenőrizni", "forras": "mely forrás döntené el"}],
 "osszegzes": "3–5 mondat: mi változott és mi maradt nyitva"}"""


def keres_atiras(t, modell, max_ki):
    n = t['sorszam']
    txt = kozos.tetel_szoveg(n)
    eloirt = af.eloirt_szoveg(t) or '(a kiírás ehhez a tételhez a korpuszban meglévő forrást nem jelöl meg)'
    le = lelet(n)
    tartalom = ('# (1) A KIÍRÁS TÉTELE\n%d. %s\n\n# (2) AZ ELŐÍRT JOGANYAG HATÁLYOS SZÖVEGE (2026. december 9. utáni állapot)\n%s\n\n'
                '# (3) A TÉTEL JELENLEGI SZÖVEGE (soronként számozva)\n%s\n\n# (4) A TÉTEL LELETE\n%s'
                % (n, t['szoveg'], eloirt, szamozott(txt),
                   json.dumps(le, ensure_ascii=False) if le else '(nincs lelet; a tételt a (2) rész ellen magad vesd össze)'))
    return {'custom_id': 'atir-%02d' % n,
            'params': {'model': modell, 'max_tokens': max(max_ki, MAX_KI), 'system': RENDSZER_ATIRAS,
                       'messages': [{'role': 'user', 'content': tartalom}]}}


RENDSZER_ELLENORZO = ak.RENDSZER.replace('magyar polgári eljárásjog és kapcsolódó jogterületek', TARGY).replace(
    'Jogi szakvizsga-felkészítő tétel első olvasását végzed',
    'Jogi szakvizsga-felkészítő tétel ÁTDOLGOZOTT szövegének független ellenőrző olvasását végzed').replace(
    '(3) a publikált jegyzet szövegét (a [DOBOZ] … [/DOBOZ] közötti rész szó szerinti jogszabály-idézet akar lenni).',
    '(3) az átdolgozott tétel szövegét soronként számozva (⟦sorszám⟧; a [DOBOZ-FEJ] és a [D] sorok jogszabálydobozok, '
    'ezek gépileg egyeznek a hatályos szöveggel: nem kell betűre ellenőrizned őket, és mérceként használhatod). '
    'A „hely” mezőbe a sor számát írd. A (2/b) rész ebben a feladatban üres. Külön figyelj arra, hogy a szöveg tartalmaz-e '
    'a kapott joganyagból nem igazolható bírósági gyakorlatot, határozatszámot vagy jogirodalmi állítást: ezt NEM_IGAZOLHATO-ként jelöld.')


def keres_ellenorzo(t, modell, max_ki):
    n = t['sorszam']
    eloirt = af.eloirt_szoveg(t) or '(a kiírás ehhez a tételhez a korpuszban meglévő forrást nem jelöl meg)'
    tartalom = ('# (1) A KIÍRÁS TÉTELE\n%d. %s\n\n# (2) AZ ELŐÍRT JOGANYAG HATÁLYOS SZÖVEGE (korpusz)\n%s\n\n'
                '# (2/b)\n(üres)\n\n# (3) AZ ÁTDOLGOZOTT TÉTEL\n%s'
                % (n, t['szoveg'], eloirt, szamozott(kozos.tetel_szoveg(n))))
    return {'custom_id': 'ell-%02d' % n,
            'params': {'model': modell, 'max_tokens': ak.max_ki_tetelre(t, max_ki), 'system': RENDSZER_ELLENORZO,
                       'messages': [{'role': 'user', 'content': tartalom}]}}


ak.FELADATOK['atiras'] = keres_atiras
ak.FELADATOK['ellenorzo'] = keres_ellenorzo

if __name__ == '__main__':
    ak.main()
