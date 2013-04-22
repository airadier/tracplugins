<h2>Project Properties</h2>
<form class="mod" id="modpro" method="post"><?cs
if:database_ok ?>
    <fieldset>
        <legend>Edit Project Properties:</legend>
        <div class="field">
            <label>Status:
            <select id="status" name="status"><?cs
            each:st = admin.project.statuses ?><option value="<?cs var:st.name ?>"<?cs
            if:st.selected ?> selected="selected"<?cs /if ?>><?cs
            var:st.label ?></option><?cs
            /each ?></select>-</label><label> %: <input type="text" name="percent" value="<?cs
            var:admin.project.percent ?>" /> 
            </label>
        </div>
    <div class="field">
        <label>Company:<br /> <input type="text" class="long" name="company" value="<?cs
        var:admin.project.company ?>" /></label>
    </div>
    <div class="field">
        <label>Started:<br />
        <input type="text" id="date_started" class="date" name="date_started" size="<?cs
        var:len(admin.date_hint) ?>" value="<?cs
        var:admin.project.date_started ?>" title="Format: <?cs var:admin.date_hint ?>" />
        <em>Format: <?cs var:admin.date_hint ?></em>
        </label>
    </div>
    <div class="field">
        <label>Scheduled to:<br />
        <input type="text" id="date_scheduled" class="date" name="date_scheduled" size="<?cs
        var:len(admin.date_hint) ?>" value="<?cs
        var:admin.project.date_scheduled ?>" title="Format: <?cs var:admin.date_hint ?>" />
        <em>Format: <?cs var:admin.date_hint ?></em>
        </label>
    </div>
        
    <div class="field">
        <label>     
        Closed:<br />
        <input type="text" id="date_finished" class="date" name="date_finished" size="<?cs
        var:len(admin.date_hint) ?>" value="<?cs
        var:admin.project.date_finished ?> " title="Format: <?cs
        var:admin.date_hint ?>" />
        <em>Format: <?cs var:admin.date_hint ?></em>
        </label>
    </div>

    <div class="field">
        <label>Client:<br /> <input type="text" class="long" name="client" value="<?cs
        var:admin.project.client ?>" /></label>
    </div>
        
    <div class="field">
        <label>Manager:<br /> <input type="text" class="long" name="manager" value="<?cs
        var:admin.project.manager ?>" /></label>
    </div>


    <div class="buttons">
    <input type="submit" name="save" value="Save">
    </div>
    </fieldset><?cs
else ?>
    <p>Project Manager properties database tables are missing.</p>
    <div class="buttons">
    <input type="submit" name="createdb" value="Create Tables">
    </div><?cs
/if ?>

</form>

