# golangconfig Package Developer Documentation

`golangconfig` is primarily an API for package developers to obtain
configuration information about a user's Go environment.

 - [Overview](#overview)
 - [Example](#example)
 - [API Documentation](#api-documentation)

## Overview

The `subprocess_info()` is the primary function that will be used in packages.
It accepts five parameters. The first two are positional:
 
 1. the name of the requested executable
 2. a list of required environmental variables

The three remaining parameters are keyword arguments:

 - optional_vars: a list of vars that will be pulled from project or Sublime
   Text settings and used an environmental variables
 - view: a `sublime.View` object, if available
 - window: a `sublime.Window` object, if available

The function returns a two-element tuple containing the path to the executable
and a `dict` to pass via the `env=` arg of `subprocess.Popen()`.

The `sublime.View` and/or `sublime.Window` objects are used to obtain
project-specific settings. These objects are available via attributes of the
`sublime_plugin.WindowCommand` and `sublime_plugin.TextCommand` classes.

The `golangconfig` package interacts with Sublime Text's settings API, which
means that all calls must occur within the UI thread for compatiblity with
Sublime Text 2.

### Errors

If the executable can not be found, a `golangconfig.ExecutableError()` will be
raised. It has two attributes: `.name` which is the name of the executable that
could not be found, and `.dirs` which is a list of the dirs searched by first
looking at the `PATH` from the Sublime Text settings, and then looking at the
shell `PATH` value.

If one of the required environmental variables is not set, an
`golangconfig.EnvVarError()` will be raised. It has one attribute: `.missing`
which is a list of all required environmental variables that could not be
found in the Sublime Text settings, or the shell environment.

### Requiring the Dependency

When developing a package to utilize `golangconfig`, Package Control needs to be
told to ensure that `golangconfig` is installed. To accomplish this, a file
named `dependencies.json` needs to be placed in the root of the package. The
file should contain the following specification:

```json
{
    "*": {
        "*": {
            "shellenv",
            "golangconfig"
        }
    }
}
```

This specification indicates that for all operating systems (the outer `*`) and
all versions of Sublime Text (the nested `*`), the dependencies named `shellenv`
and `golangconfig` are required.

## Example

The following snippet of Python show basic usage of `golangconfig` from within
command classes derived from `sublime_plugin.WindowCommand` and
`sublime_plugin.TextCommand`.

```python
# coding: utf-8
from __future__ import unicode_literals

import sublime
import sublime_plugin

import golangconfig


class MyWindowCommand(sublime_plugin.WindowCommand):
    def run(self):
        try:
            go_path, env = golangconfig.subprocess_info(
                'go',
                ['GOPATH'],
                window=self.window
            )

            # Launch thread to execute subprocess.Popen() ...

        except (golangconfig.ExecutableError) as e:
            error_message = '''
                My Package
               
                The %s executable could not be found. Please ensure it is
                installed and available via your PATH.

                Would you like to view documentation for setting the PATH?
            '''

            prompt = error_message % e.name

            if sublime.ok_cancel_dialog(prompt, 'Open Documentation'):
                self.window.run_command(
                    'open_url',
                    {'url': 'http://example.com/documentation'}
                )

        except (golangconfig.EnvVarError) as e:
            error_message = '''
                My Package
               
                The setting%s %s could not be found in your Sublime Text
                settings or your shell environment.

                Would you like to view the configuration documentation?
            '''

            plural = 's' if len(e.missing) > 1 else ''
            setting_names = ', '.join(e.missing)
            prompt = error_message % (plural, settings_names)

            if sublime.ok_cancel_dialog(prompt, 'Open Documentation'):
                self.window.run_command(
                    'open_url',
                    {'url': 'http://example.com/documentation'}
                )


class MyTextCommand(sublime_plugin.TextCommand):
    def run(self):
        # This example omits exception handling for brevity
        gofmt_path, env = golangconfig.subprocess_info(
            'gofmt',
            ['GOPATH'],
            view=self.view
        )

```

Since the `golangconfig` functions must be called in the UI thread, commands
will normally look up any necessary information before firing off a thread to
perform a task in the background.

## API Documentation

The public API consists of the following functions:

 - [`subprocess_info()`](#subprocess_info-function)
 - [`setting_value()`](#setting_value-function)
 - [`executable_path()`](#executable_path-function)
 - [`debug_enabled()`](#debug_enabled-function)

### `subprocess_info()` function

> ```python
> def subprocess_info(executable_name, required_vars, optional_vars=None, view=None, window=None):
>     """
>     :param executable_name:
>         A unicode string of the executable to locate, e.g. "go" or "gofmt"
>
>     :param required_vars:
>         A list of unicode strings of the environmental variables that are
>         required, e.g. "GOPATH". Obtains values from setting_value().
>
>     :param optional_vars:
>         A list of unicode strings of the environmental variables that are
>         optional, but should be pulled from setting_value() if available - e.g.
>         "GOOS", "GOARCH". Obtains values from setting_value().
>
>     :param view:
>         A sublime.View object to use in finding project-specific settings. This
>         should be passed whenever available.
>
>     :param window:
>         A sublime.Window object to use in finding project-specific settings.
>         This will only work for Sublime Text 3, and should only be passed if
>         no sublime.View object is available to pass via the view parameter.
>
>     :raises:
>         RuntimeError
>             When the function is called from any thread but the UI thread
>         TypeError
>             When any of the parameters are of the wrong type
>         golangconfig.ExecutableError
>             When the executable requested could not be located. The .name
>             attribute contains the name of the executable that could not be
>             located. The .dirs attribute contains a list of unicode strings
>             of the directories searched.
>         golangconfig.EnvVarError
>             When one or more required_vars are not available. The .missing
>             attribute will be a list of the names of missing environmental
>             variables.
>
>     :return:
>         A two-element tuple.
>
>          - [0] A unicode string (byte string for ST2) of the path to the executable
>          - [1] A dict to pass to the env parameter of subprocess.Popen()
>     """
> ```
>
> Gathers and formats information necessary to use subprocess.Popen() to
> run one of the go executables, with details pulled from setting_value() and
> executable_path().
>
> Ensures that the executable path and env dictionary are properly encoded for
> Sublime Text 2, where byte strings are necessary.

### `setting_value()` function

> ```python
> def setting_value(setting_name, view=None, window=None):
>     """
>     :param setting_name:
>         A unicode string of the setting to retrieve
>
>     :param view:
>         A sublime.View object to use in finding project-specific settings. This
>         should be passed whenever available.
>
>     :param window:
>         A sublime.Window object to use in finding project-specific settings.
>         This will only work for Sublime Text 3, and should only be passed if
>         no sublime.View object is available to pass via the view parameter.
>
>     :raises:
>         RuntimeError
>             When the function is called from any thread but the UI thread
>         TypeError
>             When any of the parameters are of the wrong type
>
>     :return:
>         A two-element tuple.
>
>         If no setting was found, the return value will be:
>
>          - [0] None
>          - [1] None
>
>         If a setting was found, the return value will be:
>
>          - [0] The setting value
>          - [1] The source of the setting, a unicode string:
>            - "project file (os-specific)"
>            - "golang.sublime-settings (os-specific)"
>            - "project file"
>            - "golang.sublime-settings"
>            - A unicode string of the path to the user's login shell
>
>         The second element of the tuple is intended to be used in the display
>         of debugging information to end users.
>     """
> ```
>
> Returns the user's setting for a specific variable, such as GOPATH or
> GOROOT. Supports global and per-platform settings. Finds settings by
> looking in:
>
> 1. If a project is open, the project settings
> 2. The global golang.sublime-settings file
> 3. The user's environmental variables, as defined by their login shell
>
> If the setting is a known name, e.g. GOPATH or GOROOT, the value will be
> checked to ensure the path exists.

### `executable_path()` function

> ```python
> def executable_path(executable_name, view=None, window=None):
>     """
>     :param name:
>         The name of the binary to find - a unicode string of "go", "gofmt" or
>         "godoc"
>
>     :param view:
>         A sublime.View object to use in finding project-specific settings. This
>         should be passed whenever available.
>
>     :param window:
>         A sublime.Window object to use in finding project-specific settings.
>         This will only work for Sublime Text 3, and should only be passed if
>         no sublime.View object is available to pass via the view parameter.
>
>     :raises:
>         RuntimeError
>             When the function is called from any thread but the UI thread
>         TypeError
>             When any of the parameters are of the wrong type
>
>     :return:
>         A 2-element tuple.
>
>         If the executable was not found, the return value will be:
>
>          - [0] None
>          - [1] None
>
>         If the exeutable was found, the return value will be:
>
>          - [0] A unicode string of the full path to the executable
>          - [1] A unicode string of the source of the PATH value
>            - "project file (os-specific)"
>            - "golang.sublime-settings (os-specific)"
>            - "project file"
>            - "golang.sublime-settings"
>            - A unicode string of the path to the user's login shell
>
>         The second element of the tuple is intended to be used in the display
>         of debugging information to end users.
>     """
> ```
>
> Uses the user's Sublime Text settings and then PATH environmental variable
> as set by their login shell to find a go executable

### `debug_enabled()` function

> ```python
> def debug_enabled():
>     """
>     :raises:
>         RuntimeError
>             When the function is called from any thread but the UI thread
>
>     :return:
>         A boolean - if debug is enabled
>     """
> ```
>
> Checks to see if the "debug" setting is true
