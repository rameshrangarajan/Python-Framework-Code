# -*- coding: utf-8 -*-
"""
Created on Mon Aug 12 16:06:59 2019

@author: godbole_s
"""

from flask import Flask, render_template,send_from_directory
from flask import Response, request, redirect, session, make_response
from redis_connector import redis_connector
from datetime import datetime
from corpus_indexer import corpus_indexer
from index_keyword_updater import index_keyword_updater
from elasticsearch_connector import elasticsearch_connector
from post_processing import ResponseCreator
from scheduler import scheduler_job
import utils
from search_query_logger import search_query_logger
from file_download_logger import file_download_logger
from user_feedback_logger import user_feedback_logger
from expert_feedback_logger import expert_feedback_logger
from autosuggest_feedback_logger import autosuggest_feedback_logger
from document_preview import document_preview
from logger import log
from keywords_extractor import keywords_extractor
from usage_metrics import usage_metrics
from OAuth import authorization
import json
from functools import wraps
import os
import threading
from collections import OrderedDict
import re
from subjective_feedback_logger import subjective_feedback_logger

logger = log.getLogger()

app = Flask(__name__, static_url_path='')

app.secret_key = '5t6y&U*I'


@app.errorhandler(404)
def not_found(e):
    return render_template("not_found_page.html"), 404

def get_user_role(user_id):
    config = utils.config_parser()
    kmp_users_index = config.get('elasticsearch', 'kmp_users_index')
    es_obj = elasticsearch_connector.get_instance()

    if es_obj.check_if_index_exists(kmp_users_index):
        search_query = {
            "query": {
                "match":
                    {
                        "_id": user_id
                    }
            }
        }
        json_data = es_obj.generic_search_query(kmp_users_index, search_query)
        hits = json_data['hits']['hits']
        if hits:
            hit_source = hits[0].get('_source')
            user_role = hit_source.get('role')
            return user_role
        else:
            return None
    else:
        return None


def is_user_authorized(allowed_roles):
    def real_decorator(function):
        @wraps(function)
        def wrapper(*args, **kwargs):
            is_authorized = False
            is_authenticated = False

            if session is not None and session is not '' and 'unique_id' in session:
                    user_id = session['unique_id'].lower()
                    user_role = get_user_role(user_id)
                    is_authenticated = True
                    if allowed_roles is not None and user_role in allowed_roles:
                        is_authorized = True

            result = function(is_authenticated, is_authorized, *args, **kwargs)
            return result
        return wrapper
    return real_decorator


@app.before_first_request
def init_scheduler():
    scheduler_job.set_scheduler()

def check_field_validations(payload_data, field_name):
    if (payload_data[field_name] is None) or (payload_data[field_name] == "" or str(payload_data[field_name]).strip() == ""):
        return field_name + " field is missing or in incorrect format"

@app.route('/static/<path:path>')
def send_static(path):
    return send_from_directory('static', path)


@app.route('/static/thumbnail/<path:path>')
@is_user_authorized(['user', 'admin'])
def send_thumbnail(is_authenticated, is_authorized, path):
    if not is_authenticated:
        return render_template("unauthorized_user.html"), 401

    return send_from_directory('static/thumbnail', path)


@app.route("/")
@is_user_authorized(['user', 'admin'])
def index(is_authenticated, is_authorized):

    if is_authenticated:
        if is_authorized:
            return render_template("index.html")
        else:
            # Restrict user and show unauthorized page
            if 'unique_id' in session:
                logger.warning("Unauthorised user %s is trying to access the server", session['unique_id'].lower())
            return render_template("unauthorized_user.html"), 401
    else:
        auth_url = authorization().getAuthURL()
        return redirect(auth_url)


