# coding: utf-8
from __future__ import unicode_literals, division, absolute_import, print_function

import unittest

import sys
import os
import stat

if sys.version_info < (3,):
    str_cls = unicode  # noqa
else:
    str_cls = str

import golangconfig
from .mocks import GolangConfigMock
from .unittest_data import data, data_class


class CustomString():

    value = None

    def __init__(self, value):
        self.value = value

    def __str__(self):
        return self.value

    def __unicode__(self):
        return self.__str__()


@data_class
class GolangconfigTests(unittest.TestCase):

    @staticmethod
    def subprocess_info_data():
        return (
            (
                'basic_shell',
                '/bin/bash',
                {
                    'PATH': '{tempdir}bin:{tempdir}usr/bin',
                    'GOPATH': '{tempdir}gopath',
                },
                None,
                None,
                {'debug': True},
                ['usr/bin/go'],
                ['gopath/'],
                'go',
                ['GOPATH'],
                None,
                (
                    '{tempdir}usr/bin/go',
                    {
                        'PATH': '{tempdir}bin:{tempdir}usr/bin',
                        'GOPATH': '{tempdir}gopath',
                    }
                ),
            ),
            (
                'view_setting_override',
                '/bin/bash',
                {
                    'PATH': '{tempdir}bin:{tempdir}usr/bin',
                    'GOPATH': '{tempdir}gopath',
                },
                {'GOPATH': '{tempdir}custom/gopath', 'GOOS': 'windows'},
                None,
                {'debug': True},
                ['usr/bin/go'],
                ['custom/gopath/'],
                'go',
                ['GOPATH'],
                None,
                (
                    '{tempdir}usr/bin/go',
                    {
                        'PATH': '{tempdir}bin:{tempdir}usr/bin',
                        'GOPATH': '{tempdir}custom/gopath',
                    }
                ),
            ),
            (
                'view_setting_override_optional_missing',
                '/bin/bash',
                {
                    'PATH': '{tempdir}bin:{tempdir}usr/bin',
                    'GOPATH': '{tempdir}gopath',
                },
                {'GOPATH': '{tempdir}custom/gopath'},
                None,
                {'debug': True},
                ['usr/bin/go'],
                ['custom/gopath/'],
                'go',
                ['GOPATH'],
                ['GOOS'],
                (
                    '{tempdir}usr/bin/go',
                    {
                        'PATH': '{tempdir}bin:{tempdir}usr/bin',
                        'GOPATH': '{tempdir}custom/gopath',
                    }
                ),
            ),
            (
                'view_setting_override_optional_present',
                '/bin/bash',
                {
                    'PATH': '{tempdir}bin:{tempdir}usr/bin',
                    'GOPATH': '{tempdir}gopath',
                },
                {'GOPATH': '{tempdir}custom/gopath', 'GOOS': 'windows'},
                None,
                {'debug': True},
                ['usr/bin/go'],
                ['custom/gopath/'],
                'go',
                ['GOPATH'],
                ['GOOS'],
                (
                    '{tempdir}usr/bin/go',
                    {
                        'PATH': '{tempdir}bin:{tempdir}usr/bin',
                        'GOPATH': '{tempdir}custom/gopath',
                        'GOOS': 'windows',
                    }
                ),
            ),
            (
                'view_setting_unset',
                '/bin/bash',
                {
                    'PATH': '{tempdir}bin:{tempdir}usr/bin',
                    'GOPATH': '{tempdir}gopath',
                    'GOOS': 'windows'
                },
                {'GOPATH': '{tempdir}custom/gopath', 'GOOS': None},
                None,
                {'debug': True},
                ['usr/bin/go'],
                ['custom/gopath/'],
                'go',
                ['GOPATH'],
                ['GOOS'],
                (
                    '{tempdir}usr/bin/go',
                    {
                        'PATH': '{tempdir}bin:{tempdir}usr/bin',
                        'GOPATH': '{tempdir}custom/gopath',
                    }
                ),
            ),
            (
                'no_executable',
                '/bin/bash',
                {
                    'PATH': '{tempdir}bin:{tempdir}usr/bin',
                    'GOPATH': '{tempdir}gopath',
                },
                {'GOPATH': '{tempdir}custom/gopath'},
                None,
                {'debug': True, 'PATH': '{tempdir}usr/local/bin'},
                [],
                ['custom/gopath/'],
                'go',
                ['GOPATH'],
                None,
                golangconfig.ExecutableError
            ),
            (
                'env_var_missing',
                '/bin/bash',
                {
                    'PATH': '{tempdir}bin:{tempdir}usr/bin',
                    'GOPATH': '{tempdir}gopath',
                },
                {'GOPATH': '{tempdir}custom/gopath'},
                None,
                {'debug': True},
                ['bin/go'],
                ['custom/gopath/'],
                'go',
                ['GOPATH', 'GOROOT'],
                None,
                golangconfig.EnvVarError
            ),
        )

    @data('subprocess_info_data', True)
    def subprocess_info(self, shell, env, view_settings, window_settings, sublime_settings,
                        executable_temp_files, temp_dirs, executable_name, required_vars, optional_vars,
                        expected_result):

        with GolangConfigMock(shell, env, view_settings, window_settings, sublime_settings) as mock_context:

            tempdir = mock_context.tempdir + os.sep

            # Fill in the tempdir path into all of the configuration data so that
            # the filesystem checks succeed
            for key in env:
                env[key] = env[key].replace('{tempdir}', tempdir)

            if view_settings:
                for key in view_settings:
                    if view_settings[key] is not None:
                        view_settings[key] = view_settings[key].replace('{tempdir}', tempdir)
                for platform in ['osx', 'windows', 'linux']:
                    if platform not in view_settings:
                        continue
                    for key in view_settings[platform]:
                        if view_settings[platform][key] is not None:
                            view_settings[platform][key] = view_settings[platform][key].replace('{tempdir}', tempdir)
            if window_settings:
                for key in window_settings:
                    window_settings[key] = window_settings[key].replace('{tempdir}', tempdir)
                for platform in ['osx', 'windows', 'linux']:
                    if platform not in window_settings:
                        continue
                    for key in window_settings[platform]:
                        window_settings[platform][key] = window_settings[platform][key].replace('{tempdir}', tempdir)

            # Set up the mock executables
            for temp_file in executable_temp_files:
                temp_file_path = os.path.join(mock_context.tempdir, temp_file)
                temp_file_dir = os.path.dirname(temp_file_path)
                if not os.path.exists(temp_file_dir):
                    os.makedirs(temp_file_dir)
                with open(temp_file_path, 'a'):
                    st = os.stat(temp_file_path)
                    os.chmod(temp_file_path, st.st_mode | stat.S_IEXEC)

            # Set up the temp dirs
            for temp_dir in temp_dirs:
                temp_dir_path = os.path.join(mock_context.tempdir, temp_dir)
                if not os.path.exists(temp_dir_path):
                    os.makedirs(temp_dir_path)

            if isinstance(expected_result, tuple):
                executable_path = expected_result[0].replace('{tempdir}', tempdir)
                if sys.version_info < (3,):
                    executable_path = executable_path.encode(golangconfig._fs_encoding)

                env_vars = {}
                for name, value in expected_result[1].items():
                    value = value.replace('{tempdir}', tempdir)
                    if sys.version_info < (3,):
                        name = name.encode(golangconfig._env_encoding)
                        value = value.encode(golangconfig._env_encoding)
                    env_vars[name] = value

                expected_result = (executable_path, env_vars)

                self.assertEquals(
                    expected_result,
                    golangconfig.subprocess_info(
                        executable_name,
                        required_vars,
                        optional_vars=optional_vars,
                        view=mock_context.view,
                        window=mock_context.window
                    )
                )

            else:
                with self.assertRaises(expected_result):
                    golangconfig.subprocess_info(
                        executable_name,
                        required_vars,
                        optional_vars=optional_vars,
                        view=mock_context.view,
                        window=mock_context.window
                    )

    @staticmethod
    def executable_path_data():
        return (
            (
                'basic_shell',
                '/bin/bash',
                {
                    'PATH': '{tempdir}bin:{tempdir}usr/bin'
                },
                None,
                None,
                {'debug': True},
                ['bin/go'],
                [],
                ('{tempdir}bin/go', '/bin/bash'),
            ),
            (
                'basic_view_settings',
                '/bin/bash',
                {
                    'PATH': '{tempdir}bin'
                },
                {'PATH': '{tempdir}usr/bin:{tempdir}usr/local/bin'},
                {},
                {'debug': True},
                ['usr/local/bin/go'],
                ['usr/bin/go'],
                ('{tempdir}usr/local/bin/go', 'project file'),
            ),
            (
                'basic_view_settings_none_found',
                '/bin/bash',
                {
                    'PATH': '{tempdir}bin'
                },
                {'PATH': '{tempdir}usr/bin:{tempdir}usr/local/bin'},
                {},
                {'debug': True},
                [],
                ['usr/bin/go'],
                (None, None),
            ),
        )

    @data('executable_path_data', True)
    def executable_path(self, shell, env, view_settings, window_settings, sublime_settings,
                        executable_temp_files, non_executable_temp_files, expected_result):

        with GolangConfigMock(shell, env, view_settings, window_settings, sublime_settings) as mock_context:

            tempdir = mock_context.tempdir + os.sep

            # Fill in the tempdir path into all of the configuration data so that
            # the filesystem checks succeed
            for key in env:
                env[key] = env[key].replace('{tempdir}', tempdir)
            if view_settings:
                for key in view_settings:
                    view_settings[key] = view_settings[key].replace('{tempdir}', tempdir)
                for platform in ['osx', 'windows', 'linux']:
                    if platform not in view_settings:
                        continue
                    for key in view_settings[platform]:
                        view_settings[platform][key] = view_settings[platform][key].replace('{tempdir}', tempdir)
            if window_settings:
                for key in window_settings:
                    window_settings[key] = window_settings[key].replace('{tempdir}', tempdir)
                for platform in ['osx', 'windows', 'linux']:
                    if platform not in window_settings:
                        continue
                    for key in window_settings[platform]:
                        window_settings[platform][key] = window_settings[platform][key].replace('{tempdir}', tempdir)

            if expected_result[0]:
                expected_result = (expected_result[0].replace('{tempdir}', tempdir), expected_result[1])

            # Set up the mock executables and regular files
            for temp_file in executable_temp_files + non_executable_temp_files:
                temp_file_path = os.path.join(mock_context.tempdir, temp_file)
                temp_file_dir = os.path.dirname(temp_file_path)
                if not os.path.exists(temp_file_dir):
                    os.makedirs(temp_file_dir)
                with open(temp_file_path, 'a'):
                    if temp_file in executable_temp_files:
                        st = os.stat(temp_file_path)
                        os.chmod(temp_file_path, st.st_mode | stat.S_IEXEC)

            self.assertEquals(
                expected_result,
                golangconfig.executable_path('go', mock_context.view, mock_context.window)
            )

    def test_executable_path_path_not_string(self):
        shell = '/bin/bash'
        env = {
            'PATH': '/bin'
        }
        view_settings = {
            'PATH': 1
        }
        with GolangConfigMock(shell, env, view_settings, None, {'debug': True}) as mock_context:
            self.assertEquals((None, None), golangconfig.executable_path('go', mock_context.view, mock_context.window))
            self.assertTrue('is not a string' in sys.stdout.getvalue())

    @staticmethod
    def setting_value_gopath_data():
        return (
            (
                'basic_shell',
                '/bin/bash',
                {
                    'PATH': '/bin',
                    'GOPATH': os.path.expanduser('~'),
                },
                None,
                None,
                {},
                'GOPATH',
                (os.path.expanduser('~'), '/bin/bash'),
            ),
            (
                'basic_shell_2',
                '/bin/bash',
                {
                    'PATH': '/bin'
                },
                None,
                None,
                {},
                'PATH',
                ('/bin', '/bin/bash'),
            ),
            (
                'basic_view_settings',
                '/bin/bash',
                {
                    'PATH': '/bin',
                    'GOPATH': os.path.expanduser('~'),
                },
                {'GOPATH': '/usr/bin'},
                None,
                {},
                'GOPATH',
                ('/usr/bin', 'project file'),
            ),
            (
                'basic_window_settings',
                '/bin/bash',
                {
                    'PATH': '/bin',
                    'GOPATH': os.path.expanduser('~'),
                },
                None,
                {'GOPATH': '/usr/bin'},
                {},
                'GOPATH',
                ('/usr/bin', 'project file'),
            ),
            (
                'basic_sublime_settings',
                '/bin/bash',
                {
                    'PATH': '/bin',
                    'GOPATH': os.path.expanduser('~'),
                },
                {},
                {},
                {'GOPATH': '/usr/local/bin'},
                'GOPATH',
                ('/usr/local/bin', 'golang.sublime-settings'),
            ),
            (
                'os_view_settings',
                '/bin/bash',
                {
                    'PATH': '/bin',
                    'GOPATH': os.path.expanduser('~'),
                },
                {
                    'osx': {'GOPATH': '/usr/bin'},
                    'windows': {'GOPATH': '/usr/bin'},
                    'linux': {'GOPATH': '/usr/bin'},
                },
                {},
                {},
                'GOPATH',
                ('/usr/bin', 'project file (os-specific)'),
            ),
            (
                'os_window_settings',
                '/bin/bash',
                {
                    'PATH': '/bin',
                    'GOPATH': os.path.expanduser('~'),
                },
                None,
                {
                    'osx': {'GOPATH': '/usr/bin'},
                    'windows': {'GOPATH': '/usr/bin'},
                    'linux': {'GOPATH': '/usr/bin'},
                },
                {},
                'GOPATH',
                ('/usr/bin', 'project file (os-specific)'),
            ),
            (
                'os_sublime_settings',
                '/bin/bash',
                {
                    'PATH': '/bin',
                    'GOPATH': os.path.expanduser('~'),
                },
                {
                    'GOPATH': '/foo/bar'
                },
                {},
                {
                    'osx': {'GOPATH': '/usr/local/bin'},
                    'windows': {'GOPATH': '/usr/local/bin'},
                    'linux': {'GOPATH': '/usr/local/bin'},
                },
                'GOPATH',
                ('/usr/local/bin', 'golang.sublime-settings (os-specific)'),
            ),
            (
                'os_sublime_settings_wrong_type',
                '/bin/bash',
                {
                    'PATH': '/bin',
                    'GOPATH': os.path.expanduser('~'),
                },
                {},
                {},
                {
                    'osx': 1,
                    'windows': 1,
                    'linux': 1,
                },
                'GOPATH',
                (os.path.expanduser('~'), '/bin/bash'),
            ),
        )

    @data('setting_value_gopath_data', True)
    def setting_value_gopath(self, shell, env, view_settings, window_settings, sublime_settings, setting, result):

        with GolangConfigMock(shell, env, view_settings, window_settings, sublime_settings) as mock_context:
            self.assertEquals(result, golangconfig.setting_value(setting, mock_context.view, mock_context.window))

    def test_setting_value_bytes_name(self):
        shell = '/bin/bash'
        env = {
            'GOPATH': os.path.expanduser('~')
        }
        with GolangConfigMock(shell, env, None, None, {'debug': True}) as mock_context:
            with self.assertRaises(TypeError):
                golangconfig.setting_value(b'GOPATH', mock_context.view, mock_context.window)

    def test_setting_value_custom_type(self):
        shell = '/bin/bash'
        env = {
            'GOPATH': os.path.expanduser('~')
        }
        with GolangConfigMock(shell, env, None, None, {'debug': True}) as mock_context:
            with self.assertRaises(TypeError):
                golangconfig.setting_value(CustomString('GOPATH'), mock_context.view, mock_context.window)

    def test_setting_value_incorrect_view_type(self):
        shell = '/bin/bash'
        env = {
            'GOPATH': os.path.expanduser('~')
        }
        with GolangConfigMock(shell, env, None, None, {'debug': True}) as mock_context:
            with self.assertRaises(TypeError):
                golangconfig.setting_value('GOPATH', True, mock_context.window)

    def test_setting_value_incorrect_window_type(self):
        shell = '/bin/bash'
        env = {
            'GOPATH': os.path.expanduser('~')
        }
        with GolangConfigMock(shell, env, None, None, {'debug': True}) as mock_context:
            with self.assertRaises(TypeError):
                golangconfig.setting_value('GOPATH', mock_context.view, True)

    def test_setting_value_gopath_not_existing(self):
        shell = '/bin/bash'
        env = {
            'GOPATH': os.path.join(os.path.expanduser('~'), 'hdjsahkjzhkjzhiashs7hdsuybyusbguycas')
        }
        with GolangConfigMock(shell, env, None, None, {'debug': True}) as mock_context:
            self.assertEquals(
                (None, None),
                golangconfig.setting_value('GOPATH', mock_context.view, mock_context.window)
            )
            self.assertTrue('does not exist on the filesystem' in sys.stdout.getvalue())

    def test_setting_value_gopath_not_string(self):
        shell = '/bin/bash'
        env = {
            'GOPATH': 1
        }
        with GolangConfigMock(shell, env, None, None, {'debug': True}) as mock_context:
            self.assertEquals(
                (None, None),
                golangconfig.setting_value('GOPATH', mock_context.view, mock_context.window)
            )
            self.assertTrue('is not a string' in sys.stdout.getvalue())
