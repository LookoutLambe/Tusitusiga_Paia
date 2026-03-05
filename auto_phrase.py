"""
Automated Samoan phrase chunker and English gloss generator.
Groups Samoan words into grammatical phrases and generates English glosses
from dictionary lookups + grammatical pattern translations.
"""
import os, re, json, sys

base = os.path.expanduser(r'~\Desktop\O le Tusi Paia')

# ============================================================
# Load resources
# ============================================================
with open(os.path.join(base, 'samoan_dictionary.json'), 'r', encoding='utf-8') as f:
    dictionary = json.load(f)

with open(os.path.join(base, '_all_samoan_verses.json'), 'r', encoding='utf-8') as f:
    samoan_verses = json.load(f)

with open(os.path.join(base, '_kjv_bible.json'), 'r', encoding='utf-8') as f:
    kjv = json.load(f)

# Load existing English verses (BOM/D&C/PGP)
eng_verses_path = os.path.join(base, 'english_verses.js')
english_verses = {}
if os.path.exists(eng_verses_path):
    with open(eng_verses_path, 'r', encoding='utf-8') as f:
        content = f.read()
    match = re.search(r'window\._englishVersesData\s*=\s*(\{.*?\});\s*$', content, re.DOTALL)
    if match:
        english_verses = json.loads(match.group(1))

# Merge KJV into english_verses
for k, v in kjv.items():
    english_verses[k] = v

# ============================================================
# Samoan function word glossary
# ============================================================
FUNC_WORDS = {
    # Articles
    'le': 'the',
    'se': 'a',
    'ni': 'some',
    # Prepositions / particles
    'i': 'in',
    'e': 'by',
    'ma': 'and',
    'mo': 'for',
    'mai': 'from',
    'nai': 'from',
    'ia': 'to',
    'ai': 'thereof',
    # Tense/aspect markers
    'na': '(past)',
    'ua': '(perf)',
    'sa': '(past)',
    "ole'a": '(fut)',
    "ole\u02bba": '(fut)',
    "o le a": '(fut)',
    "olo'o": '(prog)',
    "olo\u02bbo": '(prog)',
    'o': '',
    'ona': 'then/his/her',
    'lea': '',
    # Negation
    "le\u0304": 'not',
    # Directional particles (absorbed into verb, suppressed in gloss)
    'atu': '(dir)',
    'ifo': '(dir)',
    'ane': '(dir)',
    'maia': '(dir)',
    # Common words
    'foi': 'also',
    'lava': 'indeed',
    'uma': 'all',
    'atoa': 'together with',
    'a': 'but',
    'ae': 'but',
    'pe': 'or',
    'ina': 'let',
    'tatou': 'us',
    'te': '',
    'lo': '',
    'la': '',
    'latou': 'they/them',
    'lona': 'his/her',
    'lana': 'his/her',
    'ana': 'his/her',
    'lau': 'your',
    'laua': 'they/them (two)',
    "la'ua": 'they/them (two)',
    "la\u02bbua": 'they/them (two)',
    "ta'ua": 'us (two, incl)',
    "ta\u02bbua": 'us (two, incl)',
    "ma'ua": 'us (two, excl)',
    "ma\u02bbua": 'us (two, excl)',
    'oulua': 'you (two)',
    'outou': 'you (all)',
    'matou': 'we/us (excl)',
    'tatou': 'we/us (incl)',
    'taitasi': 'each',
    'faauta': 'behold',
    'faapea': 'thus/so',
    'nei': 'this/these',
    'isi': 'other/some',
    'lenei': 'this',
    'lena': 'that',
    'lela': 'that yonder',
    'iinei': 'here',
    'iina': 'there',
    # Numbers
    'tasi': 'one',
    'lua': 'two',
    'tolu': 'three',
    'fa': 'four',
    'lima': 'five',
    'ono': 'six',
    'fitu': 'seven',
    'valu': 'eight',
    'iva': 'nine',
    'sefulu': 'ten',
    'selau': 'hundred',
    'afe': 'thousand',
}

# ============================================================
# Extended Samoan vocabulary for scripture
# ============================================================
EXTENDED_VOCAB = {
    # Creation / nature
    'atua': 'God',
    'lagi': 'heaven',
    'lalolagi': 'earth',
    'eleele': 'earth',
    'laueleele': 'ground',
    'sami': 'sea',
    'vai': 'water',
    'moana': 'deep',
    'vanimonimo': 'firmament',
    'pouliuli': 'darkness',
    'malamalama': 'knowledge/light',
    'ao': 'day',
    'po': 'night',
    'aso': 'day',
    'afiafi': 'evening',
    'taeao': 'morning',
    'masina': 'moon',
    'la': 'sun',
    'fetu': 'star',
    'amataga': 'beginning',
    'fogaeleele': 'face of the earth',
    'fog\u0101eleele': 'face of the earth',
    'fog\u0101tai': 'face of the waters',
    'mauga': 'mountain',
    'vao': 'vegetation',
    'laau': 'tree',
    'fua': 'fruit',
    'fatu': 'seed',
    'timu': 'rain',
    'matagi': 'wind',
    'afi': 'fire',
    'maa': 'stone',
    # Override bad dictionary entries
    'afu': 'herb',
    "mu'a": 'grass',
    'mua': 'grass',

    # Creation-specific vocabulary
    'tofu': 'was without form',
    'agafoi': 'moved',
    'suasami': 'waters',
    'faapotopotoga': 'gathering',
    'potopotoga': 'gathering',
    'uiga': 'kind',
    'iai': 'there',
    'meaola': 'living creature',
    'foliga': 'likeness',
    'faatusa': 'image',
    'faailoga': 'sign',
    'tau': 'season',
    'tausaga': 'year',
    'va': 'space',
    'nimonimo': 'firmament',
    'vaefa': 'four-footed',
    'fanua': 'land',
    'lauolaola': 'green',
    'soona': 'without form',

    # People / body
    'alo': 'Son',
    'tagata': 'man',
    'tane': 'man',
    'fafine': 'woman',
    'tama': 'child',
    'atalii': 'son',
    'afafine': 'daughter',
    'tamaitiiti': 'child',
    'tamaitai': 'woman',
    'tupuga': 'descendant',
    'aiga': 'family',
    'nuu': 'nation',
    'tupu': 'king/grow',
    'alii': 'lord',
    'matai': 'chief',
    'auauna': 'servant',
    'perofeta': 'prophet',
    'aposetolo': 'apostle',
    'agaga': 'spirit/soul',
    'tino': 'body',
    'ulu': 'head',
    'lima': 'hand',
    'vae': 'foot',
    'mata': 'eye',
    'fofoga': 'face',
    'gutu': 'mouth',
    'taliga': 'ear',
    'loto': 'heart',
    'manatu': 'thought',

    # Actions / verbs
    'muai': 'first',
    "ta'uina": 'was told',
    'tauina': 'was told',
    'faia': 'made',
    'fai': 'make',
    'fetalai': 'said',
    'faaigoa': 'called',
    'silasila': 'saw',
    'iloa': 'known',
    'faalogo': 'hearken',
    'tuu': 'put',
    'ave': 'take',
    'sau': 'come',
    'alu': 'go',
    'nofo': 'dwell',
    'nofoalii': 'throne',
    'tu': 'stand',
    'savali': 'walk',
    'taofi': 'hold',
    'tago': 'reach',
    'tuli': 'drive',
    'faatoilalo': 'subdue',
    'iu': 'attain',
    "i'u": 'attain',
    'anaana': 'his own',
    'valaauina': 'called',
    'valaau': 'call',
    'tofia': 'chosen',
    "tala'i": 'preach',
    'talai': 'preach',
    'pule': 'rule',
    'fanafanau': 'be fruitful',
    'uluola': 'multiply',
    'tumu': 'fill',
    'faamanuia': 'blessed',
    'fanau': 'born',
    'oti': 'die',
    'ola': 'life/live',
    'alofa': 'love',
    'alofaina': 'beloved',
    'faamagalo': 'forgive',
    'tatalo': 'pray',
    'ifo': 'bow down',
    'galue': 'work',
    'tofi': 'appoint',
    'filifili': 'choose',
    'alualu': 'pursue',
    'sola': 'flee',
    'taua': 'war',
    'fasi': 'kill',
    'fasiotia': 'slain',
    'lavea\u02bbi': 'delivered',
    'laveai': 'deliver',
    'togafiti': 'heal',
    'maliu': 'die',
    'soifua': 'live',
    'toe': 'again',
    'potopoto': 'gather',
    'faapotopoto': 'gather together',
    'foai': 'give',
    'maua': 'received',
    'tali': 'answer',
    'aai': 'city',
    "a'ai": 'eat',
    "a\u02bbai": 'eat',
    "'aina": 'edible',
    "'ai": 'eat',
    'inu': 'drink',
    'moe': 'sleep',
    'ala': 'arise',
    'fetolofi': 'creep',
    'lele': 'fly',
    'fegaoioiai': 'moved',
    'nunumi': 'without form',
    'gaogao': 'void',
    'ufitia': 'covered',
    'eseese': 'divided',
    'iloga': 'divided',
    'tutupu': 'bring forth',
    'faamalamalama': 'give light',
    "ta'u": 'tell',
    'faailoa': 'declared',
    'tumau': 'endure',
    "fa'atonuga": 'decree',
    "fa\u02bbatonuga": 'decree',
    'tulaga': 'matter',
    "fa'amatala": 'explained',
    "fa\u02bbamatala": 'explained',
    "va'ai": 'see',
    "va\u02bbai": 'see',
    'tali': 'respond',
    # Additional verbs for scripture
    'faapea': 'so',
    'manao': 'desire',
    'tigaina': 'afflicted',
    'faamalieina': 'satisfied',
    'tausia': 'kept',
    'tausi': 'keep',
    'lavea': 'saved',
    'faaola': 'save',
    'faatali': 'wait',
    'manumalo': 'overcome',
    'faasino': 'declare',
    'faasinotonuina': 'declared',
    'matamata': 'observe',
    'silafia': 'seen',
    'mafai': 'able',
    'tatala': 'open',
    'pupuni': 'shut',
    'tapena': 'prepare',
    'saunia': 'prepared',

    # Qualities / adjectives
    'lelei': 'good',
    'leaga': 'evil',
    'tele': 'great',
    'itiiti': 'small',
    'tetele': 'great',
    'malosi': 'strong',
    'vaivai': 'weak',
    'poto': 'wise',
    'vale': 'foolish',
    'amiotonu': 'righteous',
    'agasala': 'sin',
    'mamalu': 'glory',
    'paia': 'holy',
    'matutu': 'dry',
    'uluai': 'first',
    'matua': 'very',
    'matu\u0101': 'very',
    'sili': 'most',
    'ogaoga': 'fierce',
    'malolo': 'rest',
    'saogalemu': 'safe',

    # Animals
    'manu': 'animal',
    'manulele': 'bird',
    'i\'a': 'fish',
    'tanimo': 'whale',
    'mea': 'thing',

    # Categories
    'felelei': 'flying',

    # Preposition phrases
    'lalo': 'under',
    'luga': 'above',
    'tala': 'side',
    'tua': 'behind',
    'luma': 'before',
    'totonu': 'inside',
    'fafo': 'outside',

    # Religious
    'iesu': 'Jesus',
    'keriso': 'Christ',
    'ieova': 'Jehovah',
    'alii': 'Lord',
    "ali'i": 'Lord',
    'tusi': 'book/write',
    'upu': 'word',
    'tulafono': 'law/commandment',
    'feagaiga': 'covenant',
    'papatisoga': 'baptism',
    'salamo': 'repent',
    'faatuatua': 'faith',
    'ekalesia': 'church',
    'atoniga': 'atonement',
    'siufofoga': 'voice',
    'fofoga': 'face/mouth',
    'afio': 'dwell (respectful)',
    'faafofoga': 'listen/hearken',
    'motu': 'island',
    'moni': 'true/truth',
    'la\u02bcu': 'my',
    "la'u": 'my',
    'lau': 'your',
    'lona': 'his/her',
    'lo\u02bbu': 'my',
    "lo'u": 'my',
    "o'u": 'my',
    'o\u02bbu': 'my',
    'lou': 'your',
    'ona': 'his/her',
    'tunoa': 'grace/free',
    'gasologa': 'course/process',
    'puapuaga': 'affliction',
    'alofagia': 'favored',
    'faiva': 'ministry/calling',
    'suafa': 'name',
    'manuia': 'peace/blessing',
    'faatusa': 'image/likeness',
    'foliga': 'likeness/form',
    'faailoga': 'sign/token',
    'tau': 'season/count/fight',
    'tausaga': 'year',
    'gafa': 'genealogy',

    # Pronouns (full forms)
    "a\u02bbu": 'I/me',
    "a'u": 'I/me',
    'au': 'I/me',
    'oe': 'you',
    "'oe": 'you',
    'ia': 'he/she/him/her',
    'ita': 'we (excl)',
    # Plural pronouns (3+)
    'tatou': 'we/us (incl)',
    'matou': 'we/us (excl)',
    'outou': 'you (all)',
    'latou': 'they/them',
    # Dual pronouns (2)
    "ta'ua": 'us (two, incl)',
    "ta\u02bbua": 'us (two, incl)',
    "ma'ua": 'us (two, excl)',
    "ma\u02bbua": 'us (two, excl)',
    'oulua': 'you (two)',
    'laua': 'they/them (two)',
    "la'ua": 'they/them (two)',
    "la\u02bbua": 'they/them (two)',
    'oulua': 'you (two)',
    # Short pronoun forms (used with tense markers)
    "'ou": 'I',
    "o\u02bbu": 'I',
    "'e": 'you',

    # BOM names
    'nifae': 'Nephi',
    'lamana': 'Laman',
    'lemuelu': 'Lemuel',
    'saama': 'Sam',
    'lihai': 'Lehi',
    'mamona': 'Mormon',
    'moronae': 'Moroni',
    'alema': 'Alma',
    'helamana': 'Helaman',
    'mosaea': 'Mosiah',
    'iakopo': 'Jacob',
    'enosa': 'Enos',
    'iaromo': 'Jarom',
    'amuleki': 'Amulek',
    'aminetapo': 'Aminadab',
    'korianeta': 'Coriantumr',
    'sapeli': 'Sariah',
    'isemaeli': 'Ishmael',
    'amalekae': 'Amalickiah',
    'moronihaa': 'Moroniha',
    'pahora': 'Pahoran',
    'tiankamo': 'Teancum',
    'seesaramu': 'Zeezrom',
    'kapeteni': 'Captain',

    # Bible OT names (Samoan → English)
    'atamu': 'Adam',
    'eva': 'Eve',
    'kaino': 'Cain',
    'apelu': 'Abel',
    'noa': 'Noah',
    'aperaamo': 'Abraham',
    'isaako': 'Isaac',
    'esau': 'Esau',
    'iakopo': 'Jacob',
    'iosefa': 'Joseph',
    'mose': 'Moses',
    'arona': 'Aaron',
    'iosua': 'Joshua',
    'samuelu': 'Samuel',
    'tavita': 'David',
    'solomona': 'Solomon',
    'elia': 'Elijah',
    'elisaia': 'Elisha',
    'isaia': 'Isaiah',
    'ieremia': 'Jeremiah',
    'esekielu': 'Ezekiel',
    'tanielu': 'Daniel',
    'ruta': 'Ruth',
    'eseta': 'Esther',
    'hamana': 'Haman',
    'moretekai': 'Mordecai',
    'moredekai': 'Mordecai',
    'iopa': 'Job',
    'iona': 'Jonah',
    'saulo': 'Saul',
    'setefano': 'Stephen',
    'pilatoi': 'Pilate',
    'herota': 'Herod',
    'farao': 'Pharaoh',
    'etoma': 'Edom',
    'filisitia': 'Philistine',
    'kanana': 'Canaan',
    'isaraelu': 'Israel',
    'aikupito': 'Egypt',
    'papelonia': 'Babylon',
    'ierusalema': 'Jerusalem',
    'ioroni': 'Jordan',
    'siona': 'Zion',
    'kalilaia': 'Galilee',
    'samaria': 'Samaria',
    'setena': 'Satan',
    'etena': 'Eden',

    # Bible NT names (Samoan → English)
    'iesu': 'Jesus',
    'keriso': 'Christ',
    'ieova': 'Jehovah',
    'paulo': 'Paul',
    'peteru': 'Peter',
    'ioane': 'John',
    'mataio': 'Matthew',
    'mareko': 'Mark',
    'luka': 'Luke',
    'iakopo': 'James',
    'tomas': 'Thomas',
    'aneteriu': 'Andrew',
    'filipo': 'Philip',
    'patalameo': 'Bartholomew',
    'simona': 'Simon',
    'iuta': 'Judas',
    'iutasi': 'Judas',
    'timoteo': 'Timothy',
    'tito': 'Titus',
    'pilemoni': 'Philemon',
    'epafura': 'Epaphras',
    'persila': 'Priscilla',
    'akuila': 'Aquila',
    'maria': 'Mary',
    'mareta': 'Martha',
    'lasaro': 'Lazarus',
    'nikotimo': 'Nicodemus',
    'paapasa': 'Barabbas',
    'kailafa': 'Caiaphas',

    # Places
    'roma': 'Rome',
    'korinito': 'Corinth',
    'kalatia': 'Galatia',
    'efeso': 'Ephesus',
    'filipoi': 'Philippi',
    'kolose': 'Colossae',
    'tesalonika': 'Thessalonica',
    'atioka': 'Antioch',
    'sinai': 'Sinai',
    'masitonia': 'Macedonia',
    'akaia': 'Achaia',
    'siria': 'Syria',
    'peresia': 'Persia',
    'asuria': 'Assyria',
    'napoli': 'Naples',

    # ============================================================
    # Common biblical words (top untranslated - bulk add)
    # ============================================================
    # Particles / connectors
    'auā': 'for/because',
    'aua': 'for/because',
    'loo': '(progressive)',
    'tusa': 'according to',
    'pea': 'continually',
    'nisi': 'some/others',
    'peiseai': 'as if',
    'taitoatasi': 'each one',
    'atoatoa': 'completely',
    'aunoa': 'without',

    # Family / people
    'fanauga': 'children',
    'toatele': 'many',
    'toalua': 'companion/spouse',
    'tupulaga': 'generation',
    'avā': 'wife',

    # Religious / temple
    'taulaga': 'offering/sacrifice',
    'faitaulaga': 'priest',
    'ositaulaga': 'high priest',
    'togiola': 'atonement/redemption',
    'fata': 'altar',
    'faitotoa': 'gate/door',
    'poloaiga': 'commandment',
    'poloai': 'command',
    'poloaiina': 'commanded',

    # Actions - giving / taking
    'tuuina': 'given',
    'avatu': 'give away',
    'aumaia': 'bring here',
    'avatua': 'given away',
    'auina': 'sent',
    'aauina': 'sent',
    'foaiina': 'given/bestowed',
    'talia': 'received/accepted',

    # Actions - movement / state
    'avea': 'become',
    'nonofo': 'dwelling',
    'tulai': 'arose/stood up',
    'liliu': 'turned',
    'sosola': 'fled',
    'savavali': 'walked',
    'pauu': 'fell',
    'amata': 'began',
    'latalata': 'near/approached',

    # Actions - destruction / conflict
    'fasioti': 'killed',
    'fasia': 'struck/slain',
    'autau': 'fought/army',
    'fano': 'perish',

    # Actions - communication / thought
    'tusia': 'written',
    'mafaufau': 'think/mind',
    'manatua': 'remember',
    'saili': 'seek',
    'faalogologo': 'listen',
    'pepelo': 'false/lie',
    'olioli': 'rejoice',

    # Actions - building / doing
    'faatuina': 'built/established',
    'faataunuuina': 'fulfilled',
    'faaolaina': 'saved/delivered',
    'faasaoina': 'saved/preserved',
    'laveaiina': 'delivered',
    'filifilia': 'chosen',
    'mafaia': 'able/possible',
    'vaaia': 'seen/appeared',

    # Qualities
    'malolosi': 'mighty/strong',
    'filemu': 'peace/peaceful',
    'mamā': 'clean/pure',
    'inosia': 'abominable',
    'matagofie': 'beautiful',
    'matatau': 'fear/afraid',
    'toasa': 'wrath/angry',

    # Objects / places
    'ofu': 'garment/clothing',
    'vaega': 'portion/part',
    'auro': 'gold',
    'ario': 'silver',
    'saito': 'wheat',
    'areto': 'bread',
    'uaina': 'wine',
    'kupita': 'cubit',
    'ipu': 'cup/vessel',
    'aao': 'hand (extended)',
    'vaitafe': 'river',
    'nofoaga': 'place/dwelling',
    'tupua': 'idol',
    'poa': 'captive/prisoner',
    'manogi': 'fragrant/incense',
    'olo': 'fortress',
    'tuaoi': 'border/boundary',

    # Body actions
    'sii': 'lift up',
    'ole': 'entreat/plead',
    'tuua': 'left/forsaken',
    'ita': 'angry',
    'ino': 'evil/harm',

    # Specific biblical terms
    'amio': 'conduct/behavior',
    'amioletonu': 'wickedness',
    'faasaga': 'toward/facing',
    'taimi': 'time/period',
    'taumatau': 'right hand',
    'levī': 'Levi',
    'atunuu': 'nations/people',

    # Leviticus / sacrifice vocabulary
    'sausauina': 'sprinkle',
    'sausau': 'sprinkle',
    "ga'o": 'fat',
    "fatuga'o": 'kidneys',
    'fetafai': 'tabernacle',
    'susunu': 'burn',
    'amuli': 'after/to come',
    'tupulaga': 'generation/generations',
    'aitu': 'devils',
    'mulilulua': 'whoring',
    'mulilua': 'whoring',
    'mulimuli': 'follow after',
}

