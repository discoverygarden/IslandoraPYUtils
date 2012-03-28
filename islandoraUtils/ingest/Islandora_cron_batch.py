'''
Created on 2012-03-16

@author: William Panting
@TODO: tests
'''

class Islandora_cron_batch(object):
    '''
    classdocs
    '''


    def __init__(self, Islandora_configuration_object=None, last_time_ran=None):
        '''
        @param Islandora_configuration_object: let the object figure out it's own state
        @param last_time_ran: this will override what the object can read from a configuration object
        Return false if neither parameter is set
        There is no need to specify both
        '''
        
    def _write_last_cron(self):
        '''
        This function will write to the log the timestamp associated with this instance of the cron batch
        '''
        
    def does_file_require_action(self):
        '''
        '''
    
    def is_file_new(self):
        '''
        '''
        
    def is_file_modified(self):
        '''
        '''
        
    def find_files_requiring_action(self, list_of_files):
        '''
        '''
    
    def find_new_files(self, list_of_files):
        '''
        '''
        
    def find_modified_files(self, list_of_files):
        '''
        '''
        
    def find_timestamps_requiring_aciton(self, list_of_files):
        '''
        '''
        
    def does_timestamp_require_action(self):#is_timestamp_post_last_cron
        '''
        '''
    
    