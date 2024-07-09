import unittest
from ..secret import *

import hashlib
import base64
import json

"""
python -m utility.tests.test_secret
"""


class SecretsTest(unittest.TestCase):
    
    def test_generate_secret(self):
        secret_length = 8
        secret = generate_secret(secret_length)
        self.assertEqual(len(secret), secret_length, "generated secret should be of given length")
        
        
    def test_encryption_with_salt(self):
        
        
        secret = "somePassword@1234"
        
        encrypted_secret, salt = encrypt_with_salt(secret)
        self.assertIsInstance(encrypted_secret, bytes)
        self.assertIsInstance(salt, bytes)
        self.assertEqual(len(salt), 16)

        secret_meta = generate_secret_meta(secret, salt)
        self.assertIsInstance(secret_meta, str)
        secret_meta_ = json.loads(secret_meta)
        self.assertIn("encrypted_secret", secret_meta_)
        self.assertIn("salt", secret_meta_)
        self.assertIn("iterations", secret_meta_)
        self.assertIn("hash_algorithm", secret_meta_)
        self.assertIsInstance(secret_meta_["encrypted_secret"], str)
        self.assertIsInstance(secret_meta_["salt"], str)
        base64.b64decode(secret_meta_["encrypted_secret"].encode())
        base64.b64decode(secret_meta_["salt"].encode())
        
        status = validate_secret(secret, secret_meta)
        self.assertIsInstance(status, bool)
        self.assertTrue(status, status)
        
        with self.assertRaises(InvalidSecret):
            
            validate_secret("just some string", secret)
            validate_secret("{'string': 'which is json serializable'}", secret)
            validate_secret("{'encrypted_secret': 'incomplete meta'}", secret)
            
            s = secret_meta_.copy()
            s.pop('encrypted_secret')
            s['encrypted_secret'] = "some string that is not base64 encoded"
            validate_secret(json.dumps(s), secret)
            
            s = secret_meta_.copy()
            s.pop('salt')
            s['salt'] = "some string that is not base64 encoded"
            validate_secret(json.dumps(s), secret)

        # final flow after abstraction
        secret, secret_meta = generate_random_secret_meta(url_safe_base64encode=True)
        status = validate_secret(secret, secret_meta, url_safe_base64encode=True)
        self.assertIsInstance(status, bool)
        self.assertTrue(status, status)


if __name__ == '__main__':
    unittest.main()

