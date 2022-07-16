# -*- coding: utf-8 -*-
# Copyright (c) 2018, ElasticRun and contributors
# For license information, please see license.txt

from __future__ import unicode_literals
import frappe
import time
#import libera_duo.facility_operation.config.settings as settings
import os
import yaml
import json
import datetime
import binascii
from frappe.utils.file_manager import save_file
from mimetypes import guess_extension
from frappe.utils.file_manager import get_content_hash
from werkzeug.wrappers import Response
import workorder.api.controllers.build_response as build_response
import copy

# function to get the doc
# if doc does not exist, it returns None
def get_doc(doctype, condition):
    is_temp = False
    try:
        # IF MUTE MESSAGES IS FALSE THEN TURN IT True
        if not frappe.flags.mute_messages:
            frappe.flags.mute_messages = True
            is_temp = True

        # GET DOC
        doc = frappe.get_doc(doctype, condition)
        
        # IF MUTE MESSAGE IS TRUE TURN IT FLASE
        if is_temp:
            frappe.flags.mute_messages = False
        
        # RETURN DOC
        return doc
    
    except:
        # IF MUTE MESSAGE IS TRUE TURN IT FLASE
        if is_temp:
            frappe.flags.mute_messages = False
        return None

# def get_config():
#     config_dir = os.getcwd().replace(os.path.basename(os.getcwd()), settings.CONFIG_DIR)
    
#     with open(config_dir, 'r') as ymlfile:
#         cfg = yaml.load(ymlfile)
#     return cfg
 
# function to map the json values in the object   c
def object_mapper(json_input, object):
    for key in json_input.keys():
        if type(json_input[key]) is list:
            for item in json_input[key]:
                object.append(key, item)
        else:
            setattr(object, key, json_input[key])
    return object

def time_profiler(method):


    def function(*args, **kw):
        start_time = time.time()

        result = method(*args, **kw)

        end_time = time.time()
        args_list = []
        for arg in args:
            try:
                args_list.append(arg.as_dict())
            except:
                args_list.append(arg)
                continue

        frappe.logger(__name__).info('%s %s (%s, %s) %2.2f sec' % \
            ('time_profiler_log:', method.__name__, tuple(args_list), kw, end_time - start_time) )

        return result


    return function

def get_current_ist_time():
    return (datetime.datetime.now() + datetime.timedelta(hours=5,minutes=30))

def attach_file(content,docname,doc_type,file_name):
    doc_type='Referred Facility'
    
    # print('Inside Attach File',file_name,docname,doc_type)
    base64_content=content.split(',')
    
    file_name += str(guess_extension(base64_content[0].split(":")[1].split(';')[0]))
    base64_content = base64_content[(len(base64_content)-1)]
    # print("--------------------------------------------->",file_name)
    file_data=binascii.a2b_base64(base64_content)
    if file_data:
        f=save_file(file_name,file_data,doc_type,docname,is_private=True)
        # print(f.name)
        return f
    return None

def bulk_file_attach(source_json,doc_type_object,doc_type,attachment_fields):
    doc_name = doc_type_object.name
    # print(doc_name)
    # doc_type = doc_type_object.doc_type
    for field in attachment_fields:
        file_name = doc_name + '_' + field
        # print(field)
        base64_content = source_json.get(field,None)
        file = None
        if base64_content:
            file = attach_file(base64_content,doc_name,doc_type,file_name)
            setattr(doc_type_object,field,file.file_url)
            # doc_type_object.reload()
            # doc_type_object.save()
            # frappe.db.commit()
    return doc_type_object
            
def get_file_hash(file_path):
    data = frappe.db.sql("""select content_hash from `tabFile` where 
                      file_url = %(file_url)s
                       """, {"file_url":file_path},as_dict=True)
    if len(data) > 0:
        return data[0].get('content_hash','')
    return ''