@app.route("/training")
@is_user_authorized(['user', 'admin'])
def training(is_authenticated, is_authorized):
    if is_authenticated:
        if is_authorized:
            # Continue with loading search page
            return render_template("index.html")
        else:
            # Restrict user and show unauthorized page
            if 'unique_id' in session:
                logger.warning("Unauthorised user %s is trying to access the server", session['unique_id'].lower())
            return render_template("unauthorized_user.html"), 401
    else:
        session['destination_url'] = '/training'
        auth_url = authorization().getAuthURL()
        return redirect(auth_url)


@app.route("/dashboard")
@is_user_authorized(['admin'])
def dashboard(is_authenticated, is_authorized):
    if is_authenticated:
        if is_authorized:
            # Continue with loading search page
            return render_template("index.html")
        else:
            # Restrict user and show unauthorized page
            if 'unique_id' in session:
                logger.warning("Unauthorised user %s is trying to access the server", session['unique_id'].lower())
            return render_template("unauthorized_user.html"), 401
    else:
        session['destination_url'] = '/dashboard'
        auth_url = authorization().getAuthURL()
        return redirect(auth_url)


@app.route("/callback")
def callback():
    code = request.args.get('code')
    access_token = authorization().getAccessToken(code)
    decoded_access_token = authorization().decode_jwt(access_token)
    if os.getenv('server_type') is not None and os.environ['server_type'] == 'staging':
        session['email'] = decoded_access_token['email']
    else:
        session['email'] = decoded_access_token['emailAddress']
    session['name'] = decoded_access_token['unique_name']
    session['unique_id'] = decoded_access_token['winaccountname']

    destination_url = session.pop('destination_url', '/')
    response = redirect(destination_url)

    response.set_cookie('user_name', session['name'])
    response.set_cookie('email', session['email'])

    return response


@app.route('/logout',  methods=['GET'])
def logout():
    config = utils.config_parser()
    signout_url = config.get('OAuth', 'signout_url')
    session.clear()
    response = redirect(signout_url)
    response.delete_cookie("user_name")
    response.delete_cookie("email")
    return response


def get_suggested_query_list(in_query):
    no_of_suggested_queries = 8             #no of related suggestions being returned
    redis_obj = redis_connector.get_instance()
    query = utils.clean_text(in_query)
    suggested_queries = []
    related_keys = redis_obj.query_db_with_scores(query)    #returns dictionary with suggestions as keys and rank as value
    
    if related_keys!= None:
        related_keys.pop(in_query, None)        #remove the query from related suggestions if exists
        related_keys.pop(query, None)           # remove the clean query from related suggestions if exists
        sorted_related_keys = OrderedDict((sorted(related_keys.items(), key=lambda kv: kv[1])))
        suggested_queries = list(sorted_related_keys.keys())
        return suggested_queries[:no_of_suggested_queries]
    else:
        return suggested_queries


