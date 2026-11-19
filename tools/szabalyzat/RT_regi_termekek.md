# RT – a régi termékek tartalmi javítása a lezárt tételhez (javító ügynök, javítókör, független audit; minden tételsorra)

**Hely:** `<tételsor-tároló>/tools/szabalyzat/RT_regi_termekek.md` – a közös eszközkészlet zárolt másolata, helyben nem módosítható (`python3 tools/eszkoz_ellenor.py` → eltérés 0). **Karbantartja:** a központi chat (a közös készletben). **Vezérutasítás:** `tools/szabalyzat/00_GYARTASI_SZABALYZAT.md` (S6 fejezet). **Kapcsolódó:** `tools/szabalyzat/TG_termekgyartas.md` (a továbbiakban: TG).
**Tárgy:** a régi, ma is élő termékek – kvíz (`kviz/NN/`), tanulókártya (`tanulokartyak/NN/`), hézagpótló (`hezagpotlok/NN/`), memóriaútvonal (`memoriautvonal/NN/`) – összevetése a lezárt tétellel, és a jogi hibák javítása ugyanabban a menetben. **Kinek szól:** A. fejezet – a javító ügynöknek (Cursor), a javítókörben is; B. fejezet – a független auditornak és a javítókörnek.
**A feladatlap megadja:** a munkaágat (`rt-<tételek>`), az első köteg tételeit, javítókörnél a lelet pontjait. A célág a `tetelsor/beallitas.json` `celag` kulcsa; az ellenőrző alapja a beállítás `rt2Alap` kulcsa (a célág rögzített commitja a javítás előtt).

# A. fejezet – a javító ügynök

## A1. Tilalmak

1. Böngészőt, megjelenítőt nem nyitsz, képernyőképet nem készítesz.
2. Adatbázist és Storage-ot nem írsz; importot, telepítést, `firebase`-parancsot nem futtatsz; hangot nem generálsz.
3. A `main` ágat és a célágat (`celag`) nem érinted: nem töltesz fel rájuk, nem fésülsz be. A célágra csak Attila `tools/befesul.sh` parancsa tölt fel. Feltöltés csak a saját munkaágra.
4. `git add -A` tilos.
5. A `tools/` mappa a közös készlet zárolt másolata, nem módosítható (`python3 tools/eszkoz_ellenor.py` → `eszkoz_ellenor: fájl N, eltérés 0`); a `tools/rt2_ellenor.py` a készlet része, nem te írod.
6. A tárolóba nem kerülhet kulcs, `service-account.json`, felhasználói adat, mp3.
7. A `hangmeta.py` és a `hangulat_szoveg.py` kizárólag a beállítás `hangAlapAgak` szerinti `--alap=` kapcsolóval futhat (ebben a munkában nem kell futtatni).
8. Tiltott szavak bármely szövegben: „tananyag”, „ZH-felkészítő”; a tételszövegben a „korpusz” szó nem állhat. Minden program, az eldobható szkript is, Python 3.9-en fut.
9. Nem módosítod: `NN.txt`, `termekek/`, `tts/`, `kontroll/`, `korpusz/`, `tetelsor/`, `tools/`, `ALLAPOT.md`. Csak a négy régi termékmappa szövegmezőit (A5) és a `jelentesek/RT-2_*` fájlokat írod.
10. A mérce a lezárt tétel (`NN.txt`, a jogszabálydobozokkal) és a `korpusz/` szövege. Tankönyv, kommentár, MeRSZ, web nem forrás; új jogi állítást nem írsz.

## A2. Indulás

```
git status --short                          # várt: üres; ha nem: STOP
git fetch origin
git switch -c <munkaág> origin/<celag>      # javítókörnél: git switch <munkaág> (folytatod)
git log --oneline -1
python3 tools/eszkoz_ellenor.py             # várt utolsó sor: eszkoz_ellenor: fájl N, eltérés 0
```
Ha a feladatlap megadja a célág várt csúcsát, és a `git log` mást mutat: STOP, jelzed Attilának.

