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

SLANG_MAP = {
    "aja": "saja",
    "ama": "sama",
    "banget": "sangat",
    "bgt": "sangat",
    "bkn": "bukan",
    "blm": "belum",
    "br": "baru",
    "buat": "untuk",
    "cm": "cuma",
    "cuma": "hanya",
    "dah": "sudah",
    "dg": "dengan",
    "dgn": "dengan",
    "dl": "dulu",
    "dlm": "dalam",
    "dr": "dari",
    "emg": "memang",
    "ga": "tidak",
    "gak": "tidak",
    "gk": "tidak",
    "gw": "saya",
    "gue": "saya",
    "jd": "jadi",
    "jg": "juga",
    "kalo": "kalau",
    "karna": "karena",
    "kek": "seperti",
    "kpd": "kepada",
    "krn": "karena",
    "lo": "kamu",
    "lu": "kamu",
    "ma": "sama",
    "msh": "masih",
    "ngga": "tidak",
    "nggak": "tidak",
    "org": "orang",
    "pd": "pada",
    "pemerentah": "pemerintah",
    "pemerentahan": "pemerintahan",
    "pengen": "ingin",
    "sm": "sama",
    "sma": "sama",
    "tdk": "tidak",
    "tp": "tapi",
    "trs": "terus",
    "udh": "sudah",
    "utk": "untuk",
    "yg": "yang",
}

URL_RE = re.compile(r"https?://\S+|www\.\S+", re.IGNORECASE)
MENTION_RE = re.compile(r"@\w+")
HASHTAG_RE = re.compile(r"#(\w+)")
HTML_ENTITY_RE = re.compile(r"&[a-z]+;|&#\d+;", re.IGNORECASE)
NON_TEXT_RE = re.compile(r"[^0-9a-zA-Z_'\-\s]")
REPEATED_CHAR_RE = re.compile(r"([a-zA-Z])\1{2,}")
TOKEN_RE = re.compile(r"[a-zA-Z][a-zA-Z0-9_'-]*")
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
