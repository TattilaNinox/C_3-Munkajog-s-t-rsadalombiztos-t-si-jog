# C/3 Munkajog és társadalombiztosítási jog

Export ideje: 2026-11-21T08:36:38+01:00
Ág: elo-2026-11-21-0836

56 kidolgozott szöveges anyagrész, a belőlük készült termékek, és a kötött jogszabály-korpusz. A tartalom **változatlan** másolat: nincs trimmelés, nincs átírás, nincs összevonás.

| Mappa | Forrás | Darab |
|---|---|---|
| `01.txt`–`56.txt` | `tetelek.txtContent` | 56 szöveg |
| `egyeb/tetel_html/` | `tetelek.htmlContent` | 56 html |
| `tanulokartyak/` | `notes` `type=deck` `flashcards` | 100 pakli, 3144 kártya |
| `kviz/` | `question_banks.questions` | 114 bank, 3890 kérdés |
| `hezagpotlok/` | `notes` `type=cloze` `items` | 54 gyakorlat, 1116 szegmens |
| `memoriautvonal/` | `memoriapalota_allomasok` | 56 útvonal, 1219 állomás |
| `korpusz/` | Storage TXT | 134 jogszabály |
| `tts/` | `tts_documents` chunkonként | 138 dokumentum, 906 chunk |
| `egyeb/notes/` | `notes` további típusok | 251 dokumentum |
| `egyeb/cloze_variants/` | `notes/*/cloze_variants` | 216 variáns |
| `egyeb/deck_collections/` | `deck_collections` | 50 gyűjtemény |

Egy Firestore-dokumentum = egy fájl (a darabolt anyagrészek külön pakliban/bankban maradnak). A kártyánál csak `front` / `back` / `explanation` került be; a `processed_*` elválasztó-másolat és a belső meta kimaradt. Az útvonal `utvonal.html` a `htmlTartalom` byte-azonos másolata, az `allomasok/*.json` a `tartalom` mezőé.

Az ellenőrző összegek: gyökér `manifest.json` (szövegek), a termék-mappák és a `korpusz/manifest.json`.

