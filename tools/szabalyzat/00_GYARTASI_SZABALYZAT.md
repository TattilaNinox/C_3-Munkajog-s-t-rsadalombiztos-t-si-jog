# Gyártási szabályzat – a szakvizsga-tételsorok feldolgozásának végleges rendje

**Hely:** `<tételsor-tároló>/tools/szabalyzat/00_GYARTASI_SZABALYZAT.md` – a közös készlet zárolt másolata, helyben nem módosítható (forrása: `orlomed_admin_web/tools/szakvizsga/szabalyzat/`; a tárolókba a `szinkron.py` viszi, a `tools/eszkozok.lock` zárolja).
**Hatály:** minden tételsor (A/1–C/3), minden beszélgetés és minden ügynök. Ez az A/1 tételsoron kialakított, végigvitt és rögzített rend; a gyártás e szerint megy.
**Mellette, ugyanebben a mappában – a szerepek szabályzatai:** `KP_iro.md`, `KP_olvaso.md`, `KP_audit.md` (tételmunka), `TG_termekgyartas.md`, `TG_ag_audit.md` (termékek), `RT_regi_termekek.md` (régi termékek).

**Három kötelező alapszabály a szabályzat használatához**

1. **A dolgozó beszélgetés ezt a fájlt és a tároló `ALLAPOT.md`-jét olvassa el – mást nem kell.** Az alügynök a saját szerepének szabályzatát és a feladatlapot kapja. Tételsorra átírt, „átültetett” utasításpéldány nem készül.
2. **Ami tételsoronként más, az adat, nem szabály:** a `tetelsor/beallitas.json`-ban áll (azonosító, fő kódex, jogállapot napja, célág, kommentárkötet, forrásmegfeleltetés), illetve az `ALLAPOT.md` „Tételsor-specifikus” szakaszában (a kommentárkötet adatai, a mintatétel, a tételre jelzett teendők, Attila tételsorra szóló döntései).
3. **Egyedi eset:** amire a szabályzat nem ad választ, az megálló (9. pont): az érintett tétel áll, a többi megy tovább, Attila dönt, a döntés az `ALLAPOT.md` „Egyedi eltérések” szakaszába kerül. **Új módszert, új kört, „javított” folyamatot egyetlen beszélgetés és ügynök sem vezet be és nem javasol**; a szabályzat csak Attila kifejezett döntésével módosul, a közös készletben, minden tételsorra egyszerre.

---

## 1. Alapelvek

1. **A kiindulás a publikált jegyzet** (`jegyzetek/`). A régi tételsor szövegét nem olvassuk, nem vetjük össze, nem javítjuk.
2. **Mérce:** a hivatalos kiírás által megjelölt joganyag, a `beallitas.json` `jogallapot` napján hatályos szöveggel (ha a `korpusz/manifest.json` egy forrásnál későbbi, már kihirdetett időállapotot jelöl, az). Ha a kiírás hatályon kívül helyezett jogszabályt nevez meg, a tétel a helyébe lépett hatályos jogszabályra épül (`tetelForras`), és egy mondatban jelzi ezt.
3. **A tétel nem távirat.** Egy pont akkor kész, ha megvan benne a mérce hét eleme: (1) fogalom és rendszertani hely; (2) a szabály magyarázata – hogyan működik, mi a célja; (3) joghatás, kivételek, határidők, feltételek pontosan; (4) elhatárolás a rokon intézményektől; (5) az előírt joggyakorlat érdemi feldolgozása; (6) pontos normaszöveg dobozban; (7) minden normatív állítás mögött doboz vagy korpusz-§. **Csere, nem törlés:** a nem igazolható állítás helyére igazolt tartalom kerül; pótlás nélkül csak az törölhető, aminek a tárgyban nincs igazolható megfelelője.
4. **Nincs állítás igazoló forrás nélkül.** Forrássorrend: (1) korpusz – normatív állítás csak ebből; (2) IJOTEN; (3) a tárgy Jogkódex-kommentárja; (4) nyílt, hiteles webes forrás (hivatalos indokolás, hatósági kiadvány, nyílt egyetemi tankönyv, lektorált nyílt folyóirat), dátummal és hatályossági vizsgálattal. A fő kódexre épülő többletállításnál a (2) és a (3) kötelező; ahol nincs kommentárkötet, a (3) helyére a (4) lép. Blog, Wikipédia, fórum, AI-összefoglaló, érdekképviseleti képzési anyag és a MeRSZ nem forrás. Ellentmondásnál a magasabb rang dönt.
5. **A kommentár és az IJOTEN mérce és ellenőrző forrás, nem szövegforrás:** saját megfogalmazás és szerkezet; mondat, felépítés, példa átvétele tilos; a tétel nem hivatkozik rájuk; szövegük fájlba, commitba és API-kérésbe nem kerül. A kommentár-tartományt teljes hosszában kell elolvasni; bekezdést levágni tilos.
6. **Doboz szövegét kézzel senki nem írja:** a dobozt program építi a korpuszból, betűre.
7. **A lezárást a gép mondja ki, a tartalmat független olvasó auditálja.** Munkát nem az zár le, aki végezte. Jelentés önmagában nem lezárás.
8. **Egész tételsorra méretezve:** a munka hullámokban, párhuzamosan halad; két-három tételenként senki nem áll meg jóváhagyásra.
9. **Semmi nem élesedik a tételsor teljes készültsége előtt.** Nincs futásidejű AI a termékekben.

## 2. Állandó tilalmak (mindenkire)

