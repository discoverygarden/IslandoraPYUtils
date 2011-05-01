'''
Created on Apr 20, 2011

@author: William Panting
'''
import string, re, random, subprocess
from urllib import quote

'''
A very aptly named function that will take any string and make it conform [via hack and slash]
to Fedora's Datastream ID naming requirements 

@author: Jonathan Green

@param dsid: Datastream ID to mangle

@return dsid: Mangled ID
'''
def mangle_dsid(dsid):
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
'''
This function uses curl to add a datastream to Fedora because of a bug in the pyfcrepo library, that creates unnecessary failures with ugly closed sockets.
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
def update_datastream(obj, dsid, filename, label='', mimeType='', controlGroup='M'): 
    # Using curl due to an incompatibility with the pyfcrepo library.
    conn = obj.client.api.connection 
    return 0 == subprocess.call(['curl', '-i', '-H', '-XPOST', '%(url)s/objects/%(pid)s/datastreams/%(dsid)s?dsLabel=%(label)s&mimeType=%(mimetype)s&controlGroup=%(controlgroup)s'
                           % {'url': conn.url, 'pid': obj.pid, 'dsid': dsid, 'label': quote(label), 'mimetype': mimeType, 'controlgroup': controlGroup }, 
                           '-F', 'file=@%(filename)s' % {'filename': filename}, '-u', '%(username)s:%(password)s' % {'username': conn.username, 'password': conn.password}])