#!/usr/bin/env bash
# tools/befesul.sh – auditált munkaág előrefutó befésülése a célágba, kapuk a befésült állapoton, jelentés, push.
# A TG-2 Cursor-kör helyett (Attila döntése, 2026-11-15, 20:51; folyamataudit B változat). Attila futtatja a saját gépén:
#
#   cd ~/Desktop/jogedu_tetelsor_repok/a_1_Polg-ri-jog-s-csal-di-jog && bash tools/befesul.sh <munkaág> [--nincs-push]
#
# Lépések, kötött sorrendben; bármelyik hibánál megáll (magyar üzenet, nem nulla kilépési kód = a lépés száma), és
# semmit nem tölt fel:
#    1. a munkafa tiszta (git status --short üres);
#    2. git fetch origin;
#    3. git checkout <ág> && git pull --ff-only origin <ág>; a helyi ág csúcsa = origin/<ág> (csak a feltöltött,
#       auditált állapot fésülhető be);
#    4. audit-jel: az utolsó commit üzenete „Audit (központi chat):” kezdetű, és az ALLAPOT.md valamely „## 2026” kezdetű
#       szakaszcíme tartalmazza az ág nevét (önálló szóként) és az „auditálva, befésülhető” szöveget;
#    5. git checkout <célág> && git pull --ff-only origin <célág>; a helyi célág csúcsa = origin/<célág> (helyi, fel nem
#       töltött commit a célágon nem lehet);
#    6. a célág csúcsa a munkaág őse (git merge-base --is-ancestor); ha nem: kiírja a közös őst és a két oldal elvált
#       commitjait (nem rebase-el, nem cherry-pickel, merge commitot nem készít);
#    7. git merge --ff-only <ág>;
#    8. bash tools/kapuk.sh --visszaallit: kilépési kód 0, és a kapuk ÁLLAPOT-sora = az ALLAPOT.md legfelső szakaszában
#       álló „ÁLLAPOT:” sor; ha nem teljesül: git reset --hard origin/<célág> (csak itt, csak a célágon), megáll;
#    9. a munkafa tiszta;
#   10. jelentés: jelentesek/TG-2_<ág>_jelentes.md, egyetlen commit: „TG-2: a <ág> ág befésülve; kapuk a befésült állapoton”;
#   11. git push origin <célág> – alapértelmezésben megteszi (Attila parancsa); --nincs-push: kihagyja, és kiírja a parancsot.
# A main ágat nem érinti, ágat nem töröl. macOS-en is fut (bash 3.2, BSD eszközök).

# A futó program ne a munkafából olvasson (a checkout átírhatja a saját fájlját): ideiglenes másolatból fut.
if [ -z "$BEFESUL_MASOLAT" ]; then
  GY=$(cd "$(dirname "$0")/.." 2>/dev/null && pwd) || { echo "HIBA: a tároló gyökere nem érhető el" >&2; exit 1; }
  M=$(mktemp "${TMPDIR:-/tmp}/befesul.XXXXXX") || exit 1
  cp "$0" "$M" || exit 1
  BEFESUL_MASOLAT="$M" BEFESUL_GYOKER="$GY" exec bash "$M" "$@"
fi
trap 'rm -f "$BEFESUL_MASOLAT"' EXIT
cd "$BEFESUL_GYOKER" || { echo "HIBA: a tároló gyökere nem érhető el" >&2; exit 1; }
CELAG=$(python3 -c "import json; print(json.load(open('tetelsor/beallitas.json', encoding='utf-8'))['celag'])") || { echo "HIBA: a tetelsor/beallitas.json celag mezője nem olvasható" >&2; exit 1; }

AG=""
PUSH=1
for a in "$@"; do
  case "$a" in
    --nincs-push) PUSH=0 ;;
    -h|--help) sed -n '2,26p' "$BEFESUL_MASOLAT"; exit 0 ;;
    -*) echo "HIBA: ismeretlen kapcsoló: $a" >&2; exit 64 ;;
    *) if [ -n "$AG" ]; then echo "HIBA: egyetlen munkaág adható meg" >&2; exit 64; fi; AG="$a" ;;
  esac
done
if [ -z "$AG" ]; then echo "HIBA: add meg a munkaágat: bash tools/befesul.sh <munkaág> [--nincs-push]" >&2; exit 64; fi
case "$AG" in
  *[!A-Za-z0-9._-]*) echo "HIBA: az ág neve csak betűt, számot, pontot, kötőjelet és aláhúzást tartalmazhat: $AG" >&2; exit 64 ;;
