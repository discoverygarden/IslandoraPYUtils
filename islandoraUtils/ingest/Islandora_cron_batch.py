'''
Created on 2012-03-16

@author: William Panting
@TODO: tests
'''
import time
import os

class Islandora_cron_batch(object):
    '''
    This class is meant to hold some helper code for handling 
    cron managed time sync something to Fedora ingests
    checking if things are created or 'new' is not supported because it is not cross-platform
    '''

    def __init__(self,
                 Islandora_configuration_object = None,
                 when_last_ran = 0):
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
                    self._when_last_ran = float(configuration['cron']['when_last_ran'])#needs to be a number for comparisons
        self._when_last_ran = getattr(self, '_when_last_ran', when_last_ran)
        self._write_last_cron()
            
    @property
    def when_last_ran(self):
        '''
        The dictionary version of the ingest's configuration.
        '''
        return self._when_last_ran
           
    def _write_last_cron(self):
        '''
        This function will write to the configuration the timestamp associated with this instance of the cron batch
        '''
        if self._Islandora_configuration_object:
            islandora_configuration_parser = self._Islandora_configuration_object.configuration_parser
            if not islandora_configuration_parser.has_section('cron'):
                islandora_configuration_parser.add_section('cron')
            islandora_configuration_parser.set('cron', 'when_last_ran', str(time.time()))
            configuration_file_handle = self._Islandora_configuration_object.configuration_file_write_handle
            islandora_configuration_parser.write(configuration_file_handle)
            configuration_file_handle.close()
                    
    def does_file_require_action(self,
                                 file_path):
        '''
        This method will figure out if the file needs to be operated on.
        
        @param file_path: the path to the file that must be evaluated for cron work
        
        @return boolean: Returns true if the file has been modified since the last cron
        '''
        #get timestamp
        timestamp = os.path.getmtime(file_path)
        #call to internal timestamp math func
        return self.does_timestamp_require_action(timestamp)
    
    def find_files_requiring_action(self,
                                    list_of_file_paths):
        '''
        This method returns the files that have been changed since the last time a cron was ran
        
        @param list_of_file_paths: a list of file paths to filter for cron work
        
        @return files_requiring_action: the list of files requiring cron work
        '''
        files_requiring_action = []
        for file_path in list_of_file_paths:
            if self.does_file_require_action(file_path):
                files_requiring_action.append(file_path)
        return files_requiring_action
    
    def does_timestamp_require_action(self,
                                      timestamp):
        '''
        is_timestamp_post_last_cron
        
        @param timestamp: timestamp to evaluate
        
        @return boolean: timestamp >= self._when_last_ran
        '''
        return timestamp >= self._when_last_ran
    
    def get_pids_for_sources(self,
                             list_of_sources):
        pass
    
    def diff_datastream_and_source(self,
                                   Fedora_PID,
                                   datastream_ID,
                                   source):
    