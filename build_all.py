"""
Master build script: generates all verse JS data files with word-level Samoan-English glosses,
plus the english_verses.js file for dual-mode display.
"""
import os, re, json, html.parser, sys

base = os.path.expanduser(r'~\Desktop\O le Tusi Paia')
verses_dir = os.path.join(base, 'verses')
os.makedirs(verses_dir, exist_ok=True)

# ============================================================
# Load dictionary
# ============================================================
print("Loading dictionary...")
with open(os.path.join(base, 'samoan_dictionary.json'), 'r', encoding='utf-8') as f:
    dictionary = json.load(f)
print(f"  {len(dictionary)} entries loaded")

# ============================================================
# Load Samoan verses
# ============================================================
print("Loading Samoan verses...")
with open(os.path.join(base, '_all_samoan_verses.json'), 'r', encoding='utf-8') as f:
    samoan_verses = json.load(f)
print(f"  {len(samoan_verses)} verses loaded")

# ============================================================
# Verse Parser for English EPUB XHTML
# ============================================================
class VerseParser(html.parser.HTMLParser):
    def __init__(self):
        super().__init__()
        self.verses = []
        self.current_verse_num = None
        self.current_text = []
        self.in_verse = False
        self.in_verse_num = False
        self.skip_depth = 0

    def handle_starttag(self, tag, attrs):
        attrs_dict = dict(attrs)
        cls = attrs_dict.get('class', '')
        if tag == 'footer' or cls == 'marker':
            self.skip_depth += 1
            return
        if self.skip_depth > 0:
            self.skip_depth += 1
            return
        if 'verse' in cls.split() and tag == 'p':
            self.in_verse = True
            if self.current_verse_num is not None:
                self.verses.append((self.current_verse_num, ' '.join(self.current_text).strip()))
            self.current_verse_num = None
            self.current_text = []
        if 'verse-number' in cls:
            self.in_verse_num = True

    def handle_endtag(self, tag):
        if self.skip_depth > 0:
            self.skip_depth -= 1
            return
        if self.in_verse_num:
            self.in_verse_num = False

    def handle_data(self, data):
        if self.skip_depth > 0:
            return
        if self.in_verse_num:
            num = data.strip()
            if num:
                try:
                    self.current_verse_num = int(num)
                except:
                    pass
        elif self.in_verse:
            self.current_text.append(data)

    def finish(self):
        if self.current_verse_num is not None:
            self.verses.append((self.current_verse_num, ' '.join(self.current_text).strip()))
        cleaned = []
        for num, text in self.verses:
            text = re.sub(r'\s+', ' ', text).strip()
            if text:
                cleaned.append((num, text))
        return cleaned


def parse_xhtml(filepath):
    with open(filepath, 'r', encoding='utf-8') as f:
        content = f.read()
    parser = VerseParser()
    parser.feed(content)
    return parser.finish()


# ============================================================
# Extract English verses from existing Hebrew BOM data
# ============================================================
print("Loading English BOM verses from Hebrew BOM project...")
english_verses = {}

# Parse the official_verses.js from Hebrew BOM
heb_bom = os.path.expanduser(r'~\Desktop\Hebrew BOM')
ov_path = os.path.join(heb_bom, 'official_verses.js')
if os.path.exists(ov_path):
    with open(ov_path, 'r', encoding='utf-8') as f:
        content = f.read()
    # Extract the JSON array from the JS file
    match = re.search(r'window\._officialVersesData\s*=\s*(\[.*?\]);', content, re.DOTALL)
    if match:
        data = json.loads(match.group(1))
        for v in data:
            key = f"{v['book']}|{v['chapter']}|{v['verse']}"
            english_verses[key] = v['english']
        print(f"  {len(english_verses)} English BOM verses loaded")
    else:
        print("  WARNING: Could not parse official_verses.js")
else:
    print(f"  WARNING: {ov_path} not found")

