function call(path, data, cb) {
    $.post('http://localhost:23456/' + path, JSON.stringify(data), cb);
}

function get(path, cb) {
    $.get('http://localhost:23456/' + path, cb);
}

function display_examples_helper(data, target) {
    var ul = $('<ul>');
    for (var i = 0; i < data.length; ++i) {
        var a = $('<a>').text(data[i]);
        a.attr('href', data[i]);
        var rm = $('<a>').append($('<span>').addClass('glyphicon glyphicon-remove'));
        rm.click({'example': data[i]}, remove_example);
        ul.prepend($('<li>').append(a).append(rm));
    }
    target.empty();
    target.append(ul);
}

function display_state(data) {
    console.log(data);
    if ('positive' in data)
        display_examples_helper(data['positive'], $('#positive'));
    if ('negative' in data)
        display_examples_helper(data['negative'], $('#negative'));
}

function add_positive() {
    var data = {'example': $('#example').val()};
    call('add/positive', data, display_state);
    $('#example').val('');
}

function add_negative() {
    var data = {'example': $('#example').val()};
    call('add/negative', data, display_state);
    $('#example').val('');
}

function remove_example(event) {
    call('remove', {'example': event['data']['example']}, display_state);
}

function refresh_state() {
    get('state', display_state);
}

function load_eu() {
    var positive = ['http://dbpedia.org/resource/Warsaw',
        'http://dbpedia.org/resource/Berlin',
        'http://dbpedia.org/resource/Zagreb',
        'http://dbpedia.org/resource/Nicosia',
        'http://dbpedia.org/resource/Vilnius'
    ];
    var negative = ['http://dbpedia.org/resource/Oslo'];
    for (var i = 0; i < positive.length; ++i) {
        call('add/positive', {'example': positive[i]}, display_state);
    }
    for (var i = 0; i < negative.length; ++i) {
        call('add/negative', {'example': negative[i]}, display_state);
    }
}

function set_label(data) {
    data = data['data'];
    data.target[data.n] = data.label;
    console.log(data);
    data.tr.removeClass('warning');
    data.tr.toggleClass('success', data.label);
    data.tr.toggleClass('danger', !data.label);
    var enable = true;
    for (var i = 0; i < data.length; ++i)
        if (data[i] === undefined) {
            enable = false;
            break;
        }
    if (enable)
        $('#submit_labels').removeAttr('disabled');
}

function submit_labels(data) {
    $('#new_examples').empty();
    data = data['data'];
    //console.log(data.labels);
    call('labels', {'labels': data.labels}, display_state);
    do_step();
}

function display_new_examples(data) {
    console.log(data);
    var new_examples = data['new_positive'].concat(data['new_negative']);
    var target = $('#new_examples');
    target.empty();
    var labels = [];
    for (var n = 0; n < new_examples.length; ++n) {
        labels[n] = undefined;
        var tr = $('<tr>');
        var r1 = $('<input>').attr('type', 'radio').attr('name', 'label_' + n).click({
            'target': labels,
            'n': n,
            'label': true,
            'tr': tr
        }, set_label);
        var r2 = $('<input>').attr('type', 'radio').attr('name', 'label_' + n).click({
            'target': labels,
            'n': n,
            'label': false,
            'tr': tr
        }, set_label);
        tr.addClass('warning');
        tr.append($('<td>').append(r1));
        tr.append($('<td>').append(r2));
        tr.append($('<td>').text(new_examples[n].uri));
        target.append(tr);
    }
    var btn = $('#submit_labels');
    btn.attr('disabled', '');
    btn.off('click');
    btn.click({'labels': labels}, submit_labels);
    if ('hypothesis' in data) {
        $('#hypothesis').text(data['hypothesis']);
        console.log(data['hypothesis']);
    }
}

function do_step() {
    get('step', display_new_examples);
}

$(document).ready(refresh_state);