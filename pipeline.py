import logging
import json
import sys
import spacy
import webvtt
from collections import Counter
from math import log
from pathlib import Path

logging.basicConfig(level=logging.INFO)
nlp = spacy.load("es_core_news_sm")


def lemmatize(word: str) -> str:
    return nlp(word)[0].lemma_


def extract_caption_text(path: Path) -> list[str]:
    """Extract all caption lines from a vtt file."""
    return [line.text for line in webvtt.read(path)]


def clean_caption(caption: str) -> str:
    """Clean up peculiarilities in vtt files."""
    caption = caption.replace('\n', ' ').replace('-', '')
    caption = caption.lower().strip()
    return caption


def process_captions(model, captions: list[str]) -> tuple[list, set]:
    """Tokenize the captions, discard all punctuations, and find the vocabulary."""
    tokens = []
    vocab = set()

    for caption in captions:
        caption = model(clean_caption(caption))
        caption_tokens = [
            token.text for token in caption if not token.is_punct]
        tokens.append(caption_tokens)
        vocab.update(caption_tokens)

    return tokens, vocab


def initialize_json(vocab: set) -> dict[str, dict]:
    """Initialize the dict of dicts where all information is stored."""
    token_info = {}
    for word in vocab:
        token_info[word] = {
            'word': word,
            'lemma': lemmatize(word),
            'tf': 0,
            'df': 0
        }
    return token_info


def get_tfidf_count(tokens: list[str], word_info: dict[str, dict]):
    """tf is defined as the number of occurrence in the entire corpus (script).

    df is defined as the number of caption lines in which the token occurs.
    """
    for caption in tokens:
        counter = Counter(caption)
        for token in counter:
            word_info[token]['df'] += 1
            word_info[token]['tf'] += counter[token]

    return None


def calculate_tfidf(
    num_docs: int,
    tf: int,
    df: int,
    smooth_idf: bool = True,
    sublinear_tf: bool = True
) -> float:
    if sublinear_tf:
        tf = 1 + log(tf)
    if smooth_idf:
        idf = log((num_docs + 1)/(df + 1)) + 1
    else:
        idf = log(num_docs / df) + 1

    return tf * idf


def min_max_scale(min: float, max: float, val: float) -> float:
    return (val - min) / (max - min)


def get_norm_tfidf(word_info: dict[str, dict], num_docs: int):
    """Use min max scale to normalize to (0, 1) range."""
    tfidfs = []

    for key in word_info:
        tf, df = word_info[key]['tf'], word_info[key]['df']
        tfidf = calculate_tfidf(num_docs, tf, df)
        word_info[key]['tfidf'] = tfidf
        tfidfs.append(tfidf)

    min_tfidf, max_tfidf = min(tfidfs), max(tfidfs)

    for key in word_info:
        word_info[key]['tfidf'] = min_max_scale(
            min_tfidf, max_tfidf, word_info[key]["tfidf"])

    return None


def get_word_importance_score(word_info: dict[str, dict]):
    with open('vocab_list/all_processed_vocab.json', 'r') as f:
        vocab_list = json.load(f)

    a1_a2 = set([i['word'] for i in vocab_list[:2500]])
    b1_b2 = set([i['word'] for i in vocab_list[2500:3750]])
    c1_c2 = set([i['word'] for i in vocab_list[3750:]])

    for word in word_info:
        lemma = word_info[word]['lemma']
        if lemma in a1_a2:
            word_info[word]['word_importance'] = 1
        elif lemma in b1_b2:
            word_info[word]['word_importance'] = 0.75
        elif lemma in c1_c2:
            word_info[word]['word_importance'] = 0.5
        else:
            word_info[word]['word_importance'] = 0.25

    return None


def pipeline(path: Path) -> dict[str, dict]:
    captions = extract_caption_text(path)
    num_docs = len(captions)
    tokens, vocab = process_captions(nlp, captions)

    word_info = initialize_json(vocab)
    get_word_importance_score(word_info)
    get_tfidf_count(tokens, word_info)
    get_norm_tfidf(word_info, num_docs)

    output_path = path.parents[0] / (path.stem + '.json')
    with open(output_path, 'w+') as output:
        output.write(json.dumps(word_info, indent=4))

    return word_info


def main():
    """Write word info JSON file based on the given vtt file to the same directory."""
    assert len(
        sys.argv) == 2, "Enter the path to the vtt file as a command line argument."
    assert sys.argv[1].endswith('.vtt')

    vtt_path = Path(sys.argv[1])
    pipeline(vtt_path)

    return None


if __name__ == '__main__':
    main()
