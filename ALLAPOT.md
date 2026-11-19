# C/3 Munkajog és társadalombiztosítási jog – állapot

A rend: `orlomed_admin_web/docs/szakvizsga_program/12_tetelsor_szabvany.md`. A központi chat vezeti (Attila döntése, 2026-11-19, `01_dontesek.md`).

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

### A beállítás döntései

- Átfogó (`atfogo`): csak az Mt. (a kiírás bevezetője).
- A 115/2021. Korm. rendelet (`Fhr`) és a 33/1998. NM rendelet (`NMr33`) forrásként szerepel, mert a kiírás §-sal hivatkozik rájuk; nélkülük a §-aik a megelőző törvényhez (Fszftv., Mvt.) kerültek volna (4., 6., 8., 35. tétel).
- A 4. tétel két ILO-egyezménye (2000. évi LXIX., 2001. évi XXVII. tv.) forrásmintát kapott, mert a kiírás „kihirdetve … törvénnyel” alakját az általános mód nem ismeri fel.
- 50. tétel: a Kjt. teljes nevének és az 1992. évi XXIII. törvénynek (`Ktv`) a mintája választja el az AB-határozatok címében említett §-okat (különben az Mt.-hez kerültek volna). Emiatt a tétel Kjt. 30., 33., 37., 78., 87. §-a és Ktv. 17. §-a az AB-határozatok címéből származik, nem önálló előírás.
- 52. tétel: a pont nélküli felsorolás (Kit, Kttv, Küt, Hjt, Hszt, Hajtv, Nav Szjtv.) mintát kapott; ezek „bevezető rendelkezései” egész fájlként kerülnek a tételhez.

## Attila teendői

## Központi teendő

- **EUB, CELEX-nevű fájlok** (`tools/korpusz_felmeres.py` `fajl_kulcsok()`, illetve `alapfelvetel.py` `hatarozatok_altalanos()`, amely csak a fájl első nem üres sorát nézi, itt „62015CJ0518[1]”): a „6ÉÉÉÉCJNNNN” névből nem lesz `('eub','C','NNNN','ÉÉ')` kulcs. Javaslat: CELEX-felismerés a kulcsképzésben, vagy döntés `megfeleltet`-ről a három ügyre.
- **Néma veszteség (nem jelenik meg a feloldatlanok között, a fájl a korpuszban megvan):** 1. tétel 137/B/1991. AB hat.; 50. tétel 600/B/2000., 826/B/1996., 44/B/1993., 495/B/2001. AB hat. (a `korpusz_felmeres.hivatkozasok()` a „N/B/ÉÉÉÉ.” alakot nem ismeri fel; a fájlnév „600_B_2000” sem ad kulcsot); 23. tétel C-303/1998. SIMAP és C-151/2002. Jaeger (négyjegyű év; a fájl kulcsa „C-303/98”); 38. tétel 1/2004. Közigazgatási-polgári jogegységi határozat (a szöveg nem ad kulcsot, a fájl `1_2004. számú KPJE határozat _ Kúria.txt`); 39. tétel MTVSZ Kódex (`mtvsz_kodex.txt`; név szerinti forrás, az általános mód kihagyja). Javaslat: a minták bővítése a közös eszközben, vagy tételszintű `tetelForras` Attila döntésével.
- **Fejezeti átfogó előírás:** a „Közszféra munkajoga” (Kit., Kttv., Kjt., Küt.) és a „Társadalombiztosítási jog” (Tbj., 883/2004/EK, 987/2009/EK) fejezet bevezetője fejezetszintű átfogó ismeretet ír elő; a `kiiras_tetelek()` a fejezetfej utáni bevezetőt eldobja, a beállítás `atfogo` kulcsa csak az egész tételsorra érvényes. A 883/2004/EK és a 987/2009/EK így egyetlen tételhez sem kötődik. Javaslat: fejezetszintű `atfogo` (pl. `atfogoCsoport`).
- **`alapfelvetel.py` `egysegek()`:** (1) könyves tartomány rövidített végponttal („6:15-17. §”) → feloldatlan; javaslat: a végpont örökölje a kezdőpont könyvszámát; (2) római tartomány pont nélküli kezdőponttal („I-II. cikk”, „V-XIII. cikk”, „XVII-XVIII. cikk”, 1. tétel) → csak a végpont kerül be (II, XIII, XVIII), az I., V–XII., XVII. cikk némán kimarad; (3) „Ebtv. 42./G. §” (25. tétel) → a 42/G. § kimarad; „Tbj. 5; 6-22.§” (54. tétel) → az 5. § kimarad.
- **`felold()` cím:** a gondolatjeles kiírásban a cím végén „ -” marad (a `strip(' ;,')` nem veszi le); a 41. tétel címébe a forrásmegnevezés eleje is bekerül („… követelménye - a foglalkoztatás-felügyeleti hatóság tevékenységéről szóló”). A jegyzetek manifestjének címe tiszta.
- **`kozos.py` `FEJLEC`:** `parMinta: egyszeru` mellett a „Ptk. 6:518. §” dobozfejléc nem illeszkedik (egyszerű számozásnál a `PAR` nem enged kettőspontot); a 153 Ptk-doboz így nem kötődik forráshoz.
