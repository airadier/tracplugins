from trac.core import Interface

class IMailProcessor(Interface):
    """Extension point for mail processing"""
    
    def process_message(req, msg_string):
        """Process a message in string format, and return a tuple of:
        (processed, log_message)"""