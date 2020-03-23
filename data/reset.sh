dir=$1
rm $dir/games.txt $dir/players.txt $dir/words.txt
echo -e '{"gid": "abc", "num_words": "5", "t1": "30", "t2": "30", "t3": "30"}' > $dir/games.txt
echo -e '{"gid": "xyz", "num_words": "3", "t1": "30", "t2": "30", "t3": "30"}\n' >> $dir/games.txt
touch $dir/players.txt $dir/words.txt
