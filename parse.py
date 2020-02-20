import ijson
from lxml import html
import sqlite3
from pathlib import Path
import re


def get_database():
    connection = sqlite3.connect('section-titles.db')
    cursor = connection.cursor()
    # Drop the table if it exists
    cursor.execute('DROP TABLE IF EXISTS titles')
    # Create table
    cursor.execute("""
            CREATE TABLE titles
            (source_language TEXT,
            target_language TEXT,
            source_title TEXT,
            target_title TEXT,
            frequency INTEGER)
        """)
    connection.commit()
    return cursor


def parse_file(filename, db):
    file = open(filename)
    sections = ijson.parse(file)
    index = 0
    section = dict()
    for prefix, event, value in sections:
        if prefix == 'item' and event == 'start_map':
            section = dict()
        elif prefix == 'item.sourceLanguage' and event == 'string':
            section['sourceLanguage'] = value
        elif prefix == 'item.targetLanguage' and event == 'string':
            section['targetLanguage'] = value
        elif prefix == 'item.source.content' and event == 'string':
            match = re.search(r"(</h[2-4])", value)
            if match and match.start() >= 0:
                doc = html.fromstring(value)
                title = ''.join([element.xpath("string()").strip()
                                 for element in doc.cssselect('h2, h3, h4')])
                if title:
                    section['sourceHeader'] = title
        elif prefix == 'item.target.content' and event == 'string':
            match = re.search(r"(</h[2-4])", value)
            if match and match.start() >= 0:
                doc = html.fromstring(value)
                title = ''.join([element.xpath("string()").strip()
                                 for element in doc.cssselect('h2, h3, h4')])
                if title and title != section.get('sourceHeader'):
                    section['targetHeader'] = title

        elif prefix == 'item' and event == 'end_map':
            if 'sourceHeader' in section and 'targetHeader' in section:
                params = (
                    section['sourceLanguage'], section['targetLanguage'],
                    section['sourceHeader'], section['targetHeader'],
                )
                count = db.execute(
                    """
                        SELECT count(*) from titles
                        WHERE source_language=?
                        AND target_language=? AND source_title=?
                        AND target_title=?
                    """, params).fetchone()
                if count[0] == 0:
                    db.execute("""
                        INSERT INTO titles VALUES(?,?,?,?, 1)
                        """, params)
                else:
                    count = count[0]+1
                    db.execute("""
                            UPDATE titles SET frequency=?
                            WHERE source_language=? AND target_language=?
                            AND source_title=? AND target_title=?
                        """, (count, *params))
                index += 1
            if index % 1000 == 0:
                db.connection.commit()

    db.connection.commit()

    print('Inserted %d items from %s' % (index, filename))


def main():
    db = get_database()
    folder = "dumps.wikimedia.org/other/contenttranslation"
    for path in Path(folder).rglob('cx-corpora.*.html.json'):
        parse_file(path.absolute(), db)
    db.connection.close()


if __name__ == '__main__':
    main()
