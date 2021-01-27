import utils
import os
import glob
import time
import re
import subprocess
from logger import log

logger = log.getLogger()

class thumbnail_generator():
    def generate_thumbnail_image(path_to_file, thumbnail_name):
        """Extract the image for each slide of pptx
                       Args:
                           path_to_file (str): path of pptx file
                           thumbnail_name : name of the image
                       Return:
                           sorted list of thumbnails paths created for each slide of ppt"""
        es_config = utils.config_parser()
        thumbnail_path = es_config.get('generic', 'thumbnail_path')+thumbnail_name

        # Check if thumbnail directory exists. If not exist create new directory
        if not os.path.exists(thumbnail_path):
            os.makedirs(thumbnail_path)

        # Get thumbnail size from config.txt
        thumbnail_size_smaller = es_config.get('generic', 'thumbnail_size_smaller')
        thumbnail_size_larger = es_config.get('generic', 'thumbnail_size_larger')
        export_hidden_slides = es_config.get('generic','parse_hidden_slides')

        # Extract thumbnail for both sizes for each slide of a ppt and store it in thumbnail_path
        try:
            if thumbnail_generator.convert_pptx_to_pdf_using_unoconv(path_to_file, thumbnail_path, export_hidden_slides):
                small_thumbnail_sorted_list = thumbnail_generator.convert_pdf_to_thumbnail(thumbnail_path, thumbnail_size_smaller, 'small')
                large_thumbnail_sorted_list = thumbnail_generator.convert_pdf_to_thumbnail(thumbnail_path, thumbnail_size_larger, 'large')
            else:
                logger.exception("pdf creation is failed for %s document"%path_to_file)
                return [],[]
        except Exception as e:
            logger.exception("Thumbnail generation is failed for %s with error %s " %(thumbnail_path, str(e)))
            return [],[]

        # Remove the pdf file
        for f in glob.glob(thumbnail_path + '/*.pdf'):
            os.remove(f)
        return large_thumbnail_sorted_list, small_thumbnail_sorted_list

    def convert_pdf_to_thumbnail(thumbnail_path, thumbnail_size, thumbnail_type):
        thumbnail = '"' + thumbnail_path + '/page_%d_' + thumbnail_type + '.jpg"'
        # This command converts pdf into thumbnail for each slide and store it in thumbnail_path
        try:
            thumbnail_process = subprocess.Popen(
                'convert "' + glob.glob(thumbnail_path + '/*.pdf')[0] + '" -resize ' + thumbnail_size + ' -normalize -auto-level -quality 100 -background white ' + thumbnail,
                stdout=subprocess.PIPE, shell=True)
            thumbnail_process.wait()
        except Exception as e:
            logger.exception("Thumbnail generation is failed for %s with error %s " % (thumbnail_path, str(e)))

        thumbnail_list = glob.glob(thumbnail_path + '/*' + thumbnail_type + '.jpg')

        # Sort the list of thumbnails path
        if thumbnail_list:
            return utils.sorted_nicely(thumbnail_list)
        else:
            return []

    # Function converts pptx into pdf having option to include/exclude hidden slides using unoconv
    def convert_pptx_to_pdf_using_unoconv(pptx_path, pdf_path, export_hidden_slides):
        try:
            cmd = 'unoconv -f pdf -e ExportHiddenSlides=' + export_hidden_slides + ' -o "' + pdf_path + '/converted_pdf.pdf"  -I pptx "' + pptx_path + '"'
            resp_code = subprocess.call(cmd, timeout=120, shell=True)
            logger.info("Response for process: %s"%resp_code)
            if int(resp_code) == 0:
                if os.path.exists(pdf_path + '/converted_pdf.pdf'):
                    return True
                else:
                    return False
            else:
                return False
        except Exception as e:
            logger.exception("pdf creation is failed for %s with error %s " % (pdf_path, str(e)))
            return False

    # Function converts pptx into pdf using libreoffice library (libreoffice does not provide option to include hidden slides)
    def convert_pptx_to_pdf_using_libreoffice(pptx_path, pdf_path):
        try:
            pdf_process = subprocess.Popen('libreoffice --headless --invisible --convert-to pdf "' + pptx_path + '"  --outdir "' + pdf_path + '" ', stdout=subprocess.PIPE, shell=True)
            pdf_process.wait()
        except Exception as e:
            logger.exception("pdf creation is failed for %s with error %s " % (pdf_path, str(e)))


# if __name__ == '__main__':
    # test = thumbnail_generator()
    # thumbnail_generator.test_thumbnail_generator()