- A `jogedu` adatbázisba és a Storage-ba senki nem ír; importáló, feltöltő, telepítő parancs (IM-*, TF-*, HV-*, HP-*, `firebase`) és hanggenerálás tilos. Ezeket kizárólag Attila futtatja, próbafutás és kódaudit után, pontos commit-azonosítóval.
- A `main` ágat csak Attila lépteti. A célágra (`celag`) csak Attila `tools/befesul.sh` parancsa tölt fel.
- `git add -A` és `git add .` tilos: mindig fájlnév szerint. Commit előtt: `git diff --cached --diff-filter=D --name-only` üres; `git diff --cached --name-only | grep -Ei '\.mp3$|service-account|\.key$|\.pem$'` üres.
- Tárolóba és beszélgetésbe soha: kulcs (API-kulcs sem), `service-account.json`, jelszó, felhasználói adat, mp3. Attila e-mail-címe privát.
- A `tools/` mappa a közös készlet zárolt másolata: kézzel nem módosítható (`python3 tools/eszkoz_ellenor.py | tail -1` → `eltérés 0`). Hibás vagy hiányzó eszköz: „Központi teendő” az `ALLAPOT.md`-ben; helyi foltozás nincs.
- MeRSZ tilos (megnyitni is). Bírósági oldalról (Kúria, birosag.hu, BHGY) nincs gépi letöltés vagy lekérés. Jogszabály letöltéséhez adott link a Jogtárra vagy a Jogkódexre mutat.
- A Cursor-ügynök böngészőt nem nyit, képernyőképet nem készít.
- A `kontroll/*.json` bejegyzései nem törölhetők.
- Tiltott szavak (termék, felhasználói és marketing szöveg): „tananyag”, „ZH-felkészítő”. A tételszövegben a „korpusz” szó nem állhat.
- A `hangmeta.py` és a `hangulat_szoveg.py` kizárólag a `beallitas.json` `hangAlapAgak` szerinti `--alap=` kapcsolóval futhat.
- Leállított alügynököt csak Attila kifejezett kérésére szabad újraindítani.
- Kötelező lépést senki nem halaszt, nem szűkít mintára, nem cserél másra. Ha valami nem végezhető el: megálló, és ez az üzenet első mondata.

## 3. Szerepek

| Szerep | Ki | Mit végez | Szabályzata |
|---|---|---|---|
| Megbízó | Attila | források, kiírás; befésülő és `--apply` parancsok; API-köteg futtatása; hanggenerálás; admin-teszt; döntés a megállóknál | – |
| Központi chat | kijelölt beszélgetés | a közös készlet és ez a szabályzat; S0–S2; az API-kötegek előkészítése és olvasása; a közös kód; a termékágak auditjának vezetése; megjelenítő-próba | ez a fájl |
| Tételsor-chat | tételsoronként egy | a saját tételsor S3–S6 munkája: a kötegeket vezeti, **a leletet és a diffet maga nézi át, maga adja a `levezetes` jelet, és maga zárja le a tételt**; csak a saját tárolóját és annak `ALLAPOT.md`-jét írja | ez a fájl, 6. pont |
| Író-alügynök | Opus | a tétel írása a korpuszból és az IJOTEN-ből (1. kör), a lista pontjai (2. kör); a kommentárt soha nem nyitja meg | `KP_iro.md` |
| Olvasó-auditor alügynök | Opus | a kommentár-tartomány teljes olvasása és a lista; újraindítva a célzott audit; a tételt nem írja | `KP_olvaso.md`, `KP_audit.md` |
| Gyártó | Cursor-ügynök | új termékek, felolvasószöveg, jegyzet-HTML; a régi termékek javítása; szkriptek – munkaágra | `TG_termekgyartas.md`, `RT_regi_termekek.md` |
| Ágaudit | Opus-alügynök(ök) | a termék-munkaág auditja; a régi termékek független auditja | `TG_ag_audit.md`, `RT_regi_termekek.md` |

- Ahol lehet, a munkát Opus-alügynök végzi (`model: "opus"`); a vezető beszélgetés utasít, a jelentést és a diffet ellenőrzi. Más modell csak Attila külön döntésével.
- Közös fájlt (készlet, szabályzat, az admin `docs/` mappája, skillek, a megjelenítő és az admin kódja, a `beallitas.json` közös kulcsai) csak a központi chat ír. A tételsor-chat javaslatot ír az `ALLAPOT.md` „Központi teendő” szakaszába.
- Ismeretlen eredetű, nem commitolt változást senki nem használ fel: jelezni kell Attilának.

## 4. Indulás és üzenetek (minden beszélgetés)

1. Olvasd el ezt a fájlt és a tároló `ALLAPOT.md`-jét. A tároló gyökeréből (`R`):
   ```
   cd "$R" && git fetch origin && git status --short          # üres kell legyen
   python3 tools/eszkoz_ellenor.py | tail -1                   # „eltérés 0”
   python3 tools/kontroll.py kapu | grep -m1 '^ÁLLAPOT:'       # az ÁLLAPOT-sor (az 1-es kilépési kód a várt, amíg nincs minden lezárva)
   ```
2. **Minden üzenet és jelentés első sora a `kontroll.py kapu` ÁLLAPOT-sora, szó szerint.** (S0–S2 alatt, amíg nincs tétel a kapuban: az éppen futó szakasz zárókapujának utolsó sora.)
3. **Indulási üzenet legfeljebb három sor:** állapotsor; egy mondat arról, mi indult el; és csak akadály, eltérés vagy Attilától várt teendő esetén több. Közbenső üzenetben csak a változás és a teendő áll; ami a várt értéket adja, nem kell felsorolni.
4. Magyarul, tegezve, tömören. Döntés kötelező erejű döntésként, indokkal. Attila teendőjénél a pontos, egyben futtatható parancs kódblokkban (`cd`-vel kezdve).
5. Rövid kimenetek: kapuból csak az utolsó sor kerül a beszélgetésbe; nagy fájlt (jelentés, diff, lista) csak akkor íratsz ki teljes hosszában, ha azt kell elolvasnod.
6. Új beszélgetést csak akkor kérsz, ha a jelenlegi megtelt; ekkor az üzenet a következő beszélgetés indító szövegét is tartalmazza kódblokkban (12. pont).

## 5. A tételsor útja: szakaszok és zárókapuk

Szakaszt átugrani nem lehet. Egy szakasz akkor zárul, ha a zárókapuja teljesül; az eredmény az `ALLAPOT.md`-be kerül, a kapu utolsó sorával szó szerint.

