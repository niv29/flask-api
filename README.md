# flask-api

This projects main objective is to pull files from local system, compare if the file is present in S3, if the file is not present/changed since last upload, upload it to S3.

## Componets
- config file : a json file which gives the details for the machine name to upload from as well as the path to search.
- single_comapre_api : this is the flask api built on flasks restful api package that has 3 functionalities.
  - to get the configuration such as machine name from config file
  - to compare each file metadata (MD5,Size,Created time,Modified time) recieved with file present in S3 and then return a response if whether the file should be uploaded
  - to upload the recieved files to S3 bucket (Bucket information present in the config file.)
- single_compare_test : this runs on local machine to create files metadata and communicate with the api to send the appropriate files for upload.
- thin_client_log : this logs errors of single_compare_test. 