def get_payload(payload):
    """
    This method takes input payload of frappe request and converts into actual payload desired to API
    """
    # NEW FRAPPE COMPABILITY
    if payload.get('data'):
        # OLD FRAPPE COMPABILITY
        if(isinstance(payload.get('data'),bytes)):
            payload['data'] = payload['data'].decode('utf-8')
        return json.loads(payload['data'])
    # DATA FIELD DOESNOT EX IN PAYLOAD
    # LATTE COMPABILITY
    else:
        return payload


# THESE METHODS ARE USED TO REMOVE ALL THE NONE KEYS IN DICTONARY
def scrub_dict(d):
    new_dict = {}
    for k, v in d.items():
        if isinstance(v, dict):
            v = scrub_dict(v)
        if isinstance(v, list):
            v = scrub_list(v)
        if not v in (u'', None, {}, []):
            new_dict[k] = v
    return new_dict

def scrub_list(d):
    scrubbed_list = []
    for i in d:
        if isinstance(i, dict):
            i = scrub_dict(i)
        scrubbed_list.append(i)
    return scrubbed_list

def convert_utc_to_user_timezone(date):
    return frappe.utils.convert_utc_to_user_timezone(date).replace(tzinfo=None)

@frappe.whitelist()
def get_gst_checksum(gstin):
    conv_table = '0123456789ABCDEFGHIJKLMNOPQRSTUVWXYZ0'
    final_hash = 0
    for i,c in enumerate(gstin):
        final_hash += (conv_table.index(c) * 2)//36 + (conv_table.index(c) * 2)%36 if (i+1)%2 == 0 else conv_table.index(c)//36 + conv_table.index(c)%36
    return conv_table[36-(final_hash%36)]

def replace_error_code(method):
    print("method name",method)
    def doit(*args,**kwargs):
        print(args,kwargs)
        if kwargs.get('cmd'):
            del kwargs['cmd']
        output = method(*args,**kwargs)
        # output = method(args,kwargs)
        if output and isinstance(output,Response):
            try:
                output_json = json.loads(output.data.decode("utf-8"))
            except Exception as e:
                return output
            output_json_backup = copy.deepcopy(output_json)
            if not output_json:
                return output
            output_message = output_json.get("message")
            if not output_message:
                return output

            print(output.data)
            code = output_message
            api = api_name = method.__module__ + '.' + method.__qualname__
            print(api)
            doc = frappe.db.sql(""" select c.message as m,c.handler as h from `tabAPI Custom Error Message` as p
            inner join `tabStatus Code Message` as c
            on c.parent = p.name
            where c.response_code = %(code)s
            and p.api = %(api)s
            """,{"api":api,"code":str(code)},as_dict=1,debug=1)
            print(doc)
            if not doc:
                return output
            output_message = doc[0]['m']
            output_json['message'] = output_message
            
            new_output = json.dumps(output_json)
            output.data = bytes(new_output,"utf-8")
            if doc[0]['h']:
                func = frappe.get_attr(doc[0]['h'])
                try:
                    func(pre_proc_resp=output_json_backup,proc_resp=output_json,arguments=args,keyword_arguments=kwargs,api_name=api,error_code=code)
                except Exception as e:
                    frappe.log_error(frappe.get_traceback(),"Error While Calling Handler For Processing Error Message")
        return output
            # for  doc.get()
    return doit

def log_it(api_name,error_code,*args,**kargs):
    # print("++++++++++++++++handler+++++++++++++",resp)
    rel = frappe.new_doc("Request Error Log")
    rel.api = api_name
    # print(type(kargs))
    kargs["__user__"] = frappe.session.user
    rel.input = json.dumps(kargs, sort_keys=True, indent=4)
    rel.error_code = error_code
    rel.status = "Pending"
    rel.save(ignore_permissions=True)
    frappe.db.commit()
    return

@frappe.whitelist()
@replace_error_code
def test(**kwarg):
    print("Test Called")
    return build_response.generate_response("red",1,{"process":13333})


@frappe.whitelist()
@replace_error_code
def test1(g):
    print("Test Called")
    return build_response.generate_response("red",1,{"process":13333})