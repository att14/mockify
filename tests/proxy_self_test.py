# -*- coding: utf-8 -*-
import testify as T
from mockify import patch
from mockify import proxy_self


class ProxySelfTestCase(T.TestCase):

   class Goku(object):

       foo = 'bar'

       @classmethod
       def power_level(cls, arg):
           return "9000"

   thing_one = 'thing_one'
   thing_two = 'thing_two'
   patched_one = proxy_self.thing_one.patch('one')

   patched_foo = proxy_self.Goku.foo.patch('not bar')
   patch_power_level = proxy_self.Goku.power_level.patch(return_value="Over 9000")

   def test_proxy_self(self):
       T.assert_equal(
           ('anything',),
           proxy_self.anything._proxy_self__names
       )
       T.assert_equal(
           ('one', 'two', 'three'),
           proxy_self.one.two.three._proxy_self__names
       )
       T.assert_equal(
           ('one', '__getattr__', 'escape'),
           proxy_self.one.escape('__getattr__').escape('escape')._proxy_self__names
       )

   def test_proxy_self_mocks(self):
       T.assert_equal(self.thing_one, 'one')
       T.assert_equal(self.Goku.foo, 'not bar')

   def test_resulting_mock_accesible_from_test(self):
       T.assert_equal(self.Goku.power_level(20), "Over 9000")
       self.patch_power_level.assert_called_once_with(20)

   @proxy_self.thing_one.patch('one')
   @proxy_self.thing_two.patch('two')
   def test_decorator(self, mock_thing_two, mock_thing_one):
       T.assert_equal(self.thing_one, 'one')
       T.assert_equal(self.thing_two, 'two')

   def test_proxy_self_mocked_at_top_level(self):
       with T.assert_raises(Exception):
           proxy_self.patch()

   @patch(proxy_self.thing_two, 15)
   @patch.proxy(proxy_self.thing_one, 14)
   def test_patch_proxy(self, *args):
       T.assert_equal(self.thing_one, 14)
       T.assert_equal(self.thing_two, 15)


if __name__ == '__main__':
   T.run()
