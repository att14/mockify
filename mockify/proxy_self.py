# -*- coding: utf-8 -*-
"""Enables the mocking of attributes that reside on instances of a test
case from a scope where the instance does not yet exist.

``proxy_self`` can be used the same as you would use ``self`` within the
context of a ``setup_teardown``.

.. code-block:: python

     import testify as T
     from mockify import patch, proxy_self


     class SomeObject(object):
         def work(self):
             return 'foo'

         def play(self):
             return 'bar'


     class SomeTestCase(T.TestCase):
         patched_instance_var = patch.proxy(proxy_self.instance_var.work)

         def __init__(self, *args, **kwargs):
             super(SomeTestCase, self).__init__(*args, **kwargs)
             self.instance_var = SomeObject()

Now, a ``setup_teardown`` has been added to ``SomeTestCase``. The resulting
mock can be accessed within a test case as ``patched_instance_var``.

**NOTE**: The member we are mocking (in this case ``instance_var``), must be a
member of the instance before the setup phase (e.g. in __init__ or as a
classvar).

**NOTE**: The call to ``patch`` must be assigned to a variable. This allows
testify to find the ``setup_teardown`` during the setup/teardown phase of
the test case.

.. code-block:: python

        def test_something(self):
            self.instance_var.work(1, 2, 3) # Returns a mock.
            self.patched_instance_var.assert_called_once_with(1, 2, 3)

Additionally, ``proxy_self`` can automatically generate a ``setup_teardown``.

.. code-block:: python

        patched_business_add = T.proxy_self.instance_var.play.patch(
            return_value=mock.Mock()
        )

If you need to mock a method that has the same name as an attribute that is
also defined on ``proxy_self`` you must use :py:meth:`escape`.

.. code-block:: python

    class Example(object):
        attribute = None

        def __getattr__(self, attr):
            return 'example'

    class ExampleTestCase(T.TestCase):
        patched_example = proxy_self.example.escape('__getattr__').patch(
            side_effect=Exception
        )

        def __init__(self, *args, **kwargs):
            super(ExampleTestCase, self).__init__(*args, **kwargs)
            self.example = Example()

        def test_example(self):
            with T.assert_raises(Exception):
                self.example.attribute

If you need to mock a method so that some of its attributes are based on
instance variables of your test case, you can use the ``patch_setup`` method of
``proxy_self``.

.. code-block:: python

    class ExampleTestCase(T.TestCase):

        @T.let
        def work(self):
            return 'baz'

        @T.proxy_self.SomeObject.work.patch_setup()
        def patch_work(self, mock_work):
            mock_work.return_value = self.work
"""
from .patch import patch


class ProxySelfMeta(type):
    """Allows ``proxy_self`` to have the interface where it does not need to be
    instantiated, but calls to ``__getattr__`` are recorded for use when
    creating the ``setup_teardown``.

    More specifically, it allows ``proxy_self`` to have an unbound
    ``__getattr__`` and a bound one. This actually allows the first call to
    ``__getattr__`` to instantiate and return a ``proxy_self``. While,
    subsequent calls to ``__getattr__`` are handled by the actual instance of
    ``proxy_self``, not ``ProxySelfMeta``.
    """

    def __getattr__(cls, attr):
        return cls(attr)


class proxy_self(object):

    __metaclass__ = ProxySelfMeta

    def __init__(self, *args):
        self.__names = args

    def __getattr__(self, attr):
        return type(self)(*self.__names + (attr,))

    escape = __getattr__

    def get_target_(self, test_case_instance):
        """Chains calls to ``getattr`` starting with the instance of the test
        case to get the target for mock.
        """
        return reduce(getattr, self.__names[:-1], test_case_instance)

    @property
    def attribute_(self):
        return self.__names[-1]

    def patch(self, *args, **kwargs):
        return patch.proxy(self, *args, **kwargs)

    def patch_setup(self, *args, **kwargs):
        return self.patch(*args, **kwargs).setup

    __call__ = patch
