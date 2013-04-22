# -*- coding: utf-8 -*-
"""
AMB Project Manager.
Shared settings Module
"""

## trac imports
from trac.env import Environment, open_environment
from trac.core import *
from trac.web import IRequestFilter
from trac.web.session import DetachedSession, Session
from utils import wrapfunc
import time

class SharedSettings(Component):
    implements(IRequestFilter)
    
    def __init__(self):
        wrapfunc(Environment, "get_known_users", shared_get_known_users)
        self.env.log.info("ProjectManager SharedSettings replaced Environment.get_known_users")
        wrapfunc(DetachedSession, "get_session", shared_get_session)
        self.env.log.info("ProjectManager SharedSettings replaced DetachedSession.get_session")
        wrapfunc(DetachedSession, "save", shared_save_session)
        self.env.log.info("ProjectManager SharedSettings replaced DetachedSession.save")
        wrapfunc(Session, "promote_session", shared_promote_session)
        self.env.log.info("ProjectManager SharedSettings replaced Session.promote_session")


    # IRequestFilter methods
    def pre_process_request(self, req, handler):
        return handler
    
    def post_process_request(self, req, template, data, content_type):
        return template, data, content_type


def get_master_env(curr_env):
    project_path = curr_env.config.get('projectmanager', 'master_project_path', '')
    try:
        return open_environment(project_path, use_cache = True)
    except:
        raise Exception("SharedSettings ERROR opening master project. projectmanager.master_project_path is %s " % project_path)


def shared_get_known_users(original_callable, the_class, cnx=None,
    *args, **kwargs):

    env = get_master_env(the_class)

    for tuple in original_callable(env, None, *args, **kwargs):
        yield tuple


def shared_get_session(original_callable, the_class, sid, authenticated=False,
    *args, **kwargs):
        
    #Recover all values from original function call
    original_callable(the_class, sid, authenticated, *args, **kwargs)
    
    #Now get 'email' and 'name' from master project
    env = get_master_env(the_class.env)
    
    if env == the_class.env: return
    
    db = env.get_db_cnx()
    cursor = db.cursor()
    cursor.execute("SELECT name,value FROM session_attribute "
        "WHERE sid=%s and authenticated=%s"
        "AND name IN ('email', 'name')",
        (sid, int(authenticated)))

    values = {}
    for name, value in cursor:
        if name in ('email', 'name'):
            values[name] = value

    the_class.update(values)
    the_class._old.update(values)

def shared_save_session(original_callable, the_class, *args, **kwargs):
    
    authenticated = int(the_class.authenticated)
    
    #Forzar a que siempre intente crear la sesión
    db = the_class.env.get_db_cnx()
    cursor = db.cursor()
    try:
        cursor.execute("INSERT INTO session (sid,last_visit,authenticated)"
            " VALUES(%s,%s,%s)",
            (the_class.sid, int(time.time()), authenticated))
        db.commit();
    except Exception, e:
        db.rollback()

    original_callable(the_class, *args, **kwargs)

    if not authenticated: return

    env = get_master_env(the_class.env)
    if env == the_class.env: return
        
    db = env.get_db_cnx()
    cursor = db.cursor()
    
    if not the_class._old and not the_class.items():
        # The session doesn't have associated data, so there's no need to
        # persist it
        return
    
    attrs = []
    if the_class.has_key('name'):
        attrs.append((the_class.sid, authenticated, 'name', the_class['name']))
        cursor.execute("DELETE FROM session_attribute WHERE sid=%s "
            "AND name = 'name'", (the_class.sid,))
    if the_class.has_key('email'):
        attrs.append((the_class.sid, authenticated, 'email', the_class['email']))
        cursor.execute("DELETE FROM session_attribute WHERE sid=%s "
            "AND name = 'email'", (the_class.sid,))
    
    # The session variables might already have been updated by a
    # concurrent request.
    try:
        cursor.executemany("INSERT INTO session_attribute "
            "(sid,authenticated,name,value) "
            "VALUES(%s,%s,%s,%s)", attrs)
    except Exception, e:
        db.rollback()
        the_class.env.log.warning('Attributes for session %s already '
            'updated: %s' % (the_class.sid, e))
    
    db.commit()
    return
    


def shared_promote_session(original_callable, the_class, *args, **kwargs):

    original_callable(the_class, *args, **kwargs)

    env = get_master_env(the_class.env)
    if env == the_class.env: return
    
    db = env.get_db_cnx()
    cursor = db.cursor()

    #Insertar también en la tabla session del proyecto maestro,
    #por si no existiera
    try:
        cursor.execute("INSERT INTO session (sid,last_visit,authenticated)"
        " VALUES(%s,%s,1)",
        (the_class.req.authname, 0))
    except Exception, e:
        db.rollback()
    
    db.commit()
    return
    


