import re
import string
from Sastrawi.Stemmer.StemmerFactory import StemmerFactory

STOPWORDS_ID = {
    "yang", "dan", "di", "ke", "dari", "untuk", "dengan", "atau", "itu", "ini", "karena",
    "pada", "jadi", "saya", "aku", "kami", "kita", "kamu", "dia", "mereka", "nya", "ga", "gak",
    "nggak", "tidak", "aja", "udah", "sudah", "lebih", "juga"
}

factory = StemmerFactory()
stemmer = factory.create_stemmer()


def clean_text(text: str) -> str:
    text = text.lower()
    text = re.sub(r"http\S+|www\S+", " ", text)
    text = re.sub(r"@\w+", " ", text)
    text = re.sub(r"#\w+", " ", text)
    text = re.sub(r"\d+", " ", text)
    text = text.translate(str.maketrans("", "", string.punctuation))
    text = re.sub(r"\s+", " ", text).strip()
    return text


def normalize_and_stem(text: str) -> str:
    cleaned = clean_text(text)
    tokens = [t for t in cleaned.split() if t not in STOPWORDS_ID and len(t) > 2]
    stemmed = [stemmer.stem(t) for t in tokens]
    return " ".join(stemmed)
