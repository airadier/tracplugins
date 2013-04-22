import os
import posixpath
from trac.env import open_environment


def get_property(env, property, default=None):
    """
    Return the value of the inquired property, or default if property is missing
    """
    
    db = env.get_db_cnx()
    cursor = db.cursor()
    
    try:
        cursor.execute("SELECT value FROM pm_properties WHERE key = %s", (property,))
    except:
        return default
        
    row = cursor.fetchone()
    if row:
        return row[0]
    else:
        return default


def set_property(env, property, value):
    """
    Sets the value of the property
    """
    db = env.get_db_cnx()
    cursor = db.cursor()
    try:
        cursor.execute("UPDATE pm_properties SET value = %s WHERE key = %s", (value, property))
        db.commit()
    except:
        return False
        
    return True


def get_all_tags(env, req=None):
    tags = set([])
    projects = get_project_list(env, req, True)
    for project in projects:
        tags.update(set(get_property(project[3], 'tags', '').split()))
    
    return list(tags)

def get_project_list(env, req=None, return_self = False, include_errors = False):
    
    # get search path
    search_path, this_project = os.path.split(env.path)
    if req: base_url, _ = posixpath.split(req.abs_href())
    else: base_url = ''

    #Closes #4158, thanks to jholg
    if 'tracforge' in env.config: 
        if env.config.get('tracforge', 'master_path') == env.path: 
            base_url = '/'.join((base_url, this_project, 'projects'))  

    projects = []
    for project in os.listdir(search_path):

        # skip our own project
        if not return_self and project == this_project:
            continue
        
        # make up URL for project
        project_url = '/'.join( (base_url, project) )              
        # make up path for project
        project_path = os.path.join(search_path, project)
        if not os.path.isdir( project_path ):
            continue
        try:
            env = open_environment(project_path, use_cache = True)
            projects.append((project, project_path, project_url, env))
        except:
            if include_errors:
                projects.append((project, project_path, project_url, None))
        
        
    return projects
    
    
# ===========================================================================
# Thanks to osimons for this excellent Python method replacement wizardry...
#
# ===========================================================================

def wrapfunc(obj, name, processor, avoid_doublewrap=True):
     """ patch obj.<name> so that calling it actually calls, instead,
             processor(original_callable, *args, **kwargs)

     Function wrapper (wrap function to extend functionality)
     Implemented from Recipe 20.6 / Python Cookbook 2. edition

     Example usage of funtion wrapper:

     def tracing_processor(original_callable, *args, **kwargs):
         r_name = getattr(original_callable, '__name__', '<unknown>')
         r_args = map(repr, args)
         r_args.extend(['%s=%s' % x for x in kwargs.iteritems()])
         print "begin call to %s(%s)" % (r_name, ", ".join(r_args))
         try:
             result = original_callable(*args, **kwargs)
         except:
             print "EXCEPTION in call to %s" % (r_name,)
             raise
         else:
             print "call to %s result: %r" % (r_name, result)
             return result

     def add_tracing_prints_to_method(class_object, method_name):
         wrapfunc(class_object, method_name, tracing_processor)
     """
     # get the callable at obj.<name>
     call = getattr(obj, name)
     # optionally avoid multiple identical wrappings
     if avoid_doublewrap and getattr(call, 'processor', None) is processor:
         return
     # get underlying function (if any), and anyway def the wrapper closure
     original_callable = getattr(call, 'im_func', call)
     def wrappedfunc(*args, **kwargs):
         return processor (original_callable, *args, **kwargs)
     # set attributes, for future unwrapping and to avoid double-wrapping
     wrappedfunc.original = call
     wrappedfunc.processor = processor
     # 2.4 only: wrappedfunc.__name__ = getattr(call, '__name__', name)
     # rewrap staticmethod and classmethod specifically (if obj is a class)
     import inspect
     if inspect.isclass(obj):
         if hasattr(call, 'im_self'):
             if call.im_self:
                 wrappedfunc = classmethod(wrappedfunc)
         else:
             wrappedfunc = staticmethod(wrappedfunc)
     # finally, install the wrapper closure as requested
     setattr(obj, name, wrappedfunc)


def unwrapfunc(obj, name):
     """ undo the effects of wrapfunc(obj, name, processor) """
     setattr(obj, name, getattr(obj, name).original)
