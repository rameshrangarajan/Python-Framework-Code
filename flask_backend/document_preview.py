from elasticsearch_connector import elasticsearch_connector
import utils

class document_preview():

    # This function returns the preview details for the specified document id.
    def create_document_preview_response(doc_id):
        config = utils.config_parser()
        corpus_index_name = config.get('elasticsearch', 'corpus_index_name')
        elastic_obj = elasticsearch_connector.get_instance()
        search_query = {
                        "query":
                            {
                             "match": {"_id": {"query": doc_id} }
                            },
                        "_source":
                            {
                             "includes": ["file_name","title", "url","doc_type", "created_by", "modified_by", "num_downloads", "ratings", "created_time", "modified_time","slides.page_number","slides.thumbnail_large"]
                            }
                        }
        result = elastic_obj.generic_search_query(corpus_index_name, search_query)
        if result['hits']['hits']:
            return result['hits']['hits'][0]['_source']
        else:
            return {}


