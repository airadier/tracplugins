# This plugin base on WikiInclude macro By Vegard Eriksen zyp at jvnv dot net.
# See: http://projects.edgewall.com/trac/wiki/MacroBazaar#WikiInclude
# Author: yu-ji


import mimetypes
from trac.core import *
from trac.wiki.macros import WikiMacroBase
from trac.wiki.formatter import format_to_html, format_to_oneliner
from trac.wiki.model import WikiPage
from trac.mimeview.api import Context
from trac.resource import Resource
from trac.attachment import Attachment
from trac.util.text import to_unicode

__all__ = ['WikiIncludeMacro', 'VariableReplaceMacro']

def variable_replace(text, req):
    text = text.replace('$AUTHNAME', req.authname)
    text = text.replace('$PAGENAME', req.args.get('page', 'WikiStart'))
    return text
   

class VariableReplaceMacro(WikiMacroBase):
    """
    Replace aparitions of the following variables:
    
     * $AUTHNAME: The name of the user currently logged in
     * $PAGENAME: Name of the current wiki page
    """
    
    def expand_macro(self, formatter, name, args=''):
        text = variable_replace(args, formatter.req)
        return format_to_html(self.env, formatter.context, text)
        
class VariableReplaceInlineMacro(WikiMacroBase):
    """
    Replace aparitions of the following variables, returns result inline (no additional breaks):
    
     * $AUTHNAME: The name of the user currently logged in
     * $PAGENAME: Name of the current wiki page
    """
    def expand_macro(self, formatter, name, args=''):
        text = variable_replace(args, formatter.req)
        return format_to_oneliner(self.env, formatter.context, text)

class WikiIncludeMacro(WikiMacroBase):
    """
    Inserts the contents of another wiki page, attachment or other resources.
    For wiki pages, it expands arguments in the page in the form {{N}}.
    
    Example:
    {{{
    [[WikiInclude(Foo)]]
    [[WikiInclude(Foo, Argument1, Argument2, ArgumentN)]]
    }}}
    
    Also, some variables can be used in the Page name:
     * $AUTHNAME: The name of the user currently logged in
     * $PAGENAME: Name of the current wiki page
    
    Other available sources are:
        * source (like source:/path/to/file/in/repo)
        * attachment 
    For 'source' and 'attachment', second argument can be the mime type
    """
    
    def process_text(self, args, req):
        args = [x.strip() for x in args.split(',')]
        
        if len(args) == 1:
            args.append(None)
        elif len(args) != 2:
            return 'Invalid arguments "%s"' % args
            
        # Pull out the arguments
        source, dest_format = args
        try:
            source_format, source_obj = source.split(':', 1)
        except ValueError: # If no : is present, assume its a wiki page
            source_format, source_obj = 'wiki', source
                
        if source_format == 'wiki':
            
            if not req.perm.has_permission('WIKI_VIEW'):
                return ""
            
            name = variable_replace(source_obj, req)
            page = WikiPage(self.env, name)
                                    
            if page.version == 0:
                text = "Wiki page not found: !%s" % name
            else:
                text = page.text
            
            i = 1
            for arg in args[2:]:
                text = text.replace('{{%d}}' % i, arg)
                i += 1
                
        elif source_format == 'source':
            if not req.perm.has_permission('FILE_VIEW'):
                return ""
                
            repo = self.env.get_repository(req.authname)
            node = repo.get_node(source_obj)
            out = node.get_content().read()
            
            mime_type = dest_format or mimetypes.guess_type(source_obj)[0]
            
            if mime_type: 
                text = "{{{\n#!%s\n%s\n}}}" % (mime_type, out)
            else:
                text = "{{{\n%s\n}}}" % out
        elif source_format == 'attachment':
            
            try:
                attachment = Attachment(self.env,
                    'wiki',
                    req.args.get('page', 'WikiStart'),
                    filename=source_obj, db=self.env.get_db_cnx())
            except:
                return "Failed to open attachment: %s" % source_obj

            mime_type = dest_format or mimetypes.guess_type(source_obj)[0]

            fd = attachment.open()
            
            if mime_type: 
                text = "{{{\n#!%s\n%s\n}}}" % (mime_type, to_unicode(fd.read()))
            else:
                text = "{{{\n%s\n}}}" % to_unicode(fd.read())
            
            fd.close()
        else:    
            return 'Unknown source'
        
        return text
            
    def expand_macro(self, formatter, name, args=''):
        text = self.process_text(args, formatter.req)
        return format_to_html(self.env, formatter.context, text)

class WikiIncludeInlineMacro(WikiIncludeMacro):
    def expand_macro(self, formatter, name, args=''):
        text = self.process_text(args, formatter.req)
        return format_to_oneliner(self.env, formatter.context, text)