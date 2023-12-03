import spacy
import json

nlp = spacy.load("es_core_news_sm")


def process_line(line: str) -> tuple:
    elements = line.split()
    return elements[1], int(elements[2].replace(',', '')), float(elements[3])


def lemmatize(word: str) -> str:
    return nlp(word)[0].lemma_


def make_json(idx: int, line: str) -> dict:
    word, freq_abs, freq_norm = process_line(line)
    lemma = lemmatize(word)

    return {
        "rank": idx + 1,
        "word": word,
        "lemma": lemma,
        "freq_abs": freq_abs,
        "freq_norm": freq_norm
    }


def main():
    with open('CREA_original.txt', 'r') as f:
        lines = f.readlines()[1:]

    processed_lines = [make_json(idx, line)
                       for idx, line in enumerate(lines)]

    a1_a2_vocab = processed_lines[:2500]
    b1_b2_vocab = processed_lines[2500:3750]
    c1_c2_vocab = processed_lines[3750:5000]

    with open("all_processed_vocab.json", 'w') as all_vocab:
        all_vocab.write(json.dumps(processed_lines, indent=4))

    with open("a1_a2_vocab.json", 'w') as a1_a2:
        a1_a2.write(json.dumps(a1_a2_vocab, indent=4))

    with open("b1_b2_vocab.json", 'w') as b1_b2:
        b1_b2.write(json.dumps(b1_b2_vocab, indent=4))

    with open("c1_c2_vocab.json", 'w') as c1_c2:
        c1_c2.write(json.dumps(c1_c2_vocab, indent=4))


if __name__ == "__main__":
    main()
