#!/bin/bash
# quicktube.v1.sh: A TUI script to handle YouTube and SVT Play links using gum, yt-dlp, svtplay-dl, and mpv.

# Global variables
COOKIE_ARGS=()
LAST_ACTION=""

# --- Function to check dependencies ---
check_dependencies() {
    local missing_deps=()
    # Include ffmpeg and svtplay-dl in the list of mandatory dependencies
    for cmd in gum yt-dlp svtplay-dl mpv ffmpeg; do 
        if ! command -v "$cmd" &> /dev/null;
then
            missing_deps+=("$cmd")
        fi
    done

    # Check for at least one clipboard tool
    if ! command -v wl-paste &> /dev/null && ! command -v xclip &> /dev/null;
then
        missing_deps+=("wl-paste or xclip")
    fi

    if [ ${#missing_deps[@]} -gt 0 ]; then
        gum style --foreground="212" "Error: The following dependencies are missing:"
        for dep in "${missing_deps[@]}"; do
            echo "- $dep"
        done
        gum style --foreground="212" "Please install them and try again."
        exit 1
    fi
}


# --- Function to get clipboard content ---
get_clipboard() {
    if command -v wl-paste &> /dev/null;
then
        wl-paste | tr -d "\0"
    elif command -v xclip &> /dev/null;
then
        xclip -o -selection clipboard | tr -d "\0"
    fi
}

select_cookie_browser() {
    BROWSER=$(gum choose "None (Default)" "chrome" "firefox" "brave" "edge" "safari" "opera" "vivaldi" "chromium")
    if [ "$BROWSER" != "None (Default)" ]; then
        COOKIE_ARGS=("--cookies-from-browser" "$BROWSER")
        gum style --foreground "212" "Browser selected: $BROWSER"
    else
        COOKIE_ARGS=()
        gum style --foreground "212" "Cookies disabled."
    fi
}


# --- Handle SVT Play ---
handle_svt() {
    local url="$1"
    gum style --border rounded --padding "1 2" --border-foreground "240" \
        "SVT Play link detected.
What do you want to do?"

    ACTION=$(gum choose "Download (Best quality + Subtitles)" "Download Whole Series (-A)" "Download Whole Series (yt-dlp)" "Download Specific Episodes (yt-dlp)" "Download the LAST X episodes (svtplay-dl)" "Stream (MPV)" "Download audio only")

    case "$ACTION" in
        "Download (Best quality + Subtitles)")
            echo ""
            gum style "Starting download from SVT Play..."
            # -S = subtitles, -M = merge subtitles
            svtplay-dl -S -M "$url"
            if [ $? -eq 0 ]; then
                echo ""
                gum style --foreground "212" "✔ Download complete."
            else
                echo ""
                gum style --foreground "196" "❌ Download failed."
            fi
            ;; 
        "Download Whole Series (-A)")
            echo ""
            gum style "Starting download of entire series..."
            svtplay-dl -S -M -A "$url"
            if [ $? -eq 0 ]; then
                echo ""
                gum style --foreground "212" "✔ Download complete."
            else
                 echo ""
                 gum style --foreground "196" "❌ Download failed. Try the yt-dlp option."
            fi
            ;; 
        "Download Whole Series (yt-dlp)")
            echo ""
            gum style "Starting download of entire series with yt-dlp..."
            yt-dlp "${COOKIE_ARGS[@]}" --no-warnings --force-overwrites --embed-metadata --embed-thumbnail \
                   --embed-subs --write-subs --sub-langs all \
                   -o "%(series)s/S%(season_number)02dE%(episode_number)02d - %(title)s.%(ext)s" \
                   "$url"
            if [ $? -eq 0 ]; then
                echo ""
                gum style --foreground "212" "✔ Download complete."
            else
                echo ""
                gum style --foreground "196" "❌ Download failed."
            fi
            ;; 
        "Download Specific Episodes (yt-dlp)")
            echo ""
            ITEMS=$(gum input --placeholder "Enter episodes (e.g., 1, 2-5, 10)..." --value "")
            if [ -n "$ITEMS" ]; then
                echo ""
                gum style "Downloading episodes $ITEMS with yt-dlp..."
                yt-dlp "${COOKIE_ARGS[@]}" --no-warnings --force-overwrites --embed-metadata --embed-thumbnail \
                       --embed-subs --write-subs --sub-langs all \
                       --playlist-items "$ITEMS" \
                       -o "%(series)s/S%(season_number)02dE%(episode_number)02d - %(title)s.%(ext)s" \
                       "$url"
                
                if [ $? -eq 0 ]; then
                    echo ""
                    gum style --foreground "212" "✔ Download complete."
                else
                    echo ""
                    gum style --foreground "196" "❌ Download failed."
                fi
            fi
            ;; 
        "Download the LAST X episodes (svtplay-dl)")
            echo ""
            COUNT=$(gum input --placeholder "Number of episodes from the end (e.g., 5)..." --value "")
            if [[ "$COUNT" =~ ^[0-9]+$ ]]; then
                gum style "Downloading the last $COUNT episodes..."
                svtplay-dl -S -M -A --all-last "$COUNT" "$url"
                if [ $? -eq 0 ]; then
                    echo ""
                    gum style --foreground "212" "✔ Download complete."
                else
                    echo ""
                    gum style --foreground "196" "❌ Download failed."
                fi
            else
                 gum style --foreground "196" "Invalid number specified."
            fi
            ;; 
        "Stream (MPV)")
            # MPV usually handles SVT Play links directly (via yt-dlp backend)
            mpv --no-terminal "$url"
            LAST_ACTION="stream"
            ;; 
        "Download audio only")
            echo ""
            gum style "Downloading audio only..."
            svtplay-dl --only-audio "$url"
            if [ $? -eq 0 ]; then
                echo ""
                gum style --foreground "212" "✔ Download complete."
            else
                echo ""
                gum style --foreground "196" "❌ Download failed."
            fi
            ;; 
    esac
}