| # | Szakasz | Végzi | Zárókapu |
|---|---|---|---|
| S0 | Eszközkészlet és beállítás | központi chat (Opus-alügynökkel) | `eszkoz_ellenor`: eltérés 0; `beallitas.json` kész |
| S1 | Alapfelvétel | központi chat (Opus-alügynökkel) | `alapfelvetel`: hiba 0, a feloldatlan sor mind valódi hiány; `jegyzet_txt`: eltérés 0 |
| S2 | Korpusz és hatályosság | központi chat; a forrást Attila adja | `hatalyossag.py kapu`: nyitott 0 |
| S3 | Dobozok | tételsor-chat | `ellenorzes.py`: eltérés 0, hiányzó forrás nincs; `doboz_teljesseg.py`: hiányos bekezdés 0 |
| S4 | API-körök (első olvasás, átírás, ellenőrzés) | Attila futtat; központi chat készít és olvas | minden tételre ellenőrző lelet; a költés a főkönyvben; a mintát Attila jóváhagyta |
| S5 | Tételmunka: kommentárkör | tételsor-chat + író + olvasó-auditor | `kontroll.py kapu`: N/N tétel lezárva |
| S6 | Termékek, hangszöveg, régi termékek | Cursor-ügynök; ágaudit; Attila befésül | `bash tools/kapuk.sh --visszaallit`: eltérés/hibás 0; megjelenítő-próba 0 hiba; `lefedettseg_audit.py`: 0 nyitott pár; `rt2_ellenor.py`: 0 hiba |
| S7 | Előnézet és élesítő eszközök | Cursor (szkript), központi chat (kódaudit), Attila (`--apply`, teszt) | próbafutások számai = a tároló számai; Attila admin-tesztje |
| S8 | Tartalmi zárás és csere | Attila futtat; központi chat vezet | `elesites_kapu.py`: 0; friss élő export, 0 ütközés |

**Párhuzamosság:** S2 és S1 együtt futhat; S6 a már lezárt tételeken fut, miközben S5 a következőkön halad (a termékek mindig legalább egy lezárt hullámmal a tételmunka mögött); S7 eszközei S5 alatt készülnek el, nem a végén. Sorrend egy tételen belül: lezárás → új termékek és hangszöveg → régi termékek → befésülés. Régi terméket lezáratlan tételhez igazítani tilos.

### S0 – Eszközkészlet és beállítás

1. Szinkron az admin klón gyökeréből: `python3 tools/szakvizsga/szinkron.py --cel=<tároló>`; a tárolóban `python3 tools/eszkoz_ellenor.py | tail -1` → `eltérés 0`.
2. `tetelsor/beallitas.json` minden kötelező kulccsal (minta: egy kész tételsor fájlja): `azon`, `cim`, `kategoria`, `tetelDb`, `foKodex`, `targyKod` (`szakvizsga_<azon>`), `celag` (`termekek-<azon>`), `jogallapot`, `apiKeretUsd`, `kiiras`, `forrasok` (`kod`, `nev`, `mintak`, `fajl` vagy `fajlKezdet`, `egyseg`), `parMinta`, `dobozRovidites`, `kontroll`, `kommentar`, `mintaTetelek`, `kiejtes`, `rt2Alap`, `hangAlapAgak`, `tetelForras`, és csak bizonyítható elírásra `kiirasElirasok` (indok az `ALLAPOT.md`-ben).
3. Az előkészítő ág: `elokeszites-<dátum>`; S0–S4 commitjai ide kerülnek.

### S1 – Alapfelvétel

1. Bemenet: `jegyzetek/` + `manifest.json`; a hivatalos kiírás PDF-je és szövege (`tetelsor/kiiras_<év>.txt`) – Attila adja.
2. `python3 tools/korpusz_felmeres.py --kiiras=tetelsor/kiiras_<év>.txt` (első felmérés) → `python3 tools/alapfelvetel.py` (`tetelsor/tetelsor.json`, `forrasok.json`) → `python3 tools/jegyzet_txt.py` (`NN.txt`, betűhű zárókapuval).
3. A `feloldatlan` minden sorát egyenként kell megvizsgálni: hiányzó minta → pótlás a beállításban; névhiba → `kiirasElirasok.megfeleltet`; valódi hiány → marad, és felkerül a hiánylistára. **Hiányt eltüntetni tilos.**
4. A kiírás tételszáma = a jegyzetmappák száma; minden jegyzetrész pontosan egy tételhez tartozik. Eltérés: megálló.

### S2 – Korpusz és hatályosság

1. Hiánylista Attilának **egy üzenetben** (forrás, tétel, letöltési hely: Jogtár vagy Jogkódex). A forrásokat Attila tölti le; bírósági határozatot kézzel.
2. Szakaszonkénti összevetés a megkövetelt időállapottal: `python3 tools/hatalyossag.py ujjlenyomat <korpuszfájl> [--cikk]` + a hatályos egységes szöveg lapján `tools/hatalyossag/osszevet.js` (csak szakaszszámok jönnek vissza); az eredmény a `korpusz/allapot.json`-ba; `python3 tools/hatalyossag.py jelentes`.
3. Zárókapu: `python3 tools/hatalyossag.py kapu` → nyitott 0. A cserélt korpuszfájlok Storage-feltöltése S8-ban, Attilánál.

### S3 – Dobozok

1. `python3 tools/s5/doboz_javit.py --sor --ir` (a dobozok újraépítése a korpuszból, teljes bekezdésekkel); másodszor futtatva: „módosítandó doboz: 0”.
2. Zárókapu: `python3 tools/ellenorzes.py | tail -1` és `python3 tools/doboz_teljesseg.py | head -1`. Kézi dobozírás nincs; amit a program nem tud megépíteni: Központi teendő.

### S4 – API-körök

**Mire való:** az egész tételsor egy menetben kap leletet és első átdolgozást, hogy a kommentárkör kész, javított szöveggel induljon. **Az API-lelet bemenet, nem lezárás:** kaput, kommentár-kontrollt és auditot nem vált ki.

