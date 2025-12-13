#!/bin/bash
# quicktube-mac.sh: macOS-version av QuickTube med stöd för YouTube, SVT Play och Cookies.

# Globala variabler
COOKIE_ARGS=()
LAST_ACTION=""

# --- Funktion för att kontrollera beroenden (macOS) ---
check_dependencies() {
    local missing_deps=()
    local required_cmds=("gum" "yt-dlp" "svtplay-dl" "mpv" "ffmpeg")

    for cmd in "${required_cmds[@]}"; do
        if ! command -v "$cmd" &> /dev/null;
            then
            missing_deps+=("$cmd")
        fi
    done

    if [ ${#missing_deps[@]} -gt 0 ]; then
        gum style --foreground="212" "Fel: Nödvändiga program saknas."
        gum style "Detta skript kräver: ${required_cmds[*]}"
        
        local install_command="brew install ${missing_deps[*]}"
        gum style --border normal --padding "1 1" --margin "1" "Förslag för installation med Homebrew:" "$install_command"
        
        exit 1
    fi

    if ! command -v pbpaste &> /dev/null;
        then
        gum style --foreground="212" "Varning: 'pbpaste' saknas. Klippbordshantering kanske inte fungerar."
    fi
}

# --- Funktion för att hämta urklipp (macOS) ---
get_clipboard() {
    if command -v pbpaste &> /dev/null;
        then
        pbpaste | tr -d '\0'
    else
        echo ""
    fi
}

select_cookie_browser() {
    BROWSER=$(gum choose "Ingen (Standard)" "chrome" "firefox" "brave" "edge" "safari" "opera" "vivaldi" "chromium")
    if [ "$BROWSER" != "Ingen (Standard)" ]; then
        COOKIE_ARGS=("--cookies-from-browser" "$BROWSER")
        gum style --foreground "212" "Webbläsare vald: $BROWSER"
    else
        COOKIE_ARGS=()
        gum style --foreground "212" "Cookies inaktiverade."
    fi
}

# --- Hantera SVT Play ---
handle_svt() {
    local url="$1"
    gum style --border rounded --padding "1 2" --border-foreground "240" \
        "SVT Play-länk detekterad.
Vad vill du göra?"

    ACTION=$(gum choose "Ladda ner (Bästa kvalitet + Undertexter)" "Ladda ner Hela Serien (-A)" "Ladda ner Hela Serien (yt-dlp)" "Ladda ner Specifika Avsnitt (yt-dlp)" "Ladda ner de X SISTA avsnitten (svtplay-dl)" "Stream (MPV)" "Ladda ner endast ljud")

    case "$ACTION" in
        "Ladda ner (Bästa kvalitet + Undertexter)")
            echo ""
            gum style "Startar nedladdning från SVT Play..."
            svtplay-dl -S -M "$url"
            if [ $? -eq 0 ]; then
                echo ""
                gum style --foreground "212" "✔ Nedladdning slutförd."
            else
                echo ""
                gum style --foreground "196" "❌ Nedladdning misslyckades."
            fi
            ;; 
        "Ladda ner Hela Serien (-A)")
            echo ""
            gum style "Startar nedladdning av hela serien..."
            svtplay-dl -S -M -A "$url"
            if [ $? -eq 0 ]; then
                echo ""
                gum style --foreground "212" "✔ Nedladdning slutförd."
            else
                 echo ""
                 gum style --foreground "196" "❌ Nedladdning misslyckades. Prova 'yt-dlp' alternativet."
            fi
            ;; 
        "Ladda ner Hela Serien (yt-dlp)")
            echo ""
            gum style "Startar nedladdning av hela serien med yt-dlp..."
            yt-dlp "${COOKIE_ARGS[@]}" --no-warnings --force-overwrites --embed-metadata --embed-thumbnail \
                   --embed-subs --write-subs --sub-langs all \
                   -o '%(series)s/S%(season_number)02dE%(episode_number)02d - %(title)s.%(ext)s' \
                   "$url"
            if [ $? -eq 0 ]; then
                echo ""
                gum style --foreground "212" "✔ Nedladdning slutförd."
            else
                echo ""
                gum style --foreground "196" "❌ Nedladdning misslyckades."
            fi
            ;; 
        "Ladda ner Specifika Avsnitt (yt-dlp)")
            echo ""
            ITEMS=$(gum input --placeholder "Ange avsnitt (t.ex. 1, 2-5, 10)..." --value "")
            if [ -n "$ITEMS" ]; then
                echo ""
                gum style "Laddar ner avsnitt $ITEMS med yt-dlp..."
                yt-dlp "${COOKIE_ARGS[@]}" --no-warnings --force-overwrites --embed-metadata --embed-thumbnail \
                       --embed-subs --write-subs --sub-langs all \
                       --playlist-items "$ITEMS" \
                       -o '%(series)s/S%(season_number)02dE%(episode_number)02d - %(title)s.%(ext)s' \
                       "$url"
                
                if [ $? -eq 0 ]; then
                    echo ""
                    gum style --foreground "212" "✔ Nedladdning slutförd."
                else
                    echo ""
                    gum style --foreground "196" "❌ Nedladdning misslyckades."
                fi
            fi
            ;; 
        "Ladda ner de X SISTA avsnitten (svtplay-dl)")
            echo ""
            COUNT=$(gum input --placeholder "Antal avsnitt från slutet (t.ex. 5)..." --value "")
            if [[ "$COUNT" =~ ^[0-9]+$ ]]; then
                gum style "Laddar ner de sista $COUNT avsnitten..."
                svtplay-dl -S -M -A --all-last "$COUNT" "$url"
                if [ $? -eq 0 ]; then
                    echo ""
                    gum style --foreground "212" "✔ Nedladdning slutförd."
                else
                    echo ""
                    gum style --foreground "196" "❌ Nedladdning misslyckades."
                fi
            else
                 gum style --foreground "196" "Felaktigt antal angivet."
            fi
            ;; 
        "Stream (MPV)")
            mpv --no-terminal "$url"
            LAST_ACTION="stream"
            ;; 
        "Ladda ner endast ljud")
            echo ""
            gum style "Laddar ner endast ljud..."
            svtplay-dl --only-audio "$url"
            if [ $? -eq 0 ]; then
                echo ""
                gum style --foreground "212" "✔ Nedladdning slutförd."
            else
                echo ""
                gum style --foreground "196" "❌ Nedladdning misslyckades."
            fi
            ;; 
    esac
}

