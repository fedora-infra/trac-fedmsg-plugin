import trac.core
import trac.ticket.api

import socket
import fedmsg

# If fedmsg was already initialized, let's not re-do that.
if not getattr(getattr(fedmsg, '__local', None), '__context', None):
    hostname = socket.gethostname().split('.', 1)[0]
    fedmsg.init(name="trac." + hostname)


def env2dict(env):
    """ Utility method to format the trac environment for fedmsg. """
    return dict(
        base_url=env.base_url,
        project_name=env.project_name,
        project_description=env.project_description,
        project_url=env.project_url,
        project_icon=env.project_icon,
    )


class FedmsgPlugin(trac.core.Component):
    """ The trac fedmsg plugin.

    This plugin simply listens for trac events and
    rebroadcasts them to a fedmsg message bus.
    """
    trac.core.implements(
        trac.ticket.api.ITicketChangeListener,
    )

    def publish(self, topic, **msg):
        """ Inner workhorse method.  Publish arguments to fedmsg. """
        msg['instance'] = env2dict(self.env)
        fedmsg.publish(modname='trac', topic=topic, msg=msg)

    def ticket_created(self, ticket):
        """Called when a ticket is created."""
        self.publish(topic='ticket.new', ticket=ticket.values)

    def ticket_changed(self, ticket, comment, author, old_values):
        """Called when a ticket is modified.

        `old_values` is a dictionary containing the previous values of the
        fields that have changed.
        """
        self.publish(
            topic='ticket.update',
            ticket=ticket.values,
            comment=comment,
            author=author,
            old_values=old_values,
        )

    def ticket_deleted(self, ticket):
        """Called when a ticket is deleted."""
        self.publish(topic='ticket.delete', ticket=ticket.values)
