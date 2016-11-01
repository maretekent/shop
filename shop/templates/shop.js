$(function () {
  var Fulfil = {
    csrfToken: "{{ csrf_token() }}",
    urls: {},
    form: {},
    cart: {"stripe": {}},
    user: {},
    ux: {},
    product: {},
    address: {}
  };

  // All the URLs this file needs to know
  Fulfil.urls.view_cart = "{{ url_for('cart.view_cart') }}";
  Fulfil.urls.remove_from_cart = "{{ url_for('cart.remove_from_cart') }}";
  Fulfil.urls.getVariations = "{{ url_for('products.get_variations') }}";
  Fulfil.urls.payUsingProfile = "{{ url_for('checkout.payment') }}";

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
      if ($.isFunction(options.onSubmit)) {
        options.onSubmit(event);
      }

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
   * ==================
   *
   */


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

  /*
   *
   * Product related logic
   * =====================
   *
   */

  /*
   *
   * Fetch variation data for a product template
   *
   */
  Fulfil.product.getVariations = function(templateId) {
    return $.ajax({
      url: Fulfil.urls.getVariations,
      method: "GET",
      data: {
        "template": templateId
       },
       dataType: "json",
       success: function(data) {
         Fulfil.product.loadVariations(data);
       }
    });
  };

  /*
   * Load the variation data locally to serve more
   * requests.
   */
  Fulfil.product.loadVariations = function(variationData) {
    Fulfil.product.variationData = variationData;
  };

  /*
   * Given a set of attributes, return a variant
   * that fits the attributes
   *
   */
  Fulfil.product.findMatchingVariant = function(attributeSelection) {
    return _.find(Fulfil.product.variationData['variants'], function(variant) {
      return _.isEqual(variant.attributes, attributeSelection)
    });
  };

  /*
   * Return the data of the variant with id
   *
   */
  Fulfil.product.getVariant = function(variantId) {
    return _.find(Fulfil.product.variationData['variants'], function(variant) {
      return (variant.id == variantId) ;
    });
  };

  /*
   *
   * Address related logic
   * =====================
   *
   */

  /*
   * Return list of all available countries
   */
  Fulfil.address.getCountries = function() {
    return $.getJSON('{{ url_for("public.get_countries") }}');
  };

  /*
   * Helper method to fill country options in select field
   */
  Fulfil.address.fillCountriesOpts = function(selectField, currentValue) {
    selectField.html('');
    return Fulfil.address.getCountries()
      .success(function (data) {
        var optionsHtml = '';
        $.each(data.result, function(i, country){
          optionsHtml +=
            '<option value="'+ country.id +'">' + country.name + '</option>';
        });
        selectField.html(optionsHtml);

        if (currentValue) {
          $(selectField).val(currentValue).change();
        }
      });
  };

  /*
   * Return a list of all addresses of the user
   */
   Fulfil.address.getAddresses = function() {
     return $.getJSON(
       '{{ url_for("user.addresses") }}',
       {csrf_token: Fulfil.csrfToken}
     );
   };

   /*
   * Create a stripe token using card data and address
   */
   Fulfil.cart.stripe.createToken = function(card, address, callback) {
     if (typeof Stripe === 'undefined') {
       console.debug("Stripe.js is not added");
       return;
     }
     Stripe.setPublishableKey("{{ current_channel.payment_gateway.stripe_publishable_key }}");
     Stripe.card.createToken({
       'number': card.number,
       'cvc': card.cvc,
       'exp_month': card.exp_month,
       'exp_year': card.exp_year,
       'name': card.name,
       'address_zip': address.zip,
       'address_line1': address.street,
       'address_line2': address.streetbis,
       'address_city': address.city,
       'address_state': address.subdivision,
       'address_country': address.country
     }, callback);
   };

   /*
   * Pay using stripe payment profile or token
   */
   Fulfil.cart.payUsingProfile = function(profile, amount) {
    return $.ajax({
      url: Fulfil.urls.payUsingProfile,
      method: "POST",
      data: {
        "payment_profile_id": profile.payment_profile_id,
        "stripe_token": profile.stripe_token,
        "amount": amount,
        "csrf_token": Fulfil.csrfToken
       },
       dataType: "json"
    });
   };

   Fulfil.ux.notify = function(message, level, title) {
      if (!level) {
        level = 'info'
      };
      if (toastr) {
        toastr[level](message, title);
      }
   }

  /*
   *
   * User related logic
   * ==================
   *
   */

  window.Fulfil = Fulfil;
});
