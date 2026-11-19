# TG – a lezárt tételek termékeinek gyártása (gyártó ügynök, Cursor; minden tételsorra)

**Hely:** `<tételsor-tároló>/tools/szabalyzat/TG_termekgyartas.md` – a közös eszközkészlet zárolt másolata, helyben nem módosítható (`python3 tools/eszkoz_ellenor.py` → eltérés 0). **Karbantartja:** a központi chat (a közös készletben). **Vezérutasítás:** `tools/szabalyzat/00_GYARTASI_SZABALYZAT.md` (S6 fejezet). **Kapcsolódó:** a munkaág auditja – `tools/szabalyzat/TG_ag_audit.md`; a régi termékek javítása – `tools/szabalyzat/RT_regi_termekek.md`.
**Kinek szól:** a gyártó ügynöknek (Cursor). **Indítás:** a feladatlap (az indító üzenet) megadja a tételek sorszámát (pl. „TG, tételek: 22, 23, 24, 25, 26, 27”), szükség esetén a záróköteg fajtáját (11. pont) és az élő hangágat (`<hangalap>`, lent).

## 0. Jelölések

- `NN` – a tétel kétjegyű sorszáma; `<tételek>` – a köteg sorszámai kötőjellel (pl. `22-23-24`).
- `<celag>` – a `tetelsor/beallitas.json` `celag` kulcsa. A munkaág mindig `origin/<celag>` friss távoli csúcsáról indul.
- Munkaág: `tg1-<tételek>` (pl. `tg1-22-23-24-25-26-27`), ha a feladatlap mást nem ad.
- `<azon>` – a beállítás `azon` kulcsa. Azonosító-minták: fogalommátrix `termekek/fogalommatrix/<azon>_NN_<azonosító>.json`; vázlat-hangdokumentum `hv_<azon>_NN`; csomag `ki/<azon>_termekcsomag.json`.
- `<hangalap>` – a beállítás `hangAlapAgak` listájának az élő hangot tükröző ága, amelyet a feladatlap megnevez (pl. `origin/hangpotlas-2-2026-11-12`).
- Egy termékköteg **legfeljebb 6 tétel**.

## 1. Cél

A megadott, szakmailag lezárt tételek minden terméke az új tételszöveghez igazodik: §-jegyzék, felsorolás, elhatárolások, döntési fa, számoló vagy rögzített ok, fogalommátrix minden elhatárolásra, hangos vázlat és vázlathang-szöveg, felolvasószöveg hangulatcímkékkel, jegyzet-HTML. Minden kapu 0 hibával fut, a köteg tételeinél 0 nyitott lefedettségi pár; a munka egy commitban áll a munkaágon, a munkaág fent van; jelentés készül.

## 2. Állandó tilalmak

