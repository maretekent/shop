# -*- coding: utf-8 -*-
"""Cart forms."""
from flask_wtf import Form
from shop.cart.models import SaleLine
from shop.globals import current_cart
from shop.product.models import Product
from wtforms.fields import FloatField, IntegerField
from wtforms.validators import DataRequired


class AddtoCartForm(Form):
    "A simple add to cart form"

    quantity = FloatField('Quantity', default=1.0, validators=[DataRequired()])
    product = IntegerField('Product', validators=[DataRequired()])

    def validate(self):
        """Validate the form."""
        initial_validation = super(AddtoCartForm, self).validate()
        if not initial_validation:
            return False

        # TODO: Other validation on product?
        product = Product.query.get(self.product.data)
        if not product:
            self.product.errors.append('Unknown product')
            return False
        return True


class RemoveFromCartForm(Form):
    "Form for removing sale line from cart"

    line_id = IntegerField('SaleLine', validators=[DataRequired()])

    def validate(self):
        initial_validation = super(RemoveFromCartForm, self).validate()
        if not initial_validation:
            return False

        sale_line = SaleLine.query.filter_by_domain(
            [
                ('sale', '=', current_cart.sale and current_cart.sale.id),
                ('id', '=', self.line_id.data)
            ]
        ).first()
        if not sale_line:
            self.line_id.errors.append('Unkown sale line')
            return False
        return True
