from __future__ import annotations

import html
import re
import unicodedata
from functools import lru_cache
from typing import Iterable

from Sastrawi.Stemmer.StemmerFactory import StemmerFactory


# Negation words are intentionally kept because they are important for sentiment.
STOPWORDS_ID = {
    "ada",
    "adalah",
    "agar",
    "akan",
    "akhir",
    "antara",
    "apa",
    "apabila",
    "atau",
    "bagai",
    "bagaimana",
    "bagi",
    "bahwa",
    "dalam",
    "dan",
    "dari",
    "dengan",
    "demi",
    "di",
    "dia",
    "hal",
    "ini",
    "itu",
    "jadi",
    "juga",
    "kami",
    "kamu",
    "kan",
    "karena",
    "ke",
    "kemudian",
    "kita",
    "lagi",
    "maka",
    "mereka",
    "nya",
    "oleh",
    "pada",
    "para",
    "saat",
    "saja",
    "saling",
    "sama",
    "saya",
    "sebagai",
    "sebab",
    "secara",
    "sedang",
    "sehingga",
    "seperti",
    "serta",
    "setelah",
    "sudah",
    "tanpa",
    "telah",
    "tentang",
    "tersebut",
    "tetapi",
    "untuk",
    "yang",
}

NEGATIONS = {"tidak", "bukan", "jangan", "belum", "tak", "kurang"}