# ============================================================
# Dictionary lookup with fallbacks
# ============================================================
def lookup_word(word):
    """Look up a Samoan word, return English gloss or empty string."""
    w = word.lower().rstrip('.,;:!?\u201c\u201d\u201e()').lstrip('\u201c\u201d()')
    if not w:
        return ""
    # Normalize apostrophe variants for lookups
    w_norm = w.replace('\u2018', "'").replace('\u2019', "'").replace('\u02bc', "'").replace('\u02bb', "'")
    # Check normalized form in function words
    if w_norm in FUNC_WORDS:
        return FUNC_WORDS[w_norm]
    if w_norm in EXTENDED_VOCAB:
        return EXTENDED_VOCAB[w_norm]

    # Check function words first
    if w in FUNC_WORDS:
        return FUNC_WORDS[w]

    # Check extended vocabulary
    if w in EXTENDED_VOCAB:
        return EXTENDED_VOCAB[w]

    # Direct dictionary lookup
    if w in dictionary:
        g = dictionary[w]
        # Clean up verbose dictionary entries
        g = re.sub(r'\s*\([^)]*\)', '', g).strip(' ,;.')
        if g:
            # Take first meaning before semicolon
            g = g.split(';')[0].split(',')[0].strip()
            return g
        return dictionary[w].split(';')[0].split(',')[0].strip()

    # Try without glottal stops
    w2 = w.replace('\u02bb', "'").replace('\u02bc', "'")
    if w2 in EXTENDED_VOCAB:
        return EXTENDED_VOCAB[w2]
    if w2 in dictionary:
        return dictionary[w2].split(';')[0].split(',')[0].strip()
    w3 = w.replace('\u02bb', '').replace('\u02bc', '').replace("'", '')
    if w3 in EXTENDED_VOCAB:
        return EXTENDED_VOCAB[w3]
    if w3 in dictionary:
        return dictionary[w3].split(';')[0].split(',')[0].strip()

    return ""


# ============================================================
# Phrase chunking rules
# ============================================================
# Words that START a new phrase (phrase boundaries)
PHRASE_STARTERS = {
    # Tense/aspect markers (start verb phrases)
    'ua', 'na', 'sa', 'e', "ole'a", "olo'o",
    # Conjunctions
    'ma', 'a', 'ae',
    # Prepositions (start prepositional phrases)
    'i', 'mo',
    # Verbal result pattern
    'ona',
    # Discourse markers
    'faauta', 'ina',
    # Inclusive
    'atoa',
}

# Words that NEVER start a new phrase (always attach to previous)
CLITICS = {
    'le', 'o', 'se', 'ni',  # articles (attach forward)
    'foi', 'lava',  # emphatics (attach backward)
    'ai', 'lea',  # verbal particles (attach backward)
}

# Phrase-internal words that bridge between content words
BRIDGE_WORDS = {
    'le', 'o', 'se', 'lo', 'te', 'ia', 'i',
}


def _build_phrase_pairs():
    """Build a set of consecutive word pairs from known WHOLE_PHRASES.
    Used to prevent the chunker from splitting words that belong together."""
    pairs = set()
    for phrase in WHOLE_PHRASES:
        wds = phrase.split()
        for idx in range(len(wds) - 1):
            pairs.add((wds[idx], wds[idx+1]))
    return pairs

# Will be initialized after WHOLE_PHRASES is defined (see below)
_PHRASE_PAIRS = set()  # placeholder, built after WHOLE_PHRASES


def chunk_verse(text):
    """
    Split Samoan verse text into grammatical phrase chunks.
    Returns list of phrase strings.
    """
    if not text:
        return []

    words = text.split()
    if not words:
        return []

    phrases = []
    current_phrase = [words[0]]

    for i in range(1, len(words)):
        w = words[i]
        w_clean = w.lower().strip('.,;:!?\u201c\u201d\u201e()')

        prev = words[i-1] if i > 0 else ''
        prev_clean = prev.lower().strip('.,;:!?\u201c\u201d\u201e()')

        # Should this word start a new phrase?
        start_new = False
        is_punctuation_break = False

        # Rule 1: After comma, semicolon, period, or closing paren, always start new phrase
        if prev.rstrip(')').endswith(';') or prev.rstrip(')').endswith('.') or prev.rstrip(')').endswith(','):
            start_new = True
            is_punctuation_break = True

        # Rule 1b: "o" after a pronoun (a'u, ia, etc.) starts a new phrase (naming pattern)
        elif w_clean == 'o' and len(current_phrase) >= 2:
            prev2_raw = current_phrase[-1].lower().rstrip('.,;:!?')
            # Normalize all apostrophe-like characters for comparison
            prev2_norm = prev2_raw.replace('\u02bb', "'").replace('\u2018', "'").replace('\u2019', "'").replace('\u02bc', "'")
            if prev2_norm in ("a'u", "au", "ia", "oe", "i'a"):
                start_new = True

        # Rule 2: Phrase starters begin new phrases
        elif w_clean in PHRASE_STARTERS:
            if len(current_phrase) >= 2:
                start_new = True
            elif w_clean in ('ua', 'na', 'sa', 'ona', 'faauta', 'ina', 'atoa'):
                start_new = True
            elif w_clean in ('ma', 'a', 'ae') and len(current_phrase) >= 2:
                start_new = True

        # Rule 3: "le + content_word" after 2+ word phrase starts new noun phrase
        elif w_clean == 'le' and len(current_phrase) >= 2:
            # Check if previous word is NOT a preposition/marker expecting an article
            # Include 'la' since "la le" is a compound article
            if prev_clean not in ('o', 'i', 'e', 'ma', 'mo', 'mai', 'la'):
                start_new = True

        # Rule 4: "o le" / "O le" naming/predicate pattern starts new phrase
        elif w_clean == 'o' and len(current_phrase) >= 2:
            if i + 1 < len(words) and words[i+1].lower().rstrip('.,;:') == 'le':
                start_new = True

        # Rule 5: If current phrase is getting long (6+ words), look for natural break
        elif len(current_phrase) >= 6:
            if w_clean in ('le', 'o', 'se', 'e', 'i', 'ma', 'ia'):
                start_new = True

        # Rule 6: (merged into Rule 1 — commas always break phrases)

        # Override: don't split if these words belong to a known phrase
        # (never override punctuation breaks from Rule 1)
        if start_new and not is_punctuation_break:
            # Normalize apostrophes for pair matching
            pc_norm = prev_clean.replace('\u02bb', "'").replace('\u2018', "'").replace('\u2019', "'").replace('\u02bc', "'")
            wc_norm = w_clean.replace('\u02bb', "'").replace('\u2018', "'").replace('\u2019', "'").replace('\u02bc', "'")
            if (prev_clean, w_clean) in _PHRASE_PAIRS or (pc_norm, wc_norm) in _PHRASE_PAIRS:
                start_new = False

        if start_new:
            phrases.append(' '.join(current_phrase))
            current_phrase = [w]
        else:
            current_phrase.append(w)

    if current_phrase:
        phrases.append(' '.join(current_phrase))

    return phrases


