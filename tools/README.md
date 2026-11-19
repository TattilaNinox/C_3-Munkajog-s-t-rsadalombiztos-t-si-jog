# Szakvizsga-eszközkészlet

Ez a mappa a tételsor-tárolók `tools/` mappájának közös, géppel másolt készlete. A tételsor-specifikus értékek (fő kódex, §-minta, rövidítések, kiejtés, azonosítók, célág) a tételsor `tetelsor/beallitas.json` fájljából jönnek.

## Szinkron

A készletet az admin tároló gyökeréből másolod a tételsor-tárolóba. A szinkron nem commitol.

```bash
python3 tools/szakvizsga/szinkron.py --cel=<tételsor-tároló útvonala>
```

A parancs:

- a közös fájlokat a cél `tools/` mappájába másolja (a relatív útvonal megmarad);
- megírja a cél `tools/eszkozok.lock` fájlját (admin-commit + fájlonkénti sha256);
- a célban lévő, a készletből már kivett közös fájlt törli.

A szinkron a `tools/szakvizsga` utolsó commitját írja a zárba. Ha a készlet még nincs committolva, a szkript hibával megáll.

## Helyi lista

A tételsor saját adatai **nem** a készlet részei, a szinkron nem másolja és nem törli őket:

- `matrix_adat.py` — a tételsor kézi mátrixleírása
- `hang_ar.json` — a tételsor hangár-adata

A zár `helyi` mezője ezt a két fájlt sorolja. A `tools/eszkoz_ellenor.py` (a tételsor gyökeréből: `python3 tools/eszkoz_ellenor.py`) a zárban lévő közös fájlokat hash szerint ellenőrzi; a helyi listán lévő fájl jelenléte nem hiba, hash-kényszer nincs rá.

## Tilos

- A tételsor `tools/` mappájában a közös fájlok **helyi foltozása**. A javítás ide, a készletbe kerül, majd szinkron.
- A `tools/eszkozok.lock` **kézi írása**. A zárat csak a `szinkron.py` írja.
- A tételsor-specifikus értékek bekötése a kódba: azok a `tetelsor/beallitas.json`-ban élnek.
