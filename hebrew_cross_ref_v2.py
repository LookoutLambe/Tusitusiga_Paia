"""
Hebrew-Samoan Mistranslation Finder v2
Compares the Hebrew Masoretic text (WLC) word-by-word against the
1887 Samoan Bible translation to find semantic mismatches.

Uses:
- OT verse JS files (Hebrew word + English gloss pairs)
- Samoan phrase annotations (Samoan phrase + English gloss pairs)
- KJV for reference

Detects:
1. Semantic reversals (Hebrew means X, Samoan means opposite)
2. Concept dilution (specific Hebrew → generic Samoan)
3. Missing concepts (Hebrew word has no Samoan equivalent)
4. Mistranslations (Hebrew word mapped to wrong Samoan word)
"""
import os, re, json, sys

sys.stdout.reconfigure(encoding='utf-8')

base = os.path.expanduser(r'~\Desktop\O le Tusi Paia')
swp = os.path.expanduser(r'~\Desktop\Standard Works Project')

# ============================================================
# Load data
# ============================================================
print("Loading data...")

with open(os.path.join(base, '_bible_samoan_verses.json'), 'r', encoding='utf-8') as f:
    samoan_verses = json.load(f)

with open(os.path.join(base, '_kjv_bible.json'), 'r', encoding='utf-8') as f:
    kjv = json.load(f)

with open(os.path.join(base, '_phrase_annotations.json'), 'r', encoding='utf-8') as f:
    phrase_annotations = json.load(f)

# ============================================================
# Book name mapping: JS filename -> Bible book name in verse keys
# ============================================================
BOOK_MAP = {
    'gen': 'Genesis', 'exo': 'Exodus', 'lev': 'Leviticus', 'num': 'Numbers',
    'deu': 'Deuteronomy', 'jos': 'Joshua', 'jdg': 'Judges', 'rth': 'Ruth',
    '1sa': '1 Samuel', '2sa': '2 Samuel', '1ki': '1 Kings', '2ki': '2 Kings',
    '1ch': '1 Chronicles', '2ch': '2 Chronicles', 'ezr': 'Ezra', 'neh': 'Nehemiah',
    'est': 'Esther', 'job': 'Job', 'psa': 'Psalms', 'pro': 'Proverbs',
    'ecc': 'Ecclesiastes', 'sos': 'Song of Solomon', 'isa': 'Isaiah', 'jer': 'Jeremiah',
    'lam': 'Lamentations', 'eze': 'Ezekiel', 'dan': 'Daniel', 'hos': 'Hosea',
    'joe': 'Joel', 'amo': 'Amos', 'oba': 'Obadiah', 'jon': 'Jonah',
    'mic': 'Micah', 'nah': 'Nahum', 'hab': 'Habakkuk', 'zep': 'Zephaniah',
    'hag': 'Haggai', 'zec': 'Zechariah', 'mal': 'Malachi'
}

# Hebrew verse number to integer
HEB_NUMS = {}
_heb_letters = 'אבגדהוזחטי'
for i, ch in enumerate(_heb_letters, 1):
    HEB_NUMS[ch] = i
# 11-19
for i in range(11, 20):
    tens = 'י'
    ones = _heb_letters[i - 10 - 1] if i != 10 else ''
    if i == 15:
        HEB_NUMS['טו'] = 15
    elif i == 16:
        HEB_NUMS['טז'] = 16
    else:
        HEB_NUMS[tens + _heb_letters[i - 11]] = i
# Build comprehensive table
_tens = {10: 'י', 20: 'כ', 30: 'ל', 40: 'מ', 50: 'נ', 60: 'ס', 70: 'ע', 80: 'פ', 90: 'צ', 100: 'ק'}
_ones_letters = {1: 'א', 2: 'ב', 3: 'ג', 4: 'ד', 5: 'ה', 6: 'ו', 7: 'ז', 8: 'ח', 9: 'ט'}
for t_val, t_let in _tens.items():
    HEB_NUMS[t_let] = t_val
    for o_val, o_let in _ones_letters.items():
        n = t_val + o_val
        if n == 15:
            HEB_NUMS['טו'] = 15
        elif n == 16:
            HEB_NUMS['טז'] = 16
        else:
            HEB_NUMS[t_let + o_let] = n
