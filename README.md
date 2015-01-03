sauron
======

The eye of the Sauron casts its shadow upon you... and selected IRC channels.


Setup
------------

Installation
::

    # Create a virtualenv
    mkvirtualenv sauron

    # Install requirements
    workon sauron
    pip install -r requirements.txt

Usage
-----

Typical usage flow
::

    # Activate your virtualenv
    workon sauron

    # Copy settings.py.template to settings.py and edit to point to the right server/channel etc
    cp settings.py.template settings.py
    vim settings.py

    # Start the bot
    twistd twsrs

    # Stop the bot
    kill `cat twistd.pid`

    # Run unit tests (optional)
    nosetests

