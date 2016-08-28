mockify
=======

<a href="https://codeclimate.com/github/att14/mockify"><img src="https://codeclimate.com/github/att14/mockify/badges/gpa.svg" /></a>

A compatibility layer between [Testify](https://github.com/Yelp/Testify) and
[mock](http://www.voidspace.org.uk/python/mock/).

```python
class Goku(object):

    @property
    def nickname(self):
        return "Kakarot"

    @property
    def power_level(self):
        return 1


class Vegeta(object):

    def __init__(self, target=Goku):
        self.target = target()

    def check_power_level(self):
        return "It's over 9000!" if self.target.power_level > 9000 \
                                 else 'Goodbye, {0}!'.format(self.target.nickname)
```

Before
------

```python
import mock
import testify as T

from dbz import Goku, Vegeta


class VegetaTestCase(T.TestCase):

    @T.setup_teardown
    def patch_power_level(self):
        with mock.patch.object(Goku, 'power_level',
                               return_value=9001) as self.mock_power_level:
            yield

    def test_power_level(self):
        T.assert_equal(Vegeta().check_power_level(), "It's over 9000!")
        self.mock_power_level.assert_called_once_with()
```

After
-----

```python
import testify as T
from mockify import patch

from dbz import Goku, Vegeta


class VegetaTestCase(T.TestCase):

    mock_power_level = patch.object(Goku, 'power_level', return_value=9001)

    def test_power_level(self):
        T.assert_equal(Vegeta().check_power_level(), "It's over 9000!")
        self.mock_power_level.assert_called_once_with()
```
