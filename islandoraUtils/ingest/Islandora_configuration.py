'''
Created on 2012-03-16

@author: William Panting
@TODO: should check for exceptions and log errors for missing important files/sections etc., 
'''
import ConfigParser
from islandoraUtils.misc import config_parser_to_dict

class Islandora_configuration(object):
    '''
EXAMPLE:

[Fedora]
url:http://localhost:8080/fedora
username: fedoraAdmin
password: some_where_over_the_rain_bow
[Solr]
url:http://localhost:8080/solr
[Drupal]
url:http://localhost/drupal
[logging]
directory:./logs
[alerts]
medium:mailx
emails:willy@domain.ca wonka@notadomian.com
[miscellaneous]
ingest_name:name_of_ingest
temporary_directory:./tmp
default_fedora_pid_namespace:islandora
islandora_top_collection:islandora:root
islandora_collection_content_model:islandora:collectionCModel
[cron]
when_last_ran:timestamp_here

    '''

    def __init__(self, configuration_file_path):
        '''
        Constructor
        
        @param configuration_file_path: the path to the configuration file
        '''
        #get config
        self._configuration_parser = ConfigParser.SafeConfigParser()
        self._configuration_parser.read(configuration_file_path)
        self._configuration_dictionary = {}
        self._configuration_file_path = configuration_file_path
        #loop through he configuration file sections and dump the config to a dictionary
        self._configuration_dictionary = config_parser_to_dict(self._configuration_parser)

    
    def save_configuration_variable(self, group, variable, value):
        '''
        This is only meant to alter variables that are already present in the configuration.
        Please start with a representative configuration.
        
        @param string group:
            The group the variable belongs to.
        @param string variable:
            The name of the variable to set.
        @param string value:
            The value to set the variable to.
        '''
        # Set cached value.
        self._configuration_dictionary[group][variable] = value
        
        # Set value in file.
        self._configuration_parser.set(group, variable, value)
        configuration_file_write_handle = self.configuration_file_write_handle
        self._configuration_parser.write(configuration_file_write_handle)
        configuration_file_write_handle.close()
        
        return
    
    @property
    def configuration_parser(self):
        '''
        This will return the configuration parser object that self is using
        '''
        return self._configuration_parser
    
    @property
    def configuration_file_write_handle(self):
        '''
        This will return a file handle pointing to the file used to set the configuration.
        '''
        file_handle = open(self._configuration_file_path, 'w')
        return file_handle
    
    @property
    def configuration_dictionary(self):
        '''
        The dictionary version of my configuration.
        '''
        return self._configuration_dictionary