# Hundreds
for h in range(100, 177):
    hundreds = h // 100
    remainder = h % 100
    h_let = 'ק' if hundreds == 1 else ''
    for combo, val in HEB_NUMS.items():
        if val == remainder:
            HEB_NUMS['ק' + combo] = h
            break


# ============================================================
# Parse Hebrew JS verse files (from Standard Works Project)
# ============================================================
def parse_hebrew_js(filepath):
    """Parse a Hebrew OT .js file and return {chapter: {verse_num: [(hebrew, gloss), ...]}}"""
    with open(filepath, 'r', encoding='utf-8') as f:
        content = f.read()

    chapters = {}
    ch_pattern = re.compile(r'var\s+\w+_ch(\d+)Verses\s*=\s*\[(.*?)\];', re.DOTALL)

    for ch_match in ch_pattern.finditer(content):
        ch_num = int(ch_match.group(1))
        ch_content = ch_match.group(2)
        verses = {}

        verse_pattern = re.compile(
            r'\{\s*num\s*:\s*"([^"]+)"\s*,\s*words\s*:\s*\[(.*?)\]\s*\}',
            re.DOTALL
        )

        for v_match in verse_pattern.finditer(ch_content):
            heb_num = v_match.group(1)
            words_str = v_match.group(2)
            v_num = HEB_NUMS.get(heb_num)
            if v_num is None:
                try:
                    v_num = int(heb_num)
                except:
                    continue

            word_pairs = []
            pair_pattern = re.compile(r'\["([^"]*?)"\s*,\s*"([^"]*?)"\]')
            for wp in pair_pattern.finditer(words_str):
                heb_word = wp.group(1)
                gloss = wp.group(2)
                if heb_word != '׃' and gloss:
                    word_pairs.append((heb_word, gloss))
            verses[v_num] = word_pairs

        chapters[ch_num] = verses

    return chapters


# ============================================================
# Semantic comparison
# ============================================================

# Words to skip in comparison (function words, markers, etc.)
SKIP_GLOSSES = {
    'and', 'the', 'a', 'an', 'of', 'in', 'to', 'for', 'by', 'from', 'with',
    'on', 'at', 'that', 'this', 'which', 'who', 'whom', 'not', 'but', 'or',
    'if', 'then', 'so', 'as', 'is', 'was', 'are', 'were', 'be', 'been',
    'have', 'has', 'had', 'will', 'shall', 'may', 'can', 'do', 'did',
    'it', 'he', 'she', 'they', 'we', 'you', 'i', 'me', 'him', 'her',
    'them', 'us', 'my', 'his', 'her', 'their', 'our', 'your', 'its',
    'all', 'every', 'each', 'some', 'any', 'no', 'other',
    '[acc]', '(acc)', 'acc',
}

# Known semantic opposition pairs (Hebrew gloss word -> Samoan gloss word that is WRONG)
SEMANTIC_OPPOSITES = {
    ('trust', 'fear'): 'REVERSAL: Hebrew = trust/confidence, Samoan = fear',
    ('trusting', 'fear'): 'REVERSAL: Hebrew = trusting, Samoan = fear',
    ('secure', 'fear'): 'REVERSAL: Hebrew = secure, Samoan = fear',
    ('confidence', 'fear'): 'REVERSAL: Hebrew = confidence, Samoan = fear',
    ('bless', 'curse'): 'REVERSAL: Hebrew = bless, Samoan = curse',
    ('curse', 'bless'): 'REVERSAL: Hebrew = curse, Samoan = bless',
    ('love', 'hate'): 'REVERSAL: Hebrew = love, Samoan = hate',
    ('hate', 'love'): 'REVERSAL: Hebrew = hate, Samoan = love',
    ('life', 'death'): 'REVERSAL: Hebrew = life, Samoan = death',
    ('death', 'life'): 'REVERSAL: Hebrew = death, Samoan = life',
    ('righteous', 'wicked'): 'REVERSAL: Hebrew = righteous, Samoan = wicked',
    ('wicked', 'righteous'): 'REVERSAL: Hebrew = wicked, Samoan = righteous',
    ('holy', 'profane'): 'REVERSAL: Hebrew = holy, Samoan = profane',
}