1. Böngészőt, megjelenítőt nem nyitsz, képernyőképet nem készítesz.
2. Adatbázist és Storage-ot nem írsz; importot, telepítést, `firebase`-parancsot nem futtatsz; hangot nem generálsz.
3. A `main` ágat és a célágat (`celag`) nem érinted: nem töltesz fel rájuk, nem fésülsz be. A célágra csak Attila `tools/befesul.sh` parancsa tölt fel. Más ágat nem léptetsz, ágat nem törölsz. Hálózatot csak a `git fetch` és a saját munkaág feltöltése használ.
4. `git add -A` tilos; csak a 9. pontban felsorolt útvonalakat adod hozzá.
5. A `tools/` mappa a közös készlet zárolt másolata, nem módosítható; `python3 tools/eszkoz_ellenor.py` → `eszkoz_ellenor: fájl N, eltérés 0`. Egyetlen kivétel a helyi `tools/matrix_adat.py` (a tételsor kézi mátrixleírása): a végére írt új `mx(…)` bejegyzések és a köteg tételeinek saját `mx(…)` bejegyzései változhatnak.
6. A tárolóba nem kerülhet kulcs, `service-account.json`, felhasználói adat, mp3.
7. A `hangmeta.py` és a `hangulat_szoveg.py` kizárólag `--alap=<hangalap>` kapcsolóval futhat.
8. Tiltott szavak minden szövegben: „tananyag”, „ZH-felkészítő”. A tételszövegben a „korpusz” szó nem állhat.
9. Minden program, az eldobható szkript is, Python 3.9-en fut (például nincs birtokos ismétlés: `*+`, `++`).
10. **Nem módosítod:** `NN.txt`, `kontroll/`, `korpusz/`, `tetelsor/`, `kviz/`, `tanulokartyak/`, `memoriautvonal/`, `hezagpotlok/`, `ALLAPOT.md`, `jelentesek/KP-2_merce.md`, `jelentesek/koltseg_naplo.csv`, `utasitasok/`. A `termekek/_elesites_elott.json` teendőit nem zárod le (a központi chat zárja). Ha tételszöveg-hibát látsz: a jelentés „Központi teendő” pontjába írod.
11. Új jogi állítást nem írsz. A termék minden szövege a tétel mondata, a tétel jogszabálydoboza, vagy ezekből közvetlenül következő kérdés vagy címke. Tankönyvre, kommentárra, más forrásra a termék nem hivatkozik. Minden §-t a `korpusz/` fájljából olvasol ki, nem emlékezetből.
12. Eszközhibát nem foltozol: a jelentés „Központi teendő” pontjába írod; ha a hiba kaput buktat: STOP.
13. Idegen, nem commitolt változáshoz nem nyúlsz.

## 3. Előfeltétel és ág

```
git status --short                                   # várt: üres; ha nem: STOP
git fetch origin
git switch -c tg1-<tételek> origin/<celag>
python3 tools/eszkoz_ellenor.py                      # várt utolsó sor: eszkoz_ellenor: fájl N, eltérés 0
python3 tools/kontroll.py kapu NN [NN…]              # várt első sor: ÁLLAPOT: K/K tétel lezárva; … Minden tétel lezárva.
python3 tools/kontroll.py kapu | head -1             # jegyezd fel: a munka végén is betűre ez áll
```
STOP, ha: a feladatlap 6-nál több tételt ad; bármelyik tétel nincs lezárva a célág távoli csúcsán (a tételmunka még mentőágon van) – a tételhez nem nyúlsz.

**Minták:** a legutóbbi auditált köteg termékei, továbbá a beállítás `mintaTetelek` kulcsa szerinti tételek termékei (`fa`, `szamolo`, `matrix`, `vazlat`): döntési fa `termekek/dontesi_fa/`, mátrix a `tools/matrix_adat.py`-ban, számoló-indok a `termekek/lefedettseg_indok.json`-ban, kézi vázlatkijelölés a `termekek/hangos_vazlat/kezi.json`-ban, felolvasóterv a `tts/_ujra_terv.json`-ban. Az eszközök használata a `tools/*.py` fejlécében áll.

## 4. A gyártósor parancsai sorrendben

```
python3 tools/termek_gyart.py                                   # 5.1
python3 tools/elhatarolas_gyart.py                              # 5.1
                                                                # 5.2 döntési fa (kézzel), majd:
python3 tools/fa_ellenor.py
                                                                # 5.3 mátrix a tools/matrix_adat.py végén, majd:
python3 tools/matrix_ir.py
                                                                # 5.4 számoló vagy rögzített ok, majd:
python3 tools/szamolo_ellenor.py
python3 tools/vazlat_gyart.py NN --lista                        # 5.5
python3 tools/vazlat_kezi.py NN be=… ki=…
python3 tools/vazlat_gyart.py
python3 tools/hangszoveg.py lefed NN                            # 5.6
python3 tools/tts_ujra.py NN                                    # próba
python3 tools/tts_ujra.py NN --szoveg                           # teljes elolvasás
python3 tools/tts_ujra.py NN --ir
python3 tools/hangulat_szoveg.py --alap=<hangalap> --ir
python3 tools/hangmeta.py --alap=<hangalap>
python3 tools/vazlat_hang.py NN
python3 tools/vazlat_tts_terv.py
python3 tools/jegyzet_html.py --mind                            # 5.7
                                                                # 5.8 gyártásra váró lista
bash tools/kapuk.sh --visszaallit                               # 6.
```
A felolvasószöveg sorrendje (`tts_ujra.py --ir` → `hangulat_szoveg.py --ir` → `hangmeta.py` → `vazlat_hang.py` → `vazlat_tts_terv.py` → `jegyzet_html.py --mind`) kötött.