Keretszabályok (mind kötelező): (1) a köteget Attila futtatja a saját gépén; a kulcs környezeti változóból jön (`export ANTHROPIC_API_KEY="$(security find-generic-password -s anthropic-api -w)"`), máshová nem kerül; (2) indítás előtt Attila megadja az aktuális kreditegyenleget; (3) a köteg **legrosszabb esete** és a `--plafon` a maradék kredit alatt van – nem a várható költség számít; (4) egyszerre egy tételsor kötege fut, a következő csak az előző tényleges költségének ismeretében; (5) az automatikus újratöltés kikapcsolva marad; (6) a kérésbe csak a tároló saját tartalma megy (kiírás, korpusz, jegyzet, munkaszöveg, lelet) – kommentár, IJOTEN, felhasználói adat nem; (7) S2 zárása előtt köteg nem küldhető; (8) a tényleges költés a `jelentesek/api_koltseg.csv` főkönyvben áll (`python3 tools/api_koteg.py fokonyv`).

A körök, ebben a sorrendben (Attila minden parancsot egy blokkban, `cd`-vel és feladatnévvel kap):

1. **Első olvasás – próba 3 tételen:** `python3 tools/api_koteg.py keszit elso_olvasas --tetel=a,b,c` → `kuld elso_olvasas --plafon=2` → `letolt elso_olvasas`; a központi chat a három leletet elolvassa.
2. **Első olvasás – teljes köteg:** `keszit elso_olvasas` → `kuld elso_olvasas --plafon=<USD>` → `allapot` → `letolt` (`jelentesek/api/elso_olvasas/elso-NN.json`; a csonka válasz nem lelet).
3. **Átírás:** `python3 tools/s5/koteg.py keszit atiras` → `kuld atiras --plafon=<USD>` → `letolt atiras`; csonka válasznál `python3 tools/s5/ment.py`; `python3 tools/s5/alkalmaz.py` (próbafutás), majd `--ir`. A modell műveletlistát ad, jogszabályszöveget nem ír: a dobozt a program építi a korpuszból. A csonka tételek újra megkapják az átírást (a már javított szövegre).
4. **Ellenőrző olvasás** (független, a korpusz ellen): `python3 tools/s5/koteg.py keszit ellenorzo` → `kuld ellenorzo --plafon=<USD>` → `letolt ellenorzo` (`jelentesek/api/ellenorzo/ell-NN.json`).
5. **Egy javító kör** (átírás az ellenőrző lelet alapján, `--ujra`), utána újabb ellenőrző olvasás. További kör nincs: a megmaradt pontok a kommentárkör bemenete.
6. `python3 tools/s5/osszesito.py` → `jelentesek/api/osszesito.md`; S3 kapui újra (0 eltérés).
7. **Minta Attilának:** külön egytételes kalibráció nincs; Attila a kész kötegből hagy jóvá mintát; a jóváhagyás az `ALLAPOT.md`-be kerül.

8. **A célág megnyitása:** az S4 zárásakor a célágat (`celag`) Attila nyitja meg az előkészítő ág csúcsáról, egy paranccsal: `cd <helyi klón> && git fetch origin && git push origin origin/<előkészítő ág>:refs/heads/<celag>`.

Ha a kredit az API-kört nem engedi: a tételsor a kommentárkörrel nem várhat a szabályzat megkerülésével – hogy megvárja-e a kreditet, vagy az író-alügynök maga készíti a leletet (`KP_iro.md`), tételsoronként Attila dönti el.

### S5 – Tételmunka: a kommentárkör

A részletes menet a 6. pontban.

### S6 – Termékek, hangszöveg, régi termékek

0. **Megnyitás (tételsoronként egyszer, a központi chat végzi, mielőtt az első termékköteg indul):** a `beallitas.json` termékkulcsai kitöltve (`kiejtes`, `mintaTetelek`, `hangAlapAgak`, `rt2Alap`); a gépi termékek első legyártása a teljes tételsorra és a `termekek/_gyartasra_var.json` feltöltése a még le nem zárt tételekkel; `bash tools/kapuk.sh --visszaallit` → 12 kapu, eltérés/hibás 0; „Audit (központi chat):” commit, Attila befésüli. Amíg ez nincs meg, a kapusor a termékkapukat kihagyja („termék nincs legyártva”), és termékköteg nem indítható.
1. **Új termékek** (§-jegyzék, felsorolás, hangos vázlat, döntési fa, számoló, fogalommátrix), felolvasószöveg hangulatcímkékkel, jegyzet-HTML: a Cursor-ügynök gyártja a `TG_termekgyartas.md` szerint, **legfeljebb 6 lezárt tétel egy kötegben**, `tg1-<tételek>` munkaágon; a munkaágra maga tölt fel (a tiltott fájlok ellenőrzése után). A Cursor feladata egy sor: „Olvasd el a `tools/szabalyzat/TG_termekgyartas.md` fájlt, és aszerint gyártsd le a(z) … tételek termékeit.”
2. **A munkaág auditja:** audit-alügynök a `TG_ag_audit.md` szerint; 4 tételnél nagyobb kötegnél két audit-alügynök (fák és számolók; mátrixok, vázlat, felolvasószöveg). A vezető beszélgetés a leletet és a javítások diffjét nézi át, és „Audit (központi chat):” kezdetű commitban teszi a munkaágra az `ALLAPOT.md`-vel együtt (a szakaszcímben az ág neve és az „auditálva, befésülhető” szöveg). Audit nélkül munkaág nem fésülhető be.
3. **Megjelenítő-próba:** `bash tools/megjelenito_teszt/futtat.sh <admin klón>` – a központi chat futtatja, termékkötegenként egyszer; újra csak akkor, ha a csomag vagy a megjelenítő változott.
4. **Régi termékek** (kvíz, tanulókártya, hézagpótló, memóriaútvonal): a `RT_regi_termekek.md` szerint, a tétel lezárása után, `rt-<tételek>` munkaágon: az első köteg után megálló és audit, utána hattételes kötegek; a független audit minden elemet végigolvas, a változatlanokat is. Tartalmi javítás után mindig más olvassa végig, mint aki javított.
5. **Befésülés:** Attila egy parancsa, naponta legfeljebb egy blokkban, több ág egy sorban:
   ```
   cd <a tételsor-tároló helyi klónja> && bash tools/befesul.sh <munkaág>
   ```
   A befésült munkaágra többé nem kerül commit; későbbi javítás a célág csúcsára épülő új ágra megy.
