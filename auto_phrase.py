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
    'ifo': 'down',
    'ane': '(dir)',
    'maia': '(dir)',
    # Common words
    'foi': 'also',
    'lava': 'indeed',
    'uma': 'all',
    'atoa': 'together with',
    'a': 'but',
    # 'ae' handled contextually in gloss_phrase (up/but)
    'pe': 'or',
    'ina': 'so that',
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
    'masina': 'month',
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
    # Compass directions (override bad dictionary entries)
    'sasae': 'east',
    'sisifo': 'west',
    'matu': 'north',
    'toga': 'south',
    'itu': 'side',

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
    'va': 'expanse',
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
    'iloa': 'know',
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
    # 'ifo' handled as directional 'down' in FUNC_WORDS
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
    'ieova': 'the LORD',
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
    # Exodus vocabulary
    'puluti': 'daub',
    'kome': 'bulrushes',
    'safeta': 'pitch',
    'utuutu': 'reeds',
    'auvai': 'riverbank',
    'vaitafe': 'river',
    'ato': 'basket/ark',
    'n\u0101': 'indeed',
    'mamao': 'far',
    'tuafafine': 'sister',
    'iu': 'become of',
    'taele': 'bathe',
    'tatalaina': 'opened',
    'faauta': 'behold',
    'failele': 'nursing',
    'aami': 'call',
    'tausia': 'nursed',
    'tausi': 'nurse',
    'valaau': 'call',
    'totogi': 'wages',
    'avatu': 'give',
    'tin\u0101': 'mother',
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

    # ============================================================
    # Biblical Proper Names (Samoan transliterations → English)
    # ============================================================
    # Genesis patriarchs & families
    'atamu': 'Adam',
    'eva': 'Eve',
    'kaino': 'Cain',
    'apelu': 'Abel',
    'seta': 'Seth',
    'enoka': 'Enoch',
    'noa': 'Noah',
    'sema': 'Shem',
    'hamu': 'Ham',
    'iafeta': 'Japheth',
    'aperamo': 'Abram',
    'aperaamo': 'Abraham',
    'sarai': 'Sarai',
    'sara': 'Sarah',
    'lota': 'Lot',
    'akara': 'Hagar',
    'isamaeli': 'Ishmael',
    'isaako': 'Isaac',
    'repeka': 'Rebekah',
    'esau': 'Esau',
    'iakopo': 'Jacob',
    'ruta': 'Ruth',
    'iosefa': 'Joseph',
    'raelu': 'Rachel',
    'lea': 'Leah',
    'rupena': 'Reuben',
    'simeona': 'Simeon',
    'levi': 'Levi',
    'iuta': 'Judah',
    'peniamina': 'Benjamin',
    'tana': 'Dan',
    'napatalī': 'Naphtali',
    'kata': 'Gad',
    'asera': 'Asher',
    'isakara': 'Issachar',
    'sepulona': 'Zebulun',
    'manase': 'Manasseh',
    'efaraima': 'Ephraim',
    'melekisateko': 'Melchizedek',

    # Exodus / Judges / Kings era
    'mose': 'Moses',
    'arona': 'Aaron',
    'iosua': 'Joshua',
    'nuno': 'Nun',
    'kaleva': 'Caleb',
    'raava': 'Rahab',
    'kitiona': 'Gideon',
    'samsona': 'Samson',
    'talila': 'Delilah',
    'eli': 'Eli',
    'samuelu': 'Samuel',
    'elekana': 'Elkanah',
    'hana': 'Hannah',
    'saulo': 'Saul',
    'ionatana': 'Jonathan',
    'tāvita': 'David',
    'tavita': 'David',
    'solomona': 'Solomon',
    'goliata': 'Goliath',
    'aapo': 'Ahab',
    'isepela': 'Jezebel',
    'elia': 'Elijah',
    'elisaia': 'Elisha',
    'naomi': 'Naomi',
    'poasa': 'Boaz',
    'penina': 'Peninnah',

    # Prophets
    'isaia': 'Isaiah',
    'ieremia': 'Jeremiah',
    'esekielu': 'Ezekiel',
    'tanielu': 'Daniel',
    'hosea': 'Hosea',
    'ioelu': 'Joel',
    'amosa': 'Amos',
    'opetaia': 'Obadiah',
    'iona': 'Jonah',
    'mika': 'Micah',
    'nauma': 'Nahum',
    'sapakuka': 'Habakkuk',
    'sefanaia': 'Zephaniah',
    'hakai': 'Haggai',
    'sakaria': 'Zechariah',
    'malaki': 'Malachi',
    'neemia': 'Nehemiah',
    'esera': 'Ezra',
    'iopu': 'Job',

    # New Testament people
    'maria': 'Mary',
    'marta': 'Martha',
    'lasaro': 'Lazarus',
    'peteru': 'Peter',
    'simona': 'Simon',
    'aneterea': 'Andrew',
    'iakobo': 'James',
    'ioane': 'John',
    'filipo': 'Philip',
    'patolomaio': 'Bartholomew',
    'toma': 'Thomas',
    'mataio': 'Matthew',
    'paulo': 'Paul',
    'panapa': 'Barnabas',
    'timoteo': 'Timothy',
    'tito': 'Titus',
    'herotā': 'Herod',
    'herota': 'Herod',
    'pilato': 'Pilate',
    'nikotemo': 'Nicodemus',
    'iutasa': 'Judas',

    # Book of Mormon people
    'nifae': 'Nephi',
    'liae': 'Lehi',
    'lemuela': 'Lemuel',
    'lamana': 'Laman',
    'sarama': 'Sariah',
    'isimeli': 'Ishmael',
    'sopai': 'Zoram',
    'alema': 'Alma',
    'mosaea': 'Mosiah',
    'moronae': 'Moroni',
    'mamona': 'Mormon',
    'iakopa': 'Jacob',
    'enosa': 'Enos',
    'amona': 'Ammon',

    # Places
    'ierusalema': 'Jerusalem',
    'ioritana': 'Jordan',
    'kanana': 'Canaan',
    'aikupito': 'Egypt',
    'asuria': 'Assyria',
    'papelonia': 'Babylon',
    'petheleema': 'Bethlehem',
    'peteli': 'Bethel',
    'nasareta': 'Nazareth',
    'kaperanauma': 'Capernaum',
    'sailo': 'Shiloh',
    'ieriko': 'Jericho',
    'etena': 'Eden',
    'sinai': 'Sinai',
    'moapi': 'Moab',
    'etoma': 'Edom',
    'kiliata': 'Gilead',
    'kalilaia': 'Galilee',
    'samaria': 'Samaria',
    'saitonu': 'Sidon',
    'turo': 'Tyre',
    'heperona': 'Hebron',
    'sikema': 'Shechem',
    'perea': 'Berea',
    'roma': 'Rome',
    'korinito': 'Corinth',
    'efeso': 'Ephesus',
    'antiokia': 'Antioch',
    'tesalonika': 'Thessalonica',
    'rama': 'Ramah',
    'sarepata': 'Zarephath',

    # Hyphenated compound names
    'ramata-sofimo': 'Ramathaim-zophim',
    'pere-laaroi': 'Beer-lahai-roi',
    'pere-sepa': 'Beersheba',
    'kiriat-arapa': 'Kiriath-arba',
    'kiriat-iearima': 'Kiriath-jearim',

    # Additional names (1 Samuel, Joshua, Judges etc.)
    'ieroama': 'Jeroham',
    'eliu': 'Elihu',
    "to'u": 'Tohu',
    'sufi': 'Zuph',
    'aapia': 'Abijah',
    'penina': 'Peninnah',
    'raava': 'Rahab',
    'kaleva': 'Caleb',
    'otenielu': 'Othniel',
    'iefune': 'Jephunneh',
    'epota': 'Ehud',
    'tepera': 'Deborah',
    'paraka': 'Barak',
    'kitiona': 'Gideon',
    'apisai': 'Abishai',
    'ioapa': 'Joab',
    'apena': 'Abner',
    'natano': 'Nathan',
    'patesipa': 'Bathsheba',
    'uriā': 'Uriah',
    'uria': 'Uriah',
    'apasaloma': 'Absalom',
    'rehapoamo': 'Rehoboam',
    'ieropoamo': 'Jeroboam',
    'asa': 'Asa',
    'ieosafata': 'Jehoshaphat',
    'eseta': 'Esther',
    'morekaia': 'Mordecai',
    'hamana': 'Haman',
    'aierusu': 'Ahasuerus',
    'nebukanezo': 'Nebuchadnezzar',
    'koresi': 'Cyrus',
    'tariu': 'Darius',

    # Peoples / nations
    'pilistia': 'Philistines',
    'kananā': 'Canaanites',
    'amorī': 'Amorites',
    'hetī': 'Hittites',
    'perisē': 'Perizzites',
    'iepusē': 'Jebusites',
    'hivī': 'Hivites',
    'efaratā': 'Ephrathite',
    'kenī': 'Kenites',
    'kinasā': 'Kenizzites',
    'katemonī': 'Kadmonites',
    'repaimā': 'Rephaim',

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
    'ieova': 'the LORD',
    'paulo': 'Paul',
    'peteru': 'Peter',
    'ioane': 'John',
    'mataio': 'Matthew',
    'mareko': 'Mark',
    'luka': 'Luke',
    # 'iakopo': 'James',  # Iakopo = Jacob (OT/BoM) — James handled via book-specific overrides
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
    'nuanua': 'rainbow',

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
    'ō': 'go (plural)',
    'o\u0304': 'go (plural)',
    'avea': 'become',
    'nonofo': 'dwelling',
    'tulai': 'arise/rise up',
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
    'faalili': 'provoke',
    'faaonoono': 'vex',
    'tagi': 'cry/weep',
    'mavae': 'passed/after',
    'vaai': 'look/behold',
    'asiasi': 'spy out/visit',
    'petavene': 'Beth-aven',
    'tiga': 'grieved/pain',
    'toatinoagafulu': 'ten (people)',
    'ino': 'evil/harm',

    # Specific biblical terms
    'faatoina': 'accursed thing',
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

    # ── Vocabulary learned from Genesis 1-12 manual overrides ──
    # Fix wrong dictionary meanings for biblical context
    'uso': 'brother',
    'pei': 'like',
    'lei': 'not',
    'lē': 'not',
    'malaia': 'cursed',
    'leoleo': 'guard',
    'ala': 'way',
    'silafia': 'known',
    'pepeti': 'fat portions',

    # Missing words from Genesis overrides
    'faatoaga': 'garden',
    'kerupi': 'cherubim',
    'iafeta': 'Japheth',
    'nineva': 'Nineveh',
    'usiusitai': 'obeyed',
    'faaigoaina': 'named/called',
    'feliuliuai': 'turning',
    'faasevasevaloaina': 'wanderer',
    'maumausolo': 'fugitive',
    'aapa': 'reach out',
    'faaūū': 'fallen (countenance)',
    'lavalavā': 'naked',
    'uai': 'desire',
    'faatu': 'pitch/build',
    'faatuu': 'pitch/build',
    'faatūlaga': 'set/establish',
    'faaali': 'appear/reveal',
    'faaalia': 'appear/reveal',

    # Context-dependent improvements (biblical senses)
    'galue': 'till/work',      # farm/till the ground
    'faaolaina': 'saved/keep alive',
    'avā': 'wife',
    'tam\u0101': 'father',
    'tin\u0101': 'mother',

    # Additional Genesis names
    'aperamo': 'Abram',
    'sarai': 'Sarai',
    'lota': 'Lot',
    'sekema': 'Shechem',
    'peteli': 'Bethel',
    'karana': 'Haran',
    'kananā': 'Canaanites',

    # Additional verbs from Genesis
    'āumau': 'sojourn',
    'vivii': 'praised',
    'agalelei': 'treated well',
    'faatigaina': 'afflicted/plagued',
    'tuuina': 'given/sent',
    'poloai': 'command',
    'fasioti': 'killed',
    'saogalemu': 'go well/safe',
    'matagofie': 'beautiful',
    'lalelei': 'beautiful',

    # ── High-frequency missing vocabulary (appearing 100+ times across Bible) ──
    # Deduced from English parallel text and Samoan morphology
    'mativa': 'want/lack',
    'matitiva': 'poor',
    'tutū': 'stood up',
    "'ino'ino": 'hate/abhor',
    'anamua': 'ancient/formerly',
    'ituaiga': 'tribe/kind',
    'tietie': 'ride',
    'faapaiaina': 'consecrated/holy',
    'aioi': 'cry out/weep',
    'faapotopotoina': 'gathered together',
    'atolaau': 'army/host',
    'faoa': 'seized/taken captive',
    'taia': 'struck/smitten',
    'alalaga': 'cry out/shout',
    'fusi': 'bind/girdle',
    'viiga': 'praise',
    'sese': 'wrong/astray',
    'tuugamau': 'grave/tomb',
    'solitulafono': 'transgression',
    "ta'ita'i": 'lead/leader',
    'tulia': 'driven away/chased',
    'faauuina': 'anointed',
    'afua': 'begin/originate',
    'ioritana': 'Jordan',
    'iuga': 'end/result',
    'faamalosi': 'be strong/encourage',
    'vaavaai': 'watch/look',
    'moapi': 'Moab',
    'taofia': 'held back/restrained',
    'taoto': 'lie down/sleep',
    'faaoo': 'bring upon/afflict',
    'uamea': 'iron',
    'faatafunaina': 'destroyed',
    'nofoālii': 'throne',
    'faamagaloina': 'forgiven',
    'galulue': 'labour/work',
    'faalatalata': 'draw near',
    'sapati': 'Sabbath',
    'faataamilo': 'surround',
    'mananao': 'desire/wish',
    'faitauina': 'counted/read',
    'totogi': 'wages/reward',
    'taitai': 'lead/guide',
    'memea': 'scarlet/red',
    'fefefe': 'afraid/terrified',
    'faatauvaa': 'vain/worthless',
    'tiapolo': 'devil',
    'toatolu': 'three (people)',
    'leona': 'lion',
    'maualuluga': 'most high/exalted',
    'aveeseina': 'carried away',
    'mamafa': 'heavy/severe',
    'faapena': 'likewise/so',
    'mauaina': 'obtained/found',
    'lotoā': 'court/enclosure',
    'matautia': 'fearful/terrible',
    'onosai': 'patience/endure',
    'vaivaiga': 'weakness',
    'luluina': 'shaken',
    'ilo': 'maggot/worm',
    'faamasinotonu': 'righteous judgment',
    'ioa': 'name',
    'fefinauai': 'disputing',
    "fefinaua'i": 'disputing',
    'fefinauaiga': 'dispute/quarrel',
    'tautala': 'spoke/speaking',
    'tautalaga': 'talking/speech',
    'lofituina': 'overcome',
    'faanoanoa': 'mourn/grieve',
    'faafanoga': 'destruction',
    'finauga': 'disputation/contention',
    'faigata': 'difficult/hard',
    'vagana': 'save/except/unless',
    'talitonu': 'believe/believing',
    'filiga': 'diligence/perseverance',
    'faatusaina': 'compared/likened',
    "fa'iesea": 'broken off/cut off',
    'suluina': 'grafted/grafting',
    'atoatoaga': 'fulness',
    'faaitiitia': 'diminished/scattered',
    'tauaao': 'minister/deliver',
    'papa': 'rock/foundation',
    'olataga': 'salvation/deliverance',
    'lotoa': 'fold/vineyard',
    'sulu': 'graft/torch/light',
    'pogai': 'cause/root',
    'faapefea': 'how',
    'talalelei': 'gospel',
    'apoapoai': 'exhort/admonish',
    'afioga': 'word (divine)',
    'pipiimau': 'hold fast/cling',
    'faaosoosoga': 'temptation',
    'ufanafana': 'fiery dart/arrow',
    'faatauasoina': 'led astray/blindness',

    # Reciprocal verbs: fe- + root + -ai/-a'i (each other / about)
    'fetaiai': 'meet one another',
    'feoai': 'walk about',
    "feoa'i": 'walk about',
    'feiloai': 'meet one another',
    "feiloa'i": 'meet one another',
    'fealuai': 'walk about',
    'fealualuai': 'walk about',
    'fememeai': 'whisper to one another',
    'fesagai': 'face one another',
    'feitai': 'visit one another',
    'fetautalatalai': 'converse with one another',
    "fetautalatala'i": 'converse with one another',
    'fetautalatalaai': 'converse with one another',
    'felatai': 'be near one another',
    'fevaevaeai': 'divide among one another',
    'feitagai': 'look upon one another',
    'feaveai': 'carry about',
    'femalagaai': 'travel about',
    "femalagaa'i": 'travel about',
    'femisai': 'quarrel with each other',
    "fetaia'i": 'fight one another',
    'felafolafoai': 'consult together',
    'fefaamafanafanai': 'comfort one another',
    'femaliuai': 'turn about',
    "femaliua'i": 'turn about',
    'fesootai': 'join one another',
    'fetaufetuliai': 'contend with one another',
    'fefaauoai': 'exhort one another',
    'fefaatauai': 'trade with one another',
    "fefaataua'i": 'trade with one another',
    'feaveaveai': 'carry about',
    'feganavai': 'battle one another',
    "feleiloana'i": 'meet one another',
    'feseseseai': 'err/go astray',
    "fesesea'i": 'go astray',
    'femusuai': 'murmur to one another',
    'feasofai': 'visit one another',
    "feasofa'i": 'visit one another',
    'fefasiai': 'touch one another',
    'feliuliuai': 'go about',
    "feliuliua'i": 'go about',
    'fevalaauai': 'call to one another',
    'fefilemuai': 'be at peace with one another',
    'fefaamagaloai': 'forgive one another',
    'feapoapoai': 'exhort one another',
    'fefaamalieai': 'comfort one another',
    'fefaamalosiai': 'strengthen one another',
    'fefaatonuai': 'correct one another',
    'fefaaaliai': 'reveal to one another',
    'femanaoai': 'desire one another',
    'fesaeiai': 'rise up against one another',
    'feusuai': 'marry one another',

    # High-frequency faa- causative words (proper glosses)
    'faatasi': 'together',
    'faamasino': 'judge',
    'faamaoni': 'faithful/righteous',
    'faapei': 'like/as',
    'faatatau': 'liken/compare',
    'faamoemoe': 'hope/trust',
    'faatau': 'buy/sell',
    'faafetai': 'thank/grateful',
    'faaaliga': 'revelation',
    'faasaua': 'cruel/violent',
    'faamaualuga': 'exalted/proud',
    'faaloaloa': 'stretch out',
    'faatoga': 'order/decree',
    'faalagolago': 'rely/trust',
    'faaletino': 'bodily/in the flesh',
    'faamau': 'establish/fasten',
    'faataoto': 'lay down/prostrate',
    'faatiga': 'afflict/hurt',
    'faautauta': 'careful/cautious',
    'faauma': 'finish/complete',
    'faasuafa': 'named',
    'faamalolosi': 'strengthen',
    'faasaoina': 'spared/preserved',
    'faaigoaina': 'named/called',
    'faauuina': 'anointed',
    'faafeao': 'escort/guard',
    'faatagata': 'make human/humanize',
    'faaleagaina': 'destroyed/ruined',
    'faatuatua': 'faith',
    'faataunuuina': 'fulfilled',
    'miti': 'dream',

    # Names (high frequency, untranslated)
    'selā': 'Selah',
    'iopu': 'Job',
    'faresaio': 'Pharisee',
    'osana': 'Hosanna',
    'kaletaia': 'Chaldean',
    'kaisara': 'Caesar',
    'samasoni': 'Samson',
    'ionatana': 'Jonathan',
    'ioapo': 'Joab',
    'apisaloma': 'Absalom',
    'apimeleko': 'Abimelech',
    'apineru': 'Abner',
    'iosefatu': 'Jehoshaphat',
    'esekia': 'Hezekiah',
    'napalu': 'Nebuchadnezzar',
    'moloka': 'Molech',
    'sunako': 'synagogue',
    'soia': 'stop/enough',
    'onā': 'drunk',

    # ============================================================
    # Additional Proper Names (gleaned from KJV cross-reference)
    # ============================================================
    'sotoma': 'Sodom',
    'komoro': 'Gomorrah',
    'mamere': 'Mamre',
    'tamaseko': 'Damascus',
    'rasela': 'Rachel',
    'reupena': 'Reuben',
    'mitiana': 'Midian',
    'amoni': 'Ammon',
    'kipea': 'Gibeah',
    'kilikala': 'Gilgal',
    'vasana': 'Bashan',
    'lepanona': 'Lebanon',
    'mesepa': 'Mizpah',
    'iese': 'Jesse',
    'sesera': 'Sisera',
    'akisa': 'Achish',
    'iefata': 'Jephthah',
    'eperu': 'Hebrew',
    'peteleema': 'Bethlehem',
    'suria': 'Syria',
    'kaisareia': 'Caesarea',
    'anetioka': 'Antioch',
    'nafatali': 'Naphtali',
    'kopera': 'Gopher',
    'karamu': 'Carmel',
    'saikia': 'Ziklag',
    'pisika': 'Pisgah',
    'piseka': 'Pisgah',

    # ============================================================
    # Transliterated Biblical/Religious Terms
    # ============================================================
    'malumalu': 'temple',
    'paseka': 'Passover',
    'peritome': 'circumcision',
    'peritomeina': 'circumcised',
    'efota': 'ephod',
    'tusiupu': 'scribe',
    'satukaio': 'Sadducee',
    'temoni': 'demon',
    'seoli': 'Sheol',
    'eunuka': 'eunuch',
    'parataiso': 'paradise',
    'papatisoina': 'baptized',
    'papatiso': 'baptize',
    'faasatauroina': 'crucified',
    'satauro': 'cross',
    'setima': 'shittim wood',
    'sekeli': 'shekel',
    'taleni': 'talent',
    'lamepa': 'lamp',
    'karite': 'barley',
    'kariota': 'chariot',
    'kamela': 'camel',
    'lino': 'linen',
    'tovine': 'vineyard',
    'omea': 'mortar',
    'vine': 'vine',
    'olive': 'olive',

    # ============================================================
    # Common Verbs (KJV-verified)
    # ============================================================
    'ulufale': 'enter',
    'viia': 'praised',
    'taunuu': 'fulfilled',
    'faataunuuina': 'fulfilled',
    'finau': 'strive',
    'solia': 'despised',
    'aveina': 'taken away',
    'fusifusia': 'bound',
    'faatumauina': 'established',
    'lepetia': 'overthrown',
    'lafoaiina': 'forsaken',
    'faasalaina': 'punished',
    'faamasinoina': 'judged',
    'tatalaina': 'opened',
    'momoe': 'lie down',
    'sopoia': 'crossed over',
    'siitia': 'lifted up',
    'faatalitali': 'waited',
    "ta'ita'iina": 'led',
    'aami': 'summoned',
    'molia': 'accused',
    'pepese': 'sing',
    'gatete': 'tremble',
    'folau': 'sail',
    'tapuai': 'worship',
    'vete': 'plunder',
    'faafetaiai': 'meet',
    'naunau': 'desire',
    'folafolaina': 'preached',
    'faafetaia': 'praised',
    'faailoa': 'revealed',
    'faaali': 'revealed',
    'faaalia': 'revealed',
    'faatulagaina': 'appointed',
    'faafiti': 'denied',
    'faaumatia': 'destroyed',
    'faasaoina': 'spared',
    'faasao': 'spare',
    'faatali': 'wait',
    'faamalolo': 'refresh',
    'faafeiloai': 'greet',
    'faapotopoto': 'gather',
    'faatoilalo': 'spare',
    'tolopo': 'crawl',

    # ============================================================
    # Common Nouns (KJV-verified)
    # ============================================================
    'faaolataga': 'salvation',
    'tausamiga': 'feast',
    'tootoo': 'staff',
    'feau': 'errand',
    'moega': 'bed',
    'taulealea': 'young man',
    'taulelea': 'young men',
    'taupou': 'virgin',
    'avega': 'burden',
    'vaieli': 'well',
    'fatafata': 'breast',
    'talita': 'shield',
    'efuefu': 'dust',
    'suauu': 'oil',
    'gataaga': 'boundary',
    'ufifatafata': 'breastplate',
    'laoai': 'table',
    'maea': 'rope',
    'tuluiga': 'anointing',
    "taulā'itu": 'sorcerer',
    "faataulā'itu": 'sorcery',
    'fetalaiga': 'speech',
    'pito': 'edge',
    'areto': 'bread',
    'falaoa': 'flour',
    'suāsusu': 'milk',
    'pata': 'butter',
    'fale ie': 'tent',
    'faleie': 'tent',
    'faitotoa': 'door',
    'lafu': 'herd',
    'tufaaga': 'portion',
    'amiotonu': 'righteous',
    'amioleaga': 'wickedness',
    'agasala': 'sin',
    'faamasinoga': 'judgment',
    'fetalai': 'said/spoke',
    'faataulaga': 'offering',
    'igoa': 'name',
    'nofoaga': 'place',
    'tupuga': 'nation/offspring',
    'auauna': 'servant',
    'alaga': 'cry',
    'tamaloloa': 'men',
    'potoi': 'cake',
    'lefulefu': 'ashes',
    'mauga': 'mountain',
    'vanu': 'valley',
    'sami': 'sea',
    'vaitafe': 'river',
    'malamalama': 'light',
    'pogisa': 'darkness',
    'matagi': 'wind',
    'ua': 'rain',
    'lagi': 'heaven/sky',

    # ============================================================
    # Adjectives & Descriptors
    # ============================================================
    'feai': 'wild',
    'ufiufi': 'covering',
    'naumati': 'dry',
    'sinasina': 'white',
    'fulufulu': 'hairy',
    'tauagavale': 'left',
    'manatunatu': 'meditate',
    'lotolelei': 'righteous',
    'lotoleaga': 'wicked',
    'paie': 'barren',
    'malosi': 'strong',
    'vaivai': 'weak',
    'matutua': 'old/aged',
    'toeaina': 'elder',
    'loomatua': 'old woman',
    'talavou': 'young',
    'laitiiti': 'small',
    'matuā': 'exceedingly',

    # ============================================================
    # Number Words (counting people)
    # ============================================================
    'luafulu': 'twenty',
    'tolugafulu': 'thirty',
    'fagafulu': 'forty',
    'limagafulu': 'fifty',
    'onogafulu': 'sixty',
    'fitugafulu': 'seventy',
    'valugafulu': 'eighty',
    'ivagafulu': 'ninety',
    'toafitu': 'seven (people)',
    'toalima': 'five (people)',
    'toaono': 'six (people)',
    'toasefulu': 'ten (people)',
    'toaselau': 'a hundred (people)',
    'toafitugafulu': 'seventy (people)',
    'toatolugafulu': 'thirty (people)',
    'toaluafulu': 'twenty (people)',
    'toalimagafulu': 'fifty (people)',
    'toaitiiti': 'few (people)',
    'toalua': 'two (people)',
    'toatolu': 'three (people)',
    'toafa': 'four (people)',
    'toavalu': 'eight (people)',
    'toaiva': 'nine (people)',
    'toafagafulu': 'forty (people)',
    'selau': 'hundred',
    'afe': 'thousand',
    'mano': 'ten thousand',

    # ============================================================
    # Additional vocab (gleaned from KJV cross-reference)
    # ============================================================
    'soara': 'Zoar',
    'pename': 'Ben-Ammi',
    'hofeni': 'Hophni',
    'fineaso': 'Phinehas',
    'faitaulaga': 'priest',
    'taulaga': 'offering/sacrifice',
    'teio': 'brimstone',
    'masima': 'salt',
    'tupua': 'pillar/image',
    'umu': 'oven/furnace',
    'uaina': 'wine',
    'ana': 'cave',
    'agelu': 'angel',
    'faatauaso': 'struck blind',
    'fetuleni': 'pressed hard',
    'pulunaunau': 'urged strongly',
    'nanati': 'urged',
    'laugatasi': 'plain',
    'malaia': 'disaster',
    'faatuatuai': 'lingered',
    'fetagofi': 'seized',
    'pupuni': 'shut/closed',
    'ulufafo': 'went outside',
    'faianaga': 'jesting',
    'taase': 'sojourn',
    'sofai': 'break open',
    'siomia': 'surrounded',
    'sola': 'escape/flee',
    'liua': 'turned into',
    'faainua': 'made drink',
    'taooto': 'lie down',
    'moapi': 'Moab',
    'moapī': 'Moabites',
    'alaaga': 'outcry',

    # ============================================================
    # Bulk vocabulary (deduced from KJV cross-reference)
    # Common verbs (100+ occurrences)
    # ============================================================
    'pau': 'fall',
    'suauu': 'oil',
    'faatauina': 'bought/redeemed',
    'susunuina': 'burned',
    'fuatia': 'weighed/measured',
    'faitaulia': 'counted/numbered',
    'avane': 'gave/delivered',
    "te'a": 'depart/leave',
    'aoai': 'chastise/correct',
    'valea': 'foolish',
    'manava': 'womb/belly',
    'faamamaina': 'cleansed/purified',
    'faamamā': 'purify/cleanse',
    'faamama': 'purify/cleanse',
    'fesui': 'change',
    'laugutu': 'lips',
    'faafoisia': 'restored',
    'faateleina': 'multiplied/increased',
    'faatupuina': 'raised up',
    'lata': 'near',
    'sailiili': 'search/inquire',
    'vavaeeseina': 'separated/set apart',
    'faafefeteina': 'feared/terrified',
    'avae': 'take away/remove',
    'tuliloa': 'pursue/chase',
    'faamauina': 'established/confirmed',
    'fetagisi': 'wept/wailed',
    'teu': 'store/treasure',
    'lafoai': 'forsaken/abandoned',
    'talitane': 'harlot',
    'atili': 'more/exceedingly',
    'faamu': 'burn incense',
    'galo': 'forgotten',
    'pue': 'capture/seize',
    'osia': 'hewn/cut',
    'tumutumu': 'top/summit',
    'arasi': 'cedar',
    'faaopoopo': 'add/join',
    'feagai': 'opposite/facing',
    'tanoa': 'basin/bowl',
    'tauia': 'recompense/repay',
    'faaopoopoina': 'added/joined',
    'suesue': 'examine/search',
    "faa'ole'ole": 'deceit/guile',
    "tala'iina": 'preached/proclaimed',
    'faataapeapeina': 'scattered/dispersed',
    'lepela': 'leprosy',
    'ila': 'spot/blemish',
    'aufana': 'bow',
    'tunu': 'roast/smelt',
    'faafoi': 'return/turn back',
    'fanafana': 'arrow',
    'auupega': 'weapon/armor',
    'faatoa': 'just now/recently',
    'natia': 'hide/conceal',
    'tafea': 'exiled/carried captive',
    'faasaina': 'consecrated/hallowed',
    'faavae': 'foundation',
    'faamaloloina': 'healed/comforted',
    'oona': 'drunk/drunkenness',
    'faamalosia': 'strengthened/compelled',
    'aveesea': 'removed/put away',
    'tutusa': 'equal/alike',
    'tautoga': 'oath/vow',
    'agamalu': 'meek/gentle',
    'sailia': 'sought',
    'faatumuina': 'filled',
    'sauniuni': 'prepared',
    'punitia': 'shut/closed',
    'faavaivai': 'weakened/feeble',
    'lafoina': 'cast/thrown',
    'tausiusi': 'obey/keep',
    'valelea': 'foolish/senseless',
    'faalua': 'twice/double',
    'afeafe': 'porch/vestibule',
    'tauemu': 'mock/scorn',
    'suavai': 'water/melt',
    'upega': 'net/snare',
    'aano': 'body/substance',
    'faaseseina': 'deceived/led astray',
    'faatatauina': 'determined/reckoned',
    'faamafanafanaina': 'comforted/consoled',
    'mafafai': 'able/capable',
    'tuugalamepa': 'lampstand',
    'leoleoina': 'guarded/watched',
    'faalava': 'crossbar/beam',
    'fafie': 'firewood',
    'matafaga': 'shore/seashore',
    'mati': 'fig',
    'faauu': 'anoint',
    'siosioina': 'surrounded/besieged',
    'faapaologa': 'captivity/exile',
    'maulalo': 'lowly/humble',
    'saeia': 'spared/remaining',
    'aoaiga': 'discipline/instruction',
    'tanumia': 'buried',
    'vasega': 'course/division',
    'faapau': 'overthrow/fell',
    'mauoa': 'wealthy/rich',

    # Common nouns/adjectives
    'pou': 'pillar',
    'iti': 'small/little',
    'vaa': 'ship/boat',
    'amo': 'carry/bear',
    'lautele': 'wide/broad',
    'toagalauapi': 'camp',
    'tuafanua': 'suburbs/pastureland',
    'mumu': 'scarlet/red',
    'pauli': 'blue/purple',
    'efa': 'ephah',
    'savali': 'walk/messenger',
    'taua': 'precious/costly',
    'ifea': 'where?',
    'fea': 'where?/which?',

    # ============================================================
    # Transliterated proper nouns (KJV cross-reference)
    # ============================================================
    'ierepoamo': 'Jeroboam',
    'nepukanesa': 'Nebuchadnezzar',
    'kato': 'Gath',
    'eleasaro': 'Eleazar',
    'ioasa': 'Joash',
    'setekaia': 'Zedekiah',
    'iosia': 'Josiah',
    'satoka': 'Zadok',
    'hamanu': 'Haman',
    'reopoamo': 'Rehoboam',
    'penaia': 'Benaiah',
    'asaira': 'Asherah',
    'kipeona': 'Gibeon',
    'palako': 'Balak',
    'semi': 'Shimei',
    'ioramo': 'Joram',
    'palaamo': 'Balaam',
    'ieu': 'Jehu',
    'isereelu': 'Israelite',
    'aasa': 'Asa',
    'rimoni': 'Rimmon',
    'akapi': 'Ahab',
    'atalia': 'Athaliah',
    'iesakara': 'Issachar',
    'iutaia': 'Judea',
    'kisona': 'Kishon',
    'karesi': 'Chaldeans',
    'iosua': 'Joshua',
    'iotamu': 'Jotham',
    'iepusai': 'Jebusite',
    'kileata': 'Gilead',
    'sapata': 'Zabdi',
    'karame': 'Carmi',
    'sera': 'Zerah',
    'aseta': 'Ashdod',
    'ekerona': 'Ekron',
    'asakalona': 'Ashkelon',
    'kaseta': 'Gaza',
    'kasā': 'Gaza',
    'ierosolema': 'Jerusalem',
    'peniamina': 'Benjamin',
    'ikaiolo': 'Ichabod',
    'samuelu': 'Samuel',
    'pelesitiā': 'Philistines',
    'pelesitia': 'Philistines',
    'akana': 'Achan',
    'karamelu': 'Carmel',
    'sinai': 'Sinai',
    'ninevu': 'Nineveh',
    'papelonia': 'Babylon',
    'tikera': 'Tigris',
    'eufirate': 'Euphrates',
    'lesepoa': 'Jezreel',
    'ierikaō': 'Jericho',
    'ieriko': 'Jericho',

    # ============================================================
    # BOM / D&C / PGP vocabulary (deduced from context)
    # ============================================================
    # Common words
    'nao': 'only/alone',
    'upumoni': 'truth',
    'faatonu': 'commanded/directed',
    'fausia': 'built/constructed',
    'manaomia': 'desired/needed',
    'tutuli': 'cast out/driven out',
    'meaai': 'food',
    'falepuipui': 'prison',
    'teena': 'rejected/denied',
    'aveese': 'removed/taken away',
    "pa'u": 'fell/fall',
    'faataunuu': 'fulfilled/accomplished',
    'aofai': 'number/amount',
    'saolotoga': 'freedom/liberty',
    'faatutu': 'pitched/set up',
    'manino': 'plain/clear',
    'auai': 'present/participated',
    'iloaina': 'recognized/known',
    'faaaoga': 'used/employed',
    'maaa': 'hardness/stubbornness',
    'faomea': 'robber/thief',
    'mautinoa': 'surely/certainly',
    'faafitia': 'opposed/resisted',
    'saute': 'south',
    'tausiga': 'keeping/observance',
    'laiti': 'small/little',
    'faaauau': 'continued/proceeded',
    'naua': 'exceedingly',
    'itula': 'hour',

    # Religious / doctrinal terms
    'faamanuiaina': 'blessed',
    'faamanuiaga': 'blessing',
    'faavavau': 'everlasting/eternal',
    'meaalofa': 'gift',
    'faatulagaga': 'order',
    'toetutu': 'resurrection',
    'togaolive': 'olive vineyard',
    'faalilolilo': 'secret',
    'faaumatiaina': 'destroyed',
    'fanauina': 'begotten/born',
    'togiolaina': 'redeemed',
    'valaaulia': 'called/chosen',
    'fuafuaga': 'plan',
    'foafoaina': 'created',
    'faamaaa': 'hardened',
    'faatagataotauaina': 'captivity',
    'tumau': 'enduring/steadfast',
    'fetuu': 'cursed',

    # BOM / PGP proper nouns
    "sara'emila": 'Zarahemla',
    'saraemila': 'Zarahemla',
    'iareto': 'Jared',
    'amanaki': 'Ammonihah',
    'amonaia': 'Ammonihah',
    'koraiantama': 'Coriantumr',
    'sipelomu': 'Shiblom',
    'kupasa': 'Curelom',
    'limahi': 'Limhi',
    'korinere': 'Korihor',
    'pakasa': 'Pachus',
    'alamana': 'Alma',
    'nefi': 'Nephi',
    'moronaī': 'Moroni',
    'moronai': 'Moroni',
    'lamanā': 'Lamanites',
    'lamana': 'Lamanite',
    'nifai': 'Nephite',
    'nifaī': 'Nephites',
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

    # ============================================================
    # Morphological decomposition fallbacks (Samoan grammar rules)
    # Only used when the word is not in any dictionary
    # ============================================================
    _skip_glosses = {'the', 'a', 'an', 'to', 'of', 'in', 'and', 'but', 'or',
                     'for', 'at', 'by', 'from', 'with', 'on', 'some', 'this',
                     'that', 'those', 'these', 'which', 'who', 'whom',
                     '(tam)', '(part)', '(dir)', '(prep)'}

    # 1. Reciprocal verb: fe- + root + -ai/-a'i = "[root] one another"
    if w_norm.startswith('fe') and len(w_norm) > 4:
        root = None
        if w_norm.endswith("a'i") and len(w_norm) > 5:
            root = w_norm[2:-3]
        elif w_norm.endswith('ai') and len(w_norm) > 4:
            root = w_norm[2:-2]
        if root and len(root) >= 2:
            root_g = lookup_word(root)
            if root_g and root_g.lower() not in _skip_glosses:
                return f"{root_g} one another"

    # 2. Passive suffix: root + -ina = "was [root]ed" / "[root] (passive)"
    if w_norm.endswith('ina') and len(w_norm) > 5:
        root = w_norm[:-3]
        if len(root) >= 2:
            root_g = lookup_word(root)
            if root_g and root_g.lower() not in _skip_glosses:
                return root_g
        # Try -aina variant (root + a + ina)
        if w_norm.endswith('aina') and len(w_norm) > 6:
            root2 = w_norm[:-4]
            if len(root2) >= 2:
                root_g = lookup_word(root2)
                if root_g and root_g.lower() not in _skip_glosses:
                    return root_g

    # 3. Causative prefix: faa- + root = "cause to [root]" / "make [root]"
    #    Skip if root resolves to a proper noun (capitalized = place/person name)
    if w_norm.startswith('faa') and len(w_norm) > 5:
        root = w_norm[3:]
        if len(root) >= 2:
            root_g = lookup_word(root)
            if root_g and root_g.lower() not in _skip_glosses:
                # Don't apply "make X" if X is a proper noun
                if not root_g[0].isupper():
                    return f"make {root_g}"

    return ""


