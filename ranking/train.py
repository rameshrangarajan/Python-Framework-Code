import os
from collect_features import log_features, build_features_judgments_file
from load_features import init_default_store, load_features
from log_conf import Logger
from utils import INDEX_NAME, JUDGMENTS_FILE_FEATURES, \
    FEATURE_SET_NAME, RANKLIB_JAR
from utils import ES_HOST,ES_User,ES_Passw
from requests.auth import HTTPBasicAuth
from get_training_data import get_data

def train_model(judgments_with_features_file, model_output, which_model=6):
    # java -jar RankLib-2.6.jar -ranker 6 -train sample_judgments_wfeatures.txt -save model.txt
    cmd = "java -jar %s -ranker %s -train %s -save %s -frate 1.0" % \
          (RANKLIB_JAR, which_model, judgments_with_features_file, model_output)
    Logger.logger.info("*********************************************************************")
    Logger.logger.info("*********************************************************************")
    Logger.logger.info("Running %s" % cmd)
    os.system(cmd)
    pass


def save_model(script_name, feature_set, model_fname):
    """ Save the ranklib model in Elasticsearch """
    import requests
    import json
    from urllib.parse import urljoin

    model_payload = {
        "model": {
            "name": script_name,
            "model": {
                "type": "model/ranklib",
                "definition": {
                }
            }
        }
    }

    with open(model_fname) as modelFile:
        model_content = modelFile.read()
        path = "_ltr/_featureset/%s/_createmodel" % feature_set
        full_path = urljoin(ES_HOST, path)
        print("full_path", full_path)
        model_payload['model']['model']['definition'] = model_content
        Logger.logger.info("POST %s" % full_path)
        head = {'Content-Type': 'application/json'}
        resp = requests.post(full_path, data=json.dumps(model_payload), auth = HTTPBasicAuth(ES_User,ES_Passw),headers=head,verify=False)
        Logger.logger.info(resp.status_code)
        if resp.status_code >= 300:
            Logger.logger.error(resp.text)


def parse_data_and_get_judgement():
    from judgments import Judgment
    import pandas as pd
    fileJudgments = {}

    #data = pd.read_csv("filedata.csv")
    data = get_data()

    for index, row in data.iterrows():
        #query = row["Query"]
        #id = row["Document ID"]
        #rank = row['Rank']
        query = row["search_query"]
        id = row["doc_id"]
        rank = row['grade']

        judgement_obj = Judgment(grade=rank, qid=query, keywords=query, doc_id=id)

        try:
            fileJudgments[query].append(judgement_obj)
        except KeyError:
            fileJudgments[query] = [judgement_obj]

    return fileJudgments


def training_pipeline():
    from utils import elastic_connection
    es = elastic_connection()
    file_judgments = parse_data_and_get_judgement()
    print(file_judgments)
    init_default_store()
    load_features(FEATURE_SET_NAME)
    log_features(es, judgments_dict=file_judgments, search_index=INDEX_NAME)
    build_features_judgments_file(file_judgments, filename=JUDGMENTS_FILE_FEATURES)

    for modelType in [6, 7, 9]:
    # for modelType in [0, 1, 2, 3, 4, 5, 6, 7, 8, 9]:
        Logger.logger.info("*** Training %s " % modelType)
        train_model(judgments_with_features_file=JUDGMENTS_FILE_FEATURES, model_output='model.txt',
                    which_model=modelType)
        save_model(script_name="test_%s" % modelType, feature_set=FEATURE_SET_NAME, model_fname='model.txt')

def upload_model():
    init_default_store()
    load_features(FEATURE_SET_NAME)
    save_model(script_name="test_9", feature_set=FEATURE_SET_NAME, model_fname='model.txt')
    
if __name__ == "__main__":
   training_pipeline()
