"""
Polar Technologies Email Fetcher
"""

import re
import poplib
from mailticketprocessor import IMailProcessor
from trac.web import IRequestHandler, RequestDone
from trac.config import Option
from trac.core import *

class POPFetcher(Component):
    
    implements(IRequestHandler)

    mail_processors = ExtensionPoint(IMailProcessor)

    pop_server = Option('emailfetch', 'pop_server', '',
        doc='POP Server for mail fetching')

    pop_user = Option('emailfetch', 'pop_user', '',
        doc='POP username')

    pop_password = Option('emailfetch', 'pop_password', '',
        doc='POP password')

    ##################################
    ## IRequestHandler
    
    def match_request(self, req):
        return re.match(r'/popfetch/?$', req.path_info)

    def process_request(self, req):
        server = req.args.has_key('server') and req.args['server'] or self.pop_server
        user = req.args.has_key('user') and req.args['user'] or self.pop_user
        password = req.args.has_key('pass') and req.args['pass'] or self.pop_password
        
        try:
            s = poplib.POP3(server)
            s.user(user)
            s.pass_(password)
            
            list_messages = s.list()[1]
            
            messages = []
            
            for list_entry in list_messages:
                msg_num = list_entry.split()[0]
                messages.append("\n".join(s.retr(msg_num)[1]))
                s.dele(msg_num)

            s.quit()
            
            processed = 0
            v = ""
            
            for msg in messages:
                
                mail_processed = False
                logmsg = ""                
                
                for mail_processor in self.mail_processors:                    
                    try:
                        result, logmsg = mail_processor.process_message(req, msg)
                        if result:
                            mail_processed = True
                            break
                    except Exception as ex:
                        self.env.log.error("Error processing mail: %s", ex.message)
                    
                if mail_processed:
                    processed += 1
                    v += "**** Processed: %s\n" % (logmsg)
                else:
                    v += "\n!!!! Unprocessed email !!!!:\n"
                    v += "--------------------------- Begin Mail ---------------------------\n"
                    v += msg
                    v += "\n---------------------------- End Mail ----------------------------\n\n"

            req.send("+OK\n%d of %d messages processed\n\n%s" % (processed, len(messages), v), 'text/plain', status=200)
        
        except RequestDone:
            pass            
        except Exception as ex:
            req.send("%s" % ex.message, 'text/plain', status=500)
        
        return None

    ##################################
