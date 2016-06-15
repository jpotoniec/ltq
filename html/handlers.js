function call(path, data, cb) {
    $.post('http://localhost:23456/' + path, JSON.stringify(data), cb);
}

function display_examples_helper(data, target) {
    var ul = $('<ul>');
    for (var i = 0; i < data.length; ++i) {
        var a = $('<a>').text(data[i]);
        a.attr('href', data[i]);
        var rm = $('<a>').append($('<span>').addClass('glyphicon glyphicon-remove'));
        rm.click({'example': data[i]}, remove_example);
        ul.append($('<li>').append(a).append(rm));
    }
    target.empty();
    target.append(ul);
}

function display_examples(data) {
    display_examples_helper(data['positive'], $('#positive'));
    display_examples_helper(data['negative'], $('#negative'));
}

function add_positive() {
    var data = {'example': $('#example').val()};
    call('add/positive', data, display_examples);
    $('#example').val('');
}

function add_negative() {
    var data = {'example': $('#example').val()};
    call('add/negative', data, display_examples);
    $('#example').val('');
}

function remove_example(event) {
    call('remove', {'example': event['data']['example']}, display_examples);
}