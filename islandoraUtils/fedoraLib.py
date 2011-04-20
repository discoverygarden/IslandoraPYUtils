'''
Created on Apr 20, 2011

@author: William Panting
'''
import string, re, random

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