#!/bin/bash
# yt-helper.sh: Ett TUI-skript för att hantera YouTube-länkar med gum, yt-dlp och mpv.

# --- Funktion för att kontrollera beroenden ---
check_dependencies() {
    local missing_deps=()
    # Lista över obligatoriska beroenden för macOS
    local required_cmds=("gum" "yt-dlp" "mpv" "ffmpeg")

    for cmd in "${required_cmds[@]}"; do
        if ! command -v "$cmd" &> /dev/null; then
            missing_deps+=("$cmd")
        fi
    done

    if [ ${#missing_deps[@]} -gt 0 ]; then
        gum style --foreground="212" "Fel: Nödvändiga program saknas."
        gum style "Detta skript kräver: ${required_cmds[*]}"
        
        # Skapa och visa installationskommandot för Homebrew
        local install_command="brew install ${missing_deps[*]}"
        gum style --border normal --padding "1 1" --margin "1" "Förslag för installation med Homebrew:" "$install_command"
        
        exit 1
    fi

    # Kontrollera specifikt för macOS urklippsverktyg
    if ! command -v pbpaste &> /dev/null; then
        gum style --foreground="212" "Kritiskt fel: Kommandot 'pbpaste' hittades inte." \
                  "Detta är en standardkomponent i macOS. Installationen kan vara korrupt."
        exit 1
    fi
}

# --- Funktion för att hämta urklipp ---
get_clipboard() {
    # Prioritera pbpaste för macOS
    if command -v pbpaste &> /dev/null; then
        pbpaste | tr -d '\0'
    elif command -v wl-paste &> /dev/null; then
        wl-paste | tr -d '\0'
    elif command -v xclip &> /dev/null; then
        xclip -o -selection clipboard | tr -d '\0'
    fi
}

# Huvudfunktion
main() {
    check_dependencies
    local LAST_ACTION=""

    while true; do
        # Hämta innehåll från urklipp för att eventuellt förifylla
        CLIPBOARD_CONTENT=$(get_clipboard)
        URL_FROM_CLIPBOARD=""
        
        # Förifyll bara om senaste åtgärden INTE var "Stream"
        if [[ "$LAST_ACTION" != "stream" ]]; then
            # Trimma eventuella inledande/avslutande blanksteg från urklippet för en mer robust matchning
            local trimmed_content
            trimmed_content=$(echo "$CLIPBOARD_CONTENT" | sed 's/^[[:space:]]*//;s/[[:space:]]*$//')

            # Kontrollera om det trimmade innehållet börjar med en giltig YouTube-URL-variant
            case "$trimmed_content" in
                "http://www.youtube.com/"* | \
                "https://www.youtube.com/"* | \
                "http://youtube.com/"* | \
                "https://youtube.com/"* | \
                "http://youtu.be/"* | \
                "https://youtu.be/"* | \
                "www.youtube.com/"* | \
                "youtube.com/"* | \
                "youtu.be/"* )
                    # Om det matchar, använd det ursprungliga (otrimmade) urklippsinnehållet
                    URL_FROM_CLIPBOARD="$CLIPBOARD_CONTENT"
                    ;;
            esac
        fi
        # Återställ flaggan direkt efter att den har använts
        LAST_ACTION=""
        
        # Använd 'gum input' och förifyll med urklippets innehåll om det är en giltig länk
        URL=$(gum input --placeholder "Klistra in/skriv en YouTube-URL..." --value "$URL_FROM_CLIPBOARD")

        # Om användaren inte matar in något, avsluta
        if [ -z "$URL" ]; then
            gum style "Ingen URL angiven. Avslutar."
            break
        fi

        # Enkel validering av URL
        if [[ ! "$URL" =~ "youtube.com/" && ! "$URL" =~ "youtu.be/" ]]; then
            gum style --foreground="212" "Ogiltig YouTube-URL. Försök igen."
            continue
        fi

        # Hämta videons titel, dölj varningar
        VIDEO_TITLE=$(yt-dlp --get-filename -o "%(title)s" --no-warnings "$URL" 2>/dev/null)
        # Formatera titeln för snygg radbrytning
        FORMATTED_TITLE=$(echo "$VIDEO_TITLE" | fmt -w 60)
        gum style --border rounded --padding "1 2" --border-foreground "240" \
            "Vad vill du göra med:
$FORMATTED_TITLE?"

        # Huvudmeny med gum
        ACTION=$(gum choose "Stream Video (MPV)" "Stream Ljud (MPV)" "Ladda ner video" "Ladda ner ljud")

        case "$ACTION" in
            "Stream Video (MPV)")
                # Använd --no-terminal för att undvika att mpv skriver över TUI:t
                mpv --no-terminal "$URL"
                # Sätt flaggan så att nästa loop inte förifyller samma URL
                LAST_ACTION="stream"
                ;;
            
            "Stream Ljud (MPV)")
                # Använd --no-video för att bara spela ljud, ta bort --no-terminal för konsolkontroll
                mpv --no-video "$URL"
                # Sätt flaggan så att nästa loop inte förifyller samma URL
                LAST_ACTION="stream"
                ;;

            "Ladda ner video")
                # Hämta tillgängliga format, dölj varningar
                FORMATS_OUTPUT=$(yt-dlp -F --no-warnings "$URL" 2>/dev/null)
                
                # Förbered för gum table
                HEADER="ID,Upplösning,FPS,Filtyp,Codec,Storlek"
                declare -a TABLE_DATA_ROWS
                
                while IFS= read -r line; do
                    # Försök extrahera relevanta fält från rader med "video only"
                    # Denna regex försöker matcha yt-dlp:s kolumnutdata mer robust
                    if [[ "$line" =~ ^([0-9]+)\ +([a-zA-Z0-9]+)\ +([0-9]+x[0-9]+)(\ +([0-9.]+))? ]]; then
                        id="${BASH_REMATCH[1]}"
                        ext="${BASH_REMATCH[2]}"
                        res="${BASH_REMATCH[3]}"
                        fps="${BASH_REMATCH[5]:-N/A}" # FPS är valfritt, N/A om det saknas
                        
                        filesize="N/A"
                        if [[ "$line" =~ ([0-9.]+(MiB|GiB)) ]]; then
                            filesize="${BASH_REMATCH[1]}"
                        fi
                        
                        codec="N/A"
                        # Försök hitta codec innan "video only"
                        if [[ "$line" =~ ([a-zA-Z0-9.]+)\ +video\ only ]]; then
                            codec="${BASH_REMATCH[1]}"
                        fi

                        # Se till att det är en "video only" ström
                        if [[ "$line" =~ video\ only ]]; then
                            TABLE_DATA_ROWS+=("${id},${res},${fps},${ext},${codec},${filesize}")
                        fi
                    fi
                done <<< "$FORMATS_OUTPUT"

                if [ ${#TABLE_DATA_ROWS[@]} -eq 0 ]; then
                    gum style --foreground="212" "Kunde inte hitta några videoströmmar."
                    continue
                fi

                # Sortera raderna efter upplösning (andra kolumnen, numeriskt om möjligt)
                # Vi använder sort -t, -k2,2V för att sortera på upplösning på ett "smart" sätt
                SORTED_TABLE_ROWS=($(printf "%s\n" "${TABLE_DATA_ROWS[@]}" | sort -t, -k2,2V -r))


                # Visa tabellen och låt användaren välja en rad
                # Användaren kan trycka Esc för att avbryta
                TABLE_INPUT=$(echo "$HEADER"; IFS=$'\n'; echo "${SORTED_TABLE_ROWS[*]}")
                CHOICE=$(echo "$TABLE_INPUT" | gum table -s, --height 10)
                
                if [ -z "$CHOICE" ]; then
                    # Om användaren avbryter (Esc) är CHOICE tom
                    continue
                fi

                # Extrahera formatkoden (ID) från den valda raden (första kolumnen)
                FORMAT_CODE=$(echo "$CHOICE" | cut -d, -f1)
                
                echo "" # Tom rad
                gum style "Startar nedladdning av video..."
                # Låt yt-dlp:s progressbar visas direkt, använd --no-warnings
                yt-dlp --no-warnings --force-overwrites --embed-metadata --embed-thumbnail -f "$FORMAT_CODE+bestaudio" --merge-output-format mp4 -o "%(title)s-%(height)sp.%(ext)s" "$URL"

                echo "" # Tom rad
                gum style --foreground "212" "✔ Nedladdning slutförd."
                ;;

            "Ladda ner ljud")
                echo "" # Tom rad
                gum style "Startar nedladdning av ljud..."
                
                # Hämta filens basnamn i förväg för att kunna städa upp efteråt
                BASENAME=$(yt-dlp --get-filename -o "%(title)s" --no-warnings "$URL" 2>/dev/null)

                # Ladda ner och konvertera ljudet
                yt-dlp --no-warnings --force-overwrites --embed-metadata --embed-thumbnail -f "bestaudio" -x --audio-format opus -o "%(title)s.%(ext)s" "$URL"
                
                # Hitta och radera källfilen (t.ex. .webm eller .m4a) manuellt
                # Detta är en robust metod för äldre yt-dlp versioner utan --rm-source-file
                find . -maxdepth 1 -name "$BASENAME.*" ! -name "*.opus" -type f -print0 | while IFS= read -r -d '' file; do
                    rm -- "$file"
                    gum style --foreground "240" "Temporär fil raderad: $(basename "$file")"
                done

                echo "" # Tom rad
                gum style --foreground "212" "✔ Nedladdning slutförd."
                ;;
            
        esac
        echo "" # Tom rad för bättre läsbarhet

        NEXT_STEP=$(gum choose "Ny länk" "Avsluta")
        if [[ "$NEXT_STEP" != "Ny länk" ]]; then
            break
        fi
    done
}

# Kör huvudfunktionen
main
