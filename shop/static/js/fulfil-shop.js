$(function () {
  var Fulfil = {};

  // Helper methods for form
  Fulfil.form = {};

  /**
   * Helper method to change formSubmission to ajax
   */
  Fulfil.form.ajaxSubmit = function (
    formElement, successCallback, errorCallback, alwaysCallback
  ) {
    var form = $(formElement);

    form.on('submit', function (event) {
      event.preventDefault();

      $.ajax({
        'url': form.attr("action"),
        'type': form.attr('method') || 'GET',
        'data': form.serialize(),
        'dataType': "json"
      })
        .done(successCallback)
        .fail(errorCallback)
        .always(alwaysCallback);
    });
  };

  /**
   * Method to show errors in form
   */
  Fulfil.form.showErrors = function (formElement, errorsObj) {
    var form = $(formElement);

    $(errorsObj, function (key, value) {
      // TODO: show errors
    });
  };

  /**
   * Helper method to initialize login form
   */
  Fulfil.form.initLoginForm =  function (formElement) {
    Fulfil.form.ajaxSubmit(
      formElement,
      function (result) {
        location.reload();
      },
      function (error) {
        if (error.status == 400) {
          if (!error.responseJSON.errors) {
            console.error("No 'errors' in response on bad request.");
          }
          // bad request
          Fulfil.form.showErrors(formElement, error.responseJSON.errors);
        }
        console.log(error.statusText);
      }
    );
  };

  window.Fulfil = Fulfil;
});
