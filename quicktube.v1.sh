#!/bin/bash
# yt-helper.sh: Ett TUI-skript för att hantera YouTube-länkar med gum, yt-dlp och mpv.

# --- Funktion för att kontrollera beroenden ---
check_dependencies() {
    local missing_deps=()
    # Inkludera ffmpeg i listan över obligatoriska beroenden
    for cmd in gum yt-dlp mpv ffmpeg; do
        if ! command -v "$cmd" &> /dev/null; then
            missing_deps+=("$cmd")
        fi
done

    # Kontrollera för minst ett urklippsverktyg
    if ! command -v wl-paste &> /dev/null && ! command -v xclip &> /dev/null; then
        missing_deps+=("wl-paste eller xclip")
    fi

    if [ ${#missing_deps[@]} -gt 0 ]; then
        gum style --foreground="212" "Fel: Följande beroenden saknas:"
        for dep in "${missing_deps[@]}"; do
            echo "- $dep"
        done
        gum style --foreground="212" "Installera dem och försök igen."
        exit 1
    fi
}

# --- Funktion för att hämta urklipp ---
get_clipboard() {
    if command -v wl-paste &> /dev/null; then
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


        # Hämta information om URL:en, inklusive om det är en spellista eller en enstaka video
        MEDIA_INFO=$(yt-dlp --flat-playlist --dump-json --no-warnings "$URL" 2>/dev/null)

        # Kontrollera om information kunde hämtas
        if [ -z "$MEDIA_INFO" ]; then
            gum style --foreground="212" "Kunde inte hämta information för URL:en." "Kontrollera att URL:en är giltig och offentlig, försök sedan igen."
            continue
        fi

        local ITEM_TITLE
        IS_PLAYLIST=false

        # Extrahera titel och typ med sed/grep istället för jq
        # "title": "Den här texten vill vi ha",
        # "title" : "Den här texten vill vi ha" ,
        # "title" : "Den här texten vill vi ha",
        # "title":"Den här texten vill vi ha",
        # Notera: Denna regex är avsedd att vara robust för olika JSON-formateringar
        ITEM_TITLE=$(echo "$MEDIA_INFO" | grep -oP '"title"\s*:\s*"\K[^"]+' | head -n 1)

        # Kontrollera om det är en spellista genom att söka efter '"_type": "playlist"' i JSON
        # ELLER om URL:en innehåller "list=" (snabbare och oftast tillräckligt för YouTube)
        if [[ "$URL" == *"list="* ]] || echo "$MEDIA_INFO" | grep -q '"_type": "playlist"'; then
            IS_PLAYLIST=true
            # Om titeln är tom, sätt en fallback
            if [ -z "$ITEM_TITLE" ]; then
                ITEM_TITLE="Okänd spellista"
            fi
        else
            # Om det inte är en spellista är det troligen en video
            # Om titeln är tom här är det ett fel
            if [ -z "$ITEM_TITLE" ]; then
                gum style --foreground="212" "Kunde inte hämta videoinformation." "Kontrollera att URL:en är giltig och offentlig, försök sedan igen."
                continue
            fi
        fi
        
        VIDEO_TITLE="$ITEM_TITLE"


        # Formatera titeln för snygg radbrytning
        FORMATTED_TITLE=$(echo "$VIDEO_TITLE" | fmt -w 60)
        
        # Anpassa menyn och logiken baserat på om det är en spellista eller inte
        if [ "$IS_PLAYLIST" = true ]; then
            # --- MENY FÖR SPELLISTA ---
            gum style --border rounded --padding "1 2" --border-foreground "240" \
                "Vad vill du göra med spellistan:
$FORMATTED_TITLE?"

            ACTION=$(gum choose "Stream Hela Spellistan (Video)" "Stream Hela Spellistan (Ljud)" "Ladda ner Hela Spellistan (Video)" "Ladda ner Hela Spellistan (Ljud)")

            case "$ACTION" in
                "Stream Hela Spellistan (Video)")
                    mpv --no-terminal "$URL"
                    LAST_ACTION="stream"
                    ;;
                "Stream Hela Spellistan (Ljud)")
                    mpv --no-video "$URL"
                    LAST_ACTION="stream"
                    ;;
                "Ladda ner Hela Spellistan (Video)")
                    echo ""
                    gum style "Startar nedladdning av hela spellistan (video)..."
                    # Ladda ner video (bästa formatet som mp4) och ljud, och muxa dem.
                    # Skapar en underkatalog för spellistan.
                    yt-dlp --no-warnings --force-overwrites --embed-metadata --embed-thumbnail \
                           -f "bestvideo[ext=mp4]+bestaudio[ext=m4a]/best[ext=mp4]/best" \
                           --merge-output-format mp4 \
                           -o '%(playlist)s/%(playlist_index)02d - %(title)s.%(ext)s' "$URL"
                    gum style --foreground "212" "✔ Nedladdning av spellista slutförd."
                    ;;
                "Ladda ner Hela Spellistan (Ljud)")
                    echo ""
                    gum style "Startar nedladdning av hela spellistan (ljud)..."
                    # Ladda ner och konvertera till opus.
                    # Skapar en underkatalog för spellistan.
                    yt-dlp --no-warnings --force-overwrites --embed-metadata --embed-thumbnail \
                           -f "bestaudio" -x --audio-format opus \
                           -o '%(playlist)s/%(playlist_index)02d - %(title)s.%(ext)s' "$URL"
                    gum style --foreground "212" "✔ Nedladdning av spellista slutförd."
                    ;;
            esac
        else
            # --- MENY FÖR ENSKILD VIDEO ---
            gum style --border rounded --padding "1 2" --border-foreground "240" \
                "Vad vill du göra med:
