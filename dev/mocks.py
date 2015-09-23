# coding: utf-8
from __future__ import unicode_literals, division, absolute_import, print_function

import os
import sys
import shutil
import locale

import golangconfig

if sys.version_info < (3,):
    from cStringIO import StringIO
else:
    from io import StringIO


class SublimeViewMock():

    _settings = None
    _context = None

    def __init__(self, settings, context):
        self._settings = settings
        self._context = context

    def settings(self):
        return {'golang': self._settings}

    def window(self):
        return self._context.window


class SublimeWindowMock():

    _settings = None
    _context = None

    def __init__(self, settings, context):
        self._settings = settings
        self._context = context

    def project_data(self):
        return {'settings': {'golang': self._settings}}

    def active_view(self):
        return self._context.view


class ShellenvMock():

    _shell = None
    _data = None

    def __init__(self, shell, data):
        self._shell = shell
        self._data = data

    def get_env(self, for_subprocess=False):
        if not for_subprocess or sys.version_info >= (3,):
            return (self._shell, self._data)
        fs_encoding = 'mbcs' if sys.platform == 'win32' else 'utf-8'
        env_encoding = locale.getpreferredencoding() if sys.platform == 'win32' else 'utf-8'

        shell = self._shell.encode(fs_encoding)
        env = {}
        for name, value in self._data.items():
            env[name.encode(env_encoding)] = value.encode(env_encoding)

        return (shell, env)

    def get_path(self):
        return (self._shell, self._data.get('PATH', '').split(os.pathsep))


class SublimeSettingsMock():

    _values = None

    def __init__(self, values):
        self._values = values

    def get(self, name, default=None):
        return self._values.get(name, default)


class SublimeMock():

    _settings = None
    View = SublimeViewMock
    Window = SublimeWindowMock

    def __init__(self, settings):
        self._settings = SublimeSettingsMock(settings)

    def load_settings(self, basename):
        return self._settings


class GolangConfigMock():

    _shellenv = None
    _sublime = None
    _stdout = None

    _tempdir = None

    _shell = None
    _env = None
    _view_settings = None
    _window_settings = None
    _sublime_settings = None

    def __init__(self, shell, env, view_settings, window_settings, sublime_settings):
        self._shell = shell
        self._env = env
        self._view_settings = view_settings
        self._window_settings = window_settings
        self._sublime_settings = sublime_settings
        self._tempdir = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'mock_fs')
        if not os.path.exists(self._tempdir):
            os.mkdir(self._tempdir)

    @property
    def view(self):
        if self._view_settings is None:
            return None
        return SublimeViewMock(self._view_settings, self)

    @property
    def window(self):
        if self._window_settings is None:
            return None
        return SublimeWindowMock(self._window_settings, self)

    @property
    def tempdir(self):
        return self._tempdir

    def __enter__(self):
        self._shellenv = golangconfig.shellenv
        golangconfig.shellenv = ShellenvMock(self._shell, self._env)
        self._sublime = golangconfig.sublime
        golangconfig.sublime = SublimeMock(self._sublime_settings)
        self._stdout = sys.stdout
        sys.stdout = StringIO()
        return self

    def __exit__(self, exc_type, exc_value, traceback):
        golangconfig.shellenv = self._shellenv
        golangconfig.sublime = self._sublime
        temp_stdout = sys.stdout
        sys.stdout = self._stdout
        print(temp_stdout.getvalue(), end='')
        if self._tempdir and os.path.exists(self._tempdir):
            shutil.rmtree(self._tempdir)
