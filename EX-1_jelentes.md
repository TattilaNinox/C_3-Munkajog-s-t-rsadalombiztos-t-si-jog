# EX-1 jelentés – C/3_2 Munkajog és társadalombiztosítási jog élő export

- Ág: `elo-2026-11-21-0836`
- Commit azonosító: ebben a fájlban nem szerepelhet, mert a hash a fájlt tartalmazó commitból számolódik. A feltöltés utáni `git log --oneline -1` sora a válaszban és a távoli ágon van.
- Export indítása: `2026-11-21T08:36:38+01:00` (a szkript `exportIdeje` mezője)
- Tételsor: `4QLpe9ylvwQL0S8SAgsf` — `C/3_2. MUNKAJOG ÉS TÁRSADALOMBIZTOSÍTÁSI JOG`
- A szkript kategóriája (címkékből): `C/3 Munkajog és társadalombiztosítási jog`
- Firestore: projekt `orlomed-f8f9f`, adatbázis `jogedu`. Csak olvasás.

## 4.1 Azonosító

A feladatlap első köre megállt, mert két dokumentum illeszkedett a `C/3` jelzésre és a munkajogi címre, mindkettő 56 szöveggel. Attila a `C/3_2` dokumentumot jelölte ki.

- Exportálva: `4QLpe9ylvwQL0S8SAgsf`, cím `C/3_2. MUNKAJOG ÉS TÁRSADALOMBIZTOSÍTÁSI JOG`, 56 szöveg, `status` in_progress, `kidolgozottCount` 55, `targy` Polgári jog.
- Nem exportálva: `jYKZAyYtvgDGuf7tfTn9`, cím `C/3. MUNKAJOG ÉS TÁRSADALOMBIZTOSÍTÁSI JOG TÉTELEK ÉS ELSAJÁTÍTANDÓ JOGANYAG`, 56 szöveg.

A darabszám a feladatlap 56-os számával egyezik. Az export 56 nem üres szövegfájlt írt, noha a `kidolgozottCount` mező 55.

## 4.2 Munkafa és ág

A helyi klón nem létezett. SSH-n jött létre, a feladatlap tárolójára: `git@github.com:TattilaNinox/c_3-munkajog-s-t-rsadalombiztos-t-si-jog.git`. Kilépési kód: **0**. Az HTTPS cím ugyanebben a feladatban felhasználónevet kért, ezért a klón és a push is SSH. Nem másik tároló.

Ágak: `origin/main`, `origin/elokeszites-2026-11-19`. `origin/tts-javitas` nincs. `origin/tartalom-javitas` nincs.

Ág: `elo-2026-11-21-0836`, worktree: `~/Desktop/jogedu_tetelsor_repok/c3_elo`, kiindulás: `origin/main` (`fe67f68`). `worktree add` kilépési kód: **0**.

`git rm -r -q .` kilépési kód: **0**. A törlés után a rövid státusz 1955 sor. Az első három: `D README.md`, `D hezagpotlok/01/1xdukHs8wGSviPOuvVaX.json`, `D hezagpotlok/02/BUAzvOS6MH6us9bDh5J7.json`.

## 4.3 Export

```
cd ~/Desktop/orlomed_admin_web && node functions/scripts/export_tetelsor_repo.js \
  --tetelsor=4QLpe9ylvwQL0S8SAgsf \
  --repo="$HOME/Desktop/jogedu_tetelsor_repok/c3_elo" \
  --korpusz="jogforrasok/1.Jogszabályok/Korpusz/C3 tételsor/TXT/"
```

Kilépési kód: **0**.

Kategória: C/3 Munkajog és társadalombiztosítási jog

