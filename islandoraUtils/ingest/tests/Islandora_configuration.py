'''
Created on 2012-03-16

@author: William Panting
'''
import unittest, os
from islandoraUtils.ingest.Islandora_configuration import Islandora_configuration

class TestIslandora_configuration(unittest.TestCase):
    
    def test_configuration_dictionary(self):
        expected_result = {'Drupal': {'url': 'http://localhost/drupal'}, 'logging': {'directory': './'}, 'Solr': {'url': 'http://localhost:8080/solr'}, 'Fedora': {'url': 'http://localhost:8080/fedora', 'username': 'fedoraAdmin', 'password': 'islandora'}, 'miscellaneous': {'ingest_name': 'name_of_ingest'}}
        self.assertEqual(expected_result, self.Islandora_config.configuration_dictionary)
        
    @classmethod
    def setUp(self):
        #make a log file in cwd
        configuration_string ="[Fedora]\nurl:http://localhost:8080/fedora\nusername: fedoraAdmin\npassword: islandora\n[Solr]\nurl:http://localhost:8080/solr\n[Drupal]\nurl:http://localhost/drupal\n[logging]\ndirectory:./\n[miscellaneous]\ningest_name:name_of_ingest"
        output_file_handle = open(os.path.join(os.getcwd(), 'tmp_file_name.cfg'),'w')
        output_file_handle.write(configuration_string)
        output_file_handle.close()
        #create test object
        self.Islandora_config = Islandora_configuration(os.path.join(os.getcwd(), 'tmp_file_name.cfg'))
    
    @classmethod
    def tearDown(self):        
        os.remove(os.path.join(os.getcwd(), 'tmp_file_name.cfg'))
        
if __name__ == '__main__':
    unittest.main()