document.addEventListener("DOMContentLoaded", () => {
    const name = document.getElementById("id_name");
    const semester = document.getElementById("id_semester");
    const slug = document.getElementById("id_slug");
    const default_repo = document.getElementById("id_default_repo");
    const default_repo_div = document.querySelector(".field-default_repo")
    const save = document.querySelector('[name="_save"]');
    const end_body = document.getElementById("django-admin-form-add-constants")
    const path = window.location.pathname;
    const style = document.createElement("style");

    //Removes the increment/decrement buttons from the repo id
    style.textContent = `
    input[type=number]::-webkit-inner-spin-button,
    input[type=number]::-webkit-outer-spin-button {
        -webkit-appearance: none;
        margin: 0;
    }
    `;

    document.head.appendChild(style);

    if (path.endsWith("/change/")) {
        // Hides the default repo button when accessing an existing project
        // default repo button only appears on creation of a project
        default_repo_div.style.display = "none"
    }

    // Disable changes to the slug
    slug.disabled = true;

    function slugify(text) {
        // This function should behave the same as the django slugify method
        // This function is used to show live showcase of the slug before project creation
        return text
            .toLowerCase()
            .replace(/[^\w\s-]/g, "")
            .replace(/[-\s]+/g, "-")
            .replace(/^[-_]+|[-_]+$/g, "");
    }

    function updateSlug() {
        // This function generates a slug based on the name and semester year of a project
        const nameValue = name.value || "";
        var semesterText =
            semester.options[semester.selectedIndex]?.text.slice(-4) || "";

        if (semesterText == "----"){
            semesterText = "";
        }

        slug.value = slugify(`${nameValue}-${semesterText}`);
    }

    // When the name or semester of a project is being changed, the update function is called
    name.addEventListener("input", update);
    semester.addEventListener("input", update);

    // Initial updating of the slug
    updateSlug();

    function invalidRepoNames(){
        // This function returns a list of repo names that are invalid
        const invalid = [];
        const names = []; //This stores a list of names already appeared before

        const existing_repo_names = existingrepositoryFieldset.querySelectorAll(
            '[id^="id_existingrepository_set-"][id$="-name"]'
        ); //Selects all existing repo names

        const repo_names = document.querySelectorAll(
            '[id^="id_newrepository_set-"][id$="-name"]'
        ); //Selects all new repo names
        
        if(default_repo.checked && slug.value != ""){
            for(const repo_name of repo_names){
                if(repo_name.value == slug.value){
                    invalid.push(repo_name);
                }
            }
        } //If default repo is checked a repo will be created with the slug name.
        //So this loop checks whether the user tried to make a repo with the same name as the slug, this would result in an error otherwise.
        
        for(const repo_name of existing_repo_names){
            if(!names.includes(repo_name.value)){
                names.push(repo_name.value);
            }
            else{
                if(!invalid.includes(repo_name) && repo_name.value != ""){
                    invalid.push(repo_name);
                }
            }
        } //Adds all existing repo names to the list of seen names, a duplicate name will be pushed to the invalid list

        for(const repo_name of repo_names){
            if(!names.includes(repo_name.value)){
                names.push(repo_name.value);
            }
            else{
                if(!invalid.includes(repo_name) && repo_name.value != ""){
                    invalid.push(repo_name);
                }
            }
        } //Adds all new repo names to the list of seen names, a duplicate name will be pushed to the invalid list
        return invalid;
    }

    function repoErrorUpdate(){
        //This function handles any invalid repo names errors
        const invalid_repo_names = invalidRepoNames(); //First checks for invalid repo names

        //If there are invalid repo names it handles it, otherwise clears any error messages and enables the save button
        if(invalid_repo_names.length > 0){
            save.disabled = true;
            clear(); //Clears the error messages before creating them again to prevent duplicates

            if(!document.getElementById("default_repo_copy")){ //Creates an error message below the save button
                const error = createErrorMessage("Naming a repo the same as the slug is not allowed when default repo is enabled.");
                error.id = "default_repo_copy";
                end_body.before(error);
            }

            for(const repo_name of invalid_repo_names){ //Creates error messages at each invalid repo name
                repo_name.style.border = "1px solid #e35f5f";
                const parent = repo_name.closest(".form-row.field-name");
                const error = createErrorMessage("Repo name already taken");
                error.classList.add("repo-error");
                parent.before(error);
            }
        }
        else{
            clear();
            save.disabled = false;
            document.querySelector("#default_repo_copy")?.remove(); //Removes error message below save button
        }
    }

    function createErrorMessage(message){
        //Template for creating an error message
        const error = document.createElement("ul");
        error.className = "errorlist";
        const li = document.createElement("li");
        li.textContent = message;
        error.appendChild(li);

        return error;
    }

    function clear(){
        //Clears all the error messages for repo names
        const repo_names = document.querySelectorAll('[id^="id_newrepository_set-"][id$="-name"]');
        const existing_repo_names = document.querySelectorAll('[id^="id_existingrepository_set-"][id$="-name"]');

        for(const repo_name of repo_names){
            repo_name.style.border = "";
        }

        for(const repo_name of existing_repo_names){
            repo_name.style.border = "";
        }

        const error_messages = document.querySelectorAll(".repo-error");

        for(const error_message of error_messages){
            error_message.remove();
        }
    }

    function update(){
        //Updates the slug and also checks for any potential errors
        updateSlug();
        repoErrorUpdate();
    }

    const newrepositoryFieldset = document.querySelector(
        "#newrepository_set-group"
    ); //Selects everything inside the new_repository HTML

    if (newrepositoryFieldset) {
        newrepositoryFieldset.addEventListener("input", repoErrorUpdate);
    } //If anything is inputted in new_repository, repoErrorUpdate is called, checking for any errors
    default_repo.addEventListener("change", repoErrorUpdate); //Checking and unchecking the default repo button checks for any errors

    const existingrepositoryFieldset = document.querySelector(
        "#existingrepository_set-group"
    ); //Selects everything inside the existing_repository HTML

    document.addEventListener("click", addLinkListener); //The first click on the website runs addLinkListener
    function addLinkListener(){
        //Because the addlink is loaded after the website is already loaded, a listener can't be attached
        //immediately, as a workaround, we attach a listener as soon as the user clicks anything.
        //For both addlinks(new and existing repo), we make a listener for both addlinks and remove the global listener that calls this.
        const addlink1 = newrepositoryFieldset.querySelector(".addlink");
        const addlink2 = existingrepositoryFieldset.querySelector(".addlink");
        if(addlink1){
            addlink1.addEventListener("click", createRemoveListeners);
            document.removeEventListener("click", addLinkListener);
            fetchTimeout();
        }
        if(addlink2){
            addlink2.addEventListener("click", fetchTimeout);
            document.removeEventListener("click", addLinkListener);
            fetchTimeout();
        }
    }
    function createRemoveListeners(){
        //This function creates "remove" listeners. The delete buttons at the new repository field will check for any errors when clicked
        const remove_buttons = newrepositoryFieldset.querySelectorAll(".inline-deletelink");

        for(const remove_button of remove_buttons){
            remove_button.removeEventListener("click", repoErrorUpdate);
            remove_button.addEventListener("click", repoErrorUpdate);
        }
    }

    function fetchTimeout(){
        // This function does a couple of things, 
        // - it does the same as createRemoveListeners for new repos
        // - when an user stops typing the repo id it tries to fetch it from github
        // - checks for invalid repo names when the repo names are changed
        // - disables fields (everything except repo id when nothing is fetched and only disables the repo id when it is fetched)
        const repo_names = existingrepositoryFieldset.querySelectorAll(
            '[id^="id_existingrepository_set-"][id$="-name"]'
        );

        const repo_ids = existingrepositoryFieldset.querySelectorAll(
            '[id^="id_existingrepository_set-"][id$="-github_repo_id"]'
        );

        const remove_buttons = existingrepositoryFieldset.querySelectorAll(".inline-deletelink");

        for(const repo_name of repo_names){
            repo_name.removeEventListener("click", repoErrorUpdate);
            repo_name.addEventListener("click", repoErrorUpdate);
        }

        for(const repo_id of repo_ids){
            let timeout = null;
            repo_id.removeEventListener("keyup", keyUp);
            repo_id.addEventListener("keyup", keyUp);
        }

        for(const remove_button of remove_buttons){
            remove_button.removeEventListener("click", repoErrorUpdate)
            remove_button.addEventListener("click", repoErrorUpdate)
        }

        disableFields();
    }

    function disableFields(){
        //disables fields (everything except repo id when nothing is fetched yet and only disables the repo id when it is fetched)
        const nameFields = existingrepositoryFieldset.querySelectorAll("input[name$='name']");

        for(const name of nameFields){
            const row = name.closest(".inline-related");
            const private = row.querySelector("input[name$='private']");
            const archived = row.querySelector("select[name$='is_archived']");
            const repo_id = row.querySelector('input[name$="github_repo_id"]');

            if(!repo_id.disabled){
                name.disabled = true;
                private.disabled = true;
                archived.disabled = true;
            }
        }
    }

    const keyUp = (e) => {
        //Listener that listens for when u stop typing
        clearTimeout(e.target._timeout);

        e.target._timeout = setTimeout(() => {
            fetchData(e);
        }, 500);
    };

    async function fetchData(e){
        //Fetches the data from github
        const url = `/admin/projects/project/fetch-repo/?github_repo_id=${encodeURIComponent(e.target.value)}`;
        const row = e.target.closest(".inline-related");

        try {
            const res = await fetch(url);
            const data = await res.json();

            if (data.error) {
                e.target.style.border = "1px solid #e35f5f";
                document.getElementById("error" + e.target.id)?.remove();
                const parent = e.target.closest(".form-row.field-github_repo_id");
                const error = createErrorMessage(data.error);
                error.id = "error" + e.target.id;
                parent.before(error);
                return;
            }
            e.target.style.border = "";
            document.getElementById("error" + e.target.id)?.remove();
            e.target.disabled = true;

            const nameField = row.querySelector("input[name$='name']");
            nameField.disabled = false;
            const privateField = row.querySelector("input[name$='private']");
            privateField.disabled = false;
            const archivedField = row.querySelector("select[name$='is_archived']");
            archivedField.disabled = false;

            if (nameField) nameField.value = data.name;
            if (privateField) privateField.checked = data.private;
            if (archivedField) {
            archivedField.value = String(data.archived);

            archivedField.dispatchEvent(new Event("change", { bubbles: true }));
            }
            repoErrorUpdate();
        } catch (err) {
            document.getElementById("error" + e.target.id)?.remove();
            e.target.style.border = "1px solid #e35f5f";
            const parent = e.target.closest(".form-row.field-github_repo_id");
            const error = createErrorMessage("Fetch failed");
            error.id = "error" + e.target.id;
            parent.before(error);
        }
    }

    save.addEventListener('mouseenter', () => {
        //When a mouse enters the save button it enables certain fields. Because disabled fields are not submitted when saved.
        //A known problem is: when the user navigates to the save button using tab, the fields are still disabled and the save could
        //run into problems, but we assume that the average user will not do this.
        const nameFields = existingrepositoryFieldset.querySelectorAll("input[name$='name']");
        const privateFields = existingrepositoryFieldset.querySelectorAll("input[name$='private']");
        const archivedFields = existingrepositoryFieldset.querySelectorAll("select[name$='is_archived']");
        const repo_ids = existingrepositoryFieldset.querySelectorAll(
            '[id^="id_existingrepository_set-"][id$="-github_repo_id"]'
        );

        enable(nameFields);
        enable(privateFields);
        enable(archivedFields);
        enable(repo_ids);
        slug.disabled = false;
    });

    function enable(list){
        //Enables all the items in a list.
        for(item of list){
            item.disabled = false;
        }
    }

    save.addEventListener('mouseleave', () => {
        //disables all the fields again when the mouse leaves the save button
        disableFields();
        slug.disabled = true;
    });

});