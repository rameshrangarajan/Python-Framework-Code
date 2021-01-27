from elasticsearch import Elasticsearch
import utils
from logger import log

logger = log.getLogger()

class elasticsearch_connector():
    es_connector = None
    es_client = None
    LTR_window_size = 10000
    def __init__(self):
        if elasticsearch_connector.es_connector is not None:
            raise Exception("This class is a singleton!")
        else:
            self.connect()
            elasticsearch_connector.es_connector = self

    @staticmethod
    def get_instance():
        if elasticsearch_connector.es_connector is None:
            elasticsearch_connector()
        return elasticsearch_connector.es_connector

    def connect(self):
        """ Connect to elastic search
               Args:
                   es : elastic seacrh object
               Return:
                 object of elastic search
           """
        es = self.es_client
        if es is not None and es.ping():
            logger.info('Already connected to elastic search')
        else:
            config = utils.config_parser()
            host = config.get('elasticsearch', 'host')
            port = config.get('elasticsearch', 'port')
            es_user = config.get('elasticsearch', 'user')
            es_passw = config.get('elasticsearch', 'passw')
            es = Elasticsearch([{'host': host, 'port': port}], http_auth=(es_user, es_passw), scheme="https",ca_certs=False,
                               verify_certs=False)
            logger.info('Successfully connected to Elasticsearch')
            self.es_client = es

    def clear_index(self, index_name):
        """ Remove the index if already created
                  Args:
                      index_name : index name to be removed
                  Return:
                     NA
            """
        try:
            if self.es_client is None or not self.es_client.ping():
                self.connect()

            if self.es_client.indices.exists(index_name):
                self.es_client.indices.delete(index=index_name)
                logger.info('Deleted existing index')
            else:
                logger.info('Index does not exist')
        except:
            logger.exception("could not clear index")

    def check_if_index_exists(self, index_name):
        """ Check that the index is already created
            Args:
                index_name : index name to be removed
            Return:
                NA
        """
        if self.es_client.indices.exists(index_name):
            return True
        else:
            return False

    def insert_document(self, index_name, type, document_id, document):
        """ Insert parsed input in elastic search
              Args:
                  document : parsed results returned from return_file_metadata() function
                  document_id : document will be inserted in elastic serach using this id
              Return:
                 default response for indexing is returned
        """

        try:
            if self.es_client is None or not self.es_client.ping():
                self.connect()

            if document_id is not None and document_id != "":
                return self.es_client.index(index=index_name, doc_type=type, id=document_id, body=document, refresh='wait_for', request_timeout=30)
            else:
                return self.es_client.index(index=index_name, doc_type=type, body=document, refresh='wait_for', request_timeout=30)
        except:
            logger.exception("could not insert document is %s in index %s "%(document_id, index_name))

    def update_document(self, index_name, type, document_id, document):
        try:
            if self.es_client is None or not self.es_client.ping():
                self.connect()
            result = self.es_client.update(index=index_name, doc_type=type, id=document_id, body=document, refresh=True, retry_on_conflict=2)
            return True
        except:
            logger.exception("could not update document id %s in index %s " % (document_id, index_name))
            return False

    def update_index_by_query(self, index_name, type, document):
        try:
            if self.es_client is None or not self.es_client.ping():
                self.connect()
            result = self.es_client.update_by_query(index=index_name, body=document, refresh=True)
            return True
        except:
            logger.exception("could not update all documents from index %s " % (index_name))
            return False

    def query_string(self, query_string, index_name, start_from, size, time_filter):
        """ Search the input string in elastic search
                 Args:
                     query_string : String to be searched in elastic search
                 Return:
                     result : returns the result came from elastic search
        """
        config = utils.config_parser()
        highlight_tag = config.get('elasticsearch', 'highlight_tag')
        use_model = config.get('elasticsearch', 'model')
        model_number = config.get('elasticsearch', 'model_number')

        try:
            if self.es_client is None or not self.es_client.ping():
                self.connect()

            self.es_client.indices.refresh(index=index_name)
            gte = ""
            if time_filter == "30_days":
                gte = "now-30d"
            elif time_filter == "12_months":
                gte = "now-1y"
            elif time_filter == "3_years":
                gte = "now-3y"

            if gte == "":
                query = {
                            "query_string": {
                                "query": "*" + query_string + "*",
                                "fields": ["slides.shapes.paras.lines.segments.text", "slides.title", "title", "created_by", "file_name", "modified_by"]
                                }
                        }
            else:
                query = {
                        "bool": {
                            "must": [
                                {
                                    "query_string": {
                                        "query": "*" + query_string + "*",
                                        "fields": ["slides.shapes.paras.lines.segments.text", "slides.title", "title", "created_by", "file_name", "modified_by"]
                                    }
                                },
                                {
                                    "bool": {
                                        "should": [
                                            {
                                                "range": {
                                                    "modified_time": {
                                                        "gte": gte,
                                                        "lte": "now"
                                                    }
                                                }
                                            },
                                            {
                                                "range": {
                                                    "created_time": {
                                                        "gte": gte,
                                                        "lte": "now"
                                                    }
                                                }
                                            }
                                        ]
                                    }
                                }
                            ]
                        }
                    }

            if use_model != "true":
                search_query = {
                                "from": start_from,
                                "query": query,
                                "highlight": {
                                    "pre_tags": ["<" + highlight_tag + ">"],
                                    "post_tags": ["</" + highlight_tag + ">"],
                                    "type": "plain",
                                    "fields": {
                                        "slides.shapes.paras.lines.segments.text": {},
                                        "title": {}
                                        }
                                    },
                                }

                try:
                    result = self.es_client.search(index=index_name, body=search_query, allow_partial_search_results=True, size=size)
                    logger.info('For search query: '+query_string +' got %d Hits:' % result['hits']['total']['value'])
                    return result
                except Exception as e:
                    logger.error(str(e))
                    return e
            else:
                try:
                    model = "test_" + model_number
                    logger.info("Fetching results from "+str(start_from)+" to "+str(size-1))
                    result = self.es_client.search(index=index_name, body=self.ltr_query(query_string, model, start_from, gte), size=size)
                    logger.info('For search query: '+query_string +' got %d Hits:' % result['hits']['total']['value'])
                    return result
                except Exception as e:
                    logger.error(str(e))
                    return e
        except Exception as e:
            logger.error(str(e))

    def ltr_query(self, keywords, model_name, start, gte):
        config = utils.config_parser()
        highlight_tag = config.get('elasticsearch', 'highlight_tag')

        if "\"" not in keywords:
            keywords = " ".join(keywords.split("_"))
            basic_query = {
                    "multi_match": {
                        "query": "test",
                        "analyzer": "synonym_stop",
                        "fields": ["slides.shapes.paras.lines.segments.text", "slides.title", "title", "created_by", "file_name", "modified_by"]
                    }
                }
        else:
            keywords = keywords.replace('"', '')
            basic_query = {
                    "multi_match": {
                        "query": "test",
                        "type": "phrase",
                        "fields": ["slides.shapes.paras.lines.segments.text", "slides.title", "title", "created_by",
                                   "file_name", "modified_by"]
                   }
                }

        if gte == "":
            query=basic_query
        else:
            query = {
                "bool": {
                    "must": [
                        basic_query,
                        {
                            "bool": {
                                "should": [
                                    {
                                        "range": {
                                            "modified_time": {
                                                "gte": gte,
                                                "lte": "now"
                                            }
                                        }
                                    },
                                    {
                                        "range": {
                                            "created_time": {
                                                "gte": gte,
                                                "lte": "now"
                                            }
                                        }
                                    }
                                ]
                            }
                        }
                    ]
                }
            }
        baseQuery = {
            "from": start,
            "query": query,
            "highlight": {
                "pre_tags": ["<" + highlight_tag + ">"],
                "post_tags": ["</" + highlight_tag + ">"],
                "type": "plain",
                "fields": {
                    "slides.shapes.paras.lines.segments.text": {},
                    "title": {},
                    "created_by":{}
                }
            },
            "rescore": {
                "window_size": self.LTR_window_size,
                "query": {
                    "rescore_query": {
                        "sltr": {
                            "params": {
                                "keywords": ""
                            },
                            "model": "",
                        }
                    }
                }
            }
        }
        baseQuery['rescore']['query']['rescore_query']['sltr']['model'] = model_name
        if gte == "":
            baseQuery['query']['multi_match']['query'] = keywords
        else:
            baseQuery['query']['bool']['must'][0]['multi_match']['query'] = keywords
        baseQuery['rescore']['query']['rescore_query']['sltr']['params']['keywords'] = keywords
        return baseQuery

    def get_data(self, index_name):
        """ Search the input string in elastic search
                 Args:
                     query_string : String to be searched in elastic search
                 Return:
                     result : returns the result came from elastic search
        """
        try:
            if self.es_client is None or not self.es_client.ping():
                self.connect()

            self.es_client.indices.refresh(index=index_name)
            search_query={
            	"_source": ["slides.shapes.paras.lines.segments.text"]
            }
            result = self.es_client.search(index=index_name, body=search_query, allow_partial_search_results=True, size=10000)
            logger.info('No. of Documents  got %d Hits:' % result['hits']['total']['value'])
            return result
        except:
            logger.exception("could not query elasticsearch")

    def set_egnyte_token(self,access_token):
        config = utils.config_parser()
        app_data = config.get('elasticsearch', 'app_data_index')
        document = {'token': access_token.decode('utf-8')}
        document_id = 'egnyte_token'
        self.insert_document(app_data, 'pptx', document_id, document)
        logger.info("Saved egnyte token to ElasticSearch")

    def get_egnyte_token(self):
        try:
            config = utils.config_parser()
            app_data = config.get('elasticsearch', 'app_data_index')
            es_obj = elasticsearch_connector.get_instance()
            search_query = {
                      "query": {
                        "terms": {
                          "_id": [ 'egnyte_token']
                        }
                      }
                    }
            if es_obj.check_if_index_exists(index_name=app_data):
                json_data = es_obj.generic_search_query(app_data, search_query)
                if len(json_data['hits']['hits']) > 0:
                    egnyte_access_token = json_data['hits']['hits'][0]['_source']['token']
                    return egnyte_access_token
            else:
                logger.info("Egnyte Token not found in Elasticsearch")
                return False
        except Exception as e:
            print(e)
            return False

    def return_index_parameter(self, doc_id, index_name, parameters):
        """ Search for the provided document ID in elastic search
                 Args:
                     doc_id : Document ID to be searched in elastic search
                 Return:
                     checksum : returns the checksum of a document if present in elastic search, else returns False
        """
        try:
            if self.es_client is None or not self.es_client.ping():
                self.connect()

            search_query = {
                "query": {
                    "match": {
                        "_id": {
                            "query": doc_id
                            }
                        }
                    }
                }

            json_data = self.es_client.search(index=index_name, body=search_query, allow_partial_search_results=True)
            all_docs = json_data['hits']['hits']
            for hits in all_docs:
                hits_source = hits.get('_source')

            index_parameters = {}
            for parameter in parameters:
                index_parameters[parameter] = hits_source.get(parameter)

            if any(value is None for value in index_parameters.values()):
                logger.info("One of the value is None")
                return False
            else:
                logger.info('File exists with required parameters')
                return index_parameters

        except:
            return False

    def generic_search_query(self, index_name, search_query, size=10000):
        """ Generic search query which can be used for multiple search operation in elastic search
                 Args:
                     index_name : Name of the index where we are searching query,
                     search_query : Search query to be searched in elastic search
                 Return:
                     response : return response for search uery
        """
        try:
            if self.es_client is None or not self.es_client.ping():
                self.connect()
            response = self.es_client.search(index=index_name, body=search_query, size=size)
            return response

        except Exception as e:
            logger.exception("Generic search query is failing")
            return False

    def return_doc_count(self, index_name):
        """ Fetch documents count from specific index in elastic search
                 Args:
                     index_name : Name of the index where we are searching query,
                 Return:
                     response : return response for search uery
        """
        try:
            if self.es_client is None or not self.es_client.ping():
                self.connect()
            response=self.es_client.cat.count(index_name, params={"format": "json"})
            if response:
                return response[0]["count"]
            else:
                return 0
        except Exception as e:
            logger.exception("Fetching document count is failed with error: %S"% str(e))
            return False


if __name__ == '__main__':
    es = elasticsearch_connector()
    # es.es_backup()
    es.restore()