| Fájl | Cím | Karakter |
|---|---|---|
| 01.txt | Az Mt. bevezető rendelkezései és jelentőségük. | 243755 |
| 02.txt | A munkaviszonnyal kapcsolatos jognyilatkozatok, a jognyilatkozatok (...) | 149171 |
| 03.txt | Az érvénytelenség. | 30387 |
| 04.txt | A munkaviszony alanyai. A cselekvőképtelen munkavállaló. | 68673 |
| 05.txt | A munkáltató személyében bekövetkező változás. | 50403 |
| 06.txt | A munkaviszony létesítése, a munkaszerződés tartalma, a munkáltató (...) | 79215 |
| 07.txt | A munkaviszony kezdete; a próbaidő jogi természete, rendeltetése, időtartama. | 17561 |
| 08.txt | A munkaszerződés teljesítése, alapvető kötelezettségek, a (...) | 78589 |
| 09.txt | Az utasítás teljesítésének megtagadása, mentesülés a munkavégzési (...) | 33407 |
| 10.txt | Jogkövetkezmények a munkavállaló vétkes kötelezettségszegéséért. | 18914 |
| 11.txt | A munkaszerződés módosítása. | 34214 |
| 12.txt | A munkaviszony megszűnése és megszüntetése. | 30137 |
| 13.txt | A felmondás, a munkavállalói, illetve a munkáltatói felmondás szabályai (...) | 40667 |
| 14.txt | A felmondási tilalmak és a felmondási korlátozások, a felmondási idő (...) | 29483 |
| 15.txt | A csoportos létszámcsökkentésre vonatkozó főbb szabályok. | 24773 |
| 16.txt | A végkielégítés. | 26078 |
| 17.txt | Az azonnali hatályú felmondás feltételei, fajtái. | 15169 |
| 18.txt | Eljárás a munkaviszony megszüntetése (megszűnése) esetén. | 15325 |
| 19.txt | A munkaviszony jogellenes megszüntetése és jogkövetkezményei. | 27156 |
| 20.txt | A munka- és pihenőidő fogalmai, a napi munkaidőre, a munkaidőkeretre és (...) | 58892 |
| 21.txt | A munkaidő vasárnapra vagy munkaszüneti napra történő beosztása. A (...) | 29159 |
| 22.txt | A napi és a heti pihenőidőre, illetve a heti pihenőnapra vonatkozó (...) | 32640 |
| 23.txt | A rendkívüli munkaidő fogalma, elrendelése és elrendelésének korlátai (...) | 38182 |
| 24.txt | A szabadság (alap- és pótszabadság) mértéke, kiadása, az apasági (...) | 73366 |
| 25.txt | A betegszabadság, a szülési szabadság és a fizetés nélküli szabadság, a (...) | 85358 |
| 26.txt | A munka díjazása, díjazás munkavégzés hiányában, a távolléti díj számítása. | 39160 |
| 27.txt | A munkabér védelme, a munkabérből való levonás szabályai, a jogalap (...) | 95510 |
| 28.txt | A munkáltató kártérítési felelőssége. | 45193 |
| 29.txt | A munkavállaló kártérítési felelőssége, a megőrzési felelősség, a (...) | 59584 |
| 30.txt | A határozott idejű munkaviszonyra vonatkozó különös szabályok (...) | 24137 |
| 31.txt | A munkakör megosztása, több munkáltató által létesített munkaviszony, a (...) | 21097 |
| 32.txt | A bedolgozói jogviszony és az egyszerűsített foglalkoztatásra vagy (...) | 56567 |
| 33.txt | A köztulajdonban álló munkáltatóval fennálló munkaviszonyra vonatkozó (...) | 28093 |
| 34.txt | A vezető állású munkavállalóra vonatkozó rendelkezések. | 19205 |
| 35.txt | A munkaerő-kölcsönzésre vonatkozó legfontosabb rendelkezések. | 96363 |
| 36.txt | A munkaviszonyhoz kapcsolódó egyes megállapodások: a versenytilalmi (...) | 31218 |
| 37.txt | A kollektív szerződés megkötése és tartalma, hatálya, megszűnése. | 54979 |
| 38.txt | A munkajogi igény érvényesítésének szabályai. | 99498 |
| 39.txt | Kollektív munkaügyi vita. | 33405 |
| 40.txt | A sztrájkhoz való jog a sztrájkról szóló 1989. évi VII. törvény (...) | 25680 |
| 41.txt | A rendezett munkaügyi kapcsolatok követelménye | 22017 |
| 42.txt | A Kit. hatálya, a központosított álláshelyállomány és az álláshely fogalma. | 46860 |
| 43.txt | A Kit. szerinti kormányzati szolgálati jogviszony és annak alanyai (...) | 48056 |
| 44.txt | A Kit. szerinti kormányzati szolgálati jogviszony megszűnésére és (...) | 64210 |
| 45.txt | A kormányzati szolgálati jogviszony tartalma, jogok és kötelezettségek. | 34678 |
| 46.txt | A Magyar Kormánytisztviselői Kar jogköre és az érdekegyeztetés | 38527 |
| 47.txt | A bizalomvesztés, a méltatlanság és a fegyelmi eljárás, a kártérítés (Kttv.) | 73190 |
| 48.txt | Az érdemtelenség és a fegyelmi eljárás, a Közszolgálati Döntőbizottság (...) | 115332 |
| 49.txt | A Kttv. hatálya. a Kttv. szerinti kormányzati szolgálati jogviszony (...) | 15276 |
| 50.txt | A közalkalmazotti jogviszonyra vonatkozó szabályok, a közalkalmazotti (...) | 80851 |
| 51.txt | A kártérítési felelősségre vonatkozó főbb rendelkezések a (...) | 6623 |
| 52.txt | A közszolgálati jog fogalma, annak a magánmunkajogtól való (...) | 41079 |
| 53.txt | A törvény célja, alapelvek, fontosabb fogalmak és értelmező rendelkezések. | 33640 |
| 54.txt | A társadalombiztosítás ellátásai és az ellátásra jogosultak. | 150278 |
| 55.txt | A járulékfizetésre vonatkozó általános szabályok, megállapodás (...) | 84095 |
| 56.txt | Késedelem, mulasztás következményei, valamint az ellátásokhoz (...) | 56819 |

## Korpusz

