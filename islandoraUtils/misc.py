'''
Created on May 30, 2011

This is a holding place for usefull re-usable code 
that doesn't have a place anywhere else in the package
'''

import os
import hashlib

def getMimeType(ext):
    '''
    @author William Panting
    
    This function will get the mimetype of the provided file extension
    This is not fool proof, some extensions have multiple mimetypes possible.  I return what was useful for me.
    It is also limited to a small set of mimetypes.
    
    @param ext: The file extension to find the mimetype from
    @return mimeType: The mimetype that was associated to the file extension
    
    @todo   add more mimeTypes
    @todo   Match Islandora's functionality
    '''
    mimeType=''
    #strip the '.' if it was included in the ext string
    if ext.find('.')==0:#using find to avoid catching the doesin't exist exception from index
        ext=ext[1:len(ext)]
    #known cases of mimeTypes
    '''
    elif ext=='':
        mimeType=''
    '''
    
    #combo formats
    if ext=='pdf':
        mimeType='application/pdf'
    #text formats
    elif ext=='txt':
        mimeType='text/plain' 
    elif ext=='xml':
        mimeType='text/xml'
    #image formats
    elif ext=='jpg':
        mimeType='image/jpeg'
    elif ext=='jpeg':
        mimeType='image/jpeg'
    elif ext=='nef':
        mimeType='image/x-nikon-nef'
    elif ext=='jp2':
        mimeType='image/jp2'
    elif ext=='tif':
        mimeType='image/tiff'
    elif ext=='tiff':
        mimeType='image/tiff'
    elif ext=='dng':
        mimeType='image/x-adobe-dng'
    #sound formats
    #application formats
    
    #assume is an unkown binary format if no match found
    else:
        mimeType='application/octet-stream'
    
    return mimeType

def hash_file(file_name, hash_type='SHA-1', chunksize=(10*1024*1024)):
    '''
        Hashes a file at the given path with the given algorithm, and returns the hash.
        
        @author Adam Vessey
        
        @param file_name A string containing the path to the relevant file
        @param hash_type A hashing algorithm, currently restricted to those 
            available in Fedora 3.4.2 {MD5,SHA-{1,256,38{4,5},512}} 
            NOTE:  385 is made to point to 384
        @param chunksize The number of bytes to hash at a time, to help avoid memory issues
        
        @return A string containing the hex digest of the file.
    '''
    #FIXME:  This is duplicated here and in fedoraLib.update_datastream
    #The checksum/hashing algorithms supported by Fedora (mapped to the names that Python's hashlib uses)
    hashes = {
        'MD5': 'md5', 
        'SHA-1': 'sha1',
        'SHA-256': 'sha256',
        'SHA-384': 'sha384',
        'SHA-385': 'sha384', #Seems to be an error in the Fedora documentation (SHA-385 doesn't actually exist)?  Let's try to account for it.
        'SHA-512': 'sha512'
    }
    
    if os.path.exists(file_name):
        with open(file_name) as temp:
            h = hashlib.new(hashes[hash_type])
            #Should chunk the hashing in the pieces of the size specified above..  Yay memory efficiency?
            #This seems to work, it seems a little weird in my head...  May have to look at it in the future?
            for chunk in temp.read(chunksize):
                h.update(chunk)
            return h.hexdigest()
    else:
        raise ValueError('File %s does not exist!' % file_name)