## 5. A termékek szabályai

### 5.1 Gépi termékek

A `termek_gyart.py` (§-jegyzék, felsorolás) és az `elhatarolas_gyart.py` (elhatárolások) futása után jegyezd fel tételenként a dobozok és az elhatárolás-bekezdések számát (`termekek/elhatarolasok/NN.json`).

### 5.2 Döntési fa (`termekek/dontesi_fa/<id>.json`)

1. Nézd meg a `termekek/dontesi_fa/index.json`-ban, van-e már fa a tételhez. A meglévő fát vesd össze az új szöveggel és a dobozokkal, és igazítsd (feltételek, határidők, kivételek).
2. Tételenként legalább egy fa kell, olyan kérdésre, amelyre a tétel dobozai feltételekhez kötött, egyértelmű választ adnak. Ha nincs ilyen: rögzített ok (`nincs-dontesi-helyzet` vagy más `KODOK` szerinti kód, 5.4).
3. Írás közvetlenül a JSON-ba, vagy a `tools/fa_ir.py` függvényeivel (`P(par, idezet, forras)`, `K`, `E`, `ir`) egy eldobható, **nem commitolt** szkriptből; a `P` forrásának alapértéke a beállítás `foKodex` kulcsa. Az azonosító ékezet nélküli, kötőjeles, beszédes.
4. Kötelező (a `fa_ellenor.py` fejléce szerint):
   - minden csomópontnak szó szerinti jogalapja van **a tétel saját dobozából**, egyértelmű §-, bekezdés- és pontmegjelöléssel; a törvényi idézetben a korpusz gondolatjele áll, nem kötőjel;
   - a csomópont szövegében csak az idézetben szereplő szám állhat; számított értéket a fa nem közöl, hanem a `szamolo` mezővel a számolóra utal;
   - minden eredményhez van példa; a példák saját, hétköznapi esetek (a tétel példája felhasználható, évszám nélkül), nyelvileg hibátlanok, és a megadott válaszokkal a megadott eredményre jutnak; bírói vagy hatósági mérlegelés eredménye a példában csak adott tényként szerepelhet, a törvény szavaival;
   - a nemleges ág eredménye is a §-ból következik.
5. Vitatott értelmezésből vagy bírói mérlegelésből nem készül ág; amit a fa nem dönt el, az a `megjegyzes` mezőbe kerül, a tétel mondataival.
6. Az `index.json`-t a `fa_ellenor.py` írja.

### 5.3 Fogalommátrix (`tools/matrix_adat.py` → `termekek/fogalommatrix/<azon>_NN_<azonosító>.json`)

1. A `termekek/elhatarolasok/NN.json` **minden** bekezdésére egy mátrix a `tools/matrix_adat.py` végén: `mx('<azonosító>', NN, cím, bevezető, sorcímke, sorok, oszlopok, cellák[, összegzés])`. A cella forrása a tétel egy teljes mondata, amelyet a megadott mondatkezdet pontosan egyszer azonosít.
2. Oszlop csak olyan szempont lehet, amelyről a bekezdés **mindkét** fogalomról mond valamit. Ha egy bekezdésnek nincs közös szempontja: rögzített ok `nincs-kozos-szempont` kóddal és `"elhatarolas": "<a bekezdés címe>"` mezővel.
3. **Címkeszabály** – a cella címkéje:
   - önmagában érthető, a mátrix megnyitása nélkül is (nem csonka mondatrész, nem félbehagyott felsorolás);
   - elején vagy végén nincs lógó kötőszó („és”, „vagy”, „de”, „illetve”, „mert”, „hogy”), és nincs benne a forrásmondat nélkül értelmetlen visszautalás („ez”, „ilyenkor”, „e szabály”, „a fenti”, „utóbbi”);
   - a sor kérdésére felel (ha a sor „Mikor keletkezik?”, a címke időpontot vagy feltételt mond, nem jogkövetkezményt);
   - hűen adja vissza a forrásmondatot (nem bővít, nem általánosít, feltételt nem hagy el), és a megfelelő sorhoz és oszlophoz tartozik.
