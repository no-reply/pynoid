
import unittest
import pynoid
import re

class PynoidTests(unittest.TestCase):
    
    def setUp(self):
        pass

    def tearDown(self):
        pass

    def test_naa_append(self):
        noid = pynoid.mint(naa='abc')
        self.assertTrue(noid.startswith('abc/'))

    def test_scheme_append(self):
        schemes = ['doi:', 'ark:/']
        for scheme in schemes:
            noid = pynoid.mint(scheme=scheme)
            self.assertTrue(noid.startswith(scheme))
    
    def test_mint_short_term(self):
        noid = pynoid.mint()
        self.assertTrue(noid.startswith(':shrt:'))

    def test_mint_ns(self):
        ns = range(10)
        for n in ns:
            self.assertEqual(pynoid.mint('d', n), pynoid.DIGIT[n])
        ns = range(29)
        for n in ns:
            self.assertEqual(pynoid.mint('e', n), pynoid.XDIGIT[n])

    def test_namespace_overflow(self):
        self.assertRaises(pynoid.NamespaceError, pynoid.mint, template='d', n=10)
        self.assertRaises(pynoid.NamespaceError, pynoid.mint, template='e', n=29)

    def test_mint_z_rollover(self):
        self.assertEqual(pynoid.mint('zd', 10), '10')        
        self.assertEqual(pynoid.mint('ze', 29), '10')

    def test_validate_valid(self):
        valid = 'test31wqw0wsr'
        validScheme = 'ark:/test31wqw0wsr'
        self.assertTrue(pynoid.validate(valid))
        self.assertTrue(pynoid.validate(validScheme))

    def test_validate_invalid(self):
        invalid = 'test31qww0wsr'
        invalidScheme = 'ark:/test31qww0wsr'
        self.assertRaises(pynoid.ValidationError, pynoid.validate, invalid)
        self.assertRaises(pynoid.ValidationError, pynoid.validate, invalidScheme)

    def test_checkdigit(self):
        self.assertEqual(pynoid.mint('eek', 100), '3f0')
        self.assertRaises(pynoid.ValidationError, pynoid.validate, 'f30')

    def test_version(self):
        self.assertTrue(re.match("pynoid \d.\d\Z", pynoid.version()))

if __name__ == '__main__':
    unittest.main()
        
