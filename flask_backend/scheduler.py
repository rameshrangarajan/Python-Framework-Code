import atexit
import utils
from apscheduler.schedulers.background import BackgroundScheduler
from corpus_indexer import corpus_indexer
from datetime import datetime
from logger import log
from keywords_extractor import keywords_extractor
from index_keyword_updater import index_keyword_updater
from file_download_logger import file_download_logger
from elasticsearch_connector import elasticsearch_connector
from elasticsearch_backup_restore import ES_Backup_Restore
logger = log.getLogger()

class scheduler_job:

    def index_all_on_schedule():
        config = utils.config_parser()
        job_enable = config.get("scheduler", "enable").lower()

        if job_enable == "true":
            try:
                logger.info("Starting the cron job")
                es_obj = elasticsearch_connector.get_instance()
                ES_Backup_Restore.backup("True")
                index_keyword_updater.update()
                logger.info("Index All Cron job Done")

            except Exception as e:
                logger.exception("Index using schedule Exception Occurred.")
        else:
            logger.info("Scheduler job disabled")

    def index_specific_on_schedule():
        config = utils.config_parser()
        job_enable = config.get("scheduler", "enable").lower()

        if job_enable == "true":
            try:
                logger.info("Starting the cron job")
                res = corpus_indexer.index_based_on_event()
                logger.info("Index Based on Event Cron job Done")
            except Exception as e:
                logger.exception("Index for specific file using schedule Exception Occurred.")
        else:
            logger.info("Scheduler job disabled")


    def set_scheduler():
        scheduler = BackgroundScheduler({'apscheduler.timezone': 'Asia/Kolkata'})
        config = utils.config_parser()
        schedule_time = config.get("scheduler", "schedule_time")
        datetime_object = datetime.strptime(schedule_time, '%H:%M:%S')
        hour = datetime_object.hour
        minute = datetime_object.minute
        polling_time = config.get("scheduler", "egnyte_event_polling_interval")
        datetime_object_1 = datetime.strptime(polling_time, '%H:%M:%S')
        polling_interval = datetime_object_1.minute

        # Scheduler for Parsing and Indexing all documents on daily basis
        scheduler.add_job(func=scheduler_job.index_all_on_schedule, trigger="cron", hour=hour, minute=minute)
        # Scheduler for Incremental Parsing
        scheduler.add_job(func=scheduler_job.index_specific_on_schedule,trigger="interval",minutes=int(polling_interval))
        scheduler.start()
        logger.info("Scheduler set for "+str(hour) + ": "+str(minute))
        # Shut down the scheduler when exiting the app
        atexit.register(lambda: scheduler.shutdown())

if __name__ == '__main__':
    scheduler_job.index_all_on_schedule()