$FORMATTED_TITLE?"
            
            ACTION=$(gum choose "Stream Video (MPV)" "Stream Ljud (MPV)" "Ladda ner video" "Ladda ner ljud")

            case "$ACTION" in
                "Stream Video (MPV)")
                    mpv --no-terminal "$URL"
                    LAST_ACTION="stream"
                    ;;
                
                "Stream Ljud (MPV)")
                    mpv --no-video "$URL"
                    LAST_ACTION="stream"
                    ;;

                "Ladda ner video")
                    # Hämta tillgängliga format, dölj varningar
                    FORMATS_OUTPUT=$(yt-dlp -F --no-warnings "$URL" 2>/dev/null)
                    
                    HEADER="ID,Upplösning,FPS,Filtyp,Codec,Storlek"
                    declare -a TABLE_DATA_ROWS
                    
                    while IFS= read -r line; do
                        if [[ "$line" =~ ^([0-9]+)\ +([a-zA-Z0-9]+)\ +([0-9]+x[0-9]+)(\ +([0-9.]+))? ]]; then
                            id="${BASH_REMATCH[1]}"
                            ext="${BASH_REMATCH[2]}"
                            res="${BASH_REMATCH[3]}"
                            fps="${BASH_REMATCH[5]:-N/A}"
                            
                            filesize="N/A"
                            if [[ "$line" =~ ([0-9.]+(MiB|GiB)) ]]; then
                                filesize="${BASH_REMATCH[1]}"
                            fi
                            
                            codec="N/A"
                            if [[ "$line" =~ ([a-zA-Z0-9.]+)\ +video\ only ]]; then
                                codec="${BASH_REMATCH[1]}"
                            fi

                            if [[ "$line" =~ video\ only ]]; then
                                TABLE_DATA_ROWS+=("${id},${res},${fps},${ext},${codec},${filesize}")
                            fi
                        fi
                    done <<< "$FORMATS_OUTPUT"

                    if [ ${#TABLE_DATA_ROWS[@]} -eq 0 ]; then
                        gum style --foreground="212" "Kunde inte hitta några videoströmmar."
                        continue
                    fi

                    SORTED_TABLE_ROWS=($(printf "%s\n" "${TABLE_DATA_ROWS[@]}" | sort -t, -k2,2V -r))

                    TABLE_INPUT=$(echo "$HEADER"; IFS=$'\n'; echo "${SORTED_TABLE_ROWS[*]}")
                    CHOICE=$(echo "$TABLE_INPUT" | gum table -s, --height 10)
                    
                    if [ -z "$CHOICE" ]; then
                        continue
                    fi

                    FORMAT_CODE=$(echo "$CHOICE" | cut -d, -f1)
                    
                    echo ""
                    gum style "Startar nedladdning av video..."
                    yt-dlp --no-warnings --force-overwrites --embed-metadata --embed-thumbnail -f "$FORMAT_CODE+bestaudio" --merge-output-format mp4 -o "%(title)s-%(height)sp.%(ext)s" "$URL"

                    echo ""
                    gum style --foreground "212" "✔ Nedladdning slutförd."
                    ;;

                "Ladda ner ljud")
                    echo ""
                    gum style "Startar nedladdning av ljud..."
                    
                    BASENAME=$(yt-dlp --get-filename -o "%(title)s" --no-warnings "$URL" 2>/dev/null)

                    yt-dlp --no-warnings --force-overwrites --embed-metadata --embed-thumbnail -f "bestaudio" -x --audio-format opus -o "%(title)s.%(ext)s" "$URL"
                    
                    find . -maxdepth 1 -name "$BASENAME.*" ! -name "*.opus" -type f -print0 | while IFS= read -r -d '' file; do
                        rm -- "$file"
                        gum style --foreground "240" "Temporär fil raderad: $(basename "$file")"
                    done

                    echo ""
                    gum style --foreground "212" "✔ Nedladdning slutförd."
                    ;;
            esac
        fi

        echo "" # Tom rad för bättre läsbarhet

        NEXT_STEP=$(gum choose "Ny länk" "Avsluta")
        if [[ "$NEXT_STEP" != "Ny länk" ]]; then
            break
        fi
    done
}

# Kör huvudfunktionen
main
