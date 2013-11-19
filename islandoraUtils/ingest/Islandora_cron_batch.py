'''
Created on 2012-03-16

@author: William Panting

@todo: in desperation a function like this could be called.
    def diff_datastream_and_source(self,
                                   Fedora_PID,
                                   datastream_ID,
                                   source):
        pass
    this kind of config:
        has_source_datastream_relationship_namespace:a_sane_rdf_namespace
        has_source_datastream_relationship_namespace_alias:something cute
        has_source_datastream_relationship_name:a_sane_rdf_name
    
'''

import time, os, datetime

from islandoraUtils.fedoraLib import get_all_subjects_of_relationship

class Islandora_cron_batch(object):
    '''
    This class is meant to hold some helper code for handling 
    cron managed time sync something to Fedora ingests
    checking if things are created or 'new' is not supported 
    because it is not cross-platform
    '''
    @newrelic.agent.function_trace()
    def __init__(self,
                 Fedora_client,
                 Islandora_configuration_object = None,
                 when_last_ran = 0,
                 time_math_margin = 0):
        '''
        Constructor!!!
        
        @param Islandora_configuration_object:
            Let the object figure out it's own state.
        
        @param when_last_ran: 
            This will override what the object can read from a configuration object
            assume all files must be modified if niether param is set (since the down of linux)
        '''
        if Islandora_configuration_object:
            self._Islandora_configuration_object = Islandora_configuration_object
            configuration = Islandora_configuration_object.configuration_dictionary
            if 'cron' in configuration:
                if 'when_last_ran' in configuration['cron']:
                    # If when_last_ran is None it has never been ran before.
                    if not configuration['cron']['when_last_ran'] == 'None':
                        self._when_last_ran = float(configuration['cron']['when_last_ran'])
                if 'time_math_margin' in configuration['cron']:
                    # If time_math_margin is None don't set it.
                    if not configuration['cron']['time_math_margin'] == 'None':
                        self._time_math_margin = float(configuration['cron']['time_math_margin'])
        
        self._when_last_ran = getattr(self, '_when_last_ran', when_last_ran)
        self._time_math_margin = getattr(self, '_time_math_margin', time_math_margin)
        
        self._write_last_cron()
        
        self._Fedora_client = Fedora_client
        
        self._sources_to_PIDs_cache = []
        self._sources_to_PIDs_cache_limit = configuration['cron']['cache_limit']
    @newrelic.agent.function_trace()
    @property
    def when_last_ran(self):
        '''
        Timestamp of the begining of the last ingest.
        '''
        return self._when_last_ran
    @newrelic.agent.function_trace()
    @property
    def UTC_when_last_ran(self):
        '''
        UTC string of the begining of the last ingest.
        '''
        return datetime.datetime.utcfromtimestamp(self._when_last_ran)
    
    @newrelic.agent.function_trace()
    def _write_last_cron(self):
        '''
        This function will write to the configuration the timestamp associated with this instance of the cron batch
        '''
        self._Islandora_configuration_object.save_configuration_variable('cron', 'when_last_ran', str(time.time()))
    @newrelic.agent.function_trace()
    def does_file_require_action(self,
                                 file_path):
        '''
        This method will figure out if the file needs to be operated on.
        
        @param file_path:
            the path to the file that must be evaluated for cron work
        
        @return boolean:
            Returns true if the file has been modified since the last cron,
            Returns false if the file no longer exists
        '''
        #get timestamp
        try: 
            timestamp = os.path.getmtime(file_path)
        except OSError:
            return False
        #call to internal timestamp math func
        return self.does_timestamp_require_action(timestamp)
    @newrelic.agent.function_trace()
    def find_files_requiring_action(self,
                                    list_of_file_paths):
        '''
        This method returns the files that have been changed since the last time a cron was ran.
        
        @param list_of_file_paths:
            A list of file paths to filter for cron work
        
        @return files_requiring_action:
            The list of files requiring cron work
        '''
        files_requiring_action = []
        for file_path in list_of_file_paths:
            if self.does_file_require_action(file_path):
                files_requiring_action.append(file_path)
        return files_requiring_action
    @newrelic.agent.function_trace()
    def does_timestamp_require_action(self,
                                      timestamp):
        '''
        is_timestamp_post_last_cron
        
        @param timestamp: timestamp to evaluate
        
        @return boolean: timestamp >= self._when_last_ran
        '''
        
        return timestamp >= self._when_last_ran - self._time_math_margin
    @newrelic.agent.function_trace()
    def get_PIDs_for_sources(self,
                             list_of_sources):
        '''
        This function will ask Fedora's resource index for the PIDs associated
        with the listed sources.  It will iterate over the given list asking
        once for each item.  It will ask based on the relationship in the configuration.
        
        @param list list_of_sources:
            The list of items to get the sources for.
        
        @return dictionary:
            sources_and_PIDs[source] = [Fedora_PIDs]
        '''
        # Populate sources_and_PIDs to default to None if there is no match.
        sources_and_PIDs = dict()
        for source in list_of_sources:
            sources_and_PIDs[source] = [None]
            
        config = self._Islandora_configuration_object.configuration_dictionary
        
        source_relationship_namespace = config['relationships']['has_source_identifier_relationship_namespace']
        source_relationship_name = config['relationships']['has_source_identifier_relationship_name']
        
        for source in list_of_sources:
            # Check the cache before running the query.
            results = self.check_cache_for_source(source)
            if not results:
                results = get_all_subjects_of_relationship(self._Fedora_client,
                                                           source_relationship_namespace,
                                                           source_relationship_name,
                                                           source)
                # Cache results.
                self.cache_source_mapping(source, results)
            
            for result in results:
                # Add to result set.
                if sources_and_PIDs[source][0]:
                    sources_and_PIDs[source].append(result)
                else:
                    sources_and_PIDs[source] = [result]
                    
        return sources_and_PIDs
    @newrelic.agent.function_trace()
    def replace_relationships(self, rels_object, predicate, objects):
        '''
        When writing a cron_syncing_ingest, it may be necessary to replace existing triple store
        relationships with updates.  This function will do that. It will not 
        run update on the rels_object.
        
        @todo: Get performance gain by diffing before updating.
        
        @param object rels_object:
            A fedora_relationships.rels_object to operate on.
        @param mixed predicate:
            Something acceptable by a fedora_relationsips.rels_object as a predicate.
        @param list objects:
            Something acceptable by a fedora_relationsips.rels_object as an object.
        '''
        
        # Remove predicate relationship if they exists.
        if rels_object.getRelationships(predicate):
            rels_object.purgeRelationships(predicate)
            
        # Populate predicate relationships.
        for RDF_object in objects:
            
            if isinstance(RDF_object, str):
                unicode(RDF_object)
                
            rels_object.addRelationship(predicate, RDF_object)
        
        return
    @newrelic.agent.function_trace()
    def check_cache_for_source(self, source):
        '''
        This function is for querying the cache of source to PID mappings
        
        @param string source:
            The identity of the source of the object(s).
        
        @return list:
            Fedora_PIDs The list of pids associated with the source.
        '''
        for cached_source, Fedora_PIDs in self._sources_to_PIDs_cache:
            if cached_source == source:
                return Fedora_PIDs
        return
    @newrelic.agent.function_trace()
    def cache_source_mapping(self, source, Fedora_PIDs):
        '''
        This function will store any result retrieved through
        get_PIDs_for_sources up to the limit emposed by
        self._sources_to_PIDs_cache_limit
        
        @param string source:
            The string representing the source of the object(s).
        @param list Fedora_PIDs:
            The list of PIDs associated with the source.
        '''
        
        self._sources_to_PIDs_cache.append((source, Fedora_PIDs))
        
        if len(self._sources_to_PIDs_cache) == self._sources_to_PIDs_cache_limit:
            self._sources_to_PIDs_cache.pop(0)
            