# --- Handle YouTube ---
handle_youtube() {
    local url="$1"
    
    # Get information about the URL
    MEDIA_INFO=$(yt-dlp "${COOKIE_ARGS[@]}" --flat-playlist --dump-json --no-warnings "$url" 2>/dev/null)

    # Check if information could be retrieved
    if [ -z "$MEDIA_INFO" ]; then
        gum style --foreground="212" "Could not retrieve information for the URL." "Check that the URL is valid and public (YouTube), then try again."
        return 1
    fi

    local ITEM_TITLE
    IS_PLAYLIST=false

    # Title parsing with grep -oP (Linux)
    ITEM_TITLE=$(echo "$MEDIA_INFO" | grep -oP '"title"\s*:\s*"\K[^"+' | head -n 1)

    if [[ "$url" == *"list="* ]] || echo "$MEDIA_INFO" | grep -q '"_type": "playlist"' ; then
        IS_PLAYLIST=true
        if [ -z "$ITEM_TITLE" ]; then
            ITEM_TITLE="Unknown playlist"
        fi
    else
        if [ -z "$ITEM_TITLE" ]; then
            gum style --foreground="212" "Could not retrieve video information." "Check that the URL is valid and public, then try again."
            return 1
        fi
    fi
    
    VIDEO_TITLE="$ITEM_TITLE"
    FORMATTED_TITLE=$(echo "$VIDEO_TITLE" | fmt -w 60)
    
    if [ "$IS_PLAYLIST" = true ]; then
         gum style --border rounded --padding "1 2" --border-foreground "240" \
            "What do you want to do with the playlist:
$FORMATTED_TITLE?"

        ACTION=$(gum choose "Stream Full Playlist (Video)" "Stream Full Playlist (Audio)" "Download Full Playlist (Video)" "Download Full Playlist (Audio)")

        case "$ACTION" in
            "Stream Full Playlist (Video)")
                mpv --no-terminal "$url"
                LAST_ACTION="stream"
                ;; 
            "Stream Full Playlist (Audio)")
                mpv --no-video "$url"
                LAST_ACTION="stream"
                ;; 
            "Download Full Playlist (Video)")
                echo ""
                gum style "Starting download of full playlist (video)..."
                yt-dlp "${COOKIE_ARGS[@]}" --no-warnings --force-overwrites --embed-metadata --embed-thumbnail \
                       -f "bestvideo[ext=mp4]+bestaudio[ext=m4a]/best[ext=mp4]/best" \
                       --merge-output-format mp4 \
                       -o '%(playlist)s/%(playlist_index)02d - %(title)s.%(ext)s' "$url"
                if [ $? -eq 0 ]; then
                    gum style --foreground "212" "✔ Playlist download complete."
                else
                    gum style --foreground "196" "❌ Download failed."
                fi
                ;; 
            "Download Full Playlist (Audio)")
                echo ""
                gum style "Starting download of full playlist (audio)..."
                yt-dlp "${COOKIE_ARGS[@]}" --no-warnings --force-overwrites --embed-metadata --embed-thumbnail \
                       -f "bestaudio/best" -x --audio-format opus \
                       -o '%(playlist)s/%(playlist_index)02d - %(title)s.%(ext)s' "$url"
                if [ $? -eq 0 ]; then
                    gum style --foreground "212" "✔ Playlist download complete."
                else
                    gum style --foreground "196" "❌ Download failed."
                fi
                ;; 
        esac
    else
        # Single video
        gum style --border rounded --padding "1 2" --border-foreground "240" \
            "What do you want to do with:
