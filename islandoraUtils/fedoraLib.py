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
    
def update_datastream(obj, dsid, filename, label='', mimeType='', controlGroup='M', tries=3):
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
        'filename': filename,
        'tries': tries
    }

    # Using curl due to an incompatibility with the pyfcrepo library.
    #Go figure...  You'd think that instead of [..., '-F', 'file=@%(filename)s', ...], you should be using [..., '--data-binary', '@%(filename)s', ...], but the latter here fails to upload text correctly...
    commands = ['curl', '-i', '-H', '-XPOST', '%(url)s/objects/%(pid)s/datastreams/%(dsid)s?dsLabel=%(label)s&mimeType=%(mimetype)s&controlGroup=%(controlgroup)s' % info_dict, 
        '-F', 'file=@%(filename)s' % info_dict, '-u', 
        '%(username)s:%(password)s' % info_dict]
    
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
    
def activateObjects(relations, namespaces, client):
    '''
    @author: Adam Vessey
    ***DOESN'T ACTUALLY DO ANYTHING AT PRESENT (only prints out the query it 'should' use)***
    'rels' should be a dictionary whose keys correspond to content models in SPARQL syntax (eg 'islandora:basicCModel', assuming 'islandora' is set in namespaces), pointing to a list of relationships stored in tuples.  
        (NOTE:  'AnY' indicates a wildcard search, though we check that the matched object is active)
    'client' is an fcrepo client object
    
    NOTE:  I hacked the predicate 'fedora-view:disseminates' is handled differently...  The 'subject' of the relationship should be something like 'fedora:*/JPG'
    '''
    NSs = {
        'fedora': 'info:fedora/', 
        'fedora-model': 'info:fedora/fedora-sys:def/model#'
    }
    if namespaces:
        NSs.update(namespaces)
    query = StringIO()
    for alias, uri in NSs.items():
        if isinstance(uri, FR.rels_namespace):
            query.write('PREFIX %s: <%s>\n' % (alias, uri.uri))
        else:
            query.write('PREFIX %s: <%s>\n' % (alias, uri))
    query.write('FROM <#ri> \
SELECT $obj \
WHERE {')
        
    sections = list() #List of stringIOs used to build the query for individual objects.  Each item in the list will the be joined together with 'union' separating
    for cmodel, rels in relations.items():
        section = StringIO('{\n')
        vars = 0
        for pred, obj in rels:
            u_pred = pred
            u_obj = '$obj%s' % vars
            section.write('$obj %s %s .\n' % (u_pred, u_obj))
            
            #XXX:  A terrible, terrible hack...  But it should work?
            if u_pred == 'fedora-view:disseminates':
                section.write('%s fedora-view:disseminationType <%s>.\n' % (u_obj, obj))
                section.write('%s fedora-model:State fedora-model:Active .\n')
                
            vars += 1
        section.write('$obj fedora-model:State fedora-model:Inactive .\n')
        section.write('}')
        sections.append(section)
    query.write('\nUNION\n'.join(sections))
    query.write('}')
    print query
    #for result in client.searchTriples(query=query, limit='1000000'):
    #    client.getObject(result['obj']['value'].rpartition('/')[2]).state = 'Active'
    
if __name__ == '__main__':
    connection = fcrepo.connection.Connection('http://localhost:8080/fedora', username='fedoraAdmin', password='fedoraAdmin', persistent=False)
    client = fcrepo.client.FedoraClient(connection)
    activateObjects([('fedora-view:disseminates', 'fedora:*/JPG')], {'asdf': 'fedora:atm:', 'atm-rel': 'http://www.example.org/dummy#'}, client)
    
