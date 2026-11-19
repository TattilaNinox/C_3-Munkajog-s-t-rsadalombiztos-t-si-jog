#!/usr/bin/env python3
"""Az RT-2 javítás ellenőrzése a merge-base állapothoz képest.

Csak olvas. A négy régi termékmappa szövegmezőin kívüli eltérést hibának veszi.
Utolsó sora: rt2_ellenor: tétel N, javított mező M, hiba 0
"""
import json, os, re, subprocess, sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import kozos

MAPPAK = ("kviz", "tanulokartyak", "memoriautvonal", "hezagpotlok")
TILTOTT = ("tananyag", "ZH-felkészítő")
SZOVEG_KULCS = {
    "question", "text", "rationale", "front", "back", "explanation",
    "answer", "cimke", "cim", "kulcsszo", "tartalom",
}
HELY = re.compile(r"__\[b\d+\]__")
ALAP = kozos.beallitas()['rt2Alap']   # a célág csúcsa az RT-2 befésülése előtt (A/1-en rögzített commit)


def regi_fa():
    # Az RT-2 előtti állapot rögzített commitja (a befésülés után a merge-base már maga a célág lenne).
    # Más alap: --alap=<commit>.
    alap = next((x.split("=", 1)[1] for x in sys.argv if x.startswith("--alap=")), ALAP)
    if not alap:
        sys.stderr.write('rt2_ellenor: nincs rögzített alap-commit (rt2Alap) a beállításban\n')
        raise SystemExit(2)
    lista = subprocess.check_output(
        ["git", "ls-tree", "-r", "--name-only", alap, "--", *MAPPAK],
        cwd=kozos.GYOKER, text=True,
    ).splitlines()
    return alap, lista


def regi_szoveg(alap, ut):
    return subprocess.check_output(
        ["git", "show", f"{alap}:{ut}"], cwd=kozos.GYOKER,
    )


def lemez_fajlok():
    ki = []
    for mappa in MAPPAK:
        for gyoker, _, nevek in os.walk(os.path.join(kozos.GYOKER, mappa)):
            for nev in nevek:
                teljes = os.path.join(gyoker, nev)
                ki.append(os.path.relpath(teljes, kozos.GYOKER))
    return sorted(ki)


def szovegmezo(ut, kulcs):
    if kulcs == "distractors":
        return False
    if ut.endswith(".meta.json"):
        return False
    return kulcs in SZOVEG_KULCS


def jar(regi, uj, ut, valtozas, hiba, kulcs=None):
    if isinstance(regi, dict) or isinstance(uj, dict):
        if not isinstance(regi, dict) or not isinstance(uj, dict):
            hiba.append(f"típus eltér: {ut}")
            return
        if set(regi) != set(uj):
            hiba.append(f"kulcs eltér: {ut}")
            return
        for k in regi:
            jar(regi[k], uj[k], f"{ut}.{k}", valtozas, hiba, k)
        return
    if isinstance(regi, list) or isinstance(uj, list):
        if not isinstance(regi, list) or not isinstance(uj, list) or len(regi) != len(uj):
            hiba.append(f"tömb hossza eltér: {ut}")
            return
        for i, (a, b) in enumerate(zip(regi, uj)):
            if kulcs == "distractors":
                if a != b:
                    valtozas.append((f"{ut}[{i}]", a, b))
            else:
                jar(a, b, f"{ut}[{i}]", valtozas, hiba)
        return
    if kulcs in SZOVEG_KULCS and not ut.endswith(".meta.json"):
        if regi != uj:
            valtozas.append((ut, regi, uj))
        return
    if regi != uj:
        hiba.append(f"nem szövegmező változott: {ut}")


def forras_szoveg(nev):
    jelolt = [
        os.path.join(kozos.GYOKER, nev),
        os.path.join(kozos.GYOKER, "korpusz", nev),
    ]
    for ut in jelolt:
        if os.path.isfile(ut):
            return open(ut, encoding="utf-8").read()
    return None


