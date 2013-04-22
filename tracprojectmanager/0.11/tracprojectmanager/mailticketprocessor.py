import email
import os.path
import re
from imailprocessor import IMailProcessor
from trac.core import *
from email.utils import parseaddr
from utils import get_project_list, wrapfunc
from trac.ticket.query import Query
from trac.web import IRequestFilter
from trac.ticket.notification import TicketNotifyEmail
from trac.util.datefmt import to_timestamp, utc
from trac.util.text import exception_to_unicode, to_unicode
from trac.ticket.model import Ticket
from trac.ticket.notification import TicketNotifyEmail
from datetime import datetime
from trac.config import Option

INREPLYTO_TICKET_EXPR = re.compile("""<(?P<base>.+?)#(?P<id>\d+)\.(?P<modtime>\d+)@(?P<host>.+?)>""")

class MailTicketProcessor(Component):
    
    implements(IRequestFilter)
    implements(IMailProcessor)
    
    secret_hash = Option('mailprocessor', 'secret_hash', 'eLbjFQpQsjuo6OLnz9mVdbyvcU9S7MtfhISEzTBliNsLWF22hNA2oesoPUFc9NC',
        doc='Secret Hash (used to generate secure Message IDs). Please change it and keep it secret, any random string is enough')
    
    def __init__(self):
        wrapfunc(TicketNotifyEmail, "get_message_id", get_ticket_id)
        self.env.log.info("ProjectManager MailManager replaced TicketNotifyEmail.get_message_id")

    # IRequestFilter methods
    def pre_process_request(self, req, handler):
        return handler
    
    def post_process_request(self, req, template, data, content_type):
        return template, data, content_type

    #IMailProcessor methods
    def process_message(self, req, msgstr):

        project_list = get_project_list(self.env, req, return_self = True, include_errors = False)

        msg = email.message_from_string(msgstr)
        msg_from = parseaddr(msg.get("from"))[1]
        msg_subject = msg.get("subject")
        in_reply_to = msg.get("in-reply-to", "")
        
        msg_content = ""
        if not msg.is_multipart():
            msg_content = msg.get_payload(decode=True)
        else:
            for part in msg.walk():
                if part.get_content_type() == 'text/plain':
                    msg_content = part.get_payload(decode=True)
        
        
        msg_content = to_unicode(msg_content)
        
        match = INREPLYTO_TICKET_EXPR.match(in_reply_to)
        if match:
            for project, project_path, project_url, project_env in project_list:
                if not project_env:
                    continue
                    
                if os.path.basename(project_path).lower() != match.group('base').lower():
                    continue
                
                ticket = Ticket(project_env, int(match.group('id')))
                now = datetime.now(utc)
                ticket.save_changes(msg_from, msg_content, when=now)
                
                #----- Copiado de web_ui.py -----
                
                try:
                    tn = TicketNotifyEmail(project_env)
                    tn.notify(ticket, newticket=False, modtime=now)
                except Exception, e:
                    self.log.error("Failure sending notification on change to "
                            "ticket #%s: %s", ticket.id, exception_to_unicode(e))

                ## After saving the changes, apply the side-effects.
                #for controller in controllers:
                #    self.env.log.debug('Side effect for %s' %
                #                       controller.__class__.__name__)            
                #----- Fin Copiado de web_ui.py -----
                
                return (True, "Ticket reply match - %s#%s" % (match.group('base'), match.group('id')))
        
        
        return (False, None)
                

def get_ticket_id(original_callable, the_class, rcpt, modtime=None):
    """Change the way of generating Message IDs so that it's possible to identify the project
    and ticket from the Message ID. Makes it easy to match the ticket"""
    host = the_class.from_email[the_class.from_email.find('@') + 1:]
    base = os.path.basename(the_class.env.path)
    msgid = '<%s#%d.%d@%s>' % ( base, the_class.ticket.id, to_timestamp(modtime), host)    
    return msgid