@app.route('/search',  methods=['POST'])
@is_user_authorized(['user', 'admin'])
def matched_string_folder(is_authenticated, is_authorized):
    """ This endpoint returns the matched data
            Args : Query to be searched in the file
    """
    if not is_authorized:
        return render_template("unauthorized_user.html"), 401

    start = datetime.now()
    data_json = request.get_json()
    config = utils.config_parser()
    payload_data = {}
    payload_data['query'] = data_json.get('query')
    payload_data['query_type'] = data_json.get('query_type')
    payload_data['time_filter'] = data_json.get('time_filter')
    for field in payload_data:
        response_msg = check_field_validations(payload_data, field)
        if response_msg:
            return Response(json.dumps(response_msg), status=400, mimetype='application/json')

    in_query = data_json.get('query')
    query_type = data_json.get('query_type')
    time_filter = data_json.get('time_filter')
    if data_json.get('page_number'):
        page_number = int(data_json.get('page_number'))
    else:
        page_number = 1
    es_connect = elasticsearch_connector.get_instance()
    log_data = {}
    log_data['query_timestamp'] = datetime.utcnow()
    corpus_index_name = config.get('elasticsearch', 'corpus_index_name')
    number_of_results_per_page = int(config.get('elasticsearch', 'number_of_results_per_page'))
    start_from = (page_number - 1) * number_of_results_per_page
    elasticsearch_result = es_connect.query_string(in_query, corpus_index_name, start_from , number_of_results_per_page, time_filter)
    if isinstance(elasticsearch_result, Exception):
        return render_template("internal_server_error.html"), 500
    else:
        hits_received = elasticsearch_result['hits']['total']['value']

        if 'unique_id' in session:
            log_data.update({"userId": session['unique_id'].lower(), "response_timestamp": datetime.utcnow(), "query": in_query,
                             "number_of_hits": hits_received, "query_type": query_type, "page_number":page_number, "time_filter":time_filter})
            search_query_logger.log_search_query(log_data)

        Data = {}
        number_of_documents = es_connect.return_doc_count(corpus_index_name)
        suggested_queries = get_suggested_query_list(in_query)
        if hits_received > 0:
            data1 = ResponseCreator().create_response(elasticsearch_result, session['unique_id'].lower(), page_number)
            total_time = (datetime.now() - start).total_seconds()
            Data.update({"results": data1,
                         "search_query": in_query,
                         "num_results": hits_received,
                         "processing_time": str(total_time) + ' seconds',
                         "number_of_documents": number_of_documents,
                         "suggestions": suggested_queries})
        else:
            Data.update({"status": "Query not found in DB"})

        js = json.dumps(Data)
        resp = Response(js, status=200, mimetype='application/json')
        total_api_response_time = (datetime.now() - start).total_seconds()
        logger.info("****** total_api_response_time *******: %s" % total_api_response_time)
    return resp

@app.route('/suggest',  methods=['POST'])
@is_user_authorized(['user', 'admin'])
def suggest(is_authenticated, is_authorized):
    """ This endpoint connects to redis server and gets the matched keywords
        Args : Query to be searched in the file
        Returns : list of related keywords uploaded in redis from the mock data."""

    if not is_authorized:
        return render_template("unauthorized_user.html"), 401

    data_json = request.get_json()
    payload_data = {}
    payload_data['query'] = data_json.get('query')

    for field in payload_data:
        response_msg = check_field_validations(payload_data, field)
        if response_msg:
            return Response(json.dumps(response_msg), status=400, mimetype='application/json')

    try:
        redis_obj = redis_connector.get_instance()
        if payload_data['query']:
            query = utils.clean_text(payload_data['query'])
            related_keys = redis_obj.query_db(query)                              #we get only matched keys from redis.
            related_keywords = []
            if related_keys is not None:
                if len(related_keys) != 0:
                    for word in related_keys:
                        related_keywords.append(utils.clean_text(str(word)))
                    Data = {}
                    Data.update({"query": payload_data['query'], "related_keywords": related_keywords[:5]})
                    js = json.dumps(Data)
                    resp = Response(js, status=200, mimetype='application/json')
                else:
                    Data = {}
                    Data.update({"query": payload_data['query'], "failure": "sorry We dont have a matching keyword"})
                    js = json.dumps(Data)
                    resp = Response(js, status=200, mimetype='application/json')
            else:
                Data = {}
                Data.update({"query": payload_data['query'], "failure": "No keywords available in redis"})
                js = json.dumps(Data)
                resp = Response(js, status=200, mimetype='application/json')
    except Exception as e:
        logger.exception(e)
        resp = Response(str(e), status=400, mimetype='application/json')
    return resp


@app.route('/ingest_corpus', methods=['POST'])
@is_user_authorized(['admin'])
def index_corpus(is_authenticated, is_authorized):
    """ This endpoint will be used to insert the documents in the elastic search.
        This endpoint needs an input as path.
    """
    if not is_authorized:
        return render_template("unauthorized_user.html"), 401

    try:
        thread1 = threading.Thread(target=index_keyword_updater.update)
        thread1.start()
        resp = Response(json.dumps({'status':'Ingest corpus started'}), status=201, mimetype='application/json')
    except Exception as e:
        logger.error("ingest_corpus api is failed with error %s" % str(e))
        return render_template("internal_server_error.html"), 500
    return resp


