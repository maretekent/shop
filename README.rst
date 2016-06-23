===============================
Fulfil Shop
===============================

A webshop powered by Flask and Fulfil.IO


Quickstart
----------

First, set your app's secret key as an environment variable. For example, 
example add the following to ``.bashrc`` or ``.bash_profile``.

.. code-block:: bash

    export SHOP_SECRET='something-really-secret'
    export FULFIL_SUBDOMAIN='the-subdomain'
    export FULFIL_API_KEY='your-api-key'


Then run the following commands to bootstrap your environment.


::

    git clone https://github.com/fulfilio/shop
    cd shop
    pip install -r requirements/dev.txt
    bower install
    python manage.py server

You will see a pretty welcome screen.


Deployment
----------

In your production environment, make sure the ``SHOP_ENV`` environment
variable is set to ``"prod"``.


Shell
-----

To open the interactive shell, run ::

    python manage.py shell

By default, you will have access to ``app`` and the ``User`` model.


Running Tests
-------------

To run all tests, run ::

    python manage.py test