4. A bevezető és az összegzés a tétel szövegéből következik.
5. Ha a tételhez régi mátrix tartozik (a `matrix_adat.py`-ban `NN` tételszámmal), vesd össze az új szöveggel; ha a forrásmondata megszűnt, a `matrix_ir.py` hibát jelez: a bejegyzést az új mondathoz igazítod, vagy ha a tartalma kikerült a tételből, törlöd, és a jelentésben felsorolod.
6. Gyártás: `python3 tools/matrix_ir.py` (szűrve: `python3 tools/matrix_ir.py NN [NN…]`).

### 5.4 Számoló vagy rögzített ok

1. **Számoló** (`termekek/szamolo/<id>.json`) készül minden olyan szabályhoz a tétel dobozában, ahol a törvény feltételtől függően legalább két számszerű érték (határidő, tartam, életkor, hányad) vagy kezdőpont közül választ, bírói mérlegelés nélkül.
2. Számoló nem készül: egyetlen küszöbértékhez (azt döntési fa kérdése kezeli); bírói vagy hatósági mérlegelésen múló szabályhoz („különös méltánylás”, „általában”, „indokolt esetben”); ha a doboz a szabályt nem tartalmazza.
3. Formátum (a `szamolo_ellenor.py` fejléce és a meglévő számolók szerint): bemenet logikai és egész; a szabály `alap` idézete szó szerinti; minden szabályhoz legalább egy példa, a példa bemenete egyezik a leírt tényállással. Naptári dátumot a számoló nem számol: az eredmény a tartam vagy a kezdő esemény megnevezése. Ha a tétel döntési fájának eredménye a számolóra utalhat, a fa eredményébe a `szamolo` mezővel felveszed a hivatkozást; a fa szerkezetét ezért nem változtatod.
4. **Rögzített ok** a `termekek/lefedettseg_indok.json`-ban: `{"tetel": N, "termek": "szamolo", "kod": "…", "indok": "…"}`. Megengedett kódok: a `tools/lefedettseg_audit.py` `KODOK` táblája. Az indok megnevezi a tétel számszerű szabályait, minden §-hoz bekezdéssel, és megmondja, melyik eset áll fenn: „egyetlen küszöbérték, amelyet a(z) <fa azonosítója> döntési fa kérdése kezel” (`mas-termekben`), vagy „bírói mérlegelésen múlik (<§, bekezdés>)”, vagy nincs számszerű szabály (`nincs-szamithato-ertek`).

### 5.5 Hangos vázlat (kijelölés)

1. `python3 tools/vazlat_gyart.py NN --lista` (K = gépi előjelölés), majd `python3 tools/vazlat_kezi.py NN be=… ki=…` a végleges kijelöléssel, mondatsorszámokkal (a tétel korábbi kézi kijelölését felülírja), majd `python3 tools/vazlat_gyart.py`.
2. Kulcsmondat: fogalom-meghatározás, feltétel, joghatás, kivétel, határidő, az elhatárolás lényege, a főpont összegző mondata. Nem kulcsmondat: példa, átvezetés, ismétlés, a normaszöveget csak bejelentő mondat. Irányszám: a mondatok 50–60%-a. Minden főpontból (az összefoglalásból is) és minden elhatárolásból legyen kulcsmondat – kivéve, ha az elhatárolás minden mondata a 3. alpont miatt marad ki (a jelentésben megnevezed).
3. Kimarad a kijelölésből az a mondat, amelyet a hangszöveg hibásan olvasna: Alaptörvény-cikk („XIII. cikk”, „P) cikk”), „2013-as” típusú évszám, százalék, kormányrendelet- vagy határozatszám; betűjeles § (pl. „5:159/A. §”) a betűs § kiejtésének próbahangjáig; a mondat belsejében álló római számos utalás („IV. főpont”, „(IV/2.)”). A latin megjelölést tartalmazó mondat maradhat; a jelentésben felsorolod.
4. Ismert korlát: ha a mondat kezdete a tételben nem egyedi („többször szerepel”), a mondat a gépi előjelölés szerint marad; a jelentésben sorszámmal felsorolod.
5. A vázlathang (`vazlat_hang.py NN`, `vazlat_tts_terv.py`) a 4. pont sorrendjében, a felolvasószöveg után fut.

