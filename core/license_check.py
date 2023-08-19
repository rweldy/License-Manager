# Copyright @ 2023 Overland Storage, Inc. dba Overland-Tandberg. All rights reserved.
#!/usr/share/OT/firmware/venv_soa/bin/python3
import uuid
import copy
import licensespring
import json
import re

from pathlib import Path

licensespring.app_version = "MyApp 1.2.0"

from licensespring.api import APIClient
from licensespring.api import ClientError

from shared.ot_logging import SoaLogger as Log
from shared.utils import global_stack_context

from ..core.exceptions import NotFoundException
from ..core.exceptions import CouldNotReachLicenseSpringException
from .log_topics import INTERNALDATA, ENABLEMENT

from shared.global_config import read_global_static_config
from shared.local_config import read_local_static_config
from shared.local_config import read_persistent_config
from shared.local_config import write_persistent_config
from shared.local_config import remove_persistent_config


# 2 class version (v2)

class License:
    '''
    Class for one license key and its associated information
    '''
    def __init__(self, key):
        self.license_key = key
        self.active = False
        self.product=""
        self.features={}
        self.behaviors={}
        try:
            # active will get set here, may not know product yet on first activation
            self.set_license_info()
        except:
            raise CouldNotReachLicenseSpringException

    def set_license_info(self):
        '''
        Check LicenseSpring for key and set info if possible
        If key is not active or found in LicenseSpring, values stay null
        :return: Tuple of product string, features dict, behaviors dict
        '''
        Log.debug(
            f'Setting license info.'
            f'   License key: {self.license_key}',
            topic=INTERNALDATA
        )
        for product in license_manager.products:
            # have to check all defined products for LicenseSpring API call to (maybe) not fail
            try:
                self.active = self.activate(product)
                data = license_manager.api_client.check_license(
                    product=product,
                    license_key=self.license_key)
                Log.debug(f'testing 123')
                self.product = product
                self.set_features(data)

                # return product, feature_dict, behav_dict
            except CouldNotReachLicenseSpringException as e:
                Log.error(
                    f'License creation failed.'
                    f'   Exception: {e}',
                    topic=INTERNALDATA
                )
                raise
            except Exception as e:
                Log.debug(f'unhandled exception: {e}')
                pass

    def set_behavs(self, product, feature):
        '''
        Build the behavior dict for a given license key
        :return: dict of behavior + description
        '''
        Log.debug(
            f'License set behaviors.'
            f'   License: {self.license_key}',
            topic=ENABLEMENT
        )
        behav_dict = {}
        for behav in license_manager.products[product][feature]:
            behav_dict[behav] = {
                'description': license_manager.defined_behaviors[behav]
            }
        return behav_dict

    def set_features(self, data):
        '''
        Build the feature dict for a given license key
        :return: dict of features + description
        '''
        Log.debug(
            f'License set features.'
            f'   License: {self.license_key}',
            topic=ENABLEMENT
        )
        feature_dict = {}
        for feature in data["product_features"]:
            feature_dict[feature["code"]] = {
                'description': license_manager.feature_descripts[feature["code"]],
                'behaviors': self.set_behavs(self.product, feature["code"])
            }
        self.features = copy.deepcopy(feature_dict)
        Log.debug(f'testing features: {self.features}')

    def activate(self, product):
        '''
        Attempt to activate a license key
        :return: boolean
        '''
        Log.debug(
            f'License activate'
            f'   License: {self.license_key}',
            topic=ENABLEMENT
        )
        try:
            data = license_manager.api_client.activate_license(
                product=product,
                license_key=self.license_key)
            # if license already active or activation success, no exception thrown
            return True
        except Exception as e:
            return False

    def update_info(self):
        '''
        Reaches out to LicenseSpring to update license info on QuikStation
        :return: nothing, just update class members
        '''
        Log.debug(
            f'Single License update info'
            f'   License: {self.license_key}',
            topic=INTERNALDATA
        )
        try:
            data = license_manager.api_client.check_license(
                product=self.product,
                license_key=self.license_key)
            if data:
                self.active = data["license_active"]
                self.set_features(data)
        except:
            # License does not exist in LicenseSpring or is inactive
            self.active = False


