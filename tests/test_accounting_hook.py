import unittest
from htcondor_hooks import accounting_hook
import tempfile
import os

CONFIG = """
[hook]
ignore_routes = 
log_file=/tmp/accounting-translate-hook.log
log_level=INFO
syslog_facility=local0
[groups]
physics.hep = \
user1,user2,\
user5,user7

physics.hep.susy = user3,user4

default_group = physics.hep

"""


class Test(unittest.TestCase):

    def setUp(self):
        self.temp = tempfile.NamedTemporaryFile(delete=False)
        self.temp.write(CONFIG)
        self.temp.close()
        self.groups = {
            'physics.hep': ['user1', 'user2','user5','user7'],
            'physics.hep.susy': ['user3', 'user4'],
        }

        self.config_file = self.temp.name

    def tearDown(self):
        os.unlink(self.config_file)

    def test_get_config(self):
        groups = accounting_hook.get_config(self.config_file)['groups']
        self.assertEqual(groups['physics.hep'], self.groups['physics.hep'])
        self.assertEqual(groups['physics.hep.susy'], self.groups['physics.hep.susy'])
        self.assertEqual(groups['default_group'], 'physics.hep')
    
    def test_get_user_mapping(self):
        config = accounting_hook.get_config(self.config_file)
        user_mapping = accounting_hook.get_user_mapping(config)
        self.assertEqual(user_mapping['user1'], 'physics.hep')
        self.assertEqual(user_mapping['user5'], 'physics.hep')
        self.assertEqual(user_mapping['user3'], 'physics.hep.susy')


if __name__ == "__main__":
    #import sys;sys.argv = ['', 'Test.testName']
    unittest.main()
