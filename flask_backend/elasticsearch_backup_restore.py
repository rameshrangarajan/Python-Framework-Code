from elasticsearch_connector import elasticsearch_connector
import utils
from logger import log
from datetime import datetime
import os, sys
import shutil
import errno
logger = log.getLogger()

class ES_Backup_Restore():
    def backup(backup_thumbnail="True"):
        try:
            date = str(datetime.today().date())
            config = utils.config_parser()
            host = config.get('elasticsearch', 'host')
            port = config.get('elasticsearch', 'port')
            es_dump_auth = config.get('elasticsearch', 'es_dump_auth')
            index_list = config.get('elasticsearch', 'backup_indices')
            gcs_bucket_name = config.get('elasticsearch', 'gcs_bucket_name')
            backup_to_gcs = config.get('elasticsearch', 'backup_to_gcs')
            thumbnail_path = config.get('generic', 'thumbnail_path')
            input_ip = 'https://' + host + ":" + port
            output_path = "./esbackup_" + date
            if not os.path.exists(output_path):
                os.mkdir(output_path)
            else:
                output_path = output_path+datetime.now().strftime("_%H-%M-%S")
                os.mkdir(output_path)

            if backup_thumbnail == "True":
                thumbnail_output_path = output_path + '/thumbnail'
                if os.path.isdir(thumbnail_output_path):
                    shutil.rmtree(thumbnail_output_path)
                logger.info("Creating backup of thumbnails...")
                try:
                    shutil.copytree(thumbnail_path, thumbnail_output_path)
                except OSError as e:
                    # If the error was caused because the source wasn't a directory
                    if e.errno == errno.ENOTDIR:
                        shutil.copy(thumbnail_path, output_path)
                    else:
                        logger.exception('Directory not copied. Error: %s' % e)

                if os.path.exists(thumbnail_output_path):
                    shutil.make_archive(thumbnail_output_path, 'zip', thumbnail_output_path)

                if os.path.exists(thumbnail_output_path):
                    shutil.rmtree(thumbnail_output_path)
            else:
                logger.info("Thumbnails backup is not created.")

            for index in index_list.split(','):
                logger.info("Creating es_backup for index %s" % index)
                command = "NODE_TLS_REJECT_UNAUTHORIZED=0 elasticdump --input=" + input_ip + "/" + index + " --headers '{\"Authorization\":\"Basic " + es_dump_auth + "\"}'" + " --output=" + output_path + "/" + index + ".json --type=data"
                os.system(command)

            if backup_to_gcs == 'true':
                os.system("gsutil cp -r " + output_path + " gs://" + gcs_bucket_name)

        except Exception as e:
            logger.exception("Elasticsearch es_backup failed")

    def restore(backup_path, restore_thumbnail="True"):
        try:
            config = utils.config_parser()
            host = config.get('elasticsearch', 'host')
            port = config.get('elasticsearch', 'port')
            es_dump_auth = config.get('elasticsearch', 'es_dump_auth')
            doc_type = config.get('elasticsearch', 'doc_type')
            index_list = config.get('elasticsearch', 'backup_indices')

            output_ip = 'https://' + host + ":" + port

            for index in index_list.split(','):
                logger.info("Restoring index %s"%index)
                command = "NODE_TLS_REJECT_UNAUTHORIZED=0 elasticdump --input=" + backup_path + "/" + index + ".json" +" --headers '{\"Authorization\":\"Basic "+es_dump_auth+"\"}'"+ "   --output=" + output_ip + \
                          " --type=data --output-index=" + index + "/" + doc_type
                os.system(command)

            if restore_thumbnail == "True":
                dest_thumbnail_folder = config.get('generic', 'thumbnail_path')
                source_thumbnail_folder = backup_path+'/thumbnail.zip'
                if os.path.exists(dest_thumbnail_folder):
                    shutil.rmtree(dest_thumbnail_folder)

                shutil.unpack_archive(source_thumbnail_folder, dest_thumbnail_folder, 'zip')
                logger.info("Thumbnails are restored successfully.")
            else:
                logger.info("Thumbnails are not restored.")


        except Exception as e:
            logger.exception("Elasticsearch es_backup failed")


if __name__ == '__main__':
    # if sys.argv[1] == 'backup':
    #     ES_Backup_Restore.backup(sys.argv[2])
    # elif sys.argv[1] == 'restore':
    #     ES_Backup_Restore.restore(sys.argv[2], sys.argv[3])
    # globals()[sys.argv[1]](sys.argv[2])
    # ES_Backup_Restore.restore('./esbackup_2020-01-23', False)
    ES_Backup_Restore.backup("True")