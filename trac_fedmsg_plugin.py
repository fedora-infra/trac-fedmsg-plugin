import trac.core
import trac.ticket.api

import socket
import fedmsg

# If fedmsg was already initialized, let's not re-do that.
if getattr(getattr(fedmsg, '__local', None), '__context', None):
    print "Not reinitializing fedmsg."
else:
    # Initialize fedmsg resources.
    hostname = socket.gethostname().split('.', 1)[0]
    fedmsg.init(name="trac." + hostname)
    print "initializing"


class FedmsgPlugin(trac.core.Component):
    """ The trac fedmsg plugin.

    This plugin simply listens for trac events and
    rebroadcasts them to a fedmsg message bus.
    """
    trac.core.implements(
        trac.ticket.api.ITicketChangeListener,
    )

    def env2dict(self):
        return dict(
            base_url=self.env.base_url,
            project_name=self.env.project_name,
            project_description=self.env.project_description,
            project_url=self.env.project_url,
            project_icon=self.env.project_icon,
        )

    def publish(self, topic, **msg):
        print "PUYBLISHING"
        msg['instance'] = self.env2dict()
        fedmsg.publish(modname='trac', topic=topic, msg=msg)

    def ticket_created(self, ticket):
        self.publish(topic='ticket.new', ticket=ticket.values)

    def ticket_changed(self, ticket, comment, author, old_values):
        self.publish(
            topic='ticket.update',
            ticket=ticket.values,
            comment=comment,
            author=author,
            old_values=old_values,
        )

    def ticket_deleted(self, ticket):
        self.publish(topic='ticket.delete', ticket=ticket.values)
