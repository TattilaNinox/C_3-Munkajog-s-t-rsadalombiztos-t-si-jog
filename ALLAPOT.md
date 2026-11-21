# C/3 Munkajog és társadalombiztosítási jog – állapot

**A rend: `tools/szabalyzat/00_GYARTASI_SZABALYZAT.md`** (a végleges gyártási szabályzat, a közös készlet zárolt másolata – készlet `732c88b`; a dolgozó beszélgetés ezt és ezt az állapotfájlt olvassa). A központi chat vezeti (Attila döntése, 2026-11-19, `01_dontesek.md`).

## 2026-11-19 – előkészítés indul (ág: `elokeszites-2026-11-19`)

- **Kiírás:** `tetelsor/C3_kiiras_2026.pdf`, szövege: `tetelsor/kiiras_2026.txt` (Attilától, 2026-11-19).
- **Korpusz-felmérés (első, gépi; `jelentesek/korpusz_felmeres.md`):** `korpusz_felmeres: forrás 114, megvan 109, hiányzik 5, nem hivatkozott korpuszfájl 23`
- **Szakaszok:** S0 – kész (2026-11-19: közös eszközök szinkronban, `tetelsor/beallitas.json`); S1 – kész (2026-11-19: alapfelvétel `hiba 0`, munkaszöveg `eltérés 0`; a feloldatlan és a némán elvesző hivatkozások lent); S2 – a felmérés kész, a hatályossági összevetés (2026. december 9. utáni állapot) nem indult.

## S0–S1 (2026-11-19)

A programok utolsó sora szó szerint:

- `eszkoz_ellenor: fájl 63, eltérés 0`
- `alapfelvetel: tétel 56, feloldott 393, feloldatlan 13, hiba 0`
- `jegyzet_txt: tétel 56, rész 201, karakter 4177520, eltérés 0` (előtte figyelmeztetés: „ellenőrizendő részsorrend (a tartalomban nincs római főcím): 02, 06, 08, 19, 22, 23, 26, 27, 35, 36, 42, 44, 50, 53, 54, 55, 56”)
- `ellenorzes`: `hiányos bekezdés: 68`
- `doboz_teljesseg` (első sor): `dobozok: 695, eltérés: 4; hiányzó forrás: []; lefedettségi hiány: 292 elem 54 tételben`

A tételszám 56: a kiírás 1–56. tétele és a `jegyzetek/manifest.json` sorszámai (1..56, 201 rész) egyeznek. A `kiiras_tetelek()` a gondolatjeles forráslistás formát helyesen bontja: mind az 56 tétel `szoveg` mezője a teljes forráslistát tartalmazza (oldalszám-sorok kiszűrve). A korábbi felmérés „55 tétel”-e a `korpusz_felmeres.py` számolása, nem az alapfelvételé.

### Feloldatlan (13) – egyik sem valódi korpuszhiány

- **EUB-ítéletek (3):** 23. tétel C-518/15 (Matzak) és C-214/20 (MG kontra Dublin City Council), 26. tétel C-624/19 (K és társai kontra Tesco). **A szövegük megvan a korpuszban:** `62015CJ0518 A Bíróság ítélete (ötödik tanács), 2018. február 21. Vi.._.txt`, `62020CJ0214 A Bíróság ítélete (ötödik tanács), 2021. november 11. M.._.txt`, `62019CJ0624 A Bíróság ítélete (második tanács), 2021. június 3. K e.._.txt` (25–37 ezer karakter, teljes ítélet). Az általános feloldás a CELEX-nevű fájlhoz nem képez „C-518/15” kulcsot. A központi chat utasítása szerint ezek a hiánylistán maradnak; `megfeleltet` nem került be, mert a kiírás nem elírás. Döntés kell (Központi teendő).
- **Ptk könyves tartomány rövidített végponttal (10):** 1. tétel 2:42–54; 2. tétel 6:15–17, 6:64–70; 6. tétel 6:118–119; 27. tétel 6:46–56, 6:193–201, 6:203–207; 28. és 29. tétel 6:518–534; 36. tétel 6:186–189. A §-ok a korpuszban megvannak; az eszköz a végpontot („54”) könyvszám nélkül olvassa (Központi teendő).

### Valódi korpuszhiány

- nincs (a kiírás minden megnevezett forrása megvan a korpuszban).

### `kiirasElirasok`