$FORMATTED_TITLE?"
        
        ACTION=$(gum choose "Stream Video (MPV)" "Stream Audio (MPV)" "Download video" "Download audio")

        case "$ACTION" in
            "Stream Video (MPV)")
                mpv --no-terminal "$url"
                LAST_ACTION="stream"
                ;; 
            
            "Stream Audio (MPV)")
                mpv --no-video "$url"
                LAST_ACTION="stream"
                ;; 

            "Download video")
                FORMATS_OUTPUT=$(yt-dlp "${COOKIE_ARGS[@]}" -F --no-warnings "$url" 2>/dev/null)
                
                HEADER="ID,Resolution,FPS,Filetype,Codec,Size"
                declare -a TABLE_DATA_ROWS
                
                while IFS= read -r line; do
                    # New, more flexible regex
                    if [[ "$line" =~ ^([0-9]+)\ +([a-zA-Z0-9]+)\ +.*([0-9]+x[0-9]+).*([0-9.]+) ]]; then
                        id="${BASH_REMATCH[1]}"
                        ext="${BASH_REMATCH[2]}"
                        res="${BASH_REMATCH[3]}" # Matches resolution anywhere after ID/EXT
                        fps="${BASH_REMATCH[4]:-N/A}" # FPS can be optional
                        
                        filesize="N/A"
                        if [[ "$line" =~ ([0-9.]+(MiB|GiB)) ]]; then
                            filesize="${BASH_REMATCH[1]}"
                        fi
                        
                        codec="N/A"
                        if [[ "$line" =~ ([a-zA-Z0-9.]+)\ +video\ only ]]; then
                            codec="${BASH_REMATCH[1]}"
                        fi

                        if [[ "$line" =~ video\ only ]]; then # Ensure it is a video line
                            TABLE_DATA_ROWS+=("${id},${res},${fps},${ext},${codec},${filesize}")
                        fi
                    fi
                done <<< "$FORMATS_OUTPUT"

                if [ ${#TABLE_DATA_ROWS[@]} -eq 0 ]; then
                    gum style --foreground="212" "Could not find any video streams."
                    return 1
                fi

                # Sort formats (uses sort -V for version sorting which usually exists on Linux)
                SORTED_TABLE_ROWS=($(printf "%s\n" "${TABLE_DATA_ROWS[@]}" | sort -t, -k2,2V -r))

                TABLE_INPUT=$(echo "$HEADER"; IFS=$n; echo "${SORTED_TABLE_ROWS[*]}")
                CHOICE=$(echo "$TABLE_INPUT" | gum table -s, --height 10)
                
                if [ -z "$CHOICE" ]; then
                    return 1
                fi

                FORMAT_CODE=$(echo "$CHOICE" | cut -d, -f1)
                
                echo ""
                gum style "Starting video download..."
                # Corrected filename (space removed)
                yt-dlp "${COOKIE_ARGS[@]}" --no-warnings --force-overwrites --embed-metadata --embed-thumbnail -f "$FORMAT_CODE+bestaudio" --merge-output-format mp4 -o "% (title)s-%(height)sp.%(ext)s" "$url"

                if [ $? -eq 0 ]; then
                    echo ""
                    gum style --foreground "212" "✔ Download complete."
                else
                    echo ""
                    gum style --foreground "196" "❌ Download failed."
                fi
                ;; 

            "Download audio")
                echo ""
                gum style "Starting audio download..."
                
                # Corrected filename (space removed)
                BASENAME=$(yt-dlp "${COOKIE_ARGS[@]}" --get-filename -o "% (title)s" --no-warnings "$url" 2>/dev/null)

                # Corrected filename (space removed)
                yt-dlp "${COOKIE_ARGS[@]}" --no-warnings --force-overwrites --embed-metadata --embed-thumbnail -f "bestaudio/best" -x --audio-format opus -o "% (title)s.%(ext)s" "$url"
                
                if [ $? -eq 0 ]; then
                    find . -maxdepth 1 -name "$BASENAME.*" ! -name "*.opus" -type f -print0 | while IFS= read -r -d '' file; do
                        rm -- "$file"
                        gum style --foreground "240" "Temporary file deleted: $(basename "$file")"
                    done

                    echo ""
                    gum style --foreground "212" "✔ Download complete."
                else
                    echo ""
                    gum style --foreground "196" "❌ Download failed."
                fi
                ;; 
esac
    fi
}


