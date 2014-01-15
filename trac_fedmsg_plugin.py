import trac.core

import trac.ticket.api
import trac.wiki.api
from trac.config import ListOption

import inspect
import fedmsg


def env2dict(env):
    """ Utility method to format the trac environment for fedmsg. """
    return dict(
        base_url=env.base_url,
        project_name=env.project_name,
        project_description=env.project_description,
        project_url=env.project_url,
        project_icon=env.project_icon,
    )


def wikipage2dict(page):
    attrs = ['name', 'version', 'time', 'author', 'text', 'comment']
    return dict([(attr, getattr(page, attr)) for attr in attrs])


def ticket2dict(ticket, remove_fields_before_publish):
    d = dict(id=ticket.id)
    d.update(ticket.values)

    for field in remove_fields_before_publish:
        if field in d:
            del d[field]

    return d


def currently_logged_in_user():
    """ Return the currently logged in user.

    This is insane.

    Unless your method or function is passed a reference to the trac
    'request' object, there is no way to get ahold of the currently
    logged in user.  Furthermore, there is no way globally to get ahold
    of the current request object.

    Here, we crawl our way back up the call stack until we find the
    first place that has 'req' as a local instance variable and attempt
    to extract the username of the current user from that.

    Please forgive me.
    """

    for frame in (f[0] for f in inspect.stack()):
        if 'req' in frame.f_locals:
            return frame.f_locals['req'].authname

    # Practically speaking, we should never get here.
    raise KeyError('No request object found.')


class FedmsgPlugin(trac.core.Component):
    """ The trac fedmsg plugin.

    This plugin simply listens for trac events and
    rebroadcasts them to a fedmsg message bus.
    """
    trac.core.implements(
        trac.ticket.api.ITicketChangeListener,
        trac.wiki.api.IWikiChangeListener,
    )

    # Improve doc: Add a list of fields that can be mentioned here to help the
    # user.
    option_doc = "A comma separated list of fields not to be sent to fedmsg"
    banned_fields = ListOption(
        section='fedmsg',
        name='banned_fields',
        default=None,
        sep=',',
        doc=option_doc)

    def __init__(self, *args, **kwargs):
        super(FedmsgPlugin, self).__init__(*args, **kwargs)

        # If fedmsg was already initialized, let's not re-do that.
        if not getattr(getattr(fedmsg, '__local', None), '__context', None):
            config = fedmsg.config.load_config()
            config['active'] = True
            fedmsg.init(name='relay_inbound', cert_prefix='trac', **config)

    def publish(self, topic, **msg):
        """ Inner workhorse method.  Publish arguments to fedmsg. """
        msg['instance'] = env2dict(self.env)
        msg['agent'] = currently_logged_in_user()
        fedmsg.publish(modname='trac', topic=topic, msg=msg)

    def ticket_created(self, ticket):
        """Called when a ticket is created."""
        self.publish(topic='ticket.new', ticket=ticket2dict(
            ticket, self.banned_fields))

    def ticket_changed(self, ticket, comment, author, old_values):
        """Called when a ticket is modified.

        `old_values` is a dictionary containing the previous values of the
        fields that have changed.
        """

        for field in self.banned_fields:
            if field in old_values:
                del old_values[field]

        # Should we check these too?
        self.publish(
            topic='ticket.update',
            ticket=ticket2dict(ticket, self.banned_fields),
            comment=comment,
            author=author,
            old_values=old_values,
        )

    def ticket_deleted(self, ticket):
        """Called when a ticket is deleted."""
        self.publish(topic='ticket.delete', ticket=ticket2dict(
            ticket, self.banned_fields))

    def wiki_page_added(self, page):
        """Called whenever a new Wiki page is added."""
        self.publish(topic='wiki.page.new', page=wikipage2dict(page))

    def wiki_page_changed(self, page, version, t, comment, author, ipnr):
        """Called when a page has been modified."""
        self.publish(
            topic='wiki.page.update',
            page=wikipage2dict(page),
            version=version,
            t=t,
            comment=comment,
            author=author,
            #ipnr=ipnr,  # Don't broadcast IP addresses.  Poor form.
        )

    def wiki_page_deleted(self, page):
        """Called when a page has been deleted."""
        self.publish(topic='wiki.page.delete', page=wikipage2dict(page))

    def wiki_page_version_deleted(self, page):
        """Called when a version of a page has been deleted."""
        self.publish(topic='wiki.page.version.delete',
                     page=wikipage2dict(page))

    def wiki_page_renamed(self, page, old_name):
        """Called when a page has been renamed."""
        self.publish(
            topic='wiki.page.rename',
            page=wikipage2dict(page),
            old_name=old_name
        )