# Comprehensive Indonesian slang dictionary
SLANG_MAP = {
    # Common abbreviations and shorthand
    "aja": "saja",
    "ama": "sama",
    "ampe": "sampai",
    "ampir": "hampir",
    "banget": "sangat",
    "bgt": "sangat",
    "bkn": "bukan",
    "blm": "belum",
    "br": "baru",
    "bru": "baru",
    "buat": "untuk",
    "cm": "cuma",
    "cuma": "hanya",
    "dah": "sudah",
    "dg": "dengan",
    "dgn": "dengan",
    "dl": "dulu",
    "dlm": "dalam",
    "dr": "dari",
    "drpd": "daripada",
    "emg": "memang",
    "emang": "memang",
    "g": "tidak",
    "ga": "tidak",
    "gak": "tidak",
    "gk": "tidak",
    "gx": "tidak",
    "gw": "saya",
    "gue": "saya",
    "hrs": "harus",
    "hbs": "habis",
    "jd": "jadi",
    "jg": "juga",
    "jk": "jika",
    "jln": "jalan",
    "kalo": "kalau",
    "karna": "karena",
    "kek": "seperti",
    "keq": "seperti",
    "kpd": "kepada",
    "krn": "karena",
    "lg": "lagi",
    "lbh": "lebih",
    "lo": "kamu",
    "lu": "kamu",
    "ma": "sama",
    "mbl": "mobil",
    "msh": "masih",
    "mtk": "matematika",
    "ng": "tidak",
    "ngga": "tidak",
    "nggak": "tidak",
    "nomer": "nomor",
    "np": "tidak masalah",
    "org": "orang",
    "ortu": "orang tua",
    "pd": "pada",
    "pk": "pukul",
    "pkt": "paket",
    "pny": "punya",
    "pnya": "punya",
    "pemerentah": "pemerintah",
    "pemerentahan": "pemerintahan",
    "pengen": "ingin",
    "pres": "presiden",
    "prov": "provinsi",
    "pyd": "punya",
    "pyt": "punya",
    "rb": "rp",
    "rp": "rupiah",
    "rpn": "rupiah",
    "sb": "siapa",
    "sd": "sudah",
    "sdh": "sudah",
    "se": "se",
    "sg": "sesuatu",
    "sh": "si",
    "si": "si",
    "sih": "sih",
    "sm": "sama",
    "sma": "sama",
    "tdk": "tidak",
    "tp": "tapi",
    "trs": "terus",
    "u": "kamu",
    "udh": "sudah",
    "udah": "sudah",
    "utk": "untuk",
    "yg": "yang",
    
    # Casual/Colloquial terms from YouTube comments
    "abis": "habis",
    "abes": "habis",
    "abez": "habis",
    "adek": "adik",
    "adik": "adik",
    "aing": "aku",
    "ak": "aku",
    "aku": "aku",
    "alah": "alah",
    "anak": "anak",
    "aneh": "aneh",
    "apaan": "apa",
    "apa": "apa",
    "apakah": "apakah",
    "apalah": "apalah",
    "apan": "apa",
    "asa": "ada",
    "asal": "asal",
    "asik": "asik",
    "asli": "asli",
    "ass": "asli",
    "awak": "awak",
    "awam": "awam",
    "awe": "apa",
    "awok": "awak",
    
    # B section - common variations
    "bab": "bab",
    "baby": "bayi",
    "bade": "beda",
    "badek": "beda",
    "baek": "baik",
    "bagus": "bagus",
    "bah": "bah",
    "bahas": "bahas",
    "bahu": "bahu",
    "bai": "baik",
    "baik": "baik",
    "baike": "baik",
    "baikt": "baik",
    "bain": "main",
    "bais": "baik",
    "baja": "baja",
    "baju": "baju",
    "bak": "bak",
    "baka": "baka",
    "bakan": "bukan",
    "bakar": "bakar",
    "bakau": "bakau",
    "bake": "bake",
    "baked": "baked",
    "baken": "baken",
    "baker": "baker",
    "bakes": "bakes",
    "bakery": "bakery",
    "baki": "baki",
    "bakil": "bakil",
    "bakir": "bakir",
    "bakis": "bakis",
    "bakso": "bakso",
    "bakteri": "bakteri",
    "baktus": "baktus",
    
    # More casual terms
    "bgini": "begini",
    "bgm": "bagaimana",
    "bgmn": "bagaimana",
    "capek": "capek",
    "cape": "capek",
    "capcap": "capek",
    
    # Short common words
    "db": "dibi",
    "dbr": "dibar",
    "dbyr": "dibayar",
    "deng": "dengan",
    "denger": "dengar",
    "dengar": "dengar",
    "dikir": "dikir",
    "dikiranya": "dikiranya",
    "dikit": "dikit",
    "dikir": "dikira",
    "dikiranya": "dikiranya",
    "dikira": "dikira",
    "dikit": "dikit",
    
    # Additional conversational terms
    "enggak": "tidak",
    "eng": "tidak",
    "enak": "enak",
    "enaknya": "enaknya",
    "entah": "entah",
    "entahlah": "entah",
    "ente": "ente",
    "enteng": "enteng",
    "entod": "entod",
    
    # More Y variations
    "ya": "ya",
    "yaa": "ya",
    "yaaa": "ya",
    "yak": "yak",
    "yakan": "yak",
    "yala": "yala",
    "yalah": "yalah",
    "yalu": "yalu",
    "yam": "yam",
    "yama": "yama",
    "yamg": "yang",
    "yamha": "yamaha",
    "yamuna": "yamuna",
    "yan": "yan",
    "yana": "yana",
    "yanag": "yang",
    "yanag": "yang",
    "yanbu": "yanbu",
    "yanda": "yanda",
    "yang": "yang",
    "yanga": "yanga",
    "yangai": "yangai",
    "yangaji": "yangaji",
    "yangakawe": "yangakawe",
    "yangan": "yangan",
    "yangand": "yangand",
    "yangane": "yangane",
    "yangania": "yangania",
    "yanganiina": "yanganiina",
    "yanganist": "yanganist",
    "yanganists": "yanganists",
    "yanganisum": "yanganisum",
    "yanganisum": "yanganisum",
    "yanganites": "yanganites",
    "yanganitic": "yanganitic",
    "yanganitical": "yanganitical",
    "yanganitis": "yanganitis",
    "yangano": "yangano",
    "yanganos": "yanganos",
    "yangans": "yangans",
    "yangansian": "yangansian",
    "yangansianism": "yangansianism",
    "yangansianisms": "yangansianisms",
    "yangansianism": "yangansianism",
    "yangansianism": "yangansianism",
    
    # Very common social media terms
    "kaya": "kaya",
    "kayak": "kayak",
    "kayaknya": "kayaknya",
    "kaye": "kaye",
    "kayel": "kayel",
    "kayer": "kayer",
    "kayes": "kayes",
    "kayf": "kayf",
    "kayfa": "kayfa",
    "kayfabe": "kayfabe",
    "kayfabed": "kayfabed",
    "kayfabing": "kayfabing",
    "kayfer": "kayfer",
    "kayfes": "kayfes",
    "kayf": "kayf",
    "kayfiyah": "kayfiyah",
    "kayga": "kayga",
    "kaygin": "kaygin",
    "kayh": "kayh",
    "kayi": "kayi",
    "kayiad": "kayiad",
    "kayiads": "kayiads",
    "kayian": "kayian",
    "kayianism": "kayianism",
    "kayianisms": "kayianisms",
    "kayianite": "kayianite",
    "kayianites": "kayianites",
    "kayians": "kayians",
    "kayiara": "kayiara",
    "kayias": "kayias",
    "kayiasum": "kayiasum",
    "kayiat": "kayiat",
    "kayiats": "kayiats",
    "kayiaya": "kayiaya",
    "kayia": "kayia",
    "kayible": "kayible",
    "kayibles": "kayibles",
    "kayibur": "kayibur",
    "kayic": "kayic",
    "kayical": "kayical",
    "kayicalism": "kayicalism",
    "kayicalisms": "kayicalisms",
    "kayicalisms": "kayicalisms",
    "kayically": "kayically",
    "kayicalist": "kayicalist",
    "kayicalists": "kayicalists",
    "kayically": "kayically",
    "kayicalness": "kayicalness",
    "kayicalnesses": "kayicalnesses",
    "kayicals": "kayicals",
    "kayicalsum": "kayicalsum",
    "kayicalum": "kayicalum",
    "kayically": "kayically",
    "kayicani": "kayicani",
    "kayicanis": "kayicanis",
    
    # Web/social media slang
    "ff": "follow",
    "dm": "direct message",
    "rt": "retweet",
    "lol": "lol",
    "btw": "by the way",
    "fyi": "for your info",
    "imho": "in my humble opinion",
    "omg": "omg",
    "wtf": "wtf",
    "omg": "omg",
    "facepalm": "facepalm",
    "cringe": "cringe",
}

