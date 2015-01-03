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

    #Activate your virtualenv
    workon talkbackbot

    # Copy settings.ini.EXAMPLE to settings.ini and edit to suit yourself
    cp settings.ini.EXAMPLE settings.ini
    vim settings.ini
    
    # Run the bot
    twistd -n sauron
    
    # OR if you have 'make' installed
    make run
    
    # Optionally, you can set the config file
    twistd -n sauron -c some-other-file.ini
    
    # Stop the bot
    <Ctrl-C>
    
    # Run unit tests
    trial tests
    
    # OR if you have 'make' installed
    make cov

