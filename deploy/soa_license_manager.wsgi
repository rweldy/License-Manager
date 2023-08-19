# Copyright @ 2023 Overland Storage, Inc. dba Overland-Tandberg. All rights reserved.
import os
import sys

#
# Generally speaking, we expect the following line to be the only difference between
# the wsgi files in all the SOA services.
#
service_name = 'license_manager'

#
# Standard boilerplate about having the soa directory in the path so that imports
# (particularly from shared packages) work.
#
soa_path = '/usr/share/OT/firmware/soa'
if os.path.abspath(soa_path) not in sys.path:
    sys.path.append(os.path.abspath(soa_path))

from shared.wsgi import OTApache

#
# Use OTApache to do standard stuff like activate the Venv and set up enablement
# of the service
#
ota = OTApache(service_name)
ota.activate_venv()
ota.enable_service()

from services.license_manager.main import app as application
