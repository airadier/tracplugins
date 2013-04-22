#!/usr/bin/python
# -*- coding: utf-8 -*-


from trac.core import *
from trac.wiki.macros import WikiMacroBase
from trac.perm import IPermissionRequestor
from trac.wiki.model import WikiPage
from trac.wiki.api import IWikiPageManipulator
import sys
import traceback
from StringIO import StringIO
from cgi import escape

class Field(object):
    
    def __init__(self, name, title, default_value = None, maxlen = None, description = None):
        self.name = name
        self.title = title
        self.default_value = default_value
        self.maxlen = maxlen
        self.description = description

        self.value = None
    
    def set_value(self, value):
        self.value = value
    
    def get_name(self):
        return self.name
    
    def get_value(self):
        return self.value or self.default_value
    
    def get_label(self):
        return self.title or "No label"
    
    def get_input(self):
        return "<input type='text' name='%s' value='%s'/>" % (self.name, self.get_value() or "")
        
    def get_description(self):
        return self.description or ""

class Form(object):
    
    def __init__(self, name, title=None, submit_title=None, fields=()):
        self.name = name
        self.title = title
        self.submit_title = 'Execute'
        self.fields = fields
        self.posted = False
        Form.forms.append(self)
        self.__set_args(Form.formatter.req.args)
        
    def __getitem__(self, key):
        """Access to field values using dictionary notation: form['fieldname']"""
        for field in self.fields:
            if type(field) is not Field: continue
            if field.get_name() == key:
                return field.get_value()
        return None
        
    def __setitem__(self, key, item):
        """Set field values using dictionary notation: form['fieldname'] = 'value'"""
        for field in self.fields:
            if type(field) is not Field: continue
            if field.get_name() == key:
                field.set_value(item)
                return
        raise KeyError
    
    def __set_args(self, args):
        self.args = args
        self.posted = self.args.has_key('form') and self.args['form'] == self.name
        for field in self.fields:
            if type(field) is not Field: continue
            if self.args.has_key(field.get_name()):
                field.set_value(self.args[field.get_name()])
        
    def get_html(self):
        if self.title:
            html = u"<div><strong>%s</strong></div>" % escape(self.title)
        else:
            html = u""

        html = html + "<form name='%s' method='get'><table>" % self.name
        for field in self.fields:
            if type(field) is not Field: 
                html = html + "<tr><td colspan='3'>Not a valid field</td></tr>"
            else:
                try:
                    html = html + u"<tr><td><label for='%s'>%s:</label></td><td>%s</td><td>%s</td></tr>" % (
                        field.get_name(), field.get_label(), field.get_input(), field.get_description())
                except:
                    info = sys.exc_info()
                    html = html + "<tr><td colspan='3' style='color: red'>%s for field <strong>%s</strong>: %s</td></tr>" % \
                        (info[0].__name__, field.get_name(), escape(str(info[1])))
        html = html + "</table><input type='hidden' name='form' value='%s'><input type='submit' value='%s'/>" % (self.name, self.submit_title)
        html = html + "</form>"
            
        return html