### 5.6 Felolvasószöveg és hangulatcímkék

1. `python3 tools/hangszoveg.py lefed NN` – a tétel hangdokumentumai és a blokkok lefedettsége.
2. Vedd fel a tételt a `tts/_ujra_terv.json` `tetelek` részébe: hangdokumentumonként (`ttsId`, a régi sorrendben) a meglévő `chunk_NNN` darabok és horgonyuk. A horgony annak az új tételblokknak az eleje, ahol a régi darab tartalma kezdődik (főcím vagy bekezdéskezdet), és **pontosan egy blokkra** illik; ha több blokkra illene, hosszabb horgonyt adsz (a teljes címsorral). A hangdokumentumok közötti határ a régi főpont-határ marad; az új főpontok (pl. ELHATÁROLÁSOK, ÖSSZEFOGLALÁS) az utolsó hangdokumentumba kerülnek. Folytatódarabot (`chunk_NNN_2`) a tervbe nem írsz, azt a program adja.
3. `python3 tools/tts_ujra.py NN` (próba), majd `python3 tools/tts_ujra.py NN --szoveg`: a teljes hangszöveget **elolvasod**, és megkeresed a hibás kiolvasást (latin szó, rövidítés kettőzése, cikk, évszám, betűjeles §, római számos utalás a mondat belsejében). Minden ilyet a `tts/_ujra_terv.json` `kiejtes` táblájába veszel fel (minta, csere) – ez az egyetlen megengedett javítási mód; a darabfájlt kézzel nem szerkeszted. A tételsor állandó kiejtési szabályai a beállítás `kiejtes` kulcsában vannak (a `tetelsor/` nem módosítható). Amit a `kiejtes` tábla nem tud feloldani (betűs §, általános római számos utalás), azt a jelentés „Központi teendő” pontjában darabonként felsorolod. A `--reszletes` kapcsoló a tétel egyetlen darabjára sem illeszkedő kiejtési sorokat is kiírja.
4. `python3 tools/tts_ujra.py NN --ir`.
5. **Hangulatcímkék:** `python3 tools/hangulat_szoveg.py --alap=<hangalap> --ir`. A címke szabályalapú (`tools/hangszoveg.py`, `hangulat`), az egység elejére kerül, és csak hangulatváltásnál: `[serious]` – jogszabálydoboz; `[calm]` – magyarázó bekezdés; `[emphatic]` – tilalom, semmisség, jogvesztés, kizártság, „csak akkor”; `[thoughtful]` – elhatárolás, szembeállítás, kivétel; `[curious]` – példa, kérdés; `[short pause]` – nagybetűs címsor előtt. A hangos vázlat alaphangja `[serious]`. Címkét kézzel nem írsz és nem törölsz. Hangeffektus (sóhaj, suttogás, torokköszörülés) új szövegbe – a `kiejtes` cseréjébe sem – nem kerül. Csak az a darab kap címkét, amely az élő hanghoz képest egyébként is változik; az élő hanggal azonos szövegű darabot a program az alap szövegére állítja vissza.
6. `python3 tools/hangmeta.py --alap=<hangalap>`. Ha a hivatkozás helyben nincs, a program megáll, és egyetlen `_meta.json`-t sem ír át: `git fetch origin <ág>`, és újra. Második futásra várt: `átírt _meta.json: 0`.
7. `python3 tools/vazlat_hang.py NN`, majd `python3 tools/vazlat_tts_terv.py`.
8. STOP, ha a `tts_ujra.py` „fölöslegessé vált régi folytatódarab” vagy horgonyhibával áll meg, és a horgonyok igazításával nem oldható fel. A `tts_ujra.py`-t nem módosítod.

