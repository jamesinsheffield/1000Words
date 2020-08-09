: '
Run using:
$ bash dumpPSQL.sh
This will make a backup copy of the current words database.
File created: words.csv
'

psql words <<EOF
\copy (SELECT mark,category,romanian,english FROM words) to 'words.csv' csv header;
EOF
