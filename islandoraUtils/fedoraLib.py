'''
Created on Apr 20, 2011

@author: William Panting
'''
import string, re, random, subprocess
from urllib import quote
import logging


def mangle_dsid(dsid):
    '''
A very aptly named function that will take any string and make it conform [via hack and slash]
to Fedora's Datastream ID naming requirements 

@author: Jonathan Green

@param dsid: Datastream ID to mangle

@return dsid: Mangled ID
'''
    find = '[^a-zA-Z0-9\.\_\-]';
    replace = '';
    dsid = re.sub(find, replace, dsid)

    if( len(dsid) > 64 ):
        dsid = dsid[-64:]

    if( len(dsid) > 0 and not dsid[0].isalpha() ):
        letter = random.choice(string.letters)
        if( len(dsid) == 64 ):
            dsid = letter+dsid[1:]
        else:
            dsid = letter+dsid

    if( dsid == '' ):
        for i in range(10):
            dsid += random.choice(string.letters)

    return dsid

def update_datastream(obj, dsid, filename, label='', mimeType='', controlGroup='M'):
    '''
This function uses curl to add a datastream to Fedora because 
of a bug [we need confirmation that this is the bug Alexander referenced in Federa Microservices' code]
in the pyfcrepo library, that creates unnecessary failures with closed sockets.
The bug could be related to the use of httplib.

@author Alexander Oneil

@param obj:
@param dsid:
@param filename:
@param label:
@param mimeType:
@param controlGroup:

@return the status of the curl subprocess call
'''
    logger = logging.getLogger('islandoraUtils.fedoraLib.update_datastream')
    
    #Get the connection from the object.
    conn = obj.client.api.connection
    
    info_dict = {
        'url': conn.url, 
        'username': conn.username, 'password': conn.password,
        'pid': obj.pid, 'dsid': dsid, 
        'label': quote(label), 'mimetype': mimeType, 'controlgroup': controlGroup, 
        'filename': filename
    }

    # Using curl due to an incompatibility with the pyfcrepo library.
    commands = ['curl', '-i', '-H', '-XPOST', '%(url)s/objects/%(pid)s/datastreams/%(dsid)s?dsLabel=%(label)s&mimeType=%(mimetype)s&controlGroup=%(controlgroup)s' % info_dict, 
        '--data-binary', '@%(filename)s' % info_dict, '-u', 
        '%(username)s:%(password)s' % info_dict]
    
    logger.debug("Updating/Adding datastream %(dsid)s to %(pid)s with mimetype %(mimetype)s" % info_dict)
    if 0 == subprocess.call(commands):
        logger.debug("%(pid)s/%(dsid)s updated!" % info_dict)
        return True
    else:
        logger.error('Error updating %(pid)s/%(dsid)s via CURL!' % info_dict)
        raise Exception("update_datastream CURL command failed!")
