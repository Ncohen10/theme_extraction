import pandas as pd
import spacy
from gensim.models import Phrases
from gensim.models.word2vec import LineSentence
from gensim.corpora import Dictionary

class WordModel:


    def __init__(self):
        self.nlp = spacy.load('en_core_web_sm')
        self.unigram_sentences_filepath = "../data/spacy_gensim_data/unigram_sentences_all.txt"

    @staticmethod
    def punct_space(token):
        """
        helper function to eliminate tokens
        that are pure punctuation or whitespace
        """
        return token.is_punct or token.is_space

    def sentence_generator(self, article_dir, articles_to_parse=3):
        for article_num in range(articles_to_parse):
            cur_article = article_dir + "/text" + str(article_num)
            with open(cur_article, encoding="utf-8") as f:
                next(f)  # skip first line.
                data = f.read()
                corpus = self.nlp(data)
                for sent in corpus.sents:
                    # filter out punctuation and whitespace from sentences.
                    cur_sentence = " ".join([token.lemma_ for token in sent
                                             if not self.punct_space(token)])
                    # TODO - Deal with the -PRON-
                    yield cur_sentence

    def write_all_article_sentences(self):
        with open(self.unigram_sentences_filepath, 'w', encoding="utf-8") as f:
            for sentence in self.sentence_generator("../data/article_texts"):
                f.write(sentence + '\n')


if __name__ == '__main__':
    natural = WordModel()
    natural.write_all_article_sentences()