# ============================================================
# Phrase chunking rules
# ============================================================
# Words that START a new phrase (phrase boundaries)
PHRASE_STARTERS = {
    # Tense/aspect markers (start verb phrases)
    'ua', 'na', 'sa', 'e', "ole'a", "olo'o",
    # Conjunctions
    'ma', 'a',
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
            # Store both original and lowercase pairs for case-insensitive matching
            pairs.add((wds[idx], wds[idx+1]))
            pairs.add((wds[idx].lower(), wds[idx+1].lower()))
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
                elif c_prev1 == 'mavae':
                    pass  # "ua mavae ona" = after, keep together
                elif c_prev1 == 'faapefea':
                    pass  # "e faapefea ona" = how is it that, keep together
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

        # --- Forced break after "faapea ona", "mavae ona", etc. ---
        if not start_new and len(current) >= 2:
            c2 = [c.lower().strip('.,;:!?()\u201c\u201d\u201e') for c in current[-2:]]
            if c2 == ['faapea', 'ona'] or c2 == ['tatau', 'ona'] or c2 == ['uma', 'ona'] or c2 == ['lava', 'ona'] or c2 == ['pei', 'ona'] or c2 == ['mafai', 'ona'] or c2 == ['mavae', 'ona']:
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

        # --- Override: don't split if words belong to a known compound phrase ---
        # (unless it's a punctuation break)
        if start_new and current:
            is_punct_break = (i > 0 and any(prev_raw.rstrip(')').endswith(p) for p in (',', ';', '.', ':', '!')))
            if not is_punct_break:
                if (prev_clean, w_clean) in _PHRASE_PAIRS:
                    start_new = False

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
    # ============================================================
    # Directional verb compounds (ae=up, ifo=down, atu=forth/away)
    # ============================================================
    "alu ae": 'go up',
    "alu ifo": 'go down',
    "alu atu": 'go forth',
    "alu ane": 'go forth',
    "alu ese": 'go away',
    "sau ae": 'come up',
    "sau ifo": 'come down',
    "sau atu": 'come',
    "sau mai": 'come here',
    "oo atu": 'arrived',
    "oo mai": 'came',
    "oo ifo": 'came down',
    "oo ae": 'came up',
    "tepa ae": 'looked up',
    "tepa ifo": 'looked down',
    "vaai atu": 'looked toward',
    "vaai ifo": 'looked down',
    "vaai ae": 'looked up',
    "ilo atu": 'saw',
    "tulai ae": 'rose up',
    "oso ae": 'rose up',
    "savali atu": 'walked forth',
    "sola atu": 'fled',
    "sola ae": 'fled up',
    "ave ae": 'took up',
    "ave ifo": 'took down',
    "ave atu": 'took away',
    "tago ifo": 'reached down',
    "tago atu": 'reached out',
    "mamao atu": 'afar off',
    "tu mamao": 'stood afar',
    "asiasi atu": 'visited',
    "asiasi mai": 'visited (here)',
    "toe foi mai": 'returned',
    "toe foi atu": 'went back',
    "nofo ane": 'dwell there',
    "savavali ane": 'walk along',
    "iloa atu": 'see',

    # Compound noun phrases
    "galu teine": 'maidens',
    "auauna fafine": 'maidservant',
    "fafine failele": 'nursing woman',

    # Pronoun + tense compounds
    "ou te": 'I will',
    "tatou te": 'we will',
    "latou te": 'they will',
    "lua te": 'you two will',

    # Directional markers (spatial)
    "i tai": 'towards the sea',
    "i uta": 'inland',

    # Double pronoun patterns
    "ia ia": 'to him/her',

    # "O a'u o" = "I am" patterns
    "o a\u02bbu o": 'I am',
    # Knowledge/desire compounds
    "fia iloa": 'desire to know',

    # Common scripture phrases
    "sa oo ina": 'it came to pass',
    "a oo foi": 'and also came to pass',
    "ina seia": 'until',
    "ia te ia": 'to him/her',
    "sa i lea mea foi": 'and there were also',
    "i lea mea foi": 'there were also',
    "tama tane": 'sons',
    "tama teine": 'daughters',
    "le tama tane": 'the son',
    "le tama teine": 'the daughter',
    # BOM/D&C compound phrases
    "tumau faavavau": 'everlasting',
    "le fuafuaga tele": 'the great plan',
    "fuafuaga o le faaolataga": 'plan of salvation',
    "fuafuaga o le togiolaga": 'plan of redemption',
    "faapotopotoga faalilolilo": 'secret combinations',
    "galuega faalilolilo": 'secret works',
    "le meaalofa o le Agaga Paia": 'the gift of the Holy Ghost',
    "togaolive masani": 'tame olive tree',
    "togaolive vao": 'wild olive tree',
    "tutuli ese": 'cast out',
    "au faitaulaga": 'company of priests',
    "le au faitaulaga": 'the priests',

    # Grammatical compound phrases (global patterns)
    "o le a le uiga": 'what is the meaning',
    "o le a le uiga o": 'what is the meaning of',
    "o le tasi ma le isi": 'one with another',
    "e ala i le": 'through the',
    "e ala i": 'by means of',
    "mo le va o": 'for the space of',
    "E faapefea ona": 'how is it that',
    "e faapefea ona": 'how is it that',
    "Pe faapefea ona": 'how is it that',
    "pe faapefea ona": 'how is it that',
    "ina ia mafai ona": 'that it may be',
    "i aso e gata ai": 'in the latter days',
    "o se faatusa lea": 'it is a type/likeness',
    "o se faatusa lea o": 'it is a type of',
    "pe a mavae ona": 'after',
    "seia mavae ona": 'until after',
    "sa latou fai mai": 'they said',
    "sa latou fai mai ia te": 'they said unto',
    "o lenei": 'now',

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
    "va a'i": 'divide/separate',
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

    # Compass directions (compound phrases)
    "i sasae": 'eastward',
    "i sisifo": 'westward',
    "i matu": 'northward',
    "i toga": 'southward',
    "i le itu i sasae": 'on the east side',
    "i le itu i sisifo": 'on the west side',
    "i le itu i matu": 'on the north side',
    "i le itu i toga": 'on the south side',
    "le itu i sasae": 'the east side',
    "le itu i sisifo": 'the west side',
    "le itu i matu": 'the north side',
    "le itu i toga": 'the south side',
    "ma sasae": 'and eastward',
    "ma sisifo": 'and westward',

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
    'fai ane': 'said/spoke',
    'tuu ese': 'put away/remove',
    'sola ese': 'flee away/escape',
    'atua ese': 'foreign gods',
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
    'ia te oe': 'unto you',
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

    # ── Patterns learned from Genesis 1-12 manual overrides ──
    # High-frequency phrases found across the whole Bible
    "ona fanaua lea e ia": 'then he begot',
    "ma ua fanaua ai e ia": 'and he begot',
    "ona fanaua ai lea e ia": 'then he begot',
    "o atalii ma afafine": 'sons and daughters',
    "o ona tausaga ia": 'years',
    "ona oti ai lea": 'and he died',
    "i le lalolagi": 'on the earth',
    "faauta foi": 'and behold',
    "ua fetalai atu": 'said',
    "ua faapea atu": 'and said',
    "se a le mea": 'what',
    "o ai ea": 'who',
    "o le mea lea": 'therefore',
    "i le faitotoa": 'at the door',
    "i le eleele": 'the ground',
    "i le fogāeleele": 'the face of the earth',
    "i le fogāeleele uma": 'the face of all the earth',
    "i aso uma": 'all the days',
    "taulaga mu": 'burnt offerings',
    "ua mavae ia mea": 'after these things',
    "ua mavae foi ia mea": 'after these things also',
    "ua mavae lea mea": 'after that',
    "ua mavae ona": 'after',
    "na mavae ona": 'after',
    "sa mavae ona": 'after',
    "ua mavae": 'after',
    "na mavae": 'after',
    "sa mavae": 'after',
    "na mavae ia mea": 'after these things',
    "sa mavae ia mea": 'after these things',
    "na mavae lea mea": 'after that',
    "sa mavae lea mea": 'after that',
    "a e peitai": 'but',
    "i luma o ieova": 'before the LORD',
    "o loo faapea": 'saying',
    "le laueleele": 'the ground',
    "na fai atu": 'said',
    "ua faalogo": 'heard',
    "na iloa": 'knew',
    "ua iloa": 'knew',
    "ma tagata": 'and people',
    "o le aso": 'the day',
    "le agasala": 'sin',
    "le ala": 'the way',
    "e nonofo": 'to dwell',
    "ou te faia": 'I will make',
    "o mea uma": 'everything',
    "ma outou": 'with you',
    "faatasi ma oe": 'with you',
    "faatasi ma ia": 'with him',
    "ma lana avā": 'and his wife',
    "ma lau avā": 'and your wife',
    "lona atalii": 'his son',
    "o atalii": 'sons',
    "o tagata": 'of men',
    "la'u feagaiga": 'my covenant',
    "o le feagaiga": 'the covenant',
    "le nuanua": 'the rainbow',
    "i le ao": 'in the cloud',
    "e oo i": 'unto',
    "mea ola uma": 'all living things',
    "i mea ola uma": 'of all flesh',
    "o manu felelei": 'birds',
    "o le manu poa": 'the male',
    "ma le manu fafine": 'and the female',
    "ma manu vaefa": 'and cattle',
    "ma mea fetolofi": 'and creeping things',
    "e taitasi ma lona uiga": 'after its kind',
    "ia outou fanafanau": 'be fruitful',
    "ma ia uluola": 'and multiply',
    "ia faaolaina": 'to keep alive',
    "i o latou laueleele": 'in their lands',
    "i o latou aiga": 'in their clans',
    "i o latou nuu": 'in their nations',
    "ma a latou gagana": 'according to their languages',

    # Number patterns (high frequency in genealogies)
    "e iva selau": 'nine hundred',
    "e valu selau": 'eight hundred',
    "e fitu selau": 'seven hundred',
    "e ono selau": 'six hundred',
    "e lima selau": 'five hundred',
    "e fa selau": 'four hundred',
    "e tolu selau": 'three hundred',
    "e lua selau": 'two hundred',
    "ma le sefulu": 'and ten',
    "ma le luasefulu": 'and twenty',
    "ma le tolusefulu": 'and thirty',
    "ma le fagafulu": 'and forty',
    "ma le limagafulu": 'and fifty',
    "ma le onogafulu": 'and sixty',
    "ma le fitugafulu": 'and seventy',
    "ma le valugafulu": 'and eighty',
    "ma le ivagafulu": 'and ninety',
    "ma le lima": 'and five',
    "ma le lua": 'and two',
    "ma le tolu": 'and three',
    "ma le fa": 'and four',
    "ma le ono": 'and six',
    "ma le fitu": 'and seven',
    "ma le valu": 'and eight',
    "ma le iva": 'and nine',

    # Common verbal/discourse patterns
    "ona tali mai lea o ia": 'and he answered',
    "ua ia fetalai atu foi": 'and he also said',
    "na faapea atu": 'saying',
    "ua faapea mai": 'and said',
    "ma fetalai mai": 'and said',
    "ona valaau atu lea": 'then called',
    "fai atu lea o ia": 'he said',

    # Preposition + pronoun patterns
    "ia te oe": 'unto you',
    "ia te au": 'unto me',
    "ia te ia": 'to him',
    "ia te i latou": 'unto them',
    "ia te i laua": 'unto them',
    "ia te outou": 'unto you',
    "ia te i tatou": 'unto us',

    # Common name patterns
    "ia noa": 'to Noah',
    "e noa": 'Noah',
    "o semu": 'Shem',
    "ma hamo": 'Ham',
    "o kaino": 'Cain',
    "e atamu": 'Adam',
    "o enoka": 'Enoch',
    "o ieova": 'the LORD',
    "e ieova": 'the LORD',
    "e le atua": 'God',
    "e ieova le atua": 'the LORD God',
}

# Now build the phrase pairs set (must be after WHOLE_PHRASES is defined)
_PHRASE_PAIRS = _build_phrase_pairs()


# ---- Past tense conversion for TAM marker support ----
# When ua/sa/na precede a verb, the verb should be glossed in past tense.
_PAST_TENSE = {
    # Common irregular verbs
    'make': 'made', 'come': 'came', 'say': 'said', 'give': 'gave',
    'do': 'did', 'see': 'saw', 'go': 'went', 'take': 'took',
    'know': 'knew', 'speak': 'spoke', 'write': 'wrote', 'rise': 'rose',
    'begin': 'began', 'eat': 'ate', 'drink': 'drank', 'fall': 'fell',
    'find': 'found', 'get': 'got', 'have': 'had', 'hear': 'heard',
    'hold': 'held', 'keep': 'kept', 'lead': 'led', 'leave': 'left',
    'let': 'let', 'lie': 'lay', 'lose': 'lost', 'meet': 'met',
    'pay': 'paid', 'put': 'put', 'read': 'read', 'run': 'ran',
    'send': 'sent', 'set': 'set', 'sit': 'sat', 'stand': 'stood',
    'teach': 'taught', 'tell': 'told', 'think': 'thought',
    'understand': 'understood', 'wake': 'woke', 'wear': 'wore',
    'win': 'won', 'bring': 'brought', 'build': 'built',
    'buy': 'bought', 'catch': 'caught', 'choose': 'chose',
    'draw': 'drew', 'drive': 'drove', 'feel': 'felt',
    'fight': 'fought', 'fly': 'flew', 'forget': 'forgot',
    'grow': 'grew', 'hang': 'hung', 'hide': 'hid',
    'hit': 'hit', 'lay': 'laid', 'seek': 'sought',
    'sell': 'sold', 'shine': 'shone', 'shoot': 'shot',
    'show': 'showed', 'sing': 'sang', 'sleep': 'slept',
    'spend': 'spent', 'spread': 'spread', 'steal': 'stole',
    'strike': 'struck', 'swear': 'swore', 'swim': 'swam',
    'tear': 'tore', 'throw': 'threw', 'bind': 'bound',
    'bite': 'bit', 'bleed': 'bled', 'blow': 'blew',
    'break': 'broke', 'burn': 'burned', 'cut': 'cut',
    'dig': 'dug', 'feed': 'fed', 'forgive': 'forgave',
    'freeze': 'froze', 'grind': 'ground', 'hurt': 'hurt',
    'kneel': 'knelt', 'lend': 'lent', 'mean': 'meant',
    'overcome': 'overcame', 'ride': 'rode', 'ring': 'rang',
    'shake': 'shook', 'shed': 'shed', 'shut': 'shut',
    'slide': 'slid', 'spin': 'spun', 'split': 'split',
    'spring': 'sprang', 'stick': 'stuck', 'sting': 'stung',
    'stride': 'strode', 'string': 'strung',
    'sweep': 'swept', 'swing': 'swung', 'weave': 'wove',
    'weep': 'wept', 'wind': 'wound', 'wring': 'wrung',
    'is': 'was', 'are': 'were', 'am': 'was',
    'bear': 'bore', 'become': 'became', 'be': 'was',
    'arise': 'arose', 'awake': 'awoke',
    # Bible/BofM specific irregular verbs
    'smite': 'smote', 'slay': 'slew', 'behold': 'beheld',
    'dwell': 'dwelt', 'forsake': 'forsook', 'beget': 'begat',
    'cleave': 'clove', 'strive': 'strove', 'forbid': 'forbade',
    # Verbs that stay the same in past tense
    'cast': 'cast', 'cost': 'cost', 'quit': 'quit',
    'born': 'born', 'shut': 'shut', 'rid': 'rid',
    # Common regular verbs (Bible/BofM glosses)
    'call': 'called', 'look': 'looked', 'turn': 'turned',
    'return': 'returned', 'answer': 'answered', 'gather': 'gathered',
    'scatter': 'scattered', 'destroy': 'destroyed', 'establish': 'established',
    'command': 'commanded', 'prepare': 'prepared', 'deliver': 'delivered',
    'remember': 'remembered', 'promise': 'promised', 'declare': 'declared',
    'refuse': 'refused', 'move': 'moved', 'place': 'placed',
    'name': 'named', 'offer': 'offered', 'pray': 'prayed',
    'obey': 'obeyed', 'rule': 'ruled', 'reign': 'reigned',
    'suffer': 'suffered', 'perish': 'perished', 'rejoice': 'rejoiced',
    'mourn': 'mourned', 'grieve': 'grieved', 'fear': 'feared',
    'walk': 'walked', 'follow': 'followed', 'remain': 'remained',
    'hope': 'hoped', 'trust': 'trusted', 'repent': 'repented',
    'baptize': 'baptized', 'prophesy': 'prophesied', 'worship': 'worshipped',
    'cry': 'cried', 'die': 'died', 'live': 'lived', 'love': 'loved',
    'judge': 'judged', 'believe': 'believed', 'save': 'saved',
    'serve': 'served', 'praise': 'praised', 'create': 'created',
    'bless': 'blessed', 'curse': 'cursed', 'receive': 'received',
    'fill': 'filled', 'open': 'opened', 'close': 'closed',
    'finish': 'finished', 'start': 'started', 'pass': 'passed',
    'cross': 'crossed', 'enter': 'entered', 'depart': 'departed',
    'arrive': 'arrived', 'travel': 'traveled', 'journey': 'journeyed',
    'ask': 'asked', 'help': 'helped', 'work': 'worked',
    'lift': 'lifted', 'raise': 'raised', 'lower': 'lowered',
    'cover': 'covered', 'uncover': 'uncovered', 'change': 'changed',
    'touch': 'touched', 'reach': 'reached', 'search': 'searched',
    'want': 'wanted', 'need': 'needed', 'wish': 'wished',
    'end': 'ended', 'last': 'lasted', 'wait': 'waited',
    'watch': 'watched', 'guard': 'guarded', 'protect': 'protected',
    'heal': 'healed', 'harm': 'harmed', 'kill': 'killed',
    'spare': 'spared', 'warn': 'warned', 'punish': 'punished',
    'reward': 'rewarded', 'honor': 'honored', 'thank': 'thanked',
    'test': 'tested', 'try': 'tried', 'fail': 'failed',
    'succeed': 'succeeded', 'prosper': 'prospered', 'increase': 'increased',
    'decrease': 'decreased', 'multiply': 'multiplied', 'divide': 'divided',
    'separate': 'separated', 'join': 'joined', 'unite': 'united',
    'plant': 'planted', 'harvest': 'harvested', 'reap': 'reaped',
    'sow': 'sowed', 'pour': 'poured', 'pour': 'poured',
    'wash': 'washed', 'clean': 'cleaned', 'cleanse': 'cleansed',
    'anoint': 'anointed', 'consecrate': 'consecrated', 'sanctify': 'sanctified',
    'purify': 'purified', 'redeem': 'redeemed', 'atone': 'atoned',
    'reveal': 'revealed', 'respond': 'responded', 'proclaim': 'proclaimed',
    'preach': 'preached', 'teach': 'taught', 'learn': 'learned',
    'number': 'numbered', 'count': 'counted', 'mark': 'marked',
    'seal': 'sealed', 'sign': 'signed', 'record': 'recorded',
    'dwell': 'dwelt', 'settle': 'settled', 'camp': 'camped',
    'pitch': 'pitched', 'march': 'marched', 'conquer': 'conquered',
    'surrender': 'surrendered', 'capture': 'captured', 'free': 'freed',
    'release': 'released', 'allow': 'allowed', 'permit': 'permitted',
    'deny': 'denied', 'reject': 'rejected', 'accept': 'accepted',
    'agree': 'agreed', 'promise': 'promised', 'vow': 'vowed',
    'swear': 'swore', 'pledge': 'pledged', 'devote': 'devoted',
    'commit': 'committed', 'transgress': 'transgressed', 'sin': 'sinned',
    'err': 'erred', 'wander': 'wandered', 'stray': 'strayed',
    'gather': 'gathered', 'assemble': 'assembled', 'collect': 'collected',
    'distribute': 'distributed', 'share': 'shared', 'inherit': 'inherited',
    'possess': 'possessed', 'own': 'owned', 'claim': 'claimed',
    'desire': 'desired', 'covet': 'coveted', 'envy': 'envied',
    'hate': 'hated', 'despise': 'despised', 'mock': 'mocked',
    'scorn': 'scorned', 'persecute': 'persecuted', 'oppress': 'oppressed',
    'afflict': 'afflicted', 'torment': 'tormented', 'torture': 'tortured',
    'execute': 'executed', 'appoint': 'appointed', 'ordain': 'ordained',
    'commission': 'commissioned', 'charge': 'charged', 'instruct': 'instructed',
    'counsel': 'counseled', 'advise': 'advised', 'guide': 'guided',
    'direct': 'directed', 'lead': 'led', 'govern': 'governed',
    'minister': 'ministered', 'administer': 'administered',
    'perform': 'performed', 'accomplish': 'accomplished', 'fulfill': 'fulfilled',
    'complete': 'completed', 'perfect': 'perfected',
    'cause': 'caused', 'require': 'required', 'demand': 'demanded',
    'order': 'ordered', 'decree': 'decreed', 'proclaim': 'proclaimed',
    'announce': 'announced', 'report': 'reported', 'testify': 'testified',
    'witness': 'witnessed', 'confirm': 'confirmed', 'prove': 'proved',
    'show': 'showed', 'demonstrate': 'demonstrated', 'display': 'displayed',
    'appear': 'appeared', 'disappear': 'disappeared', 'vanish': 'vanished',
    'prevail': 'prevailed', 'overcome': 'overcame', 'conquer': 'conquered',
    'resist': 'resisted', 'endure': 'endured', 'persevere': 'persevered',
    'continue': 'continued', 'cease': 'ceased', 'stop': 'stopped',
    'pause': 'paused', 'rest': 'rested', 'sleep': 'slept',
    'add': 'added', 'remove': 'removed', 'supply': 'supplied',
    'provide': 'provided', 'sustain': 'sustained', 'support': 'supported',
    'nourish': 'nourished', 'feed': 'fed', 'starve': 'starved',
    'thirst': 'thirsted', 'hunger': 'hungered',
    'carry': 'carried', 'drag': 'dragged', 'pull': 'pulled',
    'push': 'pushed', 'drop': 'dropped', 'pick': 'picked',
    'select': 'selected', 'choose': 'chose', 'prefer': 'preferred',
    'decide': 'decided', 'determine': 'determined', 'resolve': 'resolved',
    'plan': 'planned', 'intend': 'intended', 'propose': 'proposed',
    'suggest': 'suggested', 'mention': 'mentioned', 'refer': 'referred',
    'describe': 'described', 'explain': 'explained', 'interpret': 'interpreted',
    'translate': 'translated', 'express': 'expressed', 'utter': 'uttered',
    'exclaim': 'exclaimed', 'whisper': 'whispered', 'shout': 'shouted',
    'murmur': 'murmured', 'complain': 'complained', 'groan': 'groaned',
    'sigh': 'sighed', 'laugh': 'laughed', 'smile': 'smiled',
    'weep': 'wept', 'sob': 'sobbed', 'lament': 'lamented',
    'stretch': 'stretched', 'extend': 'extended', 'expand': 'expanded',
    'contract': 'contracted', 'wrap': 'wrapped', 'fold': 'folded',
    'tie': 'tied', 'bind': 'bound', 'loose': 'loosed',
    'fasten': 'fastened', 'attach': 'attached', 'detach': 'detached',
    'mix': 'mixed', 'blend': 'blended', 'combine': 'combined',
    'compare': 'compared', 'liken': 'likened', 'resemble': 'resembled',
    'differ': 'differed', 'distinguish': 'distinguished',
    'notice': 'noticed', 'observe': 'observed', 'examine': 'examined',
    'inspect': 'inspected', 'investigate': 'investigated',
    'discover': 'discovered', 'detect': 'detected', 'recognize': 'recognized',
    'identify': 'identified', 'realize': 'realized', 'notice': 'noticed',
    'imagine': 'imagined', 'suppose': 'supposed', 'assume': 'assumed',
    'conclude': 'concluded', 'infer': 'inferred', 'deduce': 'deduced',
    'reason': 'reasoned', 'argue': 'argued', 'debate': 'debated',
    'discuss': 'discussed', 'contend': 'contended', 'dispute': 'disputed',
    'quarrel': 'quarreled', 'wrestle': 'wrestled', 'struggle': 'struggled',
    'battle': 'battled', 'war': 'warred', 'fight': 'fought',
    'attack': 'attacked', 'defend': 'defended', 'retreat': 'retreated',
    'flee': 'fled', 'escape': 'escaped', 'hide': 'hid',
    'pursue': 'pursued', 'chase': 'chased', 'hunt': 'hunted',
    'trap': 'trapped', 'snare': 'snared', 'seize': 'seized',
    'grab': 'grabbed', 'grasp': 'grasped', 'grip': 'gripped',
    'release': 'released', 'free': 'freed', 'liberate': 'liberated',
    'rescue': 'rescued', 'save': 'saved', 'preserve': 'preserved',
    'maintain': 'maintained', 'repair': 'repaired', 'restore': 'restored',
    'renew': 'renewed', 'refresh': 'refreshed', 'revive': 'revived',
    'strengthen': 'strengthened', 'weaken': 'weakened',
    'empower': 'empowered', 'enable': 'enabled',
    'exist': 'existed', 'occur': 'occurred', 'happen': 'happened',
    'result': 'resulted', 'follow': 'followed', 'precede': 'preceded',
    'surpass': 'surpassed', 'exceed': 'exceeded', 'excel': 'excelled',
    'progress': 'progressed', 'advance': 'advanced', 'proceed': 'proceeded',
    'approach': 'approached', 'retreat': 'retreated', 'withdraw': 'withdrew',
    'remove': 'removed', 'place': 'placed', 'position': 'positioned',
    'arrange': 'arranged', 'organize': 'organized', 'sort': 'sorted',
    'classify': 'classified', 'rank': 'ranked', 'rate': 'rated',
    'measure': 'measured', 'weigh': 'weighed', 'balance': 'balanced',
}

# Words that should NOT get past-tense conversion (non-verb glosses)
_NO_PAST_TENSE = frozenset({
    'the', 'a', 'an', 'of', 'in', 'to', 'for', 'by', 'from', 'with',
    'on', 'at', 'and', 'but', 'or', 'not', 'also', 'only', 'then',
    'there', 'here', 'this', 'that', 'these', 'those', 'some', 'all',
    'every', 'many', 'much', 'great', 'good', 'evil', 'true', 'holy',
    'righteous', 'wicked', 'together', 'always', 'never', 'again',
    'now', 'still', 'very', 'more', 'most', 'other', 'each',
    'above', 'below', 'before', 'after', 'between', 'among',
    'up', 'down', 'out', 'into', 'upon', 'unto', 'toward',
    'like', 'as', 'so', 'if', 'when', 'while', 'until',
    'who', 'whom', 'whose', 'what', 'which', 'where', 'why', 'how',
    'one', 'two', 'three', 'four', 'five', 'six', 'seven',
    'eight', 'nine', 'ten', 'hundred', 'thousand',
    # Common adjectives (should not get -ed suffix after TAM markers)
    'beautiful', 'strong', 'weak', 'old', 'young', 'new', 'clean',
    'unclean', 'rich', 'poor', 'wise', 'foolish', 'full', 'empty',
    'high', 'low', 'long', 'short', 'deep', 'wide', 'narrow',
    'precious', 'sacred', 'bitter', 'sweet', 'dry', 'wet',
    'heavy', 'light', 'dark', 'bright', 'thick', 'thin',
    'glad', 'angry', 'afraid', 'ashamed', 'ready', 'able',
    'worthy', 'faithful', 'known', 'unknown', 'indeed', 'enough',
    'sick', 'well', 'whole', 'firm', 'clear', 'near', 'far',
    'hard', 'soft', 'rough', 'smooth', 'bare', 'fierce',
})

def _to_past_tense(gloss):
    """Convert an English verb gloss to past tense.
    Handles irregular verbs via map, regular verbs via -ed rules.
    For slash alternatives (make/do), converts only the first word.
    Skips nouns, adjectives, and other non-verb glosses."""
    if not gloss:
        return gloss

    # Handle slash alternatives: convert first word only
    parts = gloss.split('/')
    first_part = parts[0]

    # Handle multi-word glosses: convert only the first word
    words = first_part.split()
    verb = words[0].lower()

    # Skip if already past tense (-ed ending)
    if verb.endswith('ed') and verb not in ('need', 'feed', 'seed', 'speed', 'bleed'):
        return gloss

    # Skip non-verb words (articles, prepositions, adjectives, etc.)
    if verb in _NO_PAST_TENSE:
        return gloss

    # Skip words already in irregular past form (e.g. "arose", "went")
    if verb in _PAST_TENSE.values():
        return gloss

    # Check verb map (irregular + common regular verbs)
    if verb in _PAST_TENSE:
        words[0] = _PAST_TENSE[verb]
        parts[0] = ' '.join(words)
        return '/'.join(parts)

    # Unknown word — not in our verb map, leave unchanged
    # (avoids false positives on nouns, adjectives, pronouns, etc.)
    return gloss


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
    tam_context = None  # Track active TAM marker for verb tense modification
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
                _phrase_gloss = WHOLE_PHRASES[_mk]
                # Apply TAM verb tense modification to compound phrase
                if tam_context == 'past':
                    _p_past = _to_past_tense(_phrase_gloss)
                    if _p_past != _phrase_gloss:
                        _phrase_gloss = _p_past
                        tam_context = None  # consumed
                glosses.append(_phrase_gloss)
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

        # Tense markers — affect verb tense of following word
        # TAM + "le" = negative construction → output "not"
        # "na te [verb]" = pronoun "he/she/it" + past tense verb
        if cl == 'na' and idx + 1 < len(clean_words):
            next_cl = clean_words[idx+1].lower().strip('.,;:!?()\u201c\u201d\u201e')
            if next_cl == 'te':
                glosses.append('he/she/it')
                tam_context = 'past'  # na is still past tense marker
                continue
        if cl in ('ua', 'na', 'sa', "ole'a", "ole\u02bba", "olo'o", "olo\u02bbo"):
            # "sa" + proper noun = clan/family marker, NOT past tense
            # e.g., "sa Levī" = "of the clan of Levi"
            if cl == 'sa' and idx + 1 < len(clean_words):
                next_raw = words[idx+1].strip('.,;:!?()\u201c\u201d\u201e\u2018\u2019')
                if next_raw and next_raw[0].isupper():
                    glosses.append('of the clan of')
                    continue
            # Check if followed by "le" (negation) — produce "not"
            if idx + 1 < len(clean_words):
                next_cl = clean_words[idx+1].lower().strip('.,;:!?()\u201c\u201d\u201e')
                if next_cl == 'le':
                    # Check if le + verb (not le + noun/article use)
                    if idx + 2 < len(clean_words):
                        after_le = clean_words[idx+2].lower().strip('.,;:!?()\u201c\u201d\u201e')
                        after_g = lookup_word(clean_words[idx+2])
                        # If word after "le" is a known verb/adj (not article+noun pattern)
                        # Heuristic: "le" + lowercase word that has a gloss = negation
                        if after_g and after_g not in ('the', 'a', 'some', 'in', 'by', 'and', 'for', 'to', 'of', 'from'):
                            glosses.append('not')
                            skip_next = True  # skip the "le"
                            continue
                    else:
                        # "le" at end of chunk — likely negation
                        glosses.append('not')
                        skip_next = True
                        continue
            # Set TAM context for verb tense modification on next content word
            if cl in ('ua', 'na', 'sa'):
                tam_context = 'past'
            continue

        # "aua le" / "auā le" = prohibitive "do not" (not "for the")
        if cl in ('aua', 'auā') and idx + 1 < len(clean_words):
            next_cl = clean_words[idx+1].lower().strip('.,;:!?()\u201c\u201d\u201e')
            if next_cl == 'le':
                if idx + 2 < len(clean_words):
                    after_le = clean_words[idx+2].lower().strip('.,;:!?()\u201c\u201d\u201e')
                    after_g = lookup_word(clean_words[idx+2])
                    if after_g and after_g not in ('the', 'a', 'some', 'in', 'by', 'and', 'for', 'to', 'of', 'from'):
                        glosses.append('do not')
                        skip_next = True
                        continue
                else:
                    glosses.append('do not')
                    skip_next = True
                    continue

        if cl == 'ona' and pos_in_remainder == 0:
            glosses.append('and')
            continue

        # Common particles — skip in gloss
        if cl in ('ai', "a'i", 'lea', 'te'):
            continue

        # "o" — at start of phrase = predicate marker (skip), mid-phrase = "of"
        if cl == 'o':
            if pos_in_remainder == 0:
                continue  # sentence-initial predicate marker
            else:
                glosses.append('of')
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

        # "ae" — directional particle "up" after a verb, "but" as conjunction
        if cl == 'ae':
            if pos_in_remainder == 0:
                glosses.append('but')  # clause-initial = conjunction
            else:
                glosses.append('up')   # after a verb = directional
            continue

        # "ifo" — directional particle "down"
        if cl == 'ifo':
            glosses.append('down')
            continue

        # Dictionary lookup
        g = lookup_word(clean)
        if g and not g.startswith('('):
            # Apply TAM verb tense modification to first verb after marker
            # Only consume TAM context if the word actually changes (is a verb)
            if tam_context == 'past' and not (clean and clean[0].isupper()):
                g_past = _to_past_tense(g)
                if g_past != g:
                    g = g_past
                    tam_context = None  # consumed — verb got past tense
                # else: non-verb word, TAM passes through to next word
            glosses.append(g)
        elif g and g.startswith('('):
            # Skip grammatical markers like (past), (perf), (dir)
            # TAM context passes through particles (not consumed)
            continue
        else:
            # Unknown word — if it starts with uppercase, keep it (proper name)
            if clean and clean[0].isupper():
                glosses.append(clean)
                tam_context = None  # reset on proper noun
            else:
                glosses.append(clean.lower())
                tam_context = None  # reset on unknown word

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


