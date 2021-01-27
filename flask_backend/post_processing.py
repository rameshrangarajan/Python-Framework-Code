import re
import os
import objectpath
from user_feedback_logger import user_feedback_logger
import utils
from logger import log
from datetime import datetime
logger = log.getLogger()


class ResponseCreator():
    def create_response(self, json_data, userID, page_number):
        data = []
        start = datetime.now()
        like_dislike_status = user_feedback_logger.get_feedback_count_per_user_for_all_documents(userID)
        config = utils.config_parser()
        number_of_results_per_page = int(config.get('elasticsearch', 'number_of_results_per_page'))
        from_record = (page_number-1)*number_of_results_per_page
        for hits in json_data['hits']['hits']:
            keyword_list = {}
            if 'highlight' in hits:
                if 'slides.shapes.paras.lines.segments.text' in hits['highlight']:
                    for string in hits['highlight']['slides.shapes.paras.lines.segments.text']:
                        exclude_tags = re.compile(r"(<strong>|</strong>)")
                        final_str = re.sub(exclude_tags, '', string)
                        keyword_list[final_str] = string
            sorted_keyword_list = dict(sorted(keyword_list.items(), reverse=True))

            hits_source = hits.get('_source')
            file_location = hits_source.get('url')
            score = hits.get('_score')
            doc_id = hits.get('_id')
            file_name = os.path.basename(hits_source.get('file_name'))
            owned_by = hits_source.get('created_by')
            if owned_by == "":
                owned_by = "Unknown"
            date_created = hits_source.get('created_time')
            modified_by = hits_source.get('modified_by')
            if modified_by == "":
                modified_by = "Unknown"
            modified_date = hits_source.get('modified_time')
            source_path = hits_source.get('source_path')
            num_downloads = hits_source.get('num_downloads')
            title = hits_source.get('title')
            num_likes = hits_source.get('num_likes')
            num_dislikes = hits_source.get('num_dislikes')
            if like_dislike_status:
                if doc_id in like_dislike_status.keys():
                    liked_status = like_dislike_status[doc_id][0]
                    disliked_status = like_dislike_status[doc_id][1]
                else:
                    liked_status = False
                    disliked_status = False
            else:
                liked_status = False
                disliked_status = False
            indexing_time = hits_source.get('indexing_time')
            
            occurrences = []
            author_occurrences = []
            is_occurrence = False

            if 'slides' in hits_source:
                for slides in hits_source['slides']:
                    thumbnail_large = slides.get('thumbnail_large')
                    thumbnail_small = slides.get('thumbnail_small')
                    tree = objectpath.Tree(slides)
                    page_num = slides.get('page_number')
                    page_id = slides.get('page_id')
                    for segment_text in tree.execute("$..text"):
                        for key in sorted_keyword_list.keys():
                            if key in segment_text:
                                # tag_inserted_text = re.sub(re.escape(key), sorted_keyword_list[key], r"{}".format(segment_text))
                                tag_inserted_text = segment_text.replace(key, sorted_keyword_list[key])

                                is_occurrence = True
                                occurrences.append(
                                        {'page_no': page_num, 'page_id': page_id, "thumbnail_large": thumbnail_large,
                                         "thumbnail_small": thumbnail_small, 'content': [tag_inserted_text]})
                                break
                    if is_occurrence == False:
                        author_occurrences.append(
                            {'page_no': page_num, "thumbnail_large": thumbnail_large,
                             "thumbnail_small": thumbnail_small, 'content': ""})


            if is_occurrence is False:
                occurrences = author_occurrences

            # if len(occurrences) != 0:
            data.append({"doc_id": doc_id,
                         "file_name": file_name,
                         "score": score,
                         "title": title,
                         "source_path": source_path,
                         "url": file_location,
                         "created_by": owned_by,
                         "created_date": date_created,
                         "modified_by": modified_by,
                         "modified_date": modified_date,
                         "num_downloads": num_downloads,
                         "num_likes": num_likes,
                         "num_dislikes": num_dislikes,
                         "liked_status": liked_status,
                         "disliked_status": disliked_status,
                         "indexing_time": indexing_time,
                         "occurrences": occurrences })
        response = []
        response.append(data)
        total_search_result_processing_time = (datetime.now() - start).total_seconds()
        logger.info("****** total_post_processing_time *******: %s" % total_search_result_processing_time)
        return response