- `kihagy: 95/46/EK` – az 1. tételben csak a GDPR címében áll („…valamint a 95/46/EK irányelv hatályon kívül helyezéséről”); hatályon kívül helyezett irányelv, nem önálló előírás.
- `kihagy: 2010/18/EU` – a 24. tételben csak a (EU) 2019/1158 irányelv címében áll („…és a 2010/18/EU tanácsi irányelv hatályon kívül helyezéséről”); hatályon kívül helyezett irányelv, nem önálló előírás.
- `megfeleltet`: üres.
- `nemHivatkozas: a Nemzetközi Munkaügyi Konferencia 1949. évi 32. ülésszakán elfogadott 95. számú Egyezmény kihirdetéséről` (2026-11-19) – a 27. tételben a 2000. évi LIV. törvény (az ILO 95. sz. egyezmény kihirdetése) címének folytatása; a törvény a tétel feloldott hivatkozásai között van (teljes fájl), a szövegrész nem önálló forrás.
- `nemHivatkozas: cikk (3) bekezdés` (2026-11-19) – a 37. tételben a kiírás elírása („2001/23/EK irányelve … 3. § cikk (3) bekezdés”): a „3. §” feloldott hivatkozásként felhasználódik, az irányelv a tétel feloldott hivatkozása (teljes fájl, így a 3. cikke is), a maradék „cikk (3) bekezdés” nem önálló hivatkozás. Utána: `alapfelvetel: tétel 56, feloldott 472, feloldatlan 0, hiba 0`.

### A beállítás döntései

- Átfogó (`atfogo`): csak az Mt. (a kiírás bevezetője).
- A 115/2021. Korm. rendelet (`Fhr`) és a 33/1998. NM rendelet (`NMr33`) forrásként szerepel, mert a kiírás §-sal hivatkozik rájuk; nélkülük a §-aik a megelőző törvényhez (Fszftv., Mvt.) kerültek volna (4., 6., 8., 35. tétel).
- A 4. tétel két ILO-egyezménye (2000. évi LXIX., 2001. évi XXVII. tv.) forrásmintát kapott, mert a kiírás „kihirdetve … törvénnyel” alakját az általános mód nem ismeri fel.
- 50. tétel: a Kjt. teljes nevének és az 1992. évi XXIII. törvénynek (`Ktv`) a mintája választja el az AB-határozatok címében említett §-okat (különben az Mt.-hez kerültek volna). Emiatt a tétel Kjt. 30., 33., 37., 78., 87. §-a és Ktv. 17. §-a az AB-határozatok címéből származik, nem önálló előírás.
- 52. tétel: a pont nélküli felsorolás (Kit, Kttv, Küt, Hjt, Hszt, Hajtv, Nav Szjtv.) mintát kapott; ezek „bevezető rendelkezései” egész fájlként kerülnek a tételhez.

## A közös készlet KE-1 javítása után (2026-11-19, központi chat)

- `alapfelvetel: tétel 56, feloldott 472, feloldatlan 2, hiba 0`
- `dobozok: 915, eltérés: 7; hiányzó forrás: []; lefedettségi hiány: 104 elem 34 tételben`
- `hiányos bekezdés: 17`
- A korábbi „Központi teendő” pontok közül a hivatkozásfeloldás, a cikk-egység és a vegyes számozás javítva (admin-commit `d1c2925`). Az új feloldatlan sorok a maradékvizsgálatból jönnek (`jelentesek/alapfelvetel.md`): beállítást kérnek (`kiirasElirasok`), nem korpuszhiányt jelentenek.

## Attila teendői

## Központi teendő