# ============================================================
# Extract English D&C verses
# ============================================================
print("Extracting English D&C verses...")
eng_dc_dir = os.path.join(base, '_eng_dc_extract')
dc_count = 0
for sec in range(1, 139):
    filepath = os.path.join(eng_dc_dir, 'OEBPS', 'dc-testament', 'dc', f'{sec}.xhtml')
    if not os.path.exists(filepath):
        continue
    verses = parse_xhtml(filepath)
    for vnum, vtext in verses:
        key = f"D&C|{sec}|{vnum}"
        english_verses[key] = vtext
        dc_count += 1

# Official Declarations
od_path = os.path.join(eng_dc_dir, 'OEBPS', 'dc-testament', 'od.xhtml')
if os.path.exists(od_path):
    verses = parse_xhtml(od_path)
    for vnum, vtext in verses:
        key = f"D&C OD|1|{vnum}"
        english_verses[key] = vtext
        dc_count += 1

print(f"  {dc_count} English D&C verses extracted")

# ============================================================
# Extract English PGP verses
# ============================================================
print("Extracting English PGP verses...")
eng_pgp_dir = os.path.join(base, '_eng_pgp_extract')
PGP_BOOKS = [
    ('moses', 'Moses', 8),
    ('abr', 'Abraham', 5),
    ('js-m', 'JS-Matthew', 1),
    ('js-h', 'JS-History', 1),
    ('a-of-f', 'Articles of Faith', 1),
]
pgp_count = 0
for pgp_dir_name, book_name, num_chapters in PGP_BOOKS:
    for ch in range(1, num_chapters + 1):
        filepath = os.path.join(eng_pgp_dir, 'OEBPS', 'pgp', pgp_dir_name, f'{ch}.xhtml')
        if not os.path.exists(filepath):
            # Try the dc_extract as fallback (PGP might be bundled with D&C)
            filepath = os.path.join(eng_dc_dir, 'OEBPS', 'pgp', pgp_dir_name, f'{ch}.xhtml')
            if not os.path.exists(filepath):
                print(f"  WARNING: Missing English PGP {pgp_dir_name}/{ch}.xhtml")
                continue
        verses = parse_xhtml(filepath)
        for vnum, vtext in verses:
            key = f"{book_name}|{ch}|{vnum}"
            english_verses[key] = vtext
            pgp_count += 1

print(f"  {pgp_count} English PGP verses extracted")

# ============================================================
# Load Samoan Bible verses (from extract_bible.py output)
# ============================================================
bible_sam_path = os.path.join(base, '_bible_samoan_verses.json')
if os.path.exists(bible_sam_path):
    print("Loading Samoan Bible verses...")
    with open(bible_sam_path, 'r', encoding='utf-8') as f:
        bible_sam = json.load(f)
    # Merge into samoan_verses
    for k, v in bible_sam.items():
        samoan_verses[k] = v
    print(f"  {len(bible_sam)} Samoan Bible verses loaded")

# ============================================================
# Load English KJV Bible verses
# ============================================================
kjv_path = os.path.join(base, '_kjv_bible.json')
if os.path.exists(kjv_path):
    print("Loading English KJV verses...")
    with open(kjv_path, 'r', encoding='utf-8') as f:
        kjv = json.load(f)
    for k, v in kjv.items():
        english_verses[k] = v
    print(f"  {len(kjv)} English KJV verses loaded")

# ============================================================
# Save english_verses.js
# ============================================================
print("Writing english_verses.js...")
eng_js = "window._englishVersesData = " + json.dumps(english_verses, ensure_ascii=False) + ";\n"
with open(os.path.join(base, 'english_verses.js'), 'w', encoding='utf-8') as f:
    f.write(eng_js)
print(f"  {len(english_verses)} total English verses saved")