## A3. A módszer: olvasás, nem gépi mintakeresés

1. **Program nem sorolhat be elemet.** Programot csak arra használsz, hogy az elemeket olvasható formában kilistázd, a javítást a fájlba írd, és a végén ellenőrizz. Minden elem sorsáról az dönt, aki az elemet és a tételt elolvasta. Gépi besorolás (kulcsszó-, §- vagy sorszámnév-egyezés) nem használható.
2. Tételenként:
   1. Elolvasod a teljes `NN.txt`-t, a jogszabálydobozokkal együtt.
   2. Elolvasod a tétel mind a négy termékének **minden** elemét:
      - `kviz/NN/*.json` → `questions[]`: `question`, minden `options[].text` az `isCorrect` jelöléssel, `options[].rationale`;
      - `tanulokartyak/NN/*.json` → `flashcards[]`: `front`, `back`, `explanation`;
      - `hezagpotlok/NN/*.json` → `items[]`: `text` a kitöltött `blanks[].answer` értékekkel, `distractors`, `cimke`;
      - `memoriautvonal/NN/allomasok/*.json` → `cim`, `kulcsszo`, `tartalom`; és az `utvonal.html`.
   3. Minden elemnél egy kérdésre felelsz: **van-e benne olyan jogi állítás, amely a tétel egy mondatával vagy a korpusz egy §-ával ellentétes?**
3. Ha egy hibát egy elemben javítasz, a tétel minden elemét végigolvasod ugyanerre a hibára, és mindenütt egyformán javítod.
4. Alügynököt használhatsz; rá ugyanez a szabályzat vonatkozik (böngészőt ő sem nyithat), és a munkájáért te felelsz. Mintavétel nincs: ha egy tétel elemeit nem olvastad el mind, a tétel nincs kész, és a jelentésben nem szerepelhet késznek.

## A4. Mi hiba, mi nem

**Hiba (javítandó):**
1. hibás szám, határidő, életkor, százalék, értékhatár;
2. hibás vagy hiányzó feltétel, amely az állítást hamissá teszi; hibás jogkövetkezmény; a főszabály és a kivétel felcserélése;
3. az elem a megjelölt §-nak olyan tartalmat tulajdonít, amelyet a korpusz szerint az a § nem mond;
4. kvíz: a helyesnek jelölt válasz a tétel szerint hamis, vagy a hamisnak jelölt válasz a tétel szerint igaz; az indokolás a tétellel ellentétes, vagy nem igazolja a jelölést;
5. hézagpótló: a kitöltött mondat a tétel szerint hamis, vagy egy elterelő (`distractors`) a tétel szerint szintén helyes megoldás;
6. hatályon kívül helyezett vagy módosított szabály hatályosként; ha a tétel a régi és az új szabályt időbeli hatály szerint különíti el, az elem az időbeli határ nélkül.

**Nem hiba (nem nyúlsz hozzá):**
1. **Szóhasználat.** A szakszó és a latin megjelölés (kógens, diszpozitív, objektív, konstitutív, taxatív, ex tunc, ex nunc, ipso iure, sui generis, lex specialis stb.), a „jogbiztonság”, „egyik legfontosabb”, „mindenek felett álló” jellegű fordulat a régi termékben marad. Kivétel: ha a megjelölés maga hamis állítást hordoz (pl. jogvesztőnek nevez egy elévülési határidőt) – az hiba.
2. Az elem olyan §-ra hivatkozik, amelyet a tétel nem idéz, de a korpusz szerint a hivatkozás helyes.
3. Az elem a tétel által nem tárgyalt, de a korpusz szerint helyes szabályt mond.
4. A korábbi jogszabály megnevezése korábbi jogként, ha az elem nem hatályos szabályként állítja.
5. Stílus, szórend, tömörség, a tételtől eltérő megfogalmazás.