#
# Class to interact with LicenseSpring
#
class LicenseManager:
    """
    Class for all info/interaction with licenses and LicenseSpring
    """
    def __init__(self):
        """
        init stuff
        set up api client w OT keys
        """

        # api client gets initialized in setup()
        self.api_client = None

        # must match product code in licensespring!!!! (soa.yaml)
        self.products = read_global_static_config('products')

        self.defined_behaviors = read_global_static_config('behaviors')
        self.feature_descripts = read_global_static_config('features')

        # maps "key": License() object
        self.licenses = {}


    def setup(self):
        '''
        Do initializations.
        Called on enablement
        :return:
        '''
        # read keys from persistent file
        license_keys = read_persistent_config('license_keys')
        Log.debug(
            f"LicenseManager class Setup. "
            f"Current registered keys are {license_keys}",
            topic=ENABLEMENT
        )

        # api setup must come before license creation!!!
        api_key = read_local_static_config('api_key')
        shared_key = read_local_static_config('shared_key')
        self.api_client = APIClient(
            api_key=api_key,
            shared_key=shared_key
        )

        if license_keys is not None:
            for license_key in license_keys:
                new_license = License(license_key)
                self.licenses[license_key] = new_license

    def check_behavior(self, behav):
        """
        Determines whether requested behavior is permitted. \n
        Checks for requested behavior in data structure returned from get_licensed_behaviors
        Raises exceptions if behavior undefined
        :param behav:String
        :return: Boolean
        """
        Log.debug(
            f'License manager check behavior'
            f'   Behavior: {behav}',
            topic=INTERNALDATA
        )
        #
        # check for illegal characters
        #
        valid = self.validate_behav(behav)
        if not valid:
            Log.warning(
                f'Behavior contains illegal characters'
            )
            raise NotFoundException('Behavior contains illegal characters')

        #
        # check if behavior is even defined (soa.yaml)
        # data structure not in terms of behaviors, so have to search for it
        #
        behav_found = False
        for product in self.products:
            for feature in self.products[product]:
                if behav in self.products[product][feature]:
                    behav_found = True
        if not behav_found:
            Log.warning(
                f'Behavior {behav} does not exist'
            )
            raise NotFoundException(f'Behavior {behav} does not exist, check your spelling')

        # behavior is defined, so check if licensed for it
        for license_obj in self.licenses.values():
            if license_obj.active:
                for feature in license_obj.features.values():
                    if behav in [*feature['behaviors'].keys()]:
                        return True

        return False


    def validate_behav(self, behav):
        """
        check for malicious input
        :param behav:
        :return: Boolean
        """
        # allows alphanumeric and underscores
        pattern = r'^[a-zA-Z0-9_]+$'
        if re.match(pattern, behav):
            # Input is valid
            return True
        else:
            # Input contains disallowed characters
            return False

    def add_license_key(self, key):
        """
        Add license key to file, activate if inactive
        :param key:
        :return: Key that was added or error message
        """
        Log.debug(
            f'License manager add license key'
            f'   License key: {key}',
            topic=INTERNALDATA
        )
        valid = self.validate_key(key)
        if not valid:
            Log.warning(
                f'Key is of incorrect format'
            )
            return 'Key is of incorrect format'

        key = key.upper()

        # create new License instance with key
        try:
            # all initialization + LicenseSpring calls happen in License __init__
            new_license = License(key)
        except:
            Log.warning(
                f'License creation failed.'
                f'   License key: {key}',
                topic=INTERNALDATA
            )
            raise CouldNotReachLicenseSpringException

        # add new license to registered licenses dict
        self.licenses[key] = new_license

        # clear and rewrite config file of registered keys
        remove_persistent_config('license_keys')
        write_persistent_config('license_keys', [*self.licenses.keys()])

        if not self.licenses[key].active:
            return "Key registered, but could not activate"

        return key


    def validate_key(self, key):
        """
        key must be of format AAAA-AAAA-AAAA-AAAA (A-Z, 0-9)
        :param key:
        :return: Boolean
        """

        # thanks chatgpt!
        pattern = r'^[a-zA-Z0-9]{4}-[a-zA-Z0-9]{4}-[a-zA-Z0-9]{4}-[a-zA-Z0-9]{4}$'

        if re.match(pattern, key):
            return True
        return False

    def activate_license(self, license_key):
        """
        Attempt to activate license key
        :param license_key:
        :return: Boolean
        """
        Log.debug(
            f'License manager activate license.'
            f'   License key: {license_key}',
            topic=INTERNALDATA
        )
        activated = False
        try:
            # attempt to activate license
            # if already active or activation successful, no exception thrown
            self.api_client.activate_license(product=self.licenses[license_key].product, license_key=license_key)
            activated = True
        except:
            pass
        return activated

    def get_keys(self):
        """
        Returns all license keys (active or inactive) registered with this QuikStation as a list
        :return: List of keys
        """
        Log.debug(
            f'License manager get keys.',
            topic=INTERNALDATA
        )

        # self.licenses is a dict keyed by license keys
        # want to return those keys as a list
        license_keys = [*self.licenses.keys()]
        return license_keys

    def get_licensed_behaviors(self):
        """
        Return available features with associated behaviors licensed to this QuikStation \n
        features: {
            "feature1":{
                "description: "", \n
                "behaviors":{
                    "behavior1":{
                        "description": ""
                    }, \n
                    "behavior2":{
                        "description": ""
                    }
                }
            }, \n
            "feature2":...
        }
        :return: four level dictionary
        """
        Log.debug(
            f'License manager get all licensed features and behaviors',
            topic=INTERNALDATA
        )
        # build the return dict
        licensed_features = {}
        for license_key, license_obj in self.licenses.items():
            # only add active license features
            if license_obj.active:
                for feature_name, feature_obj in license_obj.features.items():
                    licensed_features[feature_name] = feature_obj
        return licensed_features


    def get_active_licenses(self):
        """
        Returns only active license keys on device \n
        active_keys = [
            {
                "license_key":AAAA-AAAA-AAAA-AAAA, \n
                "product":"qsiscsi",
                "features": [
            }, \n
            {
                ...
            }
        ]
        :return: List of dictionaries
        """
        Log.debug(
            f'License manager get active licenses',
            topic=INTERNALDATA
        )
        active_keys = []

        # check every license key registered on QuikStation if active
        for license_key in self.licenses:
            if self.licenses[license_key].active:
                k = {
                    'license_key':self.licenses[license_key].license_key,
                    'product':self.licenses[license_key].product,
                    'features': [*self.licenses[license_key].features.keys()]
                }

                active_keys.append(k)
        return active_keys


    def remove_inactive(self):
        """
        Removes all inactive license keys from file
        :return: Success message or error detail
        """
        Log.debug(
            f'License manager remove all inactive keys',
            topic=INTERNALDATA
        )
        inactive_keys = []
        for license_key in self.licenses:
            # if key not active, remove from registered dict
            if not self.licenses[license_key].active:
                inactive_keys.append(license_key)

        if len(inactive_keys)==0:
            return 'No inactive licenses found'

        for license_key in inactive_keys:
            self.licenses.pop(license_key)

        # clear and rewrite config file
        remove_persistent_config('license_keys')
        write_persistent_config('license_keys', [*self.licenses.keys()])

        return f'{len(inactive_keys)} inactive license(s) removed'


    def remove_key(self, license_key):
        """
        Removes a specific license key from file
        :param license_key:
        :return: success message or error detail
        """
        Log.debug(
            f'License manager remove key.'
            f'   License key: {license_key}',
            topic=INTERNALDATA
        )
        # validate key
        valid = self.validate_key(license_key)
        if not valid:
            Log.warning(
                f'Key is of incorrect format',
                topic=INTERNALDATA
            )
            return 'Key is of incorrect format'
        license_key = license_key.upper()

        # check if requested key is registered on QuikStation
        keys = self.get_keys()
        if license_key not in keys:
            Log.warning(
                f'License key {license_key} does not found'
            )
            return f'License key {license_key} not found'

        self.licenses.pop(license_key)

        # clear and rewrite config file
        remove_persistent_config('license_keys')
        write_persistent_config('license_keys', [*self.licenses.keys()])

        return f'License key {license_key} removed'

    def update_licenses(self):
        '''
        update each registered license with current info from LicenseSpring
        :return:
        '''
        Log.debug(
            f'License manager update all licenses',
            topic=INTERNALDATA
        )
        for license_key in self.licenses:
            try:
                self.licenses[license_key].update_info()
            except:
                raise Exception
        return "updated successfully"

#
# Importable instance.  Import this wherever we need it in the service.
#
license_manager = LicenseManager()
