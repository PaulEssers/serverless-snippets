# -*- coding: utf-8 -*-
"""
Created on Fri Feb 28 07:51:38 2020

@author: 251088
"""

import io
import os
from datetime import datetime


import pandas as pd
import json
import logging
import boto3

from flask import Flask, request

app = Flask(__name__)
app.config["DEBUG"] = True

# Set up logging
boto3.set_stream_logger(name = 'boto3.resources', 
                        level = logging.DEBUG, 
                        format_string = f'%(asctime)s %(levelname)s %(message)s')
logger = logging.getLogger()

logger.info('Starting')

s3 = boto3.client('s3')
bucket_name = "bucket-of-panda-goo"
# lb = boto3.client('lambda')
# arn = os.environ['ARN_PREFIX']

# Create the bucket if is doesn't exist already.
s3_resource = boto3.resource('s3') # this is easier with resource than with s3_client.list_buckets()
if not s3_resource.Bucket(bucket_name) in s3_resource.buckets.all():
    bucket = s3.create_bucket(Bucket = bucket_name, 
                              CreateBucketConfiguration = {'LocationConstraint': os.environ['REGION'] } , 
                              ACL = 'public-read') # You might not want to do this in real life



@app.route('/', methods=["POST"])
def saving():
    """
    Will save any input to S3 as a csv and a JSON and give back the filenames.
    """
    
    logger.debug('Entrypoint')
    # for testing purposes:
    # with open('input.json') as json_file:
    #     req_data = json.load(json_file)
    req_data = request.get_json()
    
    
    if 'filename' in req_data.keys():
        filename_excel = req_data['filename'] + '.xlsx'
        filename_json  = req_data['filename'] + '.json'
    else:
        now = datetime.now().strftime("%Y%m%d_%H%M")
        filename_excel = now + '_test.xlsx'
        filename_json  = now + '_test.json'

    
    # The excel function takes a dict of pandas dataframes.    
    logger.debug('Saving Excels')
    df1 = pd.DataFrame(req_data['firsttable'])
    df2 = pd.DataFrame(req_data['secondtable'])
    dfs = {'firsttable': df1, 'secondtable': df2} # multi-tab excel
    Excel_resp = save_excel_S3(dfs, bucket_name, filename_excel)
    
    # The JSON function takes a dict of dicts.        
    # req_data is already in dict format, convert pandas dataframes to a 
    # (dict of) dict(s) before calling this function.
    logger.debug('Saving JSON')
    JSON_resp = save_JSON_S3(req_data, bucket_name, filename_json)
    
    return {'Excel': Excel_resp, 'JSON': JSON_resp}

@app.route('/load/<string:filename>', methods=["GET"])
def loading(filename):
    """
    Will load JSON file from S3. 
    
    Not sure how to load excel, but excel should in any case only be used to
    send files to the end user.
    """
        
    return load_JSON_S3(bucket_name, filename)



def save_excel_S3(dfs, bucket, filename = 'tmp.xlsx'):
    """
    Save a dict of pandas.DataFrames to S3 as a multi-tabbed excel file.

    Parameters
    ----------
    dfs : dict
        Dictonary of pd.DataFrames, or a single pd.DataFrame. Dict keys will
        become the sheet names in the excel
    bucket : string
        Name of the bucket in which to save the file.
    filename : obj, optional
        Name and path of the file to save. The default is 'tmp.xlsx'.

    Returns
    -------
    Dict
        The response from put_object(), with an additional ['ObjectUrl'] giving
        the full URL of the object created.
    """
    
    # If only one dataframe is given, change it to a dict
    if isinstance(dfs, pd.DataFrame):
        dfs = {'sheet1': dfs}
    

    # Convert dataframe to bytes stream
    with io.BytesIO() as output:
       with pd.ExcelWriter(output, engine='xlsxwriter') as writer:
          for key, df in dfs.items():
              if not (isinstance(df, pd.DataFrame) | isinstance(df, pd.Series)):
                  continue # Make sure it does not crash if there is a non-dataframe in there.
              df.to_excel(writer, sheet_name = key)
       data = output.getvalue()    
           
    response = s3.put_object(Bucket = bucket, Key = filename, Body = data) # ACL = 'public-read'

    if response['ResponseMetadata']['HTTPStatusCode'] == 200:
        # If it succeeded, append the file url to the response   
        bucket_location = s3.get_bucket_location(Bucket=bucket)
        object_url = "https://s3-{0}.amazonaws.com/{1}/{2}".format(bucket_location['LocationConstraint'], bucket, filename)
        response['ObjectUrl'] = object_url
       
    return response


def save_JSON_S3(json_data, bucket, filename):
    """
    Saves a python Dict as a JSON file on S3.

    Parameters
    ----------
    json_data : Dict
        DESCRIPTION.
    bucket : TYPE
        DESCRIPTION.
    filename : TYPE
        DESCRIPTION.

    Returns
    -------
    None.

    """
    
    bytes_data = bytes(json.dumps(json_data).encode('UTF-8'))
    response = s3.put_object(ACL = 'public-read', Bucket = bucket, Key = filename,
                             Body = bytes_data )
    
    if response['ResponseMetadata']['HTTPStatusCode'] == 200:
        # If it succeeded, append the file url to the response   
        bucket_location = s3.get_bucket_location(Bucket=bucket)
        object_url = "https://s3-{0}.amazonaws.com/{1}/{2}".format(bucket_location['LocationConstraint'], bucket, filename)
        response['ObjectUrl'] = object_url
       
    return response


def load_JSON_S3(bucket, filename):
    """
    Load a JSON file from S3 as a python dict.

    Parameters
    ----------
    bucket : string
        Name of the bucket.
    filename : string
        path of the file.

    Returns
    -------
    dict
    """
    
    file_content = s3.get_object(Bucket = bucket, Key = filename)['Body'].read().decode('utf-8')
    return json.loads(file_content)


if __name__== '__main__':
    app.run()