**Nem ellenőrizhető:** ha egy jogi állítást sem a tételből, sem a korpuszból nem tudsz megítélni, nem javítod: a `jelentesek/RT-2_nem_ellenorizheto.json` listájába kerül (azonosító, az állítás, miért nem ítélhető meg). Egy azonosító nem állhat egyszerre ezen a listán és a javítások naplójában.

## A5. A javítás szabályai (kötöttségek)

1. Csak szövegmező változhat: `question`, `options[].text`, `options[].rationale`, `front`, `back`, `explanation`, `text`, `blanks[].answer`, `distractors[]`, `cimke`, `cim`, `kulcsszo`, `tartalom`, és az `utvonal.html` megfelelő szövege. A `question` csak akkor változik, ha a kérdés maga hamis előfeltevésre épül; a javítókörben csak a leletben megnevezett kérdésnél.
2. Nem változhat: fájlnév, azonosító, a tömbök **hossza és sorrendje** (az elemszám), a kulcsok, az `isCorrect` értéke (**a helyes válasz jelölése**), a `__[bN]__` hézagpótló-helyek száma és sorrendje, az `utvonal.meta.json`. Hibás `isCorrect` esetén a válasz szövegét igazítod úgy, hogy a jelölés helyes legyen. (Az `utvonal.meta.json` `htmlSha256` mezőjének eltérése a javított HTML-től várt, nem hiba.)
3. **Nyers szövegcsere:** a fájlban csak a javított mező szövege cserélődik; a JSON-t nem formázod újra, más bájt nem változik.
4. A javítás a legkisebb: csak a hibás tagmondat változik, a tétel megfelelő mondata alapján, saját megfogalmazásban. Elemet nem törölsz és nem veszel fel. A javítás sem állíthat olyat, amit a tétel vagy a korpusz nem mond.
5. Ha egy állomás (`allomasok/KK.json`) szövege változik, ugyanaz a szöveg az `utvonal.html`-ben is változik; a `kulcsszo` nem mondhat ellent a javított tartalomnak.
6. Kvíz: egy kérdésen belül két válasz szövege nem lehet azonos; a hamis jelölésű válasz indokolása nem kezdődik „IGAZ”-zal, az igazé nem „HAMIS”-sal, és a hamis válasz hamisságát a saját állítására indokolja. Ha a hamis válasz a javítás után nem egyértelműen hamis, a szövegét egyértelműen hamis állítássá írod (pl. „A törvény kifejezetten kimondja, hogy …”, ahol a tétel szerint a törvény ilyet nem mond).
7. Ha egy elem egész tárgya hibás, és a legkisebb javítással nem menthető: nem írod át; a naplóban `"tipus": "kozponti_dontes"` jelzéssel, javaslattal szerepel (a fájl változatlan).
8. **Megálló:** ha egy tételben a javított elemek aránya meghaladja a 15%-ot, annál a tételnél megállsz, a javításokat nem írod fájlba, és a jelentésben jelzed – az újragyártásról a központi chat dönt. A megálló alól csak a feladatlap mentheti fel a tételt, központi döntéssel.

## A6. Napló

`jelentesek/RT-2_javitasok.json` – lista, javított mezőnként pontosan egy bejegyzés:
```json
{"azonosito": "kviz/NN/kerdes_….json#15", "mezo": "options[2].rationale", "regi": "…", "uj": "…",
 "tipus": "szam|feltetel|jogkovetkezmeny|paragrafus|kviz_jeloles|elterelo|hatalyossag|kozponti_dontes",
 "bizonyitek": {"forras": "NN.txt", "idezet": "a tétel vagy a korpusz mondata szó szerint"}}
```
A `bizonyitek.forras` egy tételfájl (`NN.txt`) vagy egy korpuszfájl neve; az `idezet` abban szó szerint megtalálható, legalább 40 karakter. A `regi` és az `uj` betűre egyezik a fájl régi és új értékével.

`jelentesek/RT-2_olvasas.json` – tételenként: `{"tetel": NN, "elemek": {"kviz": n, "tanulokartyak": n, "hezagpotlok": n, "memoriautvonal": n}, "elolvasva": true, "javitott_elem": n, "nem_ellenorizheto": n}`.