esac
if [ "$AG" = "$CELAG" ] || [ "$AG" = "main" ]; then echo "HIBA: a munkaág nem lehet a célág vagy a main: $AG" >&2; exit 64; fi

allj() {  # allj <lépés> <üzenet…>
  l="$1"; shift
  echo ""
  echo "MEGÁLLT ($l. lépés): $*"
  echo "Semmi nem került fel a távoli tárolóba. Ha nem érted az okát, másold be ezt a kimenetet a központi chatnek."
  exit "$l"
}
lepes() { echo "== $1"; }

lepes "1. A munkafa tiszta-e"
S=$(git status --short)
[ -z "$S" ] || allj 1 "a munkafa nem tiszta (nem commitolt vagy követetlen fájl van). Előbb ezt kell rendezni – nem nyúlok hozzá:
$S"

lepes "2. git fetch origin"
git fetch origin || allj 2 "a git fetch origin nem sikerült (hálózat vagy jogosultság)."

lepes "3. A munkaág ($AG) letöltése"
git rev-parse --verify --quiet "refs/remotes/origin/$AG" > /dev/null || allj 3 "a(z) $AG ág nincs fent a távoli tárolóban (origin/$AG nincs). Előbb fel kell tölteni."
git checkout "$AG" || allj 3 "a git checkout $AG nem sikerült."
git pull --ff-only origin "$AG" || allj 3 "a git pull --ff-only origin $AG nem sikerült (a helyi és a távoli ág elvált)."
[ "$(git rev-parse HEAD)" = "$(git rev-parse "origin/$AG")" ] || allj 3 "a helyi $AG ág csúcsa eltér az origin/$AG-tól (helyi, fel nem töltött commit van rajta). Csak a feltöltött, auditált állapot fésülhető be."

lepes "4. Audit-jel"
UTOLSO=$(git log -1 --format=%s)
case "$UTOLSO" in
  "Audit (központi chat):"*) : ;;
  *) allj 4 "az utolsó commit nem audit-commit (az üzenete nem „Audit (központi chat):” kezdetű): „$UTOLSO”. Az ág nincs auditálva." ;;
esac
[ -f ALLAPOT.md ] || allj 4 "nincs ALLAPOT.md a munkaágon."
AGRX=$(printf '%s' "$AG" | sed 's/[.]/\\./g')
if ! grep -E '^## 2026' ALLAPOT.md | grep -F 'auditálva, befésülhető' | grep -Eq "(^|[^A-Za-z0-9_-])${AGRX}([^A-Za-z0-9_-]|\$)"; then
  allj 4 "az ALLAPOT.md egyik „## 2026” kezdetű szakaszcíme sem mondja a(z) $AG ágról, hogy „auditálva, befésülhető”. Az ág nincs auditálva."
fi

lepes "5. A célág ($CELAG) frissítése"
git checkout "$CELAG" || allj 5 "a git checkout $CELAG nem sikerült."
git pull --ff-only origin "$CELAG" || allj 5 "a git pull --ff-only origin $CELAG nem sikerült."
[ "$(git rev-parse HEAD)" = "$(git rev-parse "origin/$CELAG")" ] || allj 5 "a helyi $CELAG csúcsa eltér az origin/$CELAG-tól (helyi, fel nem töltött commit van a célágon). Nem nyúlok hozzá; szólj a központi chatnek."
ELOZO=$(git rev-parse HEAD)

lepes "6. Előrefutó-e a befésülés"
if ! git merge-base --is-ancestor "$CELAG" "$AG"; then
  MB=$(git merge-base "$CELAG" "$AG")
  echo "Közös ős: $(git log -1 --format='%h %s' "$MB")"
  echo "Csak a célágon ($CELAG):"; git log --oneline "$MB..$CELAG"
  echo "Csak a munkaágon ($AG):"; git log --oneline "$MB..$AG"
  allj 6 "a célág csúcsa nem őse a munkaágnak – előrefutó befésülés nem lehetséges. Nem rebase-elek, nem cherry-pickelek, merge commitot nem készítek; a munkaágat a célág távoli csúcsára kell átültetni (központi chat)."
fi

lepes "7. git merge --ff-only $AG"
git merge --ff-only "$AG" || allj 7 "a git merge --ff-only $AG nem sikerült."

