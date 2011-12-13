import os
import re
import sublime
import sublime_plugin
from statusprocess import *
from asyncprocess  import *
from output_panel  import *

PROMPT           = "jasmine-node:\n"
SUPPORTED_EXTENSIONS = ('js', 'coffee')
SUPPORTED_SELECTORS = map(lambda x: 'source.'+x, SUPPORTED_EXTENSIONS)

###############################################
# Support Functions
#

# returns True if the current view appears to reference a test file.  For now
# we recognize a test file as one ending with "spec.js" or "spec.coffee"
def is_testable(view):
  pattern = "spec\.("+str.join('|', SUPPORTED_EXTENSIONS)+")$"
  return not view.is_scratch() and re.search(pattern, view.file_name()) != None

def autotest_enabled(view):
  return is_testable(view) and (view.settings().get("auto_test", True))

###############################################
# Commands
#

class RunJsTestCommand(sublime_plugin.WindowCommand):

  def is_enabled(self): 
    return is_testable(self.window.active_view())

  def run(self):
    s = sublime.load_settings(SETTINGS_FILE)
    view      = self.window.active_view()
    file_path = view.file_name()
    file_name = os.path.basename(file_path)
    dir_name  = os.path.dirname(file_path)
    
    self.output_view = init_output_panel(self.window, PROMPT, file_path)
    show_output_panel(self.window)

    self.debug = s.get('debug', False)
    self.is_running = True

    pattern = re.sub('spec.+$', '', file_name)
    jasmine_bin = (sublime.packages_path() + '/' + PACKAGE_NAME + '/node_modules' +
        '/jasmine-node/bin/jasmine-node')

    cmd = ('source ~/.profile; cd "'+dir_name+ '"; "' + jasmine_bin + 
        '" --coffee --noColor . -m "' + pattern + '"')
 
    if self.debug:
      print "DEBUG: " + str(cmd)

    AsyncProcess(cmd, self) 
    StatusProcess('Running unit tests for file ' + file_name, self)

    #JsLintEventListener.disabled = True
  
  def append_data(self, proc, data, end=False):
    append_output_panel(self.output_view, data)

  def update_status(self, msg, progress):
    sublime.status_message(msg + " " + progress)

  def proc_terminated(self, proc):
    append_output_panel(self.output_view, '', True)



class TestEventListener(sublime_plugin.EventListener):
  """jslint event"""
  disabled = False
  def __init__(self):
    self.previous_resion = None
    self.file_view = None

  def on_post_save(self, view):
    if is_testable(view):
      if autotest_enabled(view):
        print "AUTOTESTING " + view.file_name() 
        #view.window().run_command("run_js_test")  
      else:
        sublime.status_message('Autotest disabled for this file')

