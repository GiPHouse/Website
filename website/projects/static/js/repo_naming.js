$(function(){
    const project = $('#id_name');
    const repository = $('#id_repository_set-0-name');
    const semester = $('#id_semester');
    let overwritten = true;
    const initial_name = project.val();

    function repo_slug(input, semester) {
        let name = slugify(input, {replacement: '-', remove: true, lower: false, strict: true});
        let year = semester.find(":selected").text().replace(/\D/g, '');
        return name + '-' + year
    }

    function onChange() {
        if (!Boolean(initial_name) && overwritten) {
            repository.val(repo_slug(project.val(),semester));
        }
    }

    function overwrite() {
        overwritten = false
    }

    project
        .change(onChange)
        .keyup(onChange);
    semester
        .change(onChange);
    repository
        .change(overwrite);
});