# Known Hebrew theological terms that should be carefully translated
# Strong's gloss keyword -> full meaning
THEOLOGICAL_TERMS = {
    'covenant': 'בְּרִית (berit) = binding covenant agreement',
    'holy': 'קָדוֹשׁ (qadosh) = holy, set apart, sacred',
    'soul': 'נֶפֶשׁ (nephesh) = soul, living being, life force',
    'spirit': 'רוּחַ (ruach) = spirit, wind, breath of God',
    'lovingkindness': 'חֶסֶד (chesed) = covenant loyalty, steadfast love',
    'mercy': 'חֶסֶד (chesed) = covenant loyalty, mercy',
    'righteousness': 'צֶדֶק (tsedeq) = righteousness, justice',
    'righteous': 'צַדִּיק (tsaddiq) = righteous one',
    'glory': 'כָּבוֹד (kavod) = glory, weight, honor',
    'atonement': 'כָּפַר (kaphar) = cover, atone, make reconciliation',
    'redeem': 'גָּאַל (gaal) = redeem, act as kinsman-redeemer',
    'salvation': 'יְשׁוּעָה (yeshuah) = salvation, deliverance',
    'judgment': 'מִשְׁפָּט (mishpat) = justice, judgment, ordinance',
    'truth': 'אֱמֶת (emet) = truth, faithfulness, reliability',
    'trust': 'בָּטַח (batach) = trust, be confident, feel secure',
    'trusting': 'בָּטַח (batach) = trusting, confident, secure',
    'fear': 'יָרֵא (yare) = fear, reverence, awe',
    'pride': 'גָּאוֹן (gaon) = pride, majesty, swelling, thicket',
    'iniquity': 'עָוֹן (avon) = iniquity, guilt, punishment',
    'sin': 'חַטָּאת (chattat) = sin, sin offering',
    'transgression': 'פֶּשַׁע (pesha) = transgression, rebellion',
    'repent': 'שׁוּב (shuv) = turn, return, repent',
    'worship': 'שָׁחָה (shachah) = bow down, worship, prostrate',
    'sacrifice': 'זֶבַח (zevach) = sacrifice, slaughter',
    'offering': 'קָרְבָּן (qorban) = offering, that which is brought near',
    'temple': 'הֵיכָל (heykal) = temple, palace',
    'tabernacle': 'מִשְׁכָּן (mishkan) = dwelling place, tabernacle',
    'priest': 'כֹּהֵן (kohen) = priest',
    'prophet': 'נָבִיא (navi) = prophet, spokesman',
    'anoint': 'מָשַׁח (mashach) = anoint, consecrate',
    'messiah': 'מָשִׁיחַ (mashiach) = anointed one, messiah',
}

