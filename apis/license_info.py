# Copyright @ 2023 Overland Storage, Inc. dba Overland-Tandberg. All rights reserved.
from flask_restx import Resource, Namespace
import json
from shared.rest_data_models import RECEIVED_REQUEST_GET, RECEIVED_REQUEST_POST
from shared.rest_data_models import \
    behavior_response_model, \
    key_response_model, \
    active_licenses_response_model, \
    features_model
from shared.ot_logging import SoaLogger as Log
from shared.utils import global_stack_context

from ..core.this_service import this_service
from ..core.license_check import license_manager
from ..core.exceptions import CouldNotReachLicenseSpringException
from ..core.exceptions import NotFoundException

# There is always one API where events are received.  All events show up there and the handler in that API needs to
# decide which to respond to and how, and which to simply ignore (which will typically be 'most of them')

#
# Create the namespace and register the shared model(s) we'll use
#
description = """
API for managing license information
"""

##############################################################################################
# This is the API which other services interact with to get or post information about licenses
# and which behaviors they are permitted use based on those licenses.
##############################################################################################

ns = Namespace('License Info', description=description)

behavior_response_model.register_model_with_namespace(ns)
key_response_model.register_model_with_namespace(ns)
active_licenses_response_model.register_model_with_namespace(ns)
features_model.register_model_with_namespace(ns)


####################################################################################
# Standard info get.  Requires a specific behavior name.
####################################################################################
@ns.route('/<behavior_name>')
class ByBehavior(Resource):
    @ns.marshal_with(behavior_response_model, skip_none=True)
    @ns.doc(
        'GET for license info',

        responses={
            418: 'Service enablement status prohibits acting on this request.',
            404: 'Behavior not found',
            502: 'Could not reach LicenseSpring',
            500: 'Unknown server error - See detail.'
        }
    )
    def get(self, behavior_name):
        """
        Check if access allowed for given behavior
        if access allowed, returns true
        if no access, returns false
        """
        with global_stack_context():

            if not this_service.respond_to_get_statuses():
                return({}, 418)

            Log.debug(
                f'/behavior check received.'
                f'   behavior: {behavior_name}',
                topic=RECEIVED_REQUEST_GET
            )

            try:
                is_permitted = license_manager.check_behavior(behavior_name)
                return {'response':is_permitted}, 200
            except NotFoundException as ex:
                return {'error_detail':ex}, 404
            except CouldNotReachLicenseSpringException as ex:
                return {'error_detail':ex}, 502
            except:
                return {'error_detail':'server error'}, 500


####################################################################################
# Get license keys
####################################################################################
@ns.route('/view_license_keys')
class ViewKeys(Resource):
    @ns.marshal_with(key_response_model, skip_none=True)
    @ns.doc(
        'GET for license keys',
        responses={
            418: 'Service enablement status prohibits acting on this request.',
            404: 'File not found',
            500: 'Unknown server error - See detail.'
        }
    )
    def get(self):
        """
        View license keys currently registered on device
        """
        with global_stack_context():

            if not this_service.respond_to_get_statuses():
                return ({}, 418)
            Log.debug(
                f'/view_license_keys received.',
                topic=RECEIVED_REQUEST_GET
            )

            registered_keys = license_manager.get_keys()
            return {'keys':registered_keys}, 200

####################################################################################
# Get licensed features
####################################################################################
@ns.route('/licensed_features')
class LicensedFeatures(Resource):
    @ns.marshal_with(features_model)
    @ns.doc(
        'GET for all licensed features and associated behaviors',
        responses={
            418: 'Service enablement status prohibits acting on this request.',
            500: 'Unknown server error - See detail.'
        }
    )
    def get(self):
        """
        View all features and associated behaviors available with current registered licenses.
        Uses LicenseSpring's check_license endpoint to retrieve features on each active
        registered license
        """
        with global_stack_context():

            if not this_service.respond_to_get_statuses():
                return ({}, 418)
            Log.debug(
                f'/licensed_features received.',
                topic=RECEIVED_REQUEST_GET
            )

            try:
                features = license_manager.get_licensed_behaviors()
                return features, 200
            except CouldNotReachLicenseSpringException as ex:
                return {'error_detail': f'Error talking to LicenseSpring: {ex}'}, 502
            except:
                return {'error_detail': 'Server error'}, 500


####################################################################################
# Get active licenses
####################################################################################
@ns.route('/active_licenses')
class ActiveLicenses(Resource):
    @ns.marshal_with(active_licenses_response_model, skip_none=True)
    @ns.doc(
        'GET for active licenses',
        responses={
            418: 'Service enablement status prohibits acting on this request.',
            404: 'Keys not found',
            500: 'Unknown server error - See detail.'
        }
    )
    def get(self):
        """
        Return all current active licenses from registered license keys and each license's associated product
        """
        with global_stack_context():

            if not this_service.respond_to_get_statuses():
                return {}, 418
            Log.debug(
                f'/active_licenses received.',
                topic=RECEIVED_REQUEST_GET
            )

            try:
                licenses = license_manager.get_active_licenses()
                return {'licenses':licenses}, 200
            except CouldNotReachLicenseSpringException as ex:
                return {'error_detail': 'Error talking to LicenseSpring'}, 500

