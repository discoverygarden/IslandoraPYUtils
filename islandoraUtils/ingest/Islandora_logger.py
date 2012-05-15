'''
Created on 2012-03-16

@author: William Panting
@TODO: test

'''
import logging, time, os

class Islandora_logger(object):
    '''
    classdocs
    @param log_level:
        Can overwrite the log_level from the configuration file
    @param logger_name:
        Can overwrite the logger(config file) to use, defaults to root because fcrepo uses the root logger
    @param Islandora_configuration_object:
        The configuration object to base construction of the logger on
        
    @TODO: make better logs: timestamps and loglevel
    @TODO: make logs rollover: 
        handler = logging.handlers.TimedRotatingFileHandler("C:\\isis_ops\\logs\\Rotate_Test",'midnight',1)
        handler.suffix = "%Y-%m-%d" # or anything else that strftime will allow
        root_logger.addHandler(handler)

    '''
    def __init__(self, Islandora_configuration_object, log_level=None, logger_name='root'):
        '''
        Constructor
        @param Islandora_configuration: The object needed to get the information necessary for logging
        '''
        #self.Islandora_configuration_object = Islandora_configuration_object
        self.configuration = Islandora_configuration_object.configuration_dictionary
        self._log_file = os.path.join(self.configuration['logging']['directory'], self.configuration['miscellaneous']['ingest_name'] + '_' + time.strftime('%y_%m_%d') + '.log')
        
        #create the log file if it does not exist
        if not os.path.exists(self.configuration['logging']['directory']):
            os.mkdir(self.configuration['logging']['directory'])
        if not os.path.exists(self._log_file):
            log_file_handle = open(self._log_file, 'w')
            log_file_handle.close()
            
        #set log level if a logger is supplied do not set the log_level if it has not already been set
        if log_level or logger_name:
            pass  
        elif 'level' in self.configuration['logging']:
            log_level = self.configuration['logging']['level']
        else:
            log_level = logging.INFO
        
        #set logger name
        if logger_name:
            self._logger_name = logger_name
        else:
            if 'logger_name' in self.configuration['logging']:
                self._logger_name = self.configuration['logging']['logger_name']
            elif 'ingest_name' in self.configuration['miscellaneous']:
                self._logger_name = self.configuration['miscellaneous']['ingest_name']
        
        #get logger
        if self._logger_name == 'root':
            self._logger = logging.getLogger()
            #logging.basicConfig(filename=logFile, level=log_level)
        else:
            self._logger = logging.getLogger(self._logger_name)
        
        #configure logger
        self._logger.setLevel(log_level)
        file_handler = logging.FileHandler(self._log_file)
        self._logger.addHandler(file_handler)
        
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