lepes "8. Kapuk a befésült állapoton"
[ -f tools/kapuk.sh ] || { git reset --hard "origin/$CELAG"; allj 8 "a befésült állapotban nincs tools/kapuk.sh. A befésülést visszavontam (git reset --hard origin/$CELAG)."; }
KI=$(mktemp "${TMPDIR:-/tmp}/befesul_kapuk.XXXXXX")
bash tools/kapuk.sh --visszaallit > "$KI" 2>&1
KRC=$?
cat "$KI"
KAPU_ALLAPOT=$(grep -m1 '^ÁLLAPOT:' "$KI")
PYT=$(mktemp "${TMPDIR:-/tmp}/befesul_py.XXXXXX")
cat > "$PYT" <<'PY'
# az ALLAPOT.md legfelső „## ” szakaszának első „ÁLLAPOT:” sora (a záró backtick előtti rész)
L = open('ALLAPOT.md', encoding='utf-8').read().split('\n')
i = next((k for k, l in enumerate(L) if l.startswith('## ')), None)
v = ''
if i is not None:
    for l in L[i + 1:]:
        if l.startswith('## '):
            break
        p = l.find('ÁLLAPOT:')
        if p >= 0:
            v = l[p:].split(chr(96))[0].strip()
            break
print(v)
PY
VART=$(python3 "$PYT")
rm -f "$PYT"
if [ "$KRC" != 0 ] || [ -z "$KAPU_ALLAPOT" ] || [ "$KAPU_ALLAPOT" != "$VART" ]; then
  git reset --hard "origin/$CELAG"
  rm -f "$KI"
  allj 8 "a kapuk elvárása nem teljesült (kapuk.sh kilépési kód: $KRC).
  a kapuk ÁLLAPOT-sora:     ${KAPU_ALLAPOT:-(nincs)}
  az ALLAPOT.md legfelső:   ${VART:-(nem található)}
A befésülést visszavontam (git reset --hard origin/$CELAG); a célág a távolival azonos."
fi

lepes "9. A munkafa tiszta-e a kapuk után"
S=$(git status --short)
if [ -n "$S" ]; then
  rm -f "$KI"
  allj 9 "a kapuk után a munkafa nem tiszta (a fenti „ÉRDEMBEN VÁLTOZOTT” fájlok vagy más):
$S
A befésülés helyben megtörtént, de nem commitoltam és nem töltöttem fel. Szólj a központi chatnek."
fi

lepes "10. Jelentés és commit"
J="jelentesek/TG-2_${AG}_jelentes.md"
SHA=$(sed -n 's/^csomag sha256: //p' "$KI" | head -1)
{
  echo "$KAPU_ALLAPOT"
  echo ""
  echo "# TG-2 – a \`$AG\` ág befésülése a \`$CELAG\` ágba (tools/befesul.sh)"
  echo ""
  echo "Készítette: \`tools/befesul.sh\`, $(date '+%Y-%m-%d %H:%M'). Előző célág-csúcs: \`$(git rev-parse --short "$ELOZO")\`; új csúcs: \`$(git rev-parse --short HEAD)\`."
  echo ""
  echo "## Befésült commitok"
  echo ""
  git log --format='- `%h` %s' "$ELOZO..HEAD"
  echo ""
  echo "## Kapuk a befésült állapoton (\`bash tools/kapuk.sh --visszaallit\`, kilépési kód: $KRC)"
  echo ""
  echo "| Kapu | Kilépési kód | Utolsó sor |"
  echo "|---|---|---|"
  grep ' | ' "$KI" | while IFS= read -r sor; do
    nev="${sor%% | *}"; rest="${sor#* | }"; kod="${rest%% | *}"; ut="${rest#* | }"
    printf '| %s | %s | %s |\n' "$nev" "$kod" "$(printf '%s' "$ut" | sed 's/|/\\|/g')"
  done
  echo ""
  grep -E '^(KAPUK:|visszaállítva|ÉRDEMBEN)' "$KI" | sed 's/^/- /'
  echo ""
  echo "**Csomag sha256:** \`${SHA:-nem olvasható}\`"
} > "$J"
rm -f "$KI"
git add "$J" || allj 10 "a git add $J nem sikerült."
git commit -q -m "TG-2: a $AG ág befésülve; kapuk a befésült állapoton" || allj 10 "a commit nem sikerült."
echo "commit: $(git log -1 --format='%h %s')"

lepes "11. Feltöltés"
if [ "$PUSH" = 1 ]; then
  git push origin "$CELAG" || allj 11 "a git push origin $CELAG nem sikerült. A befésülés és a jelentés helyben megvan; a parancsot később újra kiadhatod: git push origin $CELAG"
  echo "KÉSZ: a(z) $AG ág befésülve és feltöltve ($CELAG)."
else
  echo "KÉSZ (feltöltés nélkül, --nincs-push). A feltöltés parancsa:"
  echo "  git push origin $CELAG"
fi
echo "$KAPU_ALLAPOT"
exit 0