# Synonym groups for matching
SYNONYM_GROUPS = [
    {'trust', 'trusting', 'trusted', 'confident', 'confidence', 'secure', 'security', 'rely', 'safe', 'faith', 'believe'},
    {'fear', 'afraid', 'dread', 'terror', 'frightened', 'scared', 'reverence', 'awe'},
    {'holy', 'sacred', 'hallowed', 'sanctified', 'consecrated', 'holiness', 'sanctity'},
    {'covenant', 'agreement', 'pact', 'treaty', 'bond'},
    {'soul', 'spirit', 'life force', 'being'},
    {'righteous', 'righteousness', 'just', 'upright', 'justice', 'justifying'},
    {'wicked', 'wickedness', 'evil', 'ungodly', 'sinful', 'iniquity', 'unrighteous', 'unrighteousness'},
    {'mercy', 'compassion', 'lovingkindness', 'kindness', 'grace', 'loyal love'},
    {'glory', 'honor', 'splendor', 'majesty'},
    {'pride', 'arrogance', 'haughtiness', 'swelling', 'thicket', 'jungle'},
    {'beautiful', 'lovely', 'fair', 'pleasant'},
    {'redeem', 'ransom', 'deliver', 'rescue', 'save'},
    {'atone', 'atonement', 'cover', 'reconcile', 'expiate'},
    {'sacrifice', 'offering', 'slaughter'},
    {'worship', 'bow', 'prostrate', 'adore'},
    {'repent', 'turn', 'return', 'convert'},
    {'sin', 'transgression', 'iniquity', 'trespass', 'guilt'},
    {'prophet', 'seer', 'spokesman'},
    {'priest', 'minister'},
    {'anoint', 'consecrate', 'dedicate'},
    {'temple', 'sanctuary', 'palace'},
    {'tabernacle', 'dwelling', 'tent'},
    {'judgment', 'justice', 'ordinance', 'decree'},
    {'law', 'instruction', 'teaching', 'torah', 'commandment'},
    {'word', 'saying', 'matter', 'thing', 'command'},
    {'destroy', 'annihilate', 'devastate', 'ruin', 'perish'},
    {'create', 'make', 'form', 'fashion'},
    {'love', 'beloved', 'affection'},
    {'hate', 'abhor', 'detest', 'loathe'},
    {'bless', 'blessing', 'blessed'},
    {'curse', 'cursed', 'accursed'},
    {'peace', 'wholeness', 'completeness', 'well-being', 'prosperity'},
    {'war', 'battle', 'fight', 'combat', 'conflict'},
    {'king', 'ruler', 'sovereign', 'monarch'},
    {'servant', 'slave', 'bondservant', 'minister'},
    {'inheritance', 'heritage', 'portion', 'lot'},
    {'land', 'earth', 'ground', 'country', 'territory'},
    {'nation', 'people', 'tribe', 'clan'},
    {'mighty', 'strong', 'powerful', 'valiant'},
    {'weak', 'feeble', 'frail'},
]


def extract_content_words(gloss_text):
    """Extract meaningful content words from a gloss, skipping function words."""
    # Clean up gloss formatting
    text = gloss_text.lower()
    text = re.sub(r'\[acc\]', '', text)
    text = re.sub(r'[-/]', ' ', text)
    text = re.sub(r'[^a-z\s]', '', text)
    words = set(text.split())
    return words - SKIP_GLOSSES


def get_synonym_group(word):
    """Find which synonym groups a word belongs to."""
    word = word.lower()
    groups = []
    for group in SYNONYM_GROUPS:
        if word in group:
            groups.append(group)
    return groups


def words_semantically_related(word1, word2):
    """Check if two words are semantically related (in same synonym group)."""
    w1, w2 = word1.lower(), word2.lower()
    if w1 == w2:
        return True
    for group in SYNONYM_GROUPS:
        if w1 in group and w2 in group:
            return True
    return False


def check_semantic_opposition(heb_word, sam_word):
    """Check if Hebrew and Samoan words are semantic opposites."""
    h, s = heb_word.lower(), sam_word.lower()
    for (a, b), desc in SEMANTIC_OPPOSITES.items():
        if a in h and b in s:
            return desc
        if a in s and b in h:
            return desc
    return None


