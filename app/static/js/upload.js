$(document).ready(function() {
    $('#uploadForm').submit(function(e) {
        e.preventDefault();
        
        var formData = new FormData();
        formData.append('file', $('#file')[0].files[0]);
        
        $.ajax({
            url: '/upload',
            type: 'POST',
            data: formData,
            processData: false,
            contentType: false,
            success: function(response) {
                $('#response').text(response);
                $("#get_result_class").css('display', 'block');
                $("#get_result").css('display', 'block');
            },
            error: function(xhr, status, error) {
                console.error(error);
            }
        });
    });


    $("#get_result_class").click(function(e){
        $("#error_text").css('display', 'none');
        var question = $("#questions").val();
        if(question.length != 0){
            $.ajax({
                url: '/get_file',
                contentType: 'application/json', // Set content type explicitly
                dataType: 'json', // Specify data type expected from the server
                type: 'POST',
                data: JSON.stringify({ 'question': question }),
                success: function(response) {
                   
                },
                error: function(xhr, status, error) {
                    console.error(error);
                }
            });
        }else{
            $("#error_text").css('display', 'block');
        }
     
    });
});
