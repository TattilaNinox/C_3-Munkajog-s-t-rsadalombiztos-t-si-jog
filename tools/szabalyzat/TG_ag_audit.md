# TG-A – a termék-munkaág auditja (audit-alügynök; minden tételsorra)

**Hely:** `<tételsor-tároló>/tools/szabalyzat/TG_ag_audit.md` – a közös eszközkészlet zárolt másolata, helyben nem módosítható (`python3 tools/eszkoz_ellenor.py` → eltérés 0). **Karbantartja:** a központi chat (a közös készletben). **Vezérutasítás:** `tools/szabalyzat/00_GYARTASI_SZABALYZAT.md` (S6 fejezet). **Kapcsolódó:** a gyártás szabályai – `tools/szabalyzat/TG_termekgyartas.md` (a továbbiakban: TG).
**Ki végzi:** a központi chat által indított audit-alügynök, a munkaág kicsekkolt munkapéldányában. **A feladatban a központi chat megadja:** a munkaágat, a tételek számát, a munkapéldány útvonalát, az élő hangágat (`<hangalap>`, TG 0. pont), és 4 tételnél nagyobb kötegnél a szerepet (1. pont). A célág a `tetelsor/beallitas.json` `celag` kulcsa.
**Előzmény:** a gyártó ügynök a lezárt tételek termékeit a munkaágon legyártotta és feltöltötte (TG).

## 1. Egy vagy két audit-alügynök

1. **Legfeljebb 4 tételes köteg:** egy audit-alügynök végzi a 3. pont minden lépését.
2. **5–6 tételes köteg:** két audit-alügynök, külön munkapéldányban:
   - **„A” (fák és számolók):** 3/1., 3/2. (a fákat, számolókat, rögzített okokat érintő „Központi teendő” pontok), 3/3. Kapukat nem futtat; a javításai után csak a `python3 tools/fa_ellenor.py` és a `python3 tools/szamolo_ellenor.py` utolsó sorát adja meg.
   - **„B” (mátrixok, vázlat, felolvasószöveg; zárás):** 3/2. (a többi „Központi teendő” pont), 3/4., 3/5., 3/6., majd a központi chat jelzésére, az „A” javításainak átvétele után 3/7., egyszer, a két alügynök javításait együtt tartalmazó munkapéldányon.
   - Ugyanazt a fájlt ketten nem javítják: az „A” csak a `termekek/dontesi_fa/`, a `termekek/szamolo/` és a `termekek/lefedettseg_indok.json` számoló-bejegyzéseit; a „B” csak a `tools/matrix_adat.py`-t, a `termekek/fogalommatrix/`-ot, a `lefedettseg_indok.json` mátrix-bejegyzéseit, a `termekek/hangos_vazlat/`-ot és a `tts/`-t. A javításokat a központi chat fűzi össze.

## 2. Tilalmak

1. Böngészőt, megjelenítőt nem nyitsz, képernyőképet nem készítesz; a megjelenítő-próbát nem te futtatod (5. pont).
2. Adatbázist és Storage-ot nem írsz; importot, telepítést, `firebase`-parancsot nem futtatsz; hangot nem generálsz; mp3 a tárolóba nem kerül (próbahang csak a `/tmp` alatt).
3. Git-parancsból csak olvasót futtatsz (`status`, `diff`, `log`, `show`); commit, push, checkout, merge nincs – a commitot a központi chat készíti. A `main` ágat és a célágat nem érinted; `git add -A` tilos.
4. A `tools/` mappa a közös készlet zárolt másolata, nem módosítható (`python3 tools/eszkoz_ellenor.py` → `eszkoz_ellenor: fájl N, eltérés 0`); kivétel a helyi `tools/matrix_adat.py` (mátrixjavítás).
5. Nem módosítod: `NN.txt`, `kontroll/`, `korpusz/`, `tetelsor/`, `kviz/`, `tanulokartyak/`, `memoriautvonal/`, `hezagpotlok/`, `ALLAPOT.md`.
6. A tárolóba nem kerülhet kulcs, `service-account.json`, felhasználói adat, mp3.
7. A `hangmeta.py` és a `hangulat_szoveg.py` kizárólag `--alap=<hangalap>` kapcsolóval futhat.
8. Tiltott szavak: „tananyag”, „ZH-felkészítő”; a tételszövegben a „korpusz” szó nem állhat. Minden program Python 3.9-en fut.
9. A mérce a lezárt tétel szövege és a `korpusz/`: a termék azt nem bővítheti és nem javíthatja. Ha a tétel szövegében hibát látsz, nem javítod, hanem a leletbe írod. Minden §-t a `korpusz/` fájljából olvasol ki, nem emlékezetből.

