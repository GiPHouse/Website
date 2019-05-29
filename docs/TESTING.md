# Testing

To test our code we use multiple testing methods. All of these tests are automatically run by Travis CI when a new pull request is made.
All of these tests need to pass, before a pull request is allowed to be merged into the `master` branch.

If you want to run the tests locally, please look up the relevant test command in the [`.travis.yml`](/.travis.yml) file.
 
### Testing
Every Django app has its own tests (located in the `tests` directory inside the app root). We enforce 100% statement and 100% branch coverage in our tests, to make sure that every line of code and branch is run at least once during testing. We use [`coverage`](https://coverage.readthedocs.io/en/v4.5.x/) to run and analyse these tests. 

To make manual testing easier, we have the `createfixtures` command to automatically create test data. We also test if that command works correctly. 

### Django built-in tests
We run some built-in tests. These tests include checking if there are any database migrations needed but not created yet and checking for common problems.

### Linting
We use multiple to perform static analyis on our code. The most important one is [`flake8`](http://flake8.pycqa.org/en/latest/), a Python linter that checks whether code is formatted according to [PEP8](https://www.python.org/dev/peps/pep-0008/). In addition we also use the [flake8-import-order](https://github.com/PyCQA/flake8-import-order) to make sure the imports are neatly ordered.

Besides `flake8`, we also use [`pydocstyle`](https://github.com/PyCQA/pydocstyle) to enforce that every method, function and class is documented and that documentation is formatted according to [PEP 257](https://www.python.org/dev/peps/pep-0257/).

We also use a few Bash scripts (e.g. for deployment). These are checked using [`shellcheck`](https://github.com/koalaman/shellcheck).
