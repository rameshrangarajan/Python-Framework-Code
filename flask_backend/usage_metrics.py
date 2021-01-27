from elasticsearch_connector import elasticsearch_connector
import utils
from datetime import datetime
from logger import log

config = utils.config_parser()
logger = log.getLogger()

class usage_metrics():
    def create_usage_metrics_response(period):
        usage_metrics_dict = {}
        day_of_week = datetime.today().weekday()
        if period == "today":
            gte = "now/d"
            lte = "now"
            gte_prev = "now/d-1d/d"
            lte_prev = "now-1d"
        elif period == "this_week":
            gte = "now/d-" + str(day_of_week + 1) + "d/d"
            lte = "now"
            gte_prev = "now/d-" + str(day_of_week + 8) + "d/d"
            lte_prev = "now-7d"
        elif period == "last_week":
            gte = "now/d-" + str(day_of_week + 8) + "d/d"
            lte = "now/d-" + str(day_of_week + 1) + "d/d"
            gte_prev = "now/d-" + str(day_of_week + 15) + "d/d"
            lte_prev = "now/d-" + str(day_of_week + 8) + "d/d"
        elif period == "this_month":
            gte = "now/M"
            lte = "now"
            gte_prev = "now/M-1M"
            lte_prev = "now-1M"
        elif period == "last_month":
            gte = "now/M-1M"
            lte = "now/M"
            gte_prev = "now/M-2M"
            lte_prev = "now/M-1M"
        elif period == "this_year":
            gte = "now/y"
            lte = "now"
            gte_prev = "now/y-1y"
            lte_prev = "now-1y"

        usage_metrics_dict.update(usage_metrics.get_users_queries_usage(period, gte, lte, gte_prev, lte_prev))
        usage_metrics_dict.update(usage_metrics.get_downloads_usage(gte, lte, gte_prev, lte_prev))
        usage_metrics_dict.update(usage_metrics.get_feedback_usage(gte, lte, gte_prev, lte_prev))
        usage_metrics_dict.update(usage_metrics.get_autosuggestion_usage(gte, lte, gte_prev, lte_prev))
        usage_metrics_dict.update(usage_metrics.get_avg_query_time_usage(gte, lte, gte_prev, lte_prev))
        usage_metrics_dict['period'] = {"value":period}
        return usage_metrics_dict

    def get_users_queries_usage(period, gte, lte, gte_prev, lte_prev):
        usage_dict={}
        users_count, queries_count = usage_metrics.fetch_users_queries_usage_from_es(period, gte, lte)
        users_count_prev, queries_count_prev = usage_metrics.fetch_users_queries_usage_from_es(period, gte_prev, lte_prev)
        usage_dict["users"]={"value":users_count,"trend":usage_metrics.return_trend(users_count,users_count_prev)}
        usage_dict["queries"]={"value":queries_count,"trend":usage_metrics.return_trend(queries_count,queries_count_prev)}
        return usage_dict

    def get_downloads_usage(gte, lte, gte_prev, lte_prev):
        logs_index = config.get("elasticsearch", "download_logs_index_name")
        download_usage_dict={}
        downloads_count = usage_metrics.fetch_downloads_usage_from_es(logs_index, gte, lte)
        downloads_count_prev = usage_metrics.fetch_downloads_usage_from_es(logs_index, gte_prev, lte_prev)
        downloads_on_first_page_count = usage_metrics.fetch_first_page_downloads_usage_from_es(logs_index, gte, lte)
        downloads_on_first_page_count_prev = usage_metrics.fetch_first_page_downloads_usage_from_es(logs_index, gte_prev,lte_prev)
        download_usage_dict["downloads"]={"value":downloads_count,"trend":usage_metrics.return_trend(downloads_count,downloads_count_prev)}
        download_usage_dict["downloads_on_first_page"]={"value":downloads_on_first_page_count,"trend":usage_metrics.return_trend(downloads_on_first_page_count,downloads_on_first_page_count_prev)}
        return download_usage_dict

    def get_feedback_usage(gte, lte, gte_prev, lte_prev):
        usage_dict={}
        ratings = usage_metrics.fetch_feedback_usage_from_es(gte, lte)
        ratings_prev = usage_metrics.fetch_feedback_usage_from_es(gte_prev, lte_prev)
        usage_dict["ratings"]={"value":ratings, "trend":usage_metrics.return_trend(ratings,ratings_prev)}
        return usage_dict

    def get_autosuggestion_usage(gte, lte, gte_prev, lte_prev):
        usage_dict = {}
        accepted_suggestions = usage_metrics.fetch_autosuggestions_usage_from_es(gte,lte)
        accepted_suggestions_prev = usage_metrics.fetch_autosuggestions_usage_from_es(gte_prev,lte_prev)
        usage_dict["accepted_suggestions"]={"value":accepted_suggestions, "trend":usage_metrics.return_trend(accepted_suggestions,accepted_suggestions_prev)}
        return usage_dict

    def get_avg_query_time_usage(gte, lte, gte_prev, lte_prev):
        usage_dict = {}
        avg_query_time = usage_metrics.fetch_avg_query_time_from_es(gte,lte)
        avg_query_time_prev = usage_metrics.fetch_avg_query_time_from_es(gte_prev, lte_prev)
        usage_dict["avg_query_time"] = {"value":avg_query_time, "trend":usage_metrics.return_trend(avg_query_time,avg_query_time_prev)}
        return usage_dict

    def fetch_users_queries_usage_from_es(period, gte, lte):
        logs_index = config.get("elasticsearch", "logs_index_name")
        query = {   "size": 0,
                    "query": {
                        "bool": {
                            "must": [
                            {
                               "term": {
                                  "query_type": "search"
                               }
                            },
                                {
                                    "range": {
                                        "query_timestamp": {
                                            "gte": gte,
                                            "lte": lte
                                        }
                                    }
                                }
                            ]
                        }
                    },
                    "aggs": {

                                "users_distinct": {
                                    "cardinality": {
                                        "field": "userId.keyword"
                                    }
                                },
                                "number_of_queries": {
                                    "value_count": {
                                        "field": "query.keyword"
                                    }

                            }

                    }
                }
        es_obj = elasticsearch_connector.get_instance()
        result = es_obj.generic_search_query(logs_index, query)
        if result:
            queries_count = result["aggregations"]['number_of_queries']['value']
            users_count = result["aggregations"]['users_distinct']['value']
            return users_count, queries_count
        else:
            return 0,0


    def return_trend(current_usage, old_usage):
        if current_usage - old_usage > 0:
            trend = 1
        elif current_usage - old_usage == 0:
            trend = 0
        else:
            trend = -1
        return trend


    def fetch_downloads_usage_from_es(index_name, gte,lte):
        query ={"size":0,
                "query": {
                        "bool": {
                            "must": [
                                {
                                    "range": {
                                        "download_timestamp": {
                                            "gte": gte,
                                            "lte": lte

                                        }
                                    }
                                }
                            ]
                        }
                    }
               }
        return usage_metrics.get_usage_from_es(index_name, query)

    def get_usage_from_es(index_name, query):
        es_obj = elasticsearch_connector.get_instance()
        result = es_obj.generic_search_query(index_name, query)
        if result:
            return result["hits"]["total"]["value"]
        else:
            return 0


    def fetch_first_page_downloads_usage_from_es(index_name, gte, lte):
        query = {   "size":0,
                    "query": {
                        "bool": {
                            "must":
                                {
                                    "range": {
                                        "download_timestamp": {
                                            "gte": gte,
                                            "lte": lte

                                        }
                                    }
                                }
                            ,
                            "must_not" : {
                                "range" : {
                                    "searched_result_index" : { "gte" : 11 }
                                }
                            }
                        }
                    }
                }
        return usage_metrics.get_usage_from_es(index_name, query)


    def fetch_feedback_usage_from_es(gte, lte):
        feedback_index = config.get("elasticsearch", "user_feedback_index_name")
        query={ "size":0,
                "query": {
                    "bool": {
                        "must": [
                            {
                                "range": {
                                    "feedback_timestamp": {
                                        "gte": gte,
                                        "lte": lte
                                    }
                                }
                            }
                        ]
                    }
                }
            }
        return usage_metrics.get_usage_from_es(feedback_index, query)


    def fetch_autosuggestions_usage_from_es(gte,lte):
        autosuggest_index = config.get("elasticsearch", "autosuggest_feedback_index_name")
        query={ "size":0,
                "query": {
                    "bool": {
                        "must": [
                            {
                                "range": {
                                    "timestamp": {
                                        "gte": gte,
                                        "lte": lte
                                    }
                                }
                            }
                        ]
                    }
                }
            }
        return usage_metrics.get_usage_from_es(autosuggest_index, query)


    def fetch_avg_query_time_from_es(gte,lte):
        index_name = config.get("elasticsearch", "logs_index_name")
        query={"size":0,
                "query": {
                "bool": {
                    "must": [
                        {
                            "range": {
                                "query_timestamp": {
                                    "gte": gte,
                                    "lte": lte
                                }
                            }
                        }
                    ]
                 }
                 },
                "aggs": {
                    "avg_time": {
                        "avg": {
                            "script": "doc['response_timestamp'].value.getMillis() - doc['query_timestamp'].value.getMillis()"
                        }
                    }
                }
            }
        es_obj = elasticsearch_connector.get_instance()
        result = es_obj.generic_search_query(index_name, query)
        if result:
            if result["aggregations"]["avg_time"]["value"] != None:
                avg_query_time = round((result["aggregations"]["avg_time"]["value"]/1000), 3)
                return avg_query_time
            else:
                return 0
        else:
            return 0

    def create_queries_metrics_response():
        index_name = config.get("elasticsearch", "logs_index_name")
        response = {}
        excluded_users = usage_metrics.generate_query_to_exclude_users()
        response["recent_queries"] = usage_metrics.get_recent_queries(index_name, excluded_users)
        response["trending_queries"] =usage_metrics.get_trending_queries(index_name, excluded_users)
        return response

    def get_recent_queries(index_name, excluded_users):
        query={
                "query" :
               {
                   "bool":
                       {
                           "must": [
                           {
                           "range" : {
                                "query_timestamp" : { "gte" : "now-24h", "to" : "now" }
                                     }
                           }
                           ]
                       }
               },
               "sort":
                {
                  "response_timestamp": {
                    "order": "desc"
                  }
                }

            }
        if excluded_users != None:
            query["query"]["bool"]["must_not"] = excluded_users
        response = usage_metrics.get_recent_queries_from_es(index_name,query)
        if response != []:
            return response
        else:
            query["query"]["bool"]["must"][0]["range"]["query_timestamp"]["gte"] = "now-1w"
            response = usage_metrics.get_recent_queries_from_es(index_name,query)
            if response != []:
                return response
            else:
                query["query"]["bool"]["must"][0]["range"]["query_timestamp"]["gte"] = "now-1M"
                response = usage_metrics.get_recent_queries_from_es(index_name,query)
                if response != []:
                    return response
                else:
                    query["query"]["bool"]["must"][0]["range"]["query_timestamp"]["gte"] = "now-1y"
                    response = usage_metrics.get_recent_queries_from_es(index_name, query)
                    if response != []:
                        return response
                    else:
                        return []

    def get_trending_queries(index_name, excluded_users):
        query={ "size":0,
                "query": {
                    "bool": {
                        "must": [
                            {
                                "range": {
                                    "query_timestamp": {
                                        "gte": "now-1w"
                                    }
                                }
                            }
                        ]
                    }
                },
                "aggs": {
                    "trending_query": {
                        "terms": {
                             "field":"query.keyword"
                        }
                    }
                }
            }

        if excluded_users != None:
            query["query"]["bool"]["must_not"] = excluded_users
        response = usage_metrics.get_trending_queries_from_es(index_name,query)
        if response != []:
            return response
        else:
            query["query"]["bool"]["must"][0]["range"]["query_timestamp"]["gte"] = "now-1M"
            response = usage_metrics.get_trending_queries_from_es(index_name,query)
            if response != []:
                return response
            else:
                query["query"]["bool"]["must"][0]["range"]["query_timestamp"]["gte"] = "now-1y"
                response = usage_metrics.get_trending_queries_from_es(index_name, query)
                if response != []:
                    return response
                else:
                    return []


    def get_recent_queries_from_es(index_name, query):
        es_obj = elasticsearch_connector.get_instance()
        result = es_obj.generic_search_query(index_name, query)
        recent_query_list = []
        if result:
            if len(result["hits"]["hits"]) > 0:
                for hit in result["hits"]["hits"]:
                    query=hit["_source"]["query"].lower()
                    if query not in recent_query_list:
                        recent_query_list.append(query)
                    if recent_query_list.__len__() == 10:
                        break
            else:
                return []
        else:
            return []
        return recent_query_list

    def get_trending_queries_from_es(index_name, query):
        es_obj = elasticsearch_connector.get_instance()
        result = es_obj.generic_search_query(index_name, query)
        trending_query_list = []
        if result:
            if len(result["aggregations"]["trending_query"]["buckets"]) > 0:
                for bucket in result["aggregations"]["trending_query"]["buckets"]:
                    query=bucket["key"].lower()
                    if query not in trending_query_list:
                        trending_query_list.append(query)
                    if trending_query_list.__len__() == 10:
                        logger.info("trending_query_list: %s" % trending_query_list)
                        break
            else:
                return []
        else:
            return []
        return trending_query_list

    def generate_query_to_exclude_users():
        users = config.get('generic', 'user_logs_excluded_users')
        if users:
            user_list = users.split(',')
            excluded_user_dict = []
            for name in user_list:
                user_dict = {}
                term_dict = {}
                user_dict['userId'] = name
                term_dict['term'] = user_dict
                excluded_user_dict.append(term_dict)
            return excluded_user_dict
        else:
            return None
