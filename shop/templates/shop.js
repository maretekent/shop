$(function () {
  var Fulfil = {
    csrfToken: "{{ csrf_token() }}",
    urls: {}
  };

  // All the URLs this file needs to know
  Fulfil.urls.view_cart = "{{ url_for('cart.view_cart') }}";
  Fulfil.urls.remove_from_cart = "{{ url_for('cart.remove_from_cart') }}";

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

  /*
   *
   * Cart related logic
   */
   Fulfil.cart = {}

   /*
    * Refreshes the cart and updates Fulfil.cart.current_cart
    * Also returns the request promise.
    *
    */
   Fulfil.cart.refresh = function() {
    console.debug("Refreshing Cart");
    return $.ajax({
      cache: false,
      url: Fulfil.urls.view_cart,
      dataType: "json",
      success: function(data){
        Fulfil.cart.current_cart = data.cart;
      }
    })
   };

   /*
    * Delete a item from the cart.
    *
    */
   Fulfil.cart.deleteItem = function(lineId) {
    console.debug("Removing Line from Cart");
    return $.ajax({
      url: Fulfil.urls.remove_from_cart,
      method: "POST",
      data: {
        "line_id": lineId,
        "csrf_token": Fulfil.csrfToken
       },
       dataType: "json",
       success: function() {
         Fulfil.cart.refresh();
       }
    });
   }

  window.Fulfil = Fulfil;
});