- **EUB, CELEX-nevű fájlok** (`tools/korpusz_felmeres.py` `fajl_kulcsok()`, illetve `alapfelvetel.py` `hatarozatok_altalanos()`, amely csak a fájl első nem üres sorát nézi, itt „62015CJ0518[1]”): a „6ÉÉÉÉCJNNNN” névből nem lesz `('eub','C','NNNN','ÉÉ')` kulcs. Javaslat: CELEX-felismerés a kulcsképzésben, vagy döntés `megfeleltet`-ről a három ügyre.
- **Néma veszteség (nem jelenik meg a feloldatlanok között, a fájl a korpuszban megvan):** 1. tétel 137/B/1991. AB hat.; 50. tétel 600/B/2000., 826/B/1996., 44/B/1993., 495/B/2001. AB hat. (a `korpusz_felmeres.hivatkozasok()` a „N/B/ÉÉÉÉ.” alakot nem ismeri fel; a fájlnév „600_B_2000” sem ad kulcsot); 23. tétel C-303/1998. SIMAP és C-151/2002. Jaeger (négyjegyű év; a fájl kulcsa „C-303/98”); 38. tétel 1/2004. Közigazgatási-polgári jogegységi határozat (a szöveg nem ad kulcsot, a fájl `1_2004. számú KPJE határozat _ Kúria.txt`); 39. tétel MTVSZ Kódex (`mtvsz_kodex.txt`; név szerinti forrás, az általános mód kihagyja). Javaslat: a minták bővítése a közös eszközben, vagy tételszintű `tetelForras` Attila döntésével.
- **Fejezeti átfogó előírás:** a „Közszféra munkajoga” (Kit., Kttv., Kjt., Küt.) és a „Társadalombiztosítási jog” (Tbj., 883/2004/EK, 987/2009/EK) fejezet bevezetője fejezetszintű átfogó ismeretet ír elő; a `kiiras_tetelek()` a fejezetfej utáni bevezetőt eldobja, a beállítás `atfogo` kulcsa csak az egész tételsorra érvényes. A 883/2004/EK és a 987/2009/EK így egyetlen tételhez sem kötődik. Javaslat: fejezetszintű `atfogo` (pl. `atfogoCsoport`).
- **`alapfelvetel.py` `egysegek()`:** (1) könyves tartomány rövidített végponttal („6:15-17. §”) → feloldatlan; javaslat: a végpont örökölje a kezdőpont könyvszámát; (2) római tartomány pont nélküli kezdőponttal („I-II. cikk”, „V-XIII. cikk”, „XVII-XVIII. cikk”, 1. tétel) → csak a végpont kerül be (II, XIII, XVIII), az I., V–XII., XVII. cikk némán kimarad; (3) „Ebtv. 42./G. §” (25. tétel) → a 42/G. § kimarad; „Tbj. 5; 6-22.§” (54. tétel) → az 5. § kimarad.
- **`felold()` cím:** a gondolatjeles kiírásban a cím végén „ -” marad (a `strip(' ;,')` nem veszi le); a 41. tétel címébe a forrásmegnevezés eleje is bekerül („… követelménye - a foglalkoztatás-felügyeleti hatóság tevékenységéről szóló”). A jegyzetek manifestjének címe tiszta.
- **`kozos.py` `FEJLEC`:** `parMinta: egyszeru` mellett a „Ptk. 6:518. §” dobozfejléc nem illeszkedik (egyszerű számozásnál a `PAR` nem enged kettőspontot); a 153 Ptk-doboz így nem kötődik forráshoz.

## S2 – korpuszcsere a letöltött jogszabályokból (2026-11-19, központi chat)

- **Cserélve és ellenőrizve (19):** a C3 mappa 20 fájljából 19; a Pp., a Vht. és a Ptk. az A/2 ellenőrzött fájljára cserélve.
- **Jövőbeli időállapottal cserélve (Attila döntése, 2026-11-19 18:00; szakaszonként ellenőrizve):** Art. (2027.01.01-i időállapot).
- **Módszer:** Attila letöltése (net.jogtar.hu, mentett oldal) → átalakítás a korpusz szokása szerint → szakaszonkénti (20-as csoportokban mért) ujjlenyomat-összevetés a 2026.12.09-én hatályos időállapottal; csak az került a korpuszba, ahol az eltérő csoportok száma 0. A `korpusz/manifest.json` érintett sorai: új méret és sha256, `idoallapot`, `hatalyossag.jogallapot: 2026-12-09`. **A cserélt fájlok a Storage-ba még feltöltendők (S8).**
- **Közös készlet KE-2** (admin-commit `0cb4b3b`) szinkronizálva; a dobozok a cserélt korpuszból újraépítve (`doboz_javit.py --sor --ir`), a második futás: `módosítandó doboz: 0`.
- `alapfelvetel: tétel 56, feloldott 466, feloldatlan 1, hiba 0` (39. tétel: „Eljárási és Magatartási Kódexe I–III. rész” – forrás-beállítás kell)
- `dobozok: 915, eltérés: 1; hiányzó forrás: []; lefedettségi hiány: 103 elem 34 tételben`
- `hiányos bekezdés: 1` (32. tétel, Efo. tv. 25. § – a doboz a jogharmonizációs záradékot idézi, tartalmi kérdés)

