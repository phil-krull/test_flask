$(document).ready(function(){
    $(document).on('click', '.update_like', function(e){
        e.preventDefault()
        $.ajax({
            url: $(this).attr('href'),
        })
        .done(function(res){
            $('#thoughts').html(res);
        })
    })
    $(document).on('click', '.delete_thought', function(e){
        e.preventDefault()
        $.ajax({
            url: $(this).attr('href'),
        })
        .done(function(res){
            $('#thoughts').html(res);
        })
    })
    $('#email').keyup(function(){
        $.ajax({
            url: '/email_check',
            method: 'post',
            data: $('#register').serialize()
        })
        .done(function(result){
            $('#email_check').html(result);
        })
    })
    $('#create_thoughts').submit(function(){
        $.ajax({
            url: '/thoughts',
            method: 'post',
            data: $('#create_thoughts').serialize()
        })
        .done(function(res){
            if(res.status == true) {
                $('#create_thoughts')[0].reset();
                $('#thought_errors').html();
                $('#thoughts').html(res.data);
            } else {
                $('#thought_errors').html(res.data);
            }
        })
        return false;
    })
})