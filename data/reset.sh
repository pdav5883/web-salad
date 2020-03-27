dir=$1
rm $dir/games.txt $dir/players.txt $dir/words.txt
echo -e '{"abc": {"num_words": "5", "t1": "5", "t2": "5", "t3": "5", "started": false, "complete": false},' > $dir/games.txt
echo -e '"xyz": {"num_words": "3", "t1": "5", "t2": "5", "t3": "5", "started": false, "complete": false}}\n' >> $dir/games.txt
echo "{}" > $dir/players.txt
echo "{}" > $dir/words.txt