### 5.7 Jegyzet-HTML

`python3 tools/jegyzet_html.py --mind` – a publikált rész-jegyzetek HTML-je a tétel szövegéből és a hangdarabokból; a tétel szövegének vagy hangdarabjainak minden változása után kötelező (enélkül a 12. kapu, a `jegyzet_html_ellenor.py` eltérést jelez). Ha a program „MEGÁLLT” sorral áll le (a rész jegyzetazonosítója nem egyértelmű): STOP, a kimenet a jelentésbe kerül.

### 5.8 A gyártásra váró lista

A `termekek/_gyartasra_var.json` sorolja fel a lezárt, még nem gyártott tételeket; az ilyen tétel elavult mátrixát a `matrix_ellenor.py` (és vele a `csomag_gyart.py`, a `kapuk.sh`) „GYÁRTÁSRA VÁR” figyelmeztetésként írja ki, nem hibaként. A köteg tételeit a gyártás végén kiveszed a `tetelek` tömbből; a kötegen kívüli tételt nem veszed ki, és annak elavult mátrixát nem javítod. Utána a `matrix_ellenor.py` a köteg tételeire 0 hibát és 0 várakozót ad.

### 5.9 A régi termékek érintettsége (csak lista)

A `kontroll/NN.json` „elavult” részének `sors.indok` mezői megnevezik a törölt vagy tévesnek bizonyult állításokat és megjelöléseket (a „gépi lezárás” indokú bejegyzéseket kihagyod). Ezek kulcsszavaival szűröd a `kviz/NN/`, `tanulokartyak/NN/`, `memoriautvonal/`, `hezagpotlok/` tételhez tartozó fájljait, és a jelentésben tételenként megadod: hány elem érintett az összesből, mely kulcsszavak miatt. A fájlokat nem módosítod (javításuk: `RT_regi_termekek.md`).

## 6. Kapuk és ellenőrzés

```
bash tools/kapuk.sh --visszaallit
```
Várt utolsó sor: `KAPUK: 12 futott; eltérés/hibás: 0`, kilépési kód 0. A futás előellenőrzésként a `tools/eszkoz_ellenor.py`-t is lefuttatja; eltérésnél megáll. A beszélgetésbe és a jelentésbe a kapukból csak az utolsó sor kerül; a többit te ellenőrzöd, és csak az eltérést írod le:
- az első sor (ÁLLAPOT-sor) betűre azonos a 3. pontban feljegyzettel;
- a `fa_ellenor` és a `matrix_ellenor` darabszáma a jelentésben megadott új darabokkal nőtt; a `matrix_ellenor` a köteg tételeire 0 hibát, 0 várakozót mutat;
- a köteg tételei nincsenek a `jelentesek/lefedettseg_audit.md` „Nyitott párok” táblájában (a `lefedettseg_audit.py` kilépési kódja a többi tétel miatt 1 maradhat) és a `jelentesek/hanglefedettseg.md` hiánylistáján;
- az időbélyeges jelentésfájlok visszaállítva; ha a program „ÉRDEMBEN VÁLTOZOTT” fájlt ír ki, a jelentésben megnevezed.

Külön ellenőrzések (várt kimenettel):
```
python3 tools/hangmeta.py --alap=<hangalap>         # átírt _meta.json: 0
python3 tools/tts_ujra.py NN                        # minden köteg-tételre: próba (nem írt): változó darab 0, új darab 0
grep -rlnE "tan[a]nyag|ZH-felk[é]sz[í]tő" termekek tts tools/matrix_adat.py   # nincs találat
git status --short | grep -i "mp3"                  # üres
```
A megjelenítő böngészős próbáját (`bash tools/megjelenito_teszt/futtat.sh <admin klón>`) nem te futtatod, hanem a központi chat.

## 7. STOP

Megállsz, és a jelentésben leírod az okot, ha: az előfeltétel nem teljesül (tisztaság, lezártság, legfeljebb 6 tétel); egy kapu a te termékeden kívüli okból bukik; az 5.6 vagy az 5.7 szerinti hiba nem oldható fel; a 9. pont ellenőrzése tiltott fájlt mutat; vagy a feladat csak a tilalmak megszegésével volna teljesíthető.