# Per-verse chunk overrides: bypass the chunker entirely for specific verses.
# Each entry is a list of [samoan_chunk, english_gloss] pairs.
MANUAL_CHUNK_OVERRIDES = {
    'Genesis|1|1': [
        ['Na faia e le Atua', 'God created'],
        ['le lagi', 'the heavens'],
        ['ma le lalolagi', 'and the earth'],
        ['i le amataga.', 'in the beginning'],
    ],
    'Genesis|1|2': [
        ['Sa soona nunumi le lalolagi', 'the earth was without form'],
        ['ma ua gaogao,', 'and void'],
        ['sa ufitia foi le moana', 'and darkness covered the deep'],
        ['i le pouliuli;', 'with darkness'],
        ['na fegaoioiai foi le Agaga o le Atua', 'and the Spirit of God moved'],
        ['i le fogātai.', 'upon the face of the waters'],
    ],
    'Genesis|1|3': [
        ['Ua fetalai mai le Atua,', 'And God said'],
        ['Ia malamalama;', 'Let there be light'],
        ['ona malamalama ai lea.', 'and there was light'],
    ],
    'Genesis|1|4': [
        ['Ua silasila atu le Atua', 'And God saw'],
        ['i le malamalama,', 'the light'],
        ['ua lelei;', 'that it was good'],
        ['ona tuu eseese ai lea e le Atua', 'and God divided'],
        ['o le malamalama', 'the light'],
        ['ma le pouliuli.', 'from the darkness'],
    ],
    'Genesis|1|5': [
        ['Ua faaigoa e le Atua', 'And God called'],
        ['le malamalama,', 'the light'],
        ['O le ao;', 'Day'],
        ['a ua faaigoa e ia', 'and He called'],
        ['le pouliuli,', 'the darkness'],
        ['O le po.', 'Night'],
        ['O le afiafi ma le taeao', 'and the evening and the morning'],
        ['o le uluai aso lea.', 'were the first day'],
    ],
    'Genesis|1|6': [
        ['Ua fetalai mai foi le Atua,', 'And God said'],
        ['Ia i le va', 'Let there be space'],
        ['o vai', 'of water'],
        ['le vanimonimo,', 'the firmament'],
        ["e va a'i", 'to separate'],
        ['isi vai', 'water'],
        ['ma isi vai.', 'from the water'],
    ],
    'Genesis|1|7': [
        ['Ua faia e le Atua', 'And God made'],
        ['le va nimonimo,', 'the firmament'],
        ["ua va a'i", 'and divided'],
        ['vai', 'the waters'],
        ['i lalo', 'under'],
        ['o le vanimonimo', 'the firmament'],
        ['ma vai', 'and waters'],
        ['i luga', 'above'],
        ['o le vanimonimo;', 'the firmament'],
        ['i le ua faapea lava.', 'and it was so'],
    ],
    'Genesis|1|8': [
        ['Ua faaigoa e le Atua', 'And God called'],
        ['le vanimonimo,', 'the firmament'],
        ['O le lagi.', 'Heaven'],
        ['O le afiafi ma le taeao', 'and the evening and the morning'],
        ['o le aso lua lea.', 'were the second day'],
    ],
    'Genesis|1|9': [
        ['Ua fetalai mai foi le Atua,', 'And God said also'],
        ['Ia potopoto', 'gather together'],
        ['i le mea e tasi', 'into one place'],
        ['o vai', 'the waters'],
        ['i lalo o le lagi,', 'under the heaven'],
        ['ia iloa foi', 'let be seen also'],
        ['le eleele matutu;', 'the dry land'],
        ['i le ua faapea lava.', 'and it was so'],
    ],
    'Genesis|1|10': [
        ['Ua faaigoa e le Atua', 'And God called'],
        ['le eleele matutu,', 'the dry land'],
        ['O le eleele;', 'Earth'],
        ['a ua faaigoa e ia', 'and He called'],
        ['le faapotopotoga o vai,', 'the gathering of the waters'],
        ['O le sami;', 'Seas'],
        ['ua silasila atu i ai le Atua,', 'and God saw'],
        ['ua lelei.', 'that it was good'],
    ],
    'Genesis|1|11': [
        ['Ona fetalai mai lea o le Atua,', 'Then God said'],
        ['Ia tupu', 'Let bring forth'],
        ["le vao mu'a", 'the tender grass'],
        ['mai le eleele,', 'from the earth'],
        ['ma le laau afu', 'and the herb'],
        ['e tupu ma ona fua,', 'yielding seed'],
        ['ma le laau', 'and the tree'],
        ["e 'aina ona fua,", 'bearing fruit'],
        ['e fua mai e taitasi', 'producing according to each'],
        ['ma lona uiga,', 'its kind'],
        ['o ia te ia lava', 'in itself'],
        ['o ona fatu', 'its seed'],
        ['i luga o le eleele;', 'upon the earth'],
        ['i le ua faapea lava.', 'and it was so'],
    ],
    'Genesis|1|12': [
        ['Ona tupu mai lea', 'And it brought forth'],
        ['i le eleele', 'from the earth'],
        ["le vao mu'a", 'the tender grass'],
        ['ma le laau afu', 'and the herb'],
        ['e fua mai,', 'yielding seed'],
        ['e taitasi', 'each one'],
        ['ma lona uiga,', 'its kind'],
        ['ma le laau', 'and the tree'],
        ["e 'aina ona fua,", 'bearing fruit'],
        ['o ia te ia lava', 'in itself'],
        ['ona fatu,', 'its seed'],
        ['e taitasi', 'each one'],
        ['ma lona uiga;', 'its kind'],
        ['ua silasila atu i ai le Atua,', 'And God saw'],
        ['ua lelei.', 'that it was good'],
    ],
    'Genesis|1|13': [
        ['O le afiafi ma le taeao', 'And the evening and the morning'],
        ['o le aso tolu lea.', 'were the third day'],
    ],
    'Genesis|1|14': [
        ['Ua fetalai mai foi le Atua,', 'And God said also'],
        ['Ia iai', 'Let there be'],
        ['i le vanimonimo o le lagi', 'in the firmament of the heaven'],
        ["o mea e malamalama a'i,", 'things for giving light'],
        ['e iloga ai', 'to divide'],
        ['le ao ma le po;', 'the day and the night'],
        ['ia fai foi', 'and let them be also'],
        ['ma faailoga,', 'for signs'],
        ['ma tau,', 'and seasons'],
        ['ma aso,', 'and days'],
        ['ma tausaga.', 'and years'],
    ],
    'Genesis|1|15': [
        ["Ma ia fai ma mea e malamalama a'i", 'And let them be for lights'],
        ['i le vanimonimo o le lagi,', 'in the firmament of heaven'],
        ["e faamalamalama a'i le lalolagi;", 'to give light upon the earth'],
        ['i le ua faapea lava.', 'and it was so'],
    ],
    'Genesis|1|16': [
        ['Ona faia lea e le Atua', 'And God made'],
        ['o malamalama tetele e lua;', 'two great lights'],
        ['o le malamalama tele', 'the greater light'],
        ['e pule i le ao,', 'to rule the day'],
        ['a o le malamalama itiiti', 'and the lesser light'],
        ['e pule i le po;', 'to rule the night'],
        ['ua na faia foi fetu.', 'He made the stars also'],
    ],
    'Genesis|1|17': [
        ['Ua tuu ai e le Atua', 'And God set them'],
        ['i le vanimonimo o le lagi', 'in the firmament of heaven'],
        ["e faamalamalama a'i le lalolagi;", 'to give light upon the earth'],
    ],
    'Genesis|1|18': [
        ['e pule foi i le ao ma le po,', 'and to rule over the day and the night'],
        ['ma ia iloga ai le malamalama', 'and to divide the light'],
        ['ma le pouliuli;', 'from the darkness'],
        ['ua silasila atu i ai le Atua,', 'and God saw'],
        ['ua lelei.', 'that it was good'],
    ],
    'Genesis|1|19': [
        ['O le afiafi ma le taeao', 'And the evening and the morning'],
        ['o le aso fa lea.', 'were the fourth day'],
    ],
    'Genesis|1|20': [
        ['Ua fetalai mai foi le Atua,', 'And God said'],
        ['Ia tele ona tutupu mai i le sami', 'Let the waters bring forth abundantly'],
        ['o meaola e fetolofi,', 'moving creatures that have life'],
        ['ia lele foi le manulele', 'and let birds fly'],
        ['i luga o le laueleele', 'above the earth'],
        ['i le vanimonimo o le lagi.', 'in the firmament of heaven'],
    ],
    'Genesis|1|21': [
        ['Ua faia foi e le Atua', 'And God created'],
        ['o tanimo tetele', 'great whales'],
        ['ma meaola uma e fetolofi,', 'and every living creature that moves'],
        ['ua tele ona tutupu mai i le sami,', 'which the waters brought forth abundantly'],
        ['e taitasi ma lona uiga,', 'after their kind'],
        ['ma manu felelei', 'and every winged bird'],
        ['e taitasi ma lona uiga;', 'after its kind'],
        ['ua silasila atu i ai le Atua,', 'and God saw'],
        ['ua lelei.', 'that it was good'],
    ],
    'Genesis|1|22': [
        ['Ona faamanuia atu i ai lea e le Atua,', 'And God blessed them'],
        ['ua faapea atu,', 'saying'],
        ['Ia uluola,', 'Be fruitful'],
        ['ma ia tupu tele,', 'and multiply'],
        ['ma ia tumu ai le sami;', 'and fill the seas'],
        ['ia tupu tele foi manu felelei', 'and let birds multiply'],
        ['i le laueleele.', 'on the earth'],
    ],
    'Genesis|1|23': [
        ['O le afiafi ma le taeao', 'And the evening and the morning'],
        ['o le aso lima lea.', 'were the fifth day'],
    ],
    'Genesis|1|24': [
        ['Ua fetalai mai foi le Atua,', 'And God said'],
        ['Ia tutupu meaola', 'Let the earth bring forth living creatures'],
        ['mai le laueleele,', 'from the earth'],
        ['e taitasi ma lona uiga,', 'after its kind'],
        ['o manu vaefa fanua,', 'cattle'],
        ['ma mea fetolofi,', 'and creeping things'],
        ['ma manu vaefa o le vao,', 'and beasts of the earth'],
        ['e taitasi ma lona uiga;', 'after its kind'],
        ['i le ua faapea lava.', 'and it was so'],
    ],
    'Genesis|1|25': [
        ['Ua faia foi e le Atua', 'And God made'],
        ['o manu vaefa o le vao,', 'the beasts of the earth'],
        ['e taitasi ma lona uiga,', 'after their kind'],
        ['ma manu vaefa fanua,', 'and cattle'],
        ['e taitasi ma lona uiga,', 'after their kind'],
        ['atoa ma mea fetolofi uma', 'and every creeping thing'],
        ['i le eleele,', 'upon the earth'],
        ['e taitasi ma lona uiga;', 'after its kind'],
        ['ua silasila atu i ai le Atua,', 'and God saw'],
        ['ua lelei.', 'that it was good'],
    ],
    'Genesis|1|26': [
        ['Ona fetalai ane lea o le Atua,', 'And God said'],
        ['Ina tatou faia ia o le tagata', 'Let us make man'],
        ['i lo tatou faatusa,', 'in our image'],
        ['ia foliga ia i tatou;', 'after our likeness'],
        ['ia pule foi i latou', 'and let them have dominion'],
        ["i i'a i le sami,", 'over the fish of the sea'],
        ['ma manu felelei,', 'and over the birds'],
        ['ma manu vaefa,', 'and over the cattle'],
        ['ma le laueleele uma,', 'and over all the earth'],
        ['atoa ma mea fetolofi uma', 'and over every creeping thing'],
        ['e fetolofi i le eleele.', 'that creeps upon the earth'],
    ],
    'Genesis|1|27': [
        ['Ona faia lea e le Atua', 'So God created'],
        ['o le tagata i lona faatusa,', 'man in His own image'],
        ['o le faatusa o le Atua', 'in the image of God'],
        ['na ia faia ai o ia;', 'He created him'],
        ['na faia e ia o i laua', 'He created them'],
        ['o le tane ma le fafine.', 'male and female'],
    ],
    'Genesis|1|28': [
        ['Ua faamanuia foi e le Atua', 'And God blessed'],
        ['ia te i laua,', 'them'],
        ['ma ua fetalai atu le Atua', 'and God said'],
        ['ia te i laua,', 'unto them'],
        ['Ia fanafanau ia,', 'Be fruitful'],
        ['ma ia uluola,', 'and multiply'],
        ['ma ia tumu ai le lalolagi,', 'and fill the earth'],
        ['ia faatoilalo i ai,', 'and subdue it'],
        ["ma ia pule i i'a i le sami,", 'and have dominion over the fish of the sea'],
        ['ma manu felelei,', 'and over the birds'],
        ['atoa ma mea ola uma', 'and over every living thing'],
        ['e fetolofi i le eleele.', 'that moves upon the earth'],
    ],
    'Genesis|1|29': [
        ['Ua fetalai atu foi le Atua,', 'And God said'],
        ['Faauta,', 'Behold'],
        ['ua ou foai atu ia te oulua', 'I have given you'],
        ['o laau afu uma e tutupu', 'every herb bearing seed'],
        ['ma o latou fua o', 'which is'],
        ['i le fogāeleele uma lava,', 'upon the face of all the earth'],
        ['atoa ma laau uma', 'and every tree'],
        ['ua iai le fua o le laau', 'in which is the fruit of a tree'],
        ['e tupu ma ona fatu;', 'yielding seed'],
        ['e ia te oulua ia', 'to you it shall be'],
        ["e fai ma mea e 'ai.", 'for food'],
    ],
    'Genesis|1|30': [
        ['O manu vaefa uma foi o le vao,', 'And to every beast of the earth'],
        ['ma manu felelei uma,', 'and to every bird'],
        ['atoa ma mea fetolofi uma', 'and to every creeping thing'],
        ['i le eleele,', 'upon the earth'],
        ['o iai le ola,', 'wherein there is life'],
        ['ua ou foai atu i ai', 'I have given'],
        ['o laau afu uma lauolaola', 'every green herb'],
        ["e fai ma mea e 'ai;", 'for food'],
        ['i le ua faapea lava.', 'and it was so'],
    ],
    'Genesis|1|31': [
        ['Ua silasila atu le Atua', 'And God saw'],
        ['i mea uma ua na faia,', 'everything that He had made'],
        ['faauta foi,', 'and behold'],
        ['ua matuā lelei lava.', 'it was very good'],
        ['O le afiafi ma le taeao', 'And the evening and the morning'],
        ['o le aso ono lea.', 'were the sixth day'],
    ],
    'Genesis|3|5': [
        ['auā ua silafia', 'For knows'],
        ['e le Atua,', 'God'],
        ['o le aso lua te aai ai,', 'in the day you eat of it'],
        ['e pupula ai', 'will be opened'],
        ['o oulua mata;', 'your eyes'],
        ['ona avea ai lea o oulua', 'and you will be'],
        ['e pei ni atua o loo iloa', 'like God knowing'],
        ['le lelei', 'good'],
        ['ma le leaga.', 'and evil'],
    ],
    'Genesis|3|8': [
        ['Ua faalogo', 'Then heard'],
        ['i laua', 'they'],
        ['i le siufofoga', 'the voice'],
        ['o Ieova le Atua', 'of the LORD God'],
        ['o loo savali', 'walking'],
        ['i le faatoaga', 'in the garden'],
        ['i le itu aso', 'in the cool part/time of the day'],
        ['e agi malie mai ai le matagi;', 'when the wind blows softly'],
        ['ona lalafi ai lea', 'then hid themselves'],
        ['o Atamu ma lana avā', 'Adam and his wife'],
        ['ai luma o Ieova le Atua', 'from the presence of the LORD God'],
        ['i laau', 'among the trees'],
        ['o le faatoaga.', 'of the garden'],
    ],
    'Genesis|3|9': [
        ['Ona valaau atu lea', 'then called'],
        ['o Ieova le Atua', 'the LORD God'],
        ['ia Atamu,', 'unto Adam'],
        ['ua faapea atu', 'and said'],
        ['ia te ia,', 'unto him'],
        ['O fea o iai oe?', 'Where are you?'],
        ['Ona tali mai lea o ia,', 'So he answered'],
    ],
    'Genesis|3|17': [
        ['Ua ia fetalai atu foi', 'And He also said'],
        ['ia Atamu,', 'to Adam'],
        ['Ua e usiusitai', 'Because you have heeded'],
        ['i le upu', 'the voice'],
        ['a lau avā,', 'of your wife'],
        ["ma ua e 'ai", 'and have eaten'],
        ['i le laau', 'from the tree'],
        ['na ou fai atu ai', 'of which I commanded you'],
        ['ia te oe,', 'unto you'],
        ['na faapea atu,', 'saying'],
        ["e aua e te 'ai ai;", 'You shall not eat of it'],
        ['o le mea lea', 'therefore'],
        ['ua malaia ai', 'is cursed'],
        ['le laueleele', 'the ground'],
        ['ona o oe;', 'because of you'],
        ["e te 'ai ai", 'you shall eat of it'],
        ['ma le tiga', 'with sorrow'],
        ['i aso uma', 'all the days'],
        ['o lou ola;', 'of your life'],
    ],
    'Genesis|3|18': [
        ['e tutupu mai ai', 'shall grow'],
        ['o laau tuitui', 'thorns'],
        ['ma laau talatala', 'and thistles'],
        ['ia te oe;', 'unto you'],
        ["e te 'ai foi", 'you shall also eat'],
        ['laau afu', 'herbs'],
        ['o le fanua;', 'of the field'],
    ],
    'Genesis|3|19': [
        ["e te 'ai", 'you shall eat'],
        ['foi au', 'also your'],
        ["mea e 'ai", 'food/things to eat'],
        ['ma', 'with/in'],
        ['le afu', 'the sweat'],
        ['o ou mata,', 'of your face'],
        ['seia', 'until'],
        ['e toe foi atu', 'you return'],
        ['i le eleele;', 'to the ground'],
        ['auā', 'for'],
        ["na faiina a'i lava oe;", 'out of it indeed you were taken'],
        ['auā', 'for'],
        ['o le efuefu oe,', 'dust you are'],
        ['e te toe foi atu', 'you shall return'],
        ['lava', 'indeed'],
        ['i le efuefu.', 'to dust'],
    ],
    'Genesis|3|20': [
        ['Ua faaigoaina', 'called'],
        ['e Atamu', 'Adam'],
        ['le igoa', 'the name'],
        ['o lana avā o Eva;', 'his wife Eve'],
        ['auā o le tinā o ia', 'because she was the mother'],
        ['o tagata ola uma.', 'of all living'],
    ],
    'Genesis|3|21': [
        ["Ua faia foi", 'made also'],
        ["ofu pa'u", 'garments of skin'],
        ['e Ieova le Atua', 'the LORD God'],
        ['mo Atamu', 'for Adam'],
        ['ma lana avā,', 'and his wife'],
        ['ua faaofu ai', 'and clothed'],
        ['ia te i laua.', 'them'],
    ],
    'Genesis|3|22': [
        ['Ua fetalai ane foi', 'then said'],
        ['Ieova le Atua,', 'the LORD God'],
        ['Faauta,', 'behold'],
        ['ua avea le tagata', 'the man has become'],
        ['e pei o so tatou,', 'like one of us'],
        ['ua iloa ai', 'knowing'],
        ['le lelei ma le leaga;', 'good and evil'],
        ['o lenei,', 'now'],
        ["ne'i aapa atu lona lima,", 'lest he put forth his hand'],
        ['ma tago atu foi', 'and take also'],
        ['i le laau o le ola,', 'of the tree of life'],
        ["e 'ai ai,", 'and eat'],
        ['ma ola e faavavau;', 'and live forever'],
    ],
    'Genesis|3|23': [
        ['ona tulia ai lea', 'then sent out'],
        ['o ia', 'him'],
        ['e Ieova le Atua', 'the LORD God'],
        ['ai le faatoaga o Etena,', 'from the garden of Eden'],
        ['ia galue', 'to till'],
        ['i le eleele', 'the ground'],
        ['na faia mai ai o ia.', 'from which he was taken'],
    ],
    'Genesis|3|24': [
        ['Ua ia tuli atu lava', 'then drove out'],
        ['ia Atamu;', 'Adam'],
        ['ua ia tofia foi', 'and placed'],
        ['kerupi', 'cherubim'],
        ['e nonofo', 'to dwell'],
        ['i le itu i sasae', 'at the east'],
        ['o le faatoaga o Etena,', 'of the garden of Eden'],
        ['ma le pelu afi mumū,', 'and flaming sword'],
        ['o loo feliuliuai', 'turning every way'],
        ['e leoleo ai', 'to guard'],
        ['le ala', 'the way'],
        ['i le laau o le ola.', 'to the tree of life'],
    ],
    'Genesis|3|11': [
        ['Ua fetalai atu o ia,', 'And He said'],
        ['O ai ea', 'Who'],
        ["ua na ta'u atu ia te oe", 'told you'],
        ['ua e le lavalavā?', 'that you were naked?'],
        ["Ua e 'ai ea", 'Have you eaten'],
        ['i le laau', 'from the tree'],
        ['na ou fai atu ai', 'of which I commanded you'],
        ['ia te oe,', 'unto you'],
        ["e aua e te 'ai ai?", 'that you should not eat of it'],
    ],
    'Genesis|4|1': [
        ['Ua iloa', 'knew'],
        ['e Atamu', 'Adam'],
        ['lana avā o Eva;', 'his wife Eve'],
        ['ona to ai lea o ia,', 'then she conceived'],
        ['ona fanau mai lea e ia', 'and bore'],
        ['o Kaino,', 'Cain'],
        ['ua ia faapea ane foi,', 'and she said'],
        ['Ua ou maua', 'I have acquired'],
        ['le tagata', 'a man'],
        ['mai ia Ieova.', 'from the LORD'],
    ],
    'Genesis|4|2': [
        ['Ua toe fanau mai foi e ia', 'then she bore again'],
        ['o lona uso o Apelu.', 'his brother Abel'],
        ['O Apelu foi,', 'Abel'],
        ['o le leoleo mamoe o ia;', 'was a keeper of sheep'],
        ['a o Kaino,', 'but Cain'],
        ['o le galue fanua ia.', 'was a tiller of the ground'],
    ],
    'Genesis|4|3': [
        ['Ua oo ina atoa o aso,', 'in process of time'],
        ['ona avatu ai lea e Kaino', 'then Cain brought'],
        ['o le fua o le fanua', 'of the fruit of the ground'],
        ['o le taulaga ia Ieova.', 'an offering to the LORD'],
    ],
    'Genesis|4|4': [
        ['A o Apelu,', 'but Abel'],
        ['ua ia avatu foi', 'he also brought'],
        ["'uluai tama a lona lafu,", 'firstborn of his flock'],
        ['o e pepeti ai lava.', 'and of their fat'],
        ['Ua silasila mai', 'respected'],
        ['Ieova', 'the LORD'],
        ['ia Apelu,', 'Abel'],
        ['atoa ma lana taulaga;', 'and his offering'],
    ],
    'Genesis|4|5': [
        ['a e peitai', 'but'],
        ['o Kaino ma lana taulaga,', 'Cain and his offering'],
        ['ua ia le silasila i ai.', 'He did not respect'],
        ['Ona ita tele ai lea', 'then was very angry'],
        ['o Kaino,', 'Cain'],
        ['ua faaūū lava', 'and fell'],
        ['ona mata.', 'his countenance'],
    ],
    'Genesis|4|6': [
        ['Ona fetalai atu lea', 'then said'],
        ['o Ieova', 'the LORD'],
        ['ia Kaino,', 'to Cain'],
        ['Se a le mea ua e ita ai?', 'why are you angry'],
        ['Se a foi', 'and why'],
        ['ua faaūū ai ou mata?', 'has your countenance fallen'],
    ],
    'Genesis|4|7': [
        ['Pe afai e te amio lelei', 'if you do well'],
        ['e te le maua ea le fiafia?', 'will you not be accepted'],
        ['A e afai e te le amio lelei', 'but if you do not well'],
        ['o loo taoto', 'lies'],
        ['i le faitotoa', 'at the door'],
        ['le agasala.', 'sin'],
        ['E uai atu lona manao', 'its desire'],
        ['ia te oe,', 'is toward you'],
        ['e te pule foi oe', 'but you must rule'],
        ['ia te ia.', 'over it'],
    ],
    'Genesis|4|8': [
        ['Ua fai mai foi', 'then spoke'],
        ['Kaino', 'Cain'],
        ['ia Apelu lona uso,', 'to Abel his brother'],
        ['ua iai foi i laua', 'and they were'],
        ['i le fanua,', 'in the field'],
        ['ona tulai atu lea', 'then rose up'],
        ['o Kaino', 'Cain'],
        ['ia Apelu lona uso,', 'against Abel his brother'],
        ['ma fasioti ia te ia.', 'and killed him'],
    ],
    'Genesis|4|9': [
        ['Ua fetalai atu', 'then said'],
        ['Ieova', 'the LORD'],
        ['ia Kaino,', 'to Cain'],
        ['O fea o iai', 'where is'],
        ['Apelu lou uso?', 'Abel your brother'],
        ['Ona tali mai lea o ia,', 'then he said'],
        ['Ou te lei iloa;', 'I do not know'],
        ["o a'u ea le leoleo", 'am I the keeper'],
        ["o lo'u uso?", 'of my brother'],
    ],
    'Genesis|4|10': [
        ['Ua fetalai atu o ia,', 'And He said'],
        ['Se a le mea', 'what'],
        ['ua e faia?', 'have you done'],
        ['O loo alaga mai', 'cries out'],
        ['ia te au', 'unto me'],
        ['mai le eleele', 'from the ground'],
        ['le leo o le toto', 'the voice of the blood'],
        ['o lou uso.', 'of your brother'],
    ],
    'Genesis|4|11': [
        ['O lenei,', 'now'],
        ['ua malaia oe', 'cursed are you'],
        ['mai le eleele,', 'from the earth'],
        ['ua faamaga mai', 'which has opened'],
        ['lona gutu', 'its mouth'],
        ["e tali a'i", 'to receive'],
        ['le toto o lou uso', "your brother's blood"],
        ['mai lou lima.', 'from your hand'],
    ],
    'Genesis|4|12': [
        ['A ē galue', 'when you till'],
        ['i le eleele,', 'the ground'],
        ['e le toe fua lelei mai', 'it shall no longer yield'],
        ['ona fua ia te oe;', 'its strength to you'],
        ['e avea oe', 'you shall be'],
        ['ma maumausolo', 'a fugitive'],
        ['ma faasevasevaloaina', 'and a vagabond'],
        ['i le lalolagi.', 'on the earth'],
    ],
    'Genesis|4|13': [
        ['Ona tali mai lea', 'then said'],
        ['o Kaino', 'Cain'],
        ['ia Ieova,', 'to the LORD'],
        ["Ua sili la'u agasala,", 'my punishment is greater'],
        ['ou te le lavatia.', 'than I can bear'],
    ],
    'Genesis|4|14': [
        ['Faauta,', 'behold'],
        ["ua e tulia a'u", 'you have driven me out'],
        ['i le aso nei', 'this day'],
        ['ai le fogāeleele;', 'from the face of the ground'],
        ["o le a lilo a'u", 'I shall be hidden'],
        ['ai ou fofoga;', 'from your face'],
        ["o le a avea a'u", 'I shall be'],
        ['ma maumausolo', 'a fugitive'],
        ['ma faasevasevaloaina', 'and a vagabond'],
        ['i le lalolagi;', 'on the earth'],
        ["ai se maua a'u", 'anyone who finds me'],
        ["e fasiotia a'u e ia.", 'will kill me'],
    ],
    'Genesis|4|15': [
        ['Ua fetalai atu', 'then said'],
        ['Ieova', 'the LORD'],
        ['ia te ia,', 'to him'],
        ['O lenei,', 'therefore'],
        ['ai se fasioti ia Kaino', 'whoever kills Cain'],
        ['e tauia faafitu o ia.', 'vengeance shall be sevenfold'],
        ['Ona tuuina lea', 'and set'],
        ['e Ieova', 'the LORD'],
        ['le faailoga ia Kaino,', 'a mark on Cain'],
        ['e le fasiotia o ia', 'lest anyone kill him'],
        ['e se maua o ia.', 'who finds him'],
    ],
    'Genesis|4|16': [
        ['Ona alu atu lea', 'then went out'],
        ['o Kaino', 'Cain'],
        ['ai luma o Ieova,', 'from the presence of the LORD'],
        ['ua mau foi o ia', 'and dwelt'],
        ['i le nuu o Nota,', 'in the land of Nod'],
        ['i le itu i sasae o Etena.', 'east of Eden'],
    ],
    'Genesis|4|17': [
        ['Na iloa', 'knew'],
        ['e Kaino', 'Cain'],
        ['lana avā;', 'his wife'],
        ['ona to ai lea o ia,', 'then she conceived'],
        ['ona fanau mai lea e ia', 'and bore'],
        ['o Enoka.', 'Enoch'],
        ['Ua faia e ia', 'and he built'],
        ['le aai,', 'a city'],
        ['ua faaigoa atu foi e ia', 'and called'],
        ['o le igoa o le aai', 'the name of the city'],
        ['i le igoa o lona atalii,', 'after the name of his son'],
        ['o Enoka.', 'Enoch'],
    ],
    'Genesis|4|18': [
        ['Ua fanaua e Enoka', 'Enoch begot'],
        ['o Irata;', 'Irad'],
        ['ua fanaua e Irata', 'and Irad begot'],
        ['o Mekuala;', 'Mehujael'],
        ['ua fanaua e Mekuala', 'and Mehujael begot'],
        ['o Metusaeli;', 'Methushael'],
        ['ua fanaua foi e Metusaeli', 'and Methushael begot'],
        ['o Lameko.', 'Lamech'],
    ],
    'Genesis|4|19': [
        ['O Lameko foi', 'Lamech'],
        ['ua fai ana avā e toalua;', 'took two wives'],
        ['o le igoa o le tasi', 'the name of one'],
        ['o Ata,', 'Adah'],
        ['o le igoa foi o le isi', 'the name of the other'],
        ['o Sela.', 'Zillah'],
    ],
    'Genesis|4|20': [
        ['Ua fanau foi e Ata', 'Adah bore'],
        ['o Iapalu;', 'Jabal'],
        ['o le tupuga ia', 'he was the father'],
        ['o e mau i faleie,', 'of those who dwell in tents'],
        ['ma ua fai lafu manu.', 'and have livestock'],
    ],
    'Genesis|4|21': [
        ['O le igoa o lona uso', 'the name of his brother'],
        ['o Iupalu lea;', 'was Jubal'],
        ['o le tupuga ia', 'he was the father'],
        ['o i latou uma', 'of all those'],
        ['o e fai kitara', 'who play the harp'],
        ['ma faaili.', 'and flute'],
    ],
    'Genesis|4|22': [
        ['O Sela foi', 'Zillah also'],
        ['na fanau e ia', 'bore'],
        ['o Tupalu-kaino,', 'Tubal-Cain'],
        ['o le tufuga ia', 'an instructor'],
        ['e fai mea uma lava', 'of every craftsman'],
        ['ua faia', ''],
        ["i 'apa memea", 'in bronze'],
        ['ma uamea;', 'and iron'],
        ['o le tuafafine foi o Tupalu-kaino', 'the sister of Tubal-Cain'],
        ['o Naama lea.', 'was Naamah'],
    ],
    'Genesis|4|23': [
        ['Na fai atu', 'then said'],
        ['Lameko', 'Lamech'],
        ['i ana avā,', 'to his wives'],
        ['Ata ma Sela e,', 'Adah and Zillah'],
        ['faalogologo mai ia', 'hear'],
        ["i lo'u leo;", 'my voice'],
        ['avā e a Lameko,', 'wives of Lamech'],
        ['uai mai ia o oulua taliga', 'listen'],
        ["i la'u upu;", 'to my speech'],
        ['auā na ou fasiotia', 'for I have killed'],
        ['le tagata', 'a man'],
        ["ona o lo'u manua,", 'for wounding me'],
        ['o le taulealea foi', 'and a young man'],
        ["ona o lo'u fasiga;", 'for hurting me'],
    ],
    'Genesis|4|24': [
        ['afai e faafitu', 'if sevenfold'],
        ['ona tauia', 'is avenged'],
        ['o se fasiga o Kaino,', 'for Cain'],
        ['e faafitugafulu ma le fitu', 'then seventy-sevenfold'],
        ['o se taui', 'the vengeance'],
        ['o se fasiga o Lameko.', 'for Lamech'],
    ],
    'Genesis|4|25': [
        ['Ua toe iloa', 'knew again'],
        ['e Atamu', 'Adam'],
        ['lana avā;', 'his wife'],
        ['ua fanau foi e ia', 'and she bore'],
        ['lana tama tane,', 'a son'],
        ['ma ua faaigoa ia te ia', 'and named him'],
        ['o Setu;', 'Seth'],
        ['auā na faapea ia ,', 'for she said'],
        ['Ua tofia mai', 'God has appointed'],
        ['e le Atua', ''],
        ['ia te au', 'me'],
        ['le tasi tama', 'another seed'],
        ['o le sui o Apelu,', 'instead of Abel'],
        ['o le na fasiotia', 'whom was killed'],
        ['e Kaino.', 'by Cain'],
    ],
    'Genesis|4|26': [
        ['Ua fanaua foi', 'born to'],
        ['e Setu', 'Seth'],
        ['lona atalii,', 'a son'],
        ['ua faaigoa foi ia te ia,', 'and he named him'],
        ['o Enosa.', 'Enosh'],
        ['O ona po ia', 'in those days'],
        ['na amata ai', 'began'],
        ['ona valaau tagata', 'men to call'],
        ['i le suafa o Ieova.', 'on the name of the LORD'],
    ],
    'Genesis|5|1': [
        ['O le tusi lenei', 'this is the account'],
        ['i le gafa o Atamu.', 'of the generations of Adam'],
        ['O le aso', 'in the day'],
        ['na faia ai', 'God created'],
        ['e le Atua', ''],
        ['le tagata', 'man'],
        ['na ia faia o ia', 'he made him'],
        ['ua faatusa i le Atua.', 'in the likeness of God'],
    ],
    'Genesis|5|2': [
        ['Na ia faia i laua,', 'he created them'],
        ['o le tane ma le fafine,', 'male and female'],
        ['na ia faamanuia foi', 'and he blessed'],
        ['ia te i laua,', 'them'],
        ['ma na faaigoaina ai', 'and he called'],
        ['o la igoa o Atamu,', 'their name man'],
        ['i le aso na faia ai i laua.', 'in the day they were created'],
    ],
    'Genesis|5|3': [
        ['Na ola Atamu', 'Adam lived'],
        ['i tausaga e tasi le selau', 'one hundred and'],
        ['ma le tolugafulu,', 'thirty years'],
        ['ona fanaua lea e ia', 'then he begot'],
        ['o lona atalii', 'a son'],
        ['e foliga ia te ia', 'in his likeness'],
        ['ma faatusa i ai;', 'after his image'],
        ['ma ua faaigoaina e ia', 'and named him'],
        ['lona igoa o Setu.', 'Seth'],
    ],
    'Genesis|5|4': [
        ['O aso lava o Atamu', 'the days of Adam'],
        ['talu ina fanauina e ia o Setu', 'after he begot Seth'],
        ['e valu selau', 'eight hundred'],
        ['o ona tausaga,', 'years'],
        ['ma ua fanaua ai e ia', 'and he begat'],
        ['o atalii ma afafine.', 'sons and daughters'],
    ],
    'Genesis|5|5': [
        ['O aso uma foi', 'all the days also'],
        ['na ola ai Atamu,', 'that Adam lived'],
        ['e iva selau', 'nine hundred'],
        ['ma le tolu gafulu,', 'and thirty'],
        ['o ona tausaga ia;', 'and his years'],
        ['ona oti ai lea.', 'and he died'],
    ],
    'Genesis|5|6': [
        ['Na ola Setu', 'Seth lived'],
        ['i tausaga e tasi le selau', 'one hundred and'],
        ['ma le lima,', 'five years'],
        ['ona fanaua lea e ia', 'then he begot'],
        ['o Enosa.', 'Enosh'],
    ],
    'Genesis|5|7': [
        ['O le olaga foi o Setu', 'the life also of Seth'],
        ['talu ina fanauina e ia o Enosa,', 'after he begot Enosh'],
        ['o tausaga e valu selau', 'years eight hundred'],
        ['ma le fitu ia,', 'and seven'],
        ['ma ua fanaua ai e ia', 'and he begat'],
        ['o atalii ma afafine.', 'sons and daughters'],
    ],
    'Genesis|5|8': [
        ['O aso uma foi o Setu', 'all the days also of Seth'],
        ['e iva selau', 'nine hundred'],
        ['ma le sefulu', 'and ten'],
        ['ma le lua,', 'and two'],
        ['o ona tausaga ia;', 'and his years'],
        ['ona oti ai lea.', 'and he died'],
    ],
    'Genesis|5|9': [
        ['Na ola Enosa', 'Enosh lived'],
        ['i tausaga e ivagafulu,', 'ninety years'],
        ['ona fanaua lea e ia', 'then he begot'],
        ['o Kainano.', 'Cainan'],
    ],
    'Genesis|5|10': [
        ['O le olaga foi o Enosa', 'the life also of Enosh'],
        ['talu ina fanauina e ia o Kainano,', 'after he begot Cainan'],
        ['o tausaga ia e valu selau', 'years eight hundred'],
        ['ma le sefulu', 'and ten'],
        ['ma tausaga e lima,', 'and five years'],
        ['ma ua fanaua ai e ia', 'and he begat'],
        ['o atalii ma afafine.', 'sons and daughters'],
    ],
    'Genesis|5|11': [
        ['O aso uma foi o Enosa', 'all the days also of Enosh'],
        ['e iva selau', 'nine hundred'],
        ['ma le lima,', 'and five'],
        ['o ona tausaga ia;', 'and his years'],
        ['ona oti ai lea.', 'and he died'],
    ],
    'Genesis|5|12': [
        ['Na ola Kainano', 'Cainan lived'],
        ['i tausaga e fitugafulu,', 'seventy years'],
        ['ona fanaua lea e ia', 'then he begot'],
        ['o Maalaelu.', 'Mahalalel'],
    ],
    'Genesis|5|13': [
        ['O le olaga foi o Kainano', 'the life also of Cainan'],
        ['talu ina fanauina e ia o Maalaelu,', 'after he begot Mahalalel'],
        ['o tausaga ia e valu selau', 'years eight hundred'],
        ['ma le fagafulu,', 'and forty'],
        ['ma ua fanaua ai e ia', 'and he begat'],
        ['o atalii ma afafine.', 'sons and daughters'],
    ],
    'Genesis|5|14': [
        ['O aso uma foi o Kainano', 'all the days also of Cainan'],
        ['e iva selau', 'nine hundred'],
        ['ma le sefulu,', 'and ten'],
        ['o ona tausaga ia;', 'and his years'],
        ['ona oti ai lea.', 'and he died'],
    ],
    'Genesis|5|15': [
        ['Na ola Maalaelu', 'Mahalalel lived'],
        ['i tausaga e onogafulu', 'sixty-five'],
        ['ma le lima,', 'years'],
        ['ona fanaua ai lea e ia', 'then he begot'],
        ['o Iareto.', 'Jared'],
    ],
    'Genesis|5|16': [
        ['O le olaga foi o Maalaelu', 'the life also of Mahalalel'],
        ['talu ina fanauina e ia o Iareto,', 'after he begot Jared'],
        ['o tausaga ia e valu selau', 'years eight hundred'],
        ['ma le tolugafulu,', 'and thirty'],
        ['ma ua fanaua ai e ia', 'and he begat'],
        ['o atalii ma afafine.', 'sons and daughters'],
    ],
    'Genesis|5|17': [
        ['O aso uma foi o Maalaelu', 'all the days also of Mahalalel'],
        ['e valu selau', 'eight hundred'],
        ['ma le ivagafulu', 'and ninety'],
        ['ma le lima,', 'and five'],
        ['o ona tausaga ia;', 'and his years'],
        ['ona oti ai lea.', 'and he died'],
    ],
    'Genesis|5|18': [
        ['Na ola Iareto', 'Jared lived'],
        ['i tausaga e tasi le selau', 'one hundred and'],
        ['ma le onogafulu', 'sixty-two'],
        ['ma tausaga e lua,', 'years'],
        ['ona fanaua ai lea e ia', 'then he begot'],
        ['o Enoka.', 'Enoch'],
    ],
    'Genesis|5|19': [
        ['O le olaga foi o Iareto', 'the life also of Jared'],
        ['talu ina fanauina e ia o Enoka,', 'after he begot Enoch'],
        ['o tausaga e valu selau ia,', 'years eight hundred'],
        ['ma ua fanaua ai e ia', 'and he begat'],
        ['o atalii ma afafine.', 'sons and daughters'],
    ],
    'Genesis|5|20': [
        ['O aso uma foi o lareto', 'all the days also of Jared'],
        ['e iva selau', 'nine hundred'],
        ['ma le onogafulu', 'and sixty'],
        ['ma le lua,', 'and two'],
        ['o ona tausaga ia;', 'and his years'],
        ['ona oti ai lea.', 'and he died'],
    ],
    'Genesis|5|21': [
        ['Na ola Enoka', 'Enoch lived'],
        ['i tausaga e onogafulu', 'sixty-five'],
        ['ma le lima,', 'years'],
        ['ona fanaua ai lea e ia', 'then he begot'],
        ['o Metusela.', 'Methuselah'],
    ],
    'Genesis|5|22': [
        ['Na la feooai foi o Enoka', 'walked Enoch'],
        ['ma le Atua', 'with God'],
        ['talu ina fanauina e ia o Metusela,', 'after he begot Methuselah'],
        ['i tausaga e tolu selau,', 'three hundred years'],
        ['ma ua fanaua ai e ia', 'and he begat'],
        ['o atalii ma afafine.', 'sons and daughters'],
    ],
    'Genesis|5|23': [
        ['O aso uma foi o Enoka', 'all the days also of Enoch'],
        ['e tolu selau', 'three hundred'],
        ['ma le onogafulu', 'and sixty'],
        ['ma le lima,', 'and five'],
        ['o ona tausaga ia.', 'and his years'],
    ],
    'Genesis|5|24': [
        ['Na la feooai foi o Enoka', 'walked Enoch'],
        ['ma le Atua;', 'with God'],
        ['ua le iloa foi e ia,', 'then he was not'],
        ['auā na avea o ia', 'for took him'],
        ['e le Atua.', 'God'],
    ],
    'Genesis|5|25': [
        ['Na ola Metusela', 'Methuselah lived'],
        ['i tausaga e selau', 'one hundred and'],
        ['ma le valugafulu', 'eighty-seven'],
        ['ma tausaga e fitu,', 'years'],
        ['ona fanaua ai lea e ia', 'then he begot'],
        ['o Lameko.', 'Lamech'],
    ],
    'Genesis|5|26': [
        ['O le olaga foi o Metusela', 'the life also of Methuselah'],
        ['talu ina fanauina e ia o Lameko,', 'after he begot Lamech'],
        ['o tausaga ia e fitu selau', 'years seven hundred'],
        ['ma le valugafulu', 'and eighty'],
        ['ma tausaga e lua,', 'and two years'],
        ['ma ua fanaua ai e ia', 'and he begat'],
        ['o atalii ma afafine.', 'sons and daughters'],
    ],
    'Genesis|5|27': [
        ['O aso uma foi o Metusela', 'all the days also of Methuselah'],
        ['e iva selau', 'nine hundred'],
        ['ma le onogafulu', 'and sixty'],
        ['ma le iva,', 'and nine'],
        ['o ona tausaga ia;', 'and his years'],
        ['ona oti ai lea.', 'and he died'],
    ],
    'Genesis|5|28': [
        ['Na ola Lameko', 'Lamech lived'],
        ['i tausaga e selau', 'one hundred and'],
        ['ma le valugafulu', 'eighty-two'],
        ['ma tausaga e lua,', 'years'],
        ['ona fanaua ai lea e ia', 'then he begot'],
        ['lona atalii,', 'a son'],
    ],
    'Genesis|5|29': [
        ['ma ua faaigoaina e ia', 'and called his name'],
        ['lona igoa o Noa,', 'Noah'],
        ['o loo faapea.', 'saying'],
        ['E faamafanafanaina i tatou', 'this one will comfort us'],
        ['e ia', ''],
        ['i la tatou galuega', 'concerning our work'],
        ['ma le tiga', 'and the toil'],
        ['o tatou lima,', 'of our hands'],
        ['ona o le laueleele', 'because of the ground'],
        ['ua malaia ia Ieova.', 'which the LORD has cursed'],
    ],
    'Genesis|5|30': [
        ['O le olaga foi o Lameko', 'the life also of Lamech'],
        ['talu ina fanauina e ia o Noa,', 'after he begot Noah'],
        ['o tausaga ia e lima selau', 'years five hundred'],
        ['ma le ivagafulu', 'and ninety'],
        ['ma tausaga e lima,', 'and five years'],
        ['ma ua fanaua ai e ia', 'and he begat'],
        ['o atalii ma afafine.', 'sons and daughters'],
    ],
    'Genesis|5|31': [
        ['O aso uma foi o Lameko', 'all the days also of Lamech'],
        ['e fitu selau', 'seven hundred'],
        ['ma le fitugafulu', 'and seventy'],
        ['ma le fitu,', 'and seven'],
        ['o ona tausaga ia;', 'and his years'],
        ['ona oti ai lea.', 'and he died'],
    ],
    'Genesis|5|32': [
        ['Ua lima selau tausaga o Noa,', 'Noah was five hundred years old'],
        ['ona fanaua ai lea e Noa', 'then he begot'],
        ['o Semu,', 'Shem'],
        ['ma Hamo,', 'Ham'],
        ['ma Iafeta.', 'and Japheth'],
    ],
    'Genesis|6|1': [
        ['Ua oo ina amata', 'when began'],
        ['ona faatoateleina', 'to multiply'],
        ['o tagata', 'men'],
        ['i le fogāeleele,', 'on the earth'],
        ['ma ua fanauina', 'and were born'],
        ['e i latou', 'to them'],
        ['o afafine,', 'daughters'],
    ],
    'Genesis|6|2': [
        ['ona vaavaai lea', 'then saw'],
        ['o atalii o le Atua', 'the sons of God'],
        ['i afafine o tagata,', 'the daughters of men'],
        ['ua lalelei lava i latou;', 'that they were beautiful'],
        ['ona fai avā ai lea o i latou', 'then they took wives'],
        ['i fafine uma', 'of all'],
        ['ua latou loto i ai.', 'whom they chose'],
    ],
    'Genesis|6|3': [
        ['Ona fetalai ane lea', 'then said'],
        ['o Ieova,', 'the LORD'],
        ['E le faavavau', 'shall not'],
        ['ona finau', 'strive'],
        ["o lo'u Agaga", 'my Spirit'],
        ['ma tagata,', 'with man'],
        ['auā ua na o tagata i latou;', 'for he is flesh'],
        ['a o latou aso', 'his days'],
        ['e selau ma le luafulu', 'shall be one hundred and twenty'],
        ['o tausaga ia.', 'years'],
    ],
    'Genesis|6|4': [
        ['Sa i le lalolagi', 'there were on the earth'],
        ['i ia ona aso', 'in those days'],
        ['o tagata maualuluga;', 'the giants'],
        ['e faapea foi i ona tua mai,', 'and also afterward'],
        ['ina ua o ane', 'when'],
        ['o atalii o le Atua', 'the sons of God'],
        ['i afafine o tagata,', 'to the daughters of men'],
        ['ma ua fananau ai', 'and they bore'],
        ['ia te i latou,', 'children to them'],
        ['o tagata malolosi ia', 'they were the mighty men'],
        ["ma le ta'ua anamua.", 'men of renown of old'],
    ],
    'Genesis|6|5': [
        ['Ua silafia e Ieova', 'the LORD saw'],
        ['ua leaga tele lava', 'that was great'],
        ['tagata i le lalolagi,', 'the wickedness of man on the earth'],
        ['o manatu uma', 'every intent'],
        ['ua mafaufau ifo ai', 'of the thoughts'],
        ['i o latou loto', 'of their heart'],
        ['ua na ona leaga ia', 'was only evil'],
        ['i aso uma lava.', 'continually'],
    ],
    'Genesis|6|6': [
        ['Ua salamo foi Ieova', 'and the LORD was sorry'],
        ['ina ua faia e ia', 'that He had made'],
        ['tagata i le lalolagi,', 'man on the earth'],
        ['ma ua tiga ai', 'and He was grieved'],
        ['lona finagalo.', 'in His heart'],
    ],
    'Genesis|6|7': [
        ['Ona fetalai ane lea', 'then said'],
        ['o Ieova,', 'the LORD'],
        ['Ou te soloieseina', 'I will destroy'],
        ['i le fogāeleele', 'from the face of the earth'],
        ['tagata na ou faia;', 'man whom I have created'],
        ['o tagata,', 'man'],
        ['ma manu vaefa,', 'and beasts'],
        ['ma mea fetolofi,', 'and creeping things'],
        ['atoa ma manu felelei;', 'and birds of the heaven'],
        ['auā ua ou salamo', 'for I am sorry'],
        ['ina ua ou faia i latou.', 'that I have made them'],
    ],
    'Genesis|6|8': [
        ['A o Noa,', 'but Noah'],
        ['ua alofagia o ia', 'found grace'],
        ['e Ieova.', 'in the eyes of the LORD'],
    ],
    'Genesis|6|9': [
        ['O le tala lenei', 'these are the generations'],
        ['ia Noa;', 'of Noah'],
        ['o Noa', 'Noah'],
        ['o le tagata amiotonu ia', 'was a just man'],
        ['ma le sao', 'perfect'],
        ['i e tupulaga ma ia;', 'in his generations'],
        ['sa la feooai', 'walked'],
        ['o le Atua ma Noa.', 'God with Noah'],
    ],
    'Genesis|6|10': [
        ['Ua fanaua foi e Noa', 'Noah begot'],
        ['ona atalii e toatolu,', 'three sons'],
        ['o Semu,', 'Shem'],
        ['ma Hamo,', 'Ham'],
        ['ma Iafeta.', 'and Japheth'],
    ],
    'Genesis|6|11': [
        ['Ua leaga lava', 'was corrupt'],
        ['le lalolagi', 'the earth'],
        ['i luma o le Atua,', 'before God'],
        ['ma ua tumu', 'and was filled'],
        ['le lalolagi', 'the earth'],
        ['i le saua.', 'with violence'],
    ],
    'Genesis|6|12': [
        ['Ua silasila mai', 'looked upon'],
        ['le Atua', 'God'],
        ['i le lalolagi,', 'the earth'],
        ['faauta foi,', 'behold'],
        ['ua leaga lava;', 'it was corrupt'],
        ['auā o tagata uma', 'for all flesh'],
        ['ua leaga ia i latou', 'had corrupted'],
        ['a latou amio', 'their way'],
        ['i le lalolagi.', 'on the earth'],
    ],
    'Genesis|6|13': [
        ['Ua fetalai atu', 'then said'],
        ['le Atua', 'God'],
        ['ia Noa,', 'to Noah'],
        ["Ua oo mai i o'u luma", 'I have determined'],
        ['le iuga o tagata uma;', 'the end of all flesh'],
        ['auā ua tumu le lalolagi', 'for the earth is filled'],
        ['i le saua', 'with violence'],
        ['ona o i latou;', 'through them'],
        ['faauta foi,', 'behold'],
        ["o a'u lava,", 'I'],
        ['ou te faaumatia i latou', 'will destroy them'],
        ['atoa ma le lalolagi.', 'with the earth'],
    ],
    'Genesis|6|14': [
        ['Ia e faia', 'make for yourself'],
        ['se vaa mo oe', 'an ark'],
        ['i le laau o le kofa;', 'of gopher wood'],
        ['e te faia ni ana', 'make rooms'],
        ['i le vaa,', 'in the ark'],
        ['e te puluti ai foi', 'and cover it'],
        ['i le liu ma tua', 'inside and outside'],
        ['i pulu.', 'with pitch'],
    ],
    'Genesis|6|15': [
        ['Ia faapea foi', 'the dimensions'],
        ['ona e faia;', 'of the ark'],
        ['e tolu selau o kupita', 'three hundred cubits'],
        ['o le umi lea o le vaa,', 'the length'],
        ['e limagafulu o kupita', 'fifty cubits'],
        ['lona lautele,', 'the width'],
        ['e tolugafulu o kupita foi', 'thirty cubits'],
        ['lona maualuga.', 'the height'],
    ],
    'Genesis|6|16': [
        ['E te faia se faamalama', 'make a window'],
        ['i le vaa,', 'for the ark'],
        ['o le kupita foi', 'and finish it'],
        ['e te faaumaina i luga;', 'to a cubit from above'],
        ['e te faia foi', 'make'],
        ['se faitotoa o le vaa', 'the door of the ark'],
        ['i lona itu;', 'in its side'],
        ['e te faia', 'make'],
        ['ni ona fogavaa ,', 'decks'],
        ['o le aupito i lalo,', 'lower'],
        ['ma lona lua,', 'middle'],
        ['ma lona tolu.', 'and upper'],
    ],
    'Genesis|6|17': [
        ['Faauta,', 'behold'],
        ["o a'u foi,", 'I'],
        ['ou te faaooina atu', 'am bringing'],
        ['le lolo', 'the flood'],
        ['i luga o le laueleele,', 'upon the earth'],
        ['e faaumatia ai', 'to destroy'],
        ['mea ola uma', 'all flesh'],
        ['ua i ai le mānava o le ola', 'in which is the breath of life'],
        ['o i lalo o le lagi;', 'from under heaven'],
        ['e faauma ai le ola', 'everything'],
        ['o mea uma i le lalolagi.', 'on the earth shall die'],
    ],
    'Genesis|6|18': [
        ['A e ou te faatumauina', 'but I will establish'],
        ["la'u feagaiga ma oe;", 'my covenant with you'],
        ['e te ulu atu foi', 'you shall enter'],
        ['i le vaa,', 'the ark'],
        ['o oe,', 'you'],
        ['ma ou atalii,', 'and your sons'],
        ['ma lau avā,', 'and your wife'],
        ['atoa ma avā a ou atalii', "and your sons' wives"],
        ['faatasi ma oe.', 'with you'],
    ],
    'Genesis|6|19': [
        ['E te ave i le vaa', 'bring into the ark'],
        ['mea ola ia tailua', 'two of every kind'],
        ['i mea uma,', 'of all flesh'],
        ['ia faaolaina', 'to keep them alive'],
        ['faatasi ma oe;', 'with you'],
        ['ia i ai le manu poa', 'male'],
        ['ma le manu fafine;', 'and female'],
    ],
    'Genesis|6|20': [
        ['o manu felelei', 'of birds'],
        ['e taitasi ma lona uiga,', 'after their kind'],
        ['ma manu vaefa', 'and of animals'],
        ['e taitasi ma lona uiga,', 'after their kind'],
        ['o mea fetolofi uma', 'of every creeping thing'],
        ['o i le eleele', 'of the earth'],
        ['e taitasi ma lona uiga,', 'after its kind'],
        ['ia tailua', 'two of every kind'],
        ['ona o atu ia te oe', 'they shall come to you'],
        ['i mea uma,', ''],
        ['ia faaolaina.', 'to keep them alive'],
    ],
    'Genesis|6|21': [
        ['O oe foi', 'and you'],
        ["e te ave ma oe ni mea e 'ai", 'take with you of all food'],
        ["i mea uma e 'aina,", 'that is eaten'],
        ['e te faaputuina ia te oe;', 'gather it to yourself'],
        ["e fai foi ma mea e 'ai", 'for food'],
        ['mā oe', 'for you'],
        ['atoa ma i latou.', 'and for them'],
    ],
    'Genesis|6|22': [
        ['Na faia foi', 'thus did'],
        ['e Noa', 'Noah'],
        ['e faapei ona poloai atu ai', 'according to all that'],
        ['le Atua ia te ia', 'God commanded him'],
        ['i mea uma,', ''],
        ['sa faapea lava', 'so'],
        ['ona fai e ia.', 'he did'],
    ],
    # Genesis 7 - The Flood
    'Genesis|7|1': [
        ['Ua fetalai atu', 'said'],
        ['Ieova', 'the LORD'],
        ['ia Noa.', 'to Noah'],
        ['Ina ulu atu ia o oe', 'come you'],
        ['atoa ma lou aiga uma', 'with all your household'],
        ['i le vaa;', 'into the ark'],
        ['auā ua ou iloa oe', 'for I have seen you'],
        ['o le amiotonu', 'righteous'],
        ["i o'u luma", 'before me'],
        ['i lenei tupulaga.', 'in this generation'],
    ],
    'Genesis|7|2': [
        ['Ia e ave', 'take'],
        ['e taifitu', 'by sevens'],
        ['i manu vaefa uma e mamā,', 'of every clean animal'],
        ['o le manu poa', 'the male'],
        ['ma le manu fafine;', 'and the female'],
        ['a o manu vaefa', 'but of animals'],
        ['e le mamā', 'that are not clean'],
        ['e tailua ia,', 'by twos'],
        ['o le manu poa', 'the male'],
        ['ma le manu fafine.', 'and the female'],
    ],
    'Genesis|7|3': [
        ['O manu felelei foi', 'also of birds'],
        ['e taifitu,', 'by sevens'],
        ['o le manu poa', 'the male'],
        ['ma le manu fafine,', 'and the female'],
        ['ia ola mai ai', 'to keep alive'],
        ['a latou fanau', 'their offspring'],
        ['i le fogāeleele uma.', 'on the face of all the earth'],
    ],
    'Genesis|7|4': [
        ['Auā e toe fitu aso', 'for in seven more days'],
        ['ona ou faatotoina ifo ai lea', 'I will cause to rain'],
        ['o le ua', 'rain'],
        ['i le lalolagi', 'on the earth'],
        ['e fagafulu ona ao', 'forty days'],
        ['e fagafulu foi ona po;', 'and forty nights'],
        ['ou te soloiesea foi', 'and I will destroy'],
        ['i le fogāeleele', 'from the face of the earth'],
        ['o mea ola uma', 'every living thing'],
        ['ua ou faia.', 'that I have made'],
    ],
    'Genesis|7|5': [
        ['Na faia foi', 'and did'],
        ['e Noa', 'Noah'],
        ['e tusa ma mea uma', 'according to all'],
        ['na poloai atu ai Ieova', 'the LORD commanded'],
        ['ai te ia.', 'him'],
    ],
    'Genesis|7|6': [
        ['O le ono selau', 'six hundred'],
        ['o tausaga o Noa', 'years old was Noah'],
        ['na oo ai le lolo', 'when came the flood'],
        ['i le lalolagi.', 'on the earth'],
    ],
    'Genesis|7|7': [
        ['Ua ulu atu Noa,', 'Noah went in'],
        ['ma ona atalii,', 'and his sons'],
        ['ma lana avā,', 'and his wife'],
        ['ma avā a ona atalii', "and his sons' wives"],
        ['faatasi ma ia', 'with him'],
        ['i le vaa', 'into the ark'],
        ['ona o le lolo.', 'because of the flood'],
    ],
    'Genesis|7|8': [
        ['O manu vaefa e mamā,', 'of clean animals'],
        ['ma manu vaefa e le mamā', 'and of unclean animals'],
        ['ma manu felelei,', 'and of birds'],
        ['atoa ma mea uma', 'and of everything'],
        ['e fetolofi i le eleele,', 'that creeps on the earth'],
    ],
    'Genesis|7|9': [
        ['ua tailua', 'two by two'],
        ['ona ulu atu i latou', 'they went'],
        ['ia Noa', 'to Noah'],
        ['i le vaa,', 'into the ark'],
        ['o le manu poa', 'male'],
        ['ma le manu fafine,', 'and female'],
        ['e faapei ona poloai atu ai', 'as commanded'],
        ['le Atua', 'God'],
        ['ia Noa.', 'Noah'],
    ],
    'Genesis|7|10': [
        ['Ua oo foi', 'and it came to pass'],
        ['i le aso fitu,', 'after seven days'],
        ['ona oo ai lea', 'that came'],
        ['o le vai o le lolo', 'the waters of the flood'],
        ['i le lalolagi.', 'on the earth'],
    ],
    'Genesis|7|11': [
        ['O le tausaga e ono selau', 'in the six hundredth year'],
        ['o le olaga o Noa,', "of Noah's life"],
        ['o le masina e lua,', 'in the second month'],
        ['o le aso e sefulu ma le fitu', 'on the seventeenth day'],
        ['o le masina,', 'of the month'],
        ['o le aso lava lea', 'on that same day'],
        ['na lepeti ai', 'were broken up'],
        ['o punāvai uma', 'all the fountains'],
        ['o i le moana sausau,', 'of the great deep'],
        ['ma ua faaavanoaina', 'and were opened'],
        ['pupuni o le lagi.', 'the windows of heaven'],
    ],
    'Genesis|7|12': [
        ['Sa i ai le uaga', 'and the rain was'],
        ['i le lalolagi', 'on the earth'],
        ['i ao e fagafulu', 'forty days'],
        ['ma po e fagafulu.', 'and forty nights'],
    ],
    'Genesis|7|13': [
        ['O le aso lava lea', 'on that very day'],
        ['na ulu atu ai Noa,', 'entered Noah'],
        ['ma atalii o Noa,', "and Noah's sons"],
        ['o Semu,', 'Shem'],
        ['ma Hamo,', 'Ham'],
        ['ma Iafeta,', 'and Japheth'],
        ['ma le avā a Noa,', "and Noah's wife"],
        ['ma avā e toatolu', 'and the three wives'],
        ['a ona atalii,', 'of his sons'],
        ['e faatasi ma i latou,', 'with them'],
        ['i le vaa;', 'into the ark'],
    ],
    'Genesis|7|14': [
        ['o i latou nei,', 'they'],
        ['ma manu o le vao uma', 'and every wild beast'],
        ['e taitasi ma lona uiga,', 'after its kind'],
        ['ma manu vaefa fanua uma', 'and all cattle'],
        ['e taitasi ma lona uiga,', 'after its kind'],
        ['ma mea fetolofi uma', 'and every creeping thing'],
        ['e fetolofi i le eleele', 'that creeps on the earth'],
        ['e taitasi ma lona uiga,', 'after its kind'],
        ['ma manufelelei uma', 'and every bird'],
        ['e taitasi ma lona uiga,', 'after its kind'],
        ['o mea felelei uma', 'every winged thing'],
        ['e taitasi ma uiga, eseese,', 'of every sort'],
    ],
    'Genesis|7|15': [
        ['ua latou ulu atu foi', 'they went'],
        ['ia Noa', 'to Noah'],
        ['i le vaa,', 'into the ark'],
        ['e tailua', 'two by two'],
        ['i mea ola uma', 'of all flesh'],
        ['o i ai le mānava ola.', 'in which is the breath of life'],
    ],
    'Genesis|7|16': [
        ['Ua latou ulu atu,', 'they went in'],
        ['o le poa ma le fafine', 'male and female'],
        ['i mea ola uma,', 'of all flesh'],
        ['ua latou ulu atu,', 'they went in'],
        ['e faapei ona poloai atu', 'as commanded'],
        ['le Atua', 'God'],
        ['ia te ia;', 'him'],
        ['ona pupuni ai lea', 'then shut'],
        ['e Ieova', 'the LORD'],
        ['ia te ia.', 'him in'],
    ],
    'Genesis|7|17': [
        ['Sa i ai foi le lolo', 'the flood was'],
        ['i le lalolagi', 'on the earth'],
        ['i ona aso e fagafulu;', 'forty days'],
        ['ua faatuputeleina le vai,', 'the waters increased'],
        ['ma ua opeopea ai le vaa,', 'and lifted up the ark'],
        ['ua neetia foi', 'and it rose up'],
        ['i luga o le eleele.', 'above the earth'],
    ],
    'Genesis|7|18': [
        ['Ua malo lava le vai,', 'the waters prevailed'],
        ['ma ua matuā faateleina', 'and greatly increased'],
        ['i le lalolagi;', 'on the earth'],
        ['ua alu foi le vaa', 'and the ark moved'],
        ['i le fogāvai.', 'on the surface of the waters'],
    ],
    'Genesis|7|19': [
        ['Ua matua malo tele lava le vai', 'the waters prevailed exceedingly'],
        ['i le lalolagi;', 'on the earth'],
        ['ma ua ufitia ai', 'and were covered'],
        ['mauga maualuluga uma', 'all the high mountains'],
        ['o i lalo o le lagi uma.', 'under the whole heaven'],
    ],
    'Genesis|7|20': [
        ['E sefulu ma le lima kupita', 'fifteen cubits'],
        ['na malo ai le vai', 'the waters prevailed'],
        ['i luga,', 'upward'],
        ['ma ua ufitia ai mauga.', 'and the mountains were covered'],
    ],
    'Genesis|7|21': [
        ['Ona faauma ai lea', 'and all flesh died'],
        ['o le ola o mea ola uma', 'all living things'],
        ['na feoai i le lalolagi,', 'that moved on the earth'],
        ['o manu felelei,', 'birds'],
        ['ma manu vaefa fanua,', 'and cattle'],
        ['ma manu feai,', 'and beasts'],
        ['ma mea fetolofi uma', 'and every creeping thing'],
        ['na fetolofi i le eleele,', 'that creeps on the earth'],
    ],
    'Genesis|7|22': [
        ['atoa ma tagata uma;', 'and all mankind'],
        ['na faauma le ola', 'all died'],
        ['o mea uma', 'everything'],
        ['sa i ai le mānava o le ola', 'that had the breath of life'],
        ['i o latou pogaiisu', 'in their nostrils'],
        ['i mea uma', 'all that was'],
        ['sa i le eleele matutu.', 'on the dry land'],
    ],
    'Genesis|7|23': [
        ['Na faaumatia', 'were destroyed'],
        ['o mea ola uma', 'all living things'],
        ['sa i le fogāeleele,', 'on the face of the earth'],
        ['o tagata,', 'man'],
        ['ma manu vaefa,', 'and cattle'],
        ['ma mea fetolofi,', 'and creeping things'],
        ['atoa ma manu felelei;', 'and birds of the air'],
        ['na faaumatia i latou', 'they were destroyed'],
        ['ai le lalolagi;', 'from the earth'],
        ['na o Noa,', 'only Noah remained'],
        ['i le ma i latou', 'and those'],
        ['sa i le vaa ma ia', 'who were with him in the ark'],
        ['ua totoe.', 'survived'],
    ],
    'Genesis|7|24': [
        ['Sa malo le vai', 'the waters prevailed'],
        ['i le lalolagi', 'on the earth'],
        ['i ona aso e selau', 'one hundred'],
        ['ma le limagafulu.', 'and fifty days'],
    ],
    # Genesis 8 - The Flood Recedes
    'Genesis|8|1': [
        ['Ua manatua', 'remembered'],
        ['e le Atua', 'God'],
        ['Noa,', 'Noah'],
        ['ma mea ola uma,', 'and every living thing'],
        ['ma manu vaefa uma', 'and all the animals'],
        ['sa i le vaa ma ia.', 'that were with him in the ark'],
        ['Ua faaagi atu', 'then caused to pass'],
        ['e le Atua', 'God'],
        ['le matagi', 'a wind'],
        ['i le lalolagi;', 'over the earth'],
        ['ona maui ai lea', 'and subsided'],
        ['o le vai;', 'the waters'],
    ],
    'Genesis|8|2': [
        ['ua punitia foi', 'were stopped'],
        ['punāvai o le moana,', 'the fountains of the deep'],
        ['ma pupuni o le lagi;', 'and the windows of heaven'],
        ['ua taofia foi', 'and was restrained'],
        ['uaga mai le lagi.', 'the rain from heaven'],
    ],
    'Genesis|8|3': [
        ['Ua maui atu le vai', 'the waters receded'],
        ['ai le lalolagi,', 'from the earth'],
        ['ua saga mauiui lava;', 'continually'],
        ['ua mavae', 'after'],
        ['aso e selau ma le limagafulu', 'one hundred and fifty days'],
        ['ona faaitiiti lea o le vai.', 'the waters decreased'],
    ],
    'Genesis|8|4': [
        ['O le fitu o masina,', 'in the seventh month'],
        ['ma lona aso e sefulu ma le fitu,', 'on the seventeenth day'],
        ['ua toa ai le vaa', 'the ark rested'],
        ['i luga o mauga o Ararata.', 'on the mountains of Ararat'],
    ],
    'Genesis|8|5': [
        ['Ua saga mauiui pea le vai', 'the waters decreased continually'],
        ['ua oo i le masina e sefulu;', 'until the tenth month'],
        ['o le aso muamua', 'on the first day'],
        ['o lea masina,', 'of the month'],
        ['ua mānu ai', 'were seen'],
        ['tumutumu o mauga.', 'the tops of the mountains'],
    ],
    'Genesis|8|6': [
        ['Ua oo ina atoa', 'at the end of'],
        ['o aso e fagafulu,', 'forty days'],
        ['ona tatala lea', 'opened'],
        ['e Noa', 'Noah'],
        ['le faamalama o le vaa', 'the window of the ark'],
        ['na ia faia;', 'which he had made'],
    ],
    'Genesis|8|7': [
        ['ua ia tuu atu ai', 'he sent out'],
        ['le oreva;', 'a raven'],
        ['ua lele atu ia,', 'which went out'],
        ['ma fefoifoiai', 'going to and fro'],
        ['ua oo ina mate', 'until dried up'],
        ['o le vai', 'the waters'],
        ['ai le laueleele.', 'from the earth'],
    ],
    'Genesis|8|8': [
        ['Ua ia tuuina atu foi', 'he also sent out'],
        ['le lupe', 'a dove'],
        ['nai ia te ia,', 'from him'],
        ['ia iloa ai', 'to see if'],
        ['po ua papau le vai', 'the waters had abated'],
        ['i le fogāeleele.', 'from the face of the earth'],
    ],
    'Genesis|8|9': [
        ['A ua le maua', 'but found no'],
        ['e le lupe', 'the dove'],
        ['se mea e mapu ai ona vae,', 'resting place for the sole of her foot'],
        ['ona toe foi mai lea', 'and she returned'],
        ['o ia ia te ia', 'to him'],
        ['i le vaa;', 'into the ark'],
        ['auā sa i ai le vai', 'for the waters were'],
        ['i le fogāeleele uma.', 'on the face of all the earth'],
        ['Ona aapa atu lea', 'then he put forth'],
        ['o lona lima,', 'his hand'],
        ['ma tago i ai,', 'and took her'],
        ['ma au mai ia te ia', 'and drew her'],
        ['i le vaa.', 'into the ark'],
    ],
    'Genesis|8|10': [
        ['Ona toe faatalitali lea', 'he waited'],
        ['o ia', ''],
        ['i nisi aso e fitu,', 'yet another seven days'],
        ['ona toe tuuina atu lea', 'and again sent out'],
        ['e ia', 'he'],
        ['o le lupe', 'the dove'],
        ['ai le vaa;', 'from the ark'],
    ],
    'Genesis|8|11': [
        ['ua toe foi mai', 'returned'],
        ['ia te ia', 'to him'],
        ['o le lupe', 'the dove'],
        ['i le afiafi;', 'in the evening'],
        ['faauta foi,', 'and behold'],
        ['o i lona gutu', 'in her mouth'],
        ['le lau olive mata;', 'a freshly plucked olive leaf'],
        ['ona iloa ai lea', 'so Noah knew'],
        ['e Noa', ''],
        ['ua papau le vai', 'the waters had abated'],
        ['i le lalolagi.', 'from the earth'],
    ],
    'Genesis|8|12': [
        ['Ona toe faatalitali lea', 'he waited'],
        ['o ia', ''],
        ['i nisi aso e fitu,', 'yet another seven days'],
        ['ona tuuina atu lea', 'and sent out'],
        ['e ia', 'he'],
        ['o le lupe;', 'the dove'],
        ['a ua le toe foi mai lava', 'but she did not return again'],
        ['ia ia te ia.', 'to him'],
    ],
    'Genesis|8|13': [
        ['Ua oo i le tausaga', 'in the'],
        ['e ono selau ma le tasi,', 'six hundred and first year'],
        ['o le uluai masina ,', 'in the first month'],
        ['o le uluai aso o le masina,', 'on the first day of the month'],
        ['ua mate ai le vai', 'the waters were dried up'],
        ['i le laueleele;', 'from the earth'],
        ['ona to ese lea', 'then removed'],
        ['e Noa', 'Noah'],
        ['le ufi o le vaa,', 'the covering of the ark'],
        ['ma ua vaai atu', 'and looked'],
        ['faauta foi,', 'and behold'],
        ['ua matutu le fogāeleele.', 'the surface of the ground was dry'],
    ],
    'Genesis|8|14': [
        ['O le masina e lua', 'in the second month'],
        ['ma le aso e luafulu ma le fitu', 'on the twenty-seventh day'],
        ['o lea masina', 'of the month'],
        ['na matutu ai le eleele.', 'the earth was dried'],
    ],
    'Genesis|8|15': [
        ['Ua fetalai atu', 'then spoke'],
        ['le Atua', 'God'],
        ['ia Noa,', 'to Noah'],
        ['o loo faapea atu,', 'saying'],
    ],
    'Genesis|8|16': [
        ['Ina ulufafo ia', 'go out'],
        ['i le vaa,', 'of the ark'],
        ['o oe,', 'you'],
        ['ma lau avā,', 'and your wife'],
        ['ma ou atalii,', 'and your sons'],
        ['ma avā a ou atalii,', "and your sons' wives"],
        ['faatasi ma oe.', 'with you'],
    ],
    'Genesis|8|17': [
        ['Ina aumaia i fafo', 'bring out'],
        ['faatasi ma oe', 'with you'],
        ['o manu uma', 'every living thing'],
        ['o ia te oe,', 'that is with you'],
        ['i mea ola uma,', 'of all flesh'],
        ['o manu felelei,', 'birds'],
        ['ma manu vaefa,', 'and cattle'],
        ['atoa ma mea fetolofi uma', 'and every creeping thing'],
        ['e fetolofi i le eleele;', 'that creeps on the earth'],
        ['ina ia latou tutupu tele lava', 'that they may be fruitful'],
        ['i le lalolagi,', 'on the earth'],
        ['ia fanafanau', 'and multiply'],
        ['ma ia uluola', 'and increase'],
        ['i le lalolagi.', 'on the earth'],
    ],
    'Genesis|8|18': [
        ['Ona ulufafo lea', 'so went out'],
        ['o Noa,', 'Noah'],
        ['ma ona atalii,', 'and his sons'],
        ['ma lana avā,', 'and his wife'],
        ['ma avā a ona atalii', "and his sons' wives"],
        ['faatasi ma ia.', 'with him'],
    ],
    'Genesis|8|19': [
        ['Ona ulufafo lea', 'went out'],
        ['i le vaa,', 'of the ark'],
        ['o manu vaefa uma,', 'every animal'],
        ['o mea fetolofi uma,', 'every creeping thing'],
        ['ma manu felelei uma,', 'and every bird'],
        ['atoa ma mea uma', 'and everything'],
        ['e feoai i le laueleele', 'that moves on the earth'],
        ['e taitasi ma lona uiga.', 'after their kinds'],
    ],
    'Genesis|8|20': [
        ['Ona faia lea', 'then built'],
        ['e Noa', 'Noah'],
        ['o le fata faitaulaga', 'an altar'],
        ['ia Ieova;', 'to the LORD'],
        ['ua avea foi e ia', 'and he took'],
        ['nisi manu', 'some'],
        ['i manu vaefa uma e mamā,', 'of every clean animal'],
        ['ma manu felelei uma e mamā,', 'and of every clean bird'],
        ["ua ia fai a'i", 'and offered'],
        ['taulaga mu', 'burnt offerings'],
        ['i le fata.', 'on the altar'],
    ],
    'Genesis|8|21': [
        ['Ua lagona foi', 'and smelled'],
        ['e Ieova', 'the LORD'],
        ['le manogi lelei,', 'the pleasing aroma'],
        ['ona faapea ifo lea', 'and said'],
        ['o Ieova', 'the LORD'],
        ['i lona finagalo,', 'in His heart'],
        ['E ui lava ina leaga', 'although evil'],
        ['o manatu o loto o tagata', "the imagination of man's heart"],
        ['e afua mai', 'is from'],
        ['ina o tama iti,', 'his youth'],
        ['ou te le toe faaoo le malaia', 'I will never again curse'],
        ['i le laueleele', 'the ground'],
        ['ona o tagata;', 'because of man'],
        ['ou te le toe taia', 'nor will I again destroy'],
        ['mea ola uma', 'every living thing'],
        ['e pei ona ou faia.', 'as I have done'],
    ],
    'Genesis|8|22': [
        ['O aso uma o le lalolagi', 'while the earth remains'],
        ['e le toe utuva ai', 'shall not cease'],
        ['o tausaga e lulu ai,', 'seedtime'],
        ['ma tausaga e selesele ai,', 'and harvest'],
        ['o le maalili foi', 'cold'],
        ['ma le vevela,', 'and heat'],
        ['o le vaitoelau', 'winter'],
        ['ma le vaipalolo,', 'and summer'],
        ['o le ao foi', 'day'],
        ['ma le po.', 'and night'],
    ],
    # ── Genesis 9 — God's Covenant with Noah ──
    'Genesis|9|1': [
        ['Ua faamanuia atu', 'blessed'],
        ['e le Atua', 'God'],
        ['ia Noa', 'Noah'],
        ['ma ona atalii,', 'and his sons'],
        ['ma ua faapea atu ia te i latou,', 'and said to them'],
        ['Ia outou fanafanau,', 'be fruitful'],
        ['ma ia uluola,', 'and multiply'],
        ['ma ia tumu le lalolagi ia te outou.', 'and fill the earth'],
    ],
    'Genesis|9|2': [
        ["O le mata'u ia te outou", 'the fear of you'],
        ['ma le fefe ia te outou', 'and the dread of you'],
        ['e oo i', 'shall be upon'],
        ['manu vaefa uma o le lalolagi,', 'every beast of the earth'],
        ['ma manu felelei uma,', 'and every bird of the air'],
        ['ma mea uma e feoai', 'and everything that moves'],
        ['i le eleele,', 'on the earth'],
        ["atoa ma i'a uma o le sami;", 'and all fish of the sea'],
        ['ua tuuina atu ia', 'they are delivered'],
        ['i o outou lima.', 'into your hands'],
    ],
    'Genesis|9|3': [
        ['O mea ola uma e feoai,', 'every moving thing that lives'],
        ['e a outou ia', 'shall be yours'],
        ["e fai ma mea e 'ai;", 'to be food'],
        ['ua ou foaiina atu ma outou', 'I have given you'],
        ['o mea uma,', 'all things'],
        ['e pei o laau afu e tupu lauolaola.', 'as green plants'],
    ],
    'Genesis|9|4': [
        ['A o le aano o manu', 'but the flesh of animals'],
        ['o i ai le ola,', 'with its life'],
        ['o lona toto foi lea ,', 'that is its blood'],
        ['aua tou te aai ai.', 'you shall not eat'],
    ],
    'Genesis|9|5': [
        ['E moni lava,', 'surely'],
        ['ou te taui atu', 'I will require'],
        ['lo outou toto', 'your blood'],
        ['o lo outou ola;', 'of your lives'],
        ['ou te tauiatua', 'I will require'],
        ['i manu uma;', 'at every beast'],
        ['o le tagata foi,', 'and from man'],
        ['ou te taui atu', 'I will require'],
        ['le ola o le tagata', 'the life of man'],
        ["i le tagata lona uso.", "at the hand of every man's brother"],
    ],
    'Genesis|9|6': [
        ['O se na te faamaligiina', 'whoever sheds'],
        ['le toto o le tagata,', 'the blood of man'],
        ['e faamaligiina', 'shall be shed'],
        ['lona lava toto', 'his blood'],
        ['e le tagata;', 'by man'],
        ['au\u0101', 'for'],
        ['o le faatusa o le Atua', 'in the image of God'],
        ['na fai ai e ia', 'He made'],
        ['le tagata.', 'man'],
    ],
    'Genesis|9|7': [
        ['O outou foi,', 'and you'],
        ['ia outou fanafanau,', 'be fruitful'],
        ['ma ia outou uluola;', 'and multiply'],
        ['ia outou tuputupulaiina', 'bring forth abundantly'],
        ['i le lalolagi,', 'in the earth'],
        ['ma ia outou uluola ai.', 'and multiply in it'],
    ],
    'Genesis|9|8': [
        ['Ua fetalai atu foi', 'and said'],
        ['le Atua', 'God'],
        ['ia Noa,', 'to Noah'],
        ['ma ona atalii faatasi ma ia,', 'and his sons with him'],
        ['o loo faapea atu,', 'saying'],
    ],
    'Genesis|9|9': [
        ["Faauta foi,", 'behold'],
        ["o a'u,", 'I'],
        ['ou te faatumauina', 'establish'],
        ["la'u feagaiga ma outou,", 'my covenant with you'],
        ['ma a outou fanau', 'and with your descendants'],
        ['pe a mavae outou;', 'after you'],
    ],
    'Genesis|9|10': [
        ['atoa foi ma mea ola uma', 'and with every living creature'],
        ['o ia te outou,', 'that is with you'],
        ['o manu felelei,', 'birds'],
        ['o manu vaefa fanua,', 'cattle'],
        ['ma manu o le vao uma', 'and every beast of the earth'],
        ['o ia te outou,', 'with you'],
        ['o mea uma ua ulufafo i le vaa', 'all that go out of the ark'],
        ['e oo i manu uma o le lalolagi.', 'to every beast of the earth'],
    ],
    'Genesis|9|11': [
        ['Ou te faatumauina lava', 'I establish'],
        ["la'u feagaiga ma outou;", 'my covenant with you'],
        ['e le toe faaumatia lava', 'never again shall be cut off'],
        ['mea ola uma', 'all flesh'],
        ['i le vai o se lolo;', 'by the waters of a flood'],
        ['e leai foi', 'nor shall there any more be'],
        ['se toe lolo', 'a flood'],
        ['e faaumatia ai le lalolagi.', 'to destroy the earth'],
    ],
    'Genesis|9|12': [
        ['Ua fetalai atu foi', 'said'],
        ['le Atua,', 'God'],
        ['O le faailoga lenei', 'this is the sign'],
        ['o le feagaiga', 'of the covenant'],
        ['ou te faia', 'I make'],
        ['ma outou,', 'with you'],
        ['atoa ma mea ola uma o ia te outou,', 'and every living creature with you'],
        ['e autupulaga lava;', 'for perpetual generations'],
    ],
    'Genesis|9|13': [
        ['ua ou tuuina', 'I set'],
        ["la'u nuanua", 'my rainbow'],
        ['i le ao,', 'in the cloud'],
        ['e fai ma faailoga', 'it shall be a sign'],
        ['o le feagaiga', 'of the covenant'],
        ['a le lalolagi', 'of the earth'],
        ["ma a'u.", 'and Me'],
    ],
    'Genesis|9|14': [
        ['A ou faamalumaluina ifo', 'when I bring clouds over'],
        ['le lalolagi', 'the earth'],
        ['i se ao,', 'in a cloud'],
        ['ma ua iloa', 'and shall be seen'],
        ['le nuanua', 'the rainbow'],
        ['i le ao;', 'in the cloud'],
    ],
    'Genesis|9|15': [
        ['ona ou manatua lea', 'I will remember'],
        ["o la'u feagaiga", 'my covenant'],
        ['ua ou osia ma outou,', 'which is between Me and you'],
        ['ma mea ola eseese uma lava;', 'and every living creature of all flesh'],
        ['e le toe avea le vai', 'the waters shall never again become'],
        ['ma lolo', 'a flood'],
        ['e faaumatia ai mea ola uma.', 'to destroy all flesh'],
    ],
    'Genesis|9|16': [
        ['E i ai foi', 'shall be'],
        ['le nuanua', 'the rainbow'],
        ['i le ao,', 'in the cloud'],
        ['ou te vaai foi i ai,', 'and I will look upon it'],
        ['e manatua ai', 'to remember'],
        ['le feagaiga e faavavau', 'the everlasting covenant'],
        ["ua osia e a'u o le Atua", 'between Me God'],
        ['ma mea ola eseese uma lava', 'and every living creature'],
        ['o i le lalolagi.', 'on the earth'],
    ],
    'Genesis|9|17': [
        ['Ua fetalai atu', 'said'],
        ['le Atua', 'God'],
        ['ia Noa,', 'to Noah'],
        ['O le faailoga lenei', 'this is the sign'],
        ['o le feagaiga', 'of the covenant'],
        ["ua ou faatumauina e a'u", 'I have established'],
        ['ma mea ola uma', 'with all flesh'],
        ['o i le lalolagi.', 'on the earth'],
    ],
    'Genesis|9|18': [
        ['O atalii foi nei o Noa', 'the sons of Noah'],
        ['e na ulufafo i le vaa,', 'who went out of the ark'],
        ['o Semu, ma Hamo, ma Iafeta;', 'were Shem, Ham, and Japheth'],
        ['o Hamo foi', 'and Ham'],
        ['o le tam\u0101 ia o Kanana.', 'was the father of Canaan'],
    ],
    'Genesis|9|19': [
        ['O atalii nei e toatolu o Noa;', 'these three were the sons of Noah'],
        ['o i latou foi', 'and from these'],
        ['na \u0101ina solo ai le lalolagi uma.', 'the whole earth was populated'],
    ],
    'Genesis|9|20': [
        ['Ona amata lea e Noa', 'and Noah began'],
        ['ona galue i le eleele,', 'to be a farmer'],
        ['ua ia fai foi', 'and he planted'],
        ['le tovine.', 'a vineyard'],
    ],
    'Genesis|9|21': [
        ['Ua inu foi o ia', 'and he drank'],
        ['le uaina,', 'of the wine'],
        ['ma ua on\u0101 ai;', 'and was drunk'],
        ['ua le lavalav\u0101 foi o ia', 'and became uncovered'],
        ['i lona fale ie.', 'in his tent'],
    ],
    'Genesis|9|22': [
        ['Ona ilo atu lea', 'and saw'],
        ['e Hamo le tam\u0101 o Kanana', 'Ham the father of Canaan'],
        ['le le lavalav\u0101 o lona tam\u0101,', 'the nakedness of his father'],
        ["i le ua ta'uina atu e ia", 'and he told'],
        ['i ona uso e toalua', 'his two brothers'],
        ['i fafo.', 'outside'],
    ],
    'Genesis|9|23': [
        ['Ona fetagofi lea', 'then took'],
        ['o Semu ma Iafeta', 'Shem and Japheth'],
        ['i le ofu,', 'a garment'],
        ["ma faaee ai i o la tau'au,", 'and laid it on their shoulders'],
        ['ma la savavali tuumuli i tua,', 'and walked backward'],
        ['ma ufiufi ai', 'and covered'],
        ['le le lavalav\u0101 o lo la tam\u0101;', 'the nakedness of their father'],
        ['ua faasaga ese foi o laua mata,', 'their faces were turned away'],
        ['ua le ilo atu foi e i laua', 'and they did not see'],
        ['le le lavalav\u0101 o lo la tam\u0101.', 'the nakedness of their father'],
    ],
    'Genesis|9|24': [
        ['Ua ala Noa', 'Noah awoke'],
        ['i lana uaina,', 'from his wine'],
        ['ua iloa foi e ia', 'and he knew'],
        ['le mea ua faia ia te ia', 'what had been done to him'],
        ['e lona atalii aupito itiiti;', 'by his younger son'],
    ],
    'Genesis|9|25': [
        ['ona fai ane lea o ia,', 'and he said'],
        ['E malaia Kanana;', 'cursed be Canaan'],
        ['e matu\u0101 fai o ia', 'he shall be'],
        ['ma pologa', 'a servant'],
        ['i ona uso.', 'to his brothers'],
    ],
    'Genesis|9|26': [
        ['Ua fai ane foi o ia,', 'and he said'],
        ['Ua faafetaia Ieova', 'blessed be the LORD'],
        ['le Atua o Semu;', 'the God of Shem'],
        ['e fai foi Kanana', 'and may Canaan be'],
        ['mona pologa.', 'his servant'],
    ],
    'Genesis|9|27': [
        ['E faalauteleina', 'may God enlarge'],
        ['Iafeta', 'Japheth'],
        ['e le Atua,', 'by God'],
        ['e mau foi o ia', 'and may he dwell'],
        ['i fale ie o Semu;', 'in the tents of Shem'],
        ['e fai foi Kanana', 'and may Canaan be'],
        ['mona pologa.', 'his servant'],
    ],
    'Genesis|9|28': [
        ['Na ola foi Noa', 'and Noah lived'],
        ['talu mai le lolo', 'after the flood'],
        ['i tausaga e tolu selau', 'three hundred years'],
        ['ma le limagafulu.', 'and fifty'],
    ],
    'Genesis|9|29': [
        ['O aso uma foi o Noa', 'all the days of Noah'],
        ['e iva selau', 'nine hundred'],
        ['ma le limagafulu,', 'and fifty'],
        ['o ona tausaga ia;', 'years'],
        ['ona oti ai lea.', 'and he died'],
    ],
    # ── Genesis 10 — The Table of Nations ──
    'Genesis|10|1': [
        ['O gafa foi nei', 'these are the generations'],
        ['o atalii o Noa,', 'of the sons of Noah'],
        ['o Semu, o Hamo, ma Iafeta;', 'Shem, Ham, and Japheth'],
        ['na fananau foi', 'and were born'],
        ['ia te i latou', 'to them'],
        ['o atalii', 'sons'],
        ['a ua mavae le lolo.', 'after the flood'],
    ],
    'Genesis|10|2': [
        ['O atalii nei o Iafeta;', 'the sons of Japheth'],
        ['o Komeri,', 'Gomer'],
        ['ma Makoku,', 'and Magog'],
        ['ma Metai,', 'and Madai'],
        ['ma Iavana,', 'and Javan'],
        ['ma Tupalu,', 'and Tubal'],
        ['ma Meseko,', 'and Meshech'],
        ['ma Tirasi.', 'and Tiras'],
    ],
    'Genesis|10|3': [
        ['O atalii foi nei o Komeri;', 'the sons of Gomer'],
        ['o Asekeneso,', 'Ashkenaz'],
        ['ma Rifata,', 'and Riphath'],
        ['ma Tokaremo.', 'and Togarmah'],
    ],
    'Genesis|10|4': [
        ['O atalii foi nei o Iavana;', 'the sons of Javan'],
        ['o Elisa,', 'Elishah'],
        ['ma Tasesa,', 'and Tarshish'],
        ['o Kitimo,', 'Kittim'],
        ['ma Totanimo;', 'and Dodanim'],
    ],
    'Genesis|10|5': [
        ['o i latou nei', 'from these'],
        ['na \u0101ina solo ai', 'spread out'],
        ['o nuu tumatafaga', 'the coastland peoples'],
        ['o nuu ese,', 'of the nations'],
        ['i o latou laueleele,', 'in their lands'],
        ['e taitoatasi ma lana gagana,', 'each with his own language'],
        ['i o latou aiga,', 'in their clans'],
        ['i o latou nuu.', 'in their nations'],
    ],
    'Genesis|10|6': [
        ['O atalii foi o Hamo;', 'the sons of Ham'],
        ['o Kuso,', 'Cush'],
        ['ma Misaraimo,', 'and Mizraim'],
        ['ma Futu,', 'and Put'],
        ['ma Kanana.', 'and Canaan'],
    ],
    'Genesis|10|7': [
        ['O atalii foi o Kuso;', 'the sons of Cush'],
        ['o Sepa,', 'Seba'],
        ['ma Havila,', 'and Havilah'],
        ['ma Sapeta,', 'and Sabtah'],
        ['ma Ragama,', 'and Raamah'],
        ['ma Sapeteka;', 'and Sabteca'],
        ['o atalii foi o Ragama;', 'the sons of Raamah'],
        ['o Seepa,', 'Sheba'],
        ['ma Titana.', 'and Dedan'],
    ],
    'Genesis|10|8': [
        ['Na fanaua foi e Kuso', 'and Cush fathered'],
        ['o Nimarota;', 'Nimrod'],
        ['o ia foi', 'he'],
        ['na amata ona fai', 'began to be'],
        ['ma alii malosi', 'a mighty one'],
        ['i le lalolagi;', 'on the earth'],
    ],
    'Genesis|10|9': [
        ['o l\u0113 malosi foi o ia', 'he was mighty'],
        ['i tuli manu', 'in hunting'],
        ['i luma o Ieova;', 'before the LORD'],
        ['o le mea lea', 'therefore'],
        ['ua faapea ai le upu,', 'it is said'],
        ['E pei o Nimarota', 'like Nimrod'],
        ['l\u0113 malosi i tuli manu', 'mighty in hunting'],
        ['i luma o Ieova.', 'before the LORD'],
    ],
    'Genesis|10|10': [
        ['O le pogai foi o lona malo', 'the beginning of his kingdom'],
        ['o Papelu,', 'Babel'],
        ['ma Areka,', 'and Erech'],
        ['ma Akata,', 'and Accad'],
        ['ma Kalene,', 'and Calneh'],
        ['i le nuu o Senara.', 'in the land of Shinar'],
    ],
    'Genesis|10|11': [
        ['O le nuu lava lea', 'from that land'],
        ['na alu atu ai Asura,', 'he went to Assyria'],
        ['ma ia faia', 'and built'],
        ['Nineva,', 'Nineveh'],
        ['ma le aai o Reopo,', 'and Rehoboth-Ir'],
    ],
    'Genesis|10|12': [
        ['ma Kala,', 'and Calah'],
        ['ma Resena', 'and Resen'],
        ['e i le va o Nineva ma Kala;', 'between Nineveh and Calah'],
        ['o le aai tele lea.', 'that was the great city'],
    ],
    'Genesis|10|13': [
        ['Na fanaua foi o Misaraimo', 'and Mizraim fathered'],
        ['o tagata Luti,', 'the Ludim'],
        ['ma tagata Anama,', 'and Anamim'],
        ['ma tagata Leapi,', 'and Lehabim'],
        ['ma tagata Nafatui,', 'and Naphtuhim'],
    ],
    'Genesis|10|14': [
        ['ma tagata Pateruse,', 'and Pathrusim'],
        ['ma tagata Kaselui,', 'and Casluhim'],
        ['(sa tutupu ai Filisitia,)', '(from whom the Philistines came)'],
        ['ma tagata Kafatori.', 'and Caphtorim'],
    ],
    'Genesis|10|15': [
        ['Na fanaua foi e Kanana', 'and Canaan fathered'],
        ['o Saitonu,', 'Sidon'],
        ['o lana ulumatua lea,', 'his firstborn'],
        ['ma Heti,', 'and Heth'],
    ],
    'Genesis|10|16': [
        ['ma sa Iepus\u0113,', 'and the Jebusites'],
        ['ma sa Amor\u012b,', 'and the Amorites'],
        ['ma sa Kirekas\u0113,', 'and the Girgashites'],
        ['ma sa Hiv\u012b,', 'and the Hivites'],
    ],
    'Genesis|10|17': [
        ['ma sa Arek\u012b,', 'and the Arkites'],
        ['ma sa Sen\u012b,', 'and the Sinites'],
        ['ma sa Arat\u012b,', 'and the Arvadites'],
    ],
    'Genesis|10|18': [
        ['ma sa Semar\u012b,', 'and the Zemarites'],
        ['ma sa Hamat\u014d,', 'and the Hamathites'],
        ['mulimuli ane', 'afterward'],
        ['ua faasalalau atu', 'were dispersed'],
        ['aiga o sa Kanan\u0101.', 'the clans of the Canaanites'],
    ],
    'Genesis|10|19': [
        ['O le tuaoi foi o sa Kanan\u0101', 'the border of the Canaanites'],
        ['na afua lea i Saitonu,', 'began at Sidon'],
        ['ona oo lea i Kasa,', 'as far as Gaza'],
        ['i le ala e ui atu ai i Kira;', 'as you go toward Gerar'],
        ['ona ui lea i Sotoma,', 'as you go toward Sodom'],
        ['ma Komoro,', 'and Gomorrah'],
        ['ma Atama,', 'and Admah'],
        ['ma Sepoima,', 'and Zeboiim'],
        ['e oo atu i Lasa.', 'as far as Lasha'],
    ],
    'Genesis|10|20': [
        ['O atalii ia o Hamo', 'these are the sons of Ham'],
        ['i o latou aiga,', 'according to their clans'],
        ['ma a latou gagana,', 'according to their languages'],
        ['i o latou laueleele,', 'in their lands'],
        ['ma o latou nuu.', 'and in their nations'],
    ],
    'Genesis|10|21': [
        ['O Semu foi', 'and Shem'],
        ['na fanaua ona atalii ,', 'were born his sons'],
        ['o le tupuga', 'the father'],
        ['o le fanau uma a Eperu,', 'of all the children of Eber'],
        ['o le uso o Iafeta le matua.', 'the elder brother of Japheth'],
    ],
    'Genesis|10|22': [
        ['O atalii nei o Semu;', 'the sons of Shem'],
        ['o Elema,', 'Elam'],
        ['ma Asura,', 'and Asshur'],
        ['ma Afasata,', 'and Arphaxad'],
        ['ma Luti,', 'and Lud'],
        ['ma Arama.', 'and Aram'],
    ],
    'Genesis|10|23': [
        ['O atalii foi nei o Arama;', 'the sons of Aram'],
        ['o Usa,', 'Uz'],
        ['ma Hulo,', 'and Hul'],
        ['ma Kiteru,', 'and Gether'],
        ['ma Mase.', 'and Mash'],
    ],
    'Genesis|10|24': [
        ['Na fanaua foi e Afasata,', 'Arphaxad fathered'],
        ['o Selaa;', 'Shelah'],
        ['na fanaua foi e Selaa,', 'and Shelah fathered'],
        ['o Eperu.', 'Eber'],
    ],
    'Genesis|10|25': [
        ['Na fanaua foi e Eperu', 'to Eber were born'],
        ['ona atalii e toalua;', 'two sons'],
        ['o le igoa o le tasi', 'the name of the one'],
        ['o Peleko;', 'was Peleg'],
        ['au\u0101 o ona aso ia', 'for in his days'],
        ['ua vaevaeina ai le lalolagi;', 'the earth was divided'],
        ['o le igoa foi o lona uso', 'the name of his brother'],
        ['o Ioketana.', 'was Joktan'],
    ],
    'Genesis|10|26': [
        ['Na fanaua foi e Ioketana', 'and Joktan fathered'],
        ['o Alemotata,', 'Almodad'],
        ['ma Salefo,', 'and Sheleph'],
        ['ma Asamoveta,', 'and Hazarmaveth'],
        ['ma Iaraa,', 'and Jerah'],
    ],
    'Genesis|10|27': [
        ['ma Aturamo,', 'and Hadoram'],
        ['ma Usala,', 'and Uzal'],
        ['ma Tikelu,', 'and Diklah'],
    ],
    'Genesis|10|28': [
        ['o Upalu foi,', 'and Obal'],
        ['ma Apimalu,', 'and Abimael'],
        ['ma Seepa,', 'and Sheba'],
    ],
    'Genesis|10|29': [
        ['ma Ofeira,', 'and Ophir'],
        ['ma Havila,', 'and Havilah'],
        ['ma Iopapo;', 'and Jobab'],
        ['o i latou uma nei', 'all these'],
        ['o atalii o Ioketana.', 'were the sons of Joktan'],
    ],
    'Genesis|10|30': [
        ['O le mea na latou mau ai', 'their dwelling place'],
        ['na afua i Mesa', 'was from Mesha'],
        ['ua oo i Sefara,', 'to Sephar'],
        ['o le mauga lea i sasae.', 'the hill country of the east'],
    ],
    'Genesis|10|31': [
        ['O atalii ia o Semu,', 'these are the sons of Shem'],
        ['i o latou aiga,', 'according to their clans'],
        ['ma a latou gagana,', 'according to their languages'],
        ['i o latou laueleele,', 'in their lands'],
        ['i o latou nuu.', 'in their nations'],
    ],
    'Genesis|10|32': [
        ['O aiga ia o atalii o Noa,', 'these are the clans of the sons of Noah'],
        ['e tusa ma o latou gafa', 'according to their genealogies'],
        ['i o latou nuu;', 'in their nations'],
        ['o i latou ia foi', 'and from these'],
        ['na \u0101ina solo ai atu nuu', 'spread abroad the nations'],
        ['i le lalolagi', 'in the earth'],
        ['ina ua mavae o le lolo.', 'after the flood'],
    ],
    # ── Genesis 11:10-32 — Shem's Genealogy to Abram ──
    'Genesis|11|10': [
        ['O le gafa lenei o Semu;', 'these are the generations of Shem'],
        ['na ola Semu', 'Shem lived'],
        ['i tausaga e selau,', 'one hundred years'],
        ['ona fanaua lea e ia', 'and begot'],
        ['o Afasata', 'Arphaxad'],
        ['i le lua o tausaga', 'two years'],
        ['talu mai le lolo;', 'after the flood'],
    ],
    'Genesis|11|11': [
        ['ona ola lea o Semu', 'and Shem lived'],
        ['talu ina fanauina e ia o Afasata', 'after he begot Arphaxad'],
        ['i tausaga e lima selau,', 'five hundred years'],
        ['ma ua fanaua ai e ia', 'and he begot'],
        ['o atalii ma afafine.', 'sons and daughters'],
    ],
    'Genesis|11|12': [
        ['Na ola Afasata', 'Arphaxad lived'],
        ['i tausaga e tolugafulu ma le lima,', 'thirty-five years'],
        ['ona fanaua lea e ia', 'then he begot'],
        ['o Selaa;', 'Shelah'],
    ],
    'Genesis|11|13': [
        ['ona ola lea o Afasata', 'and Arphaxad lived'],
        ['talu ina fanauina e ia o Selaa', 'after he begot Shelah'],
        ['i tausaga e fa selau ma le tolu,', 'four hundred and three years'],
        ['ma ua fanaua ai e ia', 'and he begot'],
        ['o atalii ma afafine.', 'sons and daughters'],
    ],
    'Genesis|11|14': [
        ['Na ola Selaa', 'Shelah lived'],
        ['i tausaga e tolugafulu,', 'thirty years'],
        ['ona fanaua lea e ia', 'then he begot'],
        ['o Eperu;', 'Eber'],
    ],
    'Genesis|11|15': [
        ['ona ola lea o Salaa', 'and Shelah lived'],
        ['talu ina fanauina e ia o Eperu', 'after he begot Eber'],
        ['i tausaga e fa selau ma le tolu,', 'four hundred and three years'],
        ['ma ua fanaua ai e ia', 'and he begot'],
        ['o atalii ma afafine.', 'sons and daughters'],
    ],
    'Genesis|11|16': [
        ['Na ola Eperu', 'Eber lived'],
        ['i tausaga e tolugafulu ma le fa,', 'thirty-four years'],
        ['ona fanaua lea e ia', 'then he begot'],
        ['o Peleko;', 'Peleg'],
    ],
    'Genesis|11|17': [
        ['ona ola lea o Eperu', 'and Eber lived'],
        ['talu ina fanauina e ia o Peleko', 'after he begot Peleg'],
        ['i tausaga e fa selau ma le tolugafulu,', 'four hundred and thirty years'],
        ['ma ua fanaua ai e ia', 'and he begot'],
        ['o atalii ma afafine.', 'sons and daughters'],
    ],
    'Genesis|11|18': [
        ['Na ola Peleko', 'Peleg lived'],
        ['i tausaga e tolugafulu,', 'thirty years'],
        ['ona fanaua lea e ia', 'then he begot'],
        ['o Reu;', 'Reu'],
    ],
    'Genesis|11|19': [
        ['ona ola lea o Peleko', 'and Peleg lived'],
        ['talu ina fanauina e ia o Reu', 'after he begot Reu'],
        ['i tausaga e lua selau ma le iya,', 'two hundred and nine years'],
        ['ma ua fanaua ai e ia', 'and he begot'],
        ['o atalii ma afafine.', 'sons and daughters'],
    ],
    'Genesis|11|20': [
        ['Na ola Reu', 'Reu lived'],
        ['i tausaga e tolugafulu ma le lua,', 'thirty-two years'],
        ['ona fanaua lea e ia', 'then he begot'],
        ['o Seruka;', 'Serug'],
    ],
    'Genesis|11|21': [
        ['ona ola lea o Reu', 'and Reu lived'],
        ['talu ina fanauina e ia o Seruka', 'after he begot Serug'],
        ['i tausaga e lua selau ma le fitu,', 'two hundred and seven years'],
        ['ma ua fanaua ai e ia', 'and he begot'],
        ['o atalii ma afafine.', 'sons and daughters'],
    ],
    'Genesis|11|22': [
        ['Na ola Seruka', 'Serug lived'],
        ['i tausaga e tolugafulu,', 'thirty years'],
        ['ona fanaua lea e ia', 'then he begot'],
        ['o Nakori;', 'Nahor'],
    ],
    'Genesis|11|23': [
        ['ona ola lea o Seruka', 'and Serug lived'],
        ['talu ina fanauina e ia o Nakori', 'after he begot Nahor'],
        ['i tausaga e lua selau,', 'two hundred years'],
        ['ma ua fanaua ai e ia', 'and he begot'],
        ['o atalii ma afafine.', 'sons and daughters'],
    ],
    'Genesis|11|24': [
        ['Na ola Nakori', 'Nahor lived'],
        ['i tausaga e lua sefulu ma le iva,', 'twenty-nine years'],
        ['ona fanaua lea e ia', 'then he begot'],
        ['o Tara;', 'Terah'],
    ],
    'Genesis|11|25': [
        ['ona ola lea o Nakori', 'and Nahor lived'],
        ['talu ina fanauina e ia o Tara', 'after he begot Terah'],
        ['i tausaga e selau ma le sefulu ma le iva,', 'one hundred and nineteen years'],
        ['ma ua fanaua ai e ia', 'and he begot'],
        ['o atalii ma afafine.', 'sons and daughters'],
    ],
    'Genesis|11|26': [
        ['Na ola Tara', 'Terah lived'],
        ['i tausaga e fitugafulu,', 'seventy years'],
        ['ona fanaua lea e ia', 'then he begot'],
        ['o Aperamo, ma Nakori, ma Arana.', 'Abram, Nahor, and Haran'],
    ],
    'Genesis|11|27': [
        ['O gafa foi nei o Tara;', 'these are the generations of Terah'],
        ['na fanaua e Tara', 'Terah fathered'],
        ['o Aperamo, o Nakori ma Arana;', 'Abram, Nahor, and Haran'],
        ['na fanaua foi e Arana', 'and Haran fathered'],
        ['o Lota.', 'Lot'],
    ],
    'Genesis|11|28': [
        ['Ua oti foi Arana,', 'and Haran died'],
        ['a o nofo mai lona tama o Tara,', 'in the presence of his father Terah'],
        ['i le nuu na fanau ai o ia,', 'in the land of his birth'],
        ['o Uro lea i Kaletaia.', 'in Ur of the Chaldeans'],
    ],
    'Genesis|11|29': [
        ['Ona fai av\u0101 lea', 'then took wives'],
        ['o i laua o Aperamo ma Nakori;', 'Abram and Nahor'],
        ['o le igoa o le av\u0101 a Aperamo', 'the name of the wife of Abram'],
        ['o Sarai lea;', 'was Sarai'],
        ['a o le igoa o le av\u0101 a Nakori', 'and the name of the wife of Nahor'],
        ['o Meleka,', 'was Milcah'],
        ['o le afafine o Arana,', 'the daughter of Haran'],
        ['o le tam\u0101 o ia o Meleka,', 'the father of Milcah'],
        ['o le tam\u0101 foi o Iseka.', 'and the father of Iscah'],
    ],
    'Genesis|11|30': [
        ['O Sarai foi', 'and Sarai'],
        ['ua pa ia,', 'was barren'],
        ['ua leai sana tama.', 'she had no child'],
    ],
    'Genesis|11|31': [
        ['Na ave foi e Tara', 'then Terah took'],
        ['lona atalii o Aperamo,', 'his son Abram'],
        ['ma Lota le atalii o Arana,', 'and Lot the son of Haran'],
        ['o le atalii lea o lona atalii,', 'his grandson'],
        ['o Sarai foi le av\u0101 a lona atalii,', 'and Sarai his daughter-in-law'],
        ['o le av\u0101 lea a lona atalii o Aperamo;', "his son Abram's wife"],
        ['ona latou o atu lea ma i latou', 'and they went out together'],
        ['ai Uro i Kaletaia,', 'from Ur of the Chaldeans'],
        ['o le a o atu i le nuu o Kanana;', 'to go to the land of Canaan'],
        ['ona latou oo lea i Karana', 'and they came to Haran'],
        ['ma nonofo ai.', 'and dwelt there'],
    ],
    'Genesis|11|32': [
        ['O aso foi o Tara', 'all the days of Terah'],
        ['e lua selau ma le lima,', 'two hundred and five'],
        ['o ona tausaga ia;', 'years'],
        ['ona oti lea o Tara', 'and Terah died'],
        ['i Karana.', 'in Haran'],
    ],
    # ── Genesis 12: The Call of Abram ──
    'Genesis|12|1': [
        ['Ua fetalai mai Ieova ia Aperamo,', 'said the LORD to Abram'],
        ['Ia tuua e oe o lou nuu,', 'go out from your country'],
        ['ma tagata o lou nuu,', 'and from your family'],
        ['ma le aiga o lou tamā,', "and from your father's house"],
        ['a e alu atu i se nuu', 'to the land'],
        ['ou te faasino atu ai ia te oe.', 'that I will show you'],
    ],
    'Genesis|12|2': [
        ['Ou te faia oe ma nuu tele,', 'I will make you a great nation'],
        ['cu te faamanuia foi ia te oe,', 'I will bless you'],
        ['ou te matuā faamamaluina lou igoa;', 'I will make your name great'],
        ['e manuia foi oe.', 'and you shall be a blessing'],
    ],
    'Genesis|12|3': [
        ['Ou te faamanuia atu ia te i latou', 'I will bless'],
        ['o e faamanuia ia te oe,', 'those who bless you'],
        ['ou te faamalaia atu foi ia te i latou', 'whoever curses you'],
        ['o e fetuu ia te oe;', 'I will curse'],
        ['e manuia foi ia te oe', 'in you shall be blessed'],
        ['o aiga uma o le lalolagi.', 'all the families of the earth'],
    ],
    'Genesis|12|4': [
        ['Ona alu ai lea o Aperamo', 'Abram departed'],
        ['e faapei ona fetalai mai o Ieova ia te ia;', 'as the LORD had spoken to him'],
        ['na la o foi ma Lota;', 'and Lot went with him'],
        ['na alu atu Aperamo nai Karana', 'when he departed from Haran'],
        ['i lona tausaga e fitugafulu ma le lima.', 'seventy-five years old'],
    ],
    'Genesis|12|5': [
        ['Ua ave foi e Aperamo', 'Abram took'],
        ['lana avā o Sarai,', 'Sarai his wife'],
        ['ma Lota le atalii o lona uso,', "and Lot his brother's son"],
        ['ma o latou oloa uma lava na latou maua,', 'and all their possessions that they had gathered'],
        ['ma tagata na latou maua i Karana;', 'and the people that they had acquired in Haran'],
        ['ona latou o atu lea', 'and they set out'],
        ['o le a o i le nuu o Kanana;', 'to go to the land of Canaan'],
        ['ua oo foi i latou i le nuu o Kanana.', 'and they came to the land of Canaan'],
    ],
    'Genesis|12|6': [
        ['Ua ui atu foi Aperamo i lea nuu', 'Abram passed through the land'],
        ['ua oo i le mea e i ai Sekema,', 'to the place of Shechem'],
        ['i le aluna o Morē.', 'to the oak of Moreh'],
        ['Sa i ai sa Kananā', 'the Canaanites were'],
        ['i lea nuu i ia ona po.', 'at that time in the land'],
    ],
    'Genesis|12|7': [
        ['Ua faaali mai Ieova ia Aperamo,', 'the LORD appeared to Abram'],
        ['ma ua faapea mai,', 'and said'],
        ['Ou te foaiina atu lenei lava nuu', 'I will give this land'],
        ['mo lau fanau;', 'to your offspring'],
        ['ona faia lea e ia i lea mea', 'he built there'],
        ['o le fata faitaulaga ia Ieova,', 'an altar to the LORD'],
        ['sa faaali mai o ia ia te ia.', 'who had appeared to him'],
    ],
    'Genesis|12|8': [
        ['Ua tuua foi e ia lea mea,', 'he moved on from there'],
        ['a e alu atu i le mauga', 'to the hill'],
        ['i le itu i sasae o Peteli,', 'east of Bethel'],
        ['ma faatu ai lona fale ie,', 'and pitched his tent'],
        ['e i lona itu i sisifo o Peteli,', 'Bethel on the west'],
        ['a e i lona itu i sasae o Ai;', 'and Ai on the east'],
        ['ua ia faia foi le fata faitaulaga ia Ieova i lea mea,', 'he built an altar to the LORD there'],
        ['ma ua valaau atu i le suafa o Ieova.', 'and called upon the name of the LORD'],
    ],
    'Genesis|12|9': [
        ['Ua aga atu Aperamo,', 'Abram journeyed on'],
        ['ma alu atu pea i le itu i toga.', 'continuing toward the Negeb'],
    ],
    'Genesis|12|10': [
        ['Sa i ai foi le oge i lea nuu;', 'there was a famine in the land'],
        ['ona alu ifo lea o Aperamo i Aikupito', 'Abram went down to Egypt'],
        ['e āumau ai;', 'to sojourn there'],
        ['auā sa vale le oge i le nuu.', 'for the famine was severe in the land'],
    ],
    'Genesis|12|11': [
        ['Ua latalata ina oo i Aikupito,', 'as he was about to enter Egypt'],
        ['ona fai atu lea o ia', 'he said'],
        ['i lana avā o Sarai,', 'to Sarai his wife'],
        ['Faauta mai ea,', 'behold'],
        ['ua ou iloa', 'I know'],
        ['o oe o le fafine lalelei;', 'you are a beautiful woman'],
    ],
    'Genesis|12|12': [
        ['a vaai ia te oe tagata Aikupito,', 'when the Egyptians see you'],
        ['ona latou faapea ane lea.', 'they will say'],
        ['O lana avā lena;', 'this is his wife'],
        ['ona latou fasioti lea ia te au,', 'and they will kill me'],
        ['a e faaolaina oe.', 'but you they will let live'],
    ],
    'Genesis|12|13': [
        ["Se'i e fai atu", 'say'],
        ["o lo'u tuafafine oe,", 'you are my sister'],
        ["ina ia ou saogalemu ai ona o oe;", 'that it may go well with me because of you'],
        ["e ola ai foi a'u ona o oe.", 'and that my life may be spared because of you'],
    ],
    'Genesis|12|14': [
        ['Ua oo foi Aperamo i Aikupito,', 'when Abram came to Egypt'],
        ['ona vaaia mai lea e tagata Aikupito', 'the Egyptians saw'],
        ['o le fafine', 'the woman'],
        ['ua lalelei tasi lava ia.', 'that she was very beautiful'],
    ],
    'Genesis|12|15': [
        ['Ua ilo atu foi o ia', 'saw her'],
        ['e alii sa ia Farao,', 'the officials of Pharaoh'],
        ['ma ua vivii ia te ia ia Farao;', 'and praised her to Pharaoh'],
        ['ona avane ai lea o le fafine', 'she was taken'],
        ['i le fale o Farao.', "into Pharaoh's house"],
    ],
    'Genesis|12|16': [
        ['Ona agalelei atu lea o ia ia Aperamo', 'Abram was treated well'],
        ['ona o ia;', 'because of her'],
        ['sa ia te ia foi o mamoe, ma povi, ma asini poa', 'he had sheep, oxen, donkeys'],
        ['ma auauna tane, ma auauna fafine,', 'male and female servants'],
        ['ma asini fafine, ma kamela.', 'female donkeys and camels'],
    ],
    'Genesis|12|17': [
        ['A ua faatigaina e Ieova', 'the LORD plagued'],
        ['o Farao ma lona aiga', 'Pharaoh and his house'],
        ['i mala tetele', 'with great plagues'],
        ['ona o Sarai le avā a Aperamo.', "because of Sarai Abram's wife"],
    ],
    'Genesis|12|18': [
        ['Ona valaau ai lea o Farao ia Aperamo,', 'Pharaoh called Abram'],
        ['ua faapea atu,', 'and said'],
        ['Se a lenei mea ua e faia ia te au?', 'what is this you have done to me'],
        ["Pe se a le mea na e le ta'u mai ai", 'why did you not tell me'],
        ['ia te au o lau avā ia?', 'that she was your wife'],
    ],
    'Genesis|12|19': [
        ['O le a le mea na e faapea mai ai,', 'why did you say'],
        ["O lo'u tuafafine ia?", 'she is my sister'],
        ["Na fai a'u mao avea o ia", 'so that I took her'],
        ["e fai ma'u avā;", 'as my wife'],
        ['o lenei foi, faauta,', 'now here is your wife'],
        ['o lau avā lea,', 'your wife'],
        ['ina ave ia, ma lua o.', 'take her and go'],
    ],
    'Genesis|12|20': [
        ['Ona poloai atu lea o Farao', 'Pharaoh commanded'],
        ['i ona tagata ia te ia;', 'his men concerning him'],
        ['ona latou tuuina atu ai lea o ia', 'they sent him away'],
        ['la te o ma lana avā,', 'with his wife'],
        ['atoa ma ana mea uma.', 'and all that he had'],
    ],
    # ── Genesis 13: Abram and Lot Separate ──
    'Genesis|13|1': [
        ['Ua alu ae Aperamo', 'went up Abram'],
        ['nai Aikupito o ia,', 'from Egypt'],
        ['ma lana avā,', 'he and his wife'],
        ['ma ana mea uma,', 'and all that he had'],
        ['o Lota foi faatasi ma ia,', 'and Lot with him'],
        ['e o i le itu i toga.', 'toward the Negeb'],
    ],
    'Genesis|13|2': [
        ['Ua mauoa tele lava Aperamo', 'Abram was very rich'],
        ['i manu, ma ario, ma auro.', 'in livestock, in silver, and in gold'],
    ],
    'Genesis|13|3': [
        ['Ua alu foi o ia', 'he journeyed on'],
        ['i lana malaga', 'his journeys'],
        ['nai le itu i toga', 'from the Negeb'],
        ['ua oo i Peteli,', 'as far as Bethel'],
        ['i le mea lava sa muai i ai lona fale ie,', 'where his tent had been at the beginning'],
        ['i le va o Peteli ma Ai;', 'between Bethel and Ai'],
    ],
    'Genesis|13|4': [
        ['o le mea na i ai le fata faitaulaga', 'to the place of the altar'],
        ['sa na muai faia i lea mea;', 'which he had made at first'],
        ['ua valaau atu ai foi Aperamo', 'and there Abram called'],
        ['i le suafa o Ieova.', 'on the name of the LORD'],
    ],
    'Genesis|13|5': [
        ['O Lota foi,', 'Lot also'],
        ['sa la o ma Aperamo,', 'who went with Abram'],
        ['sa ia te ia o mamoe,', 'had flocks'],
        ['ma povi, ma fale ie.', 'and herds and tents'],
    ],
    'Genesis|13|6': [
        ['Ua le mafai lava', 'the land could not support them'],
        ['ona la mau faatasi i le nuu,', 'both dwelling together'],
        ['auā sa tele lava a laua mea,', 'for their possessions were so great'],
        ['ua le mafai ai', 'they could not'],
        ['ona la mau faatasi.', 'dwell together'],
    ],
    'Genesis|13|7': [
        ['Ua femisai foi', 'there was strife'],
        ['leoleo o manu a Aperamo', "between the herdsmen of Abram's livestock"],
        ['ma leoleo o manu a Lota;', "and the herdsmen of Lot's livestock"],
        ['o ona po foi ia', 'at that time'],
        ['sa mau ai sa Kananā', 'the Canaanites'],
        ['ma sa Perisē i le nuu.', 'and the Perizzites dwelt in the land'],
    ],
    'Genesis|13|8': [
        ['Ona fai atu lea o Aperamo ia Lota,', 'said Abram to Lot'],
        ['Aua lava', 'let there be no'],
        ["ne'i femisa'i i taua,", 'strife between you and me'],
        ["po o a taua leoleo manu:", 'and between my herdsmen and your herdsmen'],
        ['auā o le uso i taua.', 'for we are brothers'],
    ],
    'Genesis|13|9': [
        ['E le o i ou luma ea', 'Is not the whole land'],
        ['le laueleele uma?', 'before you'],
        ["Se'i e te'a ese ma a'u.", 'separate yourself from me'],
        ['Afai e te alu', 'if you take'],
        ['i le itu tauagavale,', 'the left hand'],
        ['ona ou alu ai lea', 'then I will go'],
        ['i le itu taumatau;', 'to the right'],
        ['a ē alu i le itu taumatau,', 'if you take the right hand'],
        ['ona ou alu ai lea', 'then I will go'],
        ['i le itu tauagavale.', 'to the left'],
    ],
    'Genesis|13|10': [
        ['Ua vaavaai Lota,', 'Lot lifted up his eyes'],
        ['ona ilo atu ai lea e ia', 'and saw'],
        ['i le fanua laugatasi uma', 'all the plain'],
        ['ua i ai Ioritana,', 'of the Jordan'],
        ['ua lafulemu uma lava,', 'that it was well watered everywhere'],
        ['e oo i Soara,', 'as you go to Zoar'],
        ['e pei o le faatoaga a Ieova,', 'like the garden of the LORD'],
        ['e pei o le laueleele o Aikupito,', 'like the land of Egypt'],
        ['a o lei faaumatia e Ieova', 'before the LORD destroyed'],
        ['o Sotoma ma Komoro.', 'Sodom and Gomorrah'],
    ],
    'Genesis|13|11': [
        ['Ona filifilia lea e Lota', 'Lot chose for himself'],
        ['mona o le fanua laugatasi uma', 'all the plain of the Jordan'],
        ['ua i ai Ioritana;', 'of the Jordan'],
        ["ua aga'i atu foi Lota i sasae;", 'and Lot journeyed east'],
        ["ona la te'a eseese ai lea", 'and they separated'],
        ['o le tasi ma le tasi.', 'from each other'],
    ],
    'Genesis|13|12': [
        ['Ua mau Aperamo', 'Abram dwelt'],
        ['i le nuu o Kanana,', 'in the land of Canaan'],
        ['a o Lota', 'but Lot'],
        ['ua mau ia i aai o le fanua laugatasi,', 'dwelt among the cities of the plain'],
        ['ma ua faatuina ai lona fale ie,', 'and pitched his tent'],
        ['ua oo atu i Sotoma.', 'as far as Sodom'],
    ],
    'Genesis|13|13': [
        ['A o tagata o Sotoma', 'the men of Sodom were'],
        ['ua leaga i latou,', 'wicked'],
        ['ma ua matuā agasala lava', 'and sinners exceedingly'],
        ['i luma o Ieova.', 'before the LORD'],
    ],
    'Genesis|13|14': [
        ['Ua fetalai atu foi Ieova ia Aperamo,', 'the LORD said to Abram'],
        ["ina ua te'a eseese o Lota ma ia,", 'after Lot had separated from him'],
        ["Se'i e vaavaai ia,", 'lift up your eyes'],
        ['ma ilo atu', 'and look'],
        ['i le mea e te i ai na,', 'from the place where you are'],
        ['i le itu i matu,', 'northward'],
        ['ma le itu i toga,', 'and southward'],
        ['ma sasae, ma sisifo;', 'and eastward and westward'],
    ],
    'Genesis|13|15': [
        ['auā o le laueleele uma', 'for all the land'],
        ['ua e ilo atu nei,', 'which you see'],
        ['ou te foaiina atu mo oe', 'I will give to you'],
        ['ma lau fanau e faavavau.', 'and to your offspring forever'],
    ],
    'Genesis|13|16': [
        ['Ou te faia foi lau fanau', 'I will make your offspring'],
        ['e pei o le efuefu o le eleele;', 'as the dust of the earth'],
        ['afai e mafaia e se tagata', 'so that if a man could'],
        ['ona faitauina o le efuefu o le eleele,', 'number the dust of the earth'],
        ['ona mafai lea', 'then'],
        ['ona faitaulia o lau lava fanau.', 'your offspring also could be numbered'],
    ],
    'Genesis|13|17': [
        ['Ina tulai ia,', 'arise'],
        ['ina fealualuai i le nuu', 'walk through the land'],
        ['i lona umi ma lona lautele;', 'its length and its breadth'],
        ['auā ou te foaiinaatua mo oe.', 'for I will give it to you'],
    ],
    'Genesis|13|18': [
        ['Ona ave lea e Aperamo lona fale ie,', 'Abram moved his tent'],
        ['ua alu atu', 'and came'],
        ['ua mau i aluna o Mamere,', 'and dwelt at the oaks of Mamre'],
        ['o i Heperona lea,', 'which are at Hebron'],
        ['ua ia faia foi i lea mea', 'and built there'],
        ['le fata faitaulaga ia Ieova.', 'an altar to the LORD'],
    ],
    # ── Genesis 14: The War of the Kings / Melchizedek ──
    'Genesis|14|1': [
        ['O ona po o Amarafilo', 'in the days of Amraphel'],
        ['le tupu o Senara,', 'king of Shinar'],
        ['o Arioka le tupu o Alasara,', 'and Arioch king of Ellasar'],
        ['o Kitalaoma le tupu o Elama,', 'and Chedorlaomer king of Elam'],
        ['ma Titalu le tupu o nuu;', 'and Tidal king of Goiim'],
    ],
    'Genesis|14|2': [
        ['na latou sii atu ai le taua', 'made war'],
        ['ia Pira le tupu o Sotoma,', 'with Bera king of Sodom'],
        ['ma Piresa le tupu o Komoro,', 'and with Birsha king of Gomorrah'],
        ['ma Senapo le tupu o Atama,', 'and Shinab king of Admah'],
        ['ma Semepo le tupu o Sepoima,', 'and Shemeber king of Zeboiim'],
        ['atoa ma le tupu o Pala,', 'and the king of Bela'],
        ['o Soara lea.', 'that is Zoar'],
    ],
    'Genesis|14|3': [
        ['Ua faapotopoto i latou nei uma', 'all these joined forces'],
        ['i le vanu o Setima,', 'in the Valley of Siddim'],
        ['o le sami oona lea.', 'that is the Salt Sea'],
    ],
    'Genesis|14|4': [
        ['E sefulu ma le lua o tausaga', 'twelve years'],
        ['sa nofo pologa ai i latou', 'they served'],
        ['ia Kitalaoma,', 'Chedorlaomer'],
        ['ua oo i le tausaga e sefulu ma le tolu', 'in the thirteenth year'],
        ['ona latou fou ai lea.', 'they rebelled'],
    ],
    'Genesis|14|5': [
        ['O lea tausaga foi e sefulu ma le fa', 'in the fourteenth year'],
        ['ua o mai ai Kitalaoma,', 'Chedorlaomer came'],
        ["ma tupu sa 'au faatasi ma ia,", 'and the kings who were with him'],
        ['ma latou fafasi i tagata o sa Rafā', 'and struck the Rephaim'],
        ['i Aserota Karenaima,', 'in Ashteroth-karnaim'],
        ['ma tagata Susema i Hamo,', 'and the Zuzim in Ham'],
        ['ma tagata Emema', 'and the Emim'],
        ['i Save Kiriataima,', 'in Shaveh-kiriathaim'],
    ],
    'Genesis|14|6': [
        ['ma sa Horī', 'and the Horites'],
        ['i lo latou mauga o Seira,', 'in their hill country of Seir'],
        ['e oo atu i Eleparana,', 'as far as El-paran'],
        ['e latalata lea i le vao.', 'on the border of the wilderness'],
    ],
    'Genesis|14|7': [
        ['Ua latou toe foi mai,', 'then they turned back'],
        ['ua oo i Enemisipata,', 'and came to En-mishpat'],
        ['o Katesa lea,', 'that is Kadesh'],
        ['ma latou fafasi i le nuu uma', 'and struck all the country'],
        ['o sa Amalekā,', 'of the Amalekites'],
        ['atoa foi ma sa Amorī', 'and also the Amorites'],
        ['sa nonofo i Haseso Tamara.', 'who lived in Hazazon-tamar'],
    ],
    'Genesis|14|8': [
        ['Ua o atu foi le tupu o Sotoma,', 'went out the king of Sodom'],
        ['ma le tupu o Komoro,', 'and the king of Gomorrah'],
        ['ma le tupu o Atama,', 'and the king of Admah'],
        ['ma le tupu o Sepoima,', 'and the king of Zeboiim'],
        ['ma le tupu o Pala,', 'and the king of Bela'],
        ['o Soara lea;', 'that is Zoar'],
        ['ma latou tau ai le taua', 'and joined battle'],
        ['ma i latou', 'with them'],
        ['i le vanu o Setima;', 'in the Valley of Siddim'],
    ],
    'Genesis|14|9': [
        ['o i latou ,', 'with Chedorlaomer'],
        ['o Kitalaoma le tupu o Elama,', 'king of Elam'],
        ['ma Titalu le tupu o nuu,', 'and Tidal king of Goiim'],
        ['ma Amarafilo le tupu o Senara,', 'and Amraphel king of Shinar'],
        ['ma Arioka le tupu o Alasara;', 'and Arioch king of Ellasar'],
        ['o tupu na e toafa', 'four kings'],
        ['ma ia tupu e toalima.', 'against five'],
    ],
    'Genesis|14|10': [
        ['Sa i ai foi i le vanu o Setima', 'now the Valley of Siddim was full of'],
        ['o lua o pulu emeri e tele lava;', 'bitumen pits'],
        ['na sosola foi le tupu o Sotoma', 'and the king of Sodom'],
        ['ma le tupu o Komoro', 'and the king of Gomorrah'],
        ['ma pauu i lea mea;', 'fell into them'],
        ['a o e na totoe', 'and the fugitives'],
        ['ua sosola i latou i le mauga.', 'fled to the mountain'],
    ],
    'Genesis|14|11': [
        ['Ona latou vetea lea', 'they took'],
        ['o oloa uma o Sotoma ma Komoro,', 'all the goods of Sodom and Gomorrah'],
        ["atoa ma a latou mea e 'ai uma,", 'and all their provisions'],
        ['ona o ai lea o i latou.', 'and went their way'],
    ],
    'Genesis|14|12': [
        ['Ua latou avea foi Lota', 'they also took Lot'],
        ['le atalii o le uso o Aperamo,', "the son of Abram's brother"],
        ['atoa ma ana oloa,', 'and his goods'],
        ['o ia foi sa nofo i Sotoma,', 'who lived in Sodom'],
        ['ona o ai lea o i latou.', 'and went their way'],
    ],
    'Genesis|14|13': [
        ['Ua alu atu foi le tasi na sao', 'one who had escaped came'],
        ["ma ta'uatua ia Aperamo le Eperu,", 'and told Abram the Hebrew'],
        ['o lē sa mau i aluna o Mamere', 'who was living by the oaks of Mamre'],
        ['o sa Amorī,', 'the Amorite'],
        ['o le uso o Esekolo,', 'brother of Eshcol'],
        ['o le uso foi o Aneri;', 'and of Aner'],
        ['o i latou na osi feagaiga ma Aperamo.', 'these were allies of Abram'],
    ],
    'Genesis|14|14': [
        ['Ua faalogo Aperamo', 'Abram heard'],
        ['ua avea lona uso i le taua,', 'that his kinsman had been taken captive'],
        ["ona saunia lea e ia ona tagata ua a'oa'oina,", 'he mustered the men born in his house'],
        ['e na fananau i lona aiga,', 'trained men'],
        ['e toatolu selau ma le toasefulu ma le toavalu,', 'three hundred and eighteen'],
        ['ma ua tuliloa ia te i latou', 'and pursued them'],
        ['e oo i Tanu.', 'as far as Dan'],
    ],
    'Genesis|14|15': [
        ["Ua ia tofia foi o 'au", 'he divided his forces'],
        ['a ona tagata i le po', 'against them by night'],
        ['e tau ma i latou,', 'and attacked them'],
        ['ua fafasi foi ia te i latou,', 'and pursued them'],
        ['ma tuli muliau ia te i latou', 'as far as Hobah'],
        ['ua oo i Hopa,', 'which is'],
        ['e i le itu tauagavale lea o Tamaseko.', 'north of Damascus'],
    ],
    'Genesis|14|16': [
        ['Ua toe maua mai foi e ia', 'he brought back'],
        ['o le oloa uma lava;', 'all the goods'],
        ['ua ia toe maua mai foi Lota lona uso,', 'and also brought back Lot his kinsman'],
        ['ma aua oloa,', 'and his goods'],
        ['o fafine foi,', 'with the women'],
        ['atoa ma le nuu.', 'and the people'],
    ],
    'Genesis|14|17': [
        ['Ua alu atu foi le tupu o Sotoma', 'the king of Sodom went out'],
        ['e faafetaiai ia te ia', 'to meet him'],
        ['i le vanu o Savee,', 'at the Valley of Shaveh'],
        ["e ta'ua foi lea", 'that is'],
        ['o le vanu o le tupu,', "the King's Valley"],
        ['ina ua toe foi mai', 'after he returned'],
        ['i le taua ma Kitalaoma,', 'from the defeat of Chedorlaomer'],
        ["ma tupu sa 'au faatasi ma ia.", 'and the kings who were with him'],
    ],
    'Genesis|14|18': [
        ['A o Mekisateko le tupu o Salema', 'Melchizedek king of Salem'],
        ['ua avane e ia areto ma uaina;', 'brought out bread and wine'],
        ['o le faitaulaga foi o ia', 'he was priest'],
        ['a le Atua silisili ese.', 'of God Most High'],
    ],
    'Genesis|14|19': [
        ['Ua ia faamanuia foi ia te ia,', 'he blessed him'],
        ['ua faapea atu,', 'and said'],
        ['Ia manuia Aperamo', 'blessed be Abram'],
        ['i le Atua silisili ese,', 'by God Most High'],
        ['e ona le lagi ma le lalologi;', 'Possessor of heaven and earth'],
    ],
    'Genesis|14|20': [
        ['ia faafetaia foi', 'and blessed be'],
        ['le Atua silisili ese,', 'God Most High'],
        ['o le na tuuina mai ou fili', 'who has delivered your enemies'],
        ['i ou lima.', 'into your hand'],
        ['Ua foai atu foi e Aperamo ia te ia', 'and Abram gave him'],
        ["o mea e sefulu a'i o mea uma.", 'a tenth of everything'],
    ],
    'Genesis|14|21': [
        ['Ua fai mai foi le tupu o Sotoma', 'the king of Sodom said'],
        ['ia Aperamo,', 'to Abram'],
        ['Tuu mai ia ia te au o tagata,', 'give me the persons'],
        ['a e ave ma oe le oloa.', 'but the goods take yourself'],
    ],
    'Genesis|14|22': [
        ['A ua tali atu Aperamo', 'Abram answered'],
        ['i le tupu o Sotoma,', 'the king of Sodom'],
        ["Ua sii lo'u lima ia Ieova,", 'I have lifted my hand to the LORD'],
        ['le Atua silisili ese,', 'God Most High'],
        ['e ona le lagi ma le lalolagi,', 'Possessor of heaven and earth'],
    ],
    'Genesis|14|23': [
        ['ou te le avea lava sina manoa', 'I will not take a thread'],
        ['po o sina nonoa seevae,', 'or a sandal strap'],
        ['ou te le avea lava sina mea', 'I will not take anything'],
        ['i au mea uma,', 'that is yours'],
        ["ina ne'i faapea a oe,", 'lest you should say'],
        ['Ua mauoa Aperamo ia te au.', 'I have made Abram rich'],
    ],
    'Genesis|14|24': [
        ['Tau lava o mea ua uma ona aai e taulelea,', 'only what the young men have eaten'],
        ['ma vaegāoloa a tagata', 'and the share of the men'],
        ["na matou o ma a'u,", 'who went with me'],
        ['o Aneri, ma Esekolo, ma Mamere,', 'Aner, Eshcol, and Mamre'],
        ['ia latou ave a latou vaegāoloa.', 'let them take their share'],
    ],
    # ── Genesis 15 ─────────────────────────────────────────
    'Genesis|15|1': [
        ['Ua mavae ia mea,', 'after these things'],
        ['ona tŭlei mai lea o le afioga a Ieova ia Aperamo i le faaaliga,', 'the word of the LORD came to Abram in a vision'],
        ['ua faapea mai,', 'saying'],
        ['Aperamo e, aua e te fefe;', 'Abram, do not fear'],
        ["o a'u nei o lou talita,", 'I am your shield'],
        ['o lou taui e matuā tele lava.', 'your reward shall be very great'],
    ],
    'Genesis|15|2': [
        ['Ona tali atu lea o Aperamo,', 'Abram answered'],
        ['Le Alii e, Ieova,', 'O Lord GOD'],
        ['se a se mea e te foai mai ia te au,', 'what will you give me'],
        ["auā e leai sa'u fanau,", 'since I have no children'],
        ["o le e ona le tofi i lo'u aiga", 'the heir of my house'],
        ['o Elisara lea le Tamaseko?', 'is Eliezer of Damascus'],
    ],
    'Genesis|15|3': [
        ['Ua faapea foi a Aperamo,', 'Abram also said'],
        ["Faauta, ua e le foai mai ia te au sa'u fanau;", 'behold, you have given me no offspring'],
        ["faauta foi, e fai mo'u suli", 'and behold, my heir is'],
        ["le tagata ua fanau i lo'u aiga.", 'one born in my house'],
    ],
    'Genesis|15|4': [
        ['Faauta foi, ua tŭlei mai le afioga a Ieova ia te ia,', 'behold, the word of the LORD came to him'],
        ['ua faapea mai,', 'saying'],
        ['E le fai lea tagata mou suli;', 'this man shall not be your heir'],
        ['a o le e fanaua e oe lava', 'but one who comes from your own body'],
        ['e fai o ia mou suli.', 'shall be your heir'],
    ],
    'Genesis|15|5': [
        ['Ua ia aumaia foi o ia i fafo,', 'He brought him outside'],
        ['ma faapea atu,', 'and said'],
        ['Ina e vaavaai ae ia i le lagi,', 'look toward heaven'],
        ['ma e faitauina fetu,', 'and count the stars'],
        ['pe afai e mafaia ona e faitauina;', 'if you are able to count them'],
        ['ua ia faapea atu foi ia te ia,', 'and He said to him'],
        ['E faapea lava lau fanau.', 'so shall your offspring be'],
    ],
    'Genesis|15|6': [
        ['Ua faatuatua foi o ia ia Ieova,', 'he believed the LORD'],
        ["ona ia ta'uamiotonuina mai ai lea ia te ia.", 'and He counted it to him as righteousness'],
    ],
    'Genesis|15|7': [
        ['Ua ia fetalai mai foi ia te ia,', 'He also said to him'],
        ["O a'u o Ieova,", 'I am the LORD'],
        ['o le na aumaia oe ai Uro i Kaletaia,', 'who brought you out of Ur of the Chaldeans'],
        ['ina ia foaiina atu ai ia te oe', 'to give to you'],
        ['lenei lava nuu e fai mou tofi.', 'this very land as your possession'],
    ],
    'Genesis|15|8': [
        ['Ona tali atu lea a ia,', 'he answered'],
        ['Le Alii e, Ieova,', 'O Lord GOD'],
        ['se a se mea ou te iloa ai', 'how shall I know'],
        ["e fai mo'u tofi lenei nuu ?", 'that I shall possess this land'],
    ],
    'Genesis|15|9': [
        ['Ona fetalai mai lea o ia ia te ia,', 'He said to him'],
        ['Au mai ia ia te au', 'bring Me'],
        ['se povi fafine ua tolu ona tausaga,', 'a three-year-old heifer'],
        ["ma se 'oti fafine ua tolu ona tausaga,", 'a three-year-old female goat'],
        ['ma se mamoe poa ua tolu ona tausaga,', 'a three-year-old ram'],
        ['ma se manutagi,', 'a turtledove'],
        ['ma se tamai lupe.', 'and a young pigeon'],
    ],
    'Genesis|15|10': [
        ['Ona avane lea e ia o ia mea uma,', 'he brought all these to Him'],
        ['ua ia taiisiluaina i latou,', 'and cut them in two'],
        ['ma tuu faafesagai taitasi le itu ma le tasi ona itu;', 'and laid each piece opposite the other'],
        ['a o manu felelei ua ia le isiluaina.', 'but the birds he did not divide'],
    ],
    'Genesis|15|11': [
        ['Ua felelei ifo foi manu feai', 'birds of prey came down'],
        ['i tino o manu mamate,', 'upon the carcasses'],
        ['ona tutuli lea e Aperamo ia te i latou.', 'and Abram drove them away'],
    ],
    'Genesis|15|12': [
        ['Ua tāli goto le la,', 'as the sun was going down'],
        ['ona oo lea ia Aperamo o le moe gase;', 'a deep sleep fell upon Abram'],
        ["faauta foi, o le mata'u o le pouliuli tele lava", 'and behold, a dreadful great darkness'],
        ['ua oo ia te ia.', 'fell upon him'],
    ],
    'Genesis|15|13': [
        ['Ona fetalai mai lea o ia ia Aperamo,', 'He said to Abram'],
        ['Ia e iloa lelei', 'know for certain'],
        ['e āumau lau fanau i le nuu ese,', 'your descendants will be sojourners in a foreign land'],
        ['e nofo pologa foi i latou ia te i latou,', 'and they will serve them'],
        ['e faatigaina foi i latou e i latou,', 'and they will be afflicted by them'],
        ['o tausaga ia e fa selau;', 'for four hundred years'],
    ],
    'Genesis|15|14': [
        ['o le nuu foi latou te nofo pologa ai', 'the nation they serve'],
        ['ou te faasalaina;', 'I will judge'],
        ['mulimuli ane latou te o mai ai', 'and afterward they shall come out'],
        ['ma le oloa tele.', 'with great possessions'],
    ],
    'Genesis|15|15': [
        ['A o oe,', 'as for you'],
        ['e te alu atu ma le filemu', 'you shall go in peace'],
        ['i ou tamā,', 'to your fathers'],
        ['e tauumia oe', 'you shall be buried'],
        ['pe a e matuā toeaina lava.', 'at a good old age'],
    ],
    'Genesis|15|16': [
        ['A o lona fa o tupulaga', 'in the fourth generation'],
        ['latou te toe foi mai ai iinei;', 'they shall return here'],
        ['auā ua le atoatoa le agasala a sa Amorī', 'for the iniquity of the Amorites'],
        ['i nei ona po.', 'is not yet complete'],
    ],
    'Genesis|15|17': [
        ['Ua oo foi ina goto o le la,', 'when the sun had gone down'],
        ['ma ua pouliuli,', 'and it was dark'],
        ['faauta foi, o le ogāumu ua alu ae ai le asu,', 'behold, a smoking oven with rising smoke'],
        ['ma le lamepa ua mu', 'and a flaming torch'],
        ['ua ui i le va o na mea sa vaeluaina.', 'passed between the divided pieces'],
    ],
    'Genesis|15|18': [
        ['O le aso lava lea', 'on that very day'],
        ['na osi ai le feagaiga e Ieova ma Aperamo,', 'the LORD made a covenant with Abram'],
        ['ua faapea ane,', 'saying'],
        ['Ua ou foaiina mo lau fanau', 'to your descendants I have given'],
        ['lenei laueleele,', 'this land'],
        ['e afua i le vaitafe o Aikupito', 'from the river of Egypt'],
        ['e oo atu i le vaitafe tele,', 'to the great river'],
        ['o le vaitafe o Eufirate lea;', 'the river Euphrates'],
    ],
    'Genesis|15|19': [
        ['o sa Kenī,', 'the Kenites'],
        ['ma sa Kinasā,', 'and the Kenizzites'],
        ['ma sa Katemonī,', 'and the Kadmonites'],
    ],
    'Genesis|15|20': [
        ['ma sa Hetī,', 'and the Hittites'],
        ['ma sa Perisē,', 'and the Perizzites'],
        ['ma sa Rafā,', 'and the Rephaim'],
    ],
    'Genesis|15|21': [
        ['o sa Amorī foi,', 'the Amorites'],
        ['ma sa Kananā,', 'and the Canaanites'],
        ['ma sa Kirekasē,', 'and the Girgashites'],
        ['ma sa Iepusē.', 'and the Jebusites'],
    ],
    # ── Genesis 16 ─────────────────────────────────────────
    'Genesis|16|1': [
        ['A o Sarai', 'Sarai'],
        ['le avā a Aperamo,', "the wife of Abram"],
        ['ua le fanau ia', 'bore no children'],
        ['ia te ia;', 'to him'],
        ['sa ia te ia foi', 'she had also'],
        ['le auauna fafine,', 'a maidservant'],
        ['o le Aikupito,', 'an Egyptian'],
        ['o Akara lona igoa.', 'Hagar was her name'],
    ],
    'Genesis|16|2': [
        ['Na fai atu foi Sarai', 'Sarai said'],
        ['ia Aperamo,', 'to Abram'],
        ['Faauta mai ea,', 'behold now'],
        ['ua finagalo Ieova', 'the LORD has willed'],
        ['ia ou le fanau;', 'that I bear no children'],
        ["se'i e alu ane", 'go in'],
        ["i la'u auauna fafine;", 'to my maidservant'],
        ['atonu ou te maua ai', 'perhaps I shall obtain'],
        ['ni tama ia te ia.', 'children by her'],
        ['Ua usiusitai foi Aperamo', 'and Abram heeded'],
        ['i le upu a Sarai.', 'the voice of Sarai'],
    ],
    'Genesis|16|3': [
        ['O Sarai foi', 'Sarai'],
        ['le avā a Aperamo,', "Abram's wife"],
        ['na ia ave ia Akara,', 'took Hagar'],
        ['o le Aikupito,', 'the Egyptian'],
        ['o lana auauna fafine,', 'her maidservant'],
        ['ma tuuina atu', 'and gave her'],
        ['ia Aperamo lana tane,', 'to Abram her husband'],
        ['e fai mana avā,', 'to be his wife'],
        ['ina ua mavae', 'after had passed'],
        ['o tausaga e sefulu', 'ten years'],
        ['sa nofo ai Aperamo', 'that Abram had lived'],
        ['i le nuu o Kanana.', 'in the land of Canaan'],
    ],
    'Genesis|16|4': [
        ['Ona alu ane lea o ia', 'he went in'],
        ['ia Akara,', 'to Hagar'],
        ['ona to ai lea o ia;', 'and she conceived'],
        ['ua iloa e ia', 'when she saw'],
        ['ua to o ia,', 'that she had conceived'],
        ['ona faaleaogaina lea e ia', 'she despised'],
        ['o lona matai fafine.', 'her mistress'],
    ],
    'Genesis|16|5': [
        ['Ona fai atu lea o Sarai', 'Sarai said'],
        ['ia Aperamo,', 'to Abram'],
        ['Ia i luga ia te oe', 'be upon you'],
        ["lo'u agaleagaina;", 'my wrong'],
        ["o a'u nei foi,", 'as for me'],
        ['na ou tuuina atu', 'I gave'],
        ["la'u auauna fafine", 'my maidservant'],
        ['ia te oe;', 'to you'],
        ['ua iloa foi e ia', 'when she saw'],
        ['ua to o ia,', 'that she had conceived'],
        ['ona faaleaogaina ai lea', 'I became despised'],
        ["o a'u e ia;", 'by her'],
        ['ia faamasino mai Ieova', 'may the LORD judge'],
        ['ia te i taua.', 'between you and me'],
    ],
    'Genesis|16|6': [
        ['Ona tali mai lea o Aperamo', 'Abram said'],
        ['ia Sarai,', 'to Sarai'],
        ['Faauta,', 'behold'],
        ['o ia te oe le pule', 'the power is yours'],
        ['i lau auauna fafine,', 'over your maidservant'],
        ['faitalia lava oe', 'do as you please'],
        ['se mea e te faia', 'whatever you wish'],
        ['ia te ia.', 'to her'],
        ['Ua agaleaga foi Sarai', 'then Sarai dealt harshly'],
        ['ia te ia,', 'with her'],
        ['ona sola ese ai lea o ia', 'and she fled'],
        ['i ona luma.', 'from her presence'],
    ],
    'Genesis|16|7': [
        ['Ua maua foi o ia', 'found her'],
        ['e le agelu a Ieova', 'the angel of the LORD'],
        ['i le vaipuna', 'by the spring'],
        ['i le vao,', 'in the wilderness'],
        ['o le vaipuna', 'the spring'],
        ['i le ala i Sara.', 'on the way to Shur'],
    ],
    'Genesis|16|8': [
        ['Ona faapea atu lea o ia,', 'and he said'],
        ['Akara e,', 'Hagar'],
        ['le anauna a Sarai,', 'servant of Sarai'],
        ['maifea oe?', 'where have you come from'],
        ['O fea ea', 'and where'],
        ['a e alu i ai?', 'are you going'],
        ['Ona tali mai lea o ia,', 'she said'],
        ['Ua ou sola mai', 'I am fleeing from'],
        ['ia Sarai', 'Sarai'],
        ["o lo'u matai.", 'my mistress'],
    ],
    'Genesis|16|9': [
        ['Ona faapea atu lea', 'said'],
        ['o le agelu a Ieova', 'the angel of the LORD'],
        ['ia te ia,', 'to her'],
        ['Ia e foi atu', 'return'],
        ['i lou matai', 'to your mistress'],
        ['ma e faamaulalo atu', 'and submit yourself'],
        ['ia te ia.', 'under her hand'],
    ],
    'Genesis|16|10': [
        ['Ua fetalai atu foi', 'also said'],
        ['le agelu a Ieova', 'the angel of the LORD'],
        ['ia te ia,', 'to her'],
        ['Ou te matuā faatoateleina lava', 'I will surely multiply'],
        ['lau fanau,', 'your offspring'],
        ['e le mafai lava ona faitau', 'that they cannot be counted'],
        ['ina ua toatele.', 'for multitude'],
    ],
    'Genesis|16|13': [
        ['Ona faaigoaina lea e ia', 'she called'],
        ['le suafa o Ieova', 'the name of the LORD'],
        ['o le na fetalai mai', 'who spoke'],
        ['ia te ia,', 'to her'],
        ['O oe le Atua', 'You are the God'],
        ['le ua faaali mai', 'who sees'],
        ['ia te au;', 'me'],
        ['auā ua faapea ana,', 'for she said'],
        ['Ua ou vaai atu ea iinei', 'have I also here seen'],
        ['i tua o loo silasila mai', 'Him who sees'],
        ['ia te au?', 'me'],
    ],
    'Genesis|16|14': [
        ['O le mea lea', 'therefore'],
        ['ua faaigoaina ai le vaieli,', 'the well was called'],
        ['o Pere-laaroi,', 'Beer-lahai-roi'],
        ['faauta,', 'behold'],
        ['o loo i le va', 'it is between'],
        ['o Katesa ma Pareta.', 'Kadesh and Bered'],
    ],
    'Genesis|16|15': [
        ['Ua fanau mai foi Akara', 'Hagar also bore'],
        ['le atalii', 'a son'],
        ['ia Aperamo;', 'to Abram'],
        ['ua faaigoaina foi', 'and named also'],
        ['e Aperamo', 'by Abram'],
        ['lona atalii', 'his son'],
        ['na fanau mai ia Akara,', 'whom Hagar bore'],
        ['o Isamaeli.', 'Ishmael'],
    ],
    'Genesis|16|16': [
        ['O le valu sefulu ma le ono', 'eighty-six'],
        ['o tausaga o Aperamo', 'years old was Abram'],
        ['na fanau mai ai Akara', 'when Hagar bore'],
        ['o Isamaeli', 'Ishmael'],
        ['le atalii o Aperamo.', 'the son of Abram'],
    ],
    # ── Genesis 17 ─────────────────────────────────────────
    'Genesis|17|1': [
        ['O le iva sefulu ma le iva', 'ninety-nine'],
        ['o tausaga o Aperamo,', 'years old was Abram'],
        ['na faaali mai ai Ieova', 'the LORD appeared'],
        ['ia Aperamo,', 'to Abram'],
        ['ua faapea mai foi', 'and said'],
        ['ia te ia,', 'to him'],
        ["O a'u o le Atua", 'I am God'],
        ["e o'u le malosi uma lava;", 'Almighty'],
        ['ia e savali', 'walk'],
        ["i o'u luma,", 'before Me'],
        ['ma ia sao lau amio.', 'and be blameless'],
    ],
    'Genesis|17|2': [
        ['Ta te osia le feagaiga', 'I will make My covenant'],
        ['ma oe,', 'with you'],
        ['ou te matuā faatoateleina lava', 'and will multiply exceedingly'],
        ['au fanau .', 'your descendants'],
    ],
    'Genesis|17|3': [
        ['Ona faapaū fao lea', 'fell on his face'],
        ['o Aperamo;', 'Abram'],
        ['ona fetalai mai lea', 'and said'],
        ['o le Atua', 'God'],
        ['ia te ia,', 'to him'],
        ['ua faapea mai,', 'saying'],
    ],
    'Genesis|17|4': [
        ["O a'u nei,", 'as for Me'],
        ['ou te fai atu,', 'I say'],
        ['faauta,', 'behold'],
        ['o ia te i taua le feagaiga,', 'My covenant is with you'],
        ['e fai foi oe', 'and you shall be'],
        ['ma tupuga', 'the father'],
        ['o nuu e tele.', 'of many nations'],
    ],
    'Genesis|17|5': [
        ['E le toe valaauina', 'no longer shall be called'],
        ['lou igoa o Aperamo,', 'your name Abram'],
        ['a o le a igoa oe', 'but your name shall be'],
        ['o Aperaamo,', 'Abraham'],
        ['auā ua ou faia oe', 'for I have made you'],
        ['ma tupuga', 'the father'],
        ['o nuu e tele.', 'of many nations'],
    ],
    'Genesis|17|6': [
        ['Ou te matuā faauluolaina oe,', 'I will make you exceedingly fruitful'],
        ['ou te faia oe', 'I will make you'],
        ['ma tupuga o nuu;', 'into nations'],
        ['e tupuga mai foi', 'and shall come'],
        ['ia te oe', 'from you'],
        ['o tupu.', 'kings'],
    ],
    'Genesis|17|7': [
        ['Ou te faatumauina foi', 'I will establish'],
        ['o la ta feagaiga', 'My covenant'],
        ['ma oe,', 'with you'],
        ['ma lau fanau,', 'and your descendants'],
        ['i a latou tupulaga,', 'in their generations'],
        ['pe a mavae atu oe,', 'after you'],
        ['e fai ma feagaiga e faavavau;', 'for an everlasting covenant'],
        ["ia fai a'u ma Atua", 'to be God'],
        ['ia te oe', 'to you'],
        ['ma au fanau', 'and to your descendants'],
        ['pe a mavae atu oe.', 'after you'],
    ],
    'Genesis|17|8': [
        ['Ou te foai foi', 'I give'],
        ['ia te oe,', 'to you'],
        ['ma au fanau,', 'and to your descendants'],
        ['pe a mavae atu oe,', 'after you'],
        ['o le nuu', 'the land'],
        ['o loo e āumau ai,', 'in which you are a stranger'],
        ['o le nuu uma lava lea', 'all the land'],
        ['o Kanana,', 'of Canaan'],
        ['e fai mo latou', 'as their possession'],
        ['e faavavau;', 'forever'],
        ["e fai foi a'u", 'and I will be'],
        ['mo latou Atua.', 'their God'],
    ],
    'Genesis|17|9': [
        ['Ua fetalai mai foi', 'said'],
        ['le Atua', 'God'],
        ['ia Aperaamo,', 'to Abraham'],
        ['A o oe,', 'as for you'],
        ['ia e tausi', 'you shall keep'],
        ['i la ta feagaiga,', 'My covenant'],
        ['o oe,', 'you'],
        ['ma lau fanau,', 'and your descendants'],
        ['i a latou tupulaga,', 'throughout their generations'],
        ['pe a mavae atu oe.', 'after you'],
    ],
    'Genesis|17|10': [
        ['O la tatou feagaiga lenei', 'this is My covenant'],
        ['ma onutou,', 'with you'],
        ['atoa ma lau fanau,', 'and your descendants'],
        ['pe a mavae atu oe,', 'after you'],
        ['tou te tausia;', 'which you shall keep'],
        ['e peritomeina', 'shall be circumcised'],
        ['tane uma', 'every male'],
        ['o ia te outou.', 'among you'],
    ],
    'Genesis|17|11': [
        ['Tou te peritomeina foi', 'you shall be circumcised'],
        ["pa'u o outou tino,", 'in the flesh of your foreskins'],
        ['e fai ai foi', 'and it shall be'],
        ['ma faailoga', 'a sign'],
        ['o la tatou feagaiga', 'of the covenant'],
        ['ma outou.', 'with you'],
    ],
    'Genesis|17|12': [
        ['O le ua valu ona po', 'he who is eight days old'],
        ['o ia te outou', 'among you'],
        ['ia peritomeina ia,', 'shall be circumcised'],
        ['o tane uma', 'every male'],
        ['i a outou auga tupulaga;', 'throughout your generations'],
        ['o le ua fanau', 'he who is born'],
        ['i le aiga,', 'in the house'],
        ['ma le ua faatauina mai', 'or bought'],
        ['i tupe', 'with money'],
        ['i tagata ese uma lava,', 'from any foreigner'],
        ['e le o sau fanau ia.', 'who is not your offspring'],
    ],
    'Genesis|17|13': [
        ['Ia peritomeina lava', 'must be circumcised'],
        ['o le ua fanau', 'he who is born'],
        ['i lou aiga,', 'in your house'],
        ['ma le ua faatauina', 'and he who is bought'],
        ['i au tupe;', 'with your money'],
        ['e i o outou tino', 'shall be in your flesh'],
        ['la tatou feagaiga', 'My covenant'],
        ['o le feagaiga e faavavau.', 'for an everlasting covenant'],
    ],
    'Genesis|17|14': [
        ['A o le tane foi', 'any male'],
        ['ua le peritomeina,', 'who is uncircumcised'],
        ['o le ua le peritomeina', 'who is not circumcised'],
        ["i le pa'u", 'in the flesh'],
        ['o lona tino', 'of his foreskin'],
        ['e vavaeeseina', 'shall be cut off'],
        ['lea tagata', 'that person'],
        ['i lona nuu;', 'from his people'],
        ['ua tuumavaega ia', 'he has broken'],
        ['i le feagaiga.', 'the covenant'],
    ],
    'Genesis|17|15': [
        ['Ua faapea mai foi', 'also said'],
        ['le Atua', 'God'],
        ['ia Aperaamo,', 'to Abraham'],
        ['O Sarai lau avā,', 'as for Sarai your wife'],
        ['aua e te toe valaauia', 'you shall not call'],
        ['lona igoa o Sarai,', 'her name Sarai'],
        ['a o Sara', 'but Sarah'],
        ['o lona igoa lea.', 'shall be her name'],
    ],
    'Genesis|17|16': [
        ['Ou te faamanuia foi', 'I will bless'],
        ['ia te ia,', 'her'],
        ['ma ou foaiina atu foi', 'and I will also give'],
        ['se atalii mo oe', 'a son to you'],
        ['mai ia te ia;', 'by her'],
        ['ou te faamanuia lava', 'I will bless'],
        ['ia te ia,', 'her'],
        ['e fai foi o ia', 'and she shall be'],
        ['ma tupuga o nuu;', 'a mother of nations'],
        ['e tupuga mai foi', 'shall come'],
        ['ia te ia', 'from her'],
        ['o tupu o nuu.', 'kings of peoples'],
    ],
    'Genesis|17|17': [
        ['Ona faapaū fao lea', 'fell on his face'],
        ['o Aperaamo,', 'Abraham'],
        ["ua 'ata'ata,", 'and laughed'],
        ['ma faapea ifo', 'and said'],
        ['i lona loto,', 'in his heart'],
        ['E fanau mai ea se atalii', 'shall a child be born'],
        ['i le tagata', 'to a man'],
        ['ua selau ona tausaga?', 'who is a hundred years old'],
        ['O Sara foi', 'and shall Sarah'],
        ['e fanau ea', 'bear a child'],
        ['ia ua iva sefulu', 'who is ninety'],
        ['ona tausaga?', 'years old'],
    ],
    'Genesis|17|18': [
        ['Ua faapea atu foi', 'said'],
        ['Aperaamo', 'Abraham'],
        ['i le Atua,', 'to God'],
        ['E, ou te manao', 'Oh, that'],
        ['ia ola Isamaeli', 'Ishmael might live'],
        ['i ou luma!', 'before You!'],
    ],
    'Genesis|17|19': [
        ['Ua fetalai mai le Atua,', 'God said'],
        ['E moni lava,', 'indeed'],
        ['e fanau mai sou atalii', 'a son shall be born to you'],
        ['ia Sara lau avā,', 'by Sarah your wife'],
        ['e te faaigoa foi', 'and you shall call'],
        ['ia te ia', 'him'],
        ['o Isaako;', 'Isaac'],
        ['ou te faatumauina foi', 'I will establish'],
        ['la ma feagaiga', 'My covenant'],
        ['ma ia,', 'with him'],
        ['atoa ma ana fanau,', 'and with his descendants'],
        ['pe a mavae atu o ia,', 'after him'],
        ['o le feagaiga e faavavau.', 'for an everlasting covenant'],
    ],
    'Genesis|17|20': [
        ['I le ma Isamaeli foi,', 'as for Ishmael'],
        ['ua ou faalogo ai', 'I have heard'],
        ['ia te oe;', 'you'],
        ['faauta,', 'behold'],
        ['ua ou faamanuia', 'I have blessed'],
        ['ia te ia,', 'him'],
        ['ou te faauluola', 'I will make fruitful'],
        ['ia te ia,', 'him'],
        ['ou te matuā faatoateleina lava;', 'and will multiply him exceedingly'],
        ['e fanaua foi e ia', 'he shall beget'],
        ['o alii', 'princes'],
        ['e toasefulu ma le toalua;', 'twelve'],
        ['ou te fai foi o ia', 'and I will make him'],
        ['ma tupuga', 'into'],
        ['o le nuu tele.', 'a great nation'],
    ],
    'Genesis|17|21': [
        ['A e peitai', 'but'],
        ["o la'u feagaiga", 'My covenant'],
        ['ou te faatumauina lea', 'I will establish'],
        ['ia Isaako,', 'with Isaac'],
        ['o le a fanau mai', 'whom shall be born'],
        ['e Sara', 'by Sarah'],
        ['ia te oe', 'to you'],
        ['i le faapenei lava', 'at this set time'],
        ['i le tausaga atali.', 'next year'],
    ],
    'Genesis|17|22': [
        ['Ua faaiu foi e ia', 'when He had finished'],
        ['o la la tautalaga', 'talking'],
        ['ma ia,', 'with him'],
        ['ona afio ae lea', 'went up'],
        ['o le Atua', 'God'],
        ['nai ia Aperaamo.', 'from Abraham'],
    ],
    'Genesis|17|23': [
        ['Ona tago lea', 'took'],
        ['e Aperaamo', 'Abraham'],
        ['i lona atalii o Isamaeli,', 'his son Ishmael'],
        ['ma i latou uma', 'and all'],
        ['na fananau i lona aiga,', 'who were born in his house'],
        ['atoa ma i latou uma', 'and all'],
        ['na faatauina i ana tupe,', 'who were bought with his money'],
        ['o tane uma lava', 'every male'],
        ['i le aiga o Aperaamo,', "in Abraham's household"],
        ['ma ua peritomeina e ia', 'and he circumcised'],
        ["o pa'u o latou tino", 'the flesh of their foreskins'],
        ['i lea lava aso,', 'that very same day'],
        ['e pei ona fetalai mai ai', 'as had said'],
        ['le Atua', 'God'],
        ['ia te ia.', 'to him'],
    ],
    'Genesis|17|24': [
        ['O le iva sefulu ma le iva', 'ninety-nine'],
        ['o tausaga o Aperaamo', 'years old was Abraham'],
        ['na peritomeina ai o ia', 'when he was circumcised'],
        ["i le pa'u", 'in the flesh'],
        ['o lona tino.', 'of his foreskin'],
    ],
    'Genesis|17|25': [
        ['A ua sefulu ma le tolu', 'and thirteen'],
        ['tausaga', 'years old'],
        ['o lona atalii o Isamaeli', 'was his son Ishmael'],
        ['ina ua peritomeina ai o ia', 'when he was circumcised'],
        ["i le pa'u", 'in the flesh'],
        ['o lona tino.', 'of his foreskin'],
    ],
    'Genesis|17|26': [
        ['O lea lava aso e tasi', 'that very same day'],
        ['na peritomeina ai', 'was circumcised'],
        ['Aperaamo', 'Abraham'],
        ['ma lona atalii', 'and his son'],
        ['o Isamaeli;', 'Ishmael'],
    ],
    'Genesis|17|27': [
        ['o tane uma foi', 'and all the men'],
        ['i lona aiga,', 'of his household'],
        ['e na fananau mai', 'those born'],
        ['i le aiga,', 'in the house'],
        ['atoa ma e na faatauina', 'and those bought'],
        ['i tupe', 'with money'],
        ['i tagata ese,', 'from a foreigner'],
        ['na peritomeina i latou', 'were circumcised'],
        ['faatasi ma ia.', 'with him'],
    ],

    # ==========================================================
    # Genesis 18 – Abraham's three visitors / Sarah laughs /
    #              Bargaining for Sodom
    # ==========================================================
    'Genesis|18|1': [
        ['Ua faaali mai', 'appeared'],
        ['Ieova', 'the LORD'],
        ['ia te ia', 'to him'],
        ['i aluna o Mamere,', 'at the oaks of Mamre'],
        ['a o nofo o ia', 'as he sat'],
        ['i le faitotoa', 'in the door'],
        ['o lona fale ie', 'of his tent'],
        ['i le aoauli;', 'in the heat of the day'],
    ],
    'Genesis|18|2': [
        ['ua tepa ae foi o ia', 'he lifted up his eyes'],
        ['ma ilo atu,', 'and looked'],
        ['faauta foi,', 'and behold'],
        ['o loo tut\u016b mai', 'stood'],
        ['ia te ia', 'by him'],
        ['tagata e toatolu;', 'three men'],
        ['ua ia ilo atu,', 'when he saw them'],
        ["ona momo'e atu ai lea", 'he ran'],
        ['nai le faitotoa', 'from the door'],
        ['o lona fale ie', 'of his tent'],
        ['e faafetaiai', 'to meet'],
        ['ia te i latou,', 'them'],
        ['ona ifo toele lea o ia.', 'and bowed himself to the ground'],
    ],
    'Genesis|18|3': [
        ['Ua faapea atu foi o ia,', 'he said'],
        ['Le alii e,', 'My Lord'],
        ["afai ua alofaina mai nei a'u", 'if I have found favor'],
        ['e oe,', 'in your sight'],
        ["aua ne'i e maliu loa", 'do not pass on by'],
        ['ia te au', 'me'],
        ['lau auauna;', 'your servant'],
    ],
    'Genesis|18|4': [
        ["se'i aumaia", 'let be brought'],
        ['sina vai', 'a little water'],
        ['e mulumulu ai', 'to wash'],
        ['o outou vae,', 'your feet'],
        ['ma outou malolo', 'and rest yourselves'],
        ['i lalo o le laau;', 'under the tree'],
    ],
    'Genesis|18|5': [
        ['ou te au mai foi', 'let me bring'],
        ["sina mea e 'ai", 'a morsel of bread'],
        ['ia faamalosi ai', 'that you may refresh'],
        ['o outou loto,', 'your hearts'],
        ['ona outou o ai lea;', 'after that you may pass on'],
        ['au\u0101 o le mea lea', 'since for this reason'],
        ['ua outou o mai ai', 'you have come'],
        ['i la outou auauna.', 'to your servant'],
        ['Ona latou tali mai lea,', 'So they said'],
        ['E te faia lava', 'Do so'],
        ['pei ona e fai mai na.', 'as you have said'],
    ],
    'Genesis|18|6': [
        ['Ona vave ane lea', 'So hurried'],
        ['o Aperaamo', 'Abraham'],
        ['i le fale ie', 'into the tent'],
        ['ia Sara,', 'to Sarah'],
        ['ma faapea atu,', 'and said'],
        ['Ia vave', 'Make ready quickly'],
        ['ona ave esea', 'take'],
        ['o falaoa,', 'flour'],
        ['o falaoa lelei,', 'fine flour'],
        ['se tolu,', 'three measures'],
        ['ia palu', 'knead it'],
        ["ma fai a'i", 'and make'],
        ['ni potoi areto.', 'cakes of bread'],
    ],
    'Genesis|18|7': [
        ["Ona momo'e lea", 'Then ran'],
        ['o Aperaamo', 'Abraham'],
        ['i lona lafu povi,', 'to the herd'],
        ['ua au mai ai', 'and took'],
        ['le tamai povi,', 'a calf'],
        ["e mu'amu'a", 'tender'],
        ['ma le lelei,', 'and good'],
        ['ua avatu', 'and gave it'],
        ['i le taulealea;', 'to the young man'],
        ['ona ia faavave lea', 'and he hastened'],
        ['ona gaosia.', 'to prepare it'],
    ],
    'Genesis|18|8': [
        ['Ua na ave foi', 'He took'],
        ["o su\u0101susu to'a,", 'curds'],
        ['ma su\u0101susu,', 'and milk'],
        ['ma le tamai povi', 'and the calf'],
        ['sa gaosia e ia,', 'which had been prepared'],
        ['ua laulauina atu ai', 'and set it'],
        ['i o latou luma;', 'before them'],
        ['a o ia', 'and he'],
        ['ua tu ane', 'stood'],
        ['ia te i latou', 'by them'],
        ['i lalo o le laau,', 'under the tree'],
        ['ona latou aai lea.', 'and they ate'],
        ['Ua latou fai atu', 'They said'],
        ['ia te ia,', 'to him'],
        ['O fea o i ai', 'Where is'],
        ['lau av\u0101 o Sara?', 'your wife Sarah?'],
    ],
    'Genesis|18|9': [
        ['Ona tali mai lea o ia,', 'He said'],
        ['Faauta,', 'Behold'],
        ['o loo i fal\u0113 lava.', 'she is in the tent'],
    ],
    'Genesis|18|10': [
        ['Ona faapea atu lea o ia,', 'He said'],
        ['Ou te toe foi mai lava', 'I will certainly return'],
        ['ia te oe', 'to you'],
        ['i lela tausaga;', 'next year'],
        ['faauta foi,', 'and behold'],
        ['e fanau mai', 'shall bear'],
        ['lau av\u0101 o Sara', 'your wife Sarah'],
        ['o le tama tane.', 'a son'],
        ['A o faalogologo ane foi', 'Now was listening'],
        ['o Sara', 'Sarah'],
        ['i le faitotoa', 'at the door'],
        ['o le fale ie,', 'of the tent'],
        ['sa i ona tua.', 'which was behind him'],
    ],
    'Genesis|18|11': [
        ['O Aperaamo foi', 'Now Abraham'],
        ['ma Sara', 'and Sarah'],
        ['ua matutua', 'were old'],
        ['i laua,', 'both of them'],
        ['ua tele', 'advanced'],
        ['o la tausaga;', 'in years'],
        ['ua mavae foi', 'it had ceased'],
        ['ia Sara', 'with Sarah'],
        ['le tu o fafine.', 'the way of women'],
    ],
    'Genesis|18|12': [
        ["Ona 'ata'ata lemu lea", 'So laughed'],
        ['o Sara,', 'Sarah'],
        ['ua faapea,', 'saying'],
        ['Ua ou loomatua,', 'After I am old'],
        ['e ia te au ea', 'shall I have'],
        ['le fiafia,', 'pleasure'],
        ["o la'u alii foi", 'my lord also'],
        ['ua toeaina ia?', 'being old?'],
    ],
    'Genesis|18|13': [
        ['Ona fetalai atu lea', 'Then said'],
        ['o Ieova', 'the LORD'],
        ['ia Aperaamo,', 'to Abraham'],
        ['Se a le mea', 'Why did'],
        ["ua 'ata'ata ai Sara,", 'Sarah laugh'],
        ['o loo faapea,', 'saying'],
        ['E moni ea,', 'Shall I indeed'],
        ['a ou toe fanau', 'bear a child'],
        ["o a'u le loomatua?", 'when I am old?'],
    ],
    'Genesis|18|14': [
        ['E iai ea', 'Is there'],
        ['se mea e faigata', 'anything too hard'],
        ['ia Ieova?', 'for the LORD?'],
        ['O ona po', 'At the time'],
        ['ua tuupoina', 'appointed'],
        ['ou te toe foi mai ai', 'I will return'],
        ['ia te oe,', 'to you'],
        ['i lela tausaga,', 'next year'],
        ['e maua mai ai', 'shall have'],
        ['e Sara', 'Sarah'],
        ['le tama tane.', 'a son'],
    ],
    'Genesis|18|15': [
        ['Ona faafiti mai lea', 'Then denied'],
        ['o Sara,', 'Sarah'],
        ['ua faapea mai,', 'saying'],
        ["Ou te lei 'ata'ata lava,", 'I did not laugh'],
        ['au\u0101 ua fefe ia.', 'for she was afraid'],
        ['Ona tali atu lea o ia,', 'But He said'],
        ['E leai,', 'No'],
        ["na e 'ata'ata lava.", 'but you did laugh'],
    ],
    'Genesis|18|16': [
        ['Ona tulai lea', 'Then rose up'],
        ['o ia tagata', 'the men'],
        ['nai lea mea,', 'from there'],
        ['ma faasaga atu', 'and looked'],
        ['i Sotoma;', 'toward Sodom'],
        ['ua latou o foi', 'and went along'],
        ['ma Aperaamo', 'with Abraham'],
        ['na te molimolia i latou.', 'to see them on their way'],
    ],
    'Genesis|18|17': [
        ['Ona fetalai ane lea', 'Then said'],
        ['o Ieova,', 'the LORD'],
        ['Ou te natia ea', 'Shall I hide'],
        ['ia Aperaamo', 'from Abraham'],
        ['le mea a ou faia?', 'what I am about to do?'],
    ],
    'Genesis|18|18': [
        ['Au\u0101 foi', 'seeing that'],
        ['o Aperaamo', 'Abraham'],
        ['o le a fai o ia', 'shall surely become'],
        ['ma tupuga', 'a nation'],
        ['o le nuu tele', 'great'],
        ['ma le malosi;', 'and mighty'],
        ['e manuia foi', 'and shall be blessed'],
        ['ia te ia', 'in him'],
        ['o nuu uma', 'all the nations'],
        ['o le lalolagi.', 'of the earth'],
    ],
    'Genesis|18|19': [
        ['Au\u0101 ua ou iloa o ia', 'For I know him'],
        ['na te poloai atu', 'that he will command'],
        ['i ana fanau', 'his children'],
        ['ma lona aiga', 'and his household'],
        ['pe a mavae atu o ia;', 'after him'],
        ['latou te tausia', 'and they shall keep'],
        ['le ala o Ieova,', 'the way of the LORD'],
        ['i lo latou fai', 'by doing'],
        ['amiotonu', 'righteousness'],
        ['ma faamasinoga,', 'and justice'],
        ['ina ia faataunuuina', 'that the LORD may bring'],
        ['e Ieova', 'upon Abraham'],
        ['ia Aperaamo', 'that which'],
        ['le mea na ia fetalai atu ai', 'He has spoken'],
        ['ia te ia.', 'to him'],
    ],
    'Genesis|18|20': [
        ['Ona faapea lea', 'Then said'],
        ['a Ieova,', 'the LORD'],
        ['O le alaga', 'the outcry'],
        ['mai Sotoma', 'of Sodom'],
        ['ma Komoro', 'and Gomorrah'],
        ['ua tele,', 'is great'],
        ['ma ua matu\u0101 tele lava', 'and very grievous'],
        ['a latou agasala;', 'is their sin'],
    ],
    'Genesis|18|21': [
        ['o le mea lea', 'therefore'],
        ['ou te alu ifo ai,', 'I will go down'],
        ['ia iloa', 'to see'],
        ['po ua faia lava', 'whether they have done'],
        ['e i latou', 'altogether'],
        ['e poi o le alaga', 'according to the outcry'],
        ['ua oo mai ai', 'that has come'],
        ['ia te au;', 'to Me'],
        ['afai foi ua leai,', 'and if not'],
        ['ou te iloa lava.', 'I will know'],
    ],
    'Genesis|18|22': [
        ['Ona tuua lea', 'So turned'],
        ['o lea mea', 'from there'],
        ['e nei tagata,', 'the men'],
        ['ua o atu', 'and went'],
        ['i Sotoma;', 'toward Sodom'],
        ['a o Aperaamo', 'but Abraham'],
        ['ua tu pea o ia', 'still stood'],
        ['i luma o Ieova.', 'before the LORD'],
    ],
    'Genesis|18|23': [
        ['Ona faalatalata atu lea', 'Then drew near'],
        ['o Aperaamo,', 'Abraham'],
        ['ua faapea atu,', 'and said'],
        ['E te faaumatia ea', 'Will You destroy'],
        ['e ua amiotonu', 'the righteous'],
        ['faatasi ma', 'with'],
        ['e amio leaga?', 'the wicked?'],
    ],
    'Genesis|18|24': [
        ['Pe afai o i le aai', 'Suppose there are in the city'],
        ['tagata e toalimagafulu', 'fifty persons'],
        ['o e amiotouu,', 'who are righteous'],
        ['e te faaumatia ea', 'will You destroy'],
        ['a e le faasaoina', 'and not spare'],
        ['le nuu', 'the place'],
        ['ona o le toalimagafulu', 'for the fifty righteous'],
        ['o e amiotonu', 'who are'],
        ['o i ai?', 'in it?'],
    ],
    'Genesis|18|25': [
        ['Ia mamao lava', 'Far be it'],
        ['ia te oe', 'from You'],
        ['ona e faia faapea', 'to do such a thing'],
        ['e fasioti', 'to put to death'],
        ['i e amiotonu', 'the righteous'],
        ['faatasi ma', 'with'],
        ['e amio leaga;', 'the wicked'],
        ['ma ona faagatusa', 'so that the righteous fare'],
        ['e amiotonu', 'as'],
        ['ma e amio leaga,', 'the wicked'],
        ['ia mamao lava lea', 'far be that'],
        ['ia te oe.', 'from You'],
        ['O le na te faamasinoina', 'Shall not the Judge of'],
        ['le lalolagi uma,', 'all the earth'],
        ['e le faia ea e ia', 'do'],
        ['le faamasinoga tonu?', 'what is right?'],
    ],
    'Genesis|18|26': [
        ['Ona faapea mai lea', 'Then said'],
        ['o Ieova,', 'the LORD'],
        ['Afai ou te maua', 'If I find'],
        ['i Sotoma', 'in Sodom'],
        ['tagata amiotonu', 'righteous people'],
        ['e toalimagafulu', 'fifty'],
        ['i le aai,', 'in the city'],
        ['ona ou faasao ai lea', 'I will spare'],
        ['o le nuu uma', 'the whole place'],
        ['ona o i latou.', 'for their sakes'],
    ],
    'Genesis|18|27': [
        ['Ona tali atu lea', 'Then answered'],
        ['o Aperaamo,', 'Abraham'],
        ['ua faapea atu,', 'and said'],
        ['Faauta mai,', 'Behold'],
        ["o a'u nei", 'I who am'],
        ['o le efuefu', 'but dust'],
        ['ma le lefulefu,', 'and ashes'],
        ['ua ou faamalosi', 'have taken it upon myself'],
        ['e tautala atu', 'to speak'],
        ['i le Alii;', 'to the Lord'],
    ],
    'Genesis|18|28': [
        ['afai ua toe toalima', 'suppose five of the fifty'],
        ['e faaatoa ai', 'are lacking'],
        ['le toalimagafulu', 'will You destroy'],
        ['o tagata amiotonu,', 'the righteous persons'],
        ['e te faaumatia ea', 'for lack of'],
        ['le aai uma', 'the whole city'],
        ['ona o le toalima?', 'five?'],
        ['Ona tali mai lea a ia,', 'He said'],
        ['Afai ou te maua ai', 'If I find there'],
        ['se toafagafulu', 'forty-five'],
        ['ma le toalima', 'and five'],
        ['ou te le faaumatia lava.', 'I will not destroy it'],
    ],
    'Genesis|18|29': [
        ['Ona toe fai atu lea o ia', 'He spoke to Him again'],
        ['ia te ia,', 'and said'],
        ['ua faapea atu,', 'suppose'],
        ['Pe afai ua maua ai', 'there are'],
        ['le toafagafulu', 'forty'],
        ['e a ea ?', 'found there?'],
        ['Ona fetalai mai lea o ia,', 'He answered'],
        ['Afai ou te maua ai', 'I will not do it'],
        ['le toafagafulu', 'for the sake of'],
        ['ou te le faia lava', 'forty'],
        ['ona o i latou.', 'for their sakes'],
    ],
    'Genesis|18|30': [
        ['Ona fai atu lea a ia,', 'Then he said'],
        ["Aua ne'i toasa mai", 'Oh let not'],
        ['le Alii,', 'the Lord be angry'],
        ["a se'i ou toe fai atu,", 'and I will speak'],
        ['Afai ua maua ai', 'Suppose'],
        ['se toatolugafulu', 'thirty'],
        ['e a ea ?', 'are found there?'],
        ['Ona fetalai mai lea o ia,', 'He answered'],
        ['Afai ou te maua ai', 'I will not do it'],
        ['se toatolugafulu', 'if I find thirty'],
        ['ou te le faia lava.', 'there'],
    ],
    'Genesis|18|31': [
        ['Ona fai atu lea o ia,', 'Then he said'],
        ['Faauta mai,', 'Behold'],
        ['ua ou faamalosi', 'I have taken it upon myself'],
        ['e tautala atu', 'to speak'],
        ['i le Alii,', 'to the Lord'],
        ['Afai e maua ai', 'Suppose'],
        ['se toaluafulu', 'twenty'],
        ['e a ea ?', 'are found there?'],
        ['Ona fetalai mai lea o ia,', 'He answered'],
        ['Pe a o i ai', 'For the sake of'],
        ['le toaluafulu', 'twenty'],
        ['ou te le faaumatia lava', 'I will not destroy it'],
        ['ona o i latou.', 'for their sakes'],
    ],
    'Genesis|18|32': [
        ['Ona fai atu lea o ia', 'Then he said'],
        ["Aua ne'i toasa mai", 'Oh let not'],
        ['le Alii,', 'the Lord be angry'],
        ["a se'i ou fai atu", 'and I will speak'],
        ['le toe upu lea,', 'but this once'],
        ['Afai e maua ai', 'Suppose'],
        ['se toasefulu', 'ten'],
        ['e a ea ?', 'are found there?'],
        ['Ona tali mai lea a ia,', 'He answered'],
        ['Pe a o i ai', 'For the sake of'],
        ['le toasefulu', 'ten'],
        ['ou te le faaumatia lava', 'I will not destroy it'],
        ['ona o i latou.', 'for their sakes'],
    ],
    'Genesis|18|33': [
        ['Ona afio lea', 'Then went His way'],
        ['o Ieova', 'the LORD'],
        ['ina ua faaiu', 'when He had finished'],
        ['ana fetalaiga', 'speaking'],
        ['ia Aperaamo;', 'with Abraham'],
        ['ona toe foi lea', 'and returned'],
        ['e Aperaamo', 'Abraham'],
        ['i le mea e mau ai.', 'to his place'],
    ],

    # ==========================================================
    # 1 Samuel 1:2 – Elkanah's wives
    # ==========================================================
    '1 Samuel|1|2': [
        ['Sa nonofo ana av\u0101', 'He had'],
        ['e toalua,', 'two wives'],
        ['o Hana', 'Hannah'],
        ['le igoa o le tasi,', 'was the name of one'],
        ['o Penina', 'Peninnah'],
        ['le igoa o le tasi;', 'the name of the other'],
        ['sa ia Penina', 'Peninnah had'],
        ['le fanau,', 'children'],
        ['a e leai', 'but there was not'],
        ['se fanau', 'a child'],
        ['a Hana.', 'of Hannah'],
    ],

    # ==========================================================
    # Genesis 19 – Destruction of Sodom / Lot's escape
    # ==========================================================
    'Genesis|19|1': [
        ['Ua oo atu', 'Came'],
        ['agelu e toalua', 'two angels'],
        ['i Sotoma', 'to Sodom'],
        ['i le afiafi,', 'at evening'],
        ['a o nofo Lota', 'and Lot was sitting'],
        ['i le faitotoa o Sotoma;', 'in the gateway of Sodom'],
        ['ua ilo atu e Lota,', 'when Lot saw them'],
        ['ona tulai lea', 'he rose'],
        ['e faafetaiai', 'to meet'],
        ['ia te i laua;', 'them'],
        ['ona ifo toele lea o ia;', 'and bowed with his face to the ground'],
    ],
    'Genesis|19|2': [
        ['ua fai atu foi o ia,', 'he said'],
        ['Alii e,', 'My lords'],
        ['faauta mai,', 'behold'],
        ["se'i oulua afe mai", 'please turn in'],
        ['i le fale', 'to the house'],
        ['o la oulua auauna,', 'of your servant'],
        ['ma tofa ai,', 'and spend the night'],
        ["se'i mulumulu foi", 'and wash'],
        ['o oulua vae;', 'your feet'],
        ['i le ala', 'then you may rise early'],
        ['usu ai la oulua malaga.', 'and go on your way'],
        ['Ona tali mai lea o i laua,', 'They said'],
        ['Soia,', 'No'],
        ['au\u0101 ma te momoe pea', 'we will spend the night'],
        ['i fafo.', 'in the open square'],
    ],
    'Genesis|19|3': [
        ['Ona pulunaunau atu lava lea o ia', 'But he urged them strongly'],
        ['ia te i laua;', 'so'],
        ['ona la o ane lea', 'they turned in'],
        ['ma ia,', 'to him'],
        ['ma ulufale atu', 'and entered'],
        ['i lona fale;', 'his house'],
        ['ona saunia lea e ia', 'and he prepared'],
        ["o le mea e 'ai", 'a feast'],
        ['ma i laua,', 'for them'],
        ['ma ua tunu areto', 'and baked bread'],
        ['e le faafefetoina,', 'unleavened'],
        ['ona la aai ai lea.', 'and they ate'],
    ],
    'Genesis|19|4': [
        ['A o lei taooto i laua', 'Before they lay down'],
        ['ua siomia le fale', 'surrounded the house'],
        ['e tagata o lea aai,', 'the men of that city'],
        ['o tagata lava o Sotoma,', 'the men of Sodom'],
        ['o taulelea', 'both young'],
        ['atoa ma toeaina,', 'and old'],
        ['o le nuu uma lava', 'all the people'],
        ['mai itu uma;', 'from every quarter'],
    ],
    'Genesis|19|5': [
        ['ua latou valaau', 'They called'],
        ['ia Lota,', 'to Lot'],
        ['ua faapea atu,', 'and said'],
        ['O ifea ea tagata', 'Where are the men'],
        ['na o mai ia te oe', 'who came to you'],
        ['i le po nei?', 'tonight?'],
        ['Tuu mai ia i laua', 'Bring them out'],
        ['ia te i matou nei,', 'to us'],
        ['ina ia matou iloa i laua.', 'that we may know them'],
    ],
    'Genesis|19|6': [
        ['Ona ulufafo lea', 'Went out'],
        ['o Lota', 'Lot'],
        ['i le faitotoa', 'at the doorway'],
        ['ia te i latou,', 'to them'],
        ['ua pupuni le faitotoa', 'and shut the door'],
        ['i ona tua,', 'behind him'],
    ],
    'Genesis|19|7': [
        ['ua faapea atu,', 'and said'],
        ["O'u uso e,", 'My brothers'],
        ['aua lava', 'please do not'],
        ['tou te agaleaga.', 'act so wickedly'],
    ],
    'Genesis|19|8': [
        ['Faauta mai,', 'Look'],
        ["o ia te au o'u afafine", 'I have my daughters'],
        ['e toalua,', 'two'],
        ['e lei iloa tane', 'who have not known a man'],
        ['e i laua;', 'either of them'],
        ["se'i ou tuuina mai i laua", 'let me bring them out'],
        ['ia te outou,', 'to you'],
        ['e faitalia lava outou', 'do to them'],
        ['ia te i laua;', 'as you please'],
        ['a o na tagata,', 'but to these men'],
        ['aua tou te faia se mea', 'do nothing'],
        ['ia te i laua,', 'to them'],
        ['au\u0101 o le mea lava lea', 'for this is the reason'],
        ['na o mai ai', 'they came'],
        ["lalo ifo o lo'u fale.", 'under the shelter of my roof'],
    ],
    'Genesis|19|9': [
        ['Ona faapea mai lea', 'Then said'],
        ['o i latou,', 'they'],
        ['Alu ese ia;', 'Stand back!'],
        ['ua faapea ane foi i latou,', 'and they said'],
        ['Ua sau lena tagata', 'This fellow came'],
        ['e taase,', 'to sojourn'],
        ['a o le a fai o ia', 'and he would be'],
        ['ma faamasino;', 'a judge'],
        ['o lenei,', 'now'],
        ['o le a sili le leaga', 'we will deal worse'],
        ['matou te faia ia te oe', 'with you'],
        ['a e itiiti', 'than'],
        ['ia te i laua.', 'with them'],
        ['Ua latou matu\u0101 fetuleni mai lava', 'They pressed hard'],
        ['ia Lota,', 'against Lot'],
        ['ma ua faalatalata mai', 'and drew near'],
        ['e sofai', 'to break'],
        ['i le faitotoa.', 'the door'],
    ],
    'Genesis|19|10': [
        ['A ua fetagofi atu', 'But reached out'],
        ['ia tagata', 'the men'],
        ['ia Lota,', 'and pulled Lot'],
        ['ua au mai', 'into'],
        ['i le fale', 'the house'],
        ['o i ai i laua,', 'with them'],
        ['ona la pupuni lea', 'and shut'],
        ['o le faitotoa.', 'the door'],
    ],
    'Genesis|19|11': [
        ['A o tagata', 'And the men'],
        ['sa i le faitotoa', 'who were at the door'],
        ['o le fale,', 'of the house'],
        ['ua la faatauaso', 'they struck with blindness'],
        ['ia te i latou', 'them'],
        ['o tama', 'both small'],
        ['atoa ma e matutua;', 'and great'],
        ['ona lailoa ai lea', 'so that they wearied themselves'],
        ['o i latou', 'trying'],
        ['i saili le faitotoa.', 'to find the door'],
    ],
    'Genesis|19|12': [
        ['Ona fai atu lea', 'Then said'],
        ['o ia tagata', 'the men'],
        ['ia Lota,', 'to Lot'],
        ['O ai ea nisi', 'Have you anyone else'],
        ['o lou aiga', 'of your family'],
        ['o iinei?', 'here?'],
        ['O se tane a sou afafine,', 'Son-in-law, your sons'],
        ['po o sou atalii,', 'or your daughters'],
        ['po o sou afafine,', 'or anyone'],
        ['atoa ma i latou uma', 'you have'],
        ['e ua ia te oe', 'who belongs to you'],
        ['o i le aai,', 'in the city'],
        ['ina ave ese ia', 'bring them out'],
        ['i le mea nei;', 'of this place'],
    ],
    'Genesis|19|13': [
        ['au\u0101 o le a ma faaumatia', 'for we are about to destroy'],
        ['lenei mea,', 'this place'],
        ['au\u0101 ua tele', 'because great is'],
        ['lo latou alaga', 'the outcry against them'],
        ['i luma o Ieova;', 'before the LORD'],
        ['ua aauina mai foi', 'and has sent'],
        ['i maua', 'us'],
        ['e Ieova', 'the LORD'],
        ['e faaumatia ai.', 'to destroy it'],
    ],
    'Genesis|19|14': [
        ['Ona alu atu lea', 'So went out'],
        ['o Lota,', 'Lot'],
        ['ma tautala atu', 'and spoke'],
        ['i tane a ona afafine,', 'to his sons-in-law'],
        ['o e ua fai av\u0101', 'who had married'],
        ['i ona afafine,', 'his daughters'],
        ['ua faapea atu,', 'and said'],
        ['Ina tut\u016b ia,', 'Get up'],
        ['ina outou o ese', 'get out'],
        ['i lenei mea,', 'of this place'],
        ['au\u0101 o le a faaumatia', 'for the LORD will destroy'],
        ['e Ieova', 'the LORD'],
        ['lenei aai.', 'this city'],
        ['A o ia', 'But he'],
        ['ua pei se tagata faianaga', 'seemed to be jesting'],
        ['i le manatu', 'in the eyes'],
        ['o tane a ona afafine.', 'of his sons-in-law'],
    ],
    'Genesis|19|15': [
        ['Ua malama', 'When dawned'],
        ['e le taeao', 'the morning'],
        ['ona nanati lea', 'urged'],
        ['o agelu', 'the angels'],
        ['ia Lota,', 'Lot'],
        ['o loo faapea atu,', 'saying'],
        ['Ina tulai ia,', 'Arise'],
        ['ave lau av\u0101', 'take your wife'],
        ['ma ou afafine e toalua,', 'and your two daughters'],
        ['o loo iinei,', 'who are here'],
        ["ina ne'i malaia oe", 'lest you be swept away'],
        ['i le sala', 'in the punishment'],
        ['a le aai.', 'of the city'],
    ],
    'Genesis|19|16': [
        ['Ua faatuatuai o ia,', 'But he lingered'],
        ['ona fetagofi lea', 'so seized'],
        ['o ia tagata', 'the men'],
        ['i lona lima,', 'his hand'],
        ['ma le lima', 'and the hand'],
        ['o lana av\u0101,', 'of his wife'],
        ['ma lima', 'and the hands'],
        ['o ona afafine e toalua,', 'of his two daughters'],
        ['ina ua alofaina o ia', 'the LORD being merciful'],
        ['e Ieova;', 'to him'],
        ["ua la ta'ita'i atu foi", 'and they brought him out'],
        ['ia te ia,', 'him'],
        ['ma tuu atu ia te ia', 'and set him'],
        ['i tua o le aai.', 'outside the city'],
    ],
    'Genesis|19|17': [
        ["Ua ta'ita'iina i latou", 'When they had brought them outside'],
        ['e i laua i tua,', 'one said'],
        ['ona faapea atu lea o ia,', 'he said'],
        ['Ina sola ia', 'Escape'],
        ['e te ola ai,', 'for your life'],
        ['aua e te tepa i tua,', 'do not look back'],
        ['aua foi e te tu', 'nor stop'],
        ['i se mea', 'anywhere'],
        ['o le fanua laugatasi;', 'in the plain'],
        ['a ia sola lava', 'escape'],
        ['i le mauga', 'to the mountains'],
        ["ina ne'i malaia oe.", 'lest you be consumed'],
    ],
    'Genesis|19|18': [
        ['Ona tali mai lea', 'But said'],
        ['o Lota', 'Lot'],
        ['ia te i laua,', 'to them'],
        ['Le Alii e,', 'My lords'],
        ['aua lava;', 'please no'],
    ],
    'Genesis|19|19': [
        ['faauta mai,', 'Behold'],
        ['ua alofagia', 'has found favor'],
        ['lau auauna', 'your servant'],
        ['e oe,', 'in your sight'],
        ['ua e faateleina mai foi', 'and you have shown great'],
        ['lou alofa', 'kindness'],
        ['ua e alofa mai ai', 'in showing mercy'],
        ['ia te au,', 'to me'],
        ['i lou faaola mai', 'in saving'],
        ['ia te au;', 'my life'],
        ['ou te le lav\u0101 sola', 'but I cannot escape'],
        ['i le mauga,', 'to the mountains'],
        ["ne'i maua a'u", 'lest the disaster overtake me'],
        ['i le leaga,', 'and evil'],
        ['i le ou oti ai.', 'and I die'],
    ],
    'Genesis|19|20': [
        ['Faauta mai ea,', 'Behold'],
        ['o le aai le la', 'this city'],
        ['e lata mai,', 'is near'],
        ['ou te sola i ai,', 'to flee to'],
        ['o si aai itiiti foi lea;', 'and it is a little one'],
        ["se'i ou sola ane i ai,", 'please let me escape there'],
        ['e le o si aai itiiti ea?', 'is it not a little one?'],
        ["Ona ola ai lea o a'u.", 'and my life will be saved'],
    ],
    'Genesis|19|21': [
        ['Ona faapea atu lea o ia,', 'He said to him'],
        ['Faauta,', 'Behold'],
        ['ua ou talia foi', 'I have granted'],
        ['lou manao', 'your request'],
        ['i lena mea,', 'in this matter also'],
        ['ou te le faaumatia', 'I will not overthrow'],
        ['lena aai', 'the city'],
        ['ua e fai mai ai.', 'of which you have spoken'],
    ],
    'Genesis|19|22': [
        ['Ina e sola atu ia i ai,', 'Hurry escape there'],
        ['ia vave;', 'quickly'],
        ['au\u0101 ou te le mafaia', 'for I cannot'],
        ['ona fai o se mea', 'do anything'],
        ['seia e oo atu i ai.', 'until you arrive there'],
        ['E i ai', 'Therefore'],
        ['ona faaigoa ai', 'was called the name'],
        ['o lea aai', 'of that city'],
        ['o Soara.', 'Zoar'],
    ],
    'Genesis|19|23': [
        ['Ua alu ae le la', 'The sun had risen'],
        ['i luga o le lalolagi', 'upon the earth'],
        ['ina ua oo Lota', 'when Lot came'],
        ['i Soara.', 'to Zoar'],
    ],
    'Genesis|19|24': [
        ['Ona faatot\u014d faaua ifo lea', 'Then rained down'],
        ['e Ieova', 'the LORD'],
        ['i Sotoma', 'upon Sodom'],
        ['ma Komoro', 'and Gomorrah'],
        ['o le teio', 'brimstone'],
        ['ma le afi', 'and fire'],
        ['mai ia Ieova', 'from the LORD'],
        ['mai le lagi;', 'out of heaven'],
    ],
    'Genesis|19|25': [
        ['na ia faaumatia', 'And He destroyed'],
        ['o ia lava aai,', 'those cities'],
        ['ma le fanua laugatasi uma,', 'and all the plain'],
        ['ma i latou uma', 'and all the inhabitants'],
        ['sa mau i ia aai,', 'of the cities'],
        ['atoa ma mea', 'and what'],
        ['na tutupu', 'grew'],
        ['i le eleele.', 'on the ground'],
    ],
    'Genesis|19|26': [
        ['Ua tepa i tua', 'But looked back'],
        ['lana av\u0101', 'his wife'],
        ['sa mulimuli atu', 'who followed'],
        ['ia te ia,', 'behind him'],
        ['ona liua lea o ia', 'and she became'],
        ['ma tupua masima.', 'a pillar of salt'],
    ],
    'Genesis|19|27': [
        ['Ua ala usu', 'Early rose'],
        ['Aperaamo', 'Abraham'],
        ['i le taeao', 'in the morning'],
        ['i le mea sa tu ai o ia', 'to the place where he had stood'],
        ['i luma o Ieova;', 'before the LORD'],
    ],
    'Genesis|19|28': [
        ['ua ia vaai atu', 'and he looked down toward'],
        ['i Sotoma', 'Sodom'],
        ['ma Komoro,', 'and Gomorrah'],
        ['ma le fanua laugatasi uma,', 'and all the land of the plain'],
        ['ua ilo atu faauta foi,', 'and behold'],
        ['ua alu ae', 'went up'],
        ['le asu o le nuu', 'the smoke of the land'],
        ['e pei o le asu', 'like the smoke'],
        ['o se umu.', 'of a furnace'],
    ],
    'Genesis|19|29': [
        ['Ua faaumatia e le Atua', 'When God destroyed'],
        ['o aai', 'the cities'],
        ['o le fanua laugatasi,', 'of the plain'],
        ['ona manatua lea', 'then remembered'],
        ['e le Atua', 'God'],
        ['o Aperaamo,', 'Abraham'],
        ['ma ona auina o Lota', 'and sent Lot'],
        ['ai le malaia,', 'out of the overthrow'],
        ['ina o faaumatia e ia', 'when He overthrew'],
        ['o aai sa mau ai Lota.', 'the cities where Lot dwelt'],
    ],
    'Genesis|19|30': [
        ['Ua alu ae foi Lota', 'Then Lot went up'],
        ['nai Soara,', 'out of Zoar'],
        ['ona mau ai lea o ia', 'and dwelt'],
        ['i le mauga,', 'in the mountains'],
        ['faatasi ma ona afafine', 'with his two daughters'],
        ['e toalua;', 'for'],
        ['au\u0101 ua fefe o ia', 'he was afraid'],
        ['i mau i Soara;', 'to dwell in Zoar'],
        ['ua mau foi i le ana,', 'so he dwelt in a cave'],
        ['o ia', 'he'],
        ['ma ona afafine e toalua.', 'and his two daughters'],
    ],
    'Genesis|19|31': [
        ['Ona fai atu lea', 'Then said'],
        ['o l\u0113 matua', 'the firstborn'],
        ['i le itiiti,', 'to the younger'],
        ['Ua toeaina', 'Our father is old'],
        ['lo taua tam\u0101,', 'and there is'],
        ['e leai foi se tane', 'no man'],
        ['i le nuu', 'on earth'],
        ['e sau ia te i taua', 'to come in to us'],
        ['e pei o le masani', 'after the manner'],
        ['a le lalolagi uma.', 'of all the earth'],
    ],
    'Genesis|19|32': [
        ['Sau ia,', 'Come'],
        ["se'i ta faainua", 'let us make drink'],
        ['lo ta tama', 'our father'],
        ['i le uaina,', 'wine'],
        ['ona tatou taooto ai lea', 'and we will lie'],
        ['ma ia,', 'with him'],
        ['ina ia tutupu ai', 'that we may preserve'],
        ['ia te i taua', 'offspring'],
        ['ni fanau', 'through'],
        ['ai lo ta tam\u0101.', 'our father'],
    ],
    'Genesis|19|33': [
        ['Ua faainua e i laua', 'So they made drink'],
        ['lo la tam\u0101', 'their father'],
        ['i le uaina', 'wine'],
        ['i lea lava po;', 'that night'],
        ['ona alu ane ai lea', 'and went in'],
        ['o l\u0113 matua,', 'the firstborn'],
        ['ma la taooto', 'and lay'],
        ['ma lona tam\u0101;', 'with her father'],
        ['a ua le iloa e ia', 'he did not know'],
        ['ona taoto o ia,', 'when she lay down'],
        ['ma ona toe tulai.', 'or when she arose'],
    ],
    'Genesis|19|34': [
        ['Ua oo i le taeao,', 'The next day'],
        ['ona fai atu ai lea', 'said'],
        ['o l\u0113 matua', 'the firstborn'],
        ['i le itiiti,', 'to the younger'],
        ['Faauta mai,', 'Behold'],
        ['o anapo na ma taooto ai', 'last night I lay'],
        ['ma lo ta tam\u0101;', 'with my father'],
        ["se'i ta toe faainu ia te ia", 'let us make him drink'],
        ['i le uaina', 'wine'],
        ['i le po nanei,', 'tonight also'],
        ['i le e alu ane ai foi', 'then you go in'],
        ['lua te taooto ma ia,', 'and lie with him'],
        ['ina ia tutupu ai', 'that we may preserve'],
        ['ia te i taua', 'offspring'],
        ['ni fanau', 'through'],
        ['ai lo ta tam\u0101.', 'our father'],
    ],
    'Genesis|19|35': [
        ['Ua la toe faainua foi', 'So they made drink again'],
        ['lo la tam\u0101', 'their father'],
        ['i le uaina', 'wine'],
        ['i lea po,', 'that night'],
        ['ona tulai ane lea', 'and arose'],
        ['o le itiiti,', 'the younger'],
        ['ma la taooto ma ia;', 'and lay with him'],
        ['ua le iloa foi e ia', 'and he did not know'],
        ['ona taoto o ia,', 'when she lay down'],
        ['ma ona toe tulai.', 'or when she arose'],
    ],
    'Genesis|19|36': [
        ['Ona tot\u014d ai lea', 'Thus conceived'],
        ['o afafine e toalua', 'both daughters'],
        ['o Lota,', 'of Lot'],
        ['i lo la tam\u0101.', 'by their father'],
    ],
    'Genesis|19|37': [
        ['Ua fanau e l\u0113 matua', 'The firstborn bore'],
        ['o le tama tane,', 'a son'],
        ['ma ua faaigoa ia te ia,', 'and called his name'],
        ['o Moapi;', 'Moab'],
        ['o ia o le tupuga', 'he is the father'],
        ['o sa Moap\u012b;', 'of the Moabites'],
        ['ua oo mai', 'to'],
        ['i nei ona po.', 'this day'],
    ],
    'Genesis|19|38': [
        ['O le itiiti foi,', 'The younger also'],
        ['na fanau o ia', 'bore'],
        ['o le tama tane,', 'a son'],
        ['ma ua faaigoa ia te ia', 'and called his name'],
        ['o Pename;', 'Ben-Ammi'],
        ['o ia o le tupuga', 'he is the father'],
        ['o le fanauga a Amoni', 'of the Ammonites'],
        ['ua oo mai', 'to'],
        ['i nei ona po.', 'this day'],
    ],

    # ==========================================================
    # 1 Samuel 1:3 – Elkanah goes to Shiloh
    # ==========================================================
    '1 Samuel|1|3': [
        ['Na alu ae', 'went up'],
        ['lea tagata', 'that man'],
        ['nai lana aai', 'from his city'],
        ['i lea tausaga', 'year'],
        ['ma lea tausaga', 'by year'],
        ['e tapuai,', 'to worship'],
        ['ma fai taulaga', 'and make offerings'],
        ['i Sailo', 'in Shiloh'],
        ["ia Ieova o 'au;", 'to the LORD of Hosts'],
        ['sa i lea mea foi', 'and there were also'],
        ['atalii e toalua', 'the two sons'],
        ['o Eli,', 'of Eli'],
        ['o Hofeni', 'Hophni'],
        ['ma Fineaso,', 'and Phinehas'],
        ['o faitaulaga a Ieova.', 'priests of the LORD'],
    ],
    '1 Samuel|1|4': [
        ['A oo foi', 'and also came to pass'],
        ['i le aso', 'on the day'],
        ['e fai ai le taulaga', 'made the offering'],
        ['a Elekana,', 'by Elkanah'],
        ['ona avatu lea e ia o tufaaga', 'then he gave the portions'],
        ['ia Penina lana avā,', 'to Peninnah his wife'],
        ['ma ana tama tane uma,', 'and all her sons'],
        ['atoa ma ana tama teine.', 'together with her daughters'],
    ],
    '1 Samuel|1|5': [
        ['A ua avatu', 'but he gave'],
        ['ia Hana', 'to Hannah'],
        ['lea le tufaaga', 'that portion'],
        ['e tusa ma tufaaga e lua,', 'a double portion'],
        ['auā ua ia alofa', 'because he loved'],
        ['ia Hana;', 'Hannah'],
        ['a o le pule a Ieova', 'but the will of the LORD'],
        ['na le fanau ai o ia.', 'had not given her children'],
    ],
    '1 Samuel|1|6': [
        ['Ua faalili foi ia te ia', 'she also provoked her'],
        ['le na ita mai,', 'so that she was angry'],
        ['ua faaonoono foi ia te ia', 'and she vexed her also'],
        ['ina seia ita,', 'until she was angry'],
        ['auā na le fanau o ia', 'because she had no children'],
        ['o le pule a Ieova.', 'the decree of the LORD'],
    ],
    '1 Samuel|1|7': [
        ['Ua faapea ona fai e Elekana', 'and so Elkanah did'],
        ['i lea tausaga ma lea tausaga', 'year after year'],
        ['i le alu ae', 'when going up'],
        ['o le fafine', 'the woman'],
        ['i le fale o Ieova;', 'to the house of the LORD'],
        ['ua faapea ona faalili ia te ia,', 'so she provoked her'],
        ['ona tagi ai lea o ia,', 'then she wept'],
        ["ma ua le 'ai.", 'and would not eat'],
    ],
    '1 Samuel|1|8': [
        ['Ona fai atu lea o Elekana lana tane ia te ia,', 'then Elkanah her husband said to her'],
        ['Hana e,', 'Hannah'],
        ['se a le mea e te tagi ai?', 'why do you weep?'],
        ["Se a foi le mea e te le 'ai ai?", 'and why do you not eat?'],
        ['Se a foi le mea e tiga ai lou loto?', 'and why is your heart grieved?'],
        ['E le', 'is it not'],
        ['ua sili ea ona lelei', 'better'],
        ["o a'u ia te oe", 'I to you'],
        ['i tama tane', 'sons'],
        ['e toatinoagafulu?', 'ten?'],
    ],
    'Genesis|35|1': [
        ['Ua fetalai mai le Atua', 'God spoke'],
        ['ia Iakopo,', 'to Jacob'],
        ['Tulai ia,', 'rise up'],
        ['ina e alu ae', 'so that you go up'],
        ['i Peteli', 'to Bethel'],
        ['ma nofo ai;', 'and dwell there'],
        ['ma e fai ai le fata faitaulaga', 'and make there an altar'],
        ['i le Atua', 'to God'],
        ['na faaali ia te oe', 'who appeared to you'],
        ['ina ua e sola ese', 'when you fled'],
        ['ia Esau lou uso.', 'from Esau your brother'],
    ],
    'Genesis|35|2': [
        ['Ona fai ane lea o Iakopo', 'then Jacob said'],
        ['i lona aiga', 'to his household'],
        ['ma i latou uma', 'and to all'],
        ['sa ia te ia,', 'who were with him'],
        ['Tuu ese ia', 'put away'],
        ['o atua ese', 'the foreign gods'],
        ['o loo i ai ia te outou,', 'that are among you'],
        ['ma ia outou faamamā ia te outou,', 'and purify yourselves'],
        ['ma fesui i o outou ofu;', 'and change your garments'],
    ],
    'Genesis|35|3': [
        ['ina tatou tulai ia,', 'let us arise'],
        ['ma tatou o ae i Peteli,', 'and we go up to Bethel'],
        ['ou te fai ai', 'I will make there'],
        ['le fata faitaulaga', 'the altar'],
        ['i le Atua', 'to God'],
        ['na tali mai ia te au', 'who answered me'],
        ['i le aso', 'in the day'],
        ['na ou puapuaga ai,', 'when I was in distress'],
        ['sa ia te au foi', 'He was with me also'],
        ['i le ala', 'in the way'],
        ['na ou ui ai.', 'which I traveled'],
    ],
    'Exodus|2|2': [
        ['Ona to lea o le fafine,', 'and the woman conceived'],
        ['ua fanau mai le tama tane;', 'and bare a son'],
        ['ua ia iloa o ia', 'and when she saw him'],
        ['ua lalelei,', 'that he was goodly'],
        ['ona ia n\u0101 lava lea', 'she hid him'],
        ['ia te ia', 'unto him'],
        ['i masina e tolu.', 'three months'],
    ],
    'Exodus|2|3': [
        ['Ua le toe mafai ona n\u0101 ia te ia,', 'she could no longer hide him'],
        ['ona ia ave lea', 'then she took'],
        ['mo ia o le ato kome,', 'for him an ark of bulrushes'],
        ['na ia puluti ai', 'and daubed it'],
        ['i le pulu emeri,', 'with slime'],
        ['ma le pulu safeta;', 'and with pitch'],
        ['na ia tuu ai le tama,', 'and put the child therein'],
        ['ona tuuina ai lea', 'and laid it'],
        ['i le vao utuutu', 'in the reeds'],
        ['i le auvai', 'by the riverbank'],
        ['o le vaitafe.', 'of the river'],
    ],
    'Exodus|2|4': [
        ['A ua tu mamao atu', 'and stood afar off'],
        ['lona tuafafine', 'his sister'],
        ['ina ia iloa', 'to know'],
        ['pe iu ina faapefea o ia.', 'what would be done to him'],
    ],
    'Exodus|2|5': [
        ['Ona alu ifo lea o le afafine', 'then went down the daughter'],
        ['o Farao', 'of Pharaoh'],
        ['e taele i le vaitafe,', 'to bathe in the river'],
        ['o savavali ane foi lona galu teine', 'and her maidens walked along'],
        ['i le auvai o le vaitafe;', 'by the riverbank of the river'],
        ['ua iloa atu e ia le ato', 'she saw the ark'],
        ['o loo i le vao utuutu,', 'among the reeds'],
        ['ona au atu lea e ia', 'and she sent'],
        ['o lana auauna fafine', 'her maidservant'],
        ['na te aumaia.', 'to fetch it'],
    ],
    'Exodus|2|6': [
        ['Ua ia tatalaina,', 'she opened it'],
        ['ua iloa ai le tama,', 'she saw the child'],
        ['faauta foi,', 'and behold'],
        ['ua tagi le tama;', 'the child wept'],
        ['ona alofa lea i ai,', 'and she had compassion on him'],
        ['ua faapea ane,', 'and said'],
        ['O so le fanau a sa Eper\u016b lenei.', 'this is one of the Hebrew children'],
    ],
    'Exodus|2|7': [
        ['Ona fai mai lea', 'then said'],
        ['o lona tuafafine', 'his sister'],
        ['i le afafine o Farao,', "to Pharaoh's daughter"],
        ['Ou te alu ea', 'I will go'],
        ['e aami', 'and call'],
        ['se fafine failele', 'a nursing woman'],
        ['o sa Eper\u016b', 'of the Hebrews'],
        ['e sau ia te oe,', 'to come to you'],
        ['na te tausia le tama', 'to nurse the child'],
        ['ma oe?', 'for you?'],
    ],
    'Exodus|2|8': [
        ['Ua fai atu le afafine o Farao', "Pharaoh's daughter said"],
        ['ia te ia,', 'to her'],
        ['Ina alu ia;', 'Go'],
        ['i le ua alu ane le teine', 'and the maiden went'],
        ['ma valaau', 'and called'],
        ['i le tin\u0101', 'the mother'],
        ['o le tama.', 'of the child'],
    ],
    'Exodus|2|9': [
        ['Ona fai atu lea', 'then said'],
        ['o le afafine o Farao', 'the daughter of Pharaoh'],
        ['ia te ia,', 'to her'],
        ['Ia e ave lenei tama', 'take this child'],
        ['ma tausi i ai', 'and nurse him'],
        ["ma a'u,", 'for me'],
        ['ou te avatu ai foi ia te oe', 'I will give you wages also'],
        ['le totogi;', 'the wages'],
        ['ona ave lea o le tama', 'then she took the child'],
        ['e le fafine,', 'the woman'],
        ['ma na tausia.', 'and nursed him'],
    ],
    '1 Nephi|15|1': [
        ['Ma sa oo ina', 'and it came to pass'],
        ['ua mavae ona', 'after'],
        ['aveeseina atu', 'carried away'],
        ["o a'u,", 'I'],
        ['o Nifae,', 'Nephi'],
        ['i le agaga,', 'in the spirit'],
        ['ma ou vaai', 'and I beheld'],
        ['i nei mea uma,', 'all these things'],
        ['sa ou toe foi mai', 'I returned again'],
        ['i le faleie', 'to the tent'],
        ["o lo'u tamā.", 'of my father'],
    ],
    '1 Nephi|15|2': [
        ['Ma sa oo ina', 'and it came to pass'],
        ["ou vaai atu i o'u uso,", 'I looked toward my brothers'],
        ["ma sa latou fefinaua'i", 'and they were disputing'],
        ['o le tasi ma le isi,', 'one with another'],
        ['e uiga i mea', 'concerning things'],
        ['sa tautala atu ai', 'had spoken'],
        ["lo'u tamā ia te i latou.", 'my father unto them'],
    ],
    '1 Nephi|15|3': [
        ['Ona e moni', 'and verily'],
        ['e tele mea tetele', 'many great things'],
        ['sa tautala atu ai o ia', 'he spoke'],
        ['ia te i latou,', 'unto them'],
        ['ia sa faigata', 'which were hard'],
        ['ona malamalama i ai,', 'to understand'],
        ['vagana ai', 'save'],
        ['ua ole atu le tagata', 'one entreated'],
        ['i le Alii;', 'unto the Lord'],
        ['ma ona o lo latou maaa', 'and because of their hardness'],
        ['i o latou loto,', 'in their hearts'],
        ["o lea na latou lē", 'therefore they did not'],
        ['vaai atu ai i le Alii', 'look unto the Lord'],
        ['e pei ona sa tatau ai', 'as they ought'],
        ['ia te i latou.', 'unto them'],
    ],
    '1 Nephi|15|4': [
        ['Ma o lenei', 'and now'],
        ["o a'u, o Nifae,", 'I Nephi'],
        ["sa 'ou faanoanoa", 'did mourn'],
        ['ona o le maaa', 'because of the hardness'],
        ['o o latou loto,', 'of their hearts'],
        ['o lenei foi,', 'and also'],
        ['ona o mea sa ou vaaia,', 'because of things I had seen'],
        ["ma lo'u iloa", 'and my knowing'],
        ["o le a lē maalofia", 'would not be fulfilled'],
        ['lo latou faataunuuina', 'their accomplishment'],
        ['ona o le amioleaga tele', 'because of the great wickedness'],
        ['o le fanauga a tagata.', 'of the children of men'],
    ],
    '1 Nephi|15|5': [
        ['Ma sa oo ina', 'and it came to pass'],
        ["lofituina a'u", 'I was overcome'],
        ["ona o o'u puapuaga,", 'because of my afflictions'],
        ['ona sa ou manatu', 'for I thought'],
        ["ua sili atu o'u puapuaga", 'my afflictions were greatest'],
        ['i luga atu o tagata uma,', 'above all men'],
        ['ona o le faafanoga', 'because of the destruction'],
        ["o o'u tagata,", 'of my people'],
        ['ona sa ou vaai', 'for I beheld'],
        ["i lo latou pa'ū.", 'their fall'],
    ],
    '1 Nephi|15|6': [
        ['Ma sa oo ina', 'and it came to pass'],
        ['ua mavae ona', 'after'],
        ['ou maua o le malosi', 'I received strength'],
        ['sa ou fai atu', 'I said'],
        ["i o'u uso,", 'unto my brothers'],
        ['ou te fia iloa', 'desiring to know'],
        ['mai ia te i latou', 'from them'],
        ['le pogai', 'the cause'],
        ['o a latou finauga.', 'of their disputations'],
    ],
    '1 Nephi|15|7': [
        ['Ma sa latou fai mai:', 'and they said'],
        ['Faauta,', 'behold'],
        ["ua lē mafai", 'we cannot'],
        ['ona matou malamalama', 'understand'],
        ['i upu na fai mai ai', 'the words spoken by'],
        ['lo tatou tamā', 'our father'],
        ['e faatatau', 'likening'],
        ['i lala moni', 'to true branches'],
        ['o le laau olive,', 'of the olive tree'],
        ['ma e uiga foi', 'and also concerning'],
        ['i Nuuese.', 'the Gentiles'],
    ],
    '1 Nephi|15|8': [
        ['Ma sa ou fai atu', 'and I said'],
        ['ia te i latou:', 'unto them'],
        ['Ua outou ole atu ea', 'have ye inquired'],
        ['i le Alii?', 'of the Lord?'],
    ],
    '1 Nephi|15|9': [
        ['Ma sa latou fai mai', 'and they said'],
        ["ia te a'u:", 'unto me'],
        ['Matou te lei ole atu;', 'we have not inquired'],
        ["ona e lē faailoa maia", 'for it has not been revealed'],
        ['e le Alii', 'by the Lord'],
        ['ia te i matou', 'unto us'],
        ['se mea faapena.', 'such a thing'],
    ],
    '1 Nephi|15|10': [
        ['Faauta,', 'behold'],
        ['sa ou fai atu ia te i latou:', 'I said unto them'],
        ['E faapefea', 'how is it'],
        ["ona outou lē tausia", 'that ye do not keep'],
        ['o poloaiga a le Alii?', 'the commandments of the Lord?'],
        ['E faapefea', 'how is it'],
        ['ona outou fano,', 'that ye will perish'],
        ['ona o le maaa', 'because of the hardness'],
        ['o o outou loto?', 'of your hearts?'],
    ],
    '1 Nephi|15|11': [
        ["Tou te lē manatua ea", 'do ye not remember'],
        ['mea na fetalai mai ai', 'the things spoken by'],
        ["le Alii?\u2014Afai", 'the Lord? If'],
        ["tou te lē faamaaa", 'ye will not harden'],
        ['o outou loto,', 'your hearts'],
        ["ma ole mai ia te a'u", 'and ask of me'],
        ['i le faatuatua,', 'in faith'],
        ['ma le talitonu', 'believing'],
        ['o le a outou maua,', 'that ye shall receive'],
        ['faatasi ma le filiga', 'with diligence'],
        ['i le tausiga', 'in keeping'],
        ["o a'u poloaiga,", 'my commandments'],
        ['e moni', 'surely'],
        ['o le a faailoa mai', 'shall be made known'],
        ['nei mea ia te outou.', 'these things unto you'],
    ],
    '1 Nephi|15|12': [
        ['Faauta,', 'behold'],
        ['ou te fai atu ia te outou,', 'I say unto you'],
        ['sa faatusaina le aiga o Isaraelu', 'the house of Israel was compared'],
        ['i se laau olive,', 'unto an olive tree'],
        ['e le Agaga o le Alii', 'by the Spirit of the Lord'],
        ['lea sa i lo tatou tamā;', 'which was in our father'],
        ['ma faauta', 'and behold'],
        ["pe lei fa'iesea ea i tatou", 'have we not been broken off'],
        ['mai le aiga o Isaraelu,', 'from the house of Israel'],
        ["ma pe lē o i tatou ea", 'and are we not'],
        ['o se lala', 'a branch'],
        ['o le aiga o Isaraelu?', 'of the house of Israel?'],
    ],
    '1 Nephi|15|13': [
        ['Ma o lenei,', 'and now'],
        ['o le uiga o le mea', 'the meaning of the thing'],
        ['na fai mai ai lo tatou tamā', 'which our father spake'],
        ['e uiga i le suluina', 'concerning the grafting'],
        ['o lala moni', 'of true branches'],
        ['e ala i le atoatoaga o Nuuese,', 'by the fulness of the Gentiles'],
        ['o le,', 'is'],
        ['i aso e gata ai,', 'in the latter days'],
        ['pe a mavae ona faaitiitia', 'after being scattered'],
        ['a tatou fanau', 'our seed'],
        ["i le lē talitonu,", 'in unbelief'],
        ['ioe,', 'yea'],
        ['mo le va o tausaga e tele,', 'for the space of many years'],
        ['ma tupulaga e tele', 'and many generations'],
        ['pe a mavae ona faaali mai', 'after the manifestation'],
        ['o le Mesia i le tino', 'of the Messiah in the flesh'],
        ['i le fanauga a tagata,', 'unto the children of men'],
        ['ona oo atu ai lea', 'then shall come'],
        ['o le atoatoaga o le talalelei', 'the fulness of the gospel'],
        ['a le Mesia', 'of the Messiah'],
        ['i Nuuese,', 'to the Gentiles'],
        ['ma mai Nuuese', 'and from the Gentiles'],
        ['i le toe vaega', 'unto the remnant'],
        ["o a tatou fanau\u2014", 'of our seed'],
    ],
    '1 Nephi|15|14': [
        ['Ma i lena aso', 'and in that day'],
        ['o le a iloa ai', 'shall be known'],
        ['e le toe vaega', 'by the remnant'],
        ['o a tatou fanau ,', 'of our seed'],
        ['o i latou o lo le aiga o Isaraelu,', 'that they are of the house of Israel'],
        ['ma o i latou o tagata', 'and that they are the people'],
        ['o le feagaiga a le Alii;', 'of the covenant of the Lord'],
        ['ma ona latou iloa ai lea', 'and then shall they know'],
        ['ma o mai i le malamalama', 'and come to the knowledge'],
        ["e uiga i o latou muātua'ā,", 'concerning their forefathers'],
        ['ma i le malamalama foi', 'and also to the knowledge'],
        ['o le talalelei', 'of the gospel'],
        ['a lo latou Togiola,', 'of their Redeemer'],
        ['lea sa tauaao atu e ia', 'which was ministered by him'],
        ['i o latou tamā;', 'unto their fathers'],
        ['o le mea lea,', 'wherefore'],
        ['o le a latou malamalama ai', 'they shall come to the knowledge'],
        ['i lo latou Togiola', 'of their Redeemer'],
        ["ma matāutu tonu lava", 'and the very points'],
        ['o Lana mataupu faavae,', 'of his doctrine'],
        ['ina ia mafai', 'that it may be'],
        ['ona latou iloa le ala', 'that they know the way'],
        ['e o mai ai ia te ia', 'to come unto him'],
        ['ma faaolaina.', 'and be saved'],
    ],
    '1 Nephi|15|15': [
        ['Ma ona oo lea,', 'and it shall come to pass'],
        ['i lena lava aso,', 'in that very day'],
        ["pe o le a latou lē olioli ea", 'shall they not rejoice'],
        ['ma avatu le viiga', 'and give praise'],
        ['i lo latou Atua tumau-faavavau,', 'unto their everlasting God'],
        ['o lo latou papa', 'their rock'],
        ['ma lo latou olataga?', 'and their salvation?'],
        ['Ioe,', 'yea'],
        ['i lena aso,', 'in that day'],
        ["pe o le a latou lē maua ea", 'will they not receive'],
        ['le malosi ma le tausiga', 'strength and nourishment'],
        ['mai le vine moni?', 'from the true vine?'],
        ['Ioe,', 'yea'],
        ["pe o le a latou lē o mai ea", 'will they not come'],
        ['i le lotoa moni a le Atua?', 'unto the true fold of God?'],
    ],
    '1 Nephi|15|16': [
        ['Faauta,', 'behold'],
        ['ou te fai atu ia te outou,', 'I say unto you'],
        ['Ioe;', 'yea'],
        ['o le a toe manatua i latou', 'they shall be remembered again'],
        ['i totonu o le aiga o Isaraelu;', 'in the house of Israel'],
        ['o le a sulu i latou i totonu,', 'they shall be grafted in'],
        ['ona o i latou', 'inasmuch as they'],
        ['o se lala moni', 'are a natural branch'],
        ['o le laau olive,', 'of the olive tree'],
        ['i totonu o le laau olive moni.', 'into the true olive tree'],
    ],
    '1 Nephi|15|17': [
        ['Ma o le uiga lenei', 'and this is the meaning'],
        ["o le tala a lo tatou tamā;", 'of the words of our father'],
        ['ma o le uiga o lana tala', 'and the meaning of his words'],
        ["o le a lē oo mai", 'shall not come to pass'],
        ['seia mavae ona faataapeapeina', 'until after they are scattered'],
        ['o i latou e Nuuese;', 'among the Gentiles'],
        ['ma o le uiga o lana tala', 'and the meaning of his words'],
        ['o le a oo mai', 'shall come to pass'],
        ['e ala mai i Nuuese,', 'by way of the Gentiles'],
        ['ina ia mafai', 'that it may'],
        ['ona faaalia e le Alii', 'be shown by the Lord'],
        ['lona mana i Nuuese,', 'his power unto the Gentiles'],
        ['o le pogai tonu', 'for the very cause'],
        ['ona o le a teena o ia', 'that he shall be rejected'],
        ['e tagata Iutaia,', 'by the Jews'],
        ['po o le aiga o Isaraelu.', 'or the house of Israel'],
    ],
    '1 Nephi|15|18': [
        ['O le mea lea,', 'wherefore'],
        ["e lē nao a tatou fanau", 'not only our seed'],
        ['sa tautala i ai', 'did speak concerning'],
        ['lo tatou tamā,', 'our father'],
        ['ae o le aiga uma foi', 'but also the whole house'],
        ['o Isaraelu,', 'of Israel'],
        ['e faasino i le feagaiga lea', 'pointing to the covenant which'],
        ['o le a faataunuuina', 'should be fulfilled'],
        ['i aso e gata ai;', 'in the latter days'],
        ['o le feagaiga lea', 'which covenant'],
        ['na faia e le Alii', 'the Lord made'],
        ["i lo tatou tamā o Aperaamo,", 'unto our father Abraham'],
        ['fai mai:', 'saying'],
        ['O lau fanau', 'in thy seed'],
        ['o le a manuia ai', 'shall be blessed'],
        ['aiga uma o le lalolagi.', 'all the kindreds of the earth'],
    ],
}