# --- Hantera YouTube ---
handle_youtube() {
    local url="$1"
    
    MEDIA_INFO=$(yt-dlp "${COOKIE_ARGS[@]}" --flat-playlist --dump-json --no-warnings "$url" 2>/dev/null)

    if [ -z "$MEDIA_INFO" ]; then
        gum style --foreground="212" "Kunde inte hämta information för URL:en." "Kontrollera cookies om 'Bot'-fel uppstår."
        return 1 # Returnera felkod för att signalera "försök igen/fortsätt"
    else 
        local ITEM_TITLE
        IS_PLAYLIST=false

        # macOS-anpassning: Använd Perl istället för grep -P
        ITEM_TITLE=$(echo "$MEDIA_INFO" | perl -nle 'print $1 if /"title"\s*:\s*"([^"]+)"/' | head -n 1)

        if [[ "$url" == *"list="* ]] || echo "$MEDIA_INFO" | grep -q '"_type": "playlist"'; then
            IS_PLAYLIST=true
            if [ -z "$ITEM_TITLE" ]; then
                ITEM_TITLE="Okänd spellista"
            fi
        else
            if [ -z "$ITEM_TITLE" ]; then
                # Om titel saknas trots lyckad hämtning
                ITEM_TITLE="Okänd video"
            fi
        fi
        
        VIDEO_TITLE="$ITEM_TITLE"
        FORMATTED_TITLE=$(echo "$VIDEO_TITLE" | fmt -w 60)
        
        if [ "$IS_PLAYLIST" = true ]; then
             gum style --border rounded --padding "1 2" --border-foreground "240" \
                "Vad vill du göra med spellistan:
$FORMATTED_TITLE?"

            ACTION=$(gum choose "Stream Hela Spellistan (Video)" "Stream Hela Spellistan (Ljud)" "Ladda ner Hela Spellistan (Video)" "Ladda ner Hela Spellistan (Ljud)")

            case "$ACTION" in
                "Stream Hela Spellistan (Video)")
                    mpv --no-terminal "$url"
                    LAST_ACTION="stream"
                    ;; 
                "Stream Hela Spellistan (Ljud)")
                    mpv --no-video "$url"
                    LAST_ACTION="stream"
                    ;; 
                "Ladda ner Hela Spellistan (Video)")
                    echo ""
                    gum style "Startar nedladdning av hela spellistan (video)..."
                    yt-dlp "${COOKIE_ARGS[@]}" --no-warnings --force-overwrites --embed-metadata --embed-thumbnail \
                           -f "bestvideo[ext=mp4]+bestaudio[ext=m4a]/best[ext=mp4]/best" \
                           --merge-output-format mp4 \
                           -o '%(playlist)s/%(playlist_index)02d - %(title)s.%(ext)s' "$url"
                    if [ $? -eq 0 ]; then
                        gum style --foreground "212" "✔ Nedladdning av spellista slutförd."
                    else
                        gum style --foreground "196" "❌ Nedladdning misslyckades."
                    fi
                    ;; 
                "Ladda ner Hela Spellistan (Ljud)")
                    echo ""
                    gum style "Startar nedladdning av hela spellistan (ljud)..."
                    yt-dlp "${COOKIE_ARGS[@]}" --no-warnings --force-overwrites --embed-metadata --embed-thumbnail \
                           -f "bestaudio" -x --audio-format opus \
                           -o '%(playlist)s/%(playlist_index)02d - %(title)s.%(ext)s' "$url"
                    if [ $? -eq 0 ]; then
                        gum style --foreground "212" "✔ Nedladdning av spellista slutförd."
                    else
                        gum style --foreground "196" "❌ Nedladdning misslyckades."
                    fi
                    ;; 
            esac
        else
            # Enskild video
            gum style --border rounded --padding "1 2" --border-foreground "240" \
                "Vad vill du göra med:
$FORMATTED_TITLE?"
            
            ACTION=$(gum choose "Stream Video (MPV)" "Stream Ljud (MPV)" "Ladda ner video" "Ladda ner ljud")

            case "$ACTION" in
                "Stream Video (MPV)")
                    mpv --no-terminal "$url"
                    LAST_ACTION="stream"
                    ;; 
                
                "Stream Ljud (MPV)")
                    mpv --no-video "$url"
                    LAST_ACTION="stream"
                    ;; 

                "Ladda ner video")
                    FORMATS_OUTPUT=$(yt-dlp "${COOKIE_ARGS[@]}" -F --no-warnings "$url" 2>/dev/null)
                    
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
                        return 1
                    fi

                    SORTED_TABLE_ROWS=($(printf "%s\n" "${TABLE_DATA_ROWS[@]}" | sort -t, -k2 -r))

                    TABLE_INPUT=$(echo "$HEADER"; IFS=$'\n'; echo "${SORTED_TABLE_ROWS[*]}")
                    CHOICE=$(echo "$TABLE_INPUT" | gum table -s, --height 10)
                    
                    if [ -z "$CHOICE" ]; then
                        return 1
                    fi

                    FORMAT_CODE=$(echo "$CHOICE" | cut -d, -f1)
                    
                    echo ""
                    gum style "Startar nedladdning av video..."
                    # FIX: Tog bort mellanslag i filnamnsmallen
                    yt-dlp "${COOKIE_ARGS[@]}" --no-warnings --force-overwrites --embed-metadata --embed-thumbnail -f "$FORMAT_CODE+bestaudio" --merge-output-format mp4 -o "%(title)s-%(height)sp.%(ext)s" "$url"
                    
                    if [ $? -eq 0 ]; then
                        echo ""
                        gum style --foreground "212" "✔ Nedladdning slutförd."
                    else
                        echo ""
                        gum style --foreground "196" "❌ Nedladdning misslyckades."
                    fi
                    ;; 

                "Ladda ner ljud")
                    echo ""
                    gum style "Startar nedladdning av ljud..."
                    
                    # FIX: Tog bort mellanslag i filnamnsmallen
                    BASENAME=$(yt-dlp "${COOKIE_ARGS[@]}" --get-filename -o "% (title)s" --no-warnings "$url" 2>/dev/null)

                    # FIX: Tog bort mellanslag i filnamnsmallen
                    yt-dlp "${COOKIE_ARGS[@]}" --no-warnings --force-overwrites --embed-metadata --embed-thumbnail -f "bestaudio" -x --audio-format opus -o "% (title)s.%(ext)s" "$url"
                    
                    if [ $? -eq 0 ]; then
                        find . -maxdepth 1 -name "$BASENAME.*" ! -name "*.opus" -type f -print0 | while IFS= read -r -d '' file; do
                            rm -- "$file"
                            gum style --foreground "240" "Temporär fil raderad: $(basename "$file")"
                        done
                        echo ""
                        gum style --foreground "212" "✔ Nedladdning slutförd."
                    else
                        echo ""
                        gum style --foreground "196" "❌ Nedladdning misslyckades."
                    fi
                    ;; 
            esac
        fi
    fi
}