def elem_szam(n):
    konyv = f"{n:02d}"
    ki = {}
    kviz = 0
    for fn in os.listdir(os.path.join(kozos.GYOKER, "kviz", konyv)):
        if fn.endswith(".json"):
            d = json.load(open(os.path.join(kozos.GYOKER, "kviz", konyv, fn), encoding="utf-8"))
            kviz += len(d.get("questions") or [])
    kartya = 0
    for fn in os.listdir(os.path.join(kozos.GYOKER, "tanulokartyak", konyv)):
        if fn.endswith(".json"):
            d = json.load(open(os.path.join(kozos.GYOKER, "tanulokartyak", konyv, fn), encoding="utf-8"))
            kartya += len(d.get("flashcards") or [])
    hezag = 0
    for fn in os.listdir(os.path.join(kozos.GYOKER, "hezagpotlok", konyv)):
        if fn.endswith(".json"):
            d = json.load(open(os.path.join(kozos.GYOKER, "hezagpotlok", konyv, fn), encoding="utf-8"))
            hezag += len(d.get("items") or [])
    memoria = 1
    allomas = os.path.join(kozos.GYOKER, "memoriautvonal", konyv, "allomasok")
    memoria += len([f for f in os.listdir(allomas) if f.endswith(".json")])
    ki["kviz"] = kviz
    ki["tanulokartyak"] = kartya
    ki["hezagpotlok"] = hezag
    ki["memoriautvonal"] = memoria
    return ki


