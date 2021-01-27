import os, time
import glob
import olefile
import pptx
from pptx import Presentation
# This file is for changing pptx files' created by and modified time based on the created by and modification time  of ppt files.
# Note this code is for 2 types of files ".ppt" and ".pptx"
def get_creators_and_modified(list_of_ppt_files):
    creators_of_ppt = []
    modified_time_of_ppt = []

    for file in list_of_ppt_files:
            if olefile.isOleFile(file):
                ole = olefile.OleFileIO(file)
                meta = olefile.OleFileIO.get_metadata(ole)
                creators_of_ppt.append(meta.last_saved_by)
                modified_time_of_ppt.append(meta.last_saved_time)
            else:
                print(file, "is not an OLE file")
    return creators_of_ppt,modified_time_of_ppt




def create_new_pptx_files(file_path,list_of_pptx_files,creators_of_ppt,modified_time_of_ppt):
    path_new_dir = file_path + "\\newdata"
    if not os.path.isdir(path_new_dir):
        os.mkdir(file_path + "\\newdata")
    count_of_pptx_files = 0
    for file in list_of_pptx_files:
        prs = Presentation(file)
        prs.core_properties.last_modified_by=creators_of_ppt[count_of_pptx_files].decode("utf-8")
        prs.core_properties.modified=modified_time_of_ppt[count_of_pptx_files]
        s = file_path + "\\newdata" + file.replace(file_path,'')
        prs.save(s)
        count_of_pptx_files+=1
    return count_of_pptx_files

if __name__ == '__main__':
    start_time = time.time()
    file_path = os.getcwd() # path of ppt files which are converted to pptx but date modified and created by are changed.
    list_of_pptx_files = glob.glob(file_path + "/*.pptx")
    path_of_ppt_files = r'C:\Users\bailmare_sa\Desktop\ppt_files\ppt' # path of ppt files which has original date_modified and created by
    list_of_ppt_files = glob.glob(path_of_ppt_files + "/*.ppt")
    creators_of_ppt,modified_time_of_ppt=get_creators_and_modified(list_of_ppt_files)
    count_of_pptx_files=create_new_pptx_files(file_path,list_of_pptx_files,creators_of_ppt,modified_time_of_ppt)
    print("All files are changed with previous Cretors and Moditification Time and took",time.time()-start_time,"seconds for",count_of_pptx_files,"files")
