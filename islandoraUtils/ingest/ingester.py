'''
Created on 2012-03-19

@author: William Panting
@TODO: properties configuration and logger, also accept overrides for all objects used in constructor
@TODO: look into default PID namespace
@TODO: a function for creating/deleting the tmp dir
'''
from fcrepo.connection import Connection, FedoraConnectionException
from fcrepo.client import FedoraClient

from islandoraUtils.ingest.Islandora_configuration import Islandora_configuration
from islandoraUtils.ingest.Islandora_logger import Islandora_logger
from islandoraUtils.ingest.Islandora_cron_batch import Islandora_cron_batch
from islandoraUtils.ingest.Islandora_alerter import Islandora_alerter
from islandoraUtils.metadata import fedora_relationships

class ingester(object):
    '''
    This is the kingpin.  This object should handle creating all the other basic ingest helpers.
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
        
        self._configuration = my_Islandora_configuration.configuration_dictionary
        
        self._logger = my_Islandora_logger.logger
        
        #set the class properties
        if not Islandora_alerter_object:
            self._alerter = Islandora_alerter(my_Islandora_configuration, self._logger)
        else:
            self._alerter = Islandora_alerter_object
        
        if is_a_cron:
            if not Islandora_cron_batch_object:
                self._cron_batch = Islandora_cron_batch(my_Islandora_configuration)
            else:
                self._cron_batch = Islandora_cron_batch_object
            
        #Fedora connection through fcrepo
        self._fcrepo_connection = Connection(self._configuration['Fedora']['url'],
                        username=self._configuration['Fedora']['username'],
                         password=self._configuration['Fedora']['password'])
        try:
            self._Fedora_client = FedoraClient(self._fcrepo_connection)
        except FedoraConnectionException:
            self._logger.error('Error connecting to Fedora')

    @property
    def alerter(self):
        '''
        Returns the alerter that this object creates
        '''
        return self._alerter           

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
        returns the batch job.
        '''
        return self._cron_batch
    
    def ingest_object(self, PID=None, object_label=None, archival_datastream_path=None, metadata_file_path=None, collection=None, content_model=None):
        '''
        This function will ingest an object with a single metadata and archival datastream with a specified set of relationships
        it will use our best practices for logging and assume the use of microservices for derivatives and their RELS-INT management
        it will overwrite a pre-existing object if one exists
        @TODO: look at taking in a relationship object
        @param PID: The PID of the object to create or update. If non is supplied then getNextPID is used
        @param archival_datastream: an image, audio, whatever file path will be a managed datastream
        @param metadata_file_path: will be inline xml
        @param collection: the PID of the collection so RELS-EXT can be created
        @param content_model: The PID of the content_model so the RELS-EXT can be created
        
        @return PID: The PID of the object created or updated.
        '''
        '''
        fedora_model_namespace = fedora_relationships.rels_namespace('fedora-model','info:fedora/fedora-system:def/model#')
        Fedroa_object = self._Fedora_client.createObject(PID, label = object_label)
        
        #don't use add datastreams using  add_datastream from islandoraUtils.fedoraLib.py  it hurts fcrepo caching re J Green     
        
        #add relationships
                objRelsExt = fedora_relationships.rels_ext(Fedora_object, fedora_model_namespace)
                objRelsExt.addRelationship('isMemberOf', collection)
                objRelsExt.addRelationship(fedora_relationships.rels_predicate('fedora-model','hasModel'), content_model)
                objRelsExt.update()
        '''