# -*- coding: utf-8 -*-
import testify as T
from mockify import patch


class Herp(object):

    derp = 0
    foo = 'bar'

    sleep = staticmethod(lambda: "read me a story")
    work = staticmethod(lambda: "No; I'm lazy")


class PatchTestCase(T.TestCase):

    patch_derp_on_herp = patch.object(Herp, 'derp', 1)
    patch_work_on_herp = patch.object(Herp, 'work', return_value="Yes, sir.")

    patch_foo = patch.name('tests.patch_test.Herp.foo', 'not bar')
    patch_not_actually_there = patch.name(
        'tests.patch_test.Herp.not_actually_there',
        create=True
    )

    @patch.setup(Herp, 'sleep', create=True)
    def mock_sleep(self, mock_sleep):
        mock_sleep.return_value = "zzz"

    def test_patch_setup(self):
        T.assert_equal(Herp.sleep(), "zzz")

    def test_patch(self):
        T.assert_equal(Herp.derp, 1)

    def test_mock_accesible_in_body_of_test_method(self):
        T.assert_equal(Herp.work(), "Yes, sir.")
        self.patch_work_on_herp.assert_called_once_with()

    @patch.object(Herp, 'derp', 99)
    def test_patch_decorator(self, patched_derp):
        T.assert_equal(Herp.derp, 99)

    def test_patch_name(self):
        T.assert_equal(Herp.foo, 'not bar')
        Herp.not_actually_there(24)
        self.patch_not_actually_there.assert_called_once_with(24)

    @patch(Herp, 'derp', 99)
    @patch('tests.patch_test.Herp.foo', 100)
    def test_patch_type_inference(self, *args):
        T.assert_equal(Herp.derp, 99)
        T.assert_equal(Herp.foo, 100)

    some_value = lambda self: 'some_value'

    def test_context_manager(self):
        T.assert_equal(self.some_value(), 'some_value')
        with patch.object(self, 'some_value', return_value='another_value'):
            T.assert_equal(self.some_value(), 'another_value')


if __name__ == '__main__':
    T.run()