`jelentesek/RT-2_nem_ellenorizheto.json` – az A4 szerinti lista.

## A7. Kapu

```
python3 tools/rt2_ellenor.py                # várt utolsó sor: rt2_ellenor: tétel N, javított mező M, hiba 0
bash tools/kapuk.sh --visszaallit            # várt utolsó sor: KAPUK: 12 futott; eltérés/hibás: 0
```
Az `rt2_ellenor.py` a beállítás `rt2Alap` commitjához hasonlít (más alap: `--alap=<commit>`, csak a feladatlap szerint), és hibának veszi: a négy mappában fájl eltűnt vagy keletkezett; érvénytelen JSON; nem szövegmező, kulcs, tömbhossz változott; változott mező naplóbejegyzés nélkül, vagy fordítva; kétszeres bejegyzés; a napló `regi`/`uj` értéke eltér a fájltól; az idézet rövid vagy nincs a forrásban; tiltott szó; a hézag helye változott; `kozponti_dontes` elem mégis változott; az állomás új szövege nincs az `utvonal.html`-ben; azonos opciószöveg; „IGAZ”/„HAMIS” kezdetű indokolás a jelöléssel ellentétesen; rontott kötés („és és”, „., ”, „, ;”); azonosító mindkét listában; hiányzó vagy késznek nem jelölt tétel, eltérő elemszám az olvasási naplóban. A „LISTA: vessző után nagybetű” sorokat végignézed; a döntés a tiéd. A beszélgetésbe és a jelentésbe a kapukból csak az utolsó sor kerül.

## A8. Menetrend

1. **Első köteg:** a feladatlap által megadott tételek (ha van ismert hibájú tétel, az elöl). Utána A7, commit, feltöltés, jelentés – és **megállsz**. A központi chat a javítások diffjét és a naplót auditálja (B. fejezet); csak az „RT-2 folytatható” válasz után mész tovább.
2. Folytatás hat tételes kötegekben, kötegenként egy commit és feltöltés; megálló csak az A5/8. pont esetében vagy kapuhibánál.
3. A végén: `python3 tools/rt2_ellenor.py`, `python3 tools/kontroll.py kapu`, `bash tools/kapuk.sh --visszaallit`, zárójelentés.

## A9. Commit, feltöltés, jelentés

```
git add kviz tanulokartyak hezagpotlok memoriautvonal jelentesek
git status --short                           # tiltott fájl nincs köztük
git commit -m "RT-2: a régi termékek tartalmi javítása – <tételek> (<M> javított mező)"
git diff --name-only origin/<celag> HEAD | grep -iE '\.mp3$|service-account|\.pem$|\.key$|\.env$'   # várt: üres
git push origin <munkaág>:<munkaág>
```
**Jelentés:** `jelentesek/RT-2_regi_termekek_tartalmi_javitas.md`, első sora a `python3 tools/kontroll.py kapu` ÁLLAPOT-sora szó szerint. Tartalma, felsorolva:
- tételenkénti tábla: elemszám termékenként, javított elem, javított mező hibatípusonként, nem ellenőrizhető, központi döntést kérő;
- a 15%-ot meghaladó tételek (ha van);
- a megváltozott memóriaútvonal-állomások listája (a hangjuk miatt);
- tételenként kimondva, igaz-e: „mind az N elemet elolvastam”; ha alügynök olvasott, melyik tételt;
- az `rt2_ellenor` és a kapuk utolsó sora.

**Üzenet Attilának:** az ág neve, a commit, a javított mezők száma, és hogy az ág a központi chathez megy auditra. Befésülő parancsot nem adsz; azt az audit után a központi chat adja.

# B. fejezet – a független audit és a javítókör

## B1. A független audit