def chunk_grammatical(text):
    """
    Split Samoan text into ~2-4 word grammatical phrase groups,
    similar to Hebrew interlinear style.

    Breaks on Samoan grammatical boundaries:
    - Verb phrases: tense marker + verb (+ directional particle)
    - Agent phrases: e + article + noun
    - Noun phrases: article + noun (+ modifier)
    - Prepositional phrases: prep + article + noun
    - Conjunction phrases: ma/a/ae + next phrase
    - Predicate/possessive: o + article + noun
    """
    if not text:
        return []

    words = text.split()
    if len(words) <= 3:
        return [text]

    # Prepositions/particles that expect an article to follow
    # (prevent "le" from starting a new chunk when preceded by these)
    PREP_LIKE = {'o', 'i', 'e', 'ma', 'mo', 'la', 'a', 'ia', 'lo'}

    chunks = []
    current = []

    for i, w in enumerate(words):
        raw_stripped = w.lower().strip('.,;:!?()\u201c\u201d\u201e\u2018\u2019')
        w_clean = raw_stripped.replace('\u02bb', "'").replace('\u02bc', "'")

        prev_raw = words[i-1] if i > 0 else ''
        prev_stripped = prev_raw.lower().strip('.,;:!?()\u201c\u201d\u201e\u2018\u2019') if prev_raw else ''
        prev_clean = prev_stripped.replace('\u02bb', "'").replace('\u02bc', "'") if prev_stripped else ''

        start_new = False

        # --- Hard break: after sentence-internal punctuation ---
        if i > 0 and any(prev_raw.rstrip(')').endswith(p) for p in (',', ';', '.', ':', '!')):
            start_new = True

        # --- Grammatical breaks (need >= 2 words in current chunk) ---
        elif len(current) >= 2:
            # Tense/aspect markers start new verb phrase
            if w_clean in ('ua', 'na', 'sa', "ole'a", "olo'o"):
                start_new = True
            # "ona" narrative continuation
            elif w_clean == 'ona':
                c_prev1 = current[-1].lower().strip('.,;:!?()\u201c\u201d\u201e') if current else ''
                if c_prev1 == 'faapea':
                    pass  # "faapea ona" = while thus, keep together
                elif c_prev1 == 'tatau':
                    pass  # "e tatau ona" = should/ought to, keep together
                elif c_prev1 == 'uma':
                    pass  # "ua uma ona" = finished, keep together
                elif c_prev1 == 'lava':
                    pass  # "e pei lava ona" = just as, keep together
                elif c_prev1 == 'pei':
                    pass  # "e pei ona" = as, keep together
                elif c_prev1 == 'mafai':
                    pass  # "e mafai ona" / "na mafai ona" = could/able to, keep together
                else:
                    start_new = True
            # Conjunctions (but NOT "a" when part of "o le a" future tense)
            elif w_clean in ('ma', 'a', 'ae', 'atoa'):
                if w_clean == 'a' and len(current) >= 2:
                    c_prev1 = current[-1].lower().strip('.,;:!?()\u201c\u201d\u201e')
                    c_prev2 = current[-2].lower().strip('.,;:!?()\u201c\u201d\u201e')
                    if c_prev2 == 'o' and c_prev1 == 'le':
                        pass  # "o le a" = future tense marker, keep together
                    else:
                        start_new = True
                elif w_clean == 'ma' and len(current) >= 1:
                    c_prev1 = current[-1].lower().strip('.,;:!?()\u201c\u201d\u201e')
                    if c_prev1 == 'tusa':
                        pass  # "e tusa ma" = according to, keep together
                    else:
                        start_new = True
                elif w_clean == 'atoa' and len(current) >= 1:
                    c_prev1 = current[-1].lower().strip('.,;:!?()\u201c\u201d\u201e')
                    if c_prev1 == 'loto':
                        pass  # "loto atoa" = wholeheartedly, keep together
                    else:
                        start_new = True
                else:
                    start_new = True
            # Prepositions
            elif w_clean in ('i', 'mo'):
                # Keep "e ui i lea" together (nevertheless)
                if w_clean == 'i' and len(current) >= 2:
                    c_p1 = current[-1].lower().strip('.,;:!?()\u201c\u201d\u201e')
                    c_p2 = current[-2].lower().strip('.,;:!?()\u201c\u201d\u201e')
                    if c_p2 == 'e' and c_p1 == 'ui':
                        pass  # "e ui i lea" = nevertheless, keep together
                    elif c_p1 == 'atu' and c_p2 == 'sili':
                        pass  # "sili atu i lo" = comparison, keep together
                    else:
                        start_new = True
                else:
                    start_new = True
            # "mai" as preposition (after 3+ words to preserve verb+directional)
            elif w_clean == 'mai' and len(current) >= 3:
                c_prev1 = current[-1].lower().strip('.,;:!?()\u201c\u201d\u201e')
                if c_prev1 == 'fai':
                    pass  # "sa fai mai" = said, keep together
                else:
                    start_new = True
            # Agent marker "e"
            # BUT: "e tele" = "many/great" modifies previous noun, keep together
            elif w_clean == 'e':
                if i + 1 < len(words):
                    next_e = words[i+1].lower().strip('.,;:!?()\u201c\u201d\u201e')
                    if next_e == 'tele':
                        pass  # "e tele" = many, keep with noun
                    elif next_e in ('ia', 'au', 'oe', 'latou', 'matou', 'tatou',
                                    'outou', 'laua', 'oulua', 'i') and len(current) <= 3:
                        pass  # "e + pronoun" = agent marker (by him/her), keep with verb
                    elif next_e == 'ao' and i + 2 < len(words):
                        next_e2 = words[i+2].lower().strip('.,;:!?()\u201c\u201d\u201e')
                        if next_e2 == 'ina':
                            start_new = True  # "e ao ina" = must needs, start new chunk here
                        else:
                            start_new = True
                    else:
                        start_new = True
                else:
                    start_new = True
            # "o" before article or possessive pronoun -> new predicate/possessive NP
            # BUT: "o le a [verb]" is future tense — don't split
            elif w_clean == 'o' and i + 1 < len(words):
                next_c = words[i+1].lower().strip('.,;:!?()\u201c\u201d\u201e').replace('\u02bb', "'").replace('\u02bc', "'")
                c_prev_o = current[-1].lower().strip('.,;:!?()\u201c\u201d\u201e') if current else ''
                if c_prev_o == 'pei':
                    pass  # "e pei o le" = like the, keep together
                elif c_prev_o in ('latou', 'tatou', 'matou', 'outou',
                                  'laua', 'oulua', "ta'ua", "ma'ua", "la'ua",
                                  'ia', 'oe', "'oe", 'au', "a'u"):
                    start_new = True  # "o" after pronoun = relative clause marker
                elif next_c in ('le', 'lo', 'la', 'se', 'ni',
                              "lo'u", "la'u", "o'u", "a'u",
                              'lou', 'lau', 'lona', 'lana',
                              'ona', 'ana', 'lo', 'la'):
                    # Check for "o le a" future tense pattern
                    if next_c == 'le' and i + 2 < len(words):
                        next2_c = words[i+2].lower().strip('.,;:!?()\u201c\u201d\u201e').replace('\u02bb', "'").replace('\u02bc', "'")
                        if next2_c == 'a' and i + 3 < len(words):
                            start_new = True  # "o le a [verb]" = future tense, start new chunk
                        else:
                            start_new = True
                    else:
                        start_new = True
            # Article after content word -> new NP
            elif w_clean in ('le', 'se') and prev_clean not in PREP_LIKE:
                start_new = True
            # Discourse markers
            elif w_clean in ('faauta', 'ina'):
                if w_clean == 'ina' and len(current) >= 2:
                    c_p1 = current[-1].lower().strip('.,;:!?()\u201c\u201d\u201e')
                    c_p2 = current[-2].lower().strip('.,;:!?()\u201c\u201d\u201e')
                    if c_p2 == 'e' and c_p1 == 'ao':
                        pass  # "e ao ina" = must, keep together
                    elif c_p1 == 'oo' and c_p2 == 'sa':
                        pass  # "sa oo ina" = it came to pass, keep together
                    else:
                        start_new = True
                else:
                    start_new = True
            # "pe" subordinating conjunction (whether/if)
            elif w_clean == 'pe':
                start_new = True
            # "nai" comparison marker (nai lo = more than)
            elif w_clean == 'nai':
                start_new = True

        # --- Forced break after "e ao ina" (must needs) or "sa oo ina" (it came to pass) ---
        if not start_new and len(current) >= 3:
            c_words = [c.lower().strip('.,;:!?()\u201c\u201d\u201e') for c in current[-3:]]
            if c_words == ['e', 'ao', 'ina'] or c_words == ['sa', 'oo', 'ina']:
                start_new = True

        # --- Forced break after "faapea ona" (while thus) ---
        if not start_new and len(current) >= 2:
            c2 = [c.lower().strip('.,;:!?()\u201c\u201d\u201e') for c in current[-2:]]
            if c2 == ['faapea', 'ona'] or c2 == ['tatau', 'ona'] or c2 == ['uma', 'ona'] or c2 == ['lava', 'ona'] or c2 == ['pei', 'ona'] or c2 == ['mafai', 'ona']:
                start_new = True

        # --- Forced break after "sili atu i lo" (comparison: exceeded than) ---
        if not start_new and len(current) >= 4:
            c4 = [c.lower().strip('.,;:!?()\u201c\u201d\u201e') for c in current[-4:]]
            if c4 == ['sili', 'atu', 'i', 'lo']:
                start_new = True

        # --- Forced break after "ia te ia" (unto him) ---
        if not start_new and len(current) >= 3:
            c3 = [c.lower().strip('.,;:!?()\u201c\u201d\u201e') for c in current[-3:]]
            if c3 == ['ia', 'te', 'ia']:
                start_new = True

        # --- Forced break after vocative "e" (e.g. "Le Alii e" = O Lord) ---
        if not start_new and len(current) >= 3:
            prev_e = current[-1].lower().strip('.,;:!?()\u201c\u201d\u201e')
            prev_title = current[-2].lower().strip('.,;:!?()\u201c\u201d\u201e')
            if prev_e == 'e' and prev_title in ('alii', 'atua'):
                start_new = True

        # --- Forced break at 4+ words after pronoun ---
        if not start_new and len(current) >= 4:
            prev_c = current[-1].lower().strip('.,;:!?()\u201c\u201d\u201e').replace('\u02bb', "'").replace('\u02bc', "'")
            if prev_c in ("a'u", 'au', 'oe', "'oe", 'ia', 'tatou', 'matou',
                          'latou', 'outou', 'laua', 'oulua', "ta'ua", "ma'ua", "la'ua"):
                # Don't break if next word is "te" or "i" (directional: "ia te ia" = unto him, "ia i" = toward)
                if prev_c == 'ia' and w_clean in ('te', 'i'):
                    pass
                # Don't break after possessive pronoun (lo/la + pronoun + noun)
                elif len(current) >= 2:
                    prev2_c = current[-2].lower().strip('.,;:!?()\u201c\u201d\u201e')
                    if prev2_c in ('lo', 'la'):
                        pass  # possessive phrase, let noun attach
                    else:
                        start_new = True
                else:
                    start_new = True

        # --- Forced break at 5+ words on any function word ---
        # BUT: don't break "o ia" pronoun apart
        if not start_new and len(current) >= 5:
            prev_fw = current[-1].lower().strip('.,;:!?()\u201c\u201d\u201e')
            if w_clean == 'ia' and prev_fw == 'o':
                pass  # "o ia" = he/she, keep together
            elif w_clean == 'ia' and prev_fw == 'te':
                pass  # "ia te ia" = unto him, keep together
            elif w_clean in ('le', 'o', 'se', 'e', 'i', 'ma', 'ia', 'mo', 'mai',
                           'a', 'ae', 'ona', 'ua', 'na', 'sa', 'foi', 'lava'):
                start_new = True

        # --- Vocative "e" after title/name: "Le Alii e" = O Lord ---
        if start_new and w_clean == 'e' and current:
            prev_voc = current[-1].lower().strip('.,;:!?()\u201c\u201d\u201e')
            if prev_voc in ('alii', 'atua'):
                start_new = False  # vocative "e", keep with title

        if start_new and current:
            chunks.append(' '.join(current))
            current = [w]
        else:
            current.append(w)

    if current:
        chunks.append(' '.join(current))

    return chunks


