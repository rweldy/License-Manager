# Copyright @ 2023 Overland Storage, Inc. dba Overland-Tandberg. All rights reserved.
from flask_restx import Resource, Namespace

from shared.rest_data_models import broadcast_event_model
from shared.utils import global_stack_context

from ..core.this_service import this_service

# There is always one API where events are received.  All events show up there and the handler in that API needs to
# decide which to respond to and how, and which to simply ignore (which will typically be 'most of them')

#
# Create the namespace and register the shared model(s) we'll use
#
ns = Namespace('Event Reception', description='API to receive all QuikStation broadcast events')
broadcast_event_model.register_model_with_namespace(ns)

#
# Standard incoming event endpoint.  Note: the '/broadcast-event' address is a global design requirement.
#
@ns.route('/broadcast-event')
class EventListener(Resource):
    @ns.doc('Event Reception')
    @ns.expect(broadcast_event_model, validate=True)
    def post(self):

        with global_stack_context():

            if not this_service.respond_to_event_statuses():
                return({}, 200)

            #
            # We are validating against a model with required fields, so we know these are present.
            #
            sending_service = ns.payload['service']

            #
            # this is where we look for events we care about and invoke logic because they happened.
            #
            # Example (remove this once if/when there's actual code here.)
            #     if sending_service == 'pt_dock_manager' and sending_ns == 'cart_info':
            #         do_something()

            # Return is always 200 for events because the sender doesn't really care anyway.
            return({}, 200)





