# -*- coding: utf-8 -*-
"""
This is a flask app, to be uploaded to AWS through serverless. The purpose is
just to test how to pass on data from one lambda to another, as well as defining
environment variables in the serverless.yml file.
"""

import datetime
import os

from flask import Flask
import boto3
import json
import pandas as pd


app = Flask(__name__)



@app.route('/', methods=["POST", "GET"])
def entrypoint():
    
    # This function is invoked when you post a request to API gateway.
    
    lc = boto3.client('lambda')
    
    df = pd.DataFrame({'Column1': [1,2,3,4,5], 'Column2': ['a','b','c','d','e']})
    
    # Need to give a full ARN to define the function, just using the name will not work.    
    # In serverless.yml, set this as environment variable, using pseudovariables to automatically get the correct values.
    arn = os.environ['ARN_PREFIX']
    response = lc.invoke(FunctionName= arn + "endpoint", 
                         InvocationType='RequestResponse', 
                         # Even though the payload is given as JSON, it is read in as a dict by the receiving function
                         Payload=json.dumps({'name': 'BigBoi',
                                             'df': df.to_dict() }))  # convert DataFrame to dict to transfer
    
    # You do get the full response event, not just what the lambda returned. 
    # Use .read() to get the body.
    return response['Payload'].read()


def endpoint(event, context):
    
    # Event is a dictionary containing the 'Payload' defined in the invoke function call
    # So you don't get access to the full AWS event, only the body.

    # Convert the dict back into a dataframe    
    df = pd.DataFrame(event['df'])

    current_time = datetime.datetime.now().time()
    response = {
        "message": "Hello " + event['name'] + ", the current time is " + str(current_time),
        "dataframe": df.to_dict()
    }

    # no need to convert to JSON
    return response

if __name__== '__main__':
    app.run()