6. **Lefedettség:** `python3 tools/lefedettseg_audit.py` → 0 nyitott pár; hiányzó termék vagy elkészül, vagy kötött kóddal indokolt (`termekek/lefedettseg_indok.json`), tételenként kimondva; tömeges „nem kell” nincs. Élesítés előttre halasztott teendő csak a `termekek/_elesites_elott.json`-ban élhet.

### S7 – Előnézet és élesítő eszközök

1. A szkriptek (az A/1 IM-2 és IM-3 mintája, a tételsorra paraméterezve: admin `docs/szakvizsga_program/utasitasok/IM-2_elesito_import.md`, `IM-3_uj_tetelsor_elonezet.md`, `HV-1_vazlat_hangdokumentumok.md`) S5 alatt készülnek el; a Cursor írja, a központi chat a kódot is auditálja (pontos SHA, blokknál kilépés írás előtt, tiltott mezők, visszaállítható pillanatkép).
2. Minden lépés: próbafutás → a számok egyeznek a tároló számaival → Attila `--apply` parancsa, pontos commit-azonosítóval.
3. Előnézeti tételsor az adminban (`<azon>_uj_elonezet`, tételek `<azon>uj_NN`), vázlat-hangdokumentumok (`hv_<azon>_NN`), termékcsomag (`python3 tools/csomag_gyart.py` → `ki/<azon>_termekcsomag.json`). A hangot Attila generálja; hanggenerálás csak a szöveg véglegesítése után.
4. Attila admin-tesztje (Termék-előnézet és az előnézeti tételsor). Tartalmi észrevétel a tárolóban javul, nem az adminban; felületi észrevétel a központi chaté.

### S8 – Tartalmi zárás és csere

1. Az időállapotok újraellenőrzése (S2 kapuja újra); `python3 tools/elesites_kapu.py` → 0; `python3 tools/hang_koltseg.py --alap=…` jelentése Attila előtt.
2. Friss élő export és ütközéselemzés (0 ütközés).
3. A csere egy menetben, a régi azonosítókra, ebben a sorrendben: tételszöveg → jegyzetek → részcímek → régi termékek → a tétel-hang szövege → a kész hang átvitele → vázlathang → Attila pótolja a változott hangdarabokat és összefűz → az előnézet törlése → csomag. A kötések, a felhasználói előrehaladás és a hivatkozások megmaradnak. Minden parancsot Attila futtat.

## 6. S5 részletesen – a kommentárkör menete (a tételsor-chat vezeti)

**Cél:** minden tétel lezárva a gépi kapu szerint (`python3 tools/kontroll.py kapu` → „N/N tétel lezárva”, kilépési kód 0), és minden tétel minden pontja eléri a mérce hét elemét, amit a `jelentesek/KP-2_merce.md` tételenként rögzít.

### 6.1 Munkarend

- **Tételenként két alügynök, mindkettő kétszer indul:** író (1. kör: korpusz + IJOTEN, a kommentár megnyitása nélkül; 2. kör: a lista pontjai) és olvasó-auditor (a kommentár-tartomány teljes olvasása és a lista; majd újraindítva a célzott audit).
- **A tételsor-chat a tételt előre nem olvassa el, előzetes leletet nem ír;** a leletet és a diffet olvassa, a teljes tételt nem. A leletet és a diffet maga auditálja (6.6), és maga zárja le a tételt; kötegenként nem áll meg, és nem vár másik beszélgetésre.
- **Köteg és hullám:** az alügynökök egysége a 3 tételes köteg, növekvő sorrendben. **A tételsor-chat hullámokban dolgozik: hullámonként legalább három köteget (9 tételt) indít párhuzamosan**, és amint egy köteg lezárult, indítja a következőt. Párhuzamos alügynökök külön munkapéldányban és külön böngészőlapon dolgoznak; ha a böngésző vagy a gép a párhuzamosságot nem bírja, a hullám kisebb, de a munka nem áll meg.
- Szomszédos tételek összefüggő kommentár-tartománya (együtt legfeljebb kb. 120 ezer karakter) egy olvasó-alügynöknek adható, egy olvasással; a leltár, a mérce-napló és a commit ekkor is tételenként külön készül. **700 elemnél nagyobb tartomány:** az a tétel megáll (Attila döntésével fejezethatáron két olvasó olvassa), a többi megy tovább. Cél: tételenként 15 alatti böngészőhívás.
- **Böngésző:** a kommentárt (Jogkódex) a Claude asztali alkalmazás beépített böngészőjében kell olvasni, ahol Attila bejelentkezett; a kötet azonosítója és a feltérképezett helyek a `kontroll/_kommentar_terkep.json`-ban vannak – a kötetet újra megkeresni tilos. Az IJOTEN-t az író a beépített böngészőben, saját lapon éri el; a Jogkódex az írónak tilos. Jelszót senki nem ír be. Más munkához nyitott lapot (pl. a hatályossági összevetés lapját) senki nem használ és nem zár be. Ha a böngésző nem érhető el vagy nincs bejelentkezve: megálló.
- **Ebben a szakaszban tilos:** API-hívás és az API-kör eszközei (`tools/api_koteg.py`, `tools/s5/koteg.py`, `alkalmaz.py`, `ment.py`, `osszesito.py`; a `jelentesek/api/` csak olvasható); az előkészítő ág, a célág és a `main` érintése.

### 6.2 Ág és munkapéldányok