# ============================================================
# Known whole-phrase patterns (module-level for use by both
# gloss_phrase and annotate_verse sub-phrase splitting)
# ============================================================
WHOLE_PHRASES = {
    # "O a'u o" = "I am" patterns
    "o a\u02bbu o": 'I am',
    # Common scripture phrases
    "sa oo ina": 'it came to pass',
    "e tusa ma": 'according to',
    "e ao ina": 'must needs',
    "loto atoa lava": 'wholeheartedly',
    "e ui i lea": 'nevertheless',
    "a'o faapea ona": 'and while thus',
    "e tatau ona": 'should',
    "ua uma ona": 'finished',
    "nai lo": 'more than',
    "sili atu i lo": 'exceeded',
    "tuu mai": 'gave',
    "e uiga ia": 'concerning',
    "e uiga i": 'concerning',
    "e pei o le": 'like the',
    "e pei lava ona": 'even as',
    "e pei ona": 'as',
    "puapuaga e tele": 'many afflictions',
    "malamalama tele": 'great knowledge',
    "alofagia tele": 'highly favored',
    "sa alofagia tele a'u": 'I was highly favored',
    "sa alofagia tele a\u02bbu": 'I was highly favored',
    "o'u aso uma": 'all my days',
    "o\u02bbu aso uma": 'all my days',
    "e ao ina": 'must needs',
    "e matua lelei": 'goodly parents',
    "matua lelei": 'goodly parents',
    "le tala lelei": 'the gospel',
    "tala lelei": 'gospel',
    "a le atua": 'of God',
    "o le atua": 'of God',
    "le atua": 'God',
    "le ali\u02bbi sili": 'the Lord Most High',

    # Common Book of Mormon phrases
    "foi mai": 'return',
    "sa ou miti se miti": 'I dreamed a dream',
    "na poloaiina ai a'u": 'I was commanded',
    "e lei talitonu foi i laua": 'they also did not believe',
    "ma sa pei": 'and they were like',
    "o tagata Iutaia": 'the Jews',
    "na saili": 'sought',
    "e aveese": 'to take away',
    "ona sa ou talavou lava": 'because I was very young',
    "sa ou tino ese": 'being large in stature',
    "ma sa ia te a'u foi": 'and I also had',
    "le naunau tele": 'the great desire',
    "e fia iloa mealilo": 'to know the mysteries',
    "na ou tagi atu ai": 'I cried out',
    "ma faamalūlūina lo'u loto": 'and humbled my heart',
    "sa asiasi mai o ia": 'and he visited',

    # Genesis common phrases
    "sa soona nunumi": 'was without form',
    "sa ufitia foi": 'was also covered',
    "na fegaoioiai foi": 'was also hovering',
    "le vanimonimo": 'the firmament',
    "o le vanimonimo": 'the firmament',
    "ua va a'i": 'separated',
    "le malamalama": 'the light',
    "le pouliuli": 'the darkness',
    "o le aso muamua lea": 'was the first day',
    "o le aso lua lea": 'was the second day',
    "o le uluai aso lea": 'was the first day',
    "o le aso tolu lea": 'was the third day',
    "le eleele matutu": 'the dry land',
    "e taitasi ma lona uiga": 'after its kind',
    "le faapotopotoga o vai": 'the gathering of the waters',
    "ua silasila atu le Atua": 'God saw',
    "ua silasila atu i ai le Atua": 'and God saw',
    "a ua faaigoa e ia": 'and He called',
    "o le aso fa lea": 'was the fourth day',
    "o le aso lona lima lea": 'was the fifth day',
    "e faamalamalama a'i": 'to give light upon',
    "mea ola faatuputupu": 'living creatures',
    "manu felelei": 'birds',
    "e tusa ma o latou ituaiga": 'according to their kinds',
    "tupu faatuputupu": 'be fruitful and multiply',
    "manu vaefa fanua": 'livestock',
    "mea fetolofi": 'creeping things',
    "o le aso ono lea": 'were the sixth day',
    "o le faatoaga": 'the garden',
    "le aso fitu": 'the seventh day',
    "o le mānava ola": 'the breath of life',
    "ma tagata ola": 'a living being',
    "le laau o le ola": 'the tree of life',
    "le lelei ma le leaga": 'good and evil',
    "sa fai mai": 'said',
    "sa fai atu": 'spoke',
    "sa tautala atu o ia": 'he spoke',
    "ma'umau e": 'that you would endure',
    "e mafai ona": 'could',
    "na mafai ona": 'could',
    "pei oe": 'like you',
    "e tafe atu pea": 'to flow continually',
    "o le amiotonu uma": 'of all righteousness',

    # Seeing / Vision / Revelation
    'ua ou vaai': 'I saw',
    'sa vaai o ia': 'he saw',
    'ma sa vaai o ia': 'and he saw',
    'sa ia vaaia': 'he saw',
    'ma sa vaaia': 'and he saw',
    'sa vaaia e ia': 'that he saw',
    'vaai atu o ia': 'he looked',
    'sa vaai ai lava o ia': 'he indeed saw',
    'i se faaaliga vaaia': 'in a vision',
    'i faaaliga': 'in visions',
    'faaali mai': 'revealed',
    'ua faaali manino': 'clearly revealed',
    'sa segia o ia': 'he was carried away',
    'lofituina o ia': 'he was overcome',
    'ua afio ifo': 'descending',
    'ua siosiomia': 'surrounded',

    # Speaking / Prophesying / Witnessing
    'sa tatalo atu o ia': 'he prayed',
    'ma vavalo atu': 'and prophesied',
    'ona vavalo': 'to prophesy',
    'sa ia vavalo': 'that he prophesied',
    'ma tautala atu ai': 'and spoke unto',
    'sa molimau atu o ia': 'he witnessed',
    'sa molimau moni atu': 'truly testified',
    'sa alaga atu e ia': 'he cried out',
    'ma vivii atu': 'praising',
    'ma faalogoina': 'and heard',

    # God / Divine Titles
    'le Atua Malosi Aoao': 'God Almighty',
    'le afio mai': 'the coming of',
    'le togiolaina': 'the redemption',
    'alofa mutimutivale': 'mercy',
    'alofa mutimutivale agamalu': 'tender mercies',
    'le Alii lo matou Atua': 'the Lord our God',

    # Judgment / Destruction / Sin
    'oi talofa': 'wo',
    'mea inosia': 'abominations',
    'o le a faaumatia': 'will be destroyed',
    'o le a faaumatiaina': 'shall be destroyed',
    'o le a fano': 'shall perish',
    'ia fano': 'to perish',
    'i le pelu': 'by the sword',
    'ave faatagataotaua': 'taken captive',
    'mafaufauga valea': 'foolish imaginations',

    # Emotion / State
    'sa tumu o ia': 'he was filled',
    'sa galulu': 'quaking',
    'sa latou feitai ia te ia': 'they were angry with him',

    # Obedience / Commandments
    'usiusitai o ia': 'he obeyed',
    'i le afioga': 'the word',
    'poloaiina ai o ia': 'he was commanded',
    'i le tausiga o poloaiga': 'in keeping the commandments',
    'e tumau': 'to be firm',
    'ma mausali': 'and steadfast',

    # Record-Keeping (BOM)
    'o le talafaamaumau': 'the record',
    'se otootoga': 'an abridgment',
    'i luga o papatusi': 'upon plates',
    'ua tusia': 'written',
    'sa ia faitauina': 'that he read',
    'ou te faia': 'I make',

    # Travel / Wilderness / Dwelling
    'ma o ese atu': 'and departed',
    'sa malaga o ia': 'he traveled',
    'lona faleie': 'his tent',
    'i se vanu': 'in a valley',
    'o se vaitafe': 'a river',
    'ua mavae aso': 'days had passed',

    # Sacrifice / Worship
    'se fatafaitaulaga': 'an altar',
    'se taulaga': 'an offering',
    'le faafetai': 'thanks',

    # Prophets / People
    'perofeta anamua': 'the prophets of old',
    'na o mai ai perofeta': 'there came prophets',

    # Common Connectors / Grammar
    'ona o mea': 'because of the things',
    'ma amata': 'and began',
    'e faapea': 'saying',
    'i nei mea': 'these things',
    'mea e tele': 'great things',
    'le tele o mea': 'many things',
    'e toatele': 'many',
    'ona o lo latou faatuatua': 'because of their faith',
    'i ana fanau': 'his children',
    'ma lona loto atoa lava': 'with his whole heart',

    # =============================================
    # Genesis Creation phrases (Ch. 1-3)
    # =============================================
    'na faia e le atua le lagi ma le lalolagi i le amataga': 'In the beginning God created the heaven and the earth',
    'na faia e le atua': 'God created',
    'ua fetalai mai le atua': 'And God said',
    'ua fetalai mai foi le atua': 'And God said',
    'ona fetalai mai lea o le atua': 'And God said',
    'ona fetalai ane lea o le atua': 'And God said',
    'ua fetalai atu le atua': 'And God said',
    'ua fetalai atu foi le atua': 'And God said',
    'i le ua faapea lava': 'and it was so',
    'ua faapea lava': 'and it was so',
    'ua silasila atu le atua': 'And God saw',
    'ua silasila atu i ai le atua': 'and God saw',
    'ua lelei': 'that it was good',
    'ua matua lelei lava': 'it was very good',
    'ua matu\u0101 lelei lava': 'it was very good',
    'o le afiafi ma le taeao': 'the evening and the morning',
    'na faia e ia': 'he made',
    'ona faia lea e le atua': 'And God made',
    'ua faia e le atua': 'And God made',
    'ua faia foi e le atua': 'And God made',
    'ua faaigoa e le atua': 'And God called',
    'ua faamanuia e le atua': 'And God blessed',
    'ua faamanuia foi e le atua': 'And God blessed',
    'ona faamanuia atu i ai lea': 'And blessed them',
    'e le atua': 'by God',
    'le agaga o le atua': 'the Spirit of God',
    'ia malamalama': 'Let there be light',
    'ona malamalama ai lea': 'and there was light',
    'e taitasi ma lona uiga': 'after its kind',
    # Genesis 1:2
    'sa soona nunumi le lalolagi ma ua gaogao': 'the earth was without form and void',
    'sa soona nunumi le lalolagi': 'the earth was without form',
    'sa ufitia foi le moana i le pouliuli': 'and darkness was upon the face of the deep',
    'na fegaoioiai foi le agaga o le atua i le fog\u0101tai': 'and the Spirit of God moved upon the face of the waters',
    'na fegaoioiai foi le agaga o le atua': 'and the Spirit of God moved',
    'i le fog\u0101tai': 'upon the face of the waters',
    # Genesis 1:4
    'ona tuu eseese ai lea e le atua': 'and God divided',
    'tuu eseese': 'divided',
    'o le malamalama ma le pouliuli': 'the light from the darkness',
    'o le malamalama': 'the light',
    # Genesis 1:5-8
    'o le ao': 'Day',
    'o le po': 'Night',
    'o le lagi': 'Heaven',
    'o le eleele': 'Earth',
    'o le sami': 'Sea',
    'o le uluai aso lea': 'were the first day',
    'o le aso lua lea': 'were the second day',
    'o le aso tolu lea': 'were the third day',
    'o le aso fa lea': 'were the fourth day',
    'o le aso lima lea': 'were the fifth day',
    'o le aso ono lea': 'were the sixth day',
    # Genesis 1:6
    'ia i le va o vai le vanimonimo': 'Let there be a firmament in the midst of the waters',
    'e va a\'i isi vai ma isi vai': 'and let it divide the waters from the waters',
    'va a\'i': 'divided',
    'i le va o': 'in the midst of',
    # Genesis 1:7
    'le va nimonimo': 'the firmament',
    'ua va a\'i vai i lalo o le vanimonimo': 'divided the waters under the firmament',
    'ma vai i luga o le vanimonimo': 'from the waters above the firmament',
    'i lalo o le vanimonimo': 'under the firmament',
    'i luga o le vanimonimo': 'above the firmament',
    'i lalo o le lagi': 'under the heaven',
    'i luga o le laueleele': 'above the earth',
    'i luga o le eleele': 'upon the earth',
    # Genesis 1:9
    'ia potopoto i le mea e tasi': 'Let be gathered together unto one place',
    'o vai i lalo o le lagi': 'the waters under the heaven',
    'ia iloa foi le eleele matutu': 'and let the dry land appear',
    'le eleele matutu': 'the dry land',
    # Genesis 1:10
    'le faapotopotoga o vai': 'the gathering together of the waters',
    # Genesis 1:11
    'ia tupu le vao mu\'a mai le eleele': 'Let the earth bring forth grass',
    'le vao mu\'a': 'the grass',
    'vao mu\'a': 'grass',
    'mai le eleele': 'from the earth',
    'le laau afu': 'the herb yielding seed',
    'ma le laau afu': 'and the herb yielding seed',
    'laau afu': 'herb yielding seed',
    'e tupu ma ona fua': 'yielding seed',
    'le laau e \'aina ona fua': 'the fruit tree yielding fruit',
    'ma le laau e \'aina ona fua': 'and the fruit tree yielding fruit',
    'le laau e \'aina': 'the fruit tree',
    'ma le laau e \'aina': 'and the fruit tree',
    'e fua mai e taitasi ma lona uiga': 'whose seed was in itself after its kind',
    'e fua mai': 'yielding fruit',
    'o ia te ia lava o ona fatu': 'whose seed is in itself',
    'o ia te ia lava': 'in itself',
    'ona fatu': 'its seed',
    'ona fua': 'its fruit',
    # Genesis 1:14
    'ia iai': 'Let there be',
    'i le vanimonimo o le lagi': 'in the firmament of the heaven',
    'o mea e malamalama a\'i': 'lights',
    'mea e malamalama a\'i': 'lights',
    'e malamalama a\'i': 'for lights',
    'malamalama a\'i': 'lights',
    'e iloga ai le ao ma le po': 'to divide the day from the night',
    'e iloga ai': 'to divide',
    'ia fai foi ma faailoga': 'and let them be for signs',
    'ma tau': 'and for seasons',
    'ma aso': 'and for days',
    'ma tausaga': 'and years',
    # Genesis 1:15
    'ma ia fai ma mea e malamalama a\'i': 'and let them be for lights',
    'e faamalamalama a\'i le lalolagi': 'to give light upon the earth',
    'e faamalamalama a\'i': 'to give light',
    # Genesis 1:16
    'ona faia lea e le atua o malamalama tetele e lua': 'And God made two great lights',
    'o le malamalama tele': 'the greater light',
    'e pule i le ao': 'to rule the day',
    'o le malamalama itiiti': 'the lesser light',
    'e pule i le po': 'to rule the night',
    'ua na faia foi fetu': 'he made the stars also',
    # Genesis 1:17
    'ua tuu ai e le atua': 'And God set them',
    # Genesis 1:18
    'e pule foi i le ao ma le po': 'and to rule over the day and over the night',
    'ma ia iloga ai le malamalama ma le pouliuli': 'and to divide the light from the darkness',
    # Genesis 1:20
    'ia tele ona tutupu mai i le sami o meaola e fetolofi': 'Let the waters bring forth abundantly the moving creature that hath life',
    'ia lele foi le manulele i luga o le laueleele': 'and fowl that may fly above the earth',
    'ia lele foi le manulele': 'and let fowl fly',
    'le manulele': 'the fowl',
    # Genesis 1:21-25
    'tanimo tetele': 'great whales',
    'ua faia e le atua le tagata': 'God created man',
    'i lona foliga': 'in his image',
    'i le foliga o le atua': 'in the image of God',
    'o le tane ma le fafine': 'male and female',
    'ia fanafanau': 'Be fruitful',
    'ia uluola': 'and multiply',
    'ia tumu le lalolagi': 'and fill the earth',
    # Genesis 1:26
    'tatou te faia le tagata': 'Let us make man',
    'i lo tatou foliga': 'in our image',
    'e tusa ma lo tatou uiga': 'after our likeness',
    'ia latou pule': 'and let them have dominion',
    'i\'a o le sami': 'fish of the sea',
    'manulele o le lagi': 'fowl of the air',
    # General creation vocabulary
    'mea uma': 'all things',
    'mea uma lava': 'all things',
    'mea ola uma': 'every living thing',
    # Common "Ona ... lea" narrative patterns
    'ona tupu mai lea': 'And there grew',
    'ona fai atu lea': 'And he said',
    'ona fai mai lea': 'And he said',
    'ona alu lea': 'And he went',
    'ona sau lea': 'And he came',
    'ona faia lea': 'And he made',
    # Genesis 1:24-26 animal vocabulary
    'manu vaefa fanua': 'cattle',
    'manu vaefa o le vao': 'beast of the field',
    'manu vaefa': 'beast',
    'mea fetolofi': 'creeping thing',
    'mea fetolofi uma': 'every creeping thing',
    'meaola uma': 'every living creature',
    'manu felelei': 'fowl',
    # Genesis 1:26 image/likeness
    'i lo tatou faatusa': 'in our image',
    'lo tatou faatusa': 'our image',
    'ia foliga ia i tatou': 'after our likeness',
    'ia pule foi i latou': 'and let them have dominion',
    'ina tatou faia': 'Let us make',
    'tatou faia': 'let us make',
    'o le tagata': 'man',
    # Genesis 1:16
    'o malamalama tetele e lua': 'two great lights',
    'malamalama tetele e lua': 'two great lights',
    # Genesis 1:22
    'ia uluola': 'and multiply',
    'ia tupu tele': 'and be great',
    'ma ia tumu ai le sami': 'and fill the sea',
    'ia tupu tele foi manu felelei': 'and let fowl multiply',
    # Genesis 1:7 divided the waters
    'ua va a\'i vai i lalo o le vanimonimo': 'divided the waters under the firmament',
    # Hebrew דָּבָר (davar) corrections
    # Esther 3:4: הֲיַעַמְדוּ דִּבְרֵי מׇרְדֳּכַי
    "na fai atu pea i latou ia te ia i aso uma": 'They kept urging him every day',
    "ae na l\u0113 tali mai o ia": 'but he did not respond to them',
    "na l\u0113 tali mai o ia": 'he did not respond to them',
    "na latou fa'ailoa atu ai ia hamana": 'they reported it to Haman',
    "e va'ai pe o le a tumau le tulaga a moredekai": "to see whether Mordecai's position would hold",
    "le tulaga a moredekai": "Mordecai's position",
    "au\u0101 na ia fa'amatala atu o ia o se tagata iuta": 'because he had explained to them that he was a Jew',
    "na ia fa'amatala atu o ia": 'he had explained to them',
    "o se tagata iuta": 'a Jew',

    # Romans / Epistles
    'na ia muai': 'which was first',
    "ta'uina mai": 'told',
    "ta\u02bbuina mai": 'told',
    "ta\u2018uina mai": 'told',
    'e ana perofeta': 'by his prophets',
    'i tusi paia': 'in the scriptures',
    'tusi paia': 'the scriptures',
    'i lona alo o iesu keriso lo tatou alii': 'in his Son Jesus Christ our Lord',
    'lo tatou alii': 'our Lord',
    # Romans 1:5+
    'i la le tino': 'according to the flesh',
    'la le tino': 'the flesh',
    'ua matou maua': 'we received',
    'mai ia te ia': 'from him',
    'mai ia te': 'from',
    'ia te ia': 'unto him',
    'ia te': 'unto',
    'le alofa tunoa': 'grace',
    'alofa tunoa': 'grace',
    'na fanau mai': 'was born',
    'fanau mai': 'born',
    # Common verb + directional particle patterns
    'sau mai': 'come',
    'alu atu': 'go away',
    'alu mai': 'come',
    'ave atu': 'take away',
    'ave mai': 'bring',
    'fai mai': 'said/told',
    "ta'u atu": 'told',
    'faailoa atu': 'declared',
    'fai atu': 'said to',
    'fetalai mai': 'said',
    'fetalai atu': 'said to',
    'silasila atu': 'looked',
    'silasila mai': 'looked',
    'tu mai': 'stood',
    'tu atu': 'stood',
    'nofo mai': 'dwelt',
    'tuu atu': 'placed',
    'tuu mai': 'placed',
    'aumai': 'bring',
    'au mai': 'bring',
    'au atu': 'take',
    # "e fai ma" = "to be / to be appointed as"
    'e fai ma': 'to be',
    'fai ma': 'to be',
    # "o lea" = "therefore"
    'o lea': 'therefore',
    # "i le aiga o" = "in the family of" (possessive)
    'i le aiga o': "in the family of",
    # Romans 1:4+
    'toe tu mai': 'resurrection',
    'nai': 'from',
    'e ua oti': 'the dead',
    'ma le faiva o le aposetolo': 'and the office of the apostle',
    # "ina ia" = purpose/intention compound particle
    'ina ia': 'so that',
    'ina ia iu ina anaana': 'so that he may attain for his own sake',
    # Romans 1:3-4 (Hebrew-aligned)
    'i lona alo': 'concerning his Son',
    'o le faasinotonuina mai': 'the designation',
    'faasinotonuina mai': 'declared',
    'faasinotonuina': 'declared',
    'ia ma le mana': 'with power',
    'i la le agaga e paia lea': 'according to the Spirit of holiness',
    'i la le agaga': 'according to the spirit',
    'e paia lea': 'of holiness',
    'agaga paia': 'Holy Spirit',
    # Romans 1:6
    'e i ai foi outou': 'among whom are you also',
    # Romans 1:7
    "o la'u tusi lenei": 'this letter',
    "o la\u2018u tusi lenei": 'this letter',
    'outou uma lava': 'all of you',
    'le alofa tunoa ma le manuia': 'grace and peace',
    'ma le manuia': 'and peace',
    'manuia': 'peace',
    'alofaina': 'beloved',
    'ua alofaina': 'beloved',
    'atoa ma le alii': 'and the Lord',
    'atoa ma': 'and',
    "lo tatou tam\u0101": 'our Father',
    'lo tatou tama': 'our Father',
    # Romans 1:5 continued
    'i le faatuatua o nuu uma lava': 'in the faith of all the people',
    'ona o lona suafa': 'because of his name',
    'ona o': 'because of',
    # Scripture terms - KJV aligned
    'tagata paia': 'saints',
    "au paia": 'saints',
    "'au paia": 'saints',
    # "o e" = relative pronoun "who"
    'o e': 'who',
    'o e ua valaauina': 'who were called',
    # "o le a" / "o le 'a" = future tense marker OR "what"
    "o le a": 'what',
    "o le 'a": 'what',
    "o le \u02bba": 'what',
    "o le \u2018a": 'what',

    # "na/ua ia [verb] atu" — passive/dative: "it was [verb]ed"
    # Verb + dative patterns
    'o ia o se tagata': 'to him he is a',
    "na ia fa'amatala atu": 'he explained',
    "na ia fa\u02bbamatala atu": 'he explained',
    "na ia fa'ailoa atu": 'he declared',
    "na ia fa\u02bbailoa atu": 'he declared',
    "na ia fai atu": 'he said',
    "na ia fai mai": 'he told',
    "ua ia fai atu": 'he said',
    "ua ia fai mai": 'he told',
    "na ia ta'u atu": 'he told',
    "na ia ta\u02bbu atu": 'he told',
    "ua ia ta'u atu": 'he told',

    # ============================================================
    # High-frequency phrases across ALL standard works
    # ============================================================
    # Narrative connectors (appear thousands of times)
    'ua faapea mai': 'saying',
    'ua faapea atu': 'saying',
    'ua faapea': 'saying',
    'sa faapea': 'saying',
    'o loo faapea': 'thus',
    'o loo faapea ona fetalai mai o le alii': 'thus saith the Lord',
    'o loo faapea ona fetalai mai o ieova': 'thus saith the LORD',
    'o loo faapea ona fetalai mai o le alii o ieova': 'thus saith the Lord GOD',
    'ua fetalai mai o le alii': 'saith the Lord',
    'ua fetalai mai ai le alii o ieova': 'saith the Lord GOD',
    'o le mea lea': 'therefore/wherefore',
    'ma o lenei': 'and now',
    'sa oo': 'it came to pass',
    'sa oo ina': 'it came to pass that',
    'ua oo': 'it came to pass',
    'e oo': 'it shall come to pass',
    'ina ia mafai': 'that it might be',
    'e moni': 'verily/truly',
    'e moni lava': 'verily I say',

    # Prophet/God speech patterns
    'ou te fai atu ia te outou': 'I say unto you',
    'ua fetalai mai Ieova': 'the LORD said',
    'ua fetalai mai le Alii': 'the Lord said',
    'ona fetalai mai lea o Ieova': 'and the LORD said',
    'ona fetalai mai lea o le Alii': 'and the Lord said',
    'ua fetalai mai foi Ieova ia Mose': 'and the LORD spake unto Moses',
    'Ieova e': 'O LORD',

    # Pronouns in context
    'ia te outou': 'unto you',
    'ia te au': 'unto me',
    'ia te oe': 'unto thee',
    'ia te i latou': 'unto them',
    'i o outou luma': 'before you',
    'i ona luma': 'before him',
    'i ou luma': 'before thee',
    "i o'u luma": 'before me',
    'mo outou': 'for you',
    'mo outou agaga': 'for your souls',
    'mo i latou': 'for them',
    'i o latou luma': 'before them',

    # Possessives
    'a Isaraelu': 'of Israel',
    'a Ieova': 'of the LORD',
    'a le Atua': 'of God',
    'o le Alii': 'of the Lord',
    'a Ieova lou Atua': 'of the LORD thy God',

    # Common verb phrases
    'ua uma': 'it was finished',
    'e tatau': 'it is fitting/ought',
    'e mafai': 'it is possible/can',
    'e uiga': 'concerning',
    'e faavavau': 'forever/everlasting',
    'e faavavau lava': 'forever and ever',

    # Place/direction
    'i le vao': 'in the wilderness',
    'i Ierusalema': 'in Jerusalem',
    'i le nuu': 'in the land',
    'i le laueleele': 'in the earth',
    'i le lalolagi': 'in the world',
    'i le lagi': 'in heaven',
    'i le afi': 'in the fire',
    'i luma o Ieova': 'before the LORD',
    'i luma o le Alii': 'before the Lord',
    'i le itu': 'on the side',

    # Religious terms
    'le fanauga a Isaraelu': 'the children of Israel',
    'fanauga a Isaraelu': 'children of Israel',
    'le aiga o Isaraelu': 'the house of Israel',
    'aiga o Isaraelu': 'house of Israel',
    'le Agaga Paia': 'the Holy Spirit',
    'le Alo o le Atua': 'the Son of God',
    'le Alo o le Tagata': 'the Son of Man',
    'le malo o le Atua': 'the kingdom of God',
    'le malo o le lagi': 'the kingdom of heaven',
    'le fata faitaulaga': 'the altar',
    'fata faitaulaga': 'altar',
    'le ositaulaga sili': 'the high priest',
    'le taulaga mu': 'the burnt offering',
    'taulaga mu': 'burnt offering',

    # BOM specific
    'sa nifaē': 'thus Nephi',
    'sa lamanā': 'thus Laman',

    # Common multi-word expressions (high-impact fixes)
    'leoleo mamoe': 'shepherd',
    'lo\'u leoleo mamoe': 'my shepherd',
    'fata faitaulaga': 'altar',
    'le fata faitaulaga': 'the altar',
    'i luga o le fata faitaulaga': 'upon the altar',
    'taulaga mu': 'burnt offering',
    'le taulaga mu': 'the burnt offering',
    'le ola o le tino': 'the life of the flesh',
    'ola o le tino': 'life of the flesh',
    'e fai a\'i le togiola': 'to make atonement',
    'e fai a\'i': 'to make',
    'fai a\'i': 'thereby',
    "a'i": 'thereby',
    'le togiola mo outou agaga': 'atonement for your souls',
    'togiola mo outou agaga': 'atonement for your souls',
    'le agaga o le tamā': 'the soul of the father',
    'le agaga o le atalii': 'the soul of the son',
    'o le agaga e agasala': 'the soul that sins',
    'e oti ia': 'shall die',
    'solitulafono': 'transgressions',
    'amio leaga': 'iniquity/wickedness',
    'i luga o': 'upon',
    'i lalo o': 'under',
    'i totonu o': 'in the midst of',
    'i tua o': 'behind',
    'i luma o': 'before',
    'i fafo o': 'outside of',
    'o le ola': 'the life',
    'le ola': 'the life',
    'e leai se': 'there is no',
    'ua leai se': 'there was no',
    'e leai se mea': 'there is nothing',
    'ua leai': 'there was not',
    'e leai': 'there is not',

    # Possessive patterns
    'o lo\'u': 'my',
    'o lou': 'your',
    'o lona': 'his/her',
    'o lo latou': 'their',
    'o lo tatou': 'our',
    'o lo matou': 'our (excl)',

    # Common verbal expressions
    'ua ou tuuina atu': 'I have given',
    'ou te tuuina atu': 'I will give',
    'ua tuuina atu': 'was given',
    'e tuuina atu': 'shall be given',
    'ua ia tuuina atu': 'he gave',
    'na ia tuuina atu': 'he gave',
    'ua ia faia': 'he made/did',
    'na ia faia': 'he made/did',
    'ua latou faia': 'they did',
    'na latou faia': 'they did',
    'ua ia fai mai': 'he said',
    'ua ia fai atu': 'he said to',
    'o ia te ia lava': 'himself',
    'ia te ia lava': 'himself',

    # Isaiah 53 specific
    'ua manua o ia': 'he was wounded',
    'ua momomo o ia': 'he was crushed',
    'a tatou solitulafono': 'our transgressions',
    'a tatou amio leaga': 'our iniquities',
    'e filemu ai tatou': 'our peace',
    'ua malolo ai tatou': 'we are healed',
    'ona faalavalava': 'his stripes',

    # Psalms common
    'e leai se mea ou te mativa ai': 'I shall not want',
    'o lo\'u leoleo mamoe o ia': 'he is my shepherd',

    # Leviticus vocabulary (multi-word phrases)
    'faleie': 'tent',
    'fale fetafai': 'tabernacle',
    'le fale fetafai o le faapotopotoga': 'the tabernacle of the congregation',
    'fale fetafai o le faapotopotoga': 'tabernacle of the congregation',
    'i le faitotoa o le fale fetafai o le faapotopotoga': 'at the entrance of the tabernacle of the congregation',
    'e fai ma mea manogi lelei': 'for a sweet savour',
    'mea manogi lelei': 'sweet savour',
    'e sausauina foi e le faitaulaga': 'also sprinkled by the priest',
    'e susunu foi le ga\'o': 'also burned up is the fat',
    'le fata faitaulaga o ieova': 'the altar of Jehovah',
    'i luga o le fata faitaulaga o ieova': 'upon the altar of Jehovah',

    # Lev 17:7 phrases
    'sa latou mulimuli atu ai e mulilulua ai': 'after whom they have gone a whoring',
    'latou te le toe faia foi a latou taulaga i aitu': 'and they shall no more offer their sacrifices unto devils',
    'o le tulafono lena e faavavau ia i latou': 'this shall be a statute forever unto them',

    # Generation phrases
    'i o latou tupulaga amuli': 'throughout their generations',
    'o latou tupulaga amuli': 'their generations to come',
    'tupulaga amuli': 'generations to come',
    'i o outou tupulaga amuli': 'throughout your generations',

    # Leviticus 17:11 last phrase
    "auā o le toto o le mea lava lea e fai a'i le togiola mo outou agaga": 'for it is the blood that makes atonement for your souls',

    # Ezekiel 18:4 phrases
    'o agaga uma': 'all souls',
    "o o'u lava": 'are mine',
    'e pei o le agaga o le tamā': 'as the soul of the father',
    'e faapea foi le agaga o le atalii': 'so also the soul of the son',
    "ona fai mo'u": 'is mine',
}

