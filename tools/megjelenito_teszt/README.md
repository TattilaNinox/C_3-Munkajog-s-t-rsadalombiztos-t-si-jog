# A közös megjelenítő böngészős próbája

A megjelenítő (`web/szakvizsga/termekek.html`, az admin és a kliens projektben bájtra azonos fájl) teljes körű próbája fej nélküli böngészőben, a teljes termékcsomagon. Ezt Claude futtatja a saját környezetében; a Cursor-ügynöknek nem feladata (ő böngészőt nem nyit).

```
python3 tools/csomag_gyart.py                       # ki/a1_termekcsomag.json
mkdir -p /tmp/mj/szolg/szakvizsga /tmp/mj/kepek
cp <admin>/web/szakvizsga/termekek.html /tmp/mj/szolg/szakvizsga/
cp ki/a1_termekcsomag.json /tmp/mj/szolg/csomag.json
cp tools/megjelenito_teszt/szulo.html /tmp/mj/szolg/ && cp tools/megjelenito_teszt/teszt.js /tmp/mj/
ffmpeg -loglevel error -y -f lavfi -i anullsrc=r=22050:cl=mono -t 1 -q:a 9 /tmp/mj/szolg/proba.mp3   # néma próbahang (mp3 a tárolóba nem kerülhet)
(cd /tmp/mj/szolg && python3 -m http.server 8765 &) ; cd /tmp/mj && node teszt.js
```

Mit vizsgál (2026-11-12: 4288 ellenőrzés, 0 hiba):
- a böngészőben futó önellenőrzés (fák példái, számolók példái és összes bemeneti kombinációja, mátrixok teljessége, darabszámok, a csomag SHA-256 lenyomata);
- a kifejezés-értékelő (törtek; a hibás vagy veszélyes kifejezést elutasítja);
- tipográfia (Verdana 13px / 1.6, sorkizárt, elválasztás; címek 24/20/18; vezérlők Inter);
- mind a 85 tétel minden füle: a megjelenő szöveg betűre egyezik a csomaggal (§-ok, kulcsmondatok, felsorolások, mátrixcímkék és forrásmondatok);
- a felsorolás-tréner módjai; minden fa minden példája a példagombbal és kézzel végigkattintva is; minden számoló minden példája (szabály és hányadok);
- telefonszélességen (390 px) nincs vízszintes túlcsordulás;
- beágyazva (iframe) az üzenetváltás; a csomag újratöltése; idegen forrású üzenet és hibás csomag kezelése;
- a fájlban nincs tiltott szó és nincs külső hivatkozás.

Egy paranccsal (a kimenet csak az összegző sor és a hibasorok): `bash tools/megjelenito_teszt/futtat.sh <az admin tároló klónja>` – a rendszer Chrome-jával is fut, és üres `favicon.ico`-t tesz a próbaszerver alá (nélküle a Chrome 404-es konzolhibát jelez).
