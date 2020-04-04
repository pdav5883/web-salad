dir=$1
rm $dir/games.txt $dir/players.txt $dir/words.txt
echo -e '{"abcasd": {"num_words": "5", "t1": "60", "t2": "60", "t3": "30", "started": false, "complete": false},' > $dir/games.txt
echo -e '"wxyz": {"num_words": "3", "t1": "7", "t2": "7", "t3": "7", "started": false, "complete": false}}\n' >> $dir/games.txt
echo "{}" > $dir/players.txt
echo "{}" > $dir/words.txt
