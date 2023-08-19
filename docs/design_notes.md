<!-- Copyright @ 2023 Overland Storage, Inc. dba Overland-Tandberg. All rights reserved. -->
## Endpoints
### Commands:
```license_manager/commands/```
1. **add_license_key:** Adds a license key to the list of registered keys. If not already active, it will attempt to activate it, and return whether the key was added and activated, added but not activated, or failed to add. 
2. **remove_inactive_licenses:** When called, will iterate through all currently registered licenses and remove any whose 'active' attribute is false.
3. **remove_license:** Requires a specific license key, and will remove that license from the registered licenses on the QuikStation
4. **update_licenses:** When called, will iterate through all currently registered licenses and check their information against LicenseSpring

### License info
```license_manager/licenseinfo/```
1. **active_licenses:** Returns all registered license keys whose 'active' attribute is true, as well as their associated product and features
2. **licensed_features:** Returns a 4-level dictionary of all features on registered licenses that are currently active, and their associated behaviors
3. **view_license_keys:** Returns a flat list of all registered key, both active and inactive
4. **{behavior_name}:** This endpoint is used to check whether access is allowed to a requested behavior, based on if that behavior is found in an active registered license on the QuikStation

## Classes
There are two classes used in the core layer, ```license_check.py.```

### License
This class represents a single license instance, including its key and all associated information.

**Members**:
1. license_key (string)
2. active (bool)
3. product (string)
4. features (dict)
5. behaviors (dict)

### LicenseManager
This class is essentially a singleton that contains a dictionary of all registered Licenses. It is imported in the API layers to call its functions,
which contain all the logic for managing and checking licenses. 

**Members**:
1. api_client (string, used to set up the API calls to LicenseSpring)
2. products (string, reads defined products in soa.yaml)
3. defined_behaviors (dict, reads defined behaviors in soa.yaml)
4. feature_descripts (dict, reads defined features in soa.yaml)
5. licenses (dict, contains all defined License objects. maps license key:License object)