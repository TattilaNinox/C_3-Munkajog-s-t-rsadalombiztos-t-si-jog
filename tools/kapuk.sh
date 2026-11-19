#!/usr/bin/env bash
# tools/kapuk.sh – a tételsor 12 gépi kapuja egy hívással (folyamataudit 2026-11-15, B változat; Attila döntése 20:51;
# a 12. kapu, a jegyzet_html_ellenor.py 2026-11-18 óta).
#
# Használat (bárhonnan; a program a tároló gyökerébe lép):
#   bash tools/kapuk.sh                  # a 12 kapu
#   bash tools/kapuk.sh --tetel NN [NN…] # csak `kontroll.py kapu NN…` és `ellenorzes.py` (a tétel-alügynök két kapuja)
#   bash tools/kapuk.sh --visszaallit    # a futás után a kapuk által átírt időbélyeges jelentésfájlokat visszaállítja
#                                        # (`git checkout --`), ha a diffjük csak időbélyeges sorokat érint
#
# Kimenet:
#   1. sor: a `kontroll.py kapu` ÁLLAPOT-sora szó szerint;
#   kapunként egy sor: `név | kilépési kód | a kimenet utolsó sora` (240 karakterre vágva; a doboz_teljesseg.py-nál
#   a „hiányos bekezdés: N” sor);
#   a végén: `csomag sha256: <lenyomat>` (a csomag_gyart.py kiírása = a ki/a1_termekcsomag.json „sha256” mezője)
#   és `KAPUK: 12 futott; eltérés/hibás: <ellenorzes + termek_ellenor + fa_ellenor + szamolo_ellenor + matrix_ellenor
#   + jegyzet_html_ellenor>`. A jegyzet-HTML a tétel szövegéből és a hangdarabokból készül: ha bármelyik változik,
#   előbb `python3 tools/jegyzet_html.py --mind` (különben a 12. kapu eltérést jelez).
#
# Kilépési kód: 0, ha az eltérés/hibás értékek mind 0, és egyik kapu sem omlott össze. A `kontroll.py kapu`, a
# `doboz_teljesseg.py` és a `lefedettseg_audit.py` 1-es kódja a teljes futásban nem hiba (a tételsor még nincs kész);
# a --tetel módban viszont a `kontroll.py kapu NN…` 1-es kódja hiba (a megadott tétel nincs lezárva).
# Egyébként 1. Ha egy érték nem olvasható ki a kimenetből, az is hiba (1).
#
# macOS-en is fut: bash 3.2, BSD eszközök (nincs mapfile, grep -P, GNU sed -i/date); a szövegvágás python3-mal.

cd "$(dirname "$0")/.." || { echo "HIBA: a tároló gyökere nem érhető el" >&2; exit 1; }

TETEL_MOD=0
VISSZAALLIT=0
TETELEK=""
while [ $# -gt 0 ]; do
  case "$1" in
    --tetel)
      TETEL_MOD=1; shift
      while [ $# -gt 0 ]; do
        case "$1" in --*) break ;; esac
        TETELEK="$TETELEK $1"; shift
      done
      ;;
    --visszaallit) VISSZAALLIT=1; shift ;;
    -h|--help) sed -n '2,26p' "$0"; exit 0 ;;
    *) echo "HIBA: ismeretlen kapcsoló: $1 (lásd: bash tools/kapuk.sh --help)" >&2; exit 2 ;;
  esac
done
if [ "$TETEL_MOD" = 1 ] && [ -z "$TETELEK" ]; then
  echo "HIBA: a --tetel után legalább egy tételszám kell" >&2; exit 2
fi

IDOBELYEGES="jelentesek/kontroll_allapot.md jelentesek/kontroll_allapot.json jelentesek/lefedettseg_audit.md jelentesek/lefedettseg_audit.json jelentesek/hanglefedettseg.md jelentesek/bovitesi_lista.md"

TMP=$(mktemp -d "${TMPDIR:-/tmp}/kapuk.XXXXXX") || exit 1
trap 'rm -rf "$TMP"' EXIT