## 8. Jelentés

Helye: `jelentesek/TG-1_<tételek>_jelentes.md` (a commit része). Első sora a `python3 tools/kontroll.py kapu` ÁLLAPOT-sora szó szerint. Tartalma tételenként, felsorolva:
- a futtatott parancsok és kilépési kódjuk; a kapuk utolsó sora; a külön ellenőrzések utolsó sorai;
- fák: azonosító, cím, csomópont- és példaszám; új vagy igazított; mi változott az igazítottban;
- mátrixok: azonosítók; rögzített okkal kihagyott elhatárolások; törölt vagy átírt régi mátrixok;
- számoló vagy a rögzített ok szövege;
- vázlat: kulcsmondat/összes; az 5.5/3. pont miatt kihagyott mondatok sorszáma és oka; a nem egyedi kezdetű, jelölhetetlen mondatok sorszáma; a kulcsmondat nélkül maradt elhatárolások;
- felolvasószöveg: hangdokumentum-azonosítók; változó és új darabok száma; a `kiejtes` táblába felvett új sorok; a hangdokumentum címe és az új főpont-tartalom eltérése; a táblával fel nem oldható kiolvasások darabonként;
- a régi termékek érintettsége (5.9);
- Központi teendő: eszközhibák, a kiejtési tábla hiányai, tételszöveg-hibák; bizonytalan pontok (szakmailag átnézendő cella, csomópont, példa);
- ami nem futott vagy nincs kipróbálva, kimondva; a commit azonosítója; a feltöltés eredménye.

## 9. Commit és feltöltés a munkaágra

```
git add termekek tools/matrix_adat.py tts jelentesek
git status --short                                       # tiltott fájl nincs köztük
git commit -m "TG-1: a <tételek>. tétel termékei (fa, mátrix, számoló/ok, vázlat, felolvasószöveg); kapuk 0 hibával"
git diff --name-only origin/<celag> HEAD                 # várt: csak termekek/, tts/, jelentesek/ alatti fájl és tools/matrix_adat.py
git diff --name-only origin/<celag> HEAD | grep -iE '\.mp3$|service-account|\.pem$|\.key$|\.env$'   # várt: üres
git push origin tg1-<tételek>:tg1-<tételek>
```
Ha a `git diff --name-only` bármi mást mutat (pl. `NN.txt`, `kontroll/`, `ALLAPOT.md`, más `tools/` fájl), vagy mp3, kulcs van köztük: nem töltesz fel, STOP.

**Üzenet Attilának (a beszélgetésben):** az ág neve, a commit, a kapuk utolsó sora, és hogy az ág a központi chathez megy auditra (`TG_ag_audit.md`). Befésülő parancsot nem adsz; azt az audit után a központi chat adja.

## 10. Befésülés (nem az ügynök feladata)

1. A befésülést Attila egy parancsa végzi: `bash tools/befesul.sh <ág>` (a parancs teljes alakját a központi chat adja meg). Ügynök nem fésül be, és a célágra nem tölt fel.
2. A program csak az auditált, feltöltött ágat fésüli be előrefutóan: az ág utolsó commitja „Audit (központi chat):” kezdetű, és az `ALLAPOT.md` egy `## <dátum>` szakaszcíme az ág nevével „auditálva, befésülhető”; a célág csúcsa a munkaág őse. Ezért a munkaág mindig a célág **távoli** csúcsáról indul, és az audit után rá ügynök nem commitol.
3. A befésült munkaág lezárult: ha utána még javítás kell, az a célág távoli csúcsára épülő új ágon készül (pl. `<ág>-ujra`, `audit-<tárgy>`), saját audit-jellel.

## 11. Záróköteg – eltérések a rendes kötegtől

Ami itt nincs külön leírva (tilalmak, formátumok, ellenőrzések, commit, jelentés), arra az 1–10. pont érvényes. A két fajta két külön munkaág, két külön jelentés, két külön audit; ha mindkettő kell, a számoló-köteg csak az újragyártó köteg befésülése után indul.