# ============================================================
# Word glossing function
# ============================================================
def clean_gloss(gloss):
    """Strip parenthetical info and verbose dictionary phrasing from a gloss."""
    if not gloss:
        return ""
    g = gloss
    # Remove parenthetical content: "by (a person or animate object)" -> "by"
    stripped = re.sub(r'\s*\([^)]*\)', '', g).strip(' ,;.')
    # Only use stripped version if it still has content
    if stripped:
        g = stripped
    else:
        # Entire gloss was parenthetical — keep it but remove parens
        g = re.sub(r'[()]', '', g).strip(' ,;.')
    # Clean up "alternative form of X" -> just the word X
    g = re.sub(r'^alternative form of\s+', '', g, flags=re.IGNORECASE)
    # Clean up "plural of X" -> "pl. X"
    g = re.sub(r'^the plural of\s+', 'pl. ', g, flags=re.IGNORECASE)
    g = re.sub(r'^plural of\s+', 'pl. ', g, flags=re.IGNORECASE)
    # Strip trailing punctuation and whitespace
    g = g.strip(' ,;.')
    return g


def gloss_word(word):
    """Look up a Samoan word in the dictionary, return English gloss."""
    if not word:
        return ""
    # Try exact match (lowercase)
    w = word.lower()
    if w in dictionary:
        return clean_gloss(dictionary[w])
    # Try without glottal stop variants
    w2 = w.replace('\u02bb', "'").replace('\u02bc', "'")
    if w2 in dictionary:
        return clean_gloss(dictionary[w2])
    w3 = w.replace('\u02bb', '').replace('\u02bc', '').replace("'", '')
    if w3 in dictionary:
        return clean_gloss(dictionary[w3])
    # Try without common prefixes (faa-, fa'a-)
    for prefix in ['faa', "fa'a", 'fa\u02bba']:
        if w.startswith(prefix) and len(w) > len(prefix) + 2:
            root = w[len(prefix):]
            if root in dictionary:
                return clean_gloss(f"(caus.) {dictionary[root]}")
    return ""


def tokenize_verse(text):
    """Split verse text into word tokens, preserving punctuation attached to words."""
    # Split on whitespace
    raw_tokens = text.split()
    words = []
    for token in raw_tokens:
        # Strip leading/trailing punctuation but keep the word
        # Keep glottal stops and hyphens as part of the word
        word = token.strip('.,;:!?"\u201c\u201d\u201e\u2018\u2019()')
        if word:
            words.append((token, word))  # (display_form, lookup_form)
    return words


# ============================================================
# Generate verse JS files
# ============================================================
print("\nGenerating verse JS data files...")

# Book of Mormon books
BOM_BOOKS = [
    ('1nephi', '1 Nephi', 'ch', 22),
    ('2nephi', '2 Nephi', '2n-ch', 33),
    ('jacob', 'Jacob', 'jc-ch', 7),
    ('enos', 'Enos', 'en-ch', 1),
    ('jarom', 'Jarom', 'jr-ch', 1),
    ('omni', 'Omni', 'om-ch', 1),
    ('words_of_mormon', 'Words of Mormon', 'wm-ch', 1),
    ('mosiah', 'Mosiah', 'mo-ch', 29),
    ('alma', 'Alma', 'al-ch', 63),
    ('helaman', 'Helaman', 'he-ch', 16),
    ('3nephi', '3 Nephi', '3n-ch', 30),
    ('4nephi', '4 Nephi', '4n-ch', 1),
    ('mormon', 'Mormon', 'mm-ch', 9),
    ('ether', 'Ether', 'et-ch', 15),
    ('moroni', 'Moroni', 'mr-ch', 10),
]

# D&C
DC_BOOK = ('dc', 'D&C', 'dc-sec', 138)

# PGP books
PGP_JS_BOOKS = [
    ('moses', 'Moses', 'ms-ch', 8),
    ('abraham', 'Abraham', 'ab-ch', 5),
    ('js_matthew', 'JS-Matthew', 'jm-ch', 1),
    ('js_history', 'JS-History', 'jh-ch', 1),
    ('articles_of_faith', 'Articles of Faith', 'af-ch', 1),
]