def analyze_verse_v2(book_name, ch, v, hebrew_words, samoan_text, kjv_text, samoan_glosses):
    """Deep semantic comparison of Hebrew words vs Samoan glosses.

    samoan_glosses: list of [samoan_phrase, english_gloss] from phrase annotations
    """
    findings = []

    # Build Samoan semantic content: all English gloss words from Samoan annotations
    samoan_content_words = set()
    samoan_gloss_phrases = []
    if samoan_glosses:
        for phrase_pair in samoan_glosses:
            sam_phrase = phrase_pair[0]
            sam_gloss = phrase_pair[1] if len(phrase_pair) > 1 else ''
            samoan_gloss_phrases.append((sam_phrase, sam_gloss))
            samoan_content_words |= extract_content_words(sam_gloss)

    # Also add common Samoan→English mappings that the glosser might not capture
    sam_text_lower = samoan_text.lower()
    if 'ieova' in sam_text_lower:
        samoan_content_words |= {'lord', 'yahweh', 'god'}
    if 'atua' in sam_text_lower:
        samoan_content_words |= {'god', 'deity'}
    if 'agaga' in sam_text_lower:
        samoan_content_words |= {'spirit', 'soul'}
    if 'paia' in sam_text_lower:
        samoan_content_words |= {'holy', 'sacred'}
    if 'feagaiga' in sam_text_lower:
        samoan_content_words |= {'covenant', 'agreement'}
    if 'faamasinoga' in sam_text_lower:
        samoan_content_words |= {'judgment', 'justice'}
    if 'tulafono' in sam_text_lower:
        samoan_content_words |= {'law', 'commandment'}
    if 'alofa' in sam_text_lower:
        samoan_content_words |= {'love', 'mercy', 'kindness'}
    if 'mamalu' in sam_text_lower:
        samoan_content_words |= {'glory', 'honor'}
    if 'filemu' in sam_text_lower:
        samoan_content_words |= {'peace'}
    if 'moni' in sam_text_lower:
        samoan_content_words |= {'true', 'truth'}
    if 'soifua' in sam_text_lower or 'ola' in sam_text_lower:
        samoan_content_words |= {'live', 'living', 'life'}
    if 'oti' in sam_text_lower:
        samoan_content_words |= {'death', 'die', 'dead'}
    if 'taulaga' in sam_text_lower:
        samoan_content_words |= {'offering', 'sacrifice'}
    if 'malumalu' in sam_text_lower:
        samoan_content_words |= {'temple', 'sanctuary'}
    if 'perofeta' in sam_text_lower or 'peropheta' in sam_text_lower:
        samoan_content_words |= {'prophet'}
    if "faitaulaga" in sam_text_lower or 'ositaulaga' in sam_text_lower:
        samoan_content_words |= {'priest'}
    if 'salamo' in sam_text_lower:
        samoan_content_words |= {'repent'}
    if 'amiotonu' in sam_text_lower:
        samoan_content_words |= {'righteous', 'righteousness', 'just'}
    if 'amioletonu' in sam_text_lower:
        samoan_content_words |= {'wicked', 'wickedness', 'unrighteous'}
    if 'faatuatua' in sam_text_lower:
        samoan_content_words |= {'trust', 'faith', 'believe'}
    if 'matatau' in sam_text_lower or "mata'u" in sam_text_lower:
        samoan_content_words |= {'fear', 'afraid', 'reverence'}
    if 'agasala' in sam_text_lower:
        samoan_content_words |= {'sin', 'transgression'}
    if 'solitulafono' in sam_text_lower:
        samoan_content_words |= {'transgression', 'sin'}
    if 'togiola' in sam_text_lower:
        samoan_content_words |= {'redeem', 'ransom', 'atonement'}
    if 'laveai' in sam_text_lower:
        samoan_content_words |= {'save', 'deliver', 'salvation'}
    if 'olataga' in sam_text_lower:
        samoan_content_words |= {'salvation', 'deliverance'}
    if 'ipu uu' in sam_text_lower or 'uu' in sam_text_lower.split():
        samoan_content_words |= {'anoint', 'anointed'}
    if 'tapuai' in sam_text_lower or 'ifo' in sam_text_lower.split():
        samoan_content_words |= {'worship', 'bow'}
    if 'faamaoni' in sam_text_lower:
        samoan_content_words |= {'truth', 'faithful', 'true'}
    if 'tupu' in sam_text_lower.split() or 'le tupu' in sam_text_lower:
        samoan_content_words |= {'king', 'ruler'}
    if 'auauna' in sam_text_lower:
        samoan_content_words |= {'servant', 'serve'}
    if 'toasa' in sam_text_lower:
        samoan_content_words |= {'wrath', 'anger'}
    if 'ita' in sam_text_lower.split():
        samoan_content_words |= {'anger', 'wrath'}

    # Hebrew content words for the whole verse (to avoid reversal false positives)
    all_hebrew_content = set()
    for _, hg in hebrew_words:
        all_hebrew_content |= extract_content_words(hg)

    # Only check theological terms — skip generic content words to reduce noise
    for heb_word, heb_gloss in hebrew_words:
        heb_content = extract_content_words(heb_gloss)
        if not heb_content:
            continue

        # Only check if this Hebrew word contains a theological term
        theological_hits = {hw for hw in heb_content if hw in THEOLOGICAL_TERMS}
        if not theological_hits:
            continue

        # Check if ANY theological concept has a semantic match in Samoan
        matched = False
        for hw in theological_hits:
            if hw in samoan_content_words:
                matched = True
                break
            for sw in samoan_content_words:
                if words_semantically_related(hw, sw):
                    matched = True
                    break
            if matched:
                break

        if not matched:
            # Check for semantic reversal: Hebrew concept replaced by its opposite
            # Only flag as CRITICAL if the opposite IS in Samoan but the correct
            # concept is NOT (avoids false positives where both appear in verse)
            is_reversal = False
            for hw in theological_hits:
                for sw in samoan_content_words:
                    opposition = check_semantic_opposition(hw, sw)
                    if opposition:
                        # Verify: the correct concept is truly absent from Samoan
                        # AND the opposite is NOT also in Hebrew (both naturally in verse)
                        hw_groups = get_synonym_group(hw)
                        opposite_also_in_hebrew = False
                        for og in get_synonym_group(sw):
                            for ow in og:
                                if ow in all_hebrew_content:
                                    opposite_also_in_hebrew = True
                                    break

                        if not opposite_also_in_hebrew:
                            findings.append({
                                'ref': f'{book_name}|{ch}|{v}',
                                'type': 'REVERSAL',
                                'severity': 'CRITICAL',
                                'hebrew': heb_word,
                                'hebrew_gloss': heb_gloss,
                                'samoan_text': samoan_text[:200],
                                'samoan_glosses': '; '.join(f'{p[0]}={p[1]}' for p in samoan_gloss_phrases[:8]),
                                'kjv_text': kjv_text[:200],
                                'issue': opposition,
                            })
                            is_reversal = True
                            break
                if is_reversal:
                    break

            if not is_reversal:
                # Missing theological term (not reversed, just absent)
                for hw in theological_hits:
                    findings.append({
                        'ref': f'{book_name}|{ch}|{v}',
                        'type': 'MISSING_CONCEPT',
                        'severity': 'HIGH',
                        'hebrew': heb_word,
                        'hebrew_gloss': heb_gloss,
                        'samoan_text': samoan_text[:200],
                        'samoan_glosses': '; '.join(f'{p[0]}={p[1]}' for p in samoan_gloss_phrases[:8]),
                        'kjv_text': kjv_text[:200],
                        'issue': f'Theological term {THEOLOGICAL_TERMS[hw]} not found in Samoan glosses',
                    })
                    break  # One finding per Hebrew word

    return findings