@app.route('/ingest_files', methods=['POST'])
@is_user_authorized(['admin'])
def ingest_files(is_authenticated, is_authorized):
    """ This endpoint will be used to insert the specified documents in the elastic search.
        This endpoint needs an input as comma separated list of relative egnyte file path.
    """
    if not is_authorized:
        return render_template("unauthorized_user.html"), 401

    data_json = request.get_json()
    payload_data = {}
    payload_data['egnyte_uploaded_files'] = data_json.get('egnyte_uploaded_files')
    for field in payload_data:
        response_msg = check_field_validations(payload_data, field)
        if response_msg:
            return Response(json.dumps(response_msg), status=400, mimetype='application/json')
    try:
        thread = threading.Thread(target=corpus_indexer.index_based_on_trigger, args=payload_data['egnyte_uploaded_files'])
        thread.start()
        resp = Response(json.dumps({'status':'Ingest Files started'}), status=201, mimetype='application/json')
    except Exception as e:
        logger.error("ingest_files api is failed with error %s" % str(e))
        return render_template("internal_server_error.html"), 500
    return resp


@app.route('/log_event_file_download', methods=['POST'])
@is_user_authorized(['user', 'admin'])
def log_file_download_event(is_authenticated, is_authorized):

    if not is_authorized:
        return render_template("unauthorized_user.html"), 401

    data_json = request.get_json()
    es_connect = elasticsearch_connector.get_instance()
    payload_data = {}
    payload_data['doc_id'] = data_json.get('doc_id')
    payload_data['search_query'] = data_json.get('search_query')
    payload_data['searched_result_index'] = data_json.get('searched_result_index')

    for field in payload_data:
        response_msg = check_field_validations(payload_data, field)
        if response_msg:
            return Response(json.dumps(response_msg), status=400, mimetype='application/json')

    log_data = {}
    log_data.update({'userId': session['unique_id'].lower(), 'doc_id' : payload_data['doc_id'], 'search_query': payload_data['search_query'], 'download_timestamp': datetime.utcnow(), 'searched_result_index' : payload_data['searched_result_index']})
    logged_result = file_download_logger.log_file_download_event(log_data)
    file_download_logger.update_download_count_for_document_by_1(data_json.get('doc_id'))
    if logged_result:
        return Response(json.dumps(logged_result), status=200, mimetype='application/json')
    else:
        return Response(json.dumps({'failure': 'Could not log the file download event.'}), status = 200, mimetype = 'application/json')


@app.route('/feedback', methods=['POST'])
@is_user_authorized(['user', 'admin'])
def log_user_feedback(is_authenticated, is_authorized):

    if not is_authorized:
        return render_template("unauthorized_user.html"), 401

    data_json = request.get_json()
    payload_data = {}
    payload_data['docID'] = data_json.get('docId')
    payload_data['searchQuery'] = data_json.get('searchQuery')
    payload_data['feedback_timestamp'] = data_json.get('DateTime')
    payload_data['feedback'] = data_json.get('feedback')

    for field in payload_data:
        response_msg = check_field_validations(payload_data, field)
        if response_msg:
            return Response(json.dumps(response_msg), status=400, mimetype='application/json')

    es_connect = elasticsearch_connector.get_instance()
    log_data = {}
    response_data = {}
    response_data['liked_status'], response_data['disliked_status'] = False, False
    log_data.update({'userId': session['unique_id'].lower(), 'doc_id': payload_data['docID'], 'search_query': payload_data['searchQuery'],
                     'feedback_timestamp': payload_data['feedback_timestamp'], 'feedback': int(payload_data['feedback'])})
    response_data['doc_id'] = log_data['doc_id']

    if log_data['feedback'] == 1:
        response_data['liked_status'] = True
    elif log_data['feedback'] == -1:
        response_data['disliked_status'] = True

    logged_result = user_feedback_logger.log_feedback_event(log_data)

    if logged_result:
        response_data['num_likes'], response_data['num_dislikes'] = user_feedback_logger.update_feedback_count_for_document(data_json.get('docId'), int(data_json.get('feedback')))
        return Response(json.dumps(response_data), status=200, mimetype='application/json')
    else:
        return Response(json.dumps({'failure': 'Could not log feedback from the user'}), status=200, mimetype='application/json')