# Now build the phrase pairs set (must be after WHOLE_PHRASES is defined)
_PHRASE_PAIRS = _build_phrase_pairs()


def gloss_phrase(phrase_text):
    """
    Generate an English gloss for a Samoan phrase.
    Uses dictionary lookups and grammatical patterns.
    """
    words = phrase_text.split()
    clean_words = [w.strip('.,;:!?\u201c\u201d\u201e()') for w in words]

    # Check for common whole-phrase patterns first
    phrase_lower = phrase_text.lower().strip('.,;:!?() \u201c\u201d')

    # Exact whole-phrase match (with apostrophe normalization)
    phrase_norm = phrase_lower.replace('\u02bb', "'").replace('\u2018', "'").replace('\u2019', "'").replace('\u02bc', "'")
    if phrase_lower in WHOLE_PHRASES:
        return WHOLE_PHRASES[phrase_lower]
    if phrase_norm in WHOLE_PHRASES:
        return WHOLE_PHRASES[phrase_norm]

    # ---- Greedy sub-phrase matching ----
    # Try to match known phrases from left to right within the chunk
    clean_lower = [w.lower() for w in clean_words]
    i = 0
    glosses = []
    while i < len(clean_lower):
        matched = False
        # Try longest sub-phrase first (up to 8 words)
        for length in range(min(8, len(clean_lower) - i), 1, -1):
            sub = ' '.join(clean_lower[i:i+length])
            sub_norm = sub.replace('\u02bb', "'").replace('\u2018', "'").replace('\u2019', "'").replace('\u02bc', "'")
            match_key = sub if sub in WHOLE_PHRASES else (sub_norm if sub_norm in WHOLE_PHRASES else None)
            if match_key:
                glosses.append(WHOLE_PHRASES[match_key])
                i += length
                matched = True
                break
        if matched:
            continue
        # No sub-phrase match — fall through to word-level glossing below
        break

    # If we consumed all words via sub-phrase matching, return
    if i >= len(clean_lower):
        result = ' '.join(glosses)
        result = re.sub(r'\s+', ' ', result).strip()
        return result

    # If we partially matched, gloss the rest word-by-word
    # Reset if we didn't match anything at all
    if i == 0:
        glosses = []
    # Process remaining words starting from index i
    skip_next = False
    _skip_count = 0
    start_i = i

    for idx in range(start_i, len(clean_words)):
        raw = words[idx]
        clean = clean_words[idx]
        # Adjust relative position for "phrase start" checks
        pos_in_remainder = idx - start_i

        if skip_next:
            skip_next = False
            continue
        if _skip_count > 0:
            _skip_count -= 1
            continue

        cl = clean.lower()

        # "o le a" → future tense "will" when followed by a verb (not article/noun)
        # Must check BEFORE sub-phrase matching (which would catch it as "what")
        if cl == 'o' and idx + 2 < len(clean_words):
            next1 = clean_words[idx+1].lower()
            next2 = clean_words[idx+2].lower().replace('\u02bb', "'").replace('\u02bc', "'")
            if next1 == 'le' and next2 == 'a':
                # If followed by a non-article word → future tense "will"
                if idx + 3 < len(clean_words):
                    next3 = clean_words[idx+3].lower()
                    if next3 not in ('le', 'lo', 'la', 'se', 'ni', 'o', 'i'):
                        glosses.append('will')
                        _skip_count = 2  # skip "le" and "a"
                        continue
                # else: "o le a" at end or before article → "what" (handled by sub-phrase)

        # --- Try 2-4 word compound phrase match from WHOLE_PHRASES ---
        _sub_found = False
        for _slen in range(min(4, len(clean_words) - idx), 1, -1):
            if _slen <= 1:
                break
            _sub = ' '.join(cw.lower() for cw in clean_words[idx:idx+_slen])
            _sub_n = _sub.replace('\u02bb', "'").replace('\u02bc', "'").replace('\u2018', "'").replace('\u2019', "'")
            _mk = _sub if _sub in WHOLE_PHRASES else (_sub_n if _sub_n in WHOLE_PHRASES else None)
            if _mk:
                glosses.append(WHOLE_PHRASES[_mk])
                _skip_count = _slen - 1
                _sub_found = True
                break
        if _sub_found:
            continue

        # "la le" → "the" (article compound)
        if cl == 'la' and idx + 1 < len(clean_words) and clean_words[idx+1].lower() == 'le':
            glosses.append('the')
            skip_next = True
            continue

        # "o le" → "the" (predicate marker + article)
        if cl == 'o' and idx + 1 < len(clean_words) and clean_words[idx+1].lower() == 'le':
            glosses.append('the')
            skip_next = True
            continue

        # "o le Atua" patterns — "o" as predicate marker before article
        if cl == 'o' and idx + 1 < len(clean_words) and clean_words[idx+1].lower() in ('le', 'lo', 'la', 'se'):
            continue  # skip the 'o', will get article next

        # "e" particle — meaning depends on context
        if cl == 'e':
            if idx + 1 < len(clean_words):
                next_cl = clean_words[idx+1].lower()
                # "e le" → "by the" (agent)
                if next_cl == 'le':
                    glosses.append('by the')
                    skip_next = True
                    continue
                # "e ia" → "by him" (agent + pronoun)
                if next_cl == 'ia':
                    glosses.append('by him')
                    skip_next = True
                    continue
                # "e ana" → "by his" (agent + possessive)
                if next_cl == 'ana':
                    glosses.append('by his')
                    skip_next = True
                    continue
                # "e" before a verb → "to" (purpose/infinitive)
                next_g = lookup_word(clean_words[idx+1])
                if next_g and next_g not in FUNC_WORDS.values():
                    glosses.append('to')
                    continue
            glosses.append('by')
            continue

        # "i le" → "in the"
        if cl == 'i' and idx + 1 < len(clean_words) and clean_words[idx+1].lower() in ('le', 'lo'):
            glosses.append('in the')
            skip_next = True
            continue

        # "i ai" → "therein"
        if cl == 'i' and idx + 1 < len(clean_words) and clean_words[idx+1].lower() == 'ai':
            glosses.append('therein')
            skip_next = True
            continue

        # "ma le" → "and the"
        if cl == 'ma' and idx + 1 < len(clean_words) and clean_words[idx+1].lower() in ('le', 'lo'):
            glosses.append('and the')
            skip_next = True
            continue

        # "ia te" → "unto"
        if cl == 'ia' and idx + 1 < len(clean_words) and clean_words[idx+1].lower() == 'te':
            glosses.append('unto')
            skip_next = True
            continue

        # "o a'u" → "I am" (first person pronoun predicate) — handle all apostrophe variants
        if cl == 'o' and idx + 1 < len(clean_words):
            next_norm = clean_words[idx+1].lower().replace('\u02bb', "'").replace('\u2018', "'").replace('\u2019', "'").replace('\u02bc', "'")
            if next_norm in ("a'u", "au"):
                glosses.append('I am')
                skip_next = True
                continue

        # "o ia" → "he/it"
        if cl == 'o' and idx + 1 < len(clean_words) and clean_words[idx+1].lower() == 'ia':
            glosses.append('he/it')
            skip_next = True
            continue

        # "i laua" / "i latou" → "them"
        if cl == 'i' and idx + 1 < len(clean_words) and clean_words[idx+1].lower() in ('laua', 'latou'):
            glosses.append('them')
            skip_next = True
            continue

        # Possessive patterns: "lo/la" + pronoun
        if cl in ('lo', 'la') and idx + 1 < len(clean_words):
            next_cl = clean_words[idx+1].lower()
            POSS_MAP = {
                'tatou': 'our', 'matou': 'our', 'latou': 'their',
                'outou': 'your', 'oulua': 'your', 'laua': 'their',
            }
            if next_cl in POSS_MAP:
                glosses.append(POSS_MAP[next_cl])
                skip_next = True
                continue

        # "o iai" → "there is/are"
        if cl == 'o' and idx + 1 < len(clean_words) and clean_words[idx+1].lower() == 'iai':
            glosses.append('there is')
            skip_next = True
            continue

        # Tense markers — skip them in gloss (implicit in English)
        # "na te [verb]" = pronoun "he/she/it" (not past tense marker)
        if cl == 'na' and idx + 1 < len(clean_words):
            next_cl = clean_words[idx+1].lower().strip('.,;:!?()\u201c\u201d\u201e')
            if next_cl == 'te':
                glosses.append('he/she/it')
                continue
        if cl in ('ua', 'na', 'sa', "ole'a", "ole\u02bba", "olo'o", "olo\u02bbo"):
            continue

        if cl == 'ona' and pos_in_remainder == 0:
            glosses.append('and')
            continue

        # Common particles — skip in gloss
        if cl in ('ai', "a'i", 'lea', 'te'):
            continue

        # "o" as subject/predicate marker — skip
        if cl == 'o':
            continue

        # "a" before proper noun → possessive "of" (not conjunction "but")
        if cl == 'a' and idx + 1 < len(clean_words):
            next_raw = words[idx + 1].strip('.,;:!?()\u201c\u201d\u201e\u2018\u2019')
            if next_raw and next_raw[0].isupper():
                glosses.append('of')
                continue

        # "pe" → "whether" (subordinating conjunction in clauses)
        if cl == 'pe':
            glosses.append('whether')
            continue

        # Dictionary lookup
        g = lookup_word(clean)
        if g and not g.startswith('('):
            glosses.append(g)
        elif g and g.startswith('('):
            # Skip grammatical markers like (past), (perf), (dir)
            continue
        else:
            # Unknown word — use the Samoan word itself in the gloss
            glosses.append(clean.lower())

    result = ' '.join(glosses)
    # Clean up
    result = re.sub(r'\s+', ' ', result).strip()
    # Use first option from slash alternatives for cleaner output
    result = re.sub(r'(\w+)/\w+(?:/\w+)*', r'\1', result)
    # Clean up double spaces
    result = re.sub(r'\s+', ' ', result).strip()
    return result


