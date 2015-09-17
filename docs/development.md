# golangconfig Development

 - [Package Coverage](https://packagecontrol.io/packages/Package%20Coverage) is
   used to run tests and measure code coverage
 - All code must pass the checks of the Sublime Text package
   [Python Flake8 Lint](https://packagecontrol.io/packages/Python%20Flake8%20Lint).
   The `python_interpreter` setting should be set to `internal`.
 - Tests and coverage measurement must be run in the UI thread since the package
   utilizes the `sublime` API, which is not thread safe on ST2
 - Sublime Text 2 and 3 must be supported, on Windows, OS X and Linux
 - In public-facing functions, types should be strictly checked to help reduce
   edge-case bugs
 - All functions must include a full docstring with parameter and return types
   and a list of exceptions raised
 - All code should use a consistent Python header

```python
# coding: utf-8
from __future__ import unicode_literals, division, absolute_import, print_function
```

 - Markdown-based API documentation can be automatically copied from the source
   code by executing `dev/api_docs.py` with a Python installation containing
   the `CommonMark` package

```bash
pip install CommonMark
python dev/api_docs.py
```
