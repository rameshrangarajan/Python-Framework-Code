# -*- coding: utf-8
"""
Created on Thu Sep  5 18:14:07 2019

@author: godbole_s
"""
import utils
import redis
from logger import log
import re


logger = log.getLogger()

class redis_connector():
    redis_connector_obj = None
    redis_client = None

    def __init__(self):
        if redis_connector.redis_connector_obj is not None:
            raise Exception("This class is a singleton!")
        else:
            self.connect()
            redis_connector.redis_connector_obj = self

    @staticmethod
    def get_instance():
        if redis_connector.redis_connector_obj is None:
            redis_connector()
        return redis_connector.redis_connector_obj

    def connect(self):
        redis_connect = self.redis_client
        if redis_connect is not None and redis_connect.ping():
            logger.info('Already connected to redis DB')
        else:
            config = utils.config_parser()
            redis_host = config.get("redis", "host")
            redis_password = config.get("redis", "password")
            redis_port = config.get("redis", "port")
            r_obj = redis.Redis(host=redis_host, port=redis_port, db=0, password=redis_password)
            logger.info("Successfully connected to Redis DB")
            self.redis_client = r_obj      

    def insert_set(self , keywords, key_suggestion_keywords):
        try:
            redis_connect = self.redis_client

            if redis_connect is not None and redis_connect.ping():
                self.connect()
            if redis_connect.exists(key_suggestion_keywords):
                redis_connect.delete(key_suggestion_keywords)
            if key_suggestion_keywords == 'keywords_rank':
                for i, keyword in enumerate(keywords):
                    redis_connect.zadd(key_suggestion_keywords, {keyword: i})
            else:
                for keyword in keywords:
                    redis_connect.sadd(key_suggestion_keywords, keyword)

            logger.info("Successfully added new keywords to Redis DB")
            return True
        except:
            logger.exception("failed to add new keywords to redis DB")
            return False

    def query_db(self, query):
        try:
            config = utils.config_parser()

            key_search_rank = config.get("redis", "key_search_history_rank")
            redis_connect = self.redis_client
            if redis_connect is not None and redis_connect.ping():
                self.connect()


            keywords_rank = redis_connect.zrange(key_search_rank, 0, -1)

            words_in_query = query.split()
            for index, word in enumerate(words_in_query):
                word1 = '\\b' + word
                words_in_query[index] = word1
            new_query = '\\s+'.join(words_in_query)

            suggestions = list(utils.clean_text(str(selected_keyword)) for selected_keyword in keywords_rank if re.search(new_query, utils.clean_text(str(selected_keyword))))

            return suggestions
        except:
            logger.exception("Could not query redis DB")
            return None

    def query_db_with_scores(self, query):
        try:
            config = utils.config_parser()
            key_search_rank = config.get("redis", "key_search_history_rank")
            redis_connect = self.redis_client
            if redis_connect is not None and redis_connect.ping():
                self.connect()

            keywords_rank = redis_connect.zrange(key_search_rank, 0, -1, withscores=True)
            suggestions_dict = {}
            for q in query.split(' '):
                q = r"\b" + re.escape(q) + r"\b"
                suggestions = list(suggestions_dict.update({utils.clean_text(str(selected_keywords[0])): selected_keywords[1]}) for selected_keywords in keywords_rank if re.search(q, (utils.clean_text(str(selected_keywords[0])))))
                #suggestions = list(suggestions_dict.update({utils.clean_text(str(selected_keywords[0])): selected_keywords[1]}) for selected_keywords in keywords_rank if q in (utils.clean_text(str(selected_keywords[0])).split(' ')))
            return suggestions_dict
        except:
            logger.exception("Could not query redis DB")
            return None

#if __name__ == '__main__':
#     # connect = redis_connector()
#     config = utils.config_parser()
#     redis_host = config.get("redis", "host")
#     redis_password = config.get("redis", "password")
#     redis_port = config.get("redis", "port")
#     r_obj = redis.Redis(host=redis_host, port=redis_port, db=0, password=redis_password)
#     redis_ = redis_connector()
#     redis_.insert_keywords_from_documents()
#     print(redis_.query_db("ma"))
#     redis_connector.redis_client = r_obj
#     redis_connector.query_db("iot")