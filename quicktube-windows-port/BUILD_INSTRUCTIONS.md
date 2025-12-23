# Bygginstruktioner för QuickTube (Python)

Detta projekt kan byggas till en fristående körbar fil för både Linux och macOS. Den slutgiltiga filen innehåller alla nödvändiga verktyg (`yt-dlp`, `svtplay-dl`, `gum`) inbakat.

## Förberedelser
Du behöver ha **Python 3** installerat på systemet du bygger på.

## Bygg för macOS
För att bygga en binär för Mac måste du bygga den **på en Mac**.

1.  Kopiera hela mappen `quicktube-py-dist` till din Mac.
2.  Öppna Terminal och gå till mappen:
    ```bash
    cd sökväg/till/quicktube-py-dist
    ```
3.  Gör byggscriptet körbart:
    ```bash
    chmod +x build_mac.sh
    ```
4.  Kör byggscriptet:
    ```bash
    ./build_mac.sh
    ```
    *Scriptet kommer automatiskt att ladda ner rätt versioner av verktygen för macOS och skapa den körbara filen.*

5.  Din färdiga app finns nu i mappen `dist/` och heter `quicktube-mac`.

## Bygg för Linux
1.  Gå till mappen i terminalen:
    ```bash
    cd quicktube-py-dist
    ```
2.  Gör byggscriptet körbart:
    ```bash
    chmod +x build_linux.sh
    ```
3.  Kör byggscriptet:
    ```bash
    ./build_linux.sh
    ```
4.  Din färdiga binär finns i `dist/quicktube`.

## Noteringar
- **FFmpeg & MPV:** Dessa program inkluderas *inte* i den körbara filen eftersom de är mycket stora. Användaren förväntas ha dessa installerade på sitt system (`brew install ffmpeg mpv` på Mac, `apt install ffmpeg mpv` på Linux).
