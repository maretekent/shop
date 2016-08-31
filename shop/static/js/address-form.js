$(document).ready(function(){
    // Register on change event
    $("select#country").change(function(){
      // Clear options as soon as country change
      $('select#subdivision').empty();
      $.getJSON("/countries/" + $("select#country").val() +"/subdivisions", function(data){
        $.each(data.result, function(_, subdivision) {
             $('select#subdivision')
                .append($("<option></option>")
                    .attr("value", subdivision.id)
                    .attr("code", subdivision.code)
                    .text(subdivision.name));
        });
        $("select#subdivision option[value='{{ form.subdivision.data }}']").attr('selected', true);
      });
    });
    // Onload trigger the change as country comes packed with form
    $("select#country").triggerHandler("change")
    $("form.client-validation").validate({
      errorElement: "span",
      //wrapper: "li",
      errorPlacement: function(error, element) {
        error.addClass('help-block');
        error.insertAfter(element);
      },
      highlight: function(element, errorClass) {
        $(element).parents("div.form-group").addClass("has-error");
      },
      unhighlight: function(element, errorClass) {
        $(element).parents("div.form-group").removeClass("has-error");
      },
      submitHandler: function(form) {
        $("form#editAddressForm button").button('loading');
        form.submit();
      }
    });
});
