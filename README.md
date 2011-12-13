This package provides some useful tools to writing Node-powered JavaScript apps with Sublime.

== What does it do?

    * Automatically lints both JS and CoffeeScript files when you save.
    * Invokes Jasmine-based unit tests when you have the test open and hit 
      Ctrl-Opt-J

== Installation

    1. Make sure you have node and npm installed
    2. Clone this repostiory into `~/Library/Application Support/Sublime Text 2/Packages/SublimeNodeTools`
    3. cd into the directory and type `npm install` to setup the packages
    4. Restart Sublime (if needed)

Everything should work automatically.  You can find a menu for most commands under Tools/Node

== Todo

    * Automatically detect when npm packages are not yet setup for 
        package and run `npm install` so the plugin Just Works.
    * Work with more testing frameworks than just Jasmine.
    * Make configuring jshint work directly through configuration file
    
