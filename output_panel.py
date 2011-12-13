
import sublime
import sublime_plugin

# Manage the results window for outputs

RESULT_VIEW_NAME = 'js_result_view'
SETTINGS_FILE = "NodeTools.sublime-settings"
PACKAGE_NAME  = "SublimeNodeTools"

###############################################
# Support Functions
#

def show_output_panel(window):
  window.run_command("show_panel", {"panel": "output."+RESULT_VIEW_NAME})

def hide_output_panel(window):
  window.run_command("hide_panel", {"panel": "output."+RESULT_VIEW_NAME})

def toggle_setting(settings, key_name, default_value):
  current_setting = settings.get(key_name, default_value)
  settings.set(key_name, not current_setting)


def init_output_panel(window, prompt, file_path):
  output_view = window.get_output_panel(RESULT_VIEW_NAME)
  output_view.set_name(RESULT_VIEW_NAME)

  syntax_file = 'Packages/'+PACKAGE_NAME+'/TestConsole.tmLanguage'
  color_file  = 'Packages/'+PACKAGE_NAME+'/TestConsole.tmTheme'
  output_view.set_syntax_file(syntax_file)
  output_view.settings().set('color_scheme', color_file)
  output_view.set_read_only(True)


  clear_output_panel(output_view, prompt)
  output_view.settings().set("file_path", file_path)
  return output_view

def clear_output_panel(output_view, prompt):
  output_view.set_read_only(False)
  edit = output_view.begin_edit()
  output_view.erase(edit, sublime.Region(0, output_view.size()))
  output_view.insert(edit, output_view.size(), prompt)
  output_view.end_edit(edit)
  output_view.set_read_only(True)

def append_output_panel(output_view, data, end=False):
  data = data.decode('utf8')
  
  output_view.set_read_only(False)
  edit = output_view.begin_edit()
  output_view.insert(edit, output_view.size(), data)
  output_view.end_edit(edit)
  output_view.set_read_only(True)
    

###############################################
# Commands
#

class HideResultCommand(sublime_plugin.WindowCommand):
  """show jslint result"""
  def run(self):
    hide_output_panel(self.window)

class ShowResultCommand(sublime_plugin.WindowCommand):
  """show jslint result"""
  def run(self):
    show_output_panel(self.window)