# vag <fájl>: a fájl utolsó nem üres sora, 240 karakterre vágva (karakter, nem bájt)
vag() {
  python3 - "$1" <<'PY'
import sys
L = [l.rstrip('\n') for l in open(sys.argv[1], encoding='utf-8', errors='replace')]
L = [l for l in L if l.strip()]
print((L[-1] if L else '(nincs kimenet)')[:240])
PY
}

# szam <fájl> <regex>: az utolsó illeszkedő sor első csoportja (szám), vagy üres
szam() {
  python3 - "$1" "$2" <<'PY'
import re, sys
v = ''
for l in open(sys.argv[1], encoding='utf-8', errors='replace'):
    m = re.search(sys.argv[2], l)
    if m:
        v = m.group(1)
print(v)
PY
}

OSSZEOMLOTT=0
SOROK="$TMP/sorok.txt"; : > "$SOROK"

python3 tools/eszkoz_ellenor.py > "$TMP/eszkoz_ellenor.txt" 2>&1
ERC=$?
if [ "$ERC" != 0 ]; then
  cat "$TMP/eszkoz_ellenor.txt"
  exit "$ERC"
fi

futtat() {  # futtat <név> <megengedett kódok, szóközzel> <parancs…>
  nev="$1"; enged="$2"; shift 2
  ki="$TMP/$(echo "$nev" | tr ' /.' '___').txt"
  "$@" > "$ki" 2>&1
  rc=$?
  if [ "$nev" = "doboz_teljesseg.py" ]; then
    sor=$(grep -m1 '^hiányos bekezdés:' "$ki")
    [ -z "$sor" ] && sor="(a „hiányos bekezdés” sor hiányzik) $(vag "$ki")"
  else
    sor=$(vag "$ki")
  fi
  ok=0
  for k in $enged; do [ "$rc" = "$k" ] && ok=1; done
  if [ "$ok" = 0 ]; then
    OSSZEOMLOTT=1
    if [ "$TETEL_MOD" = 1 ] && [ "$rc" = 1 ] && [ "$1" = python3 ] && [ "$2" = tools/kontroll.py ]; then
      sor="$sor  [NYITOTT: a megadott tétel nincs lezárva; a pontok: python3 tools/kontroll.py kapu$TETELEK]"
    else
      sor="$sor  [HIBA: váratlan kilépési kód]"
    fi
  fi
  printf '%s | %s | %s\n' "$nev" "$rc" "$sor" >> "$SOROK"
}

if [ "$TETEL_MOD" = 1 ]; then
  # shellcheck disable=SC2086
  futtat "kontroll.py kapu$TETELEK" "0" python3 tools/kontroll.py kapu $TETELEK
  futtat "ellenorzes.py" "0" python3 tools/ellenorzes.py
  KONTROLL_KI="$TMP/$(echo "kontroll.py kapu$TETELEK" | tr ' /.' '___').txt"
else
  futtat "kontroll.py kapu" "0 1" python3 tools/kontroll.py kapu
  futtat "ellenorzes.py" "0" python3 tools/ellenorzes.py
  futtat "doboz_teljesseg.py" "0 1" python3 tools/doboz_teljesseg.py
  futtat "termek_ellenor.py" "0" python3 tools/termek_ellenor.py
  futtat "fa_ellenor.py" "0" python3 tools/fa_ellenor.py
  futtat "szamolo_ellenor.py" "0" python3 tools/szamolo_ellenor.py
  futtat "matrix_ellenor.py" "0" python3 tools/matrix_ellenor.py
  futtat "tetel_blokk.py" "0" python3 tools/tetel_blokk.py
  futtat "lefedettseg_audit.py" "0 1" python3 tools/lefedettseg_audit.py
  futtat "hangszoveg.py lefed" "0" python3 tools/hangszoveg.py lefed
  futtat "csomag_gyart.py" "0" python3 tools/csomag_gyart.py
  futtat "jegyzet_html_ellenor.py" "0" python3 tools/jegyzet_html_ellenor.py
  KONTROLL_KI="$TMP/kontroll_py_kapu.txt"