# Old Testament books (js_filename, verse_key_book, html_prefix, num_chapters)
OT_BOOKS = [
    ('genesis', 'Genesis', 'gen-ch', 50),
    ('exodus', 'Exodus', 'exo-ch', 40),
    ('leviticus', 'Leviticus', 'lev-ch', 27),
    ('numbers', 'Numbers', 'num-ch', 36),
    ('deuteronomy', 'Deuteronomy', 'deu-ch', 34),
    ('joshua', 'Joshua', 'jos-ch', 24),
    ('judges', 'Judges', 'jdg-ch', 21),
    ('ruth', 'Ruth', 'rut-ch', 4),
    ('1samuel', '1 Samuel', '1sa-ch', 31),
    ('2samuel', '2 Samuel', '2sa-ch', 24),
    ('1kings', '1 Kings', '1ki-ch', 22),
    ('2kings', '2 Kings', '2ki-ch', 25),
    ('1chronicles', '1 Chronicles', '1ch-ch', 29),
    ('2chronicles', '2 Chronicles', '2ch-ch', 36),
    ('ezra', 'Ezra', 'ezr-ch', 10),
    ('nehemiah', 'Nehemiah', 'neh-ch', 13),
    ('esther', 'Esther', 'est-ch', 10),
    ('job', 'Job', 'job-ch', 42),
    ('psalms', 'Psalms', 'psa-ch', 150),
    ('proverbs', 'Proverbs', 'pro-ch', 31),
    ('ecclesiastes', 'Ecclesiastes', 'ecc-ch', 12),
    ('songofsolomon', 'Song of Solomon', 'sng-ch', 8),
    ('isaiah', 'Isaiah', 'isa-ch', 66),
    ('jeremiah', 'Jeremiah', 'jer-ch', 52),
    ('lamentations', 'Lamentations', 'lam-ch', 5),
    ('ezekiel', 'Ezekiel', 'ezk-ch', 48),
    ('daniel', 'Daniel', 'dan-ch', 12),
    ('hosea', 'Hosea', 'hos-ch', 14),
    ('joel', 'Joel', 'jol-ch', 3),
    ('amos', 'Amos', 'amo-ch', 9),
    ('obadiah', 'Obadiah', 'oba-ch', 1),
    ('jonah', 'Jonah', 'jon-ch', 4),
    ('micah', 'Micah', 'mic-ch', 7),
    ('nahum', 'Nahum', 'nah-ch', 3),
    ('habakkuk', 'Habakkuk', 'hab-ch', 3),
    ('zephaniah', 'Zephaniah', 'zep-ch', 3),
    ('haggai', 'Haggai', 'hag-ch', 2),
    ('zechariah', 'Zechariah', 'zec-ch', 14),
    ('malachi', 'Malachi', 'mal-ch', 4),
]

# New Testament books
NT_BOOKS = [
    ('matthew', 'Matthew', 'mat-ch', 28),
    ('mark', 'Mark', 'mrk-ch', 16),
    ('luke', 'Luke', 'luk-ch', 24),
    ('john', 'John', 'jhn-ch', 21),
    ('acts', 'Acts', 'act-ch', 28),
    ('romans', 'Romans', 'rom-ch', 16),
    ('1corinthians', '1 Corinthians', '1co-ch', 16),
    ('2corinthians', '2 Corinthians', '2co-ch', 13),
    ('galatians', 'Galatians', 'gal-ch', 6),
    ('ephesians', 'Ephesians', 'eph-ch', 6),
    ('philippians', 'Philippians', 'php-ch', 4),
    ('colossians', 'Colossians', 'col-ch', 4),
    ('1thessalonians', '1 Thessalonians', '1th-ch', 5),
    ('2thessalonians', '2 Thessalonians', '2th-ch', 3),
    ('1timothy', '1 Timothy', '1ti-ch', 6),
    ('2timothy', '2 Timothy', '2ti-ch', 4),
    ('titus', 'Titus', 'tit-ch', 3),
    ('philemon', 'Philemon', 'phm-ch', 1),
    ('hebrews', 'Hebrews', 'heb-ch', 13),
    ('james', 'James', 'jas-ch', 5),
    ('1peter', '1 Peter', '1pe-ch', 5),
    ('2peter', '2 Peter', '2pe-ch', 3),
    ('1john', '1 John', '1jn-ch', 5),
    ('2john', '2 John', '2jn-ch', 1),
    ('3john', '3 John', '3jn-ch', 1),
    ('jude', 'Jude', 'jud-ch', 1),
    ('revelation', 'Revelation', 'rev-ch', 22),
]

