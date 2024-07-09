import unittest

import cerberus


"""
python -m "utility.tests.test_views"
"""


class TestViews(unittest.TestCase):
    
    
    def test_basic(self):
        
        
        def validate_request_schema(func):
            
            def wrapper(*args, **kwargs):
                
                if args:
                    pass
                
                return func(*args, **kwargs)
        