def split_chunk_by_subphrases(phrase_text):
    """
    Try to split a chunk into multiple sub-phrases using WHOLE_PHRASES.
    Returns list of (samoan_text, english_gloss) tuples.
    If no sub-phrase splitting is possible, returns None.
    """
    words = phrase_text.split()
    clean_words = [w.strip('.,;:!?\u201c\u201d\u201e()').lower() for w in words]

    if len(clean_words) <= 1:
        return None

    # Greedy left-to-right sub-phrase matching
    # When no match found at position, collect unmatched words and keep trying
    parts = []
    matched_count = 0
    i = 0
    unmatched_buffer = []  # words not yet matched to a known phrase

    while i < len(clean_words):
        matched = False
        for length in range(min(8, len(clean_words) - i), 1, -1):
            sub = ' '.join(clean_words[i:i+length])
            # Normalize apostrophes for matching
            sub_norm = sub.replace('\u02bb', "'").replace('\u2018', "'").replace('\u2019', "'").replace('\u02bc', "'")
            match_key = sub if sub in WHOLE_PHRASES else (sub_norm if sub_norm in WHOLE_PHRASES else None)
            if match_key:
                # Flush any unmatched buffer as its own chunk
                if unmatched_buffer:
                    buf_display = ' '.join(unmatched_buffer)
                    buf_gloss = gloss_phrase(buf_display)
                    if not buf_gloss:
                        buf_gloss = buf_display.lower()
                    parts.append((buf_display, buf_gloss))
                    unmatched_buffer = []
                # Add the matched sub-phrase
                display = ' '.join(words[i:i+length])
                parts.append((display, WHOLE_PHRASES[match_key]))
                i += length
                matched = True
                matched_count += 1
                break
        if not matched:
            # No match at this position — buffer this word and move on
            unmatched_buffer.append(words[i])
            i += 1

    # Flush remaining unmatched buffer
    if unmatched_buffer:
        buf_display = ' '.join(unmatched_buffer)
        buf_gloss = gloss_phrase(buf_display)
        if not buf_gloss:
            buf_gloss = buf_display.lower()
        parts.append((buf_display, buf_gloss))

    # Only return if we found at least 1 known sub-phrase AND it splits into 2+ parts
    if matched_count >= 1 and len(parts) >= 2:
        return parts

    return None


def _split_at_punctuation(text):
    """Split text at commas, semicolons, colons, and periods (keeping punctuation with preceding segment)."""
    parts = re.split(r'(?<=[,;:.])\s+', text)
    return [p.strip() for p in parts if p.strip()]


def _merge_to_align(sam_segs, eng_segs):
    """
    When Samoan has more segments than KJV (or vice versa),
    merge the side with more segments to match the smaller count,
    then pair them. Always produces len(min(sam,eng)) pairs with no empty glosses.
    """
    if len(sam_segs) == len(eng_segs):
        return [[s, e] for s, e in zip(sam_segs, eng_segs)]

    if len(sam_segs) > len(eng_segs):
        # More Samoan segments — merge consecutive Samoan segs to match KJV count
        target = len(eng_segs)
        merged_sam = []
        # Distribute sam_segs into target groups
        for i in range(target):
            start = round(i * len(sam_segs) / target)
            end = round((i + 1) * len(sam_segs) / target)
            merged_sam.append(' '.join(sam_segs[start:end]))
        return [[s, e] for s, e in zip(merged_sam, eng_segs)]
    else:
        # More KJV segments — merge consecutive KJV segs to match Samoan count
        target = len(sam_segs)
        merged_eng = []
        for i in range(target):
            start = round(i * len(eng_segs) / target)
            end = round((i + 1) * len(eng_segs) / target)
            merged_eng.append(' '.join(eng_segs[start:end]))
        return [[s, e] for s, e in zip(sam_segs, merged_eng)]


def annotate_verse(verse_key, samoan_text, english_text=""):
    """
    Generate phrase annotations for a verse.
    Returns list of [samoan_phrase, english_gloss] pairs.
    First splits at punctuation, then applies grammatical chunking
    to produce ~2-4 word interlinear groups.
    """
    if not samoan_text:
        return []

    # First split at punctuation boundaries (commas, semicolons, colons, periods)
    punct_segments = _split_at_punctuation(samoan_text)
    if len(punct_segments) <= 1:
        punct_segments = [samoan_text]

    result = []
    for segment in punct_segments:
        # Apply grammatical chunking to each punctuation segment
        chunks = chunk_grammatical(segment)
        for chunk in chunks:
            gloss = gloss_phrase(chunk)
            if not gloss:
                gloss = chunk.lower()
            result.append([chunk, gloss])
    return result


