'''
Created on 2012-03-19

@author: William Panting
@TODO: properties configuration and logger, also accept overrides for all objects used in constructor
'''

from islandoraUtils.ingest.Islandora_configuration import Islandora_configuration
from islandoraUtils.ingest.Islandora_logger import Islandora_logger
from islandoraUtils.ingest.Islandora_cron_batch import Islandora_cron_batch
from islandoraUtils.ingest.Islandora_alerter import Islandora_alerter

class ingester(object):
    '''
    classdocs
    '''


    def __init__(self, configuration_file_path, is_a_cron=False, Islandora_configuration_object=None, Islandora_logger_object=None, Islandora_alerter_object=None, Islandora_cron_batch_object=None):
        '''
        Get all the objects that are likely to be used for an ingest
        @param configuration_file_path: where the configuration for the ingest can be found
        @param last_time_ran: the last time this ingest was ran (if this is set a cron_batch object is created with the information)
        '''
        
        #configuration and logger have intermediate objects
        if not Islandora_configuration_object:
            my_Islandora_configuration = Islandora_configuration(configuration_file_path)
        else:
            my_Islandora_configuration = Islandora_configuration_object
        
        if not Islandora_logger_object:
            my_Islandora_logger = Islandora_logger(my_Islandora_configuration)
        else:
            my_Islandora_logger = Islandora_logger_object
        
        #set the class properties
        if not Islandora_alerter_object:
            self._alerter = Islandora_alerter(my_Islandora_configuration)
        else:
            self._alerter = Islandora_alerter_object
        
        if is_a_cron:
            if not Islandora_cron_batch_object:
                self._cron_batch = Islandora_cron_batch(my_Islandora_configuration)
            else:
                self._cron_batch = Islandora_cron_batch_object
            
        
        self._configuration = my_Islandora_configuration.configuration_dictionary
        
        self._logger = my_Islandora_logger.logger
            

    @property
    def logger(self):
        '''
        Returns the logger that this object creates
        '''
        return self._logger
    
    @property
    def configuration(self):
        '''
        The dictionary version of the ingest's configuration.
        '''
        return self._configuration
    
    @property
    def cron_batch(self):
        '''
        The dictionary version of the ingest's configuration.
        '''
        return self._cron_batch
    
    def ingest_object(self, pid=None, archival_datastream_path=None, metadata_file_path=None, collection=None, content_model=None):
        '''
        This function will ingest an object with a single metadata and archival datastream with a specified set of relationships
        it will use our best practices for logging and assume the use of microservices for derivatives and their RELS-INT management
        it will overwrite a pre-existing object if one exists
        @TODO: look at taking in a relationship object
        @param pid: The pid of the object to create or update. If non is supplied then getNextPid is used
        @param archival_datastream:
        @param metadata_file_path:
        @param collection:
        @param content_model:
        
        @return pid: The pid of the object created or updated.
        '''