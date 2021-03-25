wget --recursive --no-parent -nc -A .html.json.gz https://dumps.wikimedia.org/other/contenttranslation/20210319/
gunzip -rfkv dumps.wikimedia.org/other/contenttranslation
python parse.py
