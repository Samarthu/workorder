from __future__ import unicode_literals, print_function
from logging import debug, exception
from numpy import append
import frappe
import json
import yaml
import sys
import os
import datetime
import requests
import json
import inspect
import workorder.api.controllers.build_response as build_response


@frappe.whitelist() 
def get_org():
    res = frappe.db.sql(f"""SELECT org_name,org_id from `tabOrganization`""")
    return build_response.generate_response("green", "organisation data", res)

def get_org_lists(orgs_filter,org_field):
    res=frappe.get_all("Organization",filters={'status':'active'},fields=['name','org_name'])
    if len(res) > 0:
        return build_response.generate_response("green","Organisation data founded",res)
    else:
        return build_response.generate_response('red','Organisation {0} not found.'.format(orgs_filter),[])
    
def get_org_station(org_id):
    res = frappe.get_all('Org Station',filters={'org_id':org_id},fields=['location_id','station_name','name','org_id'])
    if len(res) > 0:
        i = 0
        for r in res:
            c_res = frappe.get_all('Cost Center Config',filters={'parent':r.name},fields=['cost_center','warehouse']) 
            res[i]['cost_center'] = c_res
            i+=1
            
        return build_response.generate_response("green","Organisation data founded",res)
    else:
        return build_response.generate_response('red','Organisation Station data not found',[])

def get_ccw_details(station_name,org_id):
        res = frappe.get_all('Org Station',filters={'station_name':station_name,'org_id':org_id},fields=['name']) 
        if len(res) > 0:
            c_res = []
            for r in res:
                c_res.append(frappe.get_all('Cost Center Config',filters={'parent':r.name},fields=['cost_center','warehouse']))
                   
            return build_response.generate_response("green","Organisation data founded",c_res[0])
        else:
            return build_response.generate_response('red','Organisation data not found.',[])