# ============================================================
# Main: generate annotations for all verses
# ============================================================
def main():
    sys.stdout = open(sys.stdout.fileno(), mode='w', encoding='utf-8', buffering=1)

    # Regenerate ALL annotations from scratch
    phrase_path = os.path.join(base, '_phrase_annotations.json')
    annotations = {}

    # Process all verses
    total = 0
    auto = 0

    for key, samoan_text in sorted(samoan_verses.items()):
        eng = english_verses.get(key, '')
        phrases = annotate_verse(key, samoan_text, eng)

        if phrases:
            annotations[key] = phrases
            auto += 1

        total += 1
        if total % 5000 == 0:
            print(f"  Processed {total} verses ({auto} auto-annotated)...")

    print(f"\nTotal verses processed: {total}")
    print(f"Auto-annotated: {auto}")
    print(f"Regenerated from scratch (no preserved entries)")
    print(f"Total annotations: {len(annotations)}")

    # ============================================================
    # Manual overrides for specific verse glosses
    # ============================================================
    MANUAL_GLOSS_OVERRIDES = {
        'Esther|3|4': {
            "auā na ia fa\u02bbamatala atu": 'he explained',
            "auā na ia fa'amatala atu": 'he explained',
            'o ia': 'to him',
            'o se tagata Iuta.': 'he is a Jew',
            'pe o le a tumau': 'whether | will | endure',
            'Na fai atu pea': 'they continually said',
            'i latou ia te ia': 'to him',
            'i aso uma,': 'every day',
            'ae na lē tali': 'but he did not',
            'mai o ia.': 'respond',
            'O lea': 'therefore',
            'na latou fa\u02bbailoa atu ai': 'they declared',
            "na latou fa'ailoa atu ai": 'they declared',
            'ia Hamana,': 'to Haman',
        },
        '1 Nephi|1|1': {
            'na fanaua': 'born to',
            'e matua lelei ,': 'goodly parents',
            "na aoaoina ai a'u": 'I was taught',
            'teisi i le poto uma': 'somewhat in all the knowledge',
            "o lo'u tamā;": 'of my father',
            'ma ona': 'therefore',
            'ua ou vaai': 'I saw',
            'i le gasologa': 'in the course',
            "o o'u aso,": 'of my days',
            'o lea ou te faia ai': 'therefore I make',
            "o a'u taualumaga": 'my proceedings',
            "i o'u aso.": 'in my days',
        },
        '1 Nephi|1|2': {
            'ou te faia': 'I make',
            'a tagata Aikupito.': 'Egyptian',
        },
        '1 Nephi|1|3': {
            'Ma ua ou iloa': 'I know',
            "i lo'u lava lima;": 'by my own hand',
            "e tusa ma lo'u iloa.": 'according to my knowledge',
        },
        '1 Nephi|1|4': {
            'i ona aso uma);': 'in all his days',
            'na o mai ai perofeta': 'there came prophets',
            'e toatele,': 'many',
            'ma vavalo atu': 'and prophesied',
            'i tagata': 'to the people',
            'e faapea': 'saying',
            'latou salamo,': 'they repent',
            'po o': 'all',
            'o le a faaumatia': 'will be destroyed',
            'le aai tele o Ierusalema .': 'the great city | Jerusalem',
        },
        '1 Nephi|1|5': {
            "ua alu atu lo'u tamā,": 'my father went forth',
            'sa tatalo atu o ia': 'he prayed',
            'ma lona loto atoa lava,': 'with his whole heart',
            'mo ona tagata.': 'for his people',
        },
        '1 Nephi|1|6': {
            "a'o tatalo atu o ia": 'while he prayed',
            'se afi faaniutu': 'a pillar of fire',
            'ma ua nofo': 'and dwelt',
            'i luga': 'upon',
            'o se papa': 'a rock',
            'i ona luma;': 'before him',
            'ma sa vaaia': 'and he saw',
            'ma faalogoina e ia': 'and he heard',
            'mea e tele;': 'great things',
            'sa ia vaaia': 'he saw',
            'ma faalogoina,': 'and heard',
            'sa galulu': 'quaking',
            'ma tetemu tele ai o ia.': 'and trembling exceedingly | upon him',
        },
        '1 Nephi|1|7': {
            "ma sa ia faapa'\u016b o ia": 'and he fell',
            'lava i lona moega,': 'upon his bed',
            'ona ua lofituina o ia': 'therefore | being overcome',
            'i le Agaga': 'by the Spirit',
            'ma mea': 'of things',
            'na ia vaaia.': 'which he saw',
        },
        '1 Nephi|1|8': {
            "Ma a'o faapea ona": 'and while he was thus',
            'lofituina o ia': 'he was overcome',
            'i le Agaga,': 'by the Spirit',
            'sa segia o ia': 'he was carried away',
            'i se faaaliga vaaia,': 'in a vision',
            'sa vaai ai lava o ia': 'he indeed saw',
            'ua avanoa': 'the heaven',
            'le lagi ,': 'opened',
            'sa vaai o ia': 'he saw',
            'i le Atua o afio': 'God | sitting',
            'i lona nofoalii,': 'upon his throne',
            'ua siosiomia': 'surrounded',
            "i 'au agelu": 'by his angels',
            "e l\u0113 masino": 'multitude',
            'e peiseai o pepese': 'in the attitude of singing',
            'ma vivii atu': 'praising',
            'ma sa manatu o ia': 'and he thought',
            'i lo latou Atua.': 'their God',
        },
        '1 Nephi|1|9': {
            'vaai atu o ia': 'he looked',
            'i se Toatasi': 'One',
            'ua afio ifo': 'descending',
            'ma sa vaai o ia': 'and he saw',
            'ua sili atu lona pupula': 'was greater | his brightness',
            'nai lo le la': 'more than the sun',
            'i le aoauli.': 'at noon',
        },
        '1 Nephi|1|10': {
            'Ma sa vaaia foi': 'and he also saw',
            'e ia ni isi': 'others',
            'e toasefululua o mulimuli atu': 'twelve | following',
            'ia te ia,': 'him',
            'ma o lo latou pupula': 'and their brightness',
            'sa sili atu i lo': 'exceeded',
            'fetu o le vanimonimo.': 'stars of the firmament',
        },
        '1 Nephi|1|11': {
            'Ma sa latou afifio ifo': 'and they came down',
            'i lalo': 'below',
            'ma maliliu atu': 'and they went forth',
            'i luga': 'upon',
            'o le lalolagi;': 'the earth',
            'ma sa afio': 'and there came',
            "mai l\u0113": 'the',
            'na muamua': 'first',
            'ma tu': 'and stood',
            'i luma': 'before',
            "o lo'u tam\u0101,": 'my father',
            'ma tuu mai ia te ia': 'and gave unto him',
            'ma fetalai mai ia te ia': 'and said | unto him',
            'se tusi ,': 'a book',
            'faitau e ia.': 'read it',
        },
        '1 Nephi|1|12': {
            'ua faitau o ia,': 'as he read',
            'sa tumu o ia': 'he was filled',
            'i le Agaga': 'by the Spirit',
        },
        '1 Nephi|1|13': {
            'Ma sa faitau o ia,': 'and it read',
            'fai mai:': 'saying',
            'Oi talofa,': 'wo',
            'oi talofa,': 'wo',
            'aua ua Ou vaai': 'for I see',
            'i au mea inosia!': 'your iniquities',
            'ma e tele mea': 'and great things',
            'sa faitau': 'read',
            "i ai lo'u tam\u0101": 'it | my father',
            "e uiga ia Ierusalema \u2014e faapea": 'concerning Jerusalem | that',
            'o le a faaumatiaina,': 'it shall be destroyed',
            'ma e o nonofo ai;': 'and the inhabitants thereof',
            'e toatele': 'many',
            'o le a fano': 'shall perish',
            'i le pelu,': 'by the sword',
            'ma e toatele foi': 'and many also',
            'o le a ave faatagataotaua': 'will be taken | captive',
            'i Papelonia.': 'into Babylon',
        },
        '1 Nephi|1|14': {
            "faitau ma vaai lo'u tam\u0101": 'reading and seeing | my father',
            'i le tele o mea tetele': 'many great',
            'ma le ofoofogia,': 'and marvelous things',
            'e tele mea': 'many things',
            'sa alaga atu e ia': 'he cried out',
            'i le Alii;': 'to the Lord',
            'e pei o le:': 'such as',
            'Ua silisili': 'great',
            'ma ofoofogia au galuega,': 'and marvelous | your works',
            'Le Alii e': 'O Lord',
            'le Atua Malosi Aoao!' : 'God Almighty',
            'Ua maualug\u0101': 'is lifted high',
            'i le lagi lou nofoalii,': 'in the heaven | thy throne',
            'ma o lou mana,': 'and your power',
            'ma lou alofa mutimutivale': 'and your mercy',
            'ua i ai': 'is',
            'i luga o': 'upon',
            'e uma o nonofo': 'all who dwell',
            'i le lalolagi;': 'on the earth',
            'ona e te alofa mutimutivale,': 'because of your mercy',
            'e te l\u0113 tuua': 'you will not suffer',
            'i latou': 'them',
            'o e': 'who',
            'e o mai ia te oe': 'come | unto you',
            'ia fano': 'to perish',
        },
        '1 Nephi|1|15': {
            'Ma sa faapea': 'after this manner',
            'le ituaiga o gagana': 'of language',
            "a lo'u tam\u0101": 'my father',
            'i le viiga': 'in the praising',
            'o lona Atua;': 'of his God',
            'ona sa olioli lona agaga,': 'then his soul rejoiced',
            'ma sa tumu lona loto atoa,': 'and his whole heart was filled',
            'ona o mea': 'because of the things',
            'sa vaaia e ia,': 'that he saw',
            'na faaali mai': 'had shown',
        },
        '1 Nephi|1|16': {
            'Ma o lenei,': 'and now',
            "o a'u,": 'I',
            'o Nifae,': 'Nephi',
            'ou te l\u0113 faia': 'I do not make',
            'se tala': 'a complete',
            'atoa o mea': 'record | of things',
            'ua tusia': 'that were written',
            "e lo'u tam\u0101,": 'by my father',
            'ona ua tusia e ia': 'because he wrote',
            'le tele o mea': 'many things',
            'sa ia vaaia': 'which he saw',
            'i faaaliga': 'in visions',
            'ma miti;': 'and dreams',
            'ma ua tusia foi': 'and he also had written',
            'e ia le tele o mea': 'many things',
            'sa ia vavalo': 'that he prophesied',
            'ma tautala atu ai': 'and spoke unto',
            'i ana fanau,': 'his children',
            'o le a ou l\u0113 faia': 'I do not make',
            'i ai': 'thereof',
            'se tala': 'a complete',
            'atoa.': 'record',
        },
        '1 Nephi|1|17': {
            'Ae o le a ou faia': 'but | I will make',
            'se tala': 'a record',
            "i a'u taualumaga": 'the proceedings',
            "i o'u aso.": 'in my days',
            'ou te faia': 'I make',
            'se otootoga': 'an abridgment',
            'o le talafaamaumau': 'the record',
            "a lo'u tam\u0101,": 'of my father',
            'i luga o papatusi': 'upon plates',
            'na ou faia': 'which I made',
            "i o'u lava lima;": 'with my own hands',
            'o le mea lea,': 'wherefore',
            'a uma ona': 'when I am finished',
            'ou otooto': 'abridging',
            "a lo'u tam\u0101": 'of my father',
            'ona ou faia lea': 'I will make',
            'o se tala': 'a record',
            "o lo'u lava olaga.": 'of my life',
        },
        '1 Nephi|1|18': {
            'O lea,': 'therefore',
            'ou te manao ia': 'I desire',
            'outou iloa,': 'that you will know',
            'ina ua uma ona': 'when finished',
            'faaali mai': 'revealing',
            'e le Alii': 'by the Lord',
            "i lo'u tam\u0101,": 'to my father',
            "le tele na'u\u0101 o mea ofoofogia,": 'many marvelous things',
            'e uiga': 'concerning',
            'i le faaumatiaga o Ierusalema,': 'the destruction of Jerusalem',
            'sa alu atu o ia': 'he went',
            'i tagata,': 'to the people',
            'ma amata': 'and began',
            'ona vavalo': 'to prophesy',
            'ma tautino atu ia te': 'and witness | unto',
            'i latou': 'them',
            'i mea': 'the things',
            'sa ia vaaia': 'which he saw',
            'ma faalogoina.': 'and heard',
        },
        '1 Nephi|1|19': {
            'faatauemu tagata Iutaia ia te ia': 'the Jews mocked him',
            'ona o mea': 'because of the things',
            'sa molimau atu ai o ia': 'which he did witness of',
            'e uiga ia te': 'concerning',
            'i latou;': 'them',
            'ona sa molimau moni atu': 'for he truly testified',
            'i lo latou amioleaga': 'of their sins',
            'ma a latou mea inosia;': 'and of their abominations',
            'ma sa molimau atu o ia': 'and he witnessed',
            'o mea': 'of things',
            'sa ia vaaia': 'he saw',
            'ma faalogoina,': 'and heard',
            'ma mea foi': 'and other things',
            'sa ia faitauina': 'that he read',
            'ua faaali manino': 'that clearly revealed',
            'mai ai': 'from that',
            'le afio mai': 'the coming of',
            'o se Mesia ,': 'a Messiah',
            'ma le togiolaina foi': 'and also the redemption',
            'o le lalolagi.': 'of the world',
        },
        '1 Nephi|1|20': {
            'Ma ina': 'and when',
            'ua faalogo mai tagata Iutaia': 'the Jews heard',
            'i nei mea': 'these things',
            'sa latou feitai ia te ia;': 'they were angry with him',
            'e pei lava ona': 'even as',
            'sa latou faia': 'they did unto',
            'i perofeta anamua,': 'the prophets of old',
            'o e': 'who',
            'na latou tutuli esea,': 'they cast out',
            'ma fetogi': 'and stoned',
            'i maa,': 'with stones',
            'ma fasioti;': 'and killed',
            'ma sa latou saili foi lona ola,': 'they also sought his life',
            'ina ia latou aveeseina.': 'so they could take it away',
            'o le alofa mutimutivale agamalu': 'of the tender mercies',
            'o le Alii': 'of the Lord',
            'i luga o': 'is upon',
            'i latou uma o': 'all those',
            'e ua ia filifilia,': 'who he has chosen',
            'ona o lo latou faatuatua,': 'because of their faith',
            'i latou': 'them',
            'e faamalolosi tele ai': 'to make them mighty',
            'o le a ou faaali atu': 'I will show',
            'ia te outou': 'unto you',
            "le 'ai": 'the presence',
            'e oo lava': 'unto',
            'i le mana': 'the power',
            'e laveaiina ai.': 'of deliverance',
        },
        '1 Nephi|2|1': {
            'i se miti lava,': 'even in a dream',
            'ona o mea': 'because of the things',
            'ua e faia;': 'you have done',
            'sa e faamaoni': 'you were faithful',
            'ma tautino atu': 'and declared unto',
            'i lenei nuu mea': 'to this people',
            'na Ou poloaiina ai oe,': 'that I commanded you',
            'ua latou saili': 'they seek',
            'e aveese lou ola.': 'to take your life',
        },
        '1 Nephi|2|2': {
            "poloaiina e le Alii lo'u tamā,": 'the Lord commanded my father',
            'i se miti lava,': 'even in a dream',
            'e tatau ia te ia': 'that he should',
            'ona ave lona aiga': 'take his family',
            'ma o ese atu': 'depart',
            'i le vao.': 'the wilderness',
        },
        '1 Nephi|2|3': {
            'usiusitai o ia': 'he obeyed',
            'i le afioga': 'the word',
            'a le Alii,': 'of the Lord',
            'na faia ai e ia': 'he did',
            'poloaiina ai o ia': 'he was commanded',
            'e le Alii.': 'by the Lord',
        },
        '1 Nephi|2|4': {
            'alu ese atu o ia': 'he went out',
            'Ma sa tuu e ia': 'and he left',
            'o lona tofi,': 'of his inheritance',
            'ma ana mea taua,': 'and his precious things',
            'ma sa lē avea': 'he did not take',
            'e ia se mea,': 'a thing',
            'vagana ai lona aiga,': 'except his family',
            'ma tapenapenaga,': 'and provisions',
            'ma faleie,': 'and tents',
            'ma o ese atu': 'and they departed',
            'i le vao.': 'the wilderness',
        },
        '1 Nephi|2|5': {
            'Ma sa alu ifo o ia': 'and he came down',
            'i lalo': 'below',
            'i tafatafa o tuaoi': 'by the borders neighboring',
            'e latalata': 'near',
            'i le matafaga': 'the shore',
            'o le Sami Ulaula;': 'the Red Sea',
            'ma sa malaga o ia': 'and he traveled',
            'i tuaoi': 'in the borders',
            'e latalata lava': 'even near',
            'i le Sami Ulaula;': 'the Red Sea',
            'i le vao faatasi': 'in the wilderness',
            'ma lona aiga,': 'with his family',
            "sa i ai lo'u tinā,": 'consisting of my mother',
            'o Sarai,': 'Saraiah',
            "ma o'u uso matutua,": 'and my older brothers',
            'ma Sama.': 'and Sam',
        },
        '1 Nephi|2|6': {
            'ua mavae aso': 'days had passed',
            'e tolu talu': 'three | since',
            'ona malaga o ia': 'he traveled',
            'sa faatu e ia': 'he pitched',
            'lona faleie': 'his tent',
            'i se vanu': 'in a valley',
            'i tafatafa': 'near',
            'o se vaitafe.': 'a river',
        },
        '1 Nephi|2|7': {
            'faia e ia se fatafaitaulaga': 'he made an altar',
            'i maa ,': 'of stones',
            'ma osi ai': 'and offered on it',
            'se taulaga': 'an offering',
            'i le Alii,': 'to the Lord',
            'ma avatu': 'and offered',
            'le faafetai': 'thanks',
            'i le Alii lo matou Atua.': 'to the Lord our God',
        },
        '1 Nephi|2|8': {
            'faaigoa e ia le vaitafe,': 'he named the river',
            'ma sa tafe atu': 'as it flowed',
            'i le Sami Ulaula;': 'the Red Sea',
            'ma o le vanu': 'and the valley',
            'sa i tuaoi latalata': 'was near the borders',
            'i lona mulivai.': 'its mouth',
        },
        '1 Nephi|2|9': {
            'Ma ina': 'and when',
            "ua vaai atu lo'u tamā": 'saw my father',
            'ua tafe atu vai': 'emptied',
            'o le vaitafe': 'the water of the river',
            'i le punavai': 'in the fountain',
            'o le Sami Ulaula,': 'of the Red Sea',
            'sa tautala atu o ia': 'he spoke',
            'ia Lamana,': 'unto Laman',
            'ua fai atu:': 'saying',
            'E,': 'Oh',
            "ma'umau e": 'that you would endure',
            'pe a': 'if',
            'na mafai ona': 'could',
            'pei oe': 'like you',
            'o lenei vaitafe,': 'this river',
            'e tafe atu pea': 'to flow continually',
            'o le amiotonu uma!': 'of all righteousness!',
        },
        '1 Nephi|2|10': {
            'Ma sa tautala atu foi': 'he also spake',
            'o ia ia Lemuelu:': 'unto Lemuel',
            'E,': 'Oh',
            'pe a': 'if',
            'o lenei vanu,': 'this valley',
            'e tumau': 'to be firm',
            'ma mausali,': 'and steadfast',
            'ma lē maluelue': 'and immovable',
            'i le tausiga o poloaiga': 'in keeping the commandments',
            'a le Alii!': 'of the Lord!',
        },
        '1 Nephi|2|11': {
            'ua maaa o Lamana': 'the stiffneckedness of Laman',
            'Ma sa fai mai': 'and they said',
            'i laua': 'unto them (two)',
            'ua faia e ia': 'he did',
            'ona o mafaufauga valea': 'because of the foolish imaginations',
            'o lona loto.': 'of his heart',
        },
        '1 Nephi|2|13': {
            'E lei talitonu foi': 'they also did not believe',
            'Ma sa pei': 'and they were like',
            'o tagata Iutaia o': 'the Jews',
            'na saili': 'sought',
            'e aveese': 'to take away',
            "le ola": 'the life',
            "o lo'u tamā.": 'of my father',
        },
        'Genesis|1|1': {
            'Na faia': 'created',
            'le lagi': 'the heavens',
            'ma le lalolagi': 'and the earth',
        },
        'Genesis|1|2': {
            'Sa soona nunumi': 'was without form',
            'le lalolagi': 'the earth',
            'ma ua gaogao,': 'and void',
            'sa ufitia foi': 'was also covered',
            'le moana': 'the deep',
            'i le pouliuli;': 'with darkness',
            'na fegaoioiai foi': 'was also hovering',
            'le Agaga': 'the Spirit',
            'o le Atua': 'of God',
            'i le fogātai.': 'over the surface of the waters',
        },
        'Genesis|1|3': {
            'Ua fetalai mai': 'God said',
            'le Atua,': 'God',
        },
        'Genesis|1|4': {
            'Ua silasila atu': 'saw',
            'le Atua': 'God',
            'i le malamalama,': 'the light',
            'ona tuu eseese ai lea': 'and separated',
            'o le malamalama': 'the light',
            'ma le pouliuli.': 'from the darkness',
        },
        'Genesis|1|5': {
            'Ua faaigoa': 'called',
            'le malamalama,': 'the light',
            'O le ao;': 'Day',
            'a ua faaigoa e ia': 'and He called',
            'le pouliuli,': 'the darkness',
            'O le po.': 'Night',
            'o le uluai aso lea.': 'was the first day',
        },
        'Genesis|1|6': {
            'Ua fetalai mai foi': 'And God said',
            'le Atua,': 'God',
            'Ia i le va o vai': 'Let there be in the midst of the waters',
            'e va a\u02bbi isi vai': 'to divide the waters',
            'ma isi vai.': 'from the waters',
        },
        'Genesis|1|7': {
            'Ua faia': 'made',
            'le va nimonimo,': 'the firmament',
            'ua va a\u02bbi vai': 'and separated the waters',
            'i lalo': 'below',
            'o le vanimonimo': 'the firmament',
            'ma vai': 'from the waters',
            'i luga': 'above',
            'o le vanimonimo;': 'the firmament',
            'i le': 'in the',
        },
        'Genesis|1|8': {
            'Ua faaigoa': 'called',
            'le vanimonimo,': 'the firmament',
            'O le lagi.': 'Heaven',
            'o le aso lua lea.': 'was the second day',
        },
        'Genesis|1|9': {
            'Ua fetalai mai foi': 'And God said',
            'le Atua,': 'God',
            'Ia potopoto': 'Let be gathered',
            'i le mea': 'into place',
            'e tasi o vai': 'one | the waters',
            'i lalo': 'under',
            'o le lagi,': 'the heaven',
            'ia iloa foi': 'and let appear',
            'le eleele matutu;': 'the dry land',
        },
        'Genesis|1|10': {
            'Ua faaigoa': 'called',
            'le eleele matutu,': 'the dry land',
            'O le eleele;': 'Earth',
            'a ua faaigoa e ia': 'and He called',
            'le faapotopotoga o vai,': 'the gathering of the waters',
            'O le sami;': 'Seas',
            'ua silasila atu': 'saw',
            'i ai': 'it',
            'le Atua,': 'God',
        },
        'Genesis|1|11': {
            'Ona fetalai mai lea': 'And said',
            'o le Atua,': 'God',
            'Ia tupu': 'Let bring forth',
            "le vao mu'a": 'grass',
            'mai le eleele,': 'from the earth',
            'ma le laau afu': 'and the herb yielding',
            'e tupu': 'bearing',
            "ma ona fua,": 'seed',
            'ma le laau': 'and the tree',
            "e 'aina": 'bearing',
            "ona fua,": 'fruit',
            'e fua mai': 'yielding fruit',
            'e taitasi': 'each',
            "ma lona uiga,": 'after its kind',
            'o ia te ia': 'in itself',
            'lava o': 'indeed',
            'ona fatu': 'its seed',
            'i luga': 'upon',
            "o le eleele;": 'the earth',
        },
        'Genesis|1|12': {
            'Ona tupu mai lea': 'And the earth brought forth',
            'i le eleele': 'from the earth',
            "le vao mu'a": 'grass',
            'ma le laau afu': 'and the herb yielding',
            "e fua mai,": 'seed',
            'e taitasi': 'each',
            "ma lona uiga,": 'after its kind',
            'ma le laau': 'and the tree',
            "e 'aina": 'bearing',
            "ona fua,": 'fruit',
            'o ia te ia': 'with seed in itself',
            'lava ona': 'indeed',
            "fatu,": 'seed',
            "ma lona uiga;": 'after its kind',
            'ua silasila atu': 'saw',
            'i ai': 'it',
            'le Atua,': 'God',
        },
        'Genesis|1|13': {
            'o le aso tolu lea.': 'was the third day',
        },
        'Genesis|1|14': {
            'Ua fetalai mai foi': 'And God said',
            'le Atua,': 'God',
            'Ia iai': 'Let there be',
            'i le vanimonimo': 'in the firmament',
            'o le lagi o mea': 'of the heaven | lights',
            "e malamalama a'i,": 'for lights',
            'e iloga ai': 'to separate',
            'le ao': 'the day',
            'ma le po;': 'from the night',
            'ia fai foi': 'and let them be',
            'ma faailoga,': 'for signs',
            'ma tau,': 'and seasons',
            'ma aso,': 'and days',
            'ma tausaga.': 'and years',
        },
        'Genesis|1|15': {
            'Ma ia fai': 'And let them be',
            'ma mea': 'lights',
            "e malamalama a'i": 'for light',
            'i le vanimonimo': 'in the firmament',
            'o le lagi,': 'of the heaven',
            "e faamalamalama a'i": 'to give light upon',
            'le lalolagi;': 'the earth',
        },
        'Genesis|1|16': {
            'Ona faia lea': 'And made',
            'e le Atua o malamalama tetele': 'God | two great lights',
            'e lua;': 'two',
            'o le malamalama tele': 'the greater light',
            'e pule': 'to rule',
            'i le ao,': 'the day',
            'a o le malamalama itiiti': 'and the lesser light',
            'i le po;': 'the night',
            'ua na faia foi fetu.': 'He made the stars also',
        },
        'Genesis|1|17': {
            'Ua tuu ai': 'And set them',
            'i le vanimonimo': 'in the firmament',
            'o le lagi': 'of the heaven',
            "e faamalamalama a'i": 'to give light upon',
            'le lalolagi;': 'the earth',
        },
        'Genesis|1|18': {
            'e pule foi': 'and to rule',
            'i le ao': 'over the day',
            'ma le po,': 'and the night',
            'ma ia iloga ai': 'and to separate',
            'le malamalama': 'the light',
            'ma le pouliuli;': 'from the darkness',
            'ua silasila atu': 'saw',
            'i ai': 'it',
            'le Atua,': 'God',
        },
        'Genesis|1|19': {
            'o le aso fa lea.': 'was the fourth day',
        },
        'Genesis|1|20': {
            'Ia tupu tele le vai': 'Let the waters swarm',
            'i mea ola faatuputupu,': 'with living creatures',
            'ma manu felelei': 'and let birds',
            'e lele': 'fly',
            'i luga o le eleele': 'above the earth',
            'i le vanimonimo': 'across the firmament',
            'o le lagi.': 'of the heaven',
        },
        'Genesis|1|21': {
            'mea tetele o le sami,': 'the great sea creatures',
            'ma mea ola uma faatuputupu': 'and every living creature',
            'na tupu tele': 'that swarmed',
            'i le vai': 'in the waters',
            'ma manu uma felelei': 'and every winged bird',
        },
        'Genesis|1|22': {
            'ia i latou,': 'them',
            'Ia tupu faatuputupu': 'Be fruitful and multiply',
            'ma faatumau': 'and fill',
            'le vai i le sami,': 'the waters in the seas',
            'ma ia faatuputupu': 'and let multiply',
            'le manu': 'the birds',
            'i le eleele.': 'on the earth',
        },
        'Genesis|1|23': {
            'o le aso lona lima lea.': 'was the fifth day',
        },
        'Genesis|1|24': {
            'Ua fetalai mai foi': 'And God said',
            'le Atua,': 'God',
            'Ia tutupu meaola': 'Let the earth bring forth living creatures',
            'mai le laueleele,': 'from the earth',
            'e taitasi': 'each',
            'ma lona uiga,': 'after its kind',
            'o manu vaefa fanua,': 'livestock',
            'ma mea fetolofi,': 'and creeping things',
            'ma manu vaefa': 'and beasts',
            'o le vao,': 'of the earth',
            'ma lona uiga;': 'after its kind',
            'ua faapea lava.': 'and it was so',
        },
        'Genesis|1|25': {
            'Ua faia foi': 'And God made',
            'e le Atua o manu vaefa': 'the beasts',
            'o le vao,': 'of the earth',
            'e taitasi': 'each',
            'ma lona uiga,': 'after its kind',
            'ma manu vaefa fanua,': 'and livestock',
            'ma lona uiga;': 'after its kind',
            'atoa ma mea fetolofi uma': 'and every creeping thing',
            'i le eleele,': 'on the earth',
            'ua silasila atu': 'and God saw',
            'i ai': 'that',
            'le Atua,': 'God',
            'ua lelei.': 'it was good',
        },
        'Genesis|1|26': {
            'Ona fetalai ane lea': 'And said',
            'o le Atua,': 'God',
            'Ina tatou faia ia': 'Let us make',
            'o le tagata': 'man',
            'i lo tatou faatusa,': 'in our image',
            'ia foliga ia': 'after our likeness',
            'i tatou;': 'of us',
            'ia pule foi': 'and let them have dominion',
            'i latou': 'over',
            "i i'a": 'the fish',
            'i le sami,': 'of the sea',
            'ma manu felelei,': 'and over the birds',
            'ma manu vaefa,': 'and over the livestock',
            'ma le laueleele uma,': 'and over all the earth',
            'atoa ma mea fetolofi uma': 'and over every creeping thing',
            'e fetolofi': 'that creeps',
            'i le eleele.': 'upon the earth',
        },
        'Genesis|1|27': {
            'Ona faia lea': 'So created',
            'e le Atua': 'God',
            'o le tagata': 'man',
            'i lona faatusa,': 'in His own image',
            'o le faatusa': 'in the image',
            'o le Atua': 'of God',
            'na ia faia ai o ia;': 'He created him',
            'na faia e ia': 'He created',
            'o i laua': 'them',
            'o le tane': 'male',
            'ma le fafine.': 'and female',
        },
        'Genesis|1|28': {
            'Ua faamanuia foi': 'And God blessed',
            'e le Atua ia te': 'them',
            'i laua,': '',
            'ma ua fetalai atu': 'and God said',
            'le Atua ia te': 'unto',
            'Ia fanafanau ia,': 'Be fruitful',
            'ma ia uluola,': 'and multiply',
            'ma ia tumu ai': 'and fill',
            'le lalolagi,': 'the earth',
            'ia faatoilalo': 'and subdue',
            'i ai,': 'it',
            'ma ia pule': 'and have dominion',
            "i i'a": 'over the fish',
            'i le sami,': 'of the sea',
            'ma manu felelei,': 'and over the birds',
            'atoa ma mea ola uma': 'and over every living thing',
            'e fetolofi': 'that moves',
            'i le eleele.': 'upon the earth',
        },
        'Genesis|1|29': {
            'Ua fetalai atu foi': 'And God said',
            'le Atua,': 'God',
            'Faauta,': 'Behold',
            'ua ou foai atu ia te oulua': 'I have given you',
            'o laau afu uma': 'every herb bearing seed',
            'e tutupu': 'that grows',
            'ma o latou fua o': 'with its fruit',
            'i le fogāeleele uma lava,': 'on the face of all the earth',
            'atoa ma laau uma': 'and every tree',
            'ua iai': 'which has',
            'le fua': 'the fruit',
            'o le laau': 'of a tree',
            'e tupu': 'yielding',
            'ma ona fatu;': 'seed',
            'e ia te oulua': 'to you',
            'ia e fai': 'it shall be',
            'ma mea': 'for',
            "e 'ai.": 'food',
        },
        'Genesis|1|30': {
            'O manu vaefa uma foi': 'And to every beast',
            'o le vao,': 'of the earth',
            'ma manu felelei uma,': 'and to every bird',
            'atoa ma mea fetolofi uma': 'and to every creeping thing',
            'i le eleele,': 'on the earth',
            'o iai': 'wherein there is',
            'le ola,': 'life',
            'ua ou foai atu': 'I have given',
            'i ai o laau afu uma lauolaola': 'every green herb',
            'e fai': 'for',
            'ma mea': '',
            "e 'ai;": 'food',
            'ua faapea lava.': 'and it was so',
        },
        'Genesis|1|31': {
            'Ua silasila atu': 'And God saw',
            'le Atua': 'God',
            'i mea uma': 'everything',
            'ua na faia,': 'that He had made',
            'faauta foi,': 'and behold',
            'ua matuā lelei lava.': 'it was very good',
            'O le afiafi': 'And the evening',
            'ma le taeao': 'and the morning',
            'o le aso ono lea.': 'were the sixth day',
        },
        'Genesis|2|1': {
            'Ua uma lava ona': 'Thus were finished',
            'faia o le lagi': 'the heavens',
            'ma le lalolagi,': 'and the earth',
            'atoa foi': 'and all',
            'ma mea uma o iai.': 'the host of them',
        },
        'Genesis|2|2': {
            'Ua faauma': 'And finished',
            'e le Atua': 'God',
            'i le aso fitu lana galuega': 'on the seventh day His work',
            'na faia e ia;': 'which He had made',
            'ona malolo ai lea o ia': 'and He rested',
            'i le aso fitu': 'on the seventh day',
            'i lana galuega uma': 'from all His work',
            'na faia e ia.': 'which He had made',
        },
        'Genesis|2|3': {
            'Ona faamanuia atu lea': 'Then blessed',
            'e le Atua': 'God',
            'i le aso fitu,': 'the seventh day',
            'ma na faasaina ai;': 'and sanctified it',
            'auā na malolo ai o ia': 'because He rested on it',
            'i lana galuega uma lava': 'from all His work',
            'na faia': 'which had been created',
            'ma na saunia.': 'and made',
        },
        'Genesis|2|4': {
            'O le tala lenei': 'These are the generations',
            'i le lagi': 'of the heavens',
            'ma le lalolagi': 'and the earth',
            'ina o faia ia,': 'when they were created',
            'i le aso': 'in the day',
            'na fai ai': 'that made',
            'e Ieova': 'the LORD',
            'le Atua': 'God',
            'le lalolagi': 'the earth',
            'ma le lagi.': 'and the heavens',
        },
        'Genesis|2|5': {
            'A o leai lava ni vaoiti uma': 'No plant of the field was yet',
            'o le fanua': 'in the field',
            'i le laueleele,': 'in the earth',
            'ua le tutupu foi laau afu uma': 'and no herb of the field had yet sprung up',
            'o le fanua;': 'of the field',
            'auā e lei faatotōina': 'for had not caused to rain',
            'le ua': 'rain',
            'e Ieova': 'the LORD',
            'le Atua': 'God',
            'i le eleele,': 'upon the earth',
            'ua leai foi': 'and there was no',
            'se tagata': 'man',
            'e galue': 'to till',
            'i le laueleele.': 'the ground',
        },
        'Genesis|2|6': {
            'A ua alu': 'But went up',
            'ae le ausa': 'a mist',
            'i le eleele,': 'from the earth',
            'ua sūsū ai': 'and watered',
            'le fogāeleele uma.': 'the whole face of the ground',
        },
        'Genesis|2|7': {
            'Ona faia lea': 'Then formed',
            'e Ieova': 'the LORD',
            'le Atua': 'God',
            'o le tagata': 'man',
            'i le efuefu': 'of the dust',
            'o le eleele,': 'of the ground',
            'ma ua mānava': 'and breathed',
            'i ona pogaiisu': 'into his nostrils',
            'o le mānava ola,': 'the breath of life',
            'ona avea ai lea': 'and became',
            'ma tagata ola.': 'a living being',
        },
        'Genesis|2|8': {
            'Ua faia foi': 'And planted',
            'e Ieova': 'the LORD',
            'le Atua': 'God',
            'o le faatoaga': 'a garden',
            'i Etena': 'in Eden',
            'i sasae;': 'in the east',
            'ona ia tuuina lea': 'and He put',
            'i lea mea': 'there',
            'o le tagata': 'the man',
            'na na faia.': 'whom He had formed',
        },
        'Genesis|2|9': {
            'Ua faatutupuina foi': 'And made to grow',
            'e Ieova': 'the LORD',
            'le Atua': 'God',
            'i le fanua o laau uma': 'out of the ground every tree',
            'e matagofie': 'pleasant',
            'i le vaai,': 'to the sight',
            'e lelei foi': 'and good',
            "pe a 'aina;": 'for food',
            'ma le laau': 'the tree',
            'o le ola': 'of life',
            'i totonu': 'in the midst',
            'o le faatoaga,': 'of the garden',
            'e iloa ai': 'of the knowledge of',
            'le lelei': 'good',
            'ma le leaga.': 'and evil',
        },
        'Genesis|2|10': {
            'Na tafe atu foi': 'Now a river went out',
            'le vaitafe mai Etena': 'from Eden',
            'e faasūsū ai': 'to water',
            'le faatoaga,': 'the garden',
            'ona ala eseese ai lea,': 'and from there it parted',
            'ua avea': 'and became',
            'ma vaitafe': 'rivers',
            'e fa.': 'four',
        },
        'Genesis|2|11': {
            'O le igoa': 'The name',
            'o le tasi o Pisona;': 'of the first is Pishon',
            'e faataamilomilo lea': 'it winds through',
            'i le nuu uma o Havila,': 'the whole land of Havilah',
            'e i ai auro;': 'where there is gold',
        },
        'Genesis|2|12': {
            'e lelei foi auro o lea nuu;': 'The gold of that land is good',
            'e iai petala': 'there is also bdellium',
            'ma maa soama.': 'and onyx stone',
        },
        'Genesis|2|13': {
            'O le igoa foi': 'The name',
            'o lona lua o vaitafe': 'of the second river',
            'o Kaiona;': 'is Gihon',
            'e faataamilomilo lea': 'it winds through',
            'i le nuu uma o Kuso.': 'the whole land of Cush',
        },
        'Genesis|2|14': {
            'O le igoa foi': 'The name',
            'o lona tolu o vaitafe': 'of the third river',
            'o Hitekelu;': 'is Hiddekel',
            'e tafe atu lea': 'it flows',
            'i sasae': 'east',
            'i Asuria.': 'of Assyria',
            'O lona fa o vaitafe': 'And the fourth river',
            'o Eufirate lea.': 'is the Euphrates',
        },
        'Genesis|2|15': {
            'Ua ave foi': 'And took',
            'le tagata,': 'the man',
            'e Ieova': 'the LORD',
            'le Atua,': 'God',
            'ma ua tuu ia te ia': 'and put him',
            'i le faatoaga': 'in the garden',
            'i Etena': 'in Eden',
            'e galue ai': 'to work it',
            'ma leoleo ai.': 'and keep it',
        },
        'Genesis|2|16': {
            'Ua fetalai atu foi Ieova': 'And the LORD commanded',
            'le Atua': 'God',
            'i le tagata,': 'the man',
            'o loo faapea atu,': 'saying',
            'O laau uma o': 'Of every tree',
            'i le faatoaga': 'of the garden',
            "e te 'ai ai.": 'you may freely eat',
        },
        'Genesis|2|17': {
            'A o le laau': 'But of the tree',
            'e iloa ai': 'of the knowledge of',
            'le lelei': 'good',
            'ma le leaga,': 'and evil',
            "aua e te 'ai ai;": 'you shall not eat',
            'auā o le aso': 'for in the day',
            "e te 'ai ai": 'that you eat of it',
            'e te oti ai lava.': 'you shall surely die',
        },
        'Genesis|2|18': {
            'Ua fetalai mai foi Ieova': 'And the LORD said',
            'le Atua,': 'God',
            'E le lelei': 'It is not good',
            'ina toatasi': 'that should be alone',
            'o le tagata;': 'the man',
            'ou te faia sona fesoasoani': 'I will make him a helper',
            'e tatau': 'fit',
            'ma ia.': 'for him',
        },
        'Genesis|2|19': {
            'Na faia': 'And formed',
            'e Ieova': 'the LORD',
            'le Atua': 'God',
            'i le eleele o manu vaefa uma': 'out of the ground every beast',
            'lava,': 'of the field',
            'ma manu felelei uma lava;': 'and every bird of the air',
            'na ia aumaia ia': 'and brought them',
            'Atamu ia iloa': 'to Adam to see',
            'pe ni': 'what',
            'a ni igoa': 'names',
            'na te faaigoa ai;': 'he would call them',
            'o le igoa': 'and whatever name',
            'ua faaigoaina ai': 'was given',
            'e Atamu': 'by Adam',
            'i meaola uma': 'to each living creature',
            'o lona igoa lea.': 'that was its name',
        },
        'Genesis|2|20': {
            'Ona faaigoaina atu lea': 'So gave names',
            'e Atamu o igoa': 'Adam',
            'i manu vaefa fanua uma,': 'to all livestock',
            'ma manu felelei,': 'and to the birds',
            'atoa ma manu vaefa uma': 'and to every beast',
            'o le vao;': 'of the field',
            'a o Atamu,': 'but for Adam',
            'e lei maua': 'there was not found',
            'se fesoasoani': 'a helper',
            'e tatau': 'fit',
            'ma ia.': 'for him',
        },
        'Genesis|2|21': {
            'Ua faamoegaseina o Atamu': 'God caused a deep sleep to fall upon Adam',
            'e Ieova': 'the LORD',
            'le Atua,': 'God',
            'ua moe lava;': 'and he slept',
            'ona toina lea e ia': 'then He took',
            'le tasi': 'one',
            'ona ivi asoaso,': 'of his ribs',
            'ma na faasoo ane': 'and closed up',
            'le aano': 'the flesh',
            "e sui a'i.": 'in its place',
        },
        'Genesis|2|22': {
            'O le ivi asoaso foi': 'And the rib',
            'na toina': 'which He had taken',
            'e Ieova': 'the LORD',
            'le Atua ia Atamu': 'God from Adam',
            "ua na fai a'i": 'He made into',
            'le fafine,': 'a woman',
            'ona ia aumaia lea o ia': 'and He brought her',
            'ia Atamu.': 'to Adam',
        },
        'Genesis|2|23': {
            'Ona faapea ai lea o Atamu,': 'And Adam said',
            'O le ivi lava lenei': 'This is now bone',
            "o o'u ivi,": 'of my bones',
            'ma le aano': 'and flesh',
            "o o'u aano;": 'of my flesh',
            "e ta'ua": 'she shall be called',
            'o ia': '',
            'o le fafine,': 'Woman',
            'auā na toina atu o ia': 'because she was taken out',
            'ai le tane.': 'of man',
        },
        'Genesis|2|24': {
            'O le mea lea': 'Therefore',
            'e tuua ai': 'shall leave',
            'e le tane lona tamā': 'a man his father',
            'ma lona tinā,': 'and his mother',
            'a e faatasi': 'and be joined',
            'ma lana avā;': 'to his wife',
            'ona avea ai lea o': 'and they shall become',
            'i laua': '',
            'ma tino': 'one',
            'e tasi.': 'flesh',
        },
        'Genesis|2|25': {
            'Sa le lavalavā': 'And they were both naked',
            'i laua': '',
            'o Atamu': 'Adam',
            'ma lana avā,': 'and his wife',
            'a ua': 'and were',
            'le mamā lava.': 'not ashamed',
        },
        'Esther|3|3': {
            'Ona fai atu lea o auauna': 'then said a servant',
            'a le tupu,': 'of the king',
            'e na': 'which was',
            'i ai': 'therein',
            'i le faitotoa': 'in the gate',
            'o le tupu,': 'of the king',
            'ia Moretekai,': 'to Mordecai',
            'Se a le mea': 'what is this?',
            'ua e soli ai': 'why do you transgress',
            'le poloaiga': 'the commandment',
            'a le tupu?': 'of the king',
        },
    }
    overridden = 0
    for vkey, overrides in MANUAL_GLOSS_OVERRIDES.items():
        if vkey in annotations:
            for i, pair in enumerate(annotations[vkey]):
                samoan = pair[0]
                if samoan in overrides:
                    annotations[vkey][i][1] = overrides[samoan]
                    overridden += 1
    if overridden:
        print(f"Applied {overridden} manual gloss overrides")

    # Save
    with open(phrase_path, 'w', encoding='utf-8') as f:
        json.dump(annotations, f, ensure_ascii=False, indent=1)
    print(f"Saved to {phrase_path}")


if __name__ == '__main__':
    main()