def main():
    hiba = []
    alap, regi_lista = regi_fa()
    uj_lista = lemez_fajlok()
    if sorted(regi_lista) != uj_lista:
        hiba.append("fájllista eltér a merge-base állapottól")
    valtozas = []
    for ut in sorted(set(regi_lista) & set(uj_lista)):
        regi_bajt = regi_szoveg(alap, ut)
        uj_ut = os.path.join(kozos.GYOKER, ut)
        uj_bajt = open(uj_ut, "rb").read()
        if ut.endswith(".html"):
            if regi_bajt != uj_bajt:
                valtozas.append((ut, regi_bajt.decode("utf-8"), uj_bajt.decode("utf-8")))
            continue
        if not ut.endswith(".json"):
            if regi_bajt != uj_bajt:
                hiba.append(f"nem json fájl változott: {ut}")
            continue
        try:
            regi = json.loads(regi_bajt.decode("utf-8"))
            uj = json.loads(uj_bajt.decode("utf-8"))
        except json.JSONDecodeError as e:
            hiba.append(f"érvénytelen json: {ut} ({e})")
            continue
        jar(regi, uj, ut, valtozas, hiba)
    naplo_ut = os.path.join(kozos.GYOKER, "jelentesek", "RT-2_javitasok.json")
    if not os.path.isfile(naplo_ut):
        hiba.append("hiányzik a jelentesek/RT-2_javitasok.json")
        naplo = []
    else:
        naplo = json.load(open(naplo_ut, encoding="utf-8"))
    if not isinstance(naplo, list):
        hiba.append("a napló nem lista")
        naplo = []
    vart = {}
    for i, be in enumerate(naplo):
        if be.get("tipus") == "kozponti_dontes":
            continue
        kulcs = (be.get("azonosito"), be.get("mezo"))
        if kulcs in vart:
            hiba.append(f"kétszeres napló: {kulcs}")
        vart[kulcs] = be
        idezet = be.get("bizonyitek", {}).get("idezet") or ""
        forras = be.get("bizonyitek", {}).get("forras") or ""
        if len(idezet) < 40:
            hiba.append(f"rövid idézet: {be.get('azonosito')}")
        szov = forras_szoveg(forras)
        if szov is None or idezet not in szov:
            hiba.append(f"az idézet nincs a forrásban: {forras} / {be.get('azonosito')}")
        if any(s in (be.get("uj") or "") for s in TILTOTT):
            hiba.append(f"tiltott szó: {be.get('azonosito')}")
    teny = {}
    for ut, regi, uj in valtozas:
        if any(s in uj for s in TILTOTT):
            hiba.append(f"tiltott szó a fájlban: {ut}")
        if ".text" in ut or ut.endswith(".text"):
            if HELY.findall(regi or "") != HELY.findall(uj or ""):
                hiba.append(f"a hézag helye változott: {ut}")
    # A napló mezője a fájlon belüli út. A változás kulcsa a teljes út.
    # A bejegyzés azonosítója a termék eleméé, a mezo a mező útja.
    # Összevetés: a változás utolsó két összetevője és a napló mezője.
    def naplo_kulcs(ut):
        return ut
    tenyleges = {ut: (regi, uj) for ut, regi, uj in valtozas}
    def ut_a_naplobol(be):
        azonosito = be.get("azonosito") or ""
        mezo = be.get("mezo") or ""
        fajl, _, elem = azonosito.partition("#")
        if fajl.endswith(".html") or mezo == "utvonal.html":
            return fajl
        if "/allomasok/" in fajl:
            return f"{fajl}.{mezo}"
        with open(os.path.join(kozos.GYOKER, fajl), encoding="utf-8") as fh:
            d = json.load(fh)
        if fajl.startswith("kviz/"):
            return f"{fajl}.questions[{int(elem)}].{mezo}"
        if fajl.startswith("tanulokartyak/"):
            i = next(i for i, c in enumerate(d["flashcards"]) if c.get("id") == elem)
            return f"{fajl}.flashcards[{i}].{mezo}"
        if fajl.startswith("hezagpotlok/"):
            i = next(i for i, c in enumerate(d["items"]) if c.get("id") == elem)
            return f"{fajl}.items[{i}].{mezo}"
        return None

    naplo_utak = {}
    for be in naplo:
        if be.get("tipus") == "kozponti_dontes":
            cel = be.get("azonosito") or ""
            fajl = cel.split("#")[0]
            if any(u.startswith(fajl) for u in tenyleges):
                hiba.append(f"központi döntésű elem mégis változott: {cel}")
            continue
        try:
            teljes = ut_a_naplobol(be)
        except (OSError, json.JSONDecodeError, StopIteration, ValueError):
            teljes = None
        if not teljes:
            hiba.append(f"a napló azonosítója nem oldható fel: {be.get('azonosito')}")
            continue
        if teljes in naplo_utak:
            hiba.append(f"kétszeres naplóút: {teljes}")
        naplo_utak[teljes] = be
    if set(naplo_utak) != set(tenyleges):
        csak_naplo = sorted(set(naplo_utak) - set(tenyleges))
        csak_fajl = sorted(set(tenyleges) - set(naplo_utak))
        for u in csak_naplo[:8]:
            hiba.append(f"naplóban van, a fájlban nincs: {u}")
        for u in csak_fajl[:8]:
            hiba.append(f"a fájl változott, a naplóban nincs: {u}")
    for ut, be in naplo_utak.items():
        if ut not in tenyleges:
            continue
        regi, uj = tenyleges[ut]
        if be.get("regi") != regi or be.get("uj") != uj:
            hiba.append(f"a napló régi/új értéke eltér a fájltól: {ut}")
    for ut, regi, uj in valtozas:
        if "/allomasok/" in ut and ut.endswith(".tartalom"):
            konyv = ut.split("/")[1]
            html = open(os.path.join(kozos.GYOKER, "memoriautvonal", konyv, "utvonal.html"), encoding="utf-8").read()
            if uj not in html:
                hiba.append(f"az állomás új szövege nincs az útvonalban: {ut}")
    # (a) egy kérdésben nincs két azonos opciószöveg
    for gyoker, _, nevek in os.walk(os.path.join(kozos.GYOKER, "kviz")):
        for nev in nevek:
            if not nev.endswith(".json"):
                continue
            ut = os.path.relpath(os.path.join(gyoker, nev), kozos.GYOKER)
            try:
                dok = json.load(open(os.path.join(kozos.GYOKER, ut), encoding="utf-8"))
            except (OSError, json.JSONDecodeError):
                continue
            for i, kerdes in enumerate(dok.get("questions") or []):
                szovegek = [op.get("text") for op in (kerdes.get("options") or [])]
                if len(szovegek) != len(set(szovegek)):
                    hiba.append(f"azonos opciószöveg: {ut}#{i}")
    # (b) a jelöléssel ellentétes kezdés csak a naplóban szereplő indoknál hiba
    naplo_indok = set()
    for be in naplo:
        if be.get("tipus") == "kozponti_dontes":
            continue
        if str(be.get("mezo") or "").endswith("rationale"):
            naplo_indok.add(be.get("azonosito"))
    for gyoker, _, nevek in os.walk(os.path.join(kozos.GYOKER, "kviz")):
        for nev in nevek:
            if not nev.endswith(".json"):
                continue
            ut = os.path.relpath(os.path.join(gyoker, nev), kozos.GYOKER)
            try:
                dok = json.load(open(os.path.join(kozos.GYOKER, ut), encoding="utf-8"))
            except (OSError, json.JSONDecodeError):
                continue
            for i, kerdes in enumerate(dok.get("questions") or []):
                if f"{ut}#{i}" not in naplo_indok:
                    continue
                for op in kerdes.get("options") or []:
                    r = (op.get("rationale") or "").lstrip()
                    if op.get("isCorrect") is False and r.startswith("IGAZ"):
                        hiba.append(f"hamis indok IGAZ-zal kezdődik: {ut}#{i}")
                    if op.get("isCorrect") is True and r.startswith("HAMIS"):
                        hiba.append(f"igaz indok HAMIS-sal kezdődik: {ut}#{i}")
    # (c) a változott mezők rontott kötései; a vessző utáni nagybetű csak lista.
    # Az „és és” szóismétlés, nem az „ülés és” belseje. A „Ptké.,” rövidítés nem hiba.
    ismetles = re.compile(r"(?<![A-Za-zÁÉÍÓÖŐÚÜŰáéíóöőúüű])és és(?![A-Za-zÁÉÍÓÖŐÚÜŰáéíóöőúüű])")
    rossz_pont = re.compile("".join("(?<!%s)" % x for x in kozos.beallitas()["rt2PontKivetel"]) + r"(?<!\d)\., ")
    kozszavak = ("A ", "Az ", "Ha ", "Ez ", "Ezt ", "Nem ", "Azt ")
    for ut, regi, uj in valtozas:
        if not isinstance(uj, str):
            continue
        if ismetles.search(uj) or rossz_pont.search(uj) or ", ;" in uj:
            hiba.append(f"rontott kötés: {ut}")
        for szo in kozszavak:
            if ", " + szo in uj:
                print(f"LISTA: vessző után nagybetű: {ut}")
                break
    # (d) egy azonosító nem lehet mindkét listában
    nem_ut = os.path.join(kozos.GYOKER, "jelentesek", "RT-2_nem_ellenorizheto.json")
    if os.path.isfile(nem_ut):
        nem = json.load(open(nem_ut, encoding="utf-8"))
        naplo_azon = {be.get("azonosito") for be in naplo}
        for be in nem:
            if be.get("azonosito") in naplo_azon:
                hiba.append(f"azonosító mindkét listában: {be.get('azonosito')}")
    olvas_ut = os.path.join(kozos.GYOKER, "jelentesek", "RT-2_olvasas.json")
    if not os.path.isfile(olvas_ut):
        hiba.append("hiányzik a jelentesek/RT-2_olvasas.json")
        olvas = []
    else:
        olvas = json.load(open(olvas_ut, encoding="utf-8"))
    tetelek = []
    for sor in olvas:
        n = sor.get("tetel")
        tetelek.append(n)
        if sor.get("elolvasva") is not True:
            hiba.append(f"nincs késznek jelölve: {n}")
        vart_szam = elem_szam(n)
        kapott = sor.get("elemek") or {}
        if kapott != vart_szam:
            hiba.append(f"elemszám eltér a {n}. tételnél: {kapott} != {vart_szam}")
    javitott = len(tenyleges)
    for s in hiba:
        print("HIBA:", s)
    print(f"rt2_ellenor: tétel {len(tetelek)}, javított mező {javitott}, hiba {len(hiba)}")
    return 1 if hiba else 0


if __name__ == "__main__":
    sys.exit(main())
