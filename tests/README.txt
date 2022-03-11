Tests are broken down into separate files to have cleaner imports.

It's easier to find which tests we're looking at, and may make it easier to run only specific tests and not the whole suite every time


The refactor of the tests layout was primarily to facilitate functionality/features moving between the three classes.
It should make it easier to test the functionality in a different class just by changing the declaration in setUp() rather than cut/paste to a different file
