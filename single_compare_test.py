import socket
import requests
import shutil
import json
import hashlib
import os
from datetime import datetime, timezone
import re
import logging
import concurrent.futures

logging.basicConfig(filename='thin_client_log.log', level=logging.DEBUG,
                    format='%(asctime)s:%(levelname)s:%(funcName)s:%(message)s')


# Function to create md5 checksum
def md5(path):
    """
    creates a md5 object, 
    reads the file passed to function and
    passes it to the md5 object and 
    creates a md5 checksum for the file

    """
    md5_hash = hashlib.md5()
    a_file = open(path, "rb")
    content = a_file.read()
    md5_hash.update(content)
    md5_sum = md5_hash.hexdigest()
    return md5_sum


def file_retrieve(path):
    """
    creates a dictionary for all the files 
    present inside a path and also stores 
    the files' root directory
    os.walk() recursively fetches all
    the files and folders present with a directory 
    """
    path_dict = {"file_data": []}
    for (root, directory, file) in os.walk(path):
        for i in file:
            file_name = os.path.join(root, i)
            file_partial_path = file_name.replace(path, '')
            print(file_partial_path)
            path_dict["file_data"].append({
                "file_name": file_name,
                "file_partial_path": file_partial_path})
    return path_dict


def config_data(location, configDict):
    # temporary dict to hold file metadata
    file_metadata = {"results": {"actual_machine_name": configDict["actual_machine_name"],
                                 "machine_name": configDict["machine_name"],
                                 "operating_system": configDict["operating_system"],
                                 "description": configDict["description"],
                                 "source_files": []
                                 }
                     }

    if os.path.isfile(location):
        path = location
        stats = os.stat(path)
        md5_sum = md5(path)
        last_modified = datetime.fromtimestamp(stats.st_mtime).timestamp()
        file_metadata["results"]["source_files"].append({
            'file_name': path,
            'file_partial_path': path,
            'file_size': str(stats.st_size),
            'last_modified_date': str(last_modified),
            'file_md5': md5_sum
        })
    else:
        path_dict = file_retrieve(location)
        for file in path_dict['file_data']:
            stats = os.stat(file['file_name'])
            md5_sum = md5(file['file_name'])
            last_modified = datetime.fromtimestamp(stats.st_mtime).timestamp()
            file_metadata["results"]["source_files"].append({
                'file_name': file['file_name'],
                'file_partial_path': file['file_partial_path'],
                'file_size': str(stats.st_size),
                'last_modified_date': str(last_modified),
                'file_md5': md5_sum
            })
    return file_metadata


def file_compare_and_upload(file_data):
    try:
        compare_link = "compare/" + socket.gethostname()
        file_data_json = json.dumps(file_data)
        response = requests.post("http://127.0.0.1:5000/" + compare_link, data=file_data_json)
        response.raise_for_status()
        result = response.json()
        data = file_data
        file_name = file_data['file_name']
        if result['status'] == 'upload':
            with open(file_name, 'rb') as f:
                response = requests.post("http://127.0.0.1:5000/upload/" + socket.gethostname(), data=data,
                                         files={"file": f})
                response.raise_for_status()
            logging.info('{} Uploaded'.format(file_name))
        elif result['status'] == 'file exists':
            logging.info('{} Exists'.format(file_name))
    except requests.HTTPError as err:
        logging.error('HTTP ERROR: {}'.format(err))
    except Exception as e:
        logging.error('Exception OCCURED: {}'.format(e))


def main():
    #begin_time = datetime.now()

    # fetch the machine and file path information
    base = "http://127.0.0.1:5000/"

    configAPI = requests.get(base + "config/" + socket.gethostname())
    #print(configAPI.json)
    print(socket.gethostname())
    configDict = configAPI.json()
    # print(configDict)

    # post file_metadata to compare api
    for i in configDict['source_files']:
        file_metadata = config_data(i['location'], configDict)
        # print(file_metadata)
        with concurrent.futures.ThreadPoolExecutor(max_workers=1000) as executor:
            executor.map(file_compare_and_upload, [file_data for file_data in file_metadata['results']['source_files']])
            executor.shutdown(wait=True)
        #print(datetime.now() - begin_time)

    # upload_data = S3_data(file_metadata,compareDict["results"]["source_files"])

    # with open('/Users/nivedithahebbar/Desktop/PCR/upload_data.json', 'w') as fp:
    #    json.dump(upload_data, fp,indent = 4)


if __name__ == "__main__":
    main()
