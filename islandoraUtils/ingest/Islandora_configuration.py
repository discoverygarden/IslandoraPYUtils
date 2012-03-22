'''
Created on 2012-03-16

@author: William Panting
@TODO: should check for exceptions and log errors for missing files/sections etc., we'll need to accept a logger
'''
import ConfigParser

class Islandora_configuration(object):
    '''
EXAMPLE:

[Fedora]
url:http://localhost:8080/fedora
username: fedoraAdmin
password: islandora
[Solr]
url:http://localhost:8080/solr
[Drupal]
url:http://localhost/drupal
[logging]
directory:./
[miscellaneous]
ingest_name:name_of_ingest

    '''
    @property
    def configuration_dictionary(self):
        '''
        The dictionary version of my configuration.
        '''
        return self._configuration_dictionary

    def __init__(self, configuration_file_path):
        '''
        Constructor
        @param configuration_file_path: the path to the configuration file 
        '''
        #get config
        self.configuration_parser = ConfigParser.SafeConfigParser()
        self.configuration_parser.read(configuration_file_path)
        self._configuration_dictionary = {}
        #loop throught he configuration file sections and dump the config to a dictionary
        self.sections = self.configuration_parser.sections()
        for section in self.sections:
            self._configuration_dictionary[section] = {}
            options = self.configuration_parser.options(section)
            for option in options:
                self._configuration_dictionary[section][option] = self.configuration_parser.get(section, option)

if __name__ == '__main__':
    pass