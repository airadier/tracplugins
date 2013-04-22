<?cs include "header.cs"?>
<?cs include "macros.cs"?>

<div id="ctxtnav"></div>

<div id="content" class="projectlist">

    <h1>Project list</h1>
    <form id="filter" method="post">
    <fieldset id="filters">
        <legend>Filters:</legend>
        Status: 
            <select id="status" name="status"><?cs
            each:st = statuses ?><option value="<?cs var:st.name ?>"<?cs
            if:st.selected ?> selected="selected"<?cs /if ?>><?cs
            var:st.label ?></option><?cs
            /each ?></select>
    </fieldset>
    <div class="buttons">
        <input type="hidden" name="order" value="<?cs var:order ?>" />
        <input type="hidden" name="desc" value="<?cs var:desc ?>" />
        <input type="submit" name="update" value="Update" />
    </div>            
    <hr />
    </form>
    <table class="listing projectslist" >
        <thead> <tr>

            <th><a href="?order=name<?cs if order == "name" && !desc ?>&desc=1<?cs /if ?><?cs if status ?>&status=<?cs var:status ?><?cs /if ?>" title="Sort by Name">Project</a></th>
            <th><a href="?order=company<?cs if order == "company" && !desc ?>&desc=1<?cs /if ?><?cs if status ?>&status=<?cs var:status ?><?cs /if ?>" title="Sort by Company">Company</a></th>
            <th><a href="?order=created<?cs if order == "created" && !desc ?>&desc=1<?cs /if ?><?cs if status ?>&status=<?cs var:status ?><?cs /if ?>" title="Sort by Creation Date">Created</a></th>
            <th><a href="?order=started<?cs if order == "started" && !desc ?>&desc=1<?cs /if ?><?cs if status ?>&status=<?cs var:status ?><?cs /if ?>" title="Sort by Start Date">Started</a></th>
            <th><a href="?order=scheduled<?cs if order == "scheduled" && !desc ?>&desc=1<?cs /if ?><?cs if status ?>&status=<?cs var:status ?><?cs /if ?>" title="Sort by Scheduled Date">Scheduled</a></th>
            <th><a href="?order=finished<?cs if order == "finished" && !desc ?>&desc=1<?cs /if ?><?cs if status ?>&status=<?cs var:status ?><?cs /if ?>" title="Sort by Finished Date">Finished</a></th>
            <th><a href="?order=percent_finished<?cs if order == "percent_finished" && !desc ?>&desc=1<?cs /if ?><?cs if status ?>&status=<?cs var:status ?><?cs /if ?>" title="Sort by Percent">%</a></th>
            <th><a href="?order=status<?cs if order == "status" && !desc ?>&desc=1<?cs /if ?><?cs if status ?>&status=<?cs var:status ?><?cs /if ?>" title="Sort by Status">Status</a></th>
            <th><a href="?order=client<?cs if order == "client" && !desc ?>&desc=1<?cs /if ?><?cs if status ?>&status=<?cs var:status ?><?cs /if ?>" title="Sort by Client">Client</a></th>
            <th><a href="?order=manager<?cs if order == "manager" && !desc ?>&desc=1<?cs /if ?><?cs if status ?>&status=<?cs var:status ?><?cs /if ?>" title="Sort by Manager">Manager</a></th>
            <th><a href="?order=last_login<?cs if order == "last_login" && !desc ?>&desc=1<?cs /if ?><?cs if status ?>&status=<?cs var:status ?><?cs /if ?>" title="Sort by Activity">Last Activity</a></th>
        </tr></thead>        
        <tbody>
            <?cs each:project = projects ?>
                <tr>
                    <td class="title"><a href='<?cs var:project.href ?>'><?cs var:project.name ?></a><br/><small><?cs var:project.description ?></small></td>
                    <td><?cs var:project.company ?></td>
                    <td><?cs var:project.created ?></td>
                    <td><?cs var:project.started ?></td>
                    <td><?cs var:project.scheduled ?></td>
                    <td><?cs var:project.finished ?></td>
                    <td class="percent">
                        <table class="progress">
                           <tr>
                            <td class="closed" style="width: <?cs var:#project.percent_finished ?>%"></td>
                            <td class="open" style="width: <?cs var:#project.percent_remaining ?>%"></td>
                           </tr>
                      </table>
                      <p><?cs var:#project.percent_finished ?>%</p>
                    </td>
                    <td><?cs var:project.status ?></td>
                    <td><?cs var:project.client ?></td>
                    <td><?cs var:project.manager ?></td>
                    <td><?cs var:project.last_login ?></td>
                </tr>
        </tbody>
    <?cs /each ?>
    </table>
</div>

<?cs include "footer.cs"?>