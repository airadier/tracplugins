#!/usr/bin/python
# -*- coding: utf-8 -*-


from trac.wiki.macros import WikiMacroBase
from cgi import escape
from utils import get_project_list
from trac.web.href import Href
from admin import STATUS, get_property


from trac.timeline.web_ui import TimelineModule
from datetime import datetime, timedelta
from trac.mimeview.api import Context
from trac.util import to_unicode
from trac.util.datefmt import format_date, format_datetime
from trac.web.chrome import add_stylesheet
import traceback

class LastProjects(WikiMacroBase):
    """
    LastProjectsMacro - Display a list and link of latest visited projects
    
    Usage example:
    [[LastProjects(10)]] Shows 10 latest visited projects
    """
    
    def expand_macro(self, formatter, name, text, args=None):
        
        assert text.isdigit(), "Argument must be a number"
        
        if formatter.req.authname == 'anonymous':
            return "<div class='lastprojects'>Not available</div>"
        
        projects = get_project_list(self.env, formatter.req)
        last_projects = []
        for project, path, url, env in projects:
            cnx = env.get_db_cnx()
            cursor = cnx.cursor()
            cursor.execute("SELECT last_visit FROM session WHERE authenticated=1 AND sid=%s", (formatter.req.authname,))
            row = cursor.fetchone()
            if row:
                last_projects.append((project, path, url, env, row[0]))
        
        last_projects.sort(cmp = lambda x,y: x[4] < y[4] and 1 or -1)
        
        out = "<ul class='lastprojects'>"
        for project, path, url, env, last_visit in last_projects[0:int(text)]:
            out = out + "<li class='lastprojectitem'><a href='%s'>%s</a></li>" % (url, env.project_name)
            
        if len(last_projects) > int(text):
            out = out + "<li>...</li>"            
            
        out = out + "</ul>"
        return out


class ReportedTickets(WikiMacroBase):
    """
    ReportedTickets - Display a list of reported tickets, with highest priority first
    
    Usage example:
    [[ReportedTickets(10)]] 
    """
    
    def expand_macro(self, formatter, name, text, args=None):
        
        assert text.isdigit(), "Argument must be a number"
        
        if formatter.req.authname == 'anonymous':
            return "<div class='reportedtickets'>Not available</div>"
        
        projects = get_project_list(self.env, formatter.req)
        tickets = []
        for project, path, url, env in projects:
            
            project_status = get_property(env, 'status', 'unknown')
            if project_status not in ('unknown', 'active'): continue
            
            cnx = env.get_db_cnx()
            cursor = cnx.cursor()
            cursor.execute("""
            SELECT ticket.id, ticket.summary, ticket.time, enum.value prio_num
            FROM ticket
            INNER JOIN enum ON enum.name = ticket.priority
            WHERE enum.type = 'priority' AND status = 'new' AND reporter = %s
            """, (formatter.req.authname,))
            
            for ticket in cursor:
                tickets.append((project, path, url, env, ticket[0], ticket[1], ticket[2], ticket[3]))
        
        tickets.sort(cmp = lambda x,y: x[-1] > y[-1] and 1 or (x[-1] < y[1] and -1 or (x[-2] > y[-2] and 1 or -1)))
        
        out = "<ul class='reportedtickets'>"
        for project, path, url, env, id, summary, time, prio in tickets[0:int(text)]:
            out = out + "<li class='reportedticketsitem'><a href='%s'><strong>%s#%s</strong>: %s</a></li>" % (Href(url).ticket(id), project, id, summary)

        if len(tickets) > int(text):
            out = out + "<li>...</li>"

        out = out + "</ul>"
        return out
        
