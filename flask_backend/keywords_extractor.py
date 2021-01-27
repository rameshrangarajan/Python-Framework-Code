# -*- coding: utf-8 -*-
"""
Created on Wed Oct 23 15:58:26 2019

@author: godbole_s
"""

from __future__ import division
import re
import itertools
import unicodedata
from collections import Counter
from operator import itemgetter
import pandas as pd
import spacy
from nltk.corpus import stopwords
from nltk.tokenize import sent_tokenize
from nltk.stem import WordNetLemmatizer
import objectpath
from collections import OrderedDict
from elasticsearch_connector import elasticsearch_connector
import utils
from logger import log
from redis_connector import redis_connector
from datetime import datetime
import json
# set logger
logger = log.getLogger()

# read config
config = utils.config_parser()

# read all the attributes from config file
spacy_nlp_model_name = config.get('keywordsextractor', 'spacy_nlp_model_name')
nlp = spacy.load(spacy_nlp_model_name)

selected_ner_tags = config.get('keywordsextractor', 'selected_ner_tags').split(',')
ner_set = set(selected_ner_tags)
selected_noun_tags = config.get('keywordsextractor', 'selected_noun_tags').split(',')
noun_set = set(selected_noun_tags)
#
es_connect = elasticsearch_connector.get_instance()
wordnet_lemmatizer = WordNetLemmatizer()


