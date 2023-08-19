# Copyright @ 2023 Overland Storage, Inc. dba Overland-Tandberg. All rights reserved.
from shared.ot_logging import SoaLogger as Log
from shared.soa_service import SoaService

from .license_check import license_manager

class ThisService(SoaService):

    #
    # IMPORTANT NOTE:  An __init__ method should not be necessary for this class
    #                  extension.  Anything you want to do on initialization probably
    #                  should be done during enablement in the custom_enable function
    #                  override below.  If you feel you need an __init__ method,
    #                  be CERTAIN you call super in it.
    #

    @property
    def name(self):
        return 'license_manager'

    # required override
    def send_broadcast_events(self):
        pass

    # override
    def custom_enable(self):
        Log.info('Enabling the Service')
        license_manager.setup()


#
# Importable reference to the singleton instance.
#
this_service = ThisService()