class ScriptletMacro(WikiMacroBase):
    """
    TracScriptlets Macro - Allows you to evaluate python scripts and embed the result.
    
    Usage example:
    
{{{
#!python
    {{{
    #!Scriptlet

    [options]
    debug = False

    [forms]

    def function_default_value():
        from datetime import datetime
        return datetime.now()

    Form('myform', title='Form title', fields = (
        Field('field1', 'Field 1 Description', 'field_default_value', 'field long description'),
        Field('field2', 'Field 2 Description', function_default_value(), None),
    ))

    [script]

    if myform.posted:
        print "<div>"
        print "<p>You have clicked submit in the form<p>"
        print "<p>field1 = <strong>%s</strong></p>" % myform['field1']
        print "<p>field2 = <strong>%s</strong></p>" % myform['field2']

    }}}
}}}
    
    TracScriptlets will execute the code in the '''[script]''' section, and embed the output of the script
    in the wiki page.
    
    '''Unicode strings'''
    
    Trac works with unicode strings. When using special characters (outside the standard ASCII table),
    make sure you're using unicode strings:

     * '''WRONG:''' my_string = 'áéíóúñ'
     * '''CORRECT:''' my_string = u'áéíóúñ'
    
    If not sure, always use unicode strings.
    
    '''Options section'''
    
    Options sections must start with '''[options]''' header. Lines in this section will be interpreted in a
    limited scope. Variables declared here will be available in the script code under a dictionary named
    'options'. For example:
    
{{{
#!python
    if options['debug']: print "Debug mode on"
}}}
    
    '''Available options:'''
    
     * '''debug = True | False''' # If debug is enabled, aditional information is printed

    '''Forms section'''
    
    TracScriptlets makes it easy to define and process forms in your scripts. The lines in the '''[forms]'''
    section will be evaluated in a limited scope, where two classes are defined by default:
    'Form' and 'Field'.
    
    By creating Form instances, you define forms to be displayed before your scriptlet output. A form
    instance is created by:
    
{{{
#!python
    Form('form_name', 'Form Header or Title', form_fields)
}}}
    
    title and fields are named parameters, so this is correct too:
    
{{{
#!python
    Form('form_name', fields=form_fields, title='Form Header or Title')
}}}
        
       * '''form_name''' is a string, and must be a correct variable name in python (that is, no spaces, etc).
    A dictionary-like variable with this name will be made available for your script code. This
    dictionary will contain an entry for each field in the form, for example:
    
{{{
#!python
    form_name['field1_name'],
}}}
    
    that can read or written. Also, the property '''form_name.posted''' is True when the user has pressed the
    submit button in the form, False otherwise.
    
       * '''title''' parameter sets the string to be displayed as the form header
       * '''fields''' parameter must be a list or tuple of Field instances, defining the fields of the form
    
    To create a Field instance, use:
    
{{{
#!python
    Field(name, title, default_value, maxlen, description)
}}}
        
    all parameters except 'name' and 'title' are named parameters, and can be ommited. 
    
    * '''name''' must be a valid dictionary key string, and should be kept simple. This field will be available
    in the corresponding form as form['name']
    * '''title''' is the label of this field (shown next to the field entry)
    * '''default_value''' is a fixed value or a function call. This will be evaluated when creating the form,
    and the value assigned to the field.
    * '''maxlen''' maximum field length
    * '''description''': a long description or help text for the field
    
    """
    
    implements(IPermissionRequestor)
    implements(IWikiPageManipulator)
    
    def out(self, data):
        self.output = self.output + data

    
    def expand_macro(self, formatter, name, args):
        
        self.output = u""
        self.out("<div class='scriptlet'>")

        if not formatter.req.perm.has_permission('SCRIPTLET_RUN'):
            self.out("Permission <strong>SCRIPTLET_RUN</strong> required to run scriptlets</div>")
            return self.output

        lines = args.splitlines()

        ##########################################
        ## Format [[Scriptlet(ScriptName)]]
        if len(lines) <= 1:
            
            #Try to load ScriptName.scriptlet wiki page            
            page_name = args + ".scriptlet"
            page = WikiPage(self.env, page_name)

            #Add scriptlet title and controls div
            self.out("<div class='scriptlet_title'>%s" % page_name)
            if page.version == 0:
                #Page does not exist yet, show Create button
                if formatter.req.perm.has_permission('SCRIPTLET_MODIFY'):
                    self.out(" <a href='%s'>[Create]</a>" % formatter.req.href.wiki(page_name, {'action': 'edit', 'text':'{{{\n#!python\n\n[options]\n\n[forms]\n\n[script]\n\n}}}'}))
                self.out("</div>Page <strong>%s</strong> does not exist, please create it" % page_name)
                lines = []
            else:
                #Page already exists. Show Edit button, and load it in 'lines'
                if formatter.req.perm.has_permission('SCRIPTLET_MODIFY'):
                    self.out(" <a href='%s'>[Edit]</a>" % formatter.req.href.wiki(page_name, {'action': 'edit'}))
                self.out("</div>")
                lines = page.text.strip().lstrip("{{{").rstrip("}}}").splitlines()
                
        ##########################################

        # For inline scripts, require SCRIPTLET_MODIFY permissions
        elif not formatter.req.perm.has_permission('SCRIPTLET_MODIFY'):
            self.out("Permission <strong>SCRIPTLET_MODIFY</strong> required to run inline (using <em>[script]</em> or <em>[forms]</em>) scriptlets</div>")
            return self.output

        #############################################
        ## Split lines in options, forms and script
        
        form_lines = []
        code_lines = []
        option_lines = []
        current_list = None
        
        for line in lines:            
            if line.strip().lower() == '[options]':
                current_list = option_lines
            elif line.strip().lower() == '[forms]':
                current_list = form_lines
            elif line.strip().lower() == '[script]':
                current_list = code_lines
            elif current_list is not None:
                current_list.append(line)
                
        #############################################

        #Initialize options. Debug mode disabled by default
        options = {
            'debug': False,
        }

        #Initialize forms framework
        forms = [ ]
        Form.forms = forms
        Form.formatter = formatter
        #Add 'Form' and 'Field' classes to form parsing environment
        forms_env = { 
            'Form': Form,
            'Field': Field,
        }

        #Add 'request' and 'options' to script execution environment
        exec_env = {
            'request': formatter.req,
            'options': options,
        }
        
        script_output = u""
        errors = ""
        
        #Execute the option lines
        errors = execute(option_lines, options, 'options')
        if not errors: 
            #Execute the forms lines in the forms environment
            errors = execute(form_lines, forms_env, 'forms')
                
        if not errors:
            #Add the defined forms to the execution environment
            for form in forms:
                exec_env[form.name] = form
                    
        #If enabled, show debug information
        if options['debug']:
            self.out("<div class='scriptlet_output' style='border: solid 1px blue; padding: 15px;'>")
            self.out("<b>Options:</b><pre>%s</pre>" % escape(format_options(options)))
            self.out("<b>Forms:</b><pre>%s</pre>" % escape(str(forms)))
            self.out("<b>Code:</b><pre>%s</pre>" % escape("\n".join(code_lines)))
            self.out("</div")

        if not errors:
            #Execute script code in the exec environment
            sys.stdout = StringIO()
            errors = execute(code_lines, exec_env, 'script')

            #Add the auto generated forms HTML code to the output
            self.out("<div id='autoforms'>")
            self.out("".join([f.get_html() for f in forms]))
            self.out("</div>")
            
            script_output = script_output +  sys.stdout.getvalue()
        
        #Show errors if any, or script output if no errors
        if not errors:
            if options['debug']:
                self.out("<div style='border: solid 2px darkgreen; padding: 10px;'>")
                self.out("%s</div>" % script_output)
            else:            
                self.out(script_output)
        else:
            self.out ("<div style='margin: 10px; border: solid 2px red; padding: 10px;'>%s</div>" % errors)
            
        self.out("</div>")
        return  self.output


    #IPermissionRequestor Methods
    def get_permission_actions(self):
        return ['SCRIPTLET_RUN', 'SCRIPTLET_MODIFY']
        
    #IWikiPageManipulator Methods
    def prepare_wiki_page(self, req, page, fields):
        """Not currently called, but should be provided for future
        compatibility."""
        pass

    def validate_wiki_page(self, req, page):
        """Avoid editing .scriptlet pages with no permissions"""
        if page.name.endswith('.scriptlet') \
            and not req.perm.has_permission('SCRIPTLET_MODIFY'):
            return [(None, 'Need SCRIPTLET_MODIFY permissions')]
            
        return []

