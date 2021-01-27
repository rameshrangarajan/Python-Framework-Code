from log_conf import Logger
from datetime import datetime
import pandas as pd
from judgments import Judgment
from train import save_model, train_model

from collect_features import log_features, build_features_judgments_file
from load_features import init_default_store, load_features
from log_conf import Logger
from utils import JUDGMENTS_FILE, INDEX_NAME, JUDGMENTS_FILE_FEATURES, \
    FEATURE_SET_NAME, RANKLIB_JAR
import os

baseQuery = {
  "query": {
      "multi_match": {
          "query": "test",
          "fields": ["slides.shapes.paras.lines.segments.text", "slides.title", "title", 'created_by']
       }
   },
  "rescore": {
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
   },
    "ext": {
        "ltr_log": {
            "log_specs": {
                "name": "log_entry1",
                "rescore_index": 0
            }
        }
    }
}


def ltr_query(keywords, model_name):
    import json
    baseQuery['rescore']['query']['rescore_query']['sltr']['model'] = model_name
    baseQuery['query']['multi_match']['query'] = keywords
    baseQuery['rescore']['query']['rescore_query']['sltr']['params']['keywords'] = keywords
    Logger.logger.info("%s" % json.dumps(baseQuery))
    return baseQuery


if __name__ == "__main__":
    from utils import INDEX_NAME, elastic_connection, query_string, MODEL
    es = elastic_connection()
    model_num = "test_6"
    queries = ["vaibhav"]
    qid = 0
    for query in queries:
        aggregated_download_logs = "aggregated_download_logs"
        find_no_of_download_query = {
                        "query": {
                            "match": {
                                "key": "Xoriant_AWS_Expertise"
                            }
                        }
                    }

        data_df = []

        if query == "blockchain":
            qid = 1
        if query == "oracle":
            qid = 2
        if query == "aws":
            qid = 3
        if query == "vaibhav":
            qid = 4

        if MODEL == "true":
            results = es.search(index=INDEX_NAME, body=ltr_query(query, model_num))
        else:
            results = query_string(es, query, INDEX_NAME)
        today = datetime.now().date()

        fileJudgement = {}
        for result in results['hits']['hits']:
            source = result['_source']
            fields = result['fields']
            id = result['_id']
            modified_date = datetime.strptime(source['modified_time'].split("T")[0], '%Y-%m-%d').date()
            daydiff = str((today - modified_date).days)
            find_no_of_download_query["query"]["match"]["key"] = id

            # download_res = es.search(index=aggregated_download_logs, body=find_no_of_download_query)
            # hits = download_res["hits"]["hits"]
            #
            # if len(hits) <= 0:
            #     no_of_times_downloaded = 0
            # else:
            #     no_of_times_downloaded = hits[0]["_source"]["doc_count"]
            # print("qid: %s # %s download: %s datediff %s" % (qid, id, str(no_of_times_downloaded), daydiff))

            features_values = fields['_ltrlog'][0]['log_entry1']

            features_1_value = 0
            features_2_value = 0
            features_3_value = 0
            features_4_value = 0
            features_5_value = 0

            import math
            for item in features_values:
                if 'value' in item:
                    # print(item['name']+ " -- "+ str(item['value']))
                    if item['name'] == "1":
                        features_1_value = item['value']
                    if item['name'] == "2":
                        features_2_value = item['value']
                    if item['name'] == "3":
                        features_3_value = item['value']
                    if item['name'] == "4":
                        features_4_value = item['value']
                    if item['name'] == "5":
                        features_5_value = item['value']

    # 1: keyword present in description
    # 2: keyword present in slide title
    # 3: keyword present in deck title
    # 4: recency
    # 5: no of downloads

            rank = features_1_value + features_2_value + features_3_value + features_4_value + (features_5_value/100)
            final_rank = math.floor(rank/3)

            # print("%s qid: %s # %s download: %s datediff %s" % (final_rank, qid, id, str(no_of_times_downloaded), daydiff))
            # print("%s qid: %s # %s download: %s datediff: %s 1:%s 2:%s 3:%s 4:%s 5:%s" %
            #       (final_rank, qid, id, str(no_of_times_downloaded), daydiff,
            #        features_1_value, features_2_value, features_3_value, features_4_value, features_5_value))


            # judgement_obj = Judgment(grade=final_rank, qid=qid, keywords=query, doc_id=id)
            #
            # try:
            #     fileJudgement[qid].append(judgement_obj)
            # except KeyError:
            #     fileJudgement[qid] = [judgement_obj]
            print(id)
            single_data=[]
            single_data.append(qid)
            single_data.append(query)
            single_data.append(id)
            # single_data.append(str(no_of_times_downloaded))
            single_data.append(daydiff)
            single_data.append(features_1_value)
            single_data.append(features_2_value)
            single_data.append(features_3_value)
            single_data.append(features_4_value)
            single_data.append(features_5_value)
            single_data.append(final_rank)
            data_df.append(single_data)
            # Logger.logger.info(str(result["_id"] + " ---- " + daydiff + " ---- " + source['title']))

        df = pd.DataFrame(data_df, columns=['Qid', 'Query', 'Document ID', "Days Old",
                                            "Feature 1 value", "Feature 2 value", "Feature 3 value",
                                            "Feature 4 value","Feature 5 value", "Rank"])
        print(df.head())
        # if os.path.exists('filedata.csv'):
        #     with open('filedata.csv', 'a', newline='') as f:
        #         df.to_csv(f, header=False, index=False)
        # else:
        #     with open('filedata.csv', 'a', newline='') as f:
        #         df.to_csv(f, index=False)

        # print(fileJudgement)
        # init_default_store()
        # load_features(FEATURE_SET_NAME)
        # log_features(es, judgments_dict=fileJudgement, search_index=INDEX_NAME)
        # build_features_judgments_file(fileJudgement, filename=JUDGMENTS_FILE_FEATURES)
        # # Train each ranklib model type
        # # modelType =6
        # for modelType in [0, 1, 2, 3, 4, 5, 6, 7, 8, 9]:
        #     # 0, MART
        #     # 1, RankNet
        #     # 2, RankBoost
        #     # 3, AdaRank
        #     # 4, coord Ascent
        #     # 6, LambdaMART
        #     # 7, ListNET
        #     # 8, Random Forests
        #     # 9, Linear Regression
        #     Logger.logger.info("*** Training %s " % modelType)
        #     train_model(judgments_with_features_file=JUDGMENTS_FILE_FEATURES, model_output='model.txt',
        #                 which_model=modelType)
        #     save_model(script_name="test_%s" % modelType, feature_set=FEATURE_SET_NAME, model_fname='model.txt')
