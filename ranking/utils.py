import configparser
import elasticsearch
from requests.auth import HTTPBasicAuth

__all__ = ["ES_AUTH", "ES_HOST", "elastic_connection", "RANKLIB_JAR", "BASEPATH_FEATURES", "FEATURE_SET_NAME",
           "JUDGMENTS_FILE", "JUDGMENTS_FILE_FEATURES", "INDEX_NAME", "expert_feedback_index_name"]

config = configparser.ConfigParser()
config.read('settings.cfg')

config_set = 'DEFAULT'

ES_HOST = config[config_set]['ESHost']
es_api_key_id = config[config_set]['es_api_key_id']
es_api_key = config[config_set]['es_api_key']

ES_User = config[config_set]['ES_User']
ES_Passw = config[config_set]['ES_Passw']
if 'ESUser' in config[config_set]:
    auth = (config[config_set]['ESUser'], config[config_set]['ESPassword'])
    ES_AUTH = HTTPBasicAuth(*auth)
else:
    auth = None
    ES_AUTH = None

RANKLIB_JAR = config[config_set]['RanklibJar']
BASEPATH_FEATURES = config[config_set]['BasepathFeatures']
FEATURE_SET_NAME = config[config_set]['FeatureSetName']
JUDGMENTS_FILE = config[config_set]['JudgmentsFile']
JUDGMENTS_FILE_FEATURES = config[config_set]['JudgmentsFileWithFeature']
INDEX_NAME = config[config_set]['IndexName']
MODEL = config[config_set]['model']
expert_feedback_index_name = config[config_set]['expert_feedback_index_name']

def elastic_connection(url=None):
    if url is None:
        url = ES_HOST
    return elasticsearch.Elasticsearch([url],api_key=(es_api_key_id,es_api_key),scheme='https',verify_certs=False)

def query_string(es_client, query_string, index_name):
        """ Search the input string in elastic search
                 Args:
                     query_string : String to be searched in elastic search
                 Return:
                     result : returns the result came from elastic search
        """
        try:
            es_client.indices.refresh(index=index_name)
            search_query={
                          "query": {
                            "bool": {
                              "should": [
                                {
                                  "match" : {
                                    'slides.shapes.paras.lines.segments.text': query_string
                                  }
                                },
                                {
                                  "match" : {
                                    'title' : query_string
                                  }
                                }
                              ]
                            }
                          }
                        }
            result = es_client.search(index=index_name, body=search_query, allow_partial_search_results=True)
            return result
        except:
            print("could not query elasticsearch")