## Hatályon kívül helyezett jogszabályok a kiírásban (2026-11-19, Attila döntése 18:44)

- **Döntés:** ahol a kiírás hatályon kívül helyezett jogszabályt nevez meg, a tétel a helyébe lépett hatályos jogszabályra épül, és egy mondatban jelzi, hogy a kiírás a régit nevezi meg; a régi korpuszfájl tájékoztatásként marad.
- 21. tétel: 15/2023. (VII. 13.) GFM r. (hatálytalan 2025.01.01.) → **10/2025. (IV. 30.) NGM r.** a 2026. évi munkaszüneti napok körüli munkarendről.
- 26., 34. tétel: 573/2022. (XII. 23.) Korm. r. (hatálytalan 2023.12.01.) → **426/2025. (XII. 23.) Korm. r.** (minimálbér, garantált bérminimum 2026).
- 25., 52. tétel: 2012. évi CCV. tv. – Hjt. (hatálytalan 2024.07.01., 2024. évi XX. tv. 31. §) → **137/2024. (VI. 28.) Korm. r.** a honvédek jogállásáról (Hjkr.).
- 50. tétel: az 1992. évi XXIII. tv. (Ktv.) csak egy AB-határozat címében szerepel – nincs teendő.
- A három új rendelet a korpuszban (net.jogtar.hu, szakaszonként ellenőrizve: eltérés 0). **A `beallitas.json` megfeleltetése (`tetelForras`) a KE-3 készletjavítás után következik** (központi chat).

## Közös készlet KE-3 (2026-11-19, központi chat)

- Szinkronizálva (admin-commit `9ceab3a`): új `tools/s5/doboz_beszur.py` (doboz beszúrása a korpuszból), a `kontroll.py` minden forrás §/cikk-hivatkozását ellenőrzi és termékek nélkül is fut, betűs cikkszám, táblasor nem cikkfej, kihagyott megnevezés, záró sor levágása javítva.
- `alapfelvetel: tétel 56, feloldott 467, feloldatlan 1, hiba 0` | `dobozok: 915, eltérés: 1; hiányzó forrás: []; lefedettségi hiány: 104 elem 34 tételben` | `hiányos bekezdés: 1`
- A 21., 25., 26., 34., 52. tétel a kiírás hatályon kívül helyezett jogszabálya helyett a hatályosra épül (`tetelForras`: 10/2025. NGM r., 426/2025. Korm. r., 137/2024. Korm. r.; Attila döntése 2026-11-19 18:44).

## Élő export átvéve (2026-11-21)

- **Élő ág:** `elo-2026-11-21-0836` (a „C/3_2” tételsor-példány, `4QLpe9ylvwQL0S8SAgsf`; Attila döntése szerint ez az érvényes). Közös készlet szinkronizálva (adminCommit `bb48fe6`), `eszkoz_ellenor`: eltérés 0.
- **Átvétel (`elo_atvesz.py --ir`, commit `ac8864a`):** jegyzék 201, élő szöveges jegyzet 201; változott jegyzet **0** (azonos 201); az élőből hiányzó jegyzékelem 0, jegyzéken kívüli élő szöveges jegyzet 0 → **megálló nincs**. (Az élőből kimaradt 14 piszkozat és 1 törölt jegyzet nem jegyzékelem; a tájékoztató „202” a `manifest.json`-nal együtt számolt fájlszám volt.) tts: +1047 fájl (138 hangdokumentum); kvíz 113 módosul; tanulókártya 1 módosul, 14 törlődik (az élőben nincs); hézagpótló 1, memóriaútvonal 1 módosul; `EXPORT.json` bekerült.
- **Beállítás (commit `f357e3f`):** `hangAlapAgak` = `["origin/elo-2026-11-21-0836"]`, `rt2Alap` = `ac8864a…` (az átvétel commitja).
- **S1 újra (S1/5 első eset – API-kör és tételátdolgozás még nem volt):** az NN.txt-k története csak gépi (`8ea6536` generálás, `b12f73b` dobozépítés; a dobozokon kívüli eltérés csak dobozba olvadt normasor) – kézi/API-nyom nincs. `alapfelvetel.py` → `jegyzet_txt.py --felulir`: `jegyzet_txt: tétel 56, rész 201, karakter 4177520, eltérés 0`; az újragyártott szöveg betűre azonos a `8ea6536`-belivel. `tetelForras` érvényben: 21. → NGM10_2025; 26., 34. → Korm426_2025; 25., 52. → Hjkr (feloldatlan nélkül).
- **S3 újra:** `doboz_javit.py --sor --ir` (200 doboz), második futás: `módosítandó doboz: 0`; kihagyott doboz nincs. Az eredmény betűre azonos a korábban commitolt NN.txt-kkel (nettó változás 0).
- **Kapusorok előtte → utána (változatlan):**
  - `alapfelvetel: tétel 56, feloldott 467, feloldatlan 1, hiba 0` → ugyanaz (39. tétel: „Eljárási és Magatartási Kódexe I–III. rész”)
  - `dobozok: 915, eltérés: 1; hiányzó forrás: []; lefedettségi hiány: 104 elem 34 tételben` → ugyanaz
  - `hiányos bekezdés: 1` → ugyanaz (32. tétel, Efo. tv. 25. §)
