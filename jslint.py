import os
import re
import sublime
import sublime_plugin
from statusprocess import *
from asyncprocess import *
from output_panel import *

PROMPT = "jshint:\n"
SUPPORTED_SELECTORS = ('source.js', 'source.json', 'source.coffee')

###############################################
# Support Functions
#

def is_supported_view(view):
  return (not view.is_scratch() and 
    any(map(lambda x: view.score_selector(0, x), SUPPORTED_SELECTORS)))

def is_autolinting(view):
  return is_supported_view and (view.settings().get("js_autolint", True))

###############################################
# Commands
#

class ToggleJsAutolintCommand(sublime_plugin.WindowCommand):
  """Toggle autolinting on supported files"""
  def is_enabled(self):
    return is_supported_view(self.window.active_view())

  def run(self):
    toggle_setting(self.window.active_view().settings(), 'js_autolint', True)

class JslintCommand(sublime_plugin.WindowCommand):

  def is_enabled(self):
    return is_supported_view(self.window.active_view())

  def run(self):
    s = sublime.load_settings(SETTINGS_FILE)

    view      = self.window.active_view()
    file_path = view.file_name()
    file_name = os.path.basename(file_path)
   
    self.debug = s.get('debug', False)
    self.buffered_data = ''
    self.file_path = file_path
    self.file_name = file_name
    self.is_running = True
    self.output_panel_showed = False
    self.ignored_error_count = 0
    self.ignore_errors = s.get('ignore_errors', [])

    self.init_output_panel()

    if len(s.get('jshint_config', '')) > 0:
      config_path = s.get('jshint_config')
    else:
      config_path = sublime.packages_path()+'/SublimeNodeTools/jshint-config.json'
 
    if len(s.get('jshint_bin', '')) > 0:
      jshint_bin = s.get('jshint_bin')
    else:
      jshint_bin = sublime.packages_path() + '/SublimeNodeTools/bin/bolt-lint'

    # TODO: lookup all CoffeeScript and JavaScript ranges, not just the first
    if view.score_selector(0, 'source.coffee'):
      coffee_flag = ' --coffee '
    else:
      coffee_flag = ''

    script = view.substr(sublime.Region(0, view.size()))
    cmd = 'source ~/.profile; "'+jshint_bin + '" --config "' + config_path +'"  --file "' + file_name + '" ' + coffee_flag + s.get('jshint_options', '')

    if self.debug:
      print "DEBUG: " + str(cmd)

    AsyncProcess(cmd, self, script)
    StatusProcess('Starting JSHint for file ' + file_name, self)

    JsLintEventListener.disabled = True

  def init_output_panel(self):
    if not hasattr(self, 'output_view'):
      self.output_view = self.window.get_output_panel(RESULT_VIEW_NAME)
      self.output_view.set_name(RESULT_VIEW_NAME)
    self.clear_test_view()
    self.output_view.settings().set("file_path", self.file_path)

  def clear_test_view(self):
    self.output_view.set_read_only(False)
    edit = self.output_view.begin_edit()
    self.output_view.erase(edit, sublime.Region(0, self.output_view.size()))
    self.output_view.insert(edit, self.output_view.size(), PROMPT)
    self.output_view.end_edit(edit)
    self.output_view.set_read_only(True)

  def append_data(self, proc, data, end=False):
    self.buffered_data = self.buffered_data + data.decode("utf-8")
    data = self.buffered_data.replace(self.file_path, self.file_name).replace('\r\n', '\n').replace('\r', '\n')

    if end == False:
      rsep_pos = data.rfind('\n')
      if rsep_pos == -1:
        # not found full line.
        return
      self.buffered_data = data[rsep_pos+1:]
      data = data[:rsep_pos+1]

    # ignore error.
    text = data
    if len(self.ignore_errors) > 0:
      text = ''
      for line in data.split('\n'):
        if len(line) == 0:
          continue
        ignored = False
        for rule in self.ignore_errors:
          if re.search(rule, line):
            ignored = True
            self.ignored_error_count += 1
            if self.debug:
              print "text match line "
              print "rule = " + rule
              print "line = " + line
              print "---------"
            break
        if ignored == False:
          text += line + '\n'


    show_output_panel(self.window)
    selection_was_at_end = (len(self.output_view.sel()) == 1 and self.output_view.sel()[0] == sublime.Region(self.output_view.size()))
    self.output_view.set_read_only(False)
    edit = self.output_view.begin_edit()
    self.output_view.insert(edit, self.output_view.size(), text)

    if end and self.ignored_error_count > 0:
      text = '\nignored ' + str(self.ignored_error_count) + ' errors.\n'
      self.output_view.insert(edit, self.output_view.size(), text)

    # if selection_was_at_end:
    #   self.output_view.show(self.output_view.size())
    self.output_view.end_edit(edit)
    self.output_view.set_read_only(True)

    # if end:
    #   self.output_view.run_command("goto_line", {"line": 1})

  def update_status(self, msg, progress):
    sublime.status_message(msg + " " + progress)

  def proc_terminated(self, proc):
    if proc.returncode == 0:
      sublime.status_message("jshint: " + self.file_name + ' has no errors')
      hide_output_panel(self.window)

    else:
      msg = ''
      self.append_data(proc, msg, True)

    JsLintEventListener.disabled = False


class JsLintEventListener(sublime_plugin.EventListener):
  """jslint event"""
  disabled = False
  def __init__(self):
    self.previous_resion = None
    self.file_view = None

  def on_post_save(self, view):
    if is_supported_view(view):
      if is_autolinting(view):
        print "AUTOLINTING " + view.file_name() 
        view.window().run_command("jslint")  
      else:
        sublime.status_message('Autolint disabled for this file')

  def on_deactivated(self, view):
    if view.name() != RESULT_VIEW_NAME:
      return
    self.previous_resion = None

    if self.file_view:
      self.file_view.erase_regions(RESULT_VIEW_NAME)

  def on_selection_modified(self, view):
    if JsLintEventListener.disabled:
      return
    if view.name() != RESULT_VIEW_NAME:
      return
    region = view.line(view.sel()[0])

    # make sure call once.
    if self.previous_resion == region:
      return
    self.previous_resion = region

    # extract line from jslint result.
    text = view.substr(region).split(':')
    if len(text) < 4 or text[0] != 'jslint' or re.match('\d+', text[2]) == None or re.match('\d+', text[3]) == None:
        return
    line = int(text[2])
    col = int(text[3])

    # hightligh view line.
    view.add_regions(RESULT_VIEW_NAME, [region], "comment")

    # find the file view.
    file_path = view.settings().get('file_path')
    window = sublime.active_window()
    file_view = None
    for v in window.views():
      if v.file_name() == file_path:
        file_view = v
        break
    if file_view == None:
      return

    self.file_view = file_view
    window.focus_view(file_view)
    file_view.run_command("goto_line", {"line": line})
    file_region = file_view.line(file_view.sel()[0])

    # highlight file_view line
    file_view.add_regions(RESULT_VIEW_NAME, [file_region], "string")