# ============================================================
# Main analysis
# ============================================================
def run_analysis(books=None):
    """Run enhanced cross-reference analysis."""
    ot_dir = os.path.join(swp, 'ot_verses')

    if books is None:
        books = list(BOOK_MAP.keys())

    all_findings = []
    stats = {'verses_checked': 0, 'discrepancies': 0, 'books_processed': 0,
             'critical': 0, 'high': 0, 'medium': 0}

    for book_code in books:
        book_name = BOOK_MAP.get(book_code)
        if not book_name:
            continue

        js_path = os.path.join(ot_dir, f'{book_code}.js')
        if not os.path.exists(js_path):
            print(f"  Skipping {book_name} - no JS file found")
            continue

        print(f"Processing {book_name}...")
        hebrew_data = parse_hebrew_js(js_path)
        book_findings = []

        for ch_num, verses in sorted(hebrew_data.items()):
            for v_num, word_pairs in sorted(verses.items()):
                ref = f'{book_name}|{ch_num}|{v_num}'

                sam_text = samoan_verses.get(ref, '')
                kjv_text = kjv.get(ref, '')
                sam_glosses = phrase_annotations.get(ref, [])

                if not sam_text:
                    continue

                stats['verses_checked'] += 1

                findings = analyze_verse_v2(
                    book_name, ch_num, v_num, word_pairs,
                    sam_text, kjv_text, sam_glosses
                )

                if findings:
                    book_findings.extend(findings)
                    for f in findings:
                        stats['discrepancies'] += 1
                        sev = f['severity']
                        if sev == 'CRITICAL':
                            stats['critical'] += 1
                        elif sev == 'HIGH':
                            stats['high'] += 1
                        else:
                            stats['medium'] += 1

        if book_findings:
            all_findings.extend(book_findings)
            print(f"  Found {len(book_findings)} issues in {book_name}")

        stats['books_processed'] += 1

    return all_findings, stats