## 3. Mit olvasol, mit futtatsz

1. **Tiltott fájlok:** `git diff --name-only origin/<celag> HEAD` – változás csak `termekek/`, `tts/`, `jelentesek/` alatt és a `tools/matrix_adat.py`-ban lehet; minden más lelet. A `tools/matrix_adat.py` diffjében törölt sor csak a köteg tételeinek blokkjában lehet.
2. **A gyártó jelentése** (`jelentesek/TG-1_<tételek>_jelentes.md`): elolvasod; a „Központi teendő” pontjait a leletben egyenként megválaszolod (elintézve / a központi chatre vár).
3. **Döntési fák** (a köteg új és módosított fái): minden kérdés, ág és eredmény mellett § áll, és a szöveg a hivatkozott § korpusz-szövegéből következik; minden idézet szó szerinti; minden példa a törvényből közvetlenül kiolvasható eset, és a megadott válaszokkal a megadott eredményre jut; a megjegyzés minden mondata mögött § vagy a lezárt tétel mondata áll; minden §-hivatkozás egyértelmű (melyik § melyik bekezdése). Vitatott értelmezésből vagy bírói mérlegelésből nem készülhet ág. A számolók és a számoló-indokok (`termekek/szamolo/`, `lefedettseg_indok.json`) a TG 5.4 pontja szerint helytállók-e.
4. **Fogalommátrixok** (a köteg összes mátrixa): a TG 5.3 pontjának címkeszabálya (hű, önmagában érthető, nincs lógó kötőszó vagy visszautalás, a megfelelő sorhoz és oszlophoz tartozik, a kérdésre felel); a bevezető és az összegzés a tétel szövegéből következik; a mátrixok rögzített okai (`lefedettseg_indok.json` új bejegyzései) helytállók-e.
5. **Hangos vázlat:** a kulcsmondatok aránya (50–60%); minden főpontból és minden elhatárolásból van-e kulcsmondat (kivéve a TG 5.5/3. pontja szerint kizárt mondatok miatt); a vázlathang-szövegben nincs-e felolvashatatlan elem.
6. **Felolvasószöveg:** tételenként legalább három darab teljes elolvasása (köztük egy doboz és az ELHATÁROLÁSOK), és célzott keresés az új darabokban a felolvashatatlan elemekre (§-jel, a §-hivatkozás számjegyes alakja – pl. `5:44` –, római szám, feloldatlan rövidítés, zárójeles betűjel, latin szó kiejtési sor nélkül). `python3 tools/tts_ujra.py NN` minden érintett és minden korábban lezárt tételre; várt: `próba (nem írt): változó darab 0, új darab 0`. A betűjel felolvasott alakja („per a.: paragrafus”, „bé pont”, „a.: pont” – a magánhangzó után „.:”) eldöntött szabály, nem lelet; betűzve maradt jogszabály-rövidítés viszont lelet.
7. **Kapuk:** `bash tools/kapuk.sh --visszaallit` (a 12 kapu és előellenőrzésként az `eszkoz_ellenor`; az időbélyeges jelentésfájlokat a program visszaállítja). A leletbe csak az utolsó sor kerül; várt: `KAPUK: 12 futott; eltérés/hibás: 0`, kilépési kód 0. Ezen felül ellenőrzöd, és csak az eltérést írod le: az ÁLLAPOT-sor a munkaág `ALLAPOT.md`-je szerinti; a `doboz_teljesseg` „hiányos bekezdés” száma és a `lefedettseg_audit` nyitott párjainak száma az `ALLAPOT.md` szerinti (illetve annyival kevesebb, amennyit a köteg lezárt); a köteg tételei nincsenek a nyitott párok és a hanglefedettség táblájában; a „csomag sha256” sor lenyomata (a leletbe kerül, az 5. ponthoz). Ha a program „ÉRDEMBEN VÁLTOZOTT” fájlt ír ki, a leletben megnevezed (a központi chat dönt róla).

