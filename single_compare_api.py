from flask import Flask,request
from flask_restful import Api,Resource,reqparse,abort
from werkzeug.exceptions import HTTPException
import urllib
import socket
import json
import os
import boto3

s3 = boto3.client("s3",
                aws_access_key_id='AKIAQKUH3YXCCK6WOL5K',
                aws_secret_access_key="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"
                 )


app = Flask(__name__)
api = Api(app)

# pull config json from s3
config_json = open('/Users/nivedithahebbar/Desktop_Items/PCR/config.json','r')
config_dict = json.load(config_json)

print("NEXTGEN-RESTFUL-API")


class config_api(Resource):
    """ Resource for config response. It sends json formatted data of config file"""
    def __init__(self, **kwargs):
        self.win_name = kwargs['win_name']

    def get(self):
        try:
            return config_dict['results'][self.win_name]
        except Exception as e:
            return(e)

class compare_api(Resource):
    """ Resource for compare api. GET request renders the compare json created in comparison_json and POST
    request takes the files from client machine, compares it with S3 data and returns a dictionary of files
    that needs to be uploaded to the S3"""
    def __init__(self, **kwargs):
        self.bucket_name = kwargs['bucket_name']
        self.win_name = kwargs['win_name']


    def post(self):
        try:
            file_data = request.get_json(force=True)
            key = self.win_name+'/'+file_data['file_name']
            print(file_data)
            try:
                s3_file = s3.head_object(Bucket=self.bucket_name, Key=key)
                S3_metadata = s3_file['Metadata']
                print(S3_metadata)
                if (S3_metadata['last_modified_date'] == file_data['last_modified_date'] and S3_metadata['file_size'] == file_data['file_size'] and S3_metadata['file_md5'] == file_data['file_md5']) :
                    print("same to same")
                    return({"status":"file exists"},200)
                else:
                    return({"status":"upload"},200)
                
            except:
                print('not in S3')
                return({"status":"upload"},200)

        except HTTPException as e:
            return(e)

class upload_api(Resource):
    """ Upload recource class the does the task of uploading 
    each file with it's metadata to the S3 bucket that has been sent
    by the client """
    def __init__(self, **kwargs):
        self.win_name = kwargs['win_name']
        self.bucket_name = kwargs['bucket_name']
    def post(self):
        try:
            file = request.files['file']
            file_content = file.read()
            filename = self.win_name+"/"+ request.form['file_name']
            if file:
                s3.put_object(
                    Body = file_content,
                    Bucket = self.bucket_name,
                    Key = filename,
                    Metadata = {
                            "file_name" : request.form['file_name'],
                            "file_md5" : request.form['file_md5'],
                            "last_modified_date" : request.form['last_modified_date'],
                            "file_size" : request.form['file_size']
                    }
                    )
                msg = "Upload Done.."
            return(msg,201)
        except HTTPException as e:
            return(e)

@app.errorhandler(HTTPException)
def handle_exception(e):
    """Return JSON instead of HTML for HTTP errors."""
    # start with the correct headers and status code from the error
    response = e.get_response()
    # replace the body with JSON
    response.data = json.dumps({
        "code": e.code,
        "name": e.name,
        "description": e.description,
    })
    response.content_type = "application/json"
    return response

class healthcheck_api(Resource):
    """ Returns status code of the application """
    def __init__(self, **kwargs):
        self.status = 200

    def get(self):
        return self.status

""" Creates resource link for each machine present in the config file and adds it to the respective resource class.
Also calls the comparison_json function for the creation of compare json """
api.add_resource(healthcheck_api,"/healthcheck/",resource_class_kwargs={},endpoint = 'healthcheck')
for win_name in config_dict['results']:
    BUCKET_NAME = config_dict['results'][win_name]["Target_files"][0]['bucket']
    actual_machine_name = config_dict['results'][win_name]["actual_machine_name"]
    api.add_resource(config_api,"/config/"+win_name,resource_class_kwargs={ 'win_name': win_name },endpoint = 'config'+'_'+win_name)
    api.add_resource(upload_api,"/upload/"+win_name,resource_class_kwargs={ 'win_name': win_name, 'bucket_name': BUCKET_NAME},endpoint = 'upload'+'_'+win_name)

    #for files in config_dict['results'][win_name]['source_files']:
        #path = files['location'].replace('/','_')
    api.add_resource(compare_api,"/compare/"+win_name,resource_class_kwargs={'bucket_name': BUCKET_NAME,'win_name': win_name}
    ,endpoint = 'compare'+'_'+win_name)


if __name__ == '__main__':
    app.run(debug=True)