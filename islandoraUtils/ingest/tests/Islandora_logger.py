'''
Created on 2012-03-16

@author: William Panting
'''
import unittest, os, logging
from islandoraUtils.ingest.Islandora_configuration import Islandora_configuration
from islandoraUtils.ingest.Islandora_logger import Islandora_logger

class TestIslandora_logger(unittest.TestCase):
    
    def test_logger(self):
        #set up expectations
        expected_result_root = logging.getLogger('root')
        
        named_configuration = self.Islandora_configuration_named.configuration_dictionary
        expected_result_named = logging.getLogger(named_configuration['logging']['logger_name'])
        
        not_named_configuration = self.Islandora_configuration_not_named.configuration_dictionary
        expected_result_not_named = logging.getLogger(not_named_configuration['miscellaneous']['ingest_name'])
        
        
        #this tests more than one thing but loggers are not very testable
        self.assertNotEqual(expected_result_root.handlers, 0)
        self.assertNotEqual(expected_result_named.handlers, 0)
        self.assertNotEqual(expected_result_not_named.handlers, 0)
        
        
    @classmethod
    def setUp(self):
        
        #make a log files in cwd
        configuration_string_root ="[Fedora]\nurl:http://localhost:8080/fedora\nusername: fedoraAdmin\npassword: islandora\n[Solr]\nurl:http://localhost:8080/solr\n[Drupal]\nurl:http://localhost/drupal\n[logging]\ndirectory:./\nlevel:INFO\nlogger_name:root\n[miscellaneous]\ningest_name:name_of_ingest"
        configuration_string_named ="[Fedora]\nurl:http://localhost:8080/fedora\nusername: fedoraAdmin\npassword: islandora\n[Solr]\nurl:http://localhost:8080/solr\n[Drupal]\nurl:http://localhost/drupal\n[logging]\ndirectory:./\nlevel:INFO\nlogger_name:named_logger\n[miscellaneous]\ningest_name:name_of_ingest"
        configuration_string_not_named ="[Fedora]\nurl:http://localhost:8080/fedora\nusername: fedoraAdmin\npassword: islandora\n[Solr]\nurl:http://localhost:8080/solr\n[Drupal]\nurl:http://localhost/drupal\n[logging]\ndirectory:./\nlevel:INFO\n[miscellaneous]\ningest_name:name_of_ingest"
        
        #write configuration files
        output_file_handle = open(os.path.join(os.getcwd(), 'tmp_file_name_root.cfg'),'w')
        output_file_handle.write(configuration_string_root)
        output_file_handle.close()
        output_file_handle = open(os.path.join(os.getcwd(), 'tmp_file_name_named.cfg'),'w')
        output_file_handle.write(configuration_string_named)
        output_file_handle.close()
        output_file_handle = open(os.path.join(os.getcwd(), 'tmp_file_name_not_named.cfg'),'w')
        output_file_handle.write(configuration_string_not_named)
        output_file_handle.close()
        
        #create test configuration objects
        self.Islandora_configuration_root = Islandora_configuration(os.path.join(os.getcwd(), 'tmp_file_name_root.cfg'))
        self.Islandora_configuration_named = Islandora_configuration(os.path.join(os.getcwd(), 'tmp_file_name_named.cfg'))
        self.Islandora_configuration_not_named = Islandora_configuration(os.path.join(os.getcwd(), 'tmp_file_name_not_named.cfg'))
        
        #using root logger
        self.Islandora_logger_root = Islandora_logger(self.Islandora_configuration_root)
        #a specified logger name
        self.Islandora_logger_named = Islandora_logger(self.Islandora_configuration_named)
        #a non-specified logger 
        self.Islandora_logger_not_named = Islandora_logger(self.Islandora_configuration_not_named)
    
    @classmethod
    def tearDown(self):
        os.remove(os.path.join(os.getcwd(), 'tmp_file_name_root.cfg'))
        os.remove(os.path.join(os.getcwd(), 'tmp_file_name_named.cfg'))
        os.remove(os.path.join(os.getcwd(), 'tmp_file_name_not_named.cfg'))
        
if __name__ == '__main__':
    unittest.main()