**Ki végzi:** a központi chat által indított audit-alügynök (nagy terjedelemnél kettő, tételtartomány szerint megosztva), a munkaág munkapéldányában. **Tilalmak:** az A1 pontjai; git-parancsból csak olvasót futtat (`status`, `diff`, `log`, `show`); fájlt nem módosít – leletet ad, a javítás a javítókörben történik.

**Mit olvas:**
1. a munkaág diffjét az `rt2Alap`-hoz és a naplót: **minden** naplóbejegyzést egyenként összevet a tétellel és a korpusszal (helytálló-e a javítás, nem állít-e újat, nem rontotta-e a szöveget, egyezik-e a bizonyíték);
2. a nem javított elemeket is: **a tétel minden elemét végigolvassa, a változatlanokat is** (mintavétel nincs); a leletben tételenként megadja, hány elemet olvasott;
3. minden javított hibatípusra megkeresi a tétel többi elemében ugyanazt a hibát (maradvány);
4. a `jelentesek/RT-2_nem_ellenorizheto.json` bejegyzéseit: megítélhető-e mégis a tételből vagy a korpuszból.

**Mit futtat:** `python3 tools/rt2_ellenor.py` (utolsó sor a leletbe).

**Leletosztályok:**
| Osztály | Mi |
|---|---|
| JOGI HIBA | az elem (vagy a javítás) a tétellel vagy a korpusszal ellentétes jogi állítást tartalmaz (A4 „Hiba” 1–6.) |
| PONTATLAN | nem ellentétes, de a mérce szerinti feltétel, megszorítás, időbeli hatály vagy a pontos jogkövetkezmény elmosódik, ezért félrevezet; ide tartozik az önmagában nem érthető pótlás |
| TÚLTERJESZKEDÉS | a javítás vagy az elem olyat állít, amit sem a tétel, sem a korpusz nem mond (új állítás; kategorikus kijelentés ott, ahol a tétel szerint a törvény nem dönt) |
| MARADVÁNY | ugyanaz a hiba, amelyet máshol javítottak, más elemben vagy mezőben megmaradt; a régi szöveg, régi jogkövetkezmény vagy ideiglenes mondat maradéka; a kulcsszó vagy az `utvonal.html` nem követi a javított állomást |
| NYELVI | szövegromlás: ismételt szó, rossz írásjel vagy névelő, szócsonk, duplázott vagy csonka tagmondat, rossz vonatkozás, alany nélküli mondat, azonos szövegű válaszok |

Szóhasználat (A4 „Nem hiba” 1.) nem lelet. A szükségtelen javítás (a régi szöveg helyes volt) lelet: visszaállítást kér.

**Lelet:** pontonként – azonosító (`kviz/NN/kerdes_….json#K [i]`, `tanulokartyak/NN/….json#<kártya-azonosító>`, `memoriautvonal/NN/allomasok/KK.json`), mező, osztály, mérce (`NN.txt` sora vagy a korpusz §-a, bekezdéssel), javaslat. Az első mondat az ítélet: „Nincs lelet.” vagy a leletek száma osztályonként. A minősítést („RT-2 folytatható”, javítókör kell, illetve „auditálva, befésülhető”) a központi chat adja.

## B2. A javítókör (a javító ügynök)

