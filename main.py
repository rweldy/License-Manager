# Copyright @ 2023 Overland Storage, Inc. dba Overland-Tandberg. All rights reserved.
# Python
import os
import sys

# Third-Party Modules
from flask import Flask
from flask_restx import Api

# Overland Tandberg shared packages
#
# Standard boilerplate around requiring SOA_DIR_LOCATION and making sure it's in the
# path to import from.
#
soa_dir = os.environ.get('SOA_DIR_LOCATION', '_no_location_')
if soa_dir == '_no_location_':
    print('ERROR:  OT SOA services require the SOA_DIR_LOCATION environment variable to be set.')
    exit()
if os.path.abspath(soa_dir) not in sys.path:
    sys.path.append(os.path.abspath(soa_dir))

#Shared Packages
from shared.shared_apis import shared_ns_admin
from shared.ot_logging import SoaLogger as Log

# Local references
from .apis.event import ns as ns_events
from .core.this_service import this_service
from .apis.license_info import ns as ns_license
from .apis.commands import ns as ns_commands


#
# Set up flask/restx
#
app = Flask(__name__)  # Flask app instance initiated
app.config['RESTX_MASK_SWAGGER'] = False  # We don't need to mask out fields in this example.

#
# Template Note: Update the title and description below for this SOA service.  These are top-level
#                notes in the swagger documentation.  Do not change the validate or doc values.
#
api = Api(
    app,  # Flask restful wraps Flask app around it.
    title='License Manager',
    description='This service manages all license information',
    validate=True,  # Validates the request data for GETs
    version='v0.1',
    doc='/docs'  # Publish swagger under /docs
    )

#
# Add the namespaces and specify their endpoints
#
api.add_namespace(shared_ns_admin, path='/admin')
api.add_namespace(ns_events, path='/events')
api.add_namespace(ns_license, path='/licenseinfo')
api.add_namespace(ns_commands, path='/commands')

if __name__ == '__main__':
    app.run(
        host='0.0.0.0',
        port=this_service.port,
        debug=False,
        use_debugger=False,
        use_reloader=False
    )
