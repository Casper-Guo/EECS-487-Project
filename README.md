# Maestro: Topic-Aware, Intelligent Flashcards

## Authors
- Casper Guo
- Nick Lovell

## Directory Structure
```
.
├── Project Poster.pdf
├── README.md
├── experiment.ipynb
├── pipeline.py
├── requirements.txt
├── result_visualizations
│   ├── all_performance.png
│   ├── all_performance_stopwords.png
│   ├── lda_performance.png
│   ├── lda_tuning_large.png
│   ├── lda_tuning_small.png
│   ├── lsa_explained_variance.png
│   ├── lsa_performance.png
│   └── tfidf_performance.png
├── setup.sh
├── test-corpus
│   ├── 8.Mile
│   ├── Spider-Man
│   ├── The.Social.Dilemma
│   ├── The.Social.Network
│   ├── The.Tinder.Swindler
│   └── Whiplash
├── vocab_list
│   ├── CREA_top_10000.txt
│   ├── CREA_top_5000.txt
│   ├── a1_a2_vocab.json
│   ├── all_processed_vocab.json
│   ├── b1_b2_vocab.json
│   ├── c1_c2_vocab.json
│   └── process_vocab.py
└── webapp
    ├── client
    ├── docker-compose.yml
    └── server

12 directories, 22 files
```

## Files of Note

### `experiment.ipynb`
Code for generating all benchmarks and visualizations used in the `Experiments` section.

### `pipeline.py`
Implementation of the end-to-end pipeline that ingests vtt files via the cmmandlind and outputs JSON files with all relevant per-token scores.

### `setup.sh`
Simple shell script to install all dependencies and download pre-trained SpaCy pipeline.

### `webapp/`
- `client/`: Front-end implementation.
- `server/`: Back-end implementation, including JSON ingestion, database, SRS, and sentence ranking logic.

## Setup
Use `setup.sh` to install all necessary dependencies.

## Acknowledgement

The open-source [webvtt-py](https://github.com/glut23/webvtt-py) package.