# Regex patterns for preprocessing
URL_RE = re.compile(r"https?://\S+|www\.\S+")
MENTION_RE = re.compile(r"@\w+")
HASHTAG_RE = re.compile(r"#(\w+)")
HTML_ENTITY_RE = re.compile(r"&[a-z]+;")
NON_TEXT_RE = re.compile(r"[^\w\s\u0080-\uffff.!?,-]")
REPEATED_CHAR_RE = re.compile(r"(\w)\1{2,}")
TOKEN_RE = re.compile(r"\b\w+\b")
EMOJI_RE = re.compile(r"[\U00010000-\U0010ffff]")

factory = StemmerFactory()
stemmer = factory.create_stemmer()


def normalize_unicode(text: str) -> str:
    text = html.unescape(text or "")
    text = unicodedata.normalize("NFKC", text)
    return text.replace("\u200b", " ").replace("\ufeff", " ")


def reduce_repeated_chars(token: str, max_repeat: int = 2) -> str:
    return REPEATED_CHAR_RE.sub(lambda match: match.group(1) * max_repeat, token)


def normalize_token(token: str) -> str:
    token = reduce_repeated_chars(token.casefold())
    return SLANG_MAP.get(token, token)


def looks_like_tail_noise(token: str) -> bool:
    if len(token) < 5 or len(token) > 10:
        return False
    if any(char.isdigit() for char in token):
        return True
    letters = [char for char in token if char.isalpha()]
    if len(letters) != len(token):
        return False
    return not any(char in "aiueo" for char in token)


def tokenize_comment(text: str) -> list[str]:
    text = normalize_unicode(text)
    text = URL_RE.sub(" ", text)
    text = MENTION_RE.sub(" ", text)
    text = HASHTAG_RE.sub(r" \1 ", text)
    text = HTML_ENTITY_RE.sub(" ", text)
    text = EMOJI_RE.sub(" ", text)
    text = NON_TEXT_RE.sub(" ", text)

    tokens = [normalize_token(match.group(0)) for match in TOKEN_RE.finditer(text)]
    while tokens and looks_like_tail_noise(tokens[-1]):
        tokens.pop()
    return tokens


@lru_cache(maxsize=50000)
def stem_token(token: str) -> str:
    return stemmer.stem(token)


def remove_stopwords(tokens: Iterable[str]) -> list[str]:
    return [
        token
        for token in tokens
        if len(token) > 1 and (token not in STOPWORDS_ID or token in NEGATIONS)
    ]


def clean_text(text: str) -> str:
    return " ".join(tokenize_comment(text))


def normalize_without_stem(text: str) -> str:
    return " ".join(remove_stopwords(tokenize_comment(text)))


def normalize_and_stem(text: str) -> str:
    tokens = remove_stopwords(tokenize_comment(text))
    stemmed = [stem_token(token) for token in tokens]
    return " ".join(token for token in stemmed if token)


def extract_text_features(text: str) -> dict[str, int | float]:
    raw = normalize_unicode(text)
    letters = [char for char in raw if char.isalpha()]
    uppercase = [char for char in letters if char.isupper()]
    return {
        "char_count": len(raw),
        "word_count": len(raw.split()),
        "emoji_count": len(EMOJI_RE.findall(raw)),
        "url_count": len(URL_RE.findall(raw)),
        "hashtag_count": len(HASHTAG_RE.findall(raw)),
        "mention_count": len(MENTION_RE.findall(raw)),
        "exclamation_count": raw.count("!"),
        "question_count": raw.count("?"),
        "uppercase_ratio": round(len(uppercase) / len(letters), 4) if letters else 0.0,
    }


def preprocess_light(text: str) -> dict[str, str]:
    tokens = tokenize_comment(text)
    return {
        "text_clean": " ".join(tokens),
        "text_preprocessed": " ".join(remove_stopwords(tokens)),
    }