# Main function
main() {
    check_dependencies
    LAST_ACTION=""
    
    while true; do
        # Get content from clipboard to potentially pre-fill
        CLIPBOARD_CONTENT=$(get_clipboard)
        URL_FROM_CLIPBOARD=""
        
        # Pre-fill only if the last action was NOT "stream"
        if [[ "$LAST_ACTION" != "stream" ]]; then
            # Trim any leading/trailing whitespace from the clipboard
            local trimmed_content
            trimmed_content=$(echo "$CLIPBOARD_CONTENT" | sed 's/^[[:space:]]*//;s/[[:space:]]*$//')

            # Check if the trimmed content starts with a valid YouTube URL variant
            case "$trimmed_content" in
                "http://www.youtube.com/"* | \
                "https://www.youtube.com/"* | \
                "http://youtube.com/"* | \
                "https://youtube.com/"* | \
                "http://youtu.be/"* | \
                "https://youtu.be/"* | \
                "www.youtube.com/"* | \
                "youtube.com/"* | \
                "youtu.be/"* | \
                "http://www.svtplay.se/"* | \
                "https://www.svtplay.se/"* | \
                "http://svtplay.se/"* | \
                "https://svtplay.se/"* | \
                "www.svtplay.se/"* | \
                "svtplay.se/"* ) 
                    # If it matches, use the original (untrimmed) clipboard content
                    URL_FROM_CLIPBOARD="$CLIPBOARD_CONTENT"
                    ;; 
            esac
        fi
        LAST_ACTION=""
        
        # Use "gum input" and pre-fill with clipboard content if it is a valid link
        URL=$(gum input --placeholder "Paste/enter a URL (YouTube/SVT Play)..." --value "$URL_FROM_CLIPBOARD")

        # If the user does not enter anything, exit
        if [ -z "$URL" ]; then
            gum style "No URL specified. Exiting."
            break
        fi

        # Identify service and call the correct function
        if [[ "$URL" == *"svtplay.se"* ]]; then
            handle_svt "$URL"
        else
            handle_youtube "$URL"
        fi

        echo "" # Empty line for better readability

        NEXT_STEP=$(gum choose "New link" "Select browser for cookies" "Exit")
        
        if [[ "$NEXT_STEP" == "Select browser for cookies" ]]; then
            select_cookie_browser
            continue
        elif [[ "$NEXT_STEP" != "New link" ]]; then
            break
        fi
    done
}

# Run main function
main

