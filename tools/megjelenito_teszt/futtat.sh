#!/usr/bin/env bash
# A közös megjelenítő böngészős próbája egy paranccsal; a kimenet csak az összegző sor és az esetleges hibasorok.
#   bash tools/megjelenito_teszt/futtat.sh <az admin tároló klónja>      (előtte: python3 tools/csomag_gyart.py)
# Playwright kell (NODE_PATH-ban vagy globálisan); ha nincs letöltött Chromium, a rendszer Chrome-ját használja.
set -euo pipefail
ADMIN="${1:?add meg az admin tároló klónjának útvonalát}"
GY="$(cd "$(dirname "$0")/../.." && pwd)"
M="$(mktemp -d /tmp/mj.XXXXXX)"; PORT=8765
mkdir -p "$M/szolg/szakvizsga" "$M/kepek"
cp "$ADMIN/web/szakvizsga/termekek.html" "$M/szolg/szakvizsga/"
AZON=$(python3 -c "import json; print(json.load(open('$GY/tetelsor/beallitas.json', encoding='utf-8'))['azon'])")
cp "$GY/ki/${AZON}_termekcsomag.json" "$M/szolg/csomag.json"
cp "$GY/tools/megjelenito_teszt/szulo.html" "$M/szolg/"
python3 -c "import json; json.dump(json.load(open('$GY/tetelsor/beallitas.json', encoding='utf-8'))['mintaTetelek'], open('$M/minta.json', 'w', encoding='utf-8'), ensure_ascii=False)"
: > "$M/szolg/favicon.ico"                      # a rendszer Chrome-ja lekéri; nélküle 404 konzolhiba keletkezik
ffmpeg -loglevel error -y -f lavfi -i anullsrc=r=22050:cl=mono -t 1 -q:a 9 "$M/szolg/proba.mp3"   # néma próbahang, a /tmp alatt marad
if node -e "require('playwright').chromium.executablePath()" >/dev/null 2>&1 && [ -x "$(node -e "process.stdout.write(require('playwright').chromium.executablePath())" 2>/dev/null)" ]; then
  cp "$GY/tools/megjelenito_teszt/teszt.js" "$M/teszt.js"
else
  sed "s/chromium.launch()/chromium.launch({channel:'chrome'})/" "$GY/tools/megjelenito_teszt/teszt.js" > "$M/teszt.js"
fi
(cd "$M/szolg" && exec python3 -m http.server "$PORT" >/dev/null 2>&1) & SRV=$!
trap 'kill $SRV 2>/dev/null || true; rm -rf "$M"' EXIT
sleep 1
(cd "$M" && node teszt.js 2>&1) | grep -a -E "^(ellenőrzések|HIBA|console:|pageerror)" | cut -c1-240
