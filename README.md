# hello!

# things im planning on fixing/doing/reconsidering
1. all the functions in /music route need to be edited because the way they accept data is weird, private data like username and password should be accepted using POST data, whereas nonprivate data like original_file_name should be accepted via url parameters, i think thats the best approach
2. the entire /music route needs to be looked at, it makes no tests to see what exists in the database before adding new content, like if a playlist_songs row was added through /music/add_song_to_playlist there is no guarentee that the song_id of that row actually refers to a valid song
3. I HAVE TO PREVENT DUPLICATES FROM ENTERING THE DAMN DATABASE !!!!
