'''
Created on May 30, 2011

@author: William Panting

This is a holding place for usefull re-usable code 
that doesn't have a place anywhere else in the package
'''

def getMimeType(ext):
    '''
    This function will get the mimetype of the provided file extension
    This is not fool proof, some extensions have multiple mimetypes possible.  I return what was useful for me.
    It is also limited to a small set of mimetypes.
    
    @param ext: The file extension to find the mimetype from
    @return mimeType: The mimetype that was associated to the file extension
    
    TODO: add more mimeTypes
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