1. Ugyanazon a munkaágon folytatod (A2, `git switch <munkaág>`). A javítókör feladatlapját (a lelet pontjait) nem commitolod a munkaágra; a `/tmp` alól olvasod.
2. Az A. fejezet A1, A4–A7 pontja változatlanul érvényes. A `question` mező csak a leletben megnevezett kérdésnél változik.
3. Csak a lelet pontjaihoz nyúlsz; más tételhez, más elemhez nem. Minden pontnál megnyitod az elemet és a tétel megjelölt sorát; a megadott szöveg javaslat, a mérce a tétel és a korpusz.
4. Ahol a pont „minden elemben” keresést kér (MARADVÁNY), az érintett tétel **összes** elemét végigolvasod erre a hibára.
5. **Visszaállítás:** ahol a lelet szerint a régi szöveg helyes volt, a régi szöveget állítod vissza betűre, és a naplóbejegyzést törlöd.
6. A lelet szerint megítélhetővé vált elemet kiveszed a `RT-2_nem_ellenorizheto.json`-ból.
7. A 15%-os megálló a javítókörben is áll, kivéve, ha a feladatlap az adott tételre központi döntéssel felfüggeszti.
8. **Zárás:** `python3 tools/rt2_ellenor.py` (hiba 0), `bash tools/kapuk.sh --visszaallit`; a jelentés végére „Javítókör” szakasz: pontonként mi történt; a teljes átolvasásban talált további helyek; a megváltozott állomások frissített listája; a visszaállított bejegyzések. Egy commit: `RT-2 javítókör: az audit leletei (<M> mező)`; feltöltés a munkaágra (`git push origin <munkaág>:<munkaág>`). Attilának: az ág, a commit, a javított mezők új száma; az ág visszamegy a központi chathez.
9. A javítókör minden megváltozott mezőjét a központi chat olvassa át; az apró (írásjel-) javításokat maga végzi, a befésülhetőségről ő dönt.

## B3. Tipikus hibák (a javításban és az auditban erre figyelj)

1. **Következetlen javítás:** ugyanazt a hibát egyes elemekben javították, másokban bennhagyták (MARADVÁNY).
2. **Új állítás a javításban:** a pótlás olyat mond, amit a tétel nem (pl. egy felsorolásból kizárt esetet nevez meg, amelyet a tétel nem zár ki; megszűnés utáni kötelezettséget állít) (TÚLTERJESZKEDÉS).
3. **Kategorikus állítás, ahol a törvény nem dönt:** „taxatív”, „nem lehet alanya”, „csak akkor alkalmazható” – ha a tétel szerint a törvény ezt nem mondja ki (TÚLTERJESZKEDÉS vagy JOGI HIBA).
4. **A kvízjelölés és az indokolás elválik:** a javítás után a hamisnak jelölt válasz igaz lett, vagy az indokolás már nem igazolja a hamisságot; önellentmondó indokolás; „IGAZ”-zal kezdődő hamis indokolás (JOGI HIBA).
5. **Azonos szövegű válaszok:** ugyanazt a pótló mondatot több válaszba másolták (NYELVI).
6. **Pontatlan jogkövetkezmény:** a jogkövetkezmény rokon, de nem azonos (pl. „a bíróság pótolja a jognyilatkozatot” – a törvény szerint „a szerződést létrehozza”); a § helye téves (PONTATLAN vagy JOGI HIBA).
7. **Elhagyott feltétel:** a § feltétele csak egy pontra vonatkozik, a javítás általánosítja; a nyugvás vagy az átszállás feltétele kimarad (PONTATLAN).
8. **Régi jogkövetkezmény bennmarad:** a javított mondat mellett a régi szabály szerinti jogkövetkezmény is ott áll (MARADVÁNY).
9. **Időbeli hatály:** módosított szabály hatályosként, vagy időbeli határ nélkül; a beszúrt időbeli mondat önmagában nem érthető; ideiglenes időbeli mondat maradványa (JOGI HIBA, PONTATLAN, MARADVÁNY).
10. **Szövegromlás:** „és és”, „., ”, „, ;”, „a egyéves”, szócsonk, duplázott tagmondat, alany nélküli mondat, rossz főnévhez kapcsolódó vonatkozó mellékmondat, nem létező válaszra utalás („F opció”) (NYELVI).
11. **Állomás és útvonal:** a `tartalom` javítva, de a `kulcsszo` ellentmond neki, vagy az `utvonal.html` nem követi (MARADVÁNY).
12. **Szükségtelen javítás:** a régi szöveg helyes volt (pl. szóhasználat, helyes kártérítési utalás) – visszaállítás, a naplóbejegyzés törlése.
13. **Kettős nyilvántartás:** ugyanaz az azonosító a javítások naplójában és a nem ellenőrizhető listán.
