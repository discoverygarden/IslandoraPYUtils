'''
Created on 2012-03-16

@author: William Panting
@TODO: test

'''
import logging.handlers, time, os

class Islandora_logger(object):
    '''
    classdocs
    @param log_level:
        Can overwrite the log_level from the configuration file
    @param logger_name:
        Can overwrite the logger(config file) to use, defaults to root because fcrepo uses the root logger
    @param Islandora_configuration_object:
        The configuration object to base construction of the logger on
    '''
    def __init__(self,
                 Islandora_configuration_object,
                 log_level = None,
                 logger_name = 'root',
                 multiprocess_id = None):
        
        '''
        Constructor
        @param Islandora_configuration: The object needed to get the information necessary for logging
        @param multiprocess_id
            A string representing the ID of the current process.  None if this
            is the main thread.
        '''
        
        configuration = Islandora_configuration_object.configuration_dictionary
        if multiprocess_id is not None:
            self._log_file = os.path.join(configuration['logging']['directory'],
                                          multiprocess_id,
                                          configuration['miscellaneous']['ingest_name'] + '_' + time.strftime('%y_%m_%d') + '.log')
        else:
            self._log_file = os.path.join(configuration['logging']['directory'],
                                          configuration['miscellaneous']['ingest_name'] + '_' + time.strftime('%y_%m_%d') + '.log')
        
        #create the log file if it does not exist
        if not os.path.exists(configuration['logging']['directory']):
            os.mkdir(configuration['logging']['directory'])
        if not os.path.exists(self._log_file):
            log_file_handle = open(self._log_file, 'w')
            log_file_handle.close()
        
        # Set loging level to parameter, configured value, whatever it already is or info respectivly.
        if log_level:
            pass
        elif 'level' in configuration['logging']:
            log_level = int(configuration['logging']['level'])
        # Set to DEBUG if root because of fcrepo, needs to be something by default
        elif logger_name == 'root':
            log_level = logging.DEBUG
        elif not logger_name:
            log_level = logging.INFO
        
        #set logger name
        if logger_name:
            self._logger_name = logger_name
        else:
            if 'logger_name' in configuration['logging']:
                self._logger_name = configuration['logging']['logger_name']
            elif 'ingest_name' in configuration['miscellaneous']:
                self._logger_name = configuration['miscellaneous']['ingest_name']
        
        #get logger
        if self._logger_name == 'root':
            self._logger = logging.getLogger()
        else:
            self._logger = logging.getLogger(self._logger_name)
        
        #configure logger
        if log_level is not None:
            self._logger.setLevel(log_level)
        
        handler = logging.handlers.TimedRotatingFileHandler(self._log_file,'midnight',1)
        formatter = logging.Formatter('%(levelname)s - %(asctime)s - %(name)s - %(message)s')
        handler.setFormatter(formatter)
        handler.suffix = "%Y-%m-%d"
        self._logger.addHandler(handler)
        
        self._logger.info('Starting logging session.')
        
    @property
    def logger(self):
        '''
        Returns the logger that this object creates
        '''
        return self._logger
    
    @property
    def logger_name(self):
        '''
        Returns the name of the logger that this object creates
        '''
        return self._logger_name