| Fájl | storageFrissitve | Időállapot |
|---|---|---|
| 102_1995. (VIII. 25.) Korm. rendelet a keresőképtelenség és keresőképesség orvosi elbírálásáról és annak ellenőrzéséről - Hatályos Jogszabályok Gyűjteménye.txt | 2026-07-03T08:26:44.638Z | ismeretlen |
| 115_2021. (III. 10.) Korm. rendelet a foglalkoztatás-felügyeleti hatóság tevékenységéről - Hatályos Jogszabályok Gyűjteménye.txt | 2026-07-03T08:26:46.754Z | ismeretlen |
| 118_2001. (VI. 30.) Korm. rendelet a munkaerő-kölcsönzési és a magán-munkaközvetítői tevékenység nyilvántartásba vételéről és folytatásának feltételeiről - Hatályos Jogszabályok Gyűjteménye.txt | 2026-07-03T08:26:48.339Z | ismeretlen |
| 137_B_1991. AB határozat a külföldiek magyarországi befektetéseiről.._.txt | 2026-07-03T08:26:49.284Z | ismeretlen |
| 15_2023. (VII. 13.) GFM rendelet a 2024. évi munkaszüneti napok kör.._.txt | 2026-07-03T18:21:40.395Z | ismeretlen |
| 17_2014. (V. 30.) AB határozat a munka törvénykönyvéről szóló 2012..._.txt | 2026-07-03T08:26:51.718Z | ismeretlen |
| 18_2021. (V. 27.) AB határozat a munka törvénykönyvéről szóló 2012. évi I. törvény 94. § (3) és (4) bekezdéseinek együttes alkalmazásával kapcsolatos mulasztásban megnyilvánuló alaptörvény-ellenesség.txt | 2026-09-30T14:48:09.532Z | ismeretlen |
| 1989. évi VII. törvény a sztrájkról - Hatályos Jogszabályok Gyűjteménye.txt | 2026-07-03T08:26:57.587Z | ismeretlen |
| 1991. évi XXIX. törvény a munkavállalói érdekképviseleti tagdíjfizetés önkéntességéről - Hatályos Jogszabályok Gyűjteménye.txt | 2026-07-03T08:26:58.280Z | ismeretlen |
| 1992. évi XXIII. törvény a köztisztviselők jogállásáról - Törvények és országgyűlési határozatok.txt | 2026-07-03T08:27:00.854Z | ismeretlen |
| 1_2001. számú MJE határozat _ Kúria.txt | 2026-07-03T08:27:01.807Z | ismeretlen |
| 1_2004. számú KPJE határozat _ Kúria.txt | 2026-07-03T08:27:02.782Z | ismeretlen |
| 1_2009. (VI. 24.) PK-KK közös vélemény _ Kúria.txt | 2026-07-03T08:27:03.667Z | ismeretlen |
| 1_2013.(IV.8.) KMK vélemény a sztrájkjog gyakorlásának egyes kérdéseiről _ Kúria.txt | 2026-07-03T08:27:05.344Z | ismeretlen |
| 1_2018. (VI.25.) KMK vélemény a munkáltatónak a munkavállalója egészségi állapotában bekövetkezett károkért fennálló felelőssége egyes kérdéseiről _ Kúria.txt | 2026-07-03T08:27:07.765Z | ismeretlen |
| 1_2019. (V.20.) KMK vélemény a munkaviszonyhoz kapcsolódó egyes megállapodások_ a versenytilalmi megállapodásra és a tanulmányi szerződésre vonatkozó munkajogi szabályok értelmezéséről _ Kúria.txt | 2026-07-03T08:27:10.465Z | ismeretlen |
| 1_2022. (VI. 08.) KK vélemény a megelőző eljárás fogalmáról a közszolgálati jogviszonyokban _ Kúria.txt | 2026-08-22T07:39:41.745Z | ismeretlen |
| 2000. évi LIV. törvény a munkabér védelméről szóló, a Nemzetközi Munkaügyi Konferencia 1949. évi 32. ülésszakán elfogadott 95. számú Egyezmény kihirdetéséről - Hatályos Jogszabályok Gyűjteménye.txt | 2026-07-03T08:27:14.616Z | ismeretlen |
| 2000. évi LXIX. törvény a foglalkoztatás alsó korhatáráról szóló, a Nemzetközi Munkaügyi Konferencia 1973. évi 58. ülésszakán elfogadott 138. számú Egyezmény kihirdetéséről.txt | 2026-07-03T08:27:15.533Z | ismeretlen |
| 2000. évi LXVI. törvény a fizetett éves szabadságról szóló, a Nemzetközi Munkaügyi Konferencia 1970. évi 54. ülésszakán elfogadott 132. számú Egyezmény kihirdetéséről - Hatályos Jogszabályok Gyűjteménye.txt | 2026-07-03T08:27:16.374Z | ismeretlen |
| 2001. évi XXVII. törvény a gyermekmunka legrosszabb formáinak betiltásáról és felszámolására irányuló azonnali lépésekről szóló, a Nemzetközi Munkaügyi Konferencia 1999. évi 87. üléss.txt | 2026-07-03T08:27:17.205Z | ismeretlen |
| 2009. évi CXXII. törvény a köztulajdonban álló gazdasági társaságok takarékosabb működéséről - Hatályos Jogszabályok Gyűjteménye.txt | 2026-07-03T08:27:19.121Z | ismeretlen |
| 2009. évi LXXIV. törvény az ágazati párbeszéd bizottságokról és a középszintű szociális párbeszéd egyes kérdéseiről - Hatályos Jogszabályok Gyűjteménye.txt | 2026-07-03T08:27:21.339Z | ismeretlen |
| 2012. évi CCV. törvény a honvédek jogállásáról - Törvények és országgyűlési határozatok.txt | 2026-07-03T08:27:24.560Z | ismeretlen |
| 2020. évi CXXX. törvény a Nemzeti Adó- és Vámhivatal személyi állományának jogállásáról - Hatályos Jogszabályok Gyűjteménye.txt | 2026-08-20T08:49:41.997Z | ismeretlen |
| 2020. évi CXXXV. törvény a foglalkoztatást elősegítő szolgáltatásokról és támogatásokról, valamint a foglalkoztatás felügyeletéről - Hatályos Jogszabályok Gyűjteménye.txt | 2026-09-30T14:03:24.712Z | ismeretlen |
| 2020. évi LVIII. törvény a veszélyhelyzet megszűnésével összefüggő átmeneti szabályokról és a járványügyi készültségről - Hatályos Jogszabályok Gyűjteménye.txt | 2026-07-03T08:27:34.410Z | ismeretlen |
| 294_2011. (XII. 22.) Korm. rendelet az önkéntes tartalékos rendszerhez kapcsolódóan, a munkáltatót megillető támogatásokra vonatkozó szabályokról - Hatályos Jogszabályok Gyűjteménye.txt | 2026-07-03T08:27:35.242Z | ismeretlen |
| 2_1999. számú MJE határozat _ Kúria.txt | 2026-07-03T08:27:36.067Z | ismeretlen |
| 3001_2017 AB határozat.txt | 2026-07-03T08:27:37.700Z | ismeretlen |
| 3081_2018 AB végzés.txt | 2026-07-03T08:27:38.785Z | ismeretlen |
| 3082_2018 AB végzés.txt | 2026-07-03T08:27:39.735Z | ismeretlen |
| 30_2012. (VI. 27.) AB határozat.txt | 2026-07-03T08:27:41.967Z | ismeretlen |
| 3152_2017 AB végzés.txt | 2026-07-03T08:27:42.932Z | ismeretlen |
| 31997L0081 A Tanács 97_81_EK irányelve (1997. december 15.) az UNIC.._.txt | 2026-07-03T08:27:44.274Z | ismeretlen |
| 31998L0059 A Tanács 98_59_EK irányelve (1998. július 20.) a csoport.._.txt | 2026-07-03T08:27:45.176Z | ismeretlen |
| 31999L0070 A Tanács 1999_70_EK irányelve (1999. június 28.) az ESZS.._.txt | 2026-07-03T08:27:46.539Z | ismeretlen |
| 31_2012. (III. 7.) Korm. rendelet a közszolgálati tisztviselőkkel szembeni fegyelmi eljárásról - Hatályos Jogszabályok Gyűjteménye.txt | 2026-07-03T08:27:47.399Z | ismeretlen |
| 32003L0088 Az Európai Parlament és a Tanács 2003_88_EK irányelve (2.._.txt | 2026-07-03T08:27:48.952Z | ismeretlen |
| 32008L0104 Az Európai Parlament és a Tanács 2008_104_EK irányelve (.._.txt | 2026-07-03T08:27:50.418Z | ismeretlen |
| 32019L1152 Az Európai Parlament és a Tanács (EU) 2019_1152 irányelv.._.txt | 2026-07-03T08:27:52.658Z | ismeretlen |
| 32019L1158 Az Európai Parlament és a Tanács (EU) 2019_1158 irányelv.._.txt | 2026-07-03T08:27:54.877Z | ismeretlen |
| 335_2012. (XII. 4.) Korm. rendelet.txt | 2026-07-03T08:27:56.918Z | ismeretlen |
| 33_1998. (VI. 24.) NM rendelet a munkaköri, szakmai, illetve személyi higiénés alkalmasság orvosi vizsgálatáról és véleményezéséről - Hatályos Jogszabályok Gyűjteménye.txt | 2026-07-03T08:27:58.889Z | ismeretlen |
| 3_2014.(III.31.) KMK vélemény a munkaviszony munkáltató általi jogellenes megszüntetése jogkövetkezményeinek egyes kérdéseiről _ Kúria.txt | 2026-07-03T08:28:02.225Z | ismeretlen |
| 3_2016.(III.21.) KMK vélemény a Kormánytisztviselői Döntőbizottság határozatának felülvizsgálata iránti per egyes kérdéseiről _ Kúria.txt | 2026-08-22T07:39:46.041Z | ismeretlen |
| 3_2018. (IX.17.) KMK vélemény _ Kúria.txt | 2026-08-22T07:39:46.227Z | ismeretlen |
| 44_B_1993. AB határozat a köztisztviselők jogállásáról szóló 1992..._.txt | 2026-07-03T18:22:19.695Z | ismeretlen |
| 495_B_2001. AB határozat a közalkalmazottak jogállásáról szóló 1992.._.txt | 2026-07-03T08:28:11.895Z | ismeretlen |
| 4_2003. számú PJE határozat _ Kúria.txt | 2026-07-03T08:28:13.304Z | ismeretlen |
| 4_2013.(IX.23.) KMK vélemény a munkajogi igény érvényesítésének egyes kérdései a 2012. évi I. törvény alapján _ Kúria.txt | 2026-07-03T08:28:17.946Z | ismeretlen |
| 4_2017.(XI.28.) KMK vélemény az egyenlő bánásmód követelményének megsértésével kapcsolatos munkaügyi perek egyes kérdéseiről _ Kúria.txt | 2026-07-03T08:28:23.277Z | ismeretlen |
| 535_2022. (XII. 21.) Korm. rendelet az apasági szabadság igénybevételéről és az azzal összefüggő költségek megtérítéséről - Hatályos Jogszabályok Gyűjteménye.txt | 2026-07-03T08:28:24.194Z | ismeretlen |
| 56_1994. (XI. 10.) AB határozat.txt | 2026-07-03T08:28:25.105Z | ismeretlen |
| 573_2022. (XII. 23.) Korm. rendelet a kötelező legkisebb munkabér (.._.txt | 2026-07-03T18:22:20.509Z | ismeretlen |
| 5_2017.(XI.28.) KMK vélemény a joggal való visszaélés tilalmának megsértésével kapcsolatos munkaügyi perekben felmerült egyes kérdésekről _ Kúria.txt | 2026-07-03T08:28:31.124Z | ismeretlen |
| 5_2023. (VI. 19.) IM rendelet a békéltető testületi elnöki és tagsági feladat ellátására vonatkozó kiválasztási eljárás szabályairól és a békéltető testületi elnökök és tagok díjaz.txt | 2026-08-20T08:42:59.215Z | ismeretlen |
| 600_B_2000.txt | 2026-07-03T08:28:32.688Z | ismeretlen |
| 62002CJ0151_SUM A Bíróság 2003. szeptember 9-i ítélete. Landeshaupt.._.txt | 2026-07-03T08:28:34.963Z | ismeretlen |
| 62014CN0266 C-266_14. sz. ügy_ Az Audiencia Nacional (Spanyolország.._.txt | 2026-07-03T08:28:35.752Z | ismeretlen |
| 62015CJ0518 A Bíróság ítélete (ötödik tanács), 2018. február 21. Vi.._.txt | 2026-07-03T08:28:37.357Z | ismeretlen |
| 62019CJ0624 A Bíróság ítélete (második tanács), 2021. június 3. K e.._.txt | 2026-07-03T08:28:38.719Z | ismeretlen |
| 62020CJ0214 A Bíróság ítélete (ötödik tanács), 2021. november 11. M.._.txt | 2026-07-03T08:28:40.299Z | ismeretlen |
| 67_2009. (VI. 19.) AB határozat.txt | 2026-07-03T08:28:45.012Z | ismeretlen |
| 69_2019. (IV. 4.) Korm. rendelet a Közszolgálati Döntőbizottságról - Hatályos Jogszabályok Gyűjteménye.txt | 2026-07-03T08:28:46.492Z | ismeretlen |
| 6_2016. (XI.28.) KMK vélemény a munkaviszony jogellenes megszüntetése jogkövetkezményei egyes kérdéseiről _ Kúria.txt | 2026-07-03T08:28:52.556Z | ismeretlen |
| 73_2009. (XII. 22.) IRM rendelet a munkavállalói költségkedvezmény megállapításáról és érvényesítésének szabályairól - Hatályos Jogszabályok Gyűjteménye.txt | 2026-07-03T08:28:53.434Z | ismeretlen |
| 74_2006. (XII. 15.) AB határozat - Nemzeti Jogszabálytár.txt | 2026-07-03T08:28:55.003Z | ismeretlen |
| 7_2001. (X. 4.) ISM rendelet a tanköteles fiatal munkavállaló sportcélú foglalkoztatásáról - Hatályos Jogszabályok Gyűjteménye.txt | 2026-07-03T08:28:55.662Z | ismeretlen |
| 826_B_1996. AB határozat a közalkalmazottak jogállásáról szóló 1992.._.txt | 2026-07-03T08:28:56.559Z | ismeretlen |
| 88_2019. (IV. 23.) Korm. rendelet.txt | 2026-07-03T08:29:00.375Z | ismeretlen |
| 987_2009_EK rendelet a 883_2004_EK rendelet végrehajtásáról.txt | 2026-08-22T07:39:49.914Z | ismeretlen |
| A Tanács 2001.txt | 2026-07-03T08:29:01.380Z | ismeretlen |
| Alaptörvény - Magyarország Alaptörvénye (2011. április 25.) - Hatályos Jogszabályok Gyűjteménye.txt | 2026-09-30T14:03:57.229Z | ismeretlen |
| Art. (új) - 2017. évi CL. törvény az adózás rendjéről - Hatályos Jogszabályok Gyűjteménye.txt | 2026-09-30T14:04:44.681Z | ismeretlen |
| C-151_02 Jaeger ítélet.txt | 2026-08-22T07:39:50.967Z | ismeretlen |
| C-266_14 Tyco ítélet.txt | 2026-08-22T07:39:51.187Z | ismeretlen |
| C-303_98 SIMAP ítélet (EN).txt | 2026-08-22T07:39:51.416Z | ismeretlen |
| C-303_98. számú ítéletének összefoglalása _ Kúria.txt | 2026-07-03T08:29:35.489Z | ismeretlen |
| C-477_21 MÁV-START ítélet.txt | 2026-08-22T07:39:51.743Z | ismeretlen |
| C3_Munkajog_Tbj_beszerzesi_lista.txt | 2026-07-03T08:29:36.394Z | ismeretlen |
| Cst. - 1998. évi LXXXIV. törvény a családok támogatásáról - Hatályos Jogszabályok Gyűjteménye.txt | 2026-07-03T08:29:53.687Z | ismeretlen |
| Csvt. - 2011. évi CCXI. törvény a családok védelméről - Hatályos Jogszabályok Gyűjteménye.txt | 2026-07-03T08:29:54.510Z | ismeretlen |
| Csődtv. - 1991. évi XLIX. törvény a csődeljárásról és a felszámolási eljárásról - Hatályos Jogszabályok Gyűjteménye.txt | 2026-09-30T14:10:55.507Z | ismeretlen |
| C‑477_21. sz. MÁV-START ügyben 2023. március 2-án hozott ítélet _ Kúria.txt | 2026-07-03T08:29:55.597Z | ismeretlen |
| Ebktv. - 2003. évi CXXV. törvény az egyenlő bánásmódról és az esélyegyenlőség előmozdításáról - Hatályos Jogszabályok Gyűjteménye.txt | 2026-08-13T18:44:24.372Z | ismeretlen |
| Ebtv. - 1997. évi LXXXIII. törvény a kötelező egészségbiztosítás ellátásairól - Hatályos Jogszabályok Gyűjteménye.txt | 2026-09-30T14:11:50.970Z | ismeretlen |
| Efo. tv. - 2010. évi LXXV. törvény az egyszerűsített foglalkoztatásról - Hatályos Jogszabályok Gyűjteménye.txt | 2026-07-03T08:30:09.415Z | ismeretlen |
| Foglalkoztatási Irányelv (EU) - 32000L0078 A Tanács 2000_78_EK irán.._.txt | 2026-07-03T08:30:10.955Z | ismeretlen |
| Fot. - 1998. évi XXVI. törvény a fogyatékos személyek jogairól és esélyegyenlőségük biztosításáról - Hatályos Jogszabályok Gyűjteménye.txt | 2026-09-30T14:12:55.411Z | ismeretlen |
| GDPR - AZ EURÓPAI PARLAMENT ÉS A TANÁCS 2016. április 27-i (EU) 2016_679 RENDELETE a természetes személyeknek a személyes adatok kezelése tekintetében történő védelméről.txt | 2026-08-22T07:39:53.852Z | ismeretlen |
| Haj. tv. - 2018. évi CXIV. törvény a honvédelmi alkalmazottak jogállásáról - Hatályos Jogszabályok Gyűjteménye.txt | 2026-09-30T14:13:13.234Z | ismeretlen |
| Hszt. (új) - 2015. évi XLII. törvény a rendvédelmi feladatokat ellátó szervek hivatásos állományának szolgálati jogviszonyáról - Hatályos Jogszabályok Gyűjteménye.txt | 2026-09-30T14:15:36.079Z | ismeretlen |
| Info tv. - 2011. évi CXII. törvény az információs önrendelkezési jogról és az információszabadságról - Hatályos Jogszabályok Gyűjteménye.txt | 2026-09-30T14:15:59.449Z | ismeretlen |
| KK 24. szám.txt | 2026-07-03T18:23:18.193Z | ismeretlen |
| KK 25. szám.txt | 2026-07-03T08:30:22.221Z | ismeretlen |
| Kiküldetési Irányelv (EU) - 31996L0071 Az Európai Parlament És a Ta....txt | 2026-07-03T08:30:23.212Z | ismeretlen |
| Kiküldetési Irányelv (EU) - 31996L0071 Az Európai Parlament És a Ta.._.txt | 2026-07-03T08:30:24.273Z | ismeretlen |
| Kit. - 2018. évi CXXV. törvény a kormányzati igazgatásról - Hatályos Jogszabályok Gyűjteménye.txt | 2026-09-30T14:17:08.110Z | ismeretlen |
| Kjt. - 1992. évi XXXIII. törvény a közalkalmazottak jogállásáról - Hatályos Jogszabályok Gyűjteménye.txt | 2026-09-30T14:17:33.464Z | ismeretlen |
| Koordinációs Rendelet (EU) - 32004R0883 Az Európai Parlament és a T.._.txt | 2026-07-03T08:30:57.718Z | ismeretlen |
| Kp. - 2017. évi I. törvény a közigazgatási perrendtartásról - Hatályos Jogszabályok Gyűjteménye.txt | 2026-09-30T14:52:10.754Z | ismeretlen |
| Kttv. - 2011. évi CXCIX. törvény a közszolgálati tisztviselőkről - Hatályos Jogszabályok Gyűjteménye.txt | 2026-09-30T14:18:01.578Z | ismeretlen |
| Közvetítői tv. - 2002. évi LV. törvény a közvetítői tevékenységről - Hatályos Jogszabályok Gyűjteménye.txt | 2026-07-03T08:30:59.720Z | ismeretlen |
| Küt. - 2019. évi CVII. törvény a különleges jogállású szervekről és az általuk foglalkoztatottak jogállásáról - Hatályos Jogszabályok Gyűjteménye.txt | 2026-08-22T07:39:56.361Z | ismeretlen |
| MK 100. szám.txt | 2026-07-03T08:31:21.315Z | ismeretlen |
| MK 112. szám.txt | 2026-07-03T18:23:19.100Z | ismeretlen |
| MK 113. szám.txt | 2026-07-03T08:31:22.123Z | ismeretlen |
| MK 120. szám.txt | 2026-07-03T08:31:22.813Z | ismeretlen |
| MK 122. szám.txt | 2026-08-26T16:17:41.743Z | ismeretlen |
| MK 13. szám.txt | 2026-07-03T08:31:24.400Z | ismeretlen |
| MK 132. szám.txt | 2026-07-03T08:31:25.067Z | ismeretlen |
| MK 160. szám.txt | 2026-07-03T08:31:25.767Z | ismeretlen |
| MK 18. szám.txt | 2026-07-03T08:31:26.486Z | ismeretlen |
| MK 19. szám.txt | 2026-07-03T08:31:27.222Z | ismeretlen |
| MK 23. szám.txt | 2026-07-03T08:31:28.016Z | ismeretlen |
| MK 25. szám.txt | 2026-07-03T08:31:28.689Z | ismeretlen |
| MK 26. szám.txt | 2026-07-03T08:31:29.355Z | ismeretlen |
| MK 35. szám.txt | 2026-07-03T08:31:30.027Z | ismeretlen |
| MK 71. szám.txt | 2026-07-03T08:31:30.768Z | ismeretlen |
| MK 78. szám.txt | 2026-07-03T08:31:31.474Z | ismeretlen |
| MK 9. szám.txt | 2026-07-03T08:31:32.220Z | ismeretlen |
| MK 93. szám.txt | 2026-07-03T08:31:32.951Z | ismeretlen |
| MK 95. szám.txt | 2026-07-03T18:23:19.972Z | ismeretlen |
| Mt. (új) - 2012. évi I. törvény a munka törvénykönyvéről - Hatályos Jogszabályok Gyűjteménye.txt | 2026-09-30T14:53:15.328Z | ismeretlen |
| Munkavéd. tv. - 1993. évi XCIII. törvény a munkavédelemről - Hatályos Jogszabályok Gyűjteménye.txt | 2026-09-30T14:20:03.721Z | ismeretlen |
| Pp. (új) - 2016. évi CXXX. törvény a polgári perrendtartásról - Hatályos Jogszabályok Gyűjteménye.txt | 2026-09-30T14:54:21.272Z | ismeretlen |
| Ptk. (új) - 2013. évi V. törvény a Polgári Törvénykönyvről - Hatályos Jogszabályok Gyűjteménye.txt | 2026-09-30T14:23:29.755Z | ismeretlen |
| Tbj. (új) - 2019. évi CXXII. törvény a társadalombiztosítás ellátásaira jogosultakról, valamint ezen ellátások fedezetéről - Hatályos Jogszabályok Gyűjteménye.txt | 2026-09-30T14:24:42.934Z | ismeretlen |
| Tny. - 1997. évi LXXXI. törvény a társadalombiztosítási nyugellátásról - Hatályos Jogszabályok Gyűjteménye.txt | 2026-09-30T14:54:41.177Z | ismeretlen |
| Vbt. (új) - 2017. évi LX. törvény a választottbíráskodásról - Hatályos Jogszabályok Gyűjteménye.txt | 2026-07-03T08:32:49.150Z | ismeretlen |
| Vht. - 1994. évi LIII. törvény a bírósági végrehajtásról - Hatályos Jogszabályok Gyűjteménye.txt | 2026-09-30T14:27:02.384Z | ismeretlen |
| mtvsz_kodex.txt | 2026-07-03T08:33:10.294Z | ismeretlen |
| Áht. - 2011. évi CXCV. törvény az államháztartásról - Hatályos Jogszabályok Gyűjteménye.txt | 2026-09-30T14:49:40.559Z | ismeretlen |
