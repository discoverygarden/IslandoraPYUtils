'''
Created on 2012-03-16

@author: William Panting
@TODO: tests
@TODO: create an interface(abc module) with send_message(self, subject, message), _recievers(add, remove, clear, set)
@TODO: look into more generic alerters ie. one that understands and can run parameterized bash commands
'''
import traceback
from islandoraUtils.mailer import mailer 

class Islandora_alerter(object):
    '''
    This class wraps the known alerters so they can be called based on a configuration file
    '''
    
    @newrelic.agent.function_trace()
    def __init__(self, Islandora_configuration_object, logger):
        '''
            Constructor
            @param Islandora_configuration_object: the configuration to base this email alerter on
            @param logger: the logger to send messages to
        
        '''
        if Islandora_configuration_object.configuration_dictionary['alerts']['medium']=='mailx':
            logger.info('Using the mailx alerter')
            self._alerter = mailx_alerter(Islandora_configuration_object, logger)
    @newrelic.agent.function_trace()
    def send_message(self, message = None, subject = None):
        '''
        calls the send message on the implementation object
        If message or subject is not supplied they will be given a default.
        
        @param string subject:
            the subject of the message to send defaults to stack trace
        @param string message:
            the body of the message to send defaults to 
            'An exception has occured while ingesting.'
        '''
        if not subject:
            subject = 'An exception has occured while ingesting.'
        if not message:
            message = 'Details:' + traceback.format_exc()
            
        self._alerter.send_message(message, subject)
        
        return
    
class mailx_alerter(object):
    '''
        This class is an alerter that operates through the mailx program
    '''
    @newrelic.agent.function_trace()
    def __init__(self, Islandora_configuration_object, logger, emailer = None):
        '''
            Constructor
            @param Islandora_configuration_object: the configuration to base this mailx alerter on
            @param logger: the logger to send messages to
        
        '''
        self._logger = logger
        self._configuration = Islandora_configuration_object.configuration_dictionary
        self._subject = self._configuration['miscellaneous']['ingest_name']
        self._recievers = self._configuration['alerts']['emails'].split()
        if not emailer:
            self._mailer = mailer(subject=self._subject, addresses=self._recievers)
        else:
            self._mailer = emailer
    @newrelic.agent.function_trace()
    def send_message(self, message = None, subject = None):
        '''
        This method will send an email using mailx
        
        @param subject: the subject of the message to send
        @param message: the body of the message to send
        '''
        if subject:#use the default subject if it is not passed in
            self._mailer.set_subject(subject)
        
        #clear and set the message
        self._mailer.clear_message()
        self._mailer.add_string(message)
        
        self._logger.info("Sending email (%s) to addresses: (%s) with message (%s)" % (subject, self._recievers, message))
        self._mailer.send()
        
        self._mailer.set_subject(self._subject)#reset subject for next message