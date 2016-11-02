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
  Fulfil.urls.setBillingAddress = "{{ url_for('checkout.billing_address') }}";
  Fulfil.urls.applyPromoCode = "{{ url_for('cart.apply_promo_code') }}";

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
            '<option value="'+ country.code +'">' + country.name + '</option>';
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

   /*
   * Set billing address
   */
   Fulfil.cart.setBillingAddress = function(address) {
    return $.ajax({
      url: Fulfil.urls.setBillingAddress,
      method: "POST",
      data: {
        "billing_address": address.billing_address,
        "name": address.name,
        "street": address.street,
        "streetbis": address.streetbis,
        "city": address.city,
        "zip": address.zip,
        "country": address.country,
        "subdivision": address.subdivision,
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

  /**
   * Helper method to validate an address
   */
  Fulfil.address.validateAddress = function (addressId) {
    var formData = {
      'address_id': addressId,
      'csrf_token': Fulfil.csrfToken,
    };
    return $.post('{{ url_for("validate_address") }}', formData)
      .success(function (result) {
        var res = {};
        switch(result.validation_result.dpv_match_code) {
          case 'Y':
            // Confirmed; entire address was DPV confirmed deliverable.
            res.state = 'valid';
            res.message = 'Address good for delivery.';
            break;
          case 'N':
            // Not Confirmed; address could not be DPV confirmed as deliverable.
            res.state = 'invalid';
            res.message = 'Invalid address';
            break;
          case 'S':
          case 'D':
            // S - Confirmed By Dropping Secondary; address was DPV confirmed by
            // dropping secondary info (apartment, suite, etc.).
            // D — Confirmed - Missing Secondary Info; the address was DPV
            // confirmed, but it is missing secondary information
            // (apartment, suite, etc.).
            res.state = 'invalid';
            res.message = 'Appartment/Suite information is missing or invalid';
            break;
          default:
            // The address was not submitted for DPV. This is usually because
            // the address does not have a ZIP Code and a +4 add-on code, or
            // the address has already been determined to be Not Deliverable
            // (only returned as part of the XML response).
            res.state = 'invalid';
            res.message = 'Invalid Address';
            break;
        }
        result.processed_validation_status = res;
      });
  };

  /**
   * Helper method to init form with countries
   */
  Fulfil.address._initForm = function (formElm, noGoogleInit) {
    var countryField = formElm.find('select[name="country"]');
    var subdivisionField = formElm.find('select[name="subdivision"]');

    // On change of country
    countryField.change(function () {
      // Clear options as soon as country change
      subdivisionField.empty();

      var reqUrl = "/countries/" + $(this).val() +"/subdivisions";
      $.getJSON(reqUrl, function(data){
        $.each(data.result, function(_, subdivision) {
          subdivisionField
            .append($("<option></option>")
              .attr("value", subdivision.code)
              .attr("code", subdivision.code)
              .text(subdivision.name));
        });
        if (subdivisionField.data('value')) {
          // If data-value set that as field value and clear.
          // This is helpful in setting value of subdivision without waiting
          // for subdivison options to load.
          subdivisionField.val(subdivisionField.data('value'));
          subdivisionField.data('value', null);
        }
        subdivisionField.triggerHandler("change");
      });
    });

    // Countries are loaded by jinja template, just trigger onChange to load
    // subdivisions
    countryField.change();

    if (!noGoogleInit) {
      Fulfil.address.googlePlaceInitForm(formElm);
    }
  };

  Fulfil.address.initForm = function (selector, noGoogleInit) {
    $(selector).each(function () {
      Fulfil.address._initForm($(this));
    });
  };

  Fulfil.address.updateAddress = function (addressId, addressFormData) {
    var action_url = "/my/addresses/" + addressId + "/edit";
    return $.post(action_url, addressFormData);
  };

  /**
   * Helper method to convert google place to address object
   */
  Fulfil.address.googlePlaceToAddress = function (place) {
    var parsedPlaceObj = {};
    // place to object
    $.each(place.address_components, function (i, elm) {
      $.each(elm.types, function (i, type) {
        parsedPlaceObj[type] = {
          long_name: elm.long_name,
          short_name: elm.short_name,
        };
      });
    });

    var addressData = {};
    addressData.street = [
      parsedPlaceObj.street_number.long_name,
      parsedPlaceObj.route.long_name,
    ].join(', ');
    addressData.city = parsedPlaceObj.locality.long_name;
    addressData.subdivision =
      parsedPlaceObj.administrative_area_level_1.short_name;
    addressData.country = parsedPlaceObj.country.short_name;
    addressData.zip = parsedPlaceObj.postal_code.long_name;

    return addressData;
  };

  Fulfil.address.googlePlaceInitForm = function (formElm) {
    var inputElm = formElm.find('input[name="street"]');
    var autocomplete = new google.maps.places.Autocomplete(inputElm[0], {
      types: ['geocode']
    });
    autocomplete.addListener('place_changed', function () {
      var addressData =
        Fulfil.address.googlePlaceToAddress(autocomplete.getPlace());
      $.each(addressData, function (fname, value) {
        if (fname == 'subdivision') {
          formElm.find('[name="' + fname + '"]').val(value)
            .data('value', value);
        }
        else {
          formElm.find('[name="' + fname + '"]').val(value).change();
        }
      });
    });
  };

  /*
   * Apply promo code to cart
   */
   Fulfil.cart.applyPromoCode = function(promoCode) {
    return $.ajax({
      url: Fulfil.urls.applyPromoCode,
      method: "POST",
      data: {
        "promo_code": promoCode,
        "csrf_token": Fulfil.csrfToken
       },
       dataType: "json"
    });
   };

  /*
   *
   * User related logic
   * ==================
   *
   */

  window.Fulfil = Fulfil;
});
