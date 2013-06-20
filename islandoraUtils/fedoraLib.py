'''
Created on Apr 20, 2011

@author: William Panting
'''
import tempfile
import string
import re
import random
import subprocess
from urllib import quote
import logging
from StringIO import StringIO as StringIO
from fcrepo.connection import Connection
from fcrepo.client import FedoraClient as Client
from metadata import fedora_relationships as FR
import os
from time import sleep
import hashlib
from islandoraUtils.misc import hash_file
import requests

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

def get_datastream_as_file(obj, dsid, extension = ''):
    '''
    Download the indicated datastream (probably for processing)

    Taken out of Fedora Microservices

    @author Alexander O'Neil

    '''
    d = tempfile.mkdtemp()
    success = False
    tries = 10
    filename = '%(dir)s/content.%(ext)s' % {'dir': d, 'ext': extension}
    while not success and tries > 0:
        with open(filename, 'w') as f:
            f.write(obj[dsid].getContent().read())
            f.flush() #Flushing should be enough...  Shouldn't actually have to sync the filesystem.  Caching would actually be a good thing, yeah?
            logging.debug("Size of datastream: %(size)d. Size on disk: %(size_disk)d." % {'size': obj[dsid].size, 'size_disk': os.path.getsize(filename)})
            success = os.path.getsize(filename) == obj[dsid].size
            if not success:
                tries = tries - 1
    return d, 'content.'+extension

def update_datastream(obj, dsid, filename, label='', mimeType='', controlGroup='M', tries=3, checksumType=None, checksum=None):
    '''
    This function uses requests to add a datastream to Fedora via the REST API,
    because of a bug [we need confirmation that this is the bug Alexander
    referenced in Federa Microservices' code] in the pyfcrepo library, that
    creates unnecessary failures with closed sockets.  The bug could be related
    to the use of httplib.

    @author Alexander Oneil

    @param obj:
    @param dsid:
    @param filename: If the controlGroup is X or M. This is a filename as a string.
      If it is R or E then it should be a URL as a string.
    @param label:
    @param mimeType:
    @param controlGroup:
    @param tries:  The number of attempts at uploading
    @param checksumType:  A hashing algorithm to attempt...
    @param checksum: A precalculated sum for the file.  Is unlikely to work for
      inline XML streams, due to normalization Fedora performs when saving.
    @return boolean representing success
    '''
    logger = logging.getLogger('islandoraUtils.fedoraLib.update_datastream')

    #Get the connection from the object.
    conn = obj.client.api.connection

    '''
    XXX: Could probably avoid the creation of this array, and put stuff
    directly into the post_vars dictionary.
    '''
    info_dict = {
        'url': conn.url,
        'username': conn.username, 'password': conn.password,
        'pid': obj.pid, 'dsid': dsid,
        'label': label, 'mimetype': mimeType, 'controlgroup': controlGroup,
        'filename': filename,
        'tries': tries,
        'checksumType': checksumType,
        'checksum': checksum
    }

    #FIXME:  This is duplicated here and in misc.hash_file
    #The checksum/hashing algorithms supported by Fedora (mapped to the names that Python's hashlib uses)
    hashes = {
        'MD5': 'md5',
        'SHA-1': 'sha1',
        'SHA-256': 'sha256',
        'SHA-384': 'sha384',
        'SHA-385': 'sha384', #Seems to be an error in the Fedora documentation (SHA-385 doesn't actually exist)?  Let's try to account for it.
        'SHA-512': 'sha512'
    }

    #Wanna do checksumming?
    if checksumType in hashes:
        #Let's figure it out ourselves!
        if checksum is None:
            #No sum provided, calculate it:
            info_dict['checksum'] = hash_file(filename, checksumType)
        else:
            #We trust the user to provide the proper checksum (don't think that Fedora does, though)
            pass

    post_vars = {
      'dsLabel': info_dict['label'],
      'mimeType': info_dict['mimetype'],
      'controlGroup': info_dict['controlgroup'],
      'checksumType': info_dict['checksumType'],
      'checksum': info_dict['checksum']
    }
    if post_vars['checksumType'] is None:
        del post_vars['checksumType']
        del post_vars['checksum']
    elif post_vars['checksum'] is None:
        del post_vars['checksum']

    files = {}
    if info_dict['controlgroup'] in ['R', 'E']:
      post_vars['dsLocation'] = info_dict['filename']
    else:
      files['file'] = open(info_dict['filename'], 'rb')

    updated = False
    while not updated and info_dict['tries'] > 0:
      files['file'].seek(0)
      info_dict['tries'] = info_dict['tries'] - 1
      r = requests.post('%(url)s/objects/%(pid)s/datastreams/%(dsid)s' % info_dict,
          auth=(info_dict['username'], info_dict['password']),
          params=post_vars,
          files=files)
      if r.status_code == 201:
        logger.info('Updated %(pid)s/%(dsid)s.' % info_dict)
        updated = True
      else:
        logger.warning('Failed to update %(pid)s/%(dsid)s: %(tries)s tries remaining.' % info_dict)
        sleep(5) #Something went wrong...  Let's give it a few, to see if it sorts itself out.

    if not updated:
        logger.error('Failed to update %(pid)s/%(dsid)s in the given number ' +
          'of attempts.  Failing...')
    for name, f in files.items():
      f.close()
    return updated

def update_hashed_datastream_without_dup(obj, dsid, filename, **params):
    '''
        @author Adam Vessey
        NOTE:  This function essentially wraps update_datastream, and as such takes an
            identical set of parameters

        Get the DS profile
        if 404'd due to DS, then
            update;
        else if there is an algorithm in the profile, then
            use it to hash;
                if the calculated hash is not the same as that from the profile, update
            else,
                use the provided checksumType to hash and update
    '''

    if params['checksumType'] and params['checksumType'] != 'DISABLED': #If we do really want to hash,
        if dsid in obj and params['checksumType'] == obj[dsid].checksumType: #And we want to use the same algorithm as is already in use
            #Figure out the checksum for the given file (if it isn't given)
            if not params['checksum']:
                params['checksum'] = hash_file(filename, params['checksumType'])


            #And compare the checksums.
            if params['checksum'] == obj[dsid].checksum:
                #If it's the same, we don't actually need to add the new version.
                return True
            else:
                #If the sums are different, we need to update (fall through to end of function)
                pass
        else:
            #We're trying to use a different algorithm.  Log in info and update? (fall through to end of function)
            pass
    else:
        #No algorithm specified:  Nothing to compare, so update (fall through)
        pass

    return update_datastream(obj=obj, dsid=dsid, filename=filename, **params)

if __name__ == '__main__':
    import fcrepo
    connection = fcrepo.connection.Connection('http://localhost:8080/fedora', username='fedoraAdmin', password='fedoraAdmin', persistent=False)
    client = fcrepo.client.FedoraClient(connection)
    #print(client.getDatastreamProfile('atm:1250', 'DC'))
    #print(client.getDatastreamProfile('atm:1075', 'DC'))