A tételmunka mentőágra kerül, a célágra soha közvetlenül. A mentőág neve `kp2-<azon>-<sorszám>` (01, 02, …); az első a célág távoli csúcsáról nyílik, minden további az előző mentőág csúcsáról. Minden lezárt tétel a futó mentőágra kerül, tételenkénti commitban. **A mentőágat a tételsor-chat zárja le befésülésre** (6.7/10), legfeljebb naponta egyszer; utána új mentőágat nyit, és megállás nélkül dolgozik tovább.
```
cd "$R" && git fetch origin
AG=kp2-<azon>-<sorszám>
git switch "$AG" 2>/dev/null || git switch -c "$AG" origin/<celag>      # további mentőágnál: az előző mentőág csúcsáról
BASE=$(git rev-parse HEAD)
M="$R/../<azon>_kp2_munka"; ATADO="$M/atado"; mkdir -p "$ATADO"
for NN in <a hullám tételei, kétjegyűen>; do git worktree add --detach "$M/$NN" "$BASE"; done
```

### 6.3 Feladatlap tételenként (csak ennyi; a tételt nem olvasod el)

- a tétel száma, címe és a hivatalos kiírás, a hivatkozott korpuszfájlok: `tetelsor/tetelsor.json` (`szoveg`, `hivatkozasok`), `korpusz/manifest.json`;
- a szomszédos tételek határa (az előző és a következő tétel címe és kiírása);
- a mintatétel helye: a tételsor egy lezárt tétele az `ALLAPOT.md` „Tételsor-specifikus” szakasza szerint; amíg a tételsorban nincs lezárt tétel, egy másik tételsor ott megnevezett lezárt tétele, csak olvasásra;
- az API-lelet helye, ha van: `jelentesek/api/ellenorzo/ell-NN.json` (a lezárandó pontok száma típusonként);
- a tételre jelzett teendő az `ALLAPOT.md` „Tételsor-specifikus” szakaszából és a `tetelForras`-ból;
- a munkapéldány (`$M/NN`), az átadó mappa (`$ATADO`), az alapcommit (`$BASE`);
- az olvasónak és az auditnak: a kommentár-tartomány azonosítói a `kontroll/_kommentar_terkep.json`-ból, ha már szerepelnek; ha nem, a tételhez tartozó §-ok listája. Ahol a tételnek nincs kommentárkötete: ezt a feladatlap kimondja, és a forrássorrend (4) rangja lép be.

### 6.4 A négy alügynök-lépés

Minden alügynök visszatérésekor (az író mindkét köre után külön) egy sor a `jelentesek/koltseg_naplo.csv`-be: `datum;tetel;lepes;modell;token_ezer;fordulo;perc;bongeszohivas;visszaadas;megjegyzes`.

1. **Író, 1. kör:** „Olvasd el a `tools/szabalyzat/KP_iro.md` fájlt, és aszerint végezd el az 1. kört a feladatlap szerint.” + feladatlap. Vége: `$ATADO/NN_jelentes.md`, `$ATADO/NN_seged.json`; ha van API-lelet, a tétel leletének minden ELLENTMOND, ELAVULT_GYANU, PONTATLAN és NEM_IGAZOLHATO pontja lezárva a `kontroll/NN.json` `api_lelet` kulcsában; a kapu ekkor még nyitott.
2. **Olvasó:** „Olvasd el a `tools/szabalyzat/KP_olvaso.md` fájlt, és aszerint végezd el az olvasást és a listát.” + feladatlap. Vége: `$ATADO/NN_lista.json`, `NN_seged_olvaso.json`, `NN_olvaso_jelentes.md`; a böngészőlapját nem zárja be. Akadály (a tartomány nem fér bele, a kötet nem található, 700 elem felett): a tétel áll.
3. **Író, 2. kör** (ugyanaz a szabályzat, újraindítva, a lista helyével): a `bejegyzesek` átvezetése, a `pontok` megírása a korpusz-§-ból (`"menet": 2`); `python3 tools/kontroll.py leltar NN`, `bash tools/kapuk.sh --tetel NN` 0 nyitott pontig.
4. **Olvasó-auditor, újraindítva:** „Olvasd el a `tools/szabalyzat/KP_audit.md` fájlt, és aszerint auditáld a tételt.” + a tétel száma, a munkapéldány, `$BASE`, a jelentés, a lista, a kommentár-tartomány. Az egyezésmérőt (`python3 tools/egyezes_elokeszit.py NN --darab 12000` + `tools/kommentar/egyezes.js`) és a gépi mintát (`python3 tools/kontroll.py minta-audit NN --kihagy …`) ő futtatja. Tartalék: ha a böngészőt nem éri el, külön audit-alügynök ugyanezzel a szabályzattal. Vége: lelet ítélettel – *elfogadható* / *javítandó a tételsor-chatnél* / *visszaadandó*.

### 6.5 Leletosztályok (minden auditban ezekkel a szavakkal)

JOGI HIBA · PONTATLAN · TÚLTERJESZKEDÉS (a forrás nem igazolja: „csak”, „mindig”, „hivatalból”, kiszámított végnap, álidézet) · MARADVÁNY (régi §-szám, régi szabály újként) · NYELVI. JOGI HIBA és MARADVÁNY nyitva nem maradhat; a többi csak indokolt, az `ALLAPOT.md`-ben rögzített kivétellel.

### 6.6 A lelet és a diff a tételsor-chatnél