@app.route('/train', methods=['POST'])
@is_user_authorized(['user', 'admin'])
def log_expert_feedback(is_authenticated, is_authorized):

    if not is_authorized:
        return render_template("unauthorized_user.html"), 401

    training_data = request.get_json().get('train')

    for k, data_json in training_data.items():
        for field in data_json:
            response_msg = check_field_validations(data_json, field)
            if response_msg:
                return Response(json.dumps(response_msg), status=400, mimetype='application/json')
        log_data = {}
        log_data.update({'userId': session['unique_id'].lower(), 'doc_id': data_json.get('docId'), 'search_query': data_json.get('searchQuery'), 'feedback_timestamp': data_json.get('DateTime'), 'grade': data_json.get('grade')})
        logged_result = expert_feedback_logger.log_expert_feedback(log_data)
        logger.info("uploaded data to expert feedback -- %s"% str(logged_result))

    return Response(json.dumps("Expert feedback uploaded"), status=200, mimetype='application/json')


@app.route('/log_event_autosuggest_selection', methods=['POST'])
@is_user_authorized(['user', 'admin'])
def log_autosuggest_feedback(is_authenticated, is_authorized):

    if not is_authorized:
        return render_template("unauthorized_user.html"), 401

    data_json = request.get_json()
    payload_data = {}
    payload_data['search_query'] = data_json.get('search_query')
    payload_data['timestamp'] = data_json.get('timestamp')
    payload_data['autosuggest_index'] = data_json.get('autosuggest_index')
    payload_data['matched_query'] = data_json.get('matched_query')

    for field in payload_data:
        response_msg = check_field_validations(payload_data, field)
        if response_msg:
            return Response(json.dumps(response_msg), status=400, mimetype='application/json')

    log_data = {}
    log_data.update({'userId': session['unique_id'].lower(), 'search_query': data_json.get('search_query'),
         'timestamp': data_json.get('timestamp'), 'autosuggest_index': data_json.get('autosuggest_index'),
         'matched_query': data_json.get('matched_query')})
    logged_result = autosuggest_feedback_logger.log_autosuggest_feedback_event(log_data)
    if logged_result:
        return Response(json.dumps(logged_result), status=200, mimetype='application/json')
    else:
        return Response(json.dumps({'failure': 'Could not log autosuggest event.'}), status=400, mimetype='application/json')


@app.route('/preview', methods=['POST'])
@is_user_authorized(['user', 'admin'])
def preview(is_authenticated, is_authorized):
    if not is_authorized:
        return render_template("unauthorized_user.html"), 401

    data_json = request.get_json()
    response = document_preview.create_document_preview_response(data_json.get('doc_id'))
    if response:
        return Response(json.dumps(response), status=200, mimetype='application/json')
    else:
        return Response(json.dumps({'failure': 'Could not fetch document preview details.'}), status=400,
                        mimetype='application/json')


