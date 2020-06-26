# -*- coding: utf-8 -*-
"""
This is a very simple lambda function to test if I can invoke it without
running into time-out problems as they occur with API gateway. This works :)
But don't forget to set the timeout in serverless.yml, because the default is
only 6 seconds!

Run with:

sls invoke local --function returnInput --path input.json

@author: 251088
"""

import time
import json

def endpoint(event, context):
    
           
    if 'timeout' in event.keys():
        time.sleep(event['timeout']) # test if there is a timeout
    
    event['message'] = "Hello from AWS!"
    
    return event