1. Olvasod: az audit leletét, a két jelentést és a diffet: `git -C "$M/NN" diff "$BASE" -- NN.txt kontroll/NN.json` (célzott kiíratással).
2. **A lelet §-ra vonatkozó megállapításait a korpuszból ellenőrzöd, mielőtt javítasz** (`python3 tools/par.py <forráskód> <§>`). Mivel az audit nem független az olvasótól, a lista `allaspont` és `gyakorlat_…` jellegű pontjaira épülő bekezdéseket a diffben külön megnézed.
3. *Javítandó:* a pontszerű hibát a munkapéldányban javítod a korpuszból, a bejegyzéssel együtt (`kontroll.py leltar NN`; az `ellenorizte` mezőbe az kerül, hogy a javított mondatot a § szövegével magad vetetted össze), majd `bash tools/kapuk.sh --tetel NN`. *Visszaadandó:* a tétel a lelettel az íróhoz megy, utána újra audit.
4. **`levezetes` jel** (`"levezetes": "korpusz"`): csak a köteget vezető beszélgetés adhatja, alügynök nem. Feltételei: (a) a bekezdés minden állítása a megnevezett §-ok szövegéből következik – magad veted össze; (b) nem utal bírói gyakorlatra, szakirodalomra, jogtörténetre, külföldi jogra (a „forrás” vagy „történet” jelzőt kiváltó normafogalomnál legalább 40 karakteres `jelzo_indok`; külföldi jogra nincs kivétel); (c) az audit ugyanezt megerősítette; legalább két §, legalább 40 karakteres megjegyzés. Ha bármelyik hiányzik: a mondatot a normából javítod vagy törlöd, és csak utána adod a jelet. A megadott jeleket az `ALLAPOT.md` kötegszakaszában felsorolod.
5. **API-lelet teljessége:** a `kontroll/NN.json` `api_lelet` sorainak száma = a lelet négy lezárandó típusának pontjai; ha nem egyezik, a tétel nem zárható. „Helytálló” lezárás csak akkor adható, ha a korpusz §-a szó szerint cáfolja a leletet, és a § a sorban szerepel.
6. **Megálló:** ha egy tételt **átvétel miatt** kell visszaadni, az a tétel megáll, és Attila dönt; a többi megy tovább.

### 6.7 Átvétel a mentőágra, kapuk, napló, commit (tételenként, a lezárás után)

1. `cp "$M/NN/NN.txt" "$R/NN.txt" && cp "$M/NN/kontroll/NN.json" "$R/kontroll/NN.json"`; `python3 tools/kontroll.py leltar NN` (új bejegyzés nem keletkezhet).
2. `python3 tools/seged_osszefesul.py "$ATADO/NN_seged.json"` és `… "$ATADO/NN_seged_olvaso.json"` (kommentár-térkép, IJOTEN-jegyzék, bővítési lista). Kommentárszöveg itt sem kerülhet fájlba.
3. **Új doboz kizárólag programmal** (az író jelentése alapján): `python3 tools/s5/doboz_beszur.py NN "<forráskód> <egység> [(bek.)]" --utan "<a tételfájl sorának pontos kezdete>"` (előbb `--ir` nélkül, utána `--ir`). Ha a program hibával lép ki: Központi teendő, a mérce-naplóban a 6. elem „függőben (doboz-igény)”.
4. `python3 tools/s5/doboz_javit.py --sor --ir NN | tail -2` → „módosítandó doboz: 0”.
5. `bash tools/kapuk.sh --tetel NN` → kilépési kód 0, a tétel lezárva. A kapu termékek nélkül is fut; termék-előfuttatás nem kell.
6. `jelentesek/KP-2_merce.md`: a tétel szakasza – szakaszonként a hét elem (megvan / mélyítve / függőben / –) és egy mondat arról, mi változott; források (korpusz-§-ok, IJOTEN-szócikkek lezárási dátummal, a kommentár tartománya); hatályossági megjegyzés; ami nem került a tételbe.
7. Commit tételenként, csak fájlnévvel:
   ```
   git add NN.txt kontroll/NN.json
   git commit -m "KP-2 <azon>: NN. tétel – kommentárkör (író: Opus, olvasó-auditor: Opus; lelet és diff: tételsor-chat)"
   ```
8. Minden lezárt köteg után a segédfájlok, a napló és az állapot egy commitban, és feltöltés **csak a mentőágra**:
   ```
   git add kontroll/_kommentar_terkep.json kontroll/_ijoten_jegyzek.json kontroll/_bovites.json \
           jelentesek/KP-2_merce.md jelentesek/koltseg_naplo.csv jelentesek/kontroll_allapot.md \
           jelentesek/kontroll_allapot.json jelentesek/bovitesi_lista.md ALLAPOT.md
   git commit -m "KP-2 <azon>: a <T1>–<T3>. tétel kötege – segédfájlok, mérce-napló, állapot"
   git -c push.negotiate=true push -u origin "$AG"
   git worktree remove "$M/<NN>"        # tételenként, a push után
   ```
9. **`ALLAPOT.md`:** új legfelső szakasz: `## <dátum> – KP-2 kommentárkör, <T1>–<T3>. tétel (ág: <mentőág>)`, első sora a kapu ÁLLAPOT-sora szó szerint; utána tömören: lezárt tételek, commitok, visszaadások, doboz-igények, a megadott `levezetes` jelek (azonosító, §-ok), a bővítési lista új tételei, a böngészőhívások száma tételenként.
10. **A mentőág lezárása befésülésre** (legfeljebb naponta egyszer, amikor van lezárt tétel rajta): `bash tools/kapuk.sh --visszaallit` → kilépési kód 0; az `ALLAPOT.md` legfelső szakaszának címe tartalmazza a mentőág nevét és az „auditálva, befésülhető” szöveget, első sora a kapu ÁLLAPOT-sora; a záró commit üzenete „Audit (tételsor-chat):” kezdetű, benne az `ALLAPOT.md`; push. Attila parancsa (az üzenetben, kódblokkban): `cd <helyi klón> && bash tools/befesul.sh <mentőág>`. A lezárt mentőágra több commit nem kerül; a munka az új mentőágon megy tovább, a befésülésre várni nem kell. A termékgyártás (S6) a célágra befésült tételeken indul.
11. **Üzenet Attilának hullámonként egy** (4. pont formájában); ha van befésülendő ág, a parancs ebben áll.

## 7. Ágrend

| Ág | Mire | Ki ír rá |
|---|---|---|
| `main` | jóváhagyott állapot | csak Attila (`git merge --ff-only`) |
| `elokeszites-<dátum>` | S0–S4 | központi chat, előkészítő alügynök |
| `kp2-<azon>-<sorszám>` | S5 mentőágak | tételsor-chat |
| `tg1-<tételek>`, `rt-<tételek>` | S6 munkaágak | Cursor-ügynök; az audit commitja |
| `celag` (`termekek-<azon>`) | a befésült, auditált állapot | csak Attila `tools/befesul.sh` parancsa |

Push: `git -c push.negotiate=true push origin HEAD:<ág>`. Befésült munkaágra commit nem kerül. Párhuzamos feltöltés ütközésénél rebase a távoli csúcsra; erőltetett feltöltés nincs.

