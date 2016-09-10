# -*- coding: utf-8 -*-
"""Cart forms."""
from flask_wtf import Form
from wtforms.fields import FloatField, IntegerField
from wtforms.validators import DataRequired


class AddtoCartForm(Form):
    "A simple add to cart form"

    quantity = FloatField('Quantity', default=1.0, validators=[DataRequired()])
    product = IntegerField('Product', validators=[DataRequired()])

    def validate(self):
        """Validate the form."""
        from shop.product.models import Product
        initial_validation = super(AddtoCartForm, self).validate()
        if not initial_validation:
            return False

        # TODO: Other validation on product?
        product = Product.query.get(self.product.data)
        if not product:
            self.product.errors.append('Unknown product')
            return False
        return True