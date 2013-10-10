# -*- coding: utf-8 -*-
"""``patch`` is a macro for the creation of a Testify ``setup_teardown`` that
uses ``mock.patch`` as its patcher.

.. code-block:: python

    import testify as T
    from mockify import patch

    from somewhere import SomeClass


    class SomeTestCase(T.TestCase):
        patched_method = patch.object(SomeClass, 'method', return_value=4)

``SomeTestCase`` now has a ``setup_teardown`` which patches
``SomeClass.method``.  The resulting mock can be accessed on the test instance
with the name to which the call to ``patch`` was assigned.

.. code-block:: python

        def test_method(self):
            SomeClass.method() # Returns a mock.
            self.patched_method.assert_called_once_with()

``patch`` can also be use as a decorator, much like ``mock.patch``.

.. code-block:: python

        @patch.object(SomeClass, 'other_method', return_value=5)
        def test_other_method(self, mock_other_method):
             T.assert_equal(SomeClass.other_method(), 5)
             mock_other_method.assert_called_once_with()

``patch.name`` is like ``patch.object``, except that it uses ``mock.patch``
rather than ``mock.patch.object`` as its underlying context manager. Similarly,
``patch.proxy`` allows a ``proxy_self`` to be patched with the same interface
as the other ``patch`` methods.

If invoked directly, ``patch`` will automatically determine which ``Patch``
type should be used. That is, the addition of ``.object`` or ``.name`` after
``patch`` is not necessary, except for in some extremely obscure edge cases
(i.e. mocking a fuction on a string literal).

.. code-block::python

        @patch(SomeClass, 'other_method', return_value=5)
        def test_business_add_again(self, patched_other_method):
            T.assert_equal(SomeClass.other_method(), 5)
            patched_other_method.assert_called_once_with()

Sometimes the setup of a mock is complicated enough that it is not convenient
to specify the parameters to the mock in a single function invocation. In this
case you can use ``patch.setup`` which is used as a decorator for a method that
initializes the mock.

.. code-block::python

        @patch.setup(SomeClass, 'some_instance')
        def mock_instance(self, mock_instance):
            mock_instance.method1.return_value = "a"
            mock_instance.method2.return_value = "b"
            mock_instance.method3.side_effect = Exception

This approach also allows you to set attributes on the mock that are only
defined on the instance of the test case.

.. code-block::python

        @patch.setup(SomeClass, 'some_instance')
        def mock_instance(self, mock_instance):
            mock_instance.method1.return_value = self.busines_id
"""
from functools import wraps

import mock
import testify


class Patch(object):

    __name__ = "Patch"

    @classmethod
    def patch(cls, *args, **kwargs):
        return testify.setup_teardown(cls(*args, **kwargs))

    def __init__(self, *args, **kwargs):
        self.args = args
        self.kwargs = kwargs
        self.setup_function = None
        self.mock = None
        self.patcher = None

    def __call__(self, scope):
        if callable(scope):
            return self.decorator(scope)
        return self.setup_teardown(scope)

    def decorator(self, func):
        @wraps(func)
        def __wrapped(test_case_instance, *args, **kwargs):
            with self.build_patcher(test_case_instance) as mock_instance:
                return func(test_case_instance, mock_instance, *args, **kwargs)
        return __wrapped

    def setup_teardown(self, test_case_instance):
        with self.build_patcher(test_case_instance) as self.mock:
            if self.setup_function:
                self.setup_function(test_case_instance, self.mock)
            yield
            self.mock = None

    def __enter__(self):
        self.patcher = self.build_patcher(None)
        return self.patcher.start()

    def __exit__(self, exc_type, exc_value, traceback):
        if self.patcher:
            self.patcher.stop()

    def __get__(self, instance, owner):
        # Defining ``__get__`` here serves two purposes. First, it convinces
        # ``inspect`` that this class is of type 'method' (even though it isn't
        # really). Because Testify explicitly makes instance methods from
        # functions defined on the class it doesnt matter that this is not a
        # proper 'method' in the sense that it returns bound instances of
        # itself when called with an instance. Second, it allows for different
        # behavior depending on whether or not this is called from an instance
        # of a test case. This lets Testify register the ``setup_teardown``
        # while still giving access to the mock during the ``TestCase``.
        return self if instance is None else self.mock

    def setup(self, setup_function):
        """A decorator that handles setting the setup function that will be
        called after mocking but before yielding and ending the setup.
        """
        self.setup_function = setup_function
        return self


class PatchObject(Patch):

    __name__ = "PatchObject"

    def build_patcher(self, test_case_instance):
        return mock.patch.object(*self.args, **self.kwargs)


class PatchProxy(Patch):

    __name__ = "PatchProxy"

    def __init__(self, proxy, *args, **kwargs):
        self.proxy = proxy
        super(PatchProxy, self).__init__(self.proxy.attribute_, *args, **kwargs)

    def build_patcher(self, test_case_instance):
        assert test_case_instance
        return mock.patch.object(
            self.proxy.get_target_(test_case_instance),
            *self.args,
            **self.kwargs
        )


class PatchName(Patch):

    __name__ = "PatchName"

    def build_patcher(self, test_case_instance):
        return mock.patch(*self.args, **self.kwargs)


class patch_base(object):

    class __metaclass__(type):

        def __call__(cls, target, *args, **kwargs):
            # This isinstance check would not work if you wanted to mock a method
            # on a string instance. You probably don't want to do this anyway, but
            # if you really need to, just use `.object` explicitly.
            if isinstance(target, str):
                return cls.name(target, *args, **kwargs)
            elif hasattr(target, 'get_target_'):
                return cls.proxy(target, *args, **kwargs)
            else:
                return cls.object(target, *args, **kwargs)

    @classmethod
    def name(cls, *args, **kwargs):
        return cls.build_patch(PatchName, *args, **kwargs)

    @classmethod
    def object(cls, *args, **kwargs):
        return cls.build_patch(PatchObject, *args, **kwargs)

    @classmethod
    def proxy(cls, *args, **kwargs):
        return cls.build_patch(PatchProxy, *args, **kwargs)


class patch_setup(patch_base):

    @classmethod
    def build_patch(cls, patch_class, *args, **kwargs):
        return patch_class.patch(*args, **kwargs).setup


class patch(patch_base):

    @classmethod
    def build_patch(cls, patch_class, *args, **kwargs):
        return patch_class.patch(*args, **kwargs)

    setup = patch_setup