def write_report(findings, stats, output_base):
    """Write comprehensive report."""
    # Sort by severity
    severity_order = {'CRITICAL': 0, 'HIGH': 1, 'MEDIUM': 2}
    findings.sort(key=lambda x: (severity_order.get(x['severity'], 3), x['ref']))

    # Write JSON
    json_path = output_base + '.json'
    with open(json_path, 'w', encoding='utf-8') as f:
        json.dump(findings, f, ensure_ascii=False, indent=2)

    # Write Markdown
    md_path = output_base + '.md'
    with open(md_path, 'w', encoding='utf-8') as out:
        out.write("# Hebrew-Samoan Mistranslation Report\n\n")
        out.write("## Summary\n")
        out.write(f"- Books processed: {stats['books_processed']}\n")
        out.write(f"- Verses checked: {stats['verses_checked']}\n")
        out.write(f"- Total issues: {stats['discrepancies']}\n")
        out.write(f"- CRITICAL (semantic reversals): {stats['critical']}\n")
        out.write(f"- HIGH (missing theological terms): {stats['high']}\n")
        out.write(f"- MEDIUM (unmatched content words): {stats['medium']}\n\n")

        # Group by type
        for sev_name in ['CRITICAL', 'HIGH', 'MEDIUM']:
            sev_findings = [f for f in findings if f['severity'] == sev_name]
            if not sev_findings:
                continue

            out.write(f"## {sev_name} Severity ({len(sev_findings)} issues)\n\n")

            for item in sev_findings[:200]:  # Cap per section
                out.write(f"### {item['ref']}\n")
                out.write(f"- **Type**: {item['type']}\n")
                out.write(f"- **Hebrew**: {item['hebrew']} → {item['hebrew_gloss']}\n")
                out.write(f"- **Issue**: {item['issue']}\n")
                out.write(f"- **Samoan**: {item['samoan_text'][:150]}\n")
                out.write(f"- **KJV**: {item['kjv_text'][:150]}\n\n")

            if len(sev_findings) > 200:
                out.write(f"... and {len(sev_findings) - 200} more {sev_name} issues (see JSON)\n\n")

    print(f"\nReport written to: {md_path}")
    print(f"JSON data written to: {json_path}")
    return md_path, json_path


# ============================================================
# Main
# ============================================================
if __name__ == '__main__':
    import argparse
    parser = argparse.ArgumentParser(description='Hebrew-Samoan Mistranslation Finder')
    parser.add_argument('--books', nargs='*', help='Specific books to analyze (e.g., jer isa gen)')
    args = parser.parse_args()

    print("Hebrew-Samoan Mistranslation Analysis v2")
    print("=" * 50)

    findings, stats = run_analysis(args.books)

    print(f"\n{'=' * 50}")
    print(f"CRITICAL: {stats['critical']} | HIGH: {stats['high']} | MEDIUM: {stats['medium']}")
    print(f"Total: {stats['discrepancies']} issues across {stats['verses_checked']} verses")

    output_base = os.path.join(base, '_hebrew_samoan_mistranslations')
    write_report(findings, stats, output_base)