class AssignedTickets(WikiMacroBase):
    """
    AssignedTickets - Display a list of assigned tickets on each project for current user 
    
    Usage example:
    [[AssignedTickets(10)]] 
    """
    
    def expand_macro(self, formatter, name, text, args=None):
        
        assert text.isdigit(), "Argument must be a number"
        
        if formatter.req.authname == 'anonymous':
            return "<div class='assignedtickets'>Not available</div>"
        
        out = "<table class='assignedtickets'>"
        out = out + "<tr><th rowspan='2'>Proyecto</th><th rowspan='2'>New</th><th colspan='5'>Priority</th><th rowspan='2'>Total</th></tr>"
        out = out + "<tr><th>P1</th><th>P2</th><th>P3</th><th>P4</th><th>&gt;=5</th></tr>"
        projects = get_project_list(self.env, formatter.req)
        user = formatter.req.authname
        project_tickets = []
        for project, path, url, env in projects:
            
            project_status = get_property(env, 'status', 'unknown')
            if project_status not in ('unknown', 'active'): continue
            
            tickets = {'new': 0, '1':0, '2':0, '3':0, '4':0, '>=5':0, 'total': 0}
            
            cnx = env.get_db_cnx()
            cursor = cnx.cursor()
            cursor.execute("""
            SELECT enum.value prio_num, enum.name prio_name, COUNT(ticket.id)
            FROM enum
            LEFT JOIN ticket ON ticket.priority = enum.name AND status <> 'closed' AND status <> 'new' AND owner = %s
            WHERE enum.type = 'priority'
            GROUP BY (enum.value)
            """, (user, ))


            #cursor.execute("""
            #SELECT enum.value prio_num, COUNT(ticket.id)
            #FROM ticket
            #INNER JOIN enum ON enum.name = ticket.priority
            #WHERE enum.type = 'priority' AND status <> 'closed' AND status <> 'new' AND owner = %s
            #GROUP BY (enum.value)
            #""", (user,))
            
            for row in cursor:
                if row[0] in ('1', '2', '3', '4'):
                    tickets[row[0]] = (row[1], row[2])
                else:
                    tickets['>=5'] = tickets['>=5'] + row[2]
                tickets['total'] = tickets['total'] + row[2]
                
            cursor.execute("""
            SELECT COUNT(ticket.id)
            FROM ticket
            WHERE status = 'new' AND owner = %s
            """, (user,))
            
            row = cursor.fetchone()
            if row:
                tickets['new'] = row[0]
                tickets['total'] = tickets['total'] + row[0]
            
            
            if tickets['total'] > 0:
                
                project_tickets.append((project, url, tickets))
        
        
        project_tickets.sort(cmp = lambda x,y: x[2]['new'] < y[2]['new'] and 1 or -1)
        for project, url, tickets in project_tickets[:int(text)]:
        
            href = Href(url)
            out = """%s
            <tr>
                <td class='name'><a href='%s'>%s</a></td>
                <td class='new'><a href='%s'>%d</a></td>
                <td><a href='%s'>%d</a></td>
                <td><a href='%s'>%d</a></td>
                <td><a href='%s'>%d</a></td>
                <td><a href='%s'>%d</a></td>
                <td><a href='%s'>%d</a></td>
                <td class='total'><a href='%s'>%d</a></td>
            </tr>
                """ % (out,
                href.query(), project,
                href.query(status='new', owner=user), tickets['new'],
                href.query(status=['!closed', '!new'], priority=tickets['1'][0], owner=user), tickets['1'][1],
                href.query(status=['!closed', '!new'], priority=tickets['2'][0], owner=user), tickets['2'][1],
                href.query(status=['!closed', '!new'], priority=tickets['3'][0], owner=user), tickets['3'][1],
                href.query(status=['!closed', '!new'], priority=tickets['4'][0], owner=user), tickets['4'][1],
                href.query(status=['!closed', '!new'], owner=user), tickets['>=5'],
                href.query(status='!closed', owner=user), tickets['total'])

        if len(project_tickets) > int(text):
            out = out + "<tr><td colspan='8'>...</td></tr>"

        out = out + "</table>"
        return out
        

EVENT_CACHE_INTERVAL = 60 #seconds
EVENT_MAX_DAYS = 15 #days

class LastEvents(WikiMacroBase):
    """
    LastEvents - Display latest events in all projects
    
    Usage example:
    [[LastEvents(10)]] 
    """
    
    def expand_macro(self, formatter, name, text, args=None):
        
        assert text.isdigit(), "Argument must be a number"

        out = "<dl class='lastevents'>"
        add_stylesheet(formatter.req, 'tracprojectmanager/css/lastevents.css')

        all_events = []
        if hasattr(self.env, 'cached_lastevents'):
            expiration = self.env.cached_lastevents[1] + timedelta(seconds = EVENT_CACHE_INTERVAL)
            if datetime.now() < expiration:
                all_events = self.env.cached_lastevents[0]            
        
        if not all_events:        
            stop = datetime.now(formatter.req.tz)
            start = stop - timedelta(days=EVENT_MAX_DAYS)
            
            projects = get_project_list(self.env, formatter.req)
            user = formatter.req.authname
            
            for project, project_path, project_url, env in projects:
                env_timeline = TimelineModule(env)
                for provider in env_timeline.event_providers:
                    filters = [x[0] for x in provider.get_timeline_filters(formatter.req)]
                    self.env.log.info("Project %s - Filters: %s", project, filters)
                    try:
                        events = provider.get_timeline_events(formatter.req, start, stop, filters)
                        #self.env.log.info("Event count: %d", len([x for x in events]))
                        
                        for event in events:                            
                            context = Context(formatter.resource, Href(project_url), formatter.req.perm)
                            context.req = formatter.req
                            #context = Context.from_request(formatter.req)
                            
                            if len(event) == 6: # 0.10 events
                                kind, url, title, date, author, desc = event
                            else: # 0.11 events
                                if len(event) == 5: # with special provider
                                    kind, date, author, data, provider = event
                                else:
                                    kind, date, author, data = event         
                                    
                                title = to_unicode(provider.render_timeline_event(context, 'title', event))
                                url = provider.render_timeline_event(context, 'url', event)
                                desc = to_unicode(provider.render_timeline_event(context, 'description', event))
                            
                            all_events.append((project, kind, date, title, url, author, desc))
                    except Exception, ex: 
                        #import sys
                        self.env.log.warning("Exception: %s" % traceback.format_exc())
                        #out = out + "%s<br/>" % traceback.format_exc()
                        
            all_events.sort(cmp = lambda x,y: x[2] < y[2] and 1 or -1)
            self.env.cached_lastevents = [all_events, datetime.now()]
                
        for ev in all_events[:int(text)]:
            out = out + "<dt class='%s'><a href='%s'><strong>%s</strong> <span class='time'>%s</span> %s by <span class='author'>%s</a></dt>" % (ev[1], ev[4], ev[0], format_date(ev[2]), ev[3], ev[5])
            out = out + "<dd class='%s'>%s</dd>" % (ev[1], ev[6])
        
        if len(all_events) > int(text):
            out = out + "<dt>...</dt>"

        out = out + "</dl>"
        return out