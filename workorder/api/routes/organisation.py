from __future__ import unicode_literals, print_function
from logging import debug, exception
from numpy import append
import workorder.api.controllers.organisation as organisation_controller
import workorder.api.controllers as controllers
import workorder.api.controllers.build_response as build_response
import frappe
import json
import yaml
import sys
import os
import datetime
import requests
import json
import inspect


@frappe.whitelist()
def get_org_list(orgs_filter=None,org_field=None):
		orgs_filter = json.loads(orgs_filter) if orgs_filter is not None else []
		org_field = json.loads(org_field) if org_field is not None else []
		return organisation_controller.get_org_lists(orgs_filter,org_field)


@frappe.whitelist()
def get_org_station(org_id):
    return organisation_controller.get_org_station(org_id)

@frappe.whitelist()
def get_cost_center_and_warehouse_details(station_name,org_id):
    return organisation_controller.get_ccw_details(station_name,org_id)


@frappe.whitelist()
def bulkUploadFile(**kargs):
    keys = controllers.get_payload(kargs)
    
    return keys
    try:
        print(args)
        doc = frappe.new_doc("WO Bulk Upload")
        ret = frappe.utils.file_manager.upload()
        doc.file_name = ret["file_name"]
        doc.upload_file = ret["file_url"]
        doc.save()
        return build_response.generate_response("green", "fileuplaod successfully")
    except Exception:
        tb = frappe.get_traceback()
        print(tb)
        frappe.log_error(str(tb), 'Error occurred in validate_bulk_upload_rate_fields()')
        
    
    
    
    