### 11.1 Közös szabályok

1. A `tts/_ujra_terv.json` új kiejtési sora hosszú, egyedi szövegkörnyezetű, és más tétel darabjára nem illeszkedhet; a végén minden lezárt tételre lefut a `tts_ujra.py NN` próba: „változó darab 0, új darab 0”.
2. Az új fájlok azonosítóját betűnként ellenőrzöd.
3. Az ellenőrzés a 6. pont szerint; ezen felül `python3 tools/kontroll.py kapu | head -1` – változatlan ÁLLAPOT-sor.

### 11.2 Egy tétel újragyártása (a gyártás után megváltozott tétel)

**Munkaág:** `tg1-NN-ujra`. **Jelentés:** `jelentesek/TG-1_NN-ujra_jelentes.md`. **Commit:** `TG-1: a NN. tétel termékei újragyártva (…); kapuk 0 hibával`.
1. Az 5.2–5.7 pont a tételre; a tétel változásából következő kötelező fa- és mátrix-teendőket a feladatlap adja meg.
2. A `tools/matrix_adat.py`-ban csak a tétel blokkja változik; szűrős írás: `python3 tools/matrix_ir.py NN`. Ha a tétel új főponttal bővült, és az elhatárolásai között az új anyag is szerepel, ahhoz is mátrix készül (a forrásmondat a tétel teljes mondata).
3. A hangos vázlat kijelölése az új szerkezet szerint (az összefoglaló főpontnak is van kulcsmondata; arány 50–60%).
4. Az új főpont darabjai új darabként kerülnek a megfelelő hangdokumentumba, az 5.6 darabolási szabálya szerint.
5. A végén a tételt kiveszed a `termekek/_gyartasra_var.json` listájából; a `termekek/_elesites_elott.json` hozzá tartozó teendőjét nem zárod le.
6. Várt: `KAPUK: 12 futott; eltérés/hibás: 0`; `matrix_ellenor`: gyártásra vár 0; `tts_ujra.py NN`: változó darab 0, új darab 0.

### 11.3 Számoló-köteg

**Munkaág:** `tg1-szamolok`. **Jelentés:** `jelentesek/TG-1_szamolok_jelentes.md`. **Commit:** `TG-1: számoló-köteg (N számoló, M felülvizsgált indok); kapuk 0 hibával`.
1. A gyártandó számolók tábláját (tétel, §, a választás) a feladatlap adja meg. A szabály, a formátum és a fához kötés az 5.4 pont szerint; a §-okat a korpuszból és a tétel dobozából veszed; ha a doboz a szabályt nem tartalmazza, a számoló nem készül el, és a jelentésbe írod. Meglévő számoló bővíthető, ha a feladatlap így adja meg.
2. Minden elkészült számolónál: a `termekek/lefedettseg_indok.json` megfelelő számoló-indokát törlöd; a tétel fájának érintett eredményébe felveszed a `szamolo` hivatkozást, a fa szerkezetét nem változtatod.
3. A többi tétel számoló-indokát felülvizsgálod: ahol az indok „naptári tartam” vagy „nem számolható” érvelést használ olyan szabályra, amely egyetlen küszöbérték vagy mérlegelés, az indok az 5.4/4. pont szerinti két eset egyikét mondja ki, minden §-hoz bekezdéssel. A felülvizsgált indokok listája (tétel, régi kód, új kód) a jelentésbe kerül.
4. Ha a táblán kívül is találsz választó szabályt (legalább két érték, mérlegelés nélkül), nem készítesz hozzá számolót: a jelentés „Központi teendő” pontjába írod.
5. Várt: `python3 tools/szamolo_ellenor.py` → `… hibás: 0`; `python3 tools/fa_ellenor.py` → `… hibás fa: 0`; `KAPUK: 12 futott; eltérés/hibás: 0`; változatlan ÁLLAPOT-sor.
6. A jelentés számolónként: a szabály §-a, a bemenetek, a szabályok és a példák száma; ami nem készült el, és miért.