class keywords_extractor():
    term_pos_df = pd.DataFrame()
    term_ner_df = pd.DataFrame()
    dataset = pd.DataFrame()
    stop_words = stopwords.words('english')
    term_frequency_dict = {}# will finally have all the keywords (from history and documents) with their cummulative count

    def __init__(self):
        # Append the stopwords from the file to the nltk stopwords list
        self.get_stopwords_from_file()

    def get_data_from_ES(self):
        corpus_index_name = config.get('elasticsearch', 'corpus_index_name')
        json_data = es_connect.get_data(corpus_index_name)
        all_docs = json_data.get('hits').get('hits')
        if all_docs:
            text_array = []
            for hits in all_docs:
                hits_source = hits.get('_source')
                if hits_source.get('slides'):
                    for slides in hits_source['slides']:
                        tree = objectpath.Tree(slides)
                        text = [x for x in tree.execute("$..text")]
                        text_array.append(text)
        return text_array

    def filt(self, word):
        return unicodedata.normalize('NFKD', word).encode('ascii', errors='ignore').decode('ascii')

    def decode(self, msg):
        msg = self.filt(msg.decode('utf-8'))
        return msg

    def is_roman(self, word):
        roman_characters = re.compile(u'^M{0,3}(CM|CD|D?C{0,3})(XC|XL|L?X{0,3})(IX|IV|V?I{0,3})$')
        if roman_characters.search(word.upper()):
            return True
        return False

    def get_stopwords_from_file(self):

        stopwords_file_path = config.get('keywordsextractor', 'stopwords_file_path')

        with open(stopwords_file_path) as f:
            additional_stopwords = f.readlines()
        additional_stopwords = [x.strip() for x in additional_stopwords]

        self.stop_words.extend(additional_stopwords)
        self.stop_words = list(set(self.stop_words))


    def clean_noun_chunk(self, noun_chunk):
        """
        1. Bring word to root form
        2. Remove stop words
        3. Remove Roman words
        4. Remove words <= 2 characters

        :param msg: a noun chunk of type <class 'spacy.tokens.span.Span'>
        :return: cleaned noun chunk (a string)
        """
        alpha_characters = re.compile(u'[^A-Za-z]+')
        noun_chunk = str(noun_chunk)
        noun_chunk = alpha_characters.sub(' ', noun_chunk)
        noun_chunk = [lemmatized_word for lemmatized_word in
                      [wordnet_lemmatizer.lemmatize(word, 'n') for word in noun_chunk.split()]
                      if (lemmatized_word not in self.stop_words)
                      and (not self.is_roman(lemmatized_word))
                      and (len(lemmatized_word) > 2)
                      ]

        noun_chunk = ' '.join(list(filter(bool, noun_chunk)))
        return noun_chunk

    def clean_list_of_noun_chunks(self, list_of_noun_chunk):
        """
        performs cleaning of all the noun chunks
        :param list_of_msg: list of noun chunks in a slide i.e. list of all the noun chunks in all the sentences of a slide
        :return: a list after cleaning_text
        """
        clean_list = []
        for x in list_of_noun_chunk:
            clean_noun_chunk = self.clean_noun_chunk(x)
            if len(clean_noun_chunk) > 0:
                clean_list.append(clean_noun_chunk)
        return clean_list

    def update_dataset_with_sentence_list(self):
        self.dataset['sentences'] = self.dataset['TEXT'].apply(lambda x: [sent_tokenize(y) for y in x])
        self.dataset['sentences'] = self.dataset['sentences'].apply(lambda x: list(itertools.chain.from_iterable(x)))

    def get_nlp_sentences(self, sentences):
        sentences_nlp_results = []
        for size in range(0, len(sentences), 20000):
            sentences_batch = '. '.join(sentences[size:size + 20000])
            start = datetime.now()
            merged_sentence = nlp(sentences_batch)
            sentences_nlp_results.append(merged_sentence)
            logger.info("NLP call time  = %s"%(datetime.now() - start).total_seconds())
        return sentences_nlp_results

    def get_noun_chunks(self, sentences_nlp_results):
        start = datetime.now()
        noun_chunks = [list(this_nlp_result.noun_chunks) for this_nlp_result in sentences_nlp_results]
        noun_chunks = list(itertools.chain.from_iterable(noun_chunks))

        noun_chunks_cleaned = self.clean_list_of_noun_chunks(noun_chunks)
        noun_chunks_cleaned = self.keep_capital(noun_chunks_cleaned)
        logger.info("Noun_chunks_cleaned = %s "%(datetime.now() - start).total_seconds())
        return noun_chunks_cleaned

    def get_pos_and_ner_tags(self, sentences_nlp_results, term_phrase_frequency):
        """
        :param sentences_nlp_results: list of nlp_results for batched sentences
        :param tf: dataframe with term_phrase and its count
        :return: pos & ner labels for all the occurrences of term_phrase in the dataset
        """
        _list_pos_label = []
        _list_ner_label = []

        term_list = self.get_terms_set(term_phrase_frequency)
        start = datetime.now()

        for this_sentence_nlp_result in sentences_nlp_results:
            for t in this_sentence_nlp_result:
                lemma_text = wordnet_lemmatizer.lemmatize(t.text.lower(), 'n')
                if (lemma_text not in self.stop_words) and (not self.is_roman(lemma_text)) and (len(lemma_text) > 2) and (
                        t.text.lower() in term_list):
                    _list_pos_label.append([lemma_text, t.pos_])

            for t in this_sentence_nlp_result.ents:
                lemma_text_ = wordnet_lemmatizer.lemmatize(t.text.lower(), 'n')
                if t.text.lower() in term_list:
                    _list_ner_label.append([lemma_text_, t.label_])
        logger.info("POS and NER tagging for all docs = %s"%(datetime.now() - start).total_seconds())
        return _list_pos_label, _list_ner_label

    def get_important_term_phrase_frequency(self, noun_chunks_cleaned):
        """
        1. Get all the filtered_chunks i.e noun chunks which has a word count in [2,3] and if the chunk is a single word, the len(word) > 2
        2. N-gram based filtering
        3. Term Frequency Filtering

        :return: tf [dataframe with term_phrase and its count]
        """
        start = datetime.now()
        min_df = config.get('keywordsextractor', 'min_df')

        filtered_cleaned_chunks = list(
            filter(lambda x: len(x.split()) in [2, 3] or (len(x.split()) == 1 and len(x) > 2), noun_chunks_cleaned))
        tf = Counter(filtered_cleaned_chunks)
        tf = pd.DataFrame({'term_phrase': list(tf.keys()), 'count': list(tf.values())})
        tf = tf[tf['count'] >= int(min_df)]
        tf = tf.sort_values(by="count", ascending=False)
        logger.info("Getting tf dataframe = %s "%(datetime.now() - start).total_seconds())

        return tf

    def keep_capital(self, phrase):
        phrase_resp = []
        for string in phrase:
            word_resp = []
            for word in string.split():
                r = re.findall('([A-Z])', word)
                if word.isupper():
                    word_resp.append(word)
                elif len(r) > 1:
                    word_resp.append(word)
                else:
                    word_resp.append(word.lower())
            word_resp = ' '.join(word_resp)
            phrase_resp.append(word_resp)
        return phrase_resp

    def get_terms_set(self, term_phrase_frequency):
        results = set()
        term_phrase_frequency['term_phrase'].str.split().apply(results.update)
        return list(results)

    def get_pos_ner_df(self, _list_pos_label, _list_ner_label):
        """
        check in the dataset... in which form has the filtered term appeared
        :param tf: dataframe with termphrase and its count
        :param _dataset: initial dataset with each row having text on a slide

        :return: dataframe with terms and their POS tagging, dataframe with terms and its NER tagging

        """
        term_df_pos = pd.DataFrame(data=_list_pos_label, columns=['term', 'pos'])
        term_df_ner = pd.DataFrame(data=_list_ner_label, columns=['term', 'ner'])
        start = datetime.now()
        term_pos_df = self.extract_taggings_for_terms(term_df_pos, 'pos')
        logger.info("getting all the pos mapping for all unique tf[term] = %s"%
                    (datetime.now() - start).total_seconds())
        start = datetime.now()
        term_ner_df = self.extract_taggings_for_terms(term_df_ner, 'ner')
        logger.info("getting all the ner mapping for all unique tf[term] = %s"%
                    (datetime.now() - start).total_seconds())
        return term_pos_df, term_ner_df

    def extract_taggings_for_terms(self, term_df, param):
        """
        Checks a term has occurred for a particular POS/NER tag
        :param term_df: dataframe with terms and their POS tagging/NER tagging
        :param param: POS/NER

        :return: dataframe with terms and its count for all the POS/NER mapping
        (count is basically 1 if the word has appeared in that POS/NER form else NAN)
        """
        unique_terms = list(term_df.term.unique())
        list_of_term_dict = []
        # count the number of times a term has occurred for a particular POS tag
        for term in unique_terms:
            word_df = term_df[term_df.term == term]
            word_df = word_df.groupby(by=[param], ).count()
            _dict = {pos_tag: count.term for pos_tag, count in word_df.iterrows()}
            _dict['term'] = term
            list_of_term_dict.append(_dict)
        df_new = pd.DataFrame.from_dict(list_of_term_dict)

        return df_new

    def get_all_ner_tags_for_word(self, term):
        """
        :param term:
        :return: dataframe with the NER tags count/existence for the input
        """
        df = self.term_ner_df[self.term_ner_df.term == term].drop(['term'], axis=1).T
        if df.shape[1] == 1:
            df.columns = ['count']
            df = df.fillna(0).astype(int).sort_values(by=['count'], ascending=False)
            return df
        return None  # {'error': "Term not Found!"}

    def check_ner_tag_of_word(self, term):
        """
        :param term:
        :return: True if the term has been tagged with selected NER
        """
        df = self.get_all_ner_tags_for_word(term.lower())
        if df is not None:
            term_ner_set = set(df[df['count'] != 0]['count'].index.tolist())  # considers all occurences
            return True if len(term_ner_set.intersection(ner_set)) > 0 else False
        else:
            return None

    def check_word_in_phrase_is_in_selected_ner(self, phrase):
        terms = phrase.split()
        terms = map(self.check_ner_tag_of_word, terms)
        return any(terms)

    def get_all_pos_tags_for_word(self, term):
        df = self.term_pos_df[self.term_pos_df.term == term].drop(['term'], axis=1).T
        if df.shape[1] == 1:
            df.columns = ['count']
            df = df.fillna(0).astype(int).sort_values(by=['count'], ascending=False)
            return df
        return None  # {'error': "Term not Found!"}

    def check_pos_tag_of_word(self, term):
        df = self.get_all_pos_tags_for_word(term)
        if df is not None:
            term_pos_set = set(df[df['count'] != 0]['count'].index.tolist())  # considers all occurences
            return True if len(term_pos_set.intersection(noun_set)) > 0 else False
        else:
            return None

    def check_word_in_phrase_noun(self, phrase):
        terms = phrase.split()
        terms = map(self.check_pos_tag_of_word, terms)
        return any(terms)

    def is_capital(self, phrase):
        r = re.findall('([A-Z])', phrase)
        if len(r) > 1:
            return True
        else:
            return False

    def extract_keywords(self):
        """
        :return: the final dataframe with term_phrase and its count
        """
        text_array = self.get_data_from_ES()
        start = datetime.now()
        self.dataset = pd.DataFrame({'TEXT': text_array})
        logger.info("data[TEXT] = %s "%(datetime.now() - start).total_seconds())

        # 1. Get all the sentences in the dataset
        self.update_dataset_with_sentence_list()

        # 2.  Apply NLP on sentences
        sentences = list((itertools.chain.from_iterable(self.dataset['sentences'].tolist())))
        sentences_nlp_results = self.get_nlp_sentences(sentences)

        # 3. Get noun chunks
        noun_chunks_cleaned = self.get_noun_chunks(sentences_nlp_results)

        # 4. Get term_phrase_frequency dataframe with filtered term phrase
        term_phrase_frequency_df = self.get_important_term_phrase_frequency(noun_chunks_cleaned)

        # 5. Get pos and ner tagging for the terms in term_phrase_frequency_df
        pos_label_list, ner_label_list = self.get_pos_and_ner_tags(sentences_nlp_results, term_phrase_frequency_df)

        # 6. Get 2 global dataframes for the words with all their pos/ner tagging
        start = datetime.now()
        self.term_pos_df, self.term_ner_df = self.get_pos_ner_df(pos_label_list, ner_label_list)
        logger.info("Complete lemmatizing and pos tagging = %s"%(datetime.now() - start).total_seconds())

        # 7. Filter based on NER Selection
        start = datetime.now()
        term_phrase_frequency_df['ner_to_be_retained'] = term_phrase_frequency_df['term_phrase'].apply(
            self.check_word_in_phrase_is_in_selected_ner)
        logger.info("Selection based on ner = %s"%(datetime.now() - start).total_seconds())
        start = datetime.now()

        # 8. Filter based on POS Selection
        term_phrase_frequency_df['contains_noun_words'] = term_phrase_frequency_df['term_phrase'].apply(
            self.check_word_in_phrase_noun)
        logger.info("Selection based on pos = %s"%(datetime.now() - start).total_seconds())
        start = datetime.now()

        term_phrase_frequency_df['is_capital'] = term_phrase_frequency_df['term_phrase'].apply(self.is_capital)
        logger.info("Check for capital = %s "%(datetime.now() - start).total_seconds())

        # 9. Drop the terms if not required POS/NER
        start = datetime.now()
        nouns_to_be_dropped = term_phrase_frequency_df[(term_phrase_frequency_df['contains_noun_words'] == False) & (
                    term_phrase_frequency_df['is_capital'] == False)]
        ner_to_be_dropped = term_phrase_frequency_df[(term_phrase_frequency_df['ner_to_be_retained'] == False) & (
                    term_phrase_frequency_df['is_capital'] == False)]

        filtered_term_phrase = term_phrase_frequency_df[~term_phrase_frequency_df.isin(nouns_to_be_dropped)].dropna()
        filtered_term_phrase_frequency_df = filtered_term_phrase[~filtered_term_phrase.isin(ner_to_be_dropped)].dropna()
        logger.info("Remove unwanted terms based on above selection = %s"%(datetime.now() - start).total_seconds())

        return filtered_term_phrase_frequency_df

    def insert_keywords_from_documents(self):
        data = self.extract_keywords()

        terms = data['term_phrase'].tolist()
        count = data['count'].tolist()
        #Append the keywords from the documents in term_frequency_dict
        for i, value in enumerate(terms):
                if value.lower() not in self.term_frequency_dict.keys():
                    self.term_frequency_dict[value.lower()] = count[i]
                else:
                    self.term_frequency_dict[value.lower()] = self.term_frequency_dict[value.lower()] + count[i]


        keywords = list(data["term_phrase"])
        keywords = [keyword.lower() for keyword in keywords]
        logger.info("No of keywords extracted from documents = %s"%len(keywords))
        # dummy = keywords
        # dummy.sort()
        # outfile = open("NewCompletefilter.txt", "w")
        # outfile.write("\n".join(dummy))
        # outfile.close()
        key_suggestion_keywords = config.get("redis", "key_suggestion_keywords")
        redis_connect = redis_connector.get_instance()
        return redis_connect.insert_set(keywords, key_suggestion_keywords)

    def extract_search_history(self, min_freq):
        query_array = []
        search_history_array = []
        corpus_index_name = config.get('elasticsearch', 'logs_index_name')
        users = config.get('keywordsextractor', 'search_history_excluded_users')
        user_list = users.split(',')
        out = []
        for name in user_list:
            dict_in = {}
            dict_out = {}
            dict_in['userId'] = name
            dict_out['term'] = dict_in
            out.append(dict_out)

        query_dict = {'query': {'bool': {'must_not': []}}}
        query_dict['query']['bool']['must_not'] = out

        search_query = json.dumps(query_dict)   #search_query to get all queries not fired by the team


        json_data = es_connect.generic_search_query(corpus_index_name, search_query)

        for hit in json_data['hits']['hits']:
            query_string = hit['_source'].get('query')
            query_array.append(query_string)

        counts = Counter(query_array)
        res = Counter({k: v for k, v in counts.items() if v > min_freq and len(k.split()) <= 5})
        sorted_dict = OrderedDict(sorted(res.items(), key=lambda kv: kv[1], reverse=True))


        for key in sorted_dict:
            search_history_array.append(key)
            #Append the keywords from search history in the term_frequency_dict
            if key in self.term_frequency_dict.keys():
                self.term_frequency_dict[key] += sorted_dict[key]
            else:
                self.term_frequency_dict[key] = sorted_dict[key]

        return search_history_array

    def insert_keywords_from_search_history(self):
        min_freq = config.get("keywordsextractor", "search_history_autosuggest_min_freq")
        search_log_data = self.extract_search_history(int(min_freq))
        logger.info("No of keywords from search history = %s"%len(search_log_data))
        search_history = config.get("redis", "search_history_keywords")
        redis_connect = redis_connector.get_instance()
        return redis_connect.insert_set(search_log_data, search_history)

    def insert_keywords_from_search_history_and_documents_rank(self):
        #Add the term phrases to the Redis based on the count in descending order
        #self.term_frequency
        keywords = []
        for key, value in sorted(self.term_frequency_dict.items(), key=itemgetter(1), reverse=True):
            keywords.append(key)
        keywords_rank = config.get("redis", "key_search_history_rank")
        redis_connect = redis_connector.get_instance()
        return redis_connect.insert_set(keywords, keywords_rank)

    def refresh_autosuggest_keywords_list(self):
        # Function will be used to refresh both search log and the suggest keywords from documents
        refresh_status = True
        start = datetime.now()
        if self.insert_keywords_from_documents():
            logger.info("Extracted keywords from documents successfully.")
            logger.info("Total time taken to extract keywords from documents = %s "%
                        (datetime.now() - start).total_seconds())
        else:
            refresh_status = False
            logger.info("Extracting keywords from documents is failed")

        start = datetime.now()
        if self.insert_keywords_from_search_history():
            logger.info("Extracted keywords from search history successfully.")
            logger.info("Total time taken to extract keywords from search history = %s"%
                        (datetime.now() - start).total_seconds())
        else:
            refresh_status = False
            logger.error("Extracting keywords from search history is failed")

        start = datetime.now()
        if self.insert_keywords_from_search_history_and_documents_rank():
            logger.info("Extracted keywords from ranked history successfully.")
            logger.info("Total time taken to extract keywords from ranked history = %s",
                        (datetime.now() - start).total_seconds())
        else:
            refresh_status = False
            logger.error("Extracting keywords from ranked history failed")
        return refresh_status


if __name__ == '__main__':
    keywords_class = keywords_extractor()
    keywords_class.refresh_autosuggest_keywords_list()