def format_options(options):
    return "\n". join(["%s = %s" % (name, value) for name,value in options.iteritems()])
    

def execute(lines, context, title):
    errors = u""
    errors = errors + "<strong>Error in section: [%s]</strong><br/>" % escape(title)
    
    try:
        exec "\n".join(lines) in {}, context
    except SyntaxError, ex:
        errors = errors + "Syntax error, line %d, %d: %s" % (ex.lineno - 2, ex.offset, escape(ex.msg))
        errors = errors + "<pre style='color:red'>%s%s%s</pre>" % (escape(ex.text or ""),(' ' * (ex.offset or 0)), "^")
        return errors
    except Exception:
        info = sys.exc_info()
        trace = traceback.extract_tb(info[2])
        line = trace[-1][1]
        
        if trace[-1][0] == '<string>':
            start_line = line - 5 if line > 5 else 0
            errors = errors + "%s, line %d: %s" % (info[0].__name__, line, escape(str(info[1])))
            errors = errors + "<pre>%s\n" % escape("\n".join(lines[start_line:line-1]))
            try:
                errors = errors + "<scan style='color:red'>%s</span>\n" % escape(lines[line-1])
                errors = errors + "<scan style='color:red'>%s</span>" % ("^" * len(lines[line-1]))
            except:
                pass
            errors = errors + "</pre>"
            
        else:
            errors = errors + "%s, line %d: %s" % (info[0].__name__, line, escape(str(info[1])))
            errors = errors + "<pre>%s</pre>" % escape("\n".join(traceback.format_tb(info[2])))
        return errors

    return None
