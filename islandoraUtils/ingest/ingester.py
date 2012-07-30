'''
Created on 2012-03-19

@author: William Panting
@TODO: accept overrides for all objects used in constructor
'''
import os, json, sys

from fcrepo.connection import Connection, FedoraConnectionException
from fcrepo.client import FedoraClient

from copy import copy

from islandoraUtils.ingest.Islandora_configuration import Islandora_configuration
from islandoraUtils.ingest.Islandora_logger import Islandora_logger
from islandoraUtils.ingest.Islandora_cron_batch import Islandora_cron_batch
from islandoraUtils.ingest.Islandora_alerter import Islandora_alerter
from islandoraUtils.metadata import fedora_relationships
from islandoraUtils.misc import get_mime_type_from_path, path_to_datastream_ID, path_to_label, convert_members_to_unicode

class ingester(object):
    '''
    This is the kingpin.  This object should handle creating all the other basic ingest helpers.
    @TODO: add a function for taking in multiple objects as a list of dictionaries
    @todo: implement (this will mean a user will not need to know the content_model for a collection, or the pid of top,
        also it will have a default TN
            both of wich could come from the config file)
                def ingest_collection_object(ingester, parent_pid=None):
    
                    This funciton will ingest a collection object
                    into the Fedora repository
                    
                    @todo: incorporate this function into Utils? ingester.configuration['miscellaneous']['islandora_top_collection']
                        when it has been update this scripta(ten_million) and remove the function
                    
                    @param parent_pid:
                        The collection that the new object should go into
                    @param ingester:
                        The IslandoraPYUtils ingester object to use.
                        
                    @return: 
                        Fedora_PID the PID of the new object created in Fedora
                    
                    Fedora_PID = ingester.ingest_object(archival_datastream = ingester.configuration['ten_million']['path_to_thumbnail'],
                                                        collections = [parent_pid],
                                                        content_models = ['islandora:collectionCModel'])
                    return Fedora_PID
                    
                    
def recursivly_ingest_mime_type_in_directory (self, directory, mime_type, limit = None):
    '''


    def __init__(self,
                 configuration_file_path,
                 is_a_cron = False,
                 default_Fedora_namespace = None,
                 Islandora_configuration_object = None,
                 Islandora_logger_object = None,
                 Islandora_alerter_object = None,
                 Islandora_cron_batch_object = None):
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
        
            
        #Fedora connection through fcrepo, should not be done before custom logger because the first settings on root logger are immutable
        self._fcrepo_connection = Connection(self._configuration['Fedora']['url'],
                        username=self._configuration['Fedora']['username'],
                         password=self._configuration['Fedora']['password'])
        try:
            self._Fedora_client = FedoraClient(self._fcrepo_connection)
        except FedoraConnectionException:
            self._logger.error('Error connecting to Fedora')
        
        self._is_a_cron = False
        if is_a_cron:
            self._is_a_cron = True
            if not Islandora_cron_batch_object:
                self._cron_batch = Islandora_cron_batch(self._Fedora_client, my_Islandora_configuration)
            else:
                self._cron_batch = Islandora_cron_batch_object
                
        if not default_Fedora_namespace:#unicode because of fcrepo
            self._default_Fedora_namespace = unicode(self._configuration['miscellaneous']['default_fedora_pid_namespace'])#no caps in configParser
        else:
            self._default_Fedora_namespace = unicode(default_Fedora_namespace)
            
        
        #pyrelationships 
        self._Fedora_model_namespace = fedora_relationships.rels_namespace('fedora-model','info:fedora/fedora-system:def/model#')
        
        #create temporary directory if it does not exist and one is in the configuration
        if 'temporary_directory' in self._configuration['miscellaneous']:
            if not os.path.exists(self._configuration['miscellaneous']['temporary_directory']):
                os.makedirs(self._configuration['miscellaneous']['temporary_directory'])
        
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
    
    @property
    def Fedora_model_namespace(self):
        '''
        returns the namespace object for ('fedora-model','info:fedora/fedora-system:def/model#')
        '''
        return self._Fedora_model_namespace
    
    @property
    def Fedora_client(self):
        '''
        returns the fcrepo client object
        '''
        return self._Fedora_client
    
    @property
    def default_Fedora_namespace(self):
        '''
        returns the default namespace to ingest fedora objects into
        '''
        return self._default_Fedora_namespace
    
    def ingest_object(self,
                      PID = None,
                      object_label = None,
                      archival_datastream = None,
                      metadata_datastream = None,
                      datastreams = None,
                      collections = None,
                      content_models = None,
                      sources = None):
        '''
        This function will ingest an object with a single metadata and archival datastream with a specified set of relationships
        it will use our best practices for logging and assume the use of microservices for derivatives and their RELS-INT management
        it will overwrite a pre-existing object if one exists
        this function can be extended later, the initial write is for an atomistic content model with 'sensible' defaults
        mimetypes are detected using islandoraUtils for compatibility with Islandora
        currently only control groups x and m are supported
        
        @TODO: look at taking in a relationship object
        
        @param PID: 
            The PID of the object to create or update. If non is supplied then getNextPID is used
        @param archival_datastream: 
            an image, audio, whatever file path will be a managed datastream
            [{'path':'./objectstuff'}]
        @param metadata_file_path: 
            will be inline xml
        @param list collection: 
            the PIDs of the collection so RELS-EXT can be created
        @param list content_model:
            The PIDs of the content_model so the RELS-EXT can be created
        @param list sources:
            Only relevant if this is a cron ingest, will default to 
            [archival_datastream's path].
        
        @return:
            The PID of the object created or updated.
        '''
        
        # Set as empty lists (not in default args because of python would store state from call to call).
        if not datastreams:
            datastreams = []
        if not collections:
            collections = []
        if not content_models:
            content_models = []
            
        #if datastream label not supplied build it based on archival ds path
        if not object_label:
            if isinstance(archival_datastream, str):
                object_label = archival_datastream
            elif isinstance(archival_datastream, dict):
                object_label = archival_datastream['filepath']
            else:
                object_label = ''
            #a utf8 unicode string may be necessary to pass through urlencode
            object_label = path_to_label(object_label)
        
        #set the source
        if self._is_a_cron:
            if not sources:
                if isinstance(archival_datastream, str):
                    sources = [archival_datastream]
                elif isinstance(archival_datastream, dict):
                    sources = [archival_datastream['filepath']]
                else:
                    sources = []
                
        
        #normalize parameters to a list of dictionaries of what datastreams to ingest
        if isinstance(archival_datastream, str):
            archival_datastream_dict = {'filepath':archival_datastream,
                                        'label':path_to_label(archival_datastream),
                                        'mimetype':get_mime_type_from_path(archival_datastream),
                                        'ID':path_to_datastream_ID(archival_datastream),
                                        'control_group':'M'}
            archival_datastream = archival_datastream_dict
            
        if isinstance(metadata_datastream, str):
            metadata_datastream_dict = {'filepath':metadata_datastream,
                                        'label':path_to_label(metadata_datastream),
                                        'mimetype':get_mime_type_from_path(metadata_datastream),
                                        'ID':path_to_datastream_ID(metadata_datastream),
                                        'control_group':'X'}
            metadata_datastream = metadata_datastream_dict
        
        #add the metadata and archival datastreams to those to be ingested
        if metadata_datastream:
            datastreams.append(metadata_datastream)
        if archival_datastream:
            datastreams.append(archival_datastream)
        
        #create the object
        Fedora_object = self.get_Fedora_object(PID, object_label)
        PID = Fedora_object.pid
        
        #write datastreams to the object
        for datastream in datastreams:
            self.ingest_datastream(Fedora_object, datastream)
            
        #write relationships to the object
        if collections or content_models or self._is_a_cron:
            
            # If it is a cron we need another namespace.
            if self._is_a_cron and sources:
                source_relationship_namespace = self.configuration['relationships']['has_source_identifier_relationship_namespace']
                source_relationship_namespace_alias = self.configuration['relationships']['has_source_identifier_relationship_namespace_alias']
                source_name_space_object = fedora_relationships.rels_namespace(source_relationship_namespace_alias, source_relationship_namespace)
                
                objRelsExt = fedora_relationships.rels_ext(Fedora_object, [self._Fedora_model_namespace, source_name_space_object])
            else:
                objRelsExt = fedora_relationships.rels_ext(Fedora_object, self._Fedora_model_namespace)
            
            # Collection relationships.
            self.cron_batch.replace_relationships(objRelsExt,
                                                  'isMemberOfCollection',
                                                  collections)
            # Content model relationships.
            self.cron_batch.replace_relationships(objRelsExt,
                                                  fedora_relationships.rels_predicate('fedora-model','hasModel'),
                                                  content_models)
            
            # Source relationships.
            if self._is_a_cron and sources:
                source_relationship_name = self.configuration['relationships']['has_source_identifier_relationship_name']
                source_predicate = fedora_relationships.rels_predicate(source_relationship_namespace_alias, source_relationship_name)
                objectified_sources = []
                for source in sources:
                    objectified_sources.append(fedora_relationships.rels_object(source,
                                                                                fedora_relationships.rels_object.LITERAL))
                    
                self.cron_batch.replace_relationships(objRelsExt,
                                                      source_predicate,
                                                      objectified_sources)
                
            objRelsExt.update()
        return(PID)
    
    def ingest_default_thumbnail (self,
                                  Fedora_object):
        '''
        This function will ingest a default thumbnail into Fedora
        
        @param Fedora_object:
            The fcrepo object to add the thumbnail to.
        '''
        
        self.ingest_datastream (Fedora_object,
                                datastream = os.path.join(os.path.dirname(__file__),
                                                          '../__resources/images/icons/Crystal_Clear_action_filenew.png'),
                                datastream_ID = 'TN')
        
        return
    
    def ingest_datastream (self,
                           Fedora_object,
                           datastream,
                           datastream_ID = None):
        '''
        This function will wrap creating/modifying a datastream in Fedora
        It's some dynamic kinda crazy:
        @param mixed datstream:
            string of source
            dict defining datastream
        @param string datastream_ID:
            ignored if datastream is a dict.
        '''
        PID = Fedora_object.pid
        if not isinstance(datastream, dict):
            if not datastream_ID:
                datastream_ID = path_to_datastream_ID(datastream)
            datastream_dict = {'filepath':datastream,
                                        'label':path_to_label(datastream),
                                        'mimetype':get_mime_type_from_path(datastream),
                                        'ID':datastream_ID,
                                        'control_group':'M'}
            datastream = datastream_dict
            
        if datastream['ID'] not in Fedora_object:
            try:
                if datastream['control_group'] == 'X':
                    datastream_file_handle = open(datastream['filepath'])
                    datastream_contents = datastream_file_handle.read()
                    Fedora_object.addDataStream(unicode(datastream['ID']), unicode(datastream_contents), label = unicode(datastream['label']),
                                              mimeType = unicode(datastream['mimetype']), controlGroup = u'X',
                                              logMessage = unicode('Added ' + datastream['ID'] + ' datastream to:' + PID +' via IslandoraPYUtils'))
                elif datastream['control_group'] == 'M':#do a dummy create (an artifact of fcrepo)
                    datastream_file_handle = open(datastream['filepath'], 'rb')
                    Fedora_object.addDataStream(unicode(datastream['ID']), u'I am an artifact, ignore me.', label = unicode(datastream['label']),
                                              mimeType = unicode(datastream['mimetype']), controlGroup = u'M',
                                              logMessage = unicode('Added ' + datastream['ID'] + ' datastream to:' + PID +' via IslandoraPYUtils'))
                    
                    Fedora_object_datastream = Fedora_object[datastream['ID']]
                    Fedora_object_datastream.setContent(datastream_file_handle)
                    
                self._logger.info('Added ' + datastream['ID'] + ' datastream to: ' + PID + ' from: ' + datastream['filepath'])
                
            except (FedoraConnectionException, IOError):
                self._logger.error('Error in adding ' + datastream['ID'] + ' datastream to:' + PID + ' from: ' + datastream['filepath'])
        # Set the datastream if it is not new.
        else:
            try:
                if datastream['control_group'] == 'X':
                    datastream_file_handle = open(datastream['filepath'])
                    Fedora_object_datastream = Fedora_object[datastream['ID']]
                    datastream_contents = datastream_file_handle.read()
                    Fedora_object_datastream.setContent(datastream_contents)
                elif datastream['control_group'] == 'M':
                    datastream_file_handle = open(datastream['filepath'], 'rb')
                    Fedora_object_datastream = Fedora_object[datastream['ID']]
                    Fedora_object_datastream.setContent(datastream_file_handle)
                self._logger.info('Updated ' + datastream['ID'] + ' datastream in:' + PID + ' from: ' + datastream['filepath'])
            except (FedoraConnectionException, IOError):
                self._logger.error('Error in updating ' + datastream['ID'] + ' datastream in:' + PID + ' from: ' + datastream['filepath'])
        datastream_file_handle.close()
        
        return
    
    def get_Fedora_object(self, PID = None, object_label = None):
        '''
        This function will get/create a Fedora object
        @param string PID:
            The Fedora PID of the object to create
        @return
            If PID is supplied will return the object from Fedora
            If PID is not supplied will return a new object created in Fedora
        @todo there looks like there is too fedora object declarations, refactor out the first one
        '''
        Fedora_object = None
        if object_label != None:
            #encode in unicode because that's what fcrepo needs
            object_label = unicode(object_label)
            
            
        #set up the Fedora object PID
        if not PID:
            #PID is a list
            PID = self._Fedora_client.getNextPID(self._default_Fedora_namespace)
            Fedora_object = self._Fedora_client.createObject(PID, label = object_label)
            
        #creating vs updating
        #if not Fedora_object:
        else:
            try:
                Fedora_object = self._Fedora_client.getObject(PID)
            except FedoraConnectionException, object_fetch_exception:
                if object_fetch_exception.httpcode in [404]:
                    self._logger.info(PID + ' missing, creating object.\n')
                    Fedora_object = self._Fedora_client.createObject(PID, label = object_label)
                else:
                    self._logger.error(PID + ' was not created successfully.')
        return Fedora_object
    
    def filter_files_for_ingest(self,
                                list_of_paths,
                                filter_to_documents = False,
                                filter_to_images = False,
                                extensions_to_filter_out = None,
                                extensions_to_filter_to = None,
                                filter_by_time = None):
        '''
        This function will filter out undesirable files
        from a list of files for ingest.  It relies on a 
        list of illegal file names and file extensions in the 
        constants module.
        It does not alter the original list object.
        
        @param list list_of_paths:
            The paths to remove illegal files from. Members are expected to be unicode
        @param bool filter_to_documents:
            Use the config file to filter to document files.
        @param filter_to_images:
            Use the config file to filter to image files.
        @param extensions_to_filter_out:
            Used to filter out files based on extensions.
        @param extensions_to_filter_to:
            Will require all files to have one of the extensions passed in.
        @param boolean filter_by_time:
            Will default to true if this is a cron batch ingester.
        
        @return list filtered_list_of_paths:
            The paths after illegal files have been removed.
        '''
        
        # Set filter by time if this is a cron and not overridden in parameters.
        if filter_by_time == None:
            filter_by_time = self._is_a_cron
            
        #to handle unicode file names we convert all input strings to unicode
        if extensions_to_filter_out:
            extensions_to_filter_out = convert_members_to_unicode(extensions_to_filter_out)
        if extensions_to_filter_to:
            extensions_to_filter_to = convert_members_to_unicode(extensions_to_filter_to)
        
        filtered_list_of_paths = copy(list_of_paths)
        
        # Kill by Time
        if filter_by_time:
            filtered_list_of_paths = self._cron_batch.find_files_requiring_action(list_of_paths)
        
        # Kill by file name issues.
        for file_path in list_of_paths:
            file_name = os.path.basename(file_path)
            #lower case extension
            file_extension = os.path.splitext(file_path)[1].lower()
            
            if extensions_to_filter_to:
                if not file_extension in extensions_to_filter_to:
                    if file_path in filtered_list_of_paths:
                        filtered_list_of_paths.remove(file_path)
            
            if file_name in convert_members_to_unicode(json.loads(self._configuration['filtering']['prohibited_file_names'])):
                if file_path in filtered_list_of_paths:
                    filtered_list_of_paths.remove(file_path)
            if file_extension in convert_members_to_unicode(json.loads(self._configuration['filtering']['prohibited_file_extensions'])):
                if file_path in filtered_list_of_paths:
                    filtered_list_of_paths.remove(file_path)
            if extensions_to_filter_out:
                if file_extension in extensions_to_filter_out:
                    if file_path in filtered_list_of_paths:
                        filtered_list_of_paths.remove(file_path)
                
            if file_name.startswith(tuple(convert_members_to_unicode(json.loads(self._configuration['filtering']['prohibited_file_prefixes'])))):
                if file_path in filtered_list_of_paths:
                    filtered_list_of_paths.remove(file_path)
                
            if filter_to_documents:
                if not file_extension in convert_members_to_unicode(json.loads(self._configuration['filtering']['allowed_document_extensions'])):
                    if file_path in filtered_list_of_paths:
                        filtered_list_of_paths.remove(file_path)
                        
            if filter_to_images:
                if not file_extension in convert_members_to_unicode(json.loads(self._configuration['filtering']['allowed_image_extensions'])):
                    if file_path in filtered_list_of_paths:
                        filtered_list_of_paths.remove(file_path)
            
        # Filter by timestamp. This is expensive so I want it last
        if self._is_a_cron:
            filtered_list_of_paths = self.cron_batch.find_files_requiring_action(filtered_list_of_paths)
                
        return filtered_list_of_paths

    def recursivly_get_all_files_for_ingest(self,
                                            directory_to_walk,
                                            filter_to_documents = False,
                                            filter_to_images = False,
                                            extensions_to_filter_out = None,
                                            extensions_to_filter_to = None,
                                            filter_by_time = None,
                                            directories_to_ignore = []):
        '''
        This function will get all the files in a directory and all its'
        non-symlinked directories that are suitable for ingest.
        
        @param string directory_to_walk:
            The directory to grab files and filter from.
        @param bool filter_to_documents:
            Passed on to filter function.
        @param filter_to_images:
            Passed on to filter function.
        @param extensions_to_filter_out:
            Passed on to filter function.
        @param extensions_to_filter_to:
            Passed on to filter function.
        @param boolean filter_by_time:
            Will default to true if this is a cron batch ingester.
        
        @return list list_of_paths_to_ingest:
            The completed list of files to ingest, they will be unicode strings.
        '''
        
        #using unicode to handle if the file system is unicode
        list_of_paths_to_ingest = list()
        for path, dirs, files in os.walk(unicode(directory_to_walk)):
            # Ignore a directory and sub dirs if specified in directories_to_ignore. 
            if directories_to_ignore:
                for directory in dirs:
                    if os.path.join(path, directory) in directories_to_ignore:
                        dirs.remove(directory)
                            
            for file_name in files:
                file_path = os.path.join(path, file_name)
                list_of_paths_to_ingest.append(file_path)
                
        list_of_paths_to_ingest = self.filter_files_for_ingest(list_of_paths_to_ingest,
                                                               filter_to_documents,
                                                               filter_to_images,
                                                               extensions_to_filter_out,
                                                               extensions_to_filter_to,
                                                               filter_by_time)
        
        return list_of_paths_to_ingest

    def remove_temporary_directory(self):
        '''
        This function will remove the temporary directory.
        '''
        
        # Remove temporary directory if it exists and one is in the configuration.
        if 'temporary_directory' in self._configuration['miscellaneous']:
            if os.path.exists(self._configuration['miscellaneous']['temporary_directory']):
                os.remove(self._configuration['miscellaneous']['temporary_directory'])
                
        return