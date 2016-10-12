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
   *
   * @param formElement HTMLElement
   * @param options Object with successCallback, errorCallback,
   *                alwaysCallback, onSubmit as keys
   */
  Fulfil.form.ajaxSubmit = function (formElement, options) {
    var form = $(formElement);

    options = options || {}


    form.on('submit', function (event) {
      event.preventDefault();

      // Call onSubmit if function
      $.isFunction(options.onSubmit) && options.onSubmit();

      $.ajax({
        'url': form.attr("action"),
        'type': form.attr('method') || 'GET',
        'data': form.serialize(),
        'dataType': "json"
      })
        .done(options.successCallback)
        .fail(options.errorCallback)
        .always(options.alwaysCallback);
    });
  };

  /**
   * Method to show errors in form
   */
  Fulfil.form.showErrors = function (formElement, errorsObj) {
    var form = $(formElement);

    $.each(errorsObj, function (key, value) {
      // TODO: show errors
    });
  };

  /**
   * Helper method to initialize login form
   */
  Fulfil.form.initLoginForm =  function (formElement) {
    var errorContainer = formElement.find('.error-message');

    // by default hide error container
    errorContainer.html('').hide();

    var options = {
      onSubmit: function () {
        errorContainer.html('').hide();
      },
      successCallback: function (result) {
        location.reload();
      },
      errorCallback: function (error) {
        if (error.status == 400) {
          if (!error.responseJSON.errors) {
            console.error("No 'errors' in response on bad request.");
          }

          var errors = [];
          $.each(error.responseJSON.errors, function (key, value) {
            errors = errors.concat(value);
          });

          // Show errors in error container
          errorContainer.html(errors.join(',')).show();
          return;
        }
        console.log(error.statusText);
      }
    };

    Fulfil.form.ajaxSubmit(formElement, options);
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
