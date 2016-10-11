$(document).ready(function(){
    // Register on change event
    $("select#country").change(function(){
      // Clear options as soon as country change
      $("select#subdivision").empty();
      var reqUrl = "/countries/" + $("select#country").val() +"/subdivisions";
      $.getJSON(reqUrl, function(data){
        $.each(data.result, function(_, subdivision) {
          $("select#subdivision")
            .append($("<option></option>")
              .attr("value", subdivision.id)
              .attr("code", subdivision.code)
              .text(subdivision.name));
        });
        $("select#subdivision").triggerHandler("change");
      });
    });
    // Onload trigger the change as country comes packed with form
    $("select#country").triggerHandler("change");
});