- **Megfigyelés:** a 25. tétel „Hjt. 2. §” doboza a hatályon kívül helyezett 2012. évi CCV. törvény teljes 2. §-a (12 200 kar.), noha a tétel forrása a `tetelForras` szerint a Hjkr. – a tételmunkában kezelendő.
- **Következő lépés:** S4 – API-körök (első olvasás, átírás, ellenőrzés) az élő állapotra épülő munkaszövegen; a nyitott S3-kapu (eltérés 1, hiányos bekezdés 1: Efo. tv. 25. §) és a 39. tétel feloldatlan sora a korábbi Központi teendők szerint.

## S2 – alaki zárás (2026-11-21)

- `python3 tools/hatalyossag.py kapu | tail -1` → `hatalyossag: forrás 71, előírt 67, nyitott 41 (Sztrtv, Tagdtv, Ktv, ILO95, ILO138, ILO132, ILO182, Taktv, Fszftv, Korm294_2011, Ir97_81, Ir98_59, Ir99_70, Ir2003_88, Ir2008_104, Ir2019_1152, Ir2019_1158, Korm335_2012, NMr33, Korm535_2022, Korm69_2019, IRM73_2009, ISM7_2001, R987_2009, Ir2001_23, Cstv, Ebktv, Ebtv, Ir2000_78, Fot, GDPR, Hajtv, Infotv, Ir96_71, Kjt, R883_2004, Kp, Kozvtv, Tbj, Vbt, Aht); érintett tétel 0; előírt iránymutatás 58, korlátozott 0`
- **`korpusz/allapot.json`** elkészült (71 forrás: 67 előírt jogszabály + 4 nem előírt), kizárólag a tárolóbeli bizonyítékból (`korpusz/manifest.json` `hatalyossag`/`idoallapot`/`megjegyzes`; a fenti „S2 – korpuszcsere” és „Hatályon kívül helyezett jogszabályok” szakasz); új összevetés nem volt. A határozatok, AB-, Kúria- és EUB-döntések nem kerültek bele (ezeket a program iránymutatásként kezeli).
- **Friss: 27** (26 előírt + a nem előírt 5/2023. IM r.): Mt., Alaptörvény, Ptk., Pp., Vht., Kit., Kttv., Küt., Hszt., Tny., Cst., Csvt., Efo. tv., Munkavéd. tv., Art. (jövőbeli időállapot: 2027.01.01. – Attila döntése, 2026-11-19 18:00), 2009. évi LXXIV., 2020. évi CXXX., 2020. évi LVIII. tv., 102/1995., 115/2021., 118/2001., 31/2012., 88/2019. Korm. r., valamint a három új rendelet: 10/2025. NGM r., 426/2025. Korm. r., 137/2024. Korm. r. Az Alaptörvény, a Ptk., a Pp. és a Vht. időállapotának kezdőnapja a tárolóban nincs rögzítve (a manifest szerint „a 2026. december 9-én hatályos szöveg”).
- **Elavult, nem előírt (3):** 15/2023. GFM r., 573/2022. Korm. r., 2012. évi CCV. tv. – hatályon kívül, tájékoztatásként maradnak (`tetelForras`, `kiirasElirasok`).
- **Ellenőrizetlen előírt források (41)** – a tárolóban nincs írott összevetési bizonyíték; a séma ellenőrizetlen állapotot nem ismer, ezért `allapot: "hianyzik"` (a megjegyzés kimondja: az ellenőrzött időállapot hiányzik, nem a fájl; a B/1 megoldása szerint) – ezek tartják nyitva a kaput: Sztrtv (40); Tagdtv (27); Ktv (50); ILO95 (27); ILO138 (4); ILO132 (24); ILO182 (4); Taktv (33); Fszftv (4, 6, 35); Korm294_2011 (25); Ir97_81 (11); Ir98_59 (15); Ir99_70 (11, 30); Ir2003_88 (22, 24); Ir2008_104 (35); Ir2019_1152 (6); Ir2019_1158 (24); Korm335_2012 (2); NMr33 (8); Korm535_2022 (24); Korm69_2019 (48); IRM73_2009 (38); ISM7_2001 (4); R987_2009 (53, 54, 55, 56); Ir2001_23 (5, 37); Cstv (5); Ebktv (1); Ebtv (25, 54, 56); Ir2000_78 (1); Fot (1); GDPR (1); Hajtv (52); Infotv (1); Ir96_71 (6); Kjt (42, 43, 44, 45, 46, 47, 48, 49, 50, 51, 52); R883_2004 (53, 54, 55, 56); Kp (47, 52); Kozvtv (38); Tbj (53, 54, 55, 56); Vbt (38); Aht (41).
- **Iránymutatások:** előírt 58; valódi Kúria-lábjegyzet 10 (1/2004. KPJE: „Fenntartotta a 2/2015. BKMPJE V. 1. pont”; 4/2003. PJE: az új Ptk. és Pp. körében is irányadó; 8 KMK vélemény (1/2013., 3/2014., 4/2013., 6/2016., 4/2017., 5/2017., 1/2018., 1/2019.) azonos szövegű lábjegyzete: „A PK vélemény 1. pontja … irányadó …; 2. és 3. pontját a Kúria … nem tartja fenn” – a program „irányadó”-nak sorolja, a szöveg szerint korlátozott, és PK-véleményre utal: gyanúsan oldalsablon, ellenőrizendő). A C-151/02 (Jaeger) „*” sora („Az eljárás nyelve: német.”) nem lábjegyzet. Korlátozott a program szerint: 0.
- **Lábjegyzet nélküli előírt iránymutatás: 48** (Attila ellenőrzése a tárolóban nincs rögzítve, `iranymutatasEllenorzes` üres): 137/B/1991. AB határozat (1); 17/2014. (V. 30.) AB határozat (13); 18/2021. (V. 27.) AB határozat (20, 23); 1/2001. Munkaügyi jogegységi határozat (38); 1/2022 (VI. 8.) KK vélemény (52); 2/1999. Munkaügyi jogegységi határozat (40); 3001/2017. (I. 5.) AB határozat (50); 3081/2018. (III. 5.) AB végzés (21); 3082/2018. (III. 5.) AB végzés (21); 30/2012. (VI. 27.) AB határozat (40); 3152/2017. (VI.14.) AB végzés (44); 3/2016. (III. 21.) KMK vélemény (45, 47); 3/2018. (IX.17.) KMK vélemény (28); 44/B/1993. AB határozat (50); 495/B/2001. AB határozat (50); 56/1994. (XI. 10.) AB határozat (1); 600/B/2000. AB határozat (50); C-518/15 (23); C-624/19 (26); C-214/20 (23); 67/2009. (VI.19.) AB határozat (35); 74/2006. (XII. 15.) AB határozat (24); 826/B/1996. AB határozat (50); C-151/2002 (23); C-266/14 (23); C-303/1998 (23); C-477/21 (22); KK 24. (53); KK 25. (8); MK 100. (24); MK 112. (28); MK 113. (29); MK 120. (24); MK 122. (8); MK 13. (12); MK 132. (38); MK 160. (38); MK 18. (24); MK 19. (24); MK 23. (26); MK 25. (29); MK 26. (29); MK 35. (29, 38); MK 71. (38); MK 78. (19); MK 9. (13); MK 93. (28, 38); MK 95. (12).
- Manifest: a `jelentes` a manifest NFD-s fájlneveit nem találja; csak két (ékezet nélküli nevű) sorba írt volna „hianyzik” állapotot – a manifest visszaállítva, változatlan.
