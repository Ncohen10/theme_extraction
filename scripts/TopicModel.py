import spacy
import os
from gensim.models import Phrases
from gensim.models.word2vec import LineSentence
from spacy.lang.en.stop_words import STOP_WORDS
from gensim.corpora import Dictionary, MmCorpus
from gensim.models.ldamulticore import LdaMulticore


class TopicModel:


    def __init__(self, data_directory):
        self.nlp = spacy.load('en_core_web_sm')
        self.unigram_sentences_filepath = data_directory + "unigram_sentences_all.txt"
        self.bigram_model_filepath = data_directory + "bigram_model_all"
        self.bigram_sentences_filepath = data_directory + "bigram_sentences_all.txt"
        self.trigram_model_filepath = data_directory + "trigram_model_all"
        self.trigram_sentences_filepath = data_directory + "trigram_sentences_all.txt"
        self.trigram_articles_filepath = data_directory + "trigram_transformed_articles_all.txt"

        self.trigram_dictionary_filepath = data_directory + "trigram_dict_all.dict"
        self.trigram_bow_filepath = data_directory + "trigram_bow_corpus_all.mm"

    @staticmethod
    def punct_space(token):
        """
        helper function to eliminate tokens
        that are pure punctuation or whitespace
        """
        return token.is_punct or token.is_space

    def line_article(self, article_dir, article_to_parse=3):
        for article_num in range(article_to_parse):
            cur_article = article_dir + "/text" + str(article_num)
            with open(cur_article, encoding="utf-8") as f:
                next(f)
                for line in f:
                    yield line.replace('\\n', '\n')

    def sentence_generator(self, article_dir, articles_to_parse=3):
        """
        Generator function that yields each sentence in all text files.
        """
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
        """
        writes all sentences into one file.
        So it can be used by spaCy's LineSentence function.
        Then returns a LineSentence iterator of sentence unigrams.
        """

        with open(self.unigram_sentences_filepath, 'w', encoding="utf-8") as f:
            for sentence in self.sentence_generator("../data/article_texts"):
                f.write(sentence + '\n')

    def get_trigrams(self):
        """
        Builds unigram, bigram, and trigram models respectively.
        Writes the text of each model to a seperate file.

        """
        unigram_sentences = LineSentence(self.unigram_sentences_filepath)
        bigram_model = Phrases(unigram_sentences)
        bigram_model.save(self.bigram_model_filepath)
        bigram_model = Phrases.load(self.bigram_model_filepath)
        with open(self.bigram_sentences_filepath, 'w', encoding="utf-8") as f:
            for unigram_sentence in unigram_sentences:
                bigram_sent = " ".join(bigram_model[unigram_sentence])  # a bit confused by this.
                f.write(bigram_sent)
        bigram_sentences = LineSentence(self.bigram_sentences_filepath)
        trigram_model = Phrases(bigram_sentences)
        trigram_model.save(self.trigram_model_filepath)
        trigram_model = Phrases.load(self.trigram_model_filepath)
        with open(self.trigram_sentences_filepath, 'w', encoding="utf-8") as f:
            for bigram_sentence in bigram_sentences:
                trigram_sentence = " ".join(trigram_model[bigram_sentence])
                f.write(trigram_sentence + '\n')
        trigram_sentences = LineSentence(self.trigram_sentences_filepath)
        with open(self.trigram_articles_filepath, 'w', encoding="utf-8") as f:
            for parsed_article in self.line_article("../data/article_texts"):
                unigram_article = [token.lemma_ for token in self.nlp(parsed_article)
                                   if not self.punct_space(token)]
                bigram_article = bigram_model[unigram_article]
                trigram_article = trigram_model[bigram_article]
                trigram_article = [term for term in trigram_article
                                    if term not in STOP_WORDS]
                trigram_article = " ".join(trigram_article)
                f.write(trigram_article + '\n')

    def create_LDA_model(self):
        trigram_articles = LineSentence(self.trigram_articles_filepath)
        trigram_dictionary = Dictionary(trigram_articles)
        trigram_dictionary.filter_extremes(no_below=10, no_above=0.4)
        trigram_dictionary.compactify()
        trigram_dictionary.save(self.trigram_dictionary_filepath)
        trigram_dictionary = Dictionary.load(self.trigram_dictionary_filepath)
        print(trigram_dictionary)

"""
I think this writes 3 seperate files, each of which contain all text from 10k files.
"""
if __name__ == '__main__':
    model = TopicModel("../data/spacy_gensim_data/")
    model.write_all_article_sentences()
    model.get_trigrams()
    model.create_LDA_model()
    c = 0