## 8. Minőségbiztosítás – mit, mivel, mikor

| Mit | Eszköz / mód | Mikor | Hibánál |
|---|---|---|---|
| Doboz = korpusz, betűre | `ellenorzes.py`, `doboz_teljesseg.py` | S3, és minden szövegváltozás után | a tétel nem zárható |
| Minden bekezdés forrása | `kontroll.py kapu` | tételenként | a tétel nem zárható |
| Átvétel | az auditor olvasása (a `menet: 2` bekezdések mondatról mondatra) + egyezésmérő (küszöb 0,10 arány vagy 2-es találatsor; a jel hiánya nem bizonyíték) | tételenként, a végleges szövegen | visszaadás; megálló |
| Jogi helyesség | olvasó-auditor: joghatás, határidő, feltétel, kivétel a korpuszból; gépi minta | tételenként | lelet → javítás → a diff a tételsor-chatnél |
| Termékek | 12 kapu (`kapuk.sh`), megjelenítő-próba, ágaudit | kötegenként, befésülés előtt és után | a munkaág nem fésülhető be |
| Lefedettség | `lefedettseg_audit.py`, `hangszoveg.py lefed` | kötegenként | elkészül vagy kötött kóddal indokolt |
| Régi termékek | `rt2_ellenor.py` + mindent végigolvasó független audit | RT-kötegenként | javítókör, maradványlista |
| Szkriptek | kódaudit + próbafutás | minden `--apply` előtt | nem futhat |
| Felület és hang | Attila admin-tesztje | S7-től | tartalmi hiba a tárolóban javul |

## 9. Megállók (az érintett tétel vagy lépés áll, a többi megy tovább; Attila dönt)

1. Előírt forrás hiányzik a korpuszból, vagy időállapota nem igazolható.
2. Egy tételt átvétel miatt vissza kell adni.
3. A kommentár-tartomány 700 elemnél nagyobb, vagy nem fér bele az olvasó munkájába.
4. A kommentárkötet nem azonosítható, vagy a beépített böngésző nem érhető el.
5. A kiírás és a jegyzetek tételszáma vagy tárgya eltér; a kiírás hatályon kívül helyezett jogszabályt nevez meg, és nincs rá `tetelForras`.
6. Kapu nem zárható 0-ra a módszer megváltoztatása nélkül.
7. Próbafutás száma eltér a tároló számától, vagy ütközés van az élő adattal.
8. API-köteg legrosszabb esete nem fér a maradék kreditbe.
9. Bármi, ami visszafordíthatatlan és többféleképpen dönthető el; és minden, amire ez a szabályzat nem ad választ.

A megálló üzenetének első mondata maga az akadály; utána egy mondat arról, mi megy tovább, és a döntéshez szükséges két-három tény. Javaslat a folyamat átalakítására nem része a megálló üzenetének.

## 10. Kötelező fájlok tételsoronként

- `ALLAPOT.md` – csak az aktuális állapot: legfelül a kapu sora; „Tételsor-specifikus”; „Egyedi eltérések”; „Attila teendői” (egy listában, parancsokkal); „Központi teendő”. A régi szakaszok helye az `ALLAPOT_archiv.md`.
- `tetelsor/beallitas.json`, `tetelsor/tetelsor.json`, `tetelsor/forrasok.json`; `korpusz/manifest.json`, `korpusz/allapot.json`.
- `kontroll/NN.json`, `kontroll/_bovites.json`, `kontroll/_kommentar_terkep.json`, `kontroll/_ijoten_jegyzek.json` – forrásszöveg nélkül.
- `jelentesek/`: `KP-2_merce.md`, `koltseg_naplo.csv`, `api_koltseg.csv`, `api/`, auditleletek, `RT-2_javitasok.json`.
- `termekek/`, `termekek/lefedettseg_indok.json`, `termekek/_gyartasra_var.json`, `termekek/_elesites_elott.json`.
- Tételsoronkénti utasításfájl nincs: az `utasitasok/` mappa régi példányai hatályukat vesztették, helyettük a `tools/szabalyzat/` él.

## 11. Eszközjegyzék (a tároló `tools/` mappájában; ami itt és a szerep-szabályzatokban nincs megnevezve, azt a munka nem használja)

`eszkoz_ellenor.py` · `korpusz_felmeres.py` · `alapfelvetel.py` · `jegyzet_txt.py` · `hatalyossag.py` (`ujjlenyomat`, `jelentes`, `kapu`) + `hatalyossag/osszevet.js` · `ellenorzes.py` · `doboz_teljesseg.py` · `s5/doboz_javit.py` · `s5/doboz_beszur.py` · `api_koteg.py` (`keszit`, `kuld --plafon`, `allapot`, `letolt`, `fokonyv`) · `s5/koteg.py` (`atiras`, `ellenorzo`) · `s5/ment.py` · `s5/alkalmaz.py` · `s5/osszesito.py` · `kontroll.py` (`leltar`, `kapu`, `minta-audit`) · `kapuk.sh` (`--tetel NN`, `--visszaallit`) · `par.py` · `kiiras_lefed.py` · `egyezes_elokeszit.py` + `kommentar/betolto.js`, `kommentar/egyezes.js` · `seged_osszefesul.py` · a termékgyártás eszközei (`TG_termekgyartas.md`) · `rt2_ellenor.py` · `lefedettseg_audit.py` · `csomag_gyart.py` · `megjelenito_teszt/futtat.sh` · `elesites_kapu.py` · `hang_koltseg.py` · `befesul.sh` (csak Attila).

## 12. Indító szöveg új beszélgetésnek (ezt kapja a dolgozó ügynök – mást nem)

```
A <tételsor> gyártását folytatod. Tároló: <tároló>; ág: <ág>.
Olvasd el a tároló tools/szabalyzat/00_GYARTASI_SZABALYZAT.md és ALLAPOT.md fájlját, és aszerint dolgozz.
Más utasítás nincs; új módszert nem vezetsz be és nem javasolsz. Az első üzeneted legfeljebb három sor.
```