ALL_BOOKS = OT_BOOKS + NT_BOOKS + BOM_BOOKS + [DC_BOOK] + PGP_JS_BOOKS

# BOM book names — Samoan only, no English glosses
BOM_BOOK_NAMES = set(b[1] for b in BOM_BOOKS)

# ============================================================
# Load phrase annotations (interlinear by phrase blocks)
# ============================================================
phrase_path = os.path.join(base, '_phrase_annotations.json')
phrase_annotations = {}
if os.path.exists(phrase_path):
    with open(phrase_path, 'r', encoding='utf-8') as f:
        phrase_annotations = json.load(f)
    print(f"Loaded {len(phrase_annotations)} phrase annotations")

total_words = 0
total_glossed = 0
total_phrases = 0
unknown_words = set()

for js_name, book_name, prefix, num_chapters in ALL_BOOKS:
    skip_gloss = book_name in BOM_BOOK_NAMES
    js_lines = []
    js_lines.append(f"(function() {{")

    for ch in range(1, num_chapters + 1):
        # Collect verses for this chapter
        chapter_verses = []
        vnum = 1
        while True:
            key = f"{book_name}|{ch}|{vnum}"
            has_samoan = key in samoan_verses
            has_english = key in english_verses
            if not has_samoan and not has_english:
                break

            # Check for phrase annotations first
            if key in phrase_annotations:
                words_arr = phrase_annotations[key]
                total_phrases += len(words_arr)
                total_words += len(words_arr)
            else:
                text = samoan_verses.get(key, '')
                # If no Samoan text but English exists, use English as placeholder
                if not text and has_english:
                    text = english_verses[key]
                tokens = tokenize_verse(text)
                words_arr = []
                for display, lookup in tokens:
                    words_arr.append([display, ""])
                    total_words += 1
            chapter_verses.append({"num": vnum, "words": words_arr})
            vnum += 1

        if not chapter_verses:
            continue

        # Write chapter data
        var_name = f"{prefix.replace('-', '_')}_{ch}_Verses"
        container_id = f"{prefix}{ch}-verses"

        # Serialize manually for readability
        js_lines.append(f"var {var_name} = [")
        for v in chapter_verses:
            words_json = json.dumps(v["words"], ensure_ascii=False)
            js_lines.append(f'  {{num:{v["num"]},words:{words_json}}},')
        js_lines.append(f"];")
        js_lines.append(f"renderVerseSet({var_name}, '{container_id}');")
        js_lines.append("")

    js_lines.append(f"}})();")

    out_path = os.path.join(verses_dir, f'{js_name}.js')
    with open(out_path, 'w', encoding='utf-8') as f:
        f.write('\n'.join(js_lines))

gloss_pct = (total_glossed / total_words * 100) if total_words else 0
print(f"  Total word/phrase units: {total_words:,}")
print(f"  Phrase-annotated units: {total_phrases:,}")
print(f"  Unknown unique words: {len(unknown_words):,}")

# Save unknown words for review
unknown_sorted = sorted(unknown_words)
with open(os.path.join(base, '_unknown_words.txt'), 'w', encoding='utf-8') as f:
    for w in unknown_sorted:
        f.write(w + '\n')
print(f"  Unknown words saved to _unknown_words.txt")

# ============================================================
# Summary
# ============================================================
print(f"\n=== BUILD COMPLETE ===")
print(f"Verse JS files: {len(ALL_BOOKS)} books in {verses_dir}")
print(f"English verses: {len(english_verses)} in english_verses.js")
print(f"Dictionary coverage: {gloss_pct:.1f}%")