@app.route('/refresh_autosuggest_keywords_list', methods=['POST'])
@is_user_authorized(['admin'])
def refresh_autosuggest_keywords_list(is_authenticated, is_authorized):
    # This endpoint extracts keywords from search logs and from indexed documents and add them in redis.
    if not is_authorized:
        return render_template("unauthorized_user.html"), 401

    extract_keywords = keywords_extractor()
    try:
        thread1 = threading.Thread(target=extract_keywords.refresh_autosuggest_keywords_list)
        thread1.start()
        resp = Response(json.dumps({'status':'Refreshing autosuggest keywords list started'}), status=201, mimetype='application/json')
    except Exception as e:
        logger.error("refresh_autosuggest_keywords_list api is failed with error %s"% str(e))
        return render_template("internal_server_error.html"), 500
    return resp


@app.route('/update_download_count', methods=['POST'])
@is_user_authorized(['admin'])
def update_download_count(is_authenticated, is_authorized):
    # This endpoint extract doc_id and download count from "download_logs" index and modify download count of documents
    if not is_authorized:
        return render_template("unauthorized_user.html"), 401

    if file_download_logger.update_download_count_for_all_docs():
        return Response(json.dumps("Successfully updated download count"), status=200, mimetype='application/json')
    else:
        return Response(json.dumps({'failure': 'Error in updating download count'}), status=200,
                        mimetype='application/json')


@app.route('/update_ratings', methods=['POST'])
@is_user_authorized(['admin'])
def update_ratings(is_authenticated, is_authorized):
    # This endpoint extract doc_id and ratings from "user_feedback" index and modify ratings of documents
    if not is_authorized:
        return render_template("unauthorized_user.html"), 401

    if user_feedback_logger.update_ratings_for_all_docs():
        return Response(json.dumps("Successfully updated ratings"), status=200,
                        mimetype='application/json')
    else:
        return Response(json.dumps({'failure': 'Error in updating ratings'}), status=200,
                        mimetype='application/json')


@app.route('/reset_download_count', methods=['POST'])
@is_user_authorized(['admin'])
def reset_download_count(is_authenticated, is_authorized):
    # This endpoint reset download count to 0 for all indexed documents.
    if not is_authorized:
        return render_template("unauthorized_user.html"), 401

    if file_download_logger.reset_download_count_for_all_indexed_docs("num_downloads","0"):
        return Response(json.dumps("Successfully reset download count to 0 for all indexed documents"), status=200,
                        mimetype='application/json')
    else:
        return Response(json.dumps({'failure': 'Error in reseting download count'}), status=200,
                        mimetype='applicatio/json')


@app.route('/reset_ratings', methods=['POST'])
@is_user_authorized(['admin'])
def reset_ratings(is_authenticated, is_authorized):
    # This endpoint reset ratings, number of likes and dislikes to 0 for all indexed documents.
    if not is_authorized:
        return render_template("unauthorized_user.html"), 401

    if user_feedback_logger.reset_ratings_likes_dislikes_for_all_indexed_docs():
        return Response(json.dumps("Successfully reset ratings, num_likes and num_dislikes to 0 for all indexed documents"), status=200,
                        mimetype='application/json')
    else:
        return Response(json.dumps({'failure': 'Error in reseting ratings, num_likes and num_dislikes to 0'}), status=200,
                        mimetype='applicatio/json')


@app.route('/get_usage_metrics', methods=['POST'])
@is_user_authorized(['admin'])
def get_usage_metrics(is_authenticated, is_authorized):
    if not is_authorized:
        return render_template("unauthorized_user.html"), 401

    start = datetime.now()
    data_json = request.get_json()
    payload_data = {}
    payload_data['period'] = data_json.get('period')

    for field in payload_data:
        response_msg = check_field_validations(payload_data, field)
        if response_msg:
            return Response(json.dumps(response_msg), status=400, mimetype='application/json')

    response = usage_metrics.create_usage_metrics_response(data_json.get('period'))
    if response:
        total_time = (datetime.now() - start).total_seconds()
        response['processing_time'] = total_time
        return Response(json.dumps(response), status=200, mimetype='application/json')
    else:
        return Response(json.dumps({'failure': 'Error in fetching usage metrics'}), status=400,
                        mimetype='application/json')