fi

ALLAPOT=$(grep -m1 '^ÁLLAPOT:' "$KONTROLL_KI")
[ -z "$ALLAPOT" ] && { ALLAPOT="ÁLLAPOT: (a kontroll.py kapu nem adott ÁLLAPOT-sort)"; OSSZEOMLOTT=1; }
echo "$ALLAPOT"
cat "$SOROK"

# az eltérés/hibás értékek
OSSZEG=0
NEM_OLVASHATO=""
ertek() {  # ertek <kapu kimenetfájl> <regex> <név>
  v=$(szam "$1" "$2")
  if [ -z "$v" ]; then NEM_OLVASHATO="$NEM_OLVASHATO $3"; else OSSZEG=$((OSSZEG + v)); fi
}
ertek "$TMP/ellenorzes_py.txt" 'eltérés: (\d+)' "ellenorzes.py"
if [ "$TETEL_MOD" = 0 ]; then
  ertek "$TMP/termek_ellenor_py.txt" 'eltérés: (\d+)' "termek_ellenor.py"
  ertek "$TMP/fa_ellenor_py.txt" 'hibás fa: (\d+)' "fa_ellenor.py"
  ertek "$TMP/szamolo_ellenor_py.txt" 'hibás: (\d+)' "szamolo_ellenor.py"
  ertek "$TMP/matrix_ellenor_py.txt" 'hibás: (\d+)' "matrix_ellenor.py"
  ertek "$TMP/jegyzet_html_ellenor_py.txt" 'hibás: (\d+)' "jegyzet_html_ellenor.py"
  SHA=$(szam "$TMP/csomag_gyart_py.txt" '^sha256 ([0-9a-f]{64})')
  [ -z "$SHA" ] && { SHA="(nem olvasható)"; OSSZEOMLOTT=1; }
  echo "csomag sha256: $SHA"
  DB=12
else
  DB=2
fi
if [ -n "$NEM_OLVASHATO" ]; then
  echo "KAPUK: $DB futott; eltérés/hibás: $OSSZEG; NEM OLVASHATÓ ÉRTÉK:$NEM_OLVASHATO"
else
  echo "KAPUK: $DB futott; eltérés/hibás: $OSSZEG"
fi

# az időbélyeges jelentésfájlok visszaállítása
if [ "$VISSZAALLIT" = 1 ]; then
  if ! git rev-parse --git-dir > /dev/null 2>&1; then
    echo "VISSZAÁLLÍTÁS: nem git munkapéldány – kihagyva"
  else
    ERDEMI=""
    for f in $IDOBELYEGES; do
      git ls-files --error-unmatch "$f" > /dev/null 2>&1 || continue
      git diff --quiet -- "$f" && continue
      if git diff -U0 -- "$f" | python3 -c '
import re, sys
from collections import Counter
rx = re.compile(r"\d{4}-\d\d-\d\d[T ]\d\d:\d\d(?::\d\d(?:\.\d+)?)?")
minus, plus = Counter(), Counter()
for l in sys.stdin.read().split("\n"):
    if l.startswith("---") or l.startswith("+++"):
        continue
    if l.startswith("-"):
        minus[rx.sub("<IDO>", l[1:])] += 1
    elif l.startswith("+"):
        plus[rx.sub("<IDO>", l[1:])] += 1
sys.exit(0 if minus == plus else 1)
'; then
        git checkout -- "$f" && echo "visszaállítva (csak időbélyeg): $f"
      else
        ERDEMI="$ERDEMI $f"
      fi
    done
    if [ -n "$ERDEMI" ]; then
      echo "ÉRDEMBEN VÁLTOZOTT, NEM ÁLLÍTOTTAM VISSZA:$ERDEMI"
    fi
  fi
fi

if [ "$OSSZEOMLOTT" = 0 ] && [ "$OSSZEG" = 0 ] && [ -z "$NEM_OLVASHATO" ]; then
  exit 0
fi
exit 1