## 4. Javítás

1. Amit a 3/3–3/6. pontban hibásnak találsz, és a termék szintjén javítható, kijavítod: fa – a JSON-ban; számoló – a JSON-ban és a `lefedettseg_indok.json`-ban; mátrix – `tools/matrix_adat.py`, utána `python3 tools/matrix_ir.py`; kiejtés – `tts/_ujra_terv.json` `kiejtes` táblája, utána `python3 tools/tts_ujra.py NN --ir`, és a TG 4. pontjának kötött sorrendje (`hangulat_szoveg.py --alap=<hangalap> --ir`, `hangmeta.py --alap=<hangalap>`, `vazlat_hang.py NN`, `vazlat_tts_terv.py`, `jegyzet_html.py --mind`).
2. Utána az érintett ellenőrzőt újrafuttatod (`fa_ellenor.py`, `szamolo_ellenor.py`, `matrix_ellenor.py`, `tts_ujra.py NN`).
3. Közös eszköz (`tools/` más fájlja) hibáját nem javítod: a leletben pontosan leírod (fájl, függvény, a hiba oka, javasolt javítás).

## 5. A megjelenítő-próba (a központi chat futtatja)

`bash tools/megjelenito_teszt/futtat.sh <admin klón útvonala>` – termékkötegenként egyszer, az audit javításai után; várt összegző sor: `ellenőrzések: N, hiba: 0`. Csak akkor fut újra, ha utána a csomag sha256 lenyomata vagy az admin `web/szakvizsga/termekek.html` megváltozott. Az audit-alügynök nem futtatja; a 3/7. pont lenyomatát adja át hozzá.

## 6. Leletosztályok

| Osztály | Mi | Ki intézi |
|---|---|---|
| TILTOTT FÁJL | a 3/1. pont szerinti, megengedett körön kívüli változás | központi chat |
| JAVÍTVA | termékszintű hiba (fa, számoló, indok, mátrix, vázlat, kiejtés), amelyet a 4. pont szerint kijavítottál | auditor |
| TÉTELHIBA | a lezárt tétel szövegének hibája (nem javítod) | központi chat |
| ESZKÖZHIBA | a közös eszköz hibája (fájl, függvény, ok, javasolt javítás) | központi chat |
| KÖZPONTI TEENDŐ | a gyártó jelentésének pontja: elintézve / a központi chatre vár | auditor / központi chat |
| KAPUELTÉRÉS | a 3/7. pont bármely eltérése, „ÉRDEMBEN VÁLTOZOTT” fájl | központi chat |

## 7. Lelet és ítélet (a végső üzeneted; legfeljebb kb. 60 sor)

1. **Ítélet – az első mondatban:** „Akadály nincs.” vagy „Akadály: …” (TILTOTT FÁJL, a kapuk nem 0, javíthatatlan termékhiba). Két alügynöknél a szereped („A” vagy „B”). Az „auditálva, befésülhető” minősítést a központi chat adja: az audit commitja („Audit (központi chat): …”) és az `ALLAPOT.md` szakasza (az ág nevével, „auditálva, befésülhető”) a munkaágra kerül; ez a `tools/befesul.sh` feltétele.
2. Tiltott fájl: van / nincs.
3. JAVÍTVA – táblázatban: fájl, mi volt, mi lett, miért (§ vagy tételmondat).
4. Amiben a központi chatnek döntenie kell: TÉTELHIBA, ESZKÖZHIBA, a nyitott KÖZPONTI TEENDŐ pontok.
5. A kapuk utolsó sora és a csomag sha256 lenyomata („B” szerepben, illetve egy alügynöknél); az „A” szerepben a `fa_ellenor` és a `szamolo_ellenor` utolsó sora.
6. Az eszközhívások (böngésző nélküli fordulók) hozzávetőleges száma – a `jelentesek/koltseg_naplo.csv`-hez.
7. `git status --short` kimenete.
