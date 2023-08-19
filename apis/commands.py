# Copyright @ 2023 Overland Storage, Inc. dba Overland-Tandberg. All rights reserved. 
from flask_restx import Resource, Namespace

from shared.ot_logging import SoaLogger as Log
from shared.utils import global_stack_context
from shared.rest_data_models import RECEIVED_REQUEST_GET, RECEIVED_REQUEST_POST
from shared.rest_data_models import \
    license_key_request_model, \
    remove_inactive_response_model, \
    remove_key_response_model, \
    remove_inactive_request_model, \
    license_key_response_model, \
    update_licenses_response_model
from shared.ot_logging import SoaLogger as Log
from shared.utils import global_stack_context

from ..core.this_service import this_service
from ..core.license_check import license_manager
from ..core.exceptions import CouldNotReachLicenseSpringException
from ..core.exceptions import NotFoundException

description = """
Commands available to License Manager
"""
ns = Namespace(
    'License Manager - Commands',
    description=description
)

license_key_request_model.register_model_with_namespace(ns)
license_key_response_model.register_model_with_namespace(ns)
remove_inactive_request_model.register_model_with_namespace(ns)
remove_inactive_response_model.register_model_with_namespace(ns)
remove_key_response_model.register_model_with_namespace(ns)
update_licenses_response_model.register_model_with_namespace(ns)


####################################################################################
#                           Add License Key Command
####################################################################################
@ns.route('/add_license_key')
class LicenseKey(Resource):
    @ns.expect(license_key_request_model, validate=True)
    @ns.marshal_with(license_key_response_model,skip_none=True)
    @ns.doc("POST License Key",
            responses={
                418: 'Service enablement status prohibits acting on this request.',
                500: 'Internal Error.',
                499: 'Error writing key to file'
            })
    def post(self):
        """
        Post license keys
        automatically attempt to activate given key + add to file
        if key already active or cannot activate, just adds it to file
        """

        with global_stack_context():

            license_key = ns.payload["license_key"]
            Log.debug(
                f'/add_license_key received.'
                f'   license_key: {license_key}',
                topic=RECEIVED_REQUEST_POST
            )

            # if success, return license key + 200
            # if fail, return error detail + 499
            ret = license_manager.add_license_key(license_key)
            if 'incorrect format' in ret:
                return {"error_detail":ret}, 499
            elif ret == "key already registered" or "could not activate" in ret:
                return {"error_detail":ret}, 200
            elif ret:
                return {"response":f'License key {ret} registered and/or activated successfully'}, 200
            return {'error_detail':'server error'}, 500

####################################################################################
#                        Remove Inactive Licenses Command
####################################################################################
@ns.route('/remove_inactive_licenses')
class RemoveInactive(Resource):
    @ns.expect(remove_inactive_request_model, validate=True)
    @ns.marshal_with(remove_inactive_response_model, skip_none=True)
    @ns.doc(
        'POST to remove inactive licenses',
        responses={
            418: 'Service enablement status prohibits acting on this request.',
            404: 'File not found',
            500: 'Unknown server error - See detail.'
        }
    )
    def post(self):
        """
        Remove any inactive licenses on device
        :return:
        """
        with global_stack_context():

            if not this_service.respond_to_get_statuses():
                return ({}, 418)

            Log.debug(
                f'/remove_inactive_licenses received.',
                topic=RECEIVED_REQUEST_POST
            )

            ret = license_manager.remove_inactive()
            if ret:
                return {'response':ret}, 200
            return {'error_detail':'server error'}, 500

####################################################################################
#                           Remove Specific License Command
####################################################################################
@ns.route('/remove_license')
class RemoveKey(Resource):
    @ns.expect(license_key_request_model, validate=True)
    @ns.marshal_with(remove_key_response_model, skip_none=True)
    @ns.doc(
        'POST to remove specific key',
        responses={
            418: 'Service enablement status prohibits acting on this request.',
            404: 'Key not found',
            502: 'Could not reach LicenseSpring',
            500: 'Unknown server error - See detail.'
        }
    )
    def post(self):
        """
        Remove a specific key from file
        """
        with global_stack_context():

            if not this_service.respond_to_get_statuses():
                return({}, 418)

            license_key = ns.payload['license_key']
            Log.debug(
                f'/remove_license received.'
                f'   license_key: {license_key}',
                topic=RECEIVED_REQUEST_POST
            )

            ret = license_manager.remove_key(license_key)
            if ret == f'License key {license_key} not found' or 'incorrect format' in ret:
                return {'error_detail':ret}, 404
            elif ret:
                return {'response':ret}, 200
            return {'error_detail':'server error'}, 500


####################################################################################
#                        Remove Inactive Licenses Command
####################################################################################
@ns.route('/update_licenses')
class UpdateLicenses(Resource):
    @ns.expect(remove_inactive_request_model, validate=True)
    @ns.marshal_with(update_licenses_response_model, skip_none=True)
    @ns.doc(
        'POST to update all licenses registered on QuikStation',
        responses={
            418: 'Service enablement status prohibits acting on this request.',
            404: 'File not found',
            500: 'Unknown server error - See detail.'
        }
    )
    def post(self):
        """
        Update all licenses registered on QuikStation
        :return:
        """
        with global_stack_context():

            if not this_service.respond_to_get_statuses():
                return ({}, 418)
            Log.debug(
                f'/update_licenses received.',
                topic=RECEIVED_REQUEST_POST
            )

            updated = license_manager.update_licenses()
            if "successfully" in updated:
                return {'response':updated}, 200
            return {'error_detail':'server error'}, 500