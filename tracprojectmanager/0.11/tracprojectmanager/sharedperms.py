# -*- coding: utf-8 -*-
# Author: Alvaro Iradier <alvaro.iradier@polartechnologies.es>

# Usage:
# 
# [trac]
# permission_store = SharedPermsStore
#
# [sharedperms]
# global_prefix = "#"
# wrapped_permission_store = DefaultPermissionStore

from trac.core import *
from trac.perm import IPermissionStore, PermissionSystem, IPermissionRequestor
from trac.config import ExtensionOption, Option
from utils import get_project_list
from sharedsettings import get_master_env

class SharedPermsStore(Component):
    implements(IPermissionStore)
    implements(IPermissionRequestor)
    
    store = ExtensionOption('sharedperms', 'wrapped_permission_store', IPermissionStore,
        'DefaultPermissionStore', """Name of the component implementing `IPermissionStore`, which is used
        for managing user and group permissions.""")
    global_prefix = Option('sharedperms', 'global_prefix', '#', 'Prefix for global users and groups')

    def get_user_permissions(self, username):
        
        #Inicialmente añadimos 'usuario' y '#usuario'
        subjects = set([username])
        
        local_permissions = []
        global_permissions = []
        
        #Recuperar filas locales
        db = self.env.get_db_cnx()
        cursor = db.cursor()
        cursor.execute("SELECT username,action FROM permission")
        rows = cursor.fetchall()        
        for user, action in rows:
            local_permissions.append((user, action))
                
        env = get_master_env(self.env)
        if env != self.env:
            #Recuperar filas de proyecto maestro, sólo las que empiecen por global_prefix
            db = env.get_db_cnx()
            cursor = db.cursor()
            cursor.execute("SELECT username,action FROM permission WHERE username LIKE %s", (self.global_prefix + "%",))
            rows = cursor.fetchall()

            for user, action in rows:
                global_permissions.append((user, action))
        else:
            global_permissions = local_permissions

        for provider in self.store.group_providers:
            subjects.update(provider.get_permission_groups(username))        

        #Permisos del usuario
        actions = set([])
        #Subjects (usuarios y grupos) que se han encontrado definidos localmente
        locally_processed = set([])
        #Subjects de los que se quiere heredar los permisos
        inherit_pending = set([])
        
        #Ahora proceder con expansión de permisos. Es un doble bucle. Primero
        #intentamos expansión local (lo que hacía el código original), y a 
        #continuación se intenta la expansión en el proyecto maestro
        
        while True:
            
            while True:
                
                num_users = len(subjects)
                num_actions = len(actions)
                
                self.env.log.debug("Starting local loop. Subjects is %s", subjects)
                for user, action in local_permissions:     
                    
                    self.env.log.debug("local_check if %s in %s", user, subjects)
                    if user in subjects:
                        self.env.log.debug("YES! parsing %s - %s", user, action)
                        
                        #Si el usuario aparece en la base de datos local, añadir
                        #a locally_processed para que no se busque en el maestro
                        locally_processed.add(user)
                        
                        if action == 'INHERIT':
                            #Caso especial, Inherit from global. Añadimos a la lista inherit_pending
                            inherit_pending.add(user)
                            
                        if action.isupper() and action not in actions:
                            self.env.log.debug("local: adding action %s", action)
                            actions.add(action)
                                
                        if not action.isupper() and action not in subjects:
                            # action is actually the name of the permission group
                            # here
                            subjects.add(action)
                            
                if num_users == len(subjects) and num_actions == len(actions):
                    break
                    
            #After exhausting local expansion, try expanding global pending groups
            num_users = len(subjects)
            num_actions = len(actions)
            self.env.log.debug("Starting global loop. locally_processed = %s, inherit_pending = %s",  locally_processed, inherit_pending)
            self.env.log.debug("subjects = %s", subjects)
            for global_user, action in global_permissions:
                user = global_user[len(self.global_prefix):]
                pending_subjects = (subjects - locally_processed) | inherit_pending
                self.env.log.debug("global_check if %s in %s ", user, pending_subjects)
                if user in pending_subjects:
                    if action.isupper() and action not in actions:
                        self.env.log.debug("global: adding action %s ", action)
                        actions.add(action)
                    if not action.isupper() and action not in subjects:
                        # action is actually the name of the permission group
                        # here
                        subjects.add(action)
                        #Exit right now, to try to expand locally first
                        break
                    
            if num_users == len(subjects) and num_actions == len(actions):
                break

        return list(actions)
            
        
    #IPermissionStore Methods
        
        return self.special_get_user_permissions(username)
        



    def get_users_with_permissions(self, permissions):
        
        #Need to replace the original code instead of calling it, because it uses
        #'self.get_users_permissions', which is not our 'get_users_permissions' function
        
        # get_user_permissions() takes care of the magic 'authenticated' group.
        # The optimized loop we had before didn't.  This is very inefficient,
        # but it works.
        result = set()
        users = set([u[0] for u in self.env.get_known_users()])
        for user in users:
            userperms = self.get_user_permissions(user)
            for perm in permissions:
                if perm in userperms:
                    result.add(user)
        return list(result)


    def get_all_permissions(self):

        #Permisos locales
        perms = self.store.get_all_permissions()
        
        env = get_master_env(self.env)
        if env != self.env:
            perms = perms + [(user, permission) \
            for user, permission in PermissionSystem(env).get_all_permissions() \
            if user.startswith(self.global_prefix)]
        
        return perms
        
    def grant_permission(self, username, action):
        
        if username.startswith(self.global_prefix):
            env = get_master_env(self.env)
            if env != self.env:
                assert False, "Global subjects can be modified only from Master Project"
                return

        env = get_master_env(self.env)
        return self.store.grant_permission(username, action)
        
    def revoke_permission(self, username, action):
        
        if username.startswith(self.global_prefix):
            env = get_master_env(self.env)
            if env != self.env:
                assert False, "Global subjects can be modified only from Master Project"
                return
        
        return self.store.revoke_permission(username, action)

    #IPermissionRequestor Methods
    def get_permission_actions(self):
        
        def expand_action(action):
            actions = set([])
            if isinstance(action, list):
                for a in action:
                    actions = actions | expand_action(a)
                return actions
            elif isinstance(action, tuple):
                actions.add(action[0])
                actions = actions | expand_action(action[1])
                return actions
            else:
                return set([action])
                
        try:
            if self.recursing: return []
        except: pass
        
        actions = ['NONE', 'INHERIT']

        #Work only in master project
        if self.env != get_master_env(self.env): return actions

        self.recursing = True
        known_actions = set(actions)
        for requestor in [r for r in PermissionSystem(self.env).requestors if r is not self]:
            known_actions = known_actions | expand_action(requestor.get_permission_actions())
        try:
            del self.recursing
        except: pass
        
        projects = get_project_list(self.env)
        for project, project_path, project_url, env  in projects:
            for requestor in [r for r in PermissionSystem(env).requestors if r is not self]:
                #if requestor == self: continue
                for action in requestor.get_permission_actions():
                    #if action not in actions: actions.append(action)
                    if isinstance(action, tuple):
                        if action[0] not in known_actions:
                            actions.append(action)
                            known_actions.add(action[0])
                    else:
                        if action not in known_actions:
                            actions.append(action)
                            known_actions.add(action)
        
        #Return permissions from all projects if this is master project
        return list(actions)
        