```
STAT {"kihagyva":{"notes:status=Draft":14,"notes:deletedAt":1},"kotetlen":[],"vizsgalt":{"notes":{"talalat":420,"hiba":[]},"question_banks":{"talalat":114,"hiba":[]},"memoriapalota_allomasok":{"talalat":56,"hiba":[]},"tts_documents":{"talalat":138,"hiba":[]},"jogeset_items":{"talalat":0,"hiba":[]},"dialogus_fajlok":{"talalat":0,"hiba":[]},"sources":{"talalat":0,"hiba":[]},"temakorok":{"talalat":0,"hiba":[]},"egyetem_tetelsorok":{"talalat":0,"hiba":[]},"hangoskartyak":{"talalat":0,"hiba":[]},"deck_collections":{"talalat":1174,"kotott":50}},"kihagyottPontos":["jogforrasok/1.Jogszabályok/Korpusz/C3 tételsor/TXT/.placeholder"],"memoriaUtkozes":[],"darab":{"szovegek":56,"tanulokartyak":100,"kviz":114,"hezagpotlok":54,"memoriautvonal":56,"korpusz":134,"tts":138,"egyeb/tetel_html":56,"egyeb/notes":251,"egyeb/cloze_variants":216,"egyeb/deck_collections":50,"jogesetek":0,"dialogusok":0},"kartya":3144,"kerdes":3890,"szegmens":1116,"allomas":1219,"chunkFiles":906,"ismertIdoallapot":0,"nullIdoallapot":134,"kotottLawDocId":134,"orphan":[],"mp3":[],"kategoria":"C/3 Munkajog és társadalombiztosítási jog","exportIdeje":"2026-11-21T08:36:38+01:00","ag":"elo-2026-11-21-0836","extraUres":["sources","temakorok","egyetem_tetelsorok","hangoskartyak"],"eloSzuro":{"tetelsorok/tetelek":"a sor minden sorszama; ures txtContent nincs","notes deck":"status=Published es deletedAt ures; a gyujtemenybe tett pakli is, mert a kliens a gyujtemenyben megnyitja","notes cloze":"status=Published es deletedAt ures","notes egyeb":"status=Published es deletedAt ures; type nem deck es nem cloze","cloze_variants":"a publikalt cloze alkollekcioja, sajat allapotmezo nelkul","question_banks":"deletedAt ures, corpusGateLive nem false; status mezo nincs, vagy Published","memoriapalota_allomasok":"status=Published es deletedAt ures","tts_documents":"status=Published, vagy nincs status mezo, vagy publikalt jegyzet hangforrasa","jogeset_items":"status=Published vagy Public, deletedAt ures","dialogus_fajlok":"status=Published es deletedAt ures","deck_collections":"status=Published es a pakli-azonosito vagy a cimke koti a sorhoz","korpusz":"a Storage prefix minden fajlja"}}
```

Záró sor: `Kész. Szövegek 56, pakli 100, bank 114, gyakorlat 54, útvonal 56, korpusz 134, tts 138.`

## 5.1 Darabszámok

| Mi | Tájékoztató (feladatlap) | Most |
|---|---:|---:|
| Szövegfájl `NN.txt` | 56 | 56 (`01.txt`–`56.txt`) |
| Jegyzet, `type=text` | 202 | 201 |
| Jegyzet összesen, manifest nélkül | — | 251 |
| `tts/*/_meta.json` | nincs szám (–) | 138 |
| Tanulókártya / pakli | nincs külön szám | 100 |
| Kvízbank | nincs külön szám | 114 |
| Hézagpótló | nincs külön szám | 54 |
| Memóriaútvonal (mappa) | nincs külön szám | 56 |
| Korpusz `*.txt` | nincs külön szám | 134 |
| `EXPORT.json` | — | megvan |

A 251 jegyzet: 201 `text` + 50 `dynamic_quiz_dual`. Jegyzetmappák: `01`–`56`. A manifest nélküli JSON a szkript `darab` mezőjével egyezik. A korpusz manifest 134 tétel, 134 egyedi fájlnév, lemezen 134 txt. Nincs névütközés.

Egyéb szkript-darabok: `egyeb/tetel_html` 56, `egyeb/cloze_variants` 216, `egyeb/deck_collections` 50, kártya 3144, kérdés 3890, szegmens 1116, állomás 1219, chunk fájl 906. `deck_collections`: találat 1174, kötött 50.

