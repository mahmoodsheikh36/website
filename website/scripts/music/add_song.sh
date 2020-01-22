#!/bin/sh

if [ -z "$1" ]; then
    echo "please enter path to audio file as first argument"
    exit 1
fi

audio_file_path="$1"
music_library=/home/mahmooz/media/music


if [ ! -f "$audio_file_path" ]; then
    echo first argument is not a path to a file
    exit 1
fi

audio_mimetype=false
case "$(file --mime-type "$audio_file_path")" in *audio/*) audio_mimetype=true;; esac
if ! $audio_mimetype; then
    echo given argument is a path to file but doesnt contain audio
    exit 1
fi

if [ ! -d "$music_library" ]; then
    mkdir "$music_library"
    echo created music library directory
fi
if [ ! -d "$music_library/audio" ]; then
    mkdir "$music_library/audio"
    echo created audio directory
fi
if [ ! -d "$music_library/image" ]; then
    mkdir "$music_library/image"
    echo created image directory
fi
if [ ! -f "$music_library/data.sqlite" ]; then
    sqlite3 "$music_library/data.sqlite" "$(cat init_music_db.sql)"
    echo created sqlite database
fi

ffmpeg_output=$(ffmpeg -i "$audio_file_path" 2>&1)
artist=$(echo "$ffmpeg_output" | grep -m1 'artist' | tr -s ' ' | cut -d ' ' -f4- | sed 's/"/\"\"/g')
name=$(echo "$ffmpeg_output" | grep -m1 'title' | tr -s ' ' | cut -d ' ' -f4- | sed 's/"/\"\"/g')
album=$(echo "$ffmpeg_output" | grep -m1 'album' | tr -s ' ' | cut -d ' ' -f4- | sed 's/"/\"\"/g')
lyrics=$(echo "$ffmpeg_output" | sed -n '/^\s*:.*/p' | tr -s ' ' | cut -d ' ' -f3- | sed 's/"/\"\"/g')

audio_file_name="$(echo "$audio_file_path" | rev | cut -d '/' -f1 | rev)"
image_file_path="$music_library/image/$(echo "$audio_file_name" | sed 's/\.[a-z0-9]\+$/.png/')"
2>/dev/null 1>/dev/null ffmpeg -i "$audio_file_path" -c:a copy "$image_file_path"

time="$(echo "$ffmpeg_output" | grep Duration | cut -d ' ' -f4 | tr -d ',')"
minutes="$(echo "$time" | cut -d ':' -f2)"
seconds="$(echo "$time" | cut -d ':' -f3 | cut -d '.' -f1)"
duration=$(expr $minutes \* 60 + $seconds)

if [ -z "$lyrics" ]; then
    lyrics="NULL";
else
    lyrics="$(echo "$lyrics" | sed 's/"/\"\"/g')"
fi
if [ ! -f "$image_file_path" ]; then
    image_file_path="NULL"
else
    image_file_path="$library_path$(echo "$image_file_path" | sed 's/"/\"\"/g')"
fi

cp "$audio_file_path" "$music_library/audio/"
new_audio_file_path="$music_library/audio/$audio_file_name"

sqlite3 "$music_library/data.sqlite" "insert into songs (album, name, artist, audio_file_path, image_file_path, lyrics, duration) VALUES(\"$album\", \"$name\", \"$artist\", \"$new_audio_file_path\", \"$image_file_path\", \"$lyrics\", $duration)"

echo added song \"$name\" by \"$artist\" to library
