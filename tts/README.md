# TTS chunkok

A publikus jegyzetekhez tartozó TTS-dokumentumok, **chunkonként külön fájl**.

- Dokumentum: 138
- Chunk-fájl: 906
- Forrás: Firestore `jogedu` / `tts_documents`, élő állapot

## Szerkezet

```
tts/
  _index.json
  {ttsId}/
    _meta.json          # jegyzet-id, cím, chunk-lista
    chunk_001.txt       # a chunk fullText-je
    chunk_002.txt
```

A hangfájl (mp3) nincs a mappában; az elérési út a `_meta.json` `audioFile` mezőjében van.