def annotate_verse(verse_key, samoan_text, english_text=""):
    """
    Generate phrase annotations for a verse.
    Returns list of [samoan_phrase, english_gloss] pairs.
    First splits at punctuation, then applies grammatical chunking
    to produce ~2-4 word interlinear groups.
    """
    if not samoan_text:
        return []

    # Use manual chunk overrides if available (bypasses chunker entirely)
    if verse_key in MANUAL_CHUNK_OVERRIDES:
        return [list(pair) for pair in MANUAL_CHUNK_OVERRIDES[verse_key]]

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
                # Preserve capitalization for proper names
                words_in_chunk = chunk.split()
                if any(w[0].isupper() for w in words_in_chunk if w):
                    gloss = chunk
                else:
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
        'Genesis|3|1': {
            'Ua sili': 'Now was more crafty',
            'le atamai': 'the cunning',
            'o le gata': 'the serpent',
            'i manu uma': 'than any beast',
            'o le vao': 'of the field',
            'na faia': 'which had made',
            'e Ieova': 'the LORD',
            'le Atua.': 'God',
            'Ua fai mai o ia': 'He said',
            'i le fafine,': 'to the woman',
            'E moni ea,': 'Has God indeed said',
            'na fetalai mai': 'said',
            'le Atua,': 'God',
            'lua te': 'You shall not',
            'le aai': 'eat',
            'i laau uma': 'of every tree',
            'o le faatoaga?': 'of the garden?',
        },
        'Genesis|3|2': {
            'Ona tali atu ai lea': 'And said',
            'o le fafine': 'the woman',
            'i le gata,': 'to the serpent',
            'O fua o laau': 'The fruit of the trees',
            'o le faatoaga': 'of the garden',
            'ma te aai ai lava;': 'we may eat',
        },
        'Genesis|3|3': {
            'a o le fua': 'but of the fruit',
            'o le laau o': 'of the tree',
            'i totonu': 'in the midst',
            'o le faatoaga': 'of the garden',
            'na fetalai mai ai': 'God has said',
            'le Atua,': 'God',
            'Aua ma te aai ai,': 'You shall not eat it',
            'aua foi': 'nor shall',
            'ma te papai atu': 'you touch',
            'i ai,': 'it',
            "ne'i ma oti.": 'lest you die',
        },
        'Genesis|3|4': {
            'Ona fai mai lea': 'Then said',
            'o le gata': 'the serpent',
            'i le fafine,': 'to the woman',
            'Lua te': 'You will',
            'le oti lava;': 'not surely die',
        },
        # Genesis|3|5 handled by MANUAL_CHUNK_OVERRIDES (custom chunk boundaries)
        'Genesis|3|6': {
            'Ona vaai atu lea': 'So when saw',
            'o le fafine': 'the woman',
            'i le laau': 'the tree',
            'e lelei lava': 'that it was good',
            "pe a 'ai,": 'for food',
            'ma ua matagofie': 'and pleasant',
            'mai,': 'to the eyes',
            'o le laau foi': 'and a tree',
            'e aoga': 'desirable',
            'e maua ai': 'to make one',
            'le poto,': 'wise',
            'ona tago ai lea o ia': 'she took',
            'i lona fua,': 'of its fruit',
            "ma 'ai ai;": 'and ate',
            'na ia avatu foi': 'She also gave',
            'i lana tane faatasi': 'to her husband',
            'ma ia,': 'with her',
            "na 'ai ai foi o ia.": 'and he ate',
        },
        'Genesis|3|7': {
            'Ona pupula ai lea o laua': 'Then were opened their',
            'mata,': 'eyes',
            'ua la iloa': 'and they knew',
            'ua le lavalavā': 'and naked',
            'i laua;': 'they',
            'ona la fatu ai lea': 'and they sewed',
            'o lau': 'leaves',
            'o le mati': 'of the fig tree',
            'ua fai': 'and made',
            'mo laua titi.': 'themselves coverings',
        },
        # Genesis|3|8 handled by MANUAL_CHUNK_OVERRIDES (custom chunk boundaries)
        # Genesis|3|9 handled by MANUAL_CHUNK_OVERRIDES
        'Genesis|3|10': {
            'Na ou faalogo atu': 'I heard',
            'i lou siufofoga': 'Your voice',
            'i le faatoaga,': 'in the garden',
            'ona ou fefe ai lea,': 'and I was afraid',
            'auā ua ou': 'because I was',
            'le lavalavā;': 'naked',
            'ona ou lafi lea.': 'and I hid myself',
        },
        # Genesis|3|11 handled by MANUAL_CHUNK_OVERRIDES
        'Genesis|3|12': {
            'Ona faapea mai lea o Atamu,': 'Then the man said',
            'O le fafine': 'The woman',
            'na e aumai ia te au,': 'whom You gave to be with me',
            'ua na aumai ia te au': 'she gave me',
            'le fua': 'of the fruit',
            'o le laau,': 'of the tree',
            "ona ou 'ai ai lea.": 'and I ate',
        },
        'Genesis|3|13': {
            'Ona fetalai atu lea o Ieova': 'And the LORD said',
            'le Atua': 'God',
            'i le fafine,': 'to the woman',
            'Se a lena mea': 'What is this',
            'ua e faia?': 'you have done?',
            'Ona tali mai lea': 'The woman said',
            'o le fafine,': 'the woman',
            'Na faasese mai': 'deceived',
            'le gata ia te au,': 'The serpent me',
            "ona ou 'ai ai lea.": 'and I ate',
            'Ona fetalai atu lea o Ieova': 'So the LORD said',
            'i le gata,': 'to the serpent',
        },
        'Genesis|3|14': {
            'E sili lou malaia': 'Cursed are you',
            'i manu vaefa fanua uma,': 'more than all livestock',
            'ma manu vaefa uma lava': 'and more than every beast',
            'o le vao,': 'of the field',
            'ina ua': 'Because you have',
            'e faia lena mea;': 'done this',
            'e te sosolo': 'you shall go',
            'i lou manava,': 'on your belly',
            'o le efuefu': 'and dust',
            "e te 'ai ai": 'you shall eat',
            'i aso uma': 'all the days',
            'o lou ola;': 'of your life',
        },
        'Genesis|3|15': {
            'ou te faatupuina': 'And I will put',
            'le feitagai ia te oulua': 'enmity between you',
            'ma le fafine,': 'and the woman',
            'o lau fanau foi': 'and between your seed',
            'ma lana fanau;': 'and her Seed',
            "na te tu'imomomoina lou ulu,": 'He shall bruise your head',
            'a o oe': 'and you',
            "e te tu'imomomoina lona mulivae.": 'shall bruise His heel',
        },
        'Genesis|3|16': {
            'Ua fetalai atu o ia': 'And He said',
            'i le fafine,': 'to the woman',
            'Ou te matuā faateleina': 'I will greatly multiply',
            'le tiga': 'your sorrow',
            "o lou ma'i to;": 'and your conception',
            'e te fanau': 'you shall bring forth',
            'mai tama': 'children',
            'ma le tiga;': 'in pain',
            'e uai atu lou manao': 'Your desire shall be',
            'i lau tane,': 'for your husband',
            'e pule foi o ia': 'and he shall rule',
            'ia te oe.': 'over you',
        },
        # Genesis|3|17 handled by MANUAL_CHUNK_OVERRIDES
        # Genesis|3|18 handled by MANUAL_CHUNK_OVERRIDES
        # Genesis|3|19 handled by MANUAL_CHUNK_OVERRIDES
        # Genesis|3|20 handled by MANUAL_CHUNK_OVERRIDES
        # Genesis|3|21 handled by MANUAL_CHUNK_OVERRIDES
        # Genesis|3|22 handled by MANUAL_CHUNK_OVERRIDES
        # Genesis|3|23 handled by MANUAL_CHUNK_OVERRIDES
        # Genesis|3|24 handled by MANUAL_CHUNK_OVERRIDES
        # Genesis|4|1-26 handled by MANUAL_CHUNK_OVERRIDES
        # Genesis|5|1-32 handled by MANUAL_CHUNK_OVERRIDES
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
