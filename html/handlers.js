function call(path, data, cb) {
    $.post('api/' + path, JSON.stringify(data), cb);
}

function get(path, cb) {
    $.get('api/' + path, cb);
}

function display_examples_helper(data, target, cb) {
    var ul = $('<ul>');
    for (var i = 0; i < data.length; ++i) {
        var a = $('<a>').text(data[i]);
        a.attr('href', data[i]);
        var rm = $('<a>').append($('<span>').addClass('glyphicon glyphicon-remove'));
        rm.click({'example': data[i]}, cb);
        ul.prepend($('<li>').append(a).append(rm));
    }
    target.empty();
    target.append(ul);
}

function display_state(data) {
    console.log(data);
    if ('positive' in data)
        display_examples_helper(data['positive'], $('#positive'), remove_example);
    if ('negative' in data)
        display_examples_helper(data['negative'], $('#negative'), remove_example);
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

function load_example(positive, negative) {
    for (var i = 0; i < positive.length; ++i) {
        call('add/positive', {'example': positive[i]}, display_state);
    }
    for (var i = 0; i < negative.length; ++i) {
        call('add/negative', {'example': negative[i]}, display_state);
    }
}

function load_eu() {
    var positive = ['http://dbpedia.org/resource/Warsaw',
        'http://dbpedia.org/resource/Berlin',
        'http://dbpedia.org/resource/Zagreb',
        'http://dbpedia.org/resource/Nicosia',
        'http://dbpedia.org/resource/Vilnius'
    ];
    var negative = ['http://dbpedia.org/resource/Oslo'];
    load_example(positive, negative)
}

function load_pl() {
    var positive = ['http://dbpedia.org/resource/Gdańsk',
        'http://dbpedia.org/resource/Kraków',
        'http://dbpedia.org/resource/Lublin',
        'http://dbpedia.org/resource/Poznań',
        'http://dbpedia.org/resource/Toruń',
        'http://dbpedia.org/resource/Bydgoszcz'
    ];
    var negative = [
        'http://dbpedia.org/resource/Lesser_Poland_Voivodeship',
        'http://dbpedia.org/resource/Silesian_Voivodeship',
        'http://dbpedia.org/resource/Masuria'
    ];
    load_example(positive, negative)
}

function set_label(data) {
    data = data['data'];
    data.target[data.n] = data.label;
    console.log(data);
    data.tr.removeClass('warning');
    data.tr.toggleClass('success', data.label);
    data.tr.toggleClass('danger', !data.label);
    var enable = true;
    for (var i = 0; i < data.target.length; ++i) {
        if (data.target[i] === undefined) {
            enable = false;
            break;
        }
    }
    if (enable)
        $('#submit_labels').removeAttr('disabled');
}

function submit_labels(data) {
    $('#new_examples_panel').hide();
    $('#new_examples').empty();
    data = data['data'];
    //console.log(data.labels);
    call('labels', {'labels': data.labels}, display_state);
    do_step();
}

function display_new_examples(data) {
    console.log(data);
    $('#new_examples_panel').show();
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
        var a = $('<a>').attr('href', new_examples[n].uri).text(new_examples[n].uri);
        console.log(new_examples[n]);
        if ('comment' in new_examples[n])
            a.attr('title', new_examples[n]['comment']);
        tr.append($('<td>').append(a));
        target.append(tr);
    }
    var btn = $('#submit_labels');
    btn.attr('disabled', '');
    btn.off('click');
    btn.click({'labels': labels}, submit_labels);

}

function step_callback(data) {
    console.log(data);
    var btn = $('#submit_labels');
    btn.attr('disabled', '');
    btn.off('click');
    if ('new_positive' in data)
        display_new_examples(data);
    if ('hypothesis' in data) {
        $('#hypothesis').text(data['hypothesis']);
        console.log(data['hypothesis']);
    }
    if ('results' in data) {
        $('#results_panel').show();
        display_examples_helper(data['results'], $('#results'), function (event) {
            call('add/negative', event['data'], display_state);
        });
    }
}

function do_step() {
    $('#new_examples_panel').hide();
    $('#results_panel').hide();
    get('step', step_callback);
}

function restart() {
    get('restart', init);
}

function init() {
    refresh_state();
    $('#new_examples_panel').hide();
    $('#results_panel').hide();
    $('#hypothesis').text('');
}

$(document).ready(init);