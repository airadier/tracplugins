<form class="new" id="newpro" method="post">
<?cs if: !project_created ?>
    <h2>Make New Project</h2>
    <fieldset>
        <legend>Create a New Project:</legend>

        <div class="field">
            <label>Company:
                <select id="company" name="company"><?cs
                each:co = admin.project.companies ?><option value="<?cs var:co.name ?>"><?cs var:co.label ?></option><?cs
                /each ?></select>
            </label>
        </div>
        
        
    <div class="field">
        <label>Short name:<br />
        <input type="text" id="short_name" class="short" name="short_name" title="Used for folder name. Don't use spaces or special symbols" />
        <em>Format: Used for folder name. Don't use spaces or special symbols</em>
        </label>
    </div>        

    <div class="field">
        <label>Full name:<br /> <input type="text" class="long" name="full_name" /></label>
    </div>
        
    <div class="field">
        <input type="checkbox" name="maketrac" value="1" checked="checked" id="maketrac"/><label for="maketrac">Create <strong>Trac</strong> project</label>
    </div>

    <div class="field">
        <input type="checkbox" name="makesvn" value="1" checked="checked" id="makesvn"/><label for="makesvn">Create <strong>Subversion</strong> folder</label>
    </div>

        
    </fieldset>

        <div class="buttons">
    <input type="submit" name="make" value="Create project(s)">
    </div>        
        
<?cs else ?>
    <h2>Results</h2>

    <?cs if svn_created ?>
    <h3>Subversion repository creation:</h3>
    <?cs if svn_error ?>
        <p class="error">Error creating SVN repository</p>
    <?cs else ?>
        <p class="ok">OK</p>
    <?cs /if ?>
    <fieldset>
        <legend>svnadmin output:</legend>
        <pre class="output"><?cs var: svn_output?></pre>
        <pre class="error"><?cs var: svn_errors?></pre>
    </fieldset>
    <?cs /if ?>

    <?cs if trac_created ?>
    <h3>Trac environment creation:</h3>
    <?cs if trac_error ?>
        <p class="error">Error creating Trac environment</p>
    <?cs else ?>
        <p class="ok">OK</p>
    <?cs /if ?>
    
    <fieldset>
        <legend>trac-admin output:</legend>
        <pre class="output"><?cs var: trac_output?></pre>
        <pre class="error"><?cs var: trac_errors?></pre>
    </fieldset>
    <?cs /if ?>

    <div class="buttons">
    <input type="submit" name="back" value="Back">
    </div>            
<?cs /if ?>
</form>