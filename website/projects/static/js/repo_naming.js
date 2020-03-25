$(function(){
    var project = $('#id_name');
    var repository = $('#id_repository_set-0-name');
    var semester = $('#id_semester');
    var overwritten = true;
    var initial_name = project.val();
    function slugify(input, semester) {
        let name = input.replace(/ /g,'-')
        let year = semester.find(":selected").text().replace(/\D/g, '');
        return name + '-' + year
    }
    function onChange() {
        if (!Boolean(initial_name) && overwritten) {
            repository.val(slugify(project.val(),semester));
        }
    }
    function overwrite() {
        overwritten = false
    }
    project
        .change(onChange)
        .keyup(onChange);
    semester
        .change(onChange)
    repository
        .change(overwrite)
})
