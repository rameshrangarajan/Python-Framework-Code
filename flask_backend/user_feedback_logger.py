from elasticsearch_connector import elasticsearch_connector
import utils
from logger import log

logger = log.getLogger()


class user_feedback_logger():
    # This function updates like/dislike feedback entry in elastic search using index name provided in config
    def log_feedback_event(log_data):
        config = utils.config_parser()
        user_feedback_index = config.get('elasticsearch', 'user_feedback_index_name')
        es_obj = elasticsearch_connector.get_instance()

        get_feedback_data = {
                                "query": {
                                    "bool": {
                                        "must": [
                                            {"match": {"userId": log_data['userId']}},
                                            {"match_phrase": {"doc_id": log_data['doc_id']}},
                                        ]
                                    }
                                }
                            }

        json_data = es_obj.generic_search_query(user_feedback_index, get_feedback_data)
        feedback_data = json_data['hits']['hits']
        if feedback_data:
            update_feedback = {
                "script": {
                    "source": "ctx._source.feedback = params.feedback",
                    "lang": "painless",
                    "params": {
                        "feedback": log_data['feedback']
                    }
                },
                "query": {
                    "bool": {
                        "must": [
                            {"match": {"userId": log_data['userId']}},
                            {"match_phrase": {"doc_id": log_data['doc_id']}}

                        ]
                    }
                }
            }
            result = es_obj.update_index_by_query(user_feedback_index, "pptx", update_feedback)
        else:
            result = es_obj.insert_document(user_feedback_index, "pptx", None, log_data)
        return result

    def update_ratings_for_all_docs():
        config = utils.config_parser()
        user_feedback_index = config.get('elasticsearch', 'user_feedback_index_name')
        corpus_index_name = config.get('elasticsearch', 'corpus_index_name')
        doc_type = config.get('elasticsearch', 'doc_type')

        elastic_obj = elasticsearch_connector.get_instance()
        aggregation_query = {
                            "aggs": {
                                "user_feedback_aggregation": {
                                    "terms": {
                                        "field": "doc_id.keyword",
                                        "size": 10000
                                    },
                                    "aggs": {
                                        "group_by_feedback":{
                                            "terms": {
                                                 "field": "feedback"
                                            }
                                        }
                                    }
                                }
                            }
                        }

        result = elastic_obj.generic_search_query(user_feedback_index, aggregation_query)
        aggregations = result["aggregations"]
        buckets = aggregations["user_feedback_aggregation"]["buckets"]
        for item in buckets:
            key = item['key']
            feedback_count, num_likes, num_dislikes = 0, 0, 0
            inner_bucket = item['group_by_feedback']['buckets']
            for feedback in inner_bucket:
                feedback_count += feedback['key'] * feedback['doc_count']
                if feedback['key'] == 1:
                    num_likes = feedback['doc_count']
                elif feedback['key'] == -1:
                    num_dislikes = feedback['doc_count']

            ratings = {
                "script" : {
                    "source": "ctx._source.ratings = params.ratings; ctx._source.num_likes = params.num_likes; ctx._source.num_dislikes = params.num_dislikes",
                    "lang": "painless",
                    "params": {
                        "ratings": feedback_count,
                        "num_likes": num_likes,
                        "num_dislikes": num_dislikes
                    }
                }
            }

            result = elastic_obj.update_document(corpus_index_name, doc_type, key, ratings)
            if result:
                logger.info("Aggregated ratings updated on corpus index")
            else:
                logger.error("Could not aggregate ratings on corpus index")

    def update_feedback_count_for_document(doc_id, feedback):
        config = utils.config_parser()
        # user_feedback_index = config.get('elasticsearch', 'user_feedback_index_name')
        corpus_index_name = config.get('elasticsearch', 'corpus_index_name')
        doc_type = config.get('elasticsearch', 'doc_type')
        es_obj = elasticsearch_connector.get_instance()

        feedback_rating, num_likes, num_dislikes = user_feedback_logger.get_feedback_count_for_document(doc_id)

        update_download_count = {
             "script":
                 {
                "source": "ctx._source.ratings = params.ratings; ctx._source.num_likes = params.num_likes; ctx._source.num_dislikes = params.num_dislikes",
                "lang": "painless",
                "params":
                    {
                    "ratings": feedback_rating,
                    "num_likes": num_likes,
                    "num_dislikes": num_dislikes
                    }
                }
            }
        es_obj.update_document(corpus_index_name, doc_type, doc_id, update_download_count)
        return num_likes, num_dislikes

    # Get the current feedback count for document. This value is used while indexing document
    def get_feedback_count_for_document(doc_id):
        config = utils.config_parser()
        user_feedback_index = config.get('elasticsearch', 'user_feedback_index_name')
        elastic_obj = elasticsearch_connector.get_instance()
        aggregation_query = {
                              "query":
                                {
                                "match_phrase":
                                    {
                                    "doc_id":
                                        {
                                        "query": doc_id
                                        }
                                    }
                                },

                              "aggs": {
                                "user_feedback_aggregation":
                                {
                                    "terms":
                                        {
                                        "field": "doc_id.keyword",
                                        "size": 10000
                                        },
                                    "aggs":
                                    {
                                        "group_by_feedback":
                                        {
                                        "terms":
                                            {
                                             "field":"feedback"
                                            }
                                        }
                                    }
                                }
                              }
                            }

        try:
            result = elastic_obj.generic_search_query(user_feedback_index, aggregation_query)
            if result:
                aggregations = result["aggregations"]
                buckets = aggregations["user_feedback_aggregation"]["buckets"]
                if buckets:
                    feedback_count, num_likes, num_dislikes = 0, 0, 0
                    inner_bucket = buckets[0]['group_by_feedback']['buckets']
                    for feedback in inner_bucket:
                        feedback_count += feedback['key'] * feedback['doc_count']
                        if feedback['key'] == 1:
                            num_likes = feedback['doc_count']
                        elif feedback['key'] == -1:
                            num_dislikes = feedback['doc_count']
                    return feedback_count, num_likes, num_dislikes
                else:
                    return 0, 0, 0
            else:
                return 0, 0, 0
        except:
            return 0, 0, 0

    def reset_ratings_likes_dislikes_for_all_indexed_docs():
        config = utils.config_parser()
        index_name = config.get("elasticsearch", "corpus_index_name")
        doc_type = config.get("elasticsearch", "doc_type")
        reset_query={
                      "script": {
                        "source": "ctx._source.ratings = 0; ctx._source.num_likes = 0; ctx._source.num_dislikes = 0",
                        "lang": "painless"
                      },
                      "query": {
                        "match_all": {}
                      }
                     }
        es_obj = elasticsearch_connector.get_instance()
        return es_obj.update_index_by_query(index_name, doc_type, reset_query)

    def get_feedback_count_per_user_for_all_documents(user_id):
        config = utils.config_parser()
        user_feedback_index = config.get('elasticsearch', 'user_feedback_index_name')
        elastic_obj = elasticsearch_connector.get_instance()
        user_like_dislike = {}
        aggregation_query = {
                            "query": {
                                        "match": {
                                            "userId": {
                                                "query": user_id
                                            }
                                        }
                                    },
                            "aggs": {
                                "user_feedback_aggregation": {
                                    "terms": {
                                        "field": "doc_id.keyword",
                                        "size": 10000
                                    },
                                    "aggs": {
                                        "group_by_feedback": {
                                            "terms": {
                                                "field": "feedback"
                                            }
                                        }
                                    }
                                }
                            }
                        }

        try:
            result = elastic_obj.generic_search_query(user_feedback_index, aggregation_query)
            if result:
                aggregations = result["aggregations"]
                buckets = aggregations["user_feedback_aggregation"]["buckets"]
                if buckets:
                    for bucket in buckets:
                        doc_id, liked_status, disliked_status = 0, False, False
                        liked_count, disliked_count = 0, 0
                        doc_id = bucket['key']

                        inner_bucket = bucket['group_by_feedback']['buckets']
                        for feedback in inner_bucket:
                            if feedback['key'] == 1:
                                liked_count = feedback['doc_count']
                            elif feedback['key'] == -1:
                                disliked_count = feedback['doc_count']
                        if int(liked_count) > int(disliked_count) :
                            liked_status = True
                        elif int(liked_count) < int(disliked_count):
                            disliked_status = True

                        user_like_dislike[doc_id] = [liked_status, disliked_status]
                    return user_like_dislike
                else:
                    return False
            else:
                return False
        except:
            return False



    if __name__ == '__main__':
        update_ratings_for_all_docs()
