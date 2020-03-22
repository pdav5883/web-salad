dir=$1
rm $dir/games.txt $dir/players.txt $dir/words.txt
echo -e "abc\nxyz" > $dir/games.txt
touch $dir/players.txt $dir/words.txt
