# -*- coding: utf-8 -*-
# Copyright (c) 2018, ElasticRun and contributors
# For license information, please see license.txt

from __future__ import unicode_literals, print_function
import frappe
from werkzeug.wrappers import Response
import json
from frappe.utils.response import json_handler

def generate_exception_json(status, exception, traceback=None):
    response = Response()
    response.status_code = status
    frappe.local.response['http_status_code'] = status
    frappe.db.rollback()
    data = {"status":"red", "message": str(exception), 'traceback': traceback}
    response.mimetype = 'application/json'
    response.charset = 'utf-8'
    response.data = json.dumps(data, default=json_handler, separators=(',',':'))
    return response



def generate_response(status, msg, data=None):
    frappe.errprint(data)
    response = Response()
    data = {
        "status"  : status,
        "message" : msg,
        "data"    : data
    }
    response.mimetype = 'application/json'
    response.charset = 'utf-8'
    response.data = json.dumps(data, default=json_handler, separators=(',',':'))
    return response


def generate_json(status, msg, data=None):
    
    data = {
        "status"  : status,
        "message" : msg,
        "data"    : data
    }
    return data
    