## 5.2 Hang

- `tts/*/_meta.json`: **138**, mind `via: "audioSource"`
- `egyeb/notes/**.json` nem üres `audioPath`: **138**
- az első három `audioPath`, a jegyzetfájl útvonala szerint rendezve, változatlanul:
  - `audio/notes/n4eTzm9Fkdfn703Aj9ns.mp3` (`egyeb/notes/02/NW121BsIdXWS6YxFDvpK.json`)
  - `audio/notes/SMPKE5YoIZ88eY8O5prY.mp3` (`egyeb/notes/02/UTpjm0kAadnbP2Uj9U8u.json`)
  - `audio/notes/vdGSc62HmdZqyz1poWaj.mp3` (`egyeb/notes/02/WPOzZ7N6QlGjGlJEkAGJ.json`)

## 5.3 Tiltott fájlok

`find` (mp3, service-account, key, pem), `.git` kihagyva: **0**.

E-mail minta (`grep -rIl`), `.git` kihagyva: **1 fájl**. Kilépési kód: **0**.

A fájl: `korpusz/GDPR - AZ EURÓPAI PARLAMENT ÉS A TANÁCS 2016. április 27-i (EU) 2016_679 RENDELETE a természetes személyeknek a személyes adatok kezelése tekintetében történő védelméről.txt`. A találat kétszer az `info@orac.hu` cím: a jogszabályszöveg kiadói elérhetősége, nem felhasználói adat. Más fájlban nincs cím. Nem STOP.

## 5.4 Összevetés

- `origin/tts-javitas`: nincs ilyen ág
- `origin/tartalom-javitas`: nincs ilyen ág
- `origin/main`: megvan. Könyvtárai: `hezagpotlok jegyzetek korpusz kviz memoriautvonal tanulokartyak`. `tts` könyvtár ezen az ágon nincs.

Add előtt:

- `origin/main -- tts`: üres kimenet
- `origin/main -- jegyzetek egyeb/notes`: `202 files changed, 14400 deletions(-)`

`git add .` kilépési kód: **0**. Add után:

- `origin/main -- tts`: `1047 files changed, 28478 insertions(+)`
- `origin/main -- jegyzetek egyeb/notes`: `454 files changed, 9586 insertions(+), 14400 deletions(-)`

## Figyelmeztetések és eltérések

- A `C/3` (a `_2` nélküli) dokumentum nem került exportra. A kiírt kategória a feladatlap mondatával egyezik. A Firestore `cim` a `C/3_2` jelzést viseli, a `targy` mező `Polgári jog`.
- A `kidolgozottCount` mező 55, az export 56 szövegfájl.
- Kihagyva: 14 jegyzet `status=Draft`, 1 jegyzet `deletedAt`. Azonosítójuk nincs külön listázva.
- Jegyzet `type=text`: 201 a tájékoztató 202-höz képest. Az add előtti `jegyzetek` diff 202 fájlt törölt. Az egy publikált darab különbség oka nincs külön igazolva.
- Hangdokumentumra a feladatlap nem ad számot. Élő tts meta 138, mind `audioSource`, nem üres `audioPath` 138.
- Korpusz: a `.placeholder` kimaradt. 134 txt, mind időállapot nélkül (`ismertIdoallapot` 0, `nullIdoallapot` 134). Kötött lawDocId: 134. Nincs kettős név.
- Üres vizsgálat, hiba nélkül: `sources`, `temakorok`, `egyetem_tetelsorok`, `hangoskartyak`. Jogeset 0, dialógus 0. Kötetlen: üres.
- Hangot nem generáltam, Firestore-ba és Storage-ba nem írtam, másik ágat nem módosítottam.

## Ami nem futott, vagy nincs futásidőben ellenőrizve

- A feltöltés és a 7. pont a commit után fut; az eredménye nincs ebben a fájlban.
- A hangfájlok lejátszása, a kliens és a Firestore felület nincs megnyitva.
