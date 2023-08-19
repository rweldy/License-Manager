<!-- Copyright @ 2023 Overland Storage, Inc. dba Overland-Tandberg. All rights reserved. -->
# License Manager Service Requirements

## Overview

The License Manager service is responsible for handling all license-related activities. A license is created in LicenseSpring
(a license management company) when a customer or organization creates an order for a product, upon which a unique license 
key is generated and given to said customer or organization. A product has features defined in LicenseSpring that it is licensed for. 
This maps to specific behaviors that other services within the SOA use. These other services must ask the License Manager
for permission to use a specific behavior, in which case the License Manager will reach out to LicenseSpring's 
public API and see if the machine has any active licenses that have a feature which allows access to a given behavior. 
This service is capable of storing license keys inputted by a user or organization, retrieving license information 
from LicenseSpring's public API, and activating and removing license keys from file. 

## Inputs

### APIs

1. GET: /licenseinfo/active_licenses
   * Returns a list of all active license keys and their associated product
     * license_key : String that is associated with a given license in LicenseSpring
     * product : String that represents the product code on given license in LicenseSpring
       * Example:
       ```
       "licenses": [
         {
            "license_key": "AAAA-AAAA-AAAA-AAAA",
            "product": "qsiscsi"
         },
         {
            "license_key": "BBBB-BBBB-BBBB-BBBB",
            "product": "rdxiqa"
         }
       ]
       ```
   * Failure:
     * 404 NOT FOUND - If the service cannot reach LicenseSpring
     * 500 SERVER ERROR - Anything else


2. POST: /licenseinfo/add_license_key
    * Request
      * license_key: String representing the license key to add
    * Return
      * Success:
        * Return 200 OK
        * error_detail: "key already added to file"
      * Failure:
        * 499 - Error writing key to file
          * error_detail: "failed adding key to file" (this shouldn't happen)
        * 500 SERVER ERROR - Anything else


3. GET: /licenseinfo/licensed_features
    * Returns a list of all features available with current licenses and a short behavior description
      * feature : String that represents license feature as defined in LicenseSpring
      * behavior : String that represents a specific behavior of that feature as defined by the program
      * description : String that gives a short description of that behavior
        * Example:
        ```
        "features": [
          {
            "feature": "iSCSI Gen",
            "behavior": "iscsi_targ",
            "description": "Expose endpoint as an iSCSI target"
          },
          {
            "feature": "iSCSI Cust",
            "behavior": "iscsi_cust_naming",
            "description": "Custom naming of iSCSI targets"
          }
        ]
        ```
    * Failure:
      * 404 NOT FOUND - If the license key is not found in LicenseSpring
      * 500 SERVER ERROR - Anything else


4. GET: /licenseinfo/remove_inactive_licenses
   * Remove any inactive license keys from device 
   * Return
     * Success:
       * Return 200 OK - "Inactive license(s) removed"
       * Return 200 OK - "No inactive license(s) found"
     * Failure:
       * Return 404 NOT FOUND - "File could not be found"
       * 500 SERVER ERROR - Anything else
       
      

5. GET: /licenseinfo/remove_license/{license_key}
    * Remove a specific key from device by name
    * Return
      * Success: 
        * Return 200 OK - "{License key} removed"
      * Failure:
        * Return 404 NOT FOUND - "License key {key} not found"
        * Return 500 SERVER ERROR - Anything else


6. GET: /licenseinfo/view_license_keys
    * Returns a list of all license keys on device, whether active or inactive
      * Example: 
      ```
      "keys": [
        "AAAA-AAAA-AAAA-AAAA",
        "BBBB-BBBB-BBBB-BBBB"
      ]
      ```
    * Failure
      * 404 NOT FOUND - file license_keys.txt not found
      * 500 SERVER ERROR - Anything else (not likely)
      

7. GET: /licenseinfo/{behavior_name}
    * Returns a boolean that represents whether a requested behavior is available to use from current licenses
    * Return
      * Success:
        * Return 200 OK - Boolean response
      * Failure:
        * 404 NOT FOUND - Behavior not found
        * 502 BAD GATEWAY - Could not reach LicenseSpring
        * 500 SERVER ERROR - Anything else

## System Actions

2. On POST /licenseinfo/add_license_key:
    * Writes the given license key to a file (license_keys.txt) stored in license_manager/apis
    * If the license is inactive, this will activate it and write to file, otherwise just write to file
4. On POST /licenseinfo/remove_inactive_licenses:
    * Check all license keys stored on file with LicenseSpring
    * If the license is inactive, it is removed from the file
5. On POST /licenseinfo/remove_license:
    * Checks license_keys.txt for the given key
    * If the key is on file, it is removed
7. On GET /licenseinfo/{behavior_name}:
    * Checks given behavior (as a string) against all currently available licensed behaviors
    * If behavior is licensed, returns True, otherwise returns False

## Other Requirements

1. The exportable data structure should adhere to QuikStation Software Best-Practices.

## Persistence
License keys should persist across reboots
