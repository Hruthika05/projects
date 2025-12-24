import re
import nltk
from nltk.corpus import stopwords
from nltk.stem import WordNetLemmatizer

nltk.download('stopwords')
nltk.download('wordnet')

stop_words = set(stopwords.words('english'))
lemmatizer = WordNetLemmatizer()

def clean_text(text):
    text = text.lower()
    text = re.sub(r'[^a-z\s]', '', text)  # keep only letters
    words = text.split()
    # Keep important question words
    important_words = {"how", "what", "when", "which", "why"}
    words = [w for w in words if (w not in stop_words or w in important_words)]
    return " ".join(words)
