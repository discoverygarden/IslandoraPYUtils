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
from fcrepo.connection import Connection
from fcrepo.client import FedoraClient as Client
import os
from time import sleep

from islandoraUtils.misc import hash_file, get_extension_from_mimetype


def replace_relationships(rels_object, predicate, objects):
    '''
    It may be necessary to replace existing triple store
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
    
def purge_related_objects(Fedora_client,
                          relationship_namespace,
                          relationship_name,
                          RDF_subject = None,
                          RDF_object = None,
                          is_URI = False):
    '''
    Sometimes especialy in cron jobs that sync datastources
    to Fedora it is necessary to delete objects that are 
    derived or related to an origional object. This function
    provides for that.  It will purge any objects that are 
    related to the provided subject by a certain relationship.
    subject predicate object
    
    @param Fedora_PID:
        The subject of the relationship.
    @param relationship_namespace:
        The namespace the relationship is found in.
    @param relationship_name:
        The unqualified name of the realtionship.
    @param is_URI:
        Tells if the RDF_object is a URI or a literal
    '''
    if RDF_object is not None:
        results = get_all_subjects_of_relationship(Fedora_client,
                                                   relationship_namespace,
                                                   relationship_name,
                                                   RDF_object,
                                                   is_URI)
    if RDF_subject is not None:
        results = get_all_objects_of_relationship(Fedora_client,
                                                  relationship_namespace,
                                                  relationship_name,
                                                  RDF_subject)
    for PID_to_purge in results:
        Fedora_client.deleteObject(PID_to_purge)
        
    return

def get_all_subjects_of_relationship(Fedora_client,
                                     relationship_namespace,
                                     relationship,
                                     relationship_object,
                                     is_URI = False):
    '''
    This function will run a simple query on the resource index while.
    It will return all results.
    subject predicate object
    
    @param Fedora_client:
        The client object to use to query the resource index.
    @param relationship_namesapce:
        The namespace the relationship is in.
    @param relationship
        The relationship to query sans namespace.
    @param relationship_object
        The object of the relationship to query.
    @param is_URI:
        Tells if the RDF_object is a URI or a literal
    
    @return list:
        Fedora_PID_results the pids that match the query. Not the URIs.
    '''
    
    if is_URI:
        relationship_object = '<{0}>'.format(relationship_object)
    else:
        relationship_object = '"{0}"'.format(relationship_object)
        
    query = 'PREFIX {0}: <{1}> \
                     SELECT $object \
                     FROM <#ri> \
                     WHERE {{ \
                       {{ \
                         $object {0}:{2} {3} \
                       }} \
                     }}'.format('namespace_alias',
                                relationship_namespace,
                                relationship,
                                relationship_object)

    results = list(Fedora_client.searchTriples(query, limit = None))
    Fedora_PID_results = []
    # Ask Fedora for PID.
    for result in results:
        # Remove: "info:fedora/"
        Fedora_PID_results.append(result['object']['value'][12:])
    return Fedora_PID_results

def get_all_objects_of_relationship(Fedora_client,
                                    relationship_namespace,
                                    relationship,
                                    relationship_subject,
                                    is_URI):
    '''
    This function will run a simple query on the resource index.
    It will return all results.
    subject predicate object
    
    @param Fedora_client:
        The client object to use to query the resource index.
    @param relationship_namesapce:
        The namespace the relationship is in.
    @param relationship
        The relationship to query sans namespace.
    @param relationship_object
        The subject of the relationship to query.
    
    @return list:
        Fedora_PID_results the pids that match the query. Not the URIs.
    '''
    
        
    query = 'PREFIX {0}: <{1}> \
                     SELECT $object \
                     FROM <#ri> \
                     WHERE {{ \
                       {{ \
                         {3} {0}:{2} $object \
                       }} \
                     }}'.format('namespace_alias',
                                relationship_namespace,
                                relationship,
                                relationship_subject)

    results = list(Fedora_client.searchTriples(query, limit = None))
    Fedora_PID_results = []
    # Ask Fedora for PID.
    for result in results:
        # Remove: "info:fedora/"
        Fedora_PID_results.append(result['object']['value'][12:])
    return Fedora_PID_results

def get_collection_members(Fedora_client,
                           collection_PID):
    '''
    This function will run a query against Fedora asking for all members of the 
    specified collection.
    
    @author William Panting
    
    @param Fedora_client:
        A connection to Fedora
    @param $collection_PID:
        A Fedora PID for the collection to query against.
        
    @return:
        A list of the members of the collection.
    '''
    collection_URI = 'info:fedora/' + collection_PID
    base_query = open(os.path.join(os.path.dirname(__file__), '__resources/SPARQL/member_query.sparql'), 'r').read()
    full_query = re.sub('\$collection_object', '<' + collection_URI + '>', base_query)
    
    results = Fedora_client.searchTriples(full_query, limit = None)
    results = list(results)
    
    #put them in a usable list
    collection_members = list()
    for result in results:
        collection_members.append(result['member_object']['value'])
    return collection_members
    
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
    # If extension is not set use the mimetype of the dsid to find one.
    if not extension:
        extension = get_extension_from_mimetype(obj[dsid].mimeType)[0]
                
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
    This function uses curl to add a datastream to Fedora because
    of a bug [we need confirmation that this is the bug Alexander referenced in Federa Microservices' code]
    in the pyfcrepo library, that creates unnecessary failures with closed sockets.
    The bug could be related to the use of httplib.

    @author Alexander Oneil

    @param obj:
    @param dsid:
    @param filename: If this datastream is X or M. This is a filename as a string.
      If its R or E then it should be a URL as a string.
    @param label:
    @param mimeType:
    @param controlGroup:
    @param tries:  The number of attempts at uploading
    @param checksumType:  A hashing algorigm to attempt...
    @param checksum: A precalculated sum for the file.
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
        'filename': filename,
        'tries': tries,
        'checksumType': checksumType,
        'checksum': checksum
    }

    url = '%(url)s/objects/%(pid)s/datastreams/%(dsid)s?dsLabel=%(label)s&mimeType=%(mimetype)s&controlGroup=%(controlgroup)s' % info_dict

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
            info_dict['checksum'] = hash_file(filename)
        else:
            #We trust the user to provide the proper checksum (don't think that Fedora does, though)
            pass

        url += '&checksumType=%(checksumType)s&checksum=%(checksum)s' % info_dict

    commands = ['curl', '-i', '-H', '-f', '-u', '%(username)s:%(password)s' % info_dict]
    if info_dict['controlgroup'] in ['R', 'E']:
        url += '&dsLocation=%(filename)s' % info_dict
    else:
        if(os.path.isfile(filename)):
            commands.extend(['-F', 'file=@%(filename)s' % info_dict])
        else:
            logger.error('Failed updating %(pid)s/%(dsid)s. %(filename)s doesnt exist!' % info_dict)
            return False

    commands.extend(['-XPOST', url])
    while info_dict['tries'] > 0:
        info_dict['tries'] = info_dict['tries'] - 1
        logger.debug("Updating/Adding datastream %(dsid)s to %(pid)s with mimetype %(mimetype)s from file %(filename)s" % info_dict)
        if 0 == subprocess.call(commands):
            logger.debug("%(pid)s/%(dsid)s updated!" % info_dict)
            return True
        else:
            logger.warning('Error updating %(pid)s/%(dsid)s from %(filename)s via CURL!  %(tries)s remaining...' % info_dict)
            sleep(5)
    logger.error('Failed updating %(pid)s/%(dsid)s from %(filename)s via CURL!' % info_dict)
    return False

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