@app.route('/subjective_feedback', methods=['POST'])
@is_user_authorized(['user', 'admin'])
def subjective_feedback(is_authenticated, is_authorized):
    if not is_authorized:
        return render_template("unauthorized_user.html"), 401

    data_json = request.get_json()
    if 'star_ratings' in data_json or 'feedback_message' in data_json:
        data_json['user_id'] = session['unique_id']
        data_json['feedback_timestamp'] = datetime.now()
        response = subjective_feedback_logger.log_subjective_feedback(data_json)
        if response:
            return Response("Subjective feedback added", status=200, mimetype='application/json')
        else:
            return Response(json.dumps({'failure': 'Could not add data to subjective feedback.'}), status=400,
                            mimetype='application/json')


@app.route('/get_queries_metrics', methods=['POST'])
@is_user_authorized(['user', 'admin'])
def get_queries_metrics(is_authenticated, is_authorized):
    if not is_authorized:
        return render_template("unauthorized_user.html"), 401

    start = datetime.now()
    response = usage_metrics.create_queries_metrics_response()
    if response:
        total_time = (datetime.now() - start).total_seconds()
        response['processing_time'] = total_time
        return Response(json.dumps(response), status=200, mimetype='application/json')
    else:
        return Response(json.dumps({'failure': 'Error in fetching queries metrics'}), status=400,
                        mimetype='application/json')


@app.route('/get_recent_documents', methods=['POST'])
@is_user_authorized(['user','admin'])
def get_recently_added_documents(is_authenticated, is_authorized):
    # This endpoint will get recently added documents from corpus index based on indexing_time parameter
    if not is_authorized:
        return render_template("unauthorized_user.html"), 401

    config = utils.config_parser()
    corpus_index = config.get('elasticsearch', 'corpus_index_name')
    es_obj = elasticsearch_connector.get_instance()
    recent_documents_name_id = []
    recently_added_documents = {
        "_source": ["source_path", "file_name", "title", "indexing_time"],
        "query": {
            "match_all": {}
        },
        "sort": [
            {
                "indexing_time": {
                    "order": "desc"
                }
            }
        ]
    }

    response = es_obj.generic_search_query(corpus_index, recently_added_documents, size=10)

    if response:
        for hits in response['hits']['hits']:
            recent_data = {}
            hits_source = hits.get('_source')
            recent_data['doc_id'] = hits.get('_id')
            recent_data['source_path'] = hits_source.get('source_path')
            recent_data['file_name'] = hits_source.get('file_name')
            title = re.sub(r'^\b(Xoriant )', '', hits_source.get('title'),flags=re.IGNORECASE).strip()
            recent_data['title'] = title
            recent_data['indexing_time'] = hits_source.get('indexing_time')
            recent_documents_name_id.append(recent_data)

    if recent_documents_name_id:
        return Response(json.dumps(recent_documents_name_id), status=200, mimetype='application/json')
    else:
        return Response(json.dumps({'failure': 'Error in getting recently added docuemnts'}), status=400,
                        mimetype='application/json')


@app.route('/get_topics', methods=['POST'])
@is_user_authorized(['user','admin'])
def get_topics(is_authenticated, is_authorized):
    # This endpoint will return trending top 10 topics
    if not is_authorized:
        return render_template("unauthorized_user.html"), 401

    config = utils.config_parser()
    topic_list = config.get('trending_topics', 'topic_list').split(",")

    if topic_list:
        return Response(json.dumps({'topics': topic_list}), status=200, mimetype='application/json')
    else:
        return Response(json.dumps({'failure': 'No topics found'}), status=204,
                        mimetype='application/json')


if __name__ == '__main__':
    app.run(host='0.0.0.0',port =5000, ssl_context=('./certs/server.crt', './certs/server.key'))