# Huvudfunktion
main() {
    check_dependencies
    LAST_ACTION=""
    COOKIE_ARGS=()

    while true; do
        CLIPBOARD_CONTENT=$(get_clipboard)
        URL_FROM_CLIPBOARD=""
        
        if [[ "$LAST_ACTION" != "stream" ]]; then
            local trimmed_content
            trimmed_content=$(echo "$CLIPBOARD_CONTENT" | sed 's/^[[:space:]]*//;s/[[:space:]]*$//')

            case "$trimmed_content" in
                "http://www.youtube.com/"* |
                "https://www.youtube.com/"* |
                "http://youtube.com/"* |
                "https://youtube.com/"* |
                "http://youtu.be/"* |
                "https://youtu.be/"* |
                "www.youtube.com/"* |
                "youtube.com/"* |
                "youtu.be/"* |
                "http://www.svtplay.se/"* |
                "https://www.svtplay.se/"* |
                "http://svtplay.se/"* |
                "https://svtplay.se/"* |
                "www.svtplay.se/"* |
                "svtplay.se/"* )
                    URL_FROM_CLIPBOARD="$CLIPBOARD_CONTENT"
                    ;; 
            esac
        fi
        LAST_ACTION=""
        
        URL=$(gum input --placeholder "Klistra in/skriv en URL (YouTube/SVT Play)..." --value "$URL_FROM_CLIPBOARD")

        if [ -z "$URL" ]; then
            gum style "Ingen URL angiven. Avslutar."
            break
        fi

        if [[ "$URL" == *"svtplay.se"* ]]; then
            handle_svt "$URL"
        else
            handle_youtube "$URL"
            # Om handle_youtube returnerar 1 (fel/avbryt), fortsätter loopen och visar menyn nedan
        fi

        echo ""

        NEXT_STEP=$(gum choose "Ny länk" "Välj webbläsare för cookies" "Avsluta")
        
        if [[ "$NEXT_STEP" == "Välj webbläsare för cookies" ]]; then
            select_cookie_browser
            continue
        elif [[ "$NEXT_STEP" != "Ny länk" ]]; then
            break
        fi
    done
}

# Kör huvudfunktionen
main