'''
Created on May 30, 2011

This is a holding place for useful re-usable code
that doesn't have a place anywhere else in the package
'''

import os
import hashlib
import re

def getMimeType(extension):
    '''
    This function will get the mimetype of the provided file extension
    This is not fool proof, some extensions have multiple mimetypes possible.  I return what was useful for me.
    It is also limited to a small set of mimetypes.

    @param extension
      The file extension to find the mimetype from

    @return mimeType
      The mimetype that was associated to the file extension
    @todo
      add more mimeTypes

    @todo
      Match Islandora's functionality
    @note
      We could instead use the python mimetypes module
    @see
      http://docs.python.org/library/mimetypes.html
    '''

    # use mimetypes module instead
    """
    file = ext.lower()
    if ext.find(".") == -1:
        file = "." + ext # make sure there is a . in it
    return mimetypes.guess_type("a" + file)[0] #prepend something so there definitely is a file name
    """

    # use custom mimetype lookup
    ext = extension.lower()

    #strip the '.' if it was included in the ext string
    if ext.find('.')==0:#using find to avoid catching the doesn't exist exception from index
        ext = ext[1:]

    # this is the list of mime types defined in MimeClass.inc in islandora (commit f608652cf6421c2952100b451fe2d699cb1d8b63)
    mimes = {
        # openoffice:
        'odb' : 'application/vnd.oasis.opendocument.database',
        'odc' : 'application/vnd.oasis.opendocument.chart',
        'odf' : 'application/vnd.oasis.opendocument.formula',
        'odg' : 'application/vnd.oasis.opendocument.graphics',
        'odi' : 'application/vnd.oasis.opendocument.image',
        'odm' : 'application/vnd.oasis.opendocument.text-master',
        'odp' : 'application/vnd.oasis.opendocument.presentation',
        'ods' : 'application/vnd.oasis.opendocument.spreadsheet',
        'odt' : 'application/vnd.oasis.opendocument.text',
        'otg' : 'application/vnd.oasis.opendocument.graphics-template',
        'oth' : 'application/vnd.oasis.opendocument.text-web',
        'otp' : 'application/vnd.oasis.opendocument.presentation-template',
        'ots' : 'application/vnd.oasis.opendocument.spreadsheet-template',
        'ott' : 'application/vnd.oasis.opendocument.text-template',
        # staroffice:
        'stc' : 'application/vnd.sun.xml.calc.template',
        'std' : 'application/vnd.sun.xml.draw.template',
        'sti' : 'application/vnd.sun.xml.impress.template',
        'stw' : 'application/vnd.sun.xml.writer.template',
        'sxc' : 'application/vnd.sun.xml.calc',
        'sxd' : 'application/vnd.sun.xml.draw',
        'sxg' : 'application/vnd.sun.xml.writer.global',
        'sxi' : 'application/vnd.sun.xml.impress',
        'sxm' : 'application/vnd.sun.xml.math',
        'sxw' : 'application/vnd.sun.xml.writer',
        # k-office:
        'kil' : 'application/x-killustrator',
        'kpt' : 'application/x-kpresenter',
        'kpr' : 'application/x-kpresenter',
        'ksp' : 'application/x-kspread',
        'kwt' : 'application/x-kword',
        'kwd' : 'application/x-kword',
        # ms office 97:
        'doc' : 'application/msword',
        'xls' : 'application/vnd.ms-excel',
        'ppt' : 'application/vnd.ms-powerpoint',
        # office2007:
        'docx' : 'application/vnd.openxmlformats-officedocument.wordprocessingml.document',
        'docm' : 'application/vnd.ms-word.document.macroEnabled.12',
        'dotx' : 'application/vnd.openxmlformats-officedocument.wordprocessingml.template',
        'dotm' : 'application/vnd.ms-word.template.macroEnabled.12',
        'xlsx' : 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
        'xlsm' : 'application/vnd.ms-excel.sheet.macroEnabled.12',
        'xltx' : 'application/vnd.openxmlformats-officedocument.spreadsheetml.template',
        'xltm' : 'application/vnd.ms-excel.template.macroEnabled.12',
        'xlsb' : 'application/vnd.ms-excel.sheet.binary.macroEnabled.12',
        'xlam' : 'application/vnd.ms-excel.addin.macroEnabled.12',
        'pptx' : 'application/vnd.openxmlformats-officedocument.presentationml.presentation',
        'pptm' : 'application/vnd.ms-powerpoint.presentation.macroEnabled.12',
        'ppsx' : 'application/vnd.openxmlformats-officedocument.presentationml.slideshow',
        'ppsm' : 'application/vnd.ms-powerpoint.slideshow.macroEnabled.12',
        'potx' : 'application/vnd.openxmlformats-officedocument.presentationml.template',
        'potm' : 'application/vnd.ms-powerpoint.template.macroEnabled.12',
        'ppam' : 'application/vnd.ms-powerpoint.addin.macroEnabled.12',
        'sldx' : 'application/vnd.openxmlformats-officedocument.presentationml.slide',
        'sldm' : 'application/vnd.ms-powerpoint.slide.macroEnabled.12',
        # wordperfect (who cares?):
        'wpd' : 'application/wordperfect',
        # common and generic containers:
        'pdf' : 'application/pdf',
        'eps' : 'application/postscript',
        'ps' : 'application/postscript',
        'rtf' : 'text/rtf',
        'rtx' : 'text/richtext',
        'latex' : 'application/x-latex',
        'tex' : 'application/x-tex',
        'texi' : 'application/x-texinfo',
        'texinfo' : 'application/x-texinfo',
        # *ml:
        'css' : 'text/css',
        'htm' : 'text/html',
        'html' : 'text/html',
        'wbxml' : 'application/vnd.wap.wbxml',
        'xht' : 'application/xhtml+xml',
        'xhtml' : 'application/xhtml+xml',
        'xsl' : 'text/xml',
        'xml' : 'text/xml',
        'csv' : 'text/csv',
        'tsv' : 'text/tab-separated-values',
        'txt' : 'text/plain',
        # images:
        "bmp" : "image/bmp",
        "gif" : "image/gif",
        "ief" : "image/ief",
        "jpeg" : "image/jpeg",
        "jpe" : "image/jpeg",
        "jpg" : "image/jpeg",
        "jp2" : "image/jp2",
        "png" : "image/png",
        "tiff" : "image/tiff",
        "tif" : "image/tiff",
        "djvu" : "image/vnd.djvu",
        "djv" : "image/vnd.djvu",
        "wbmp" : "image/vnd.wap.wbmp",
        "ras" : "image/x-cmu-raster",
        "pnm" : "image/x-portable-anymap",
        "pbm" : "image/x-portable-bitmap",
        "pgm" : "image/x-portable-graymap",
        "ppm" : "image/x-portable-pixmap",
        "rgb" : "image/x-rgb",
        "xbm" : "image/x-xbitmap",
        "xpm" : "image/x-xpixmap",
        "xwd" : "image/x-windowdump",
        # videos:
        "mpeg" : "video/mpeg",
        "mpe" : "video/mpeg",
        "mpg" : "video/mpeg",
        "m4v" : "video/mp4",
        "mp4" : "video/mp4",
        "ogv" : "video/ogg",
        "qt" : "video/quicktime",
        "mov" : "video/quicktime",
        "mxu" : "video/vnd.mpegurl",
        "avi" : "video/x-msvideo",
        "movie" : "video/x-sgi-movie",
        "flv" : "video/x-flv",
        "swf" : "application/x-shockwave-flash",
        # audio:
        "mp3" : "audio/mpeg",
        "mp4a" : "audio/mp4",
        "m4a" : "audio/mp4",
        "oga" : "audio/ogg",
        "ogg" : "audio/ogg",
        "flac" : "audio/x-flac",
        "wav" : "audio/vnd.wave",
        # compressed formats: (note: http:#svn.cleancode.org/svn/email/trunk/mime.types)
        "tgz" : "application/x-gzip",
        "gz" : "application/x-gzip",
        "tar" : "application/x-tar",
        "gtar" : "application/x-gtar",
        "zip" : "application/x-zip",
        # others:
        'bin' : 'application/octet-stream',
    }

    # these are some additional mimetypes not covered that are required for various projects
    mimes.update({
        # combo types
        'dvi' : 'application/x-dvi',
        'rar' : 'application/x-rar-compressed',
        'rm'  : 'audio/x-pn-realaudio', # this one can do audio/video/images
        # text types
        'ocr' : 'text/plain',
        'mods': 'text/xml',
        'exif': 'text/xml',
        # image types
        'nef' : 'image/x-nikon-net',
        'dng' : 'image/x-adobe-dng',
        'tn'  : 'image/jpeg', # used for fedora thumbnails
        # video types
        '3gp' : 'video/3gpp',
        'wmv' : 'video/x-ms-wmv',
    })

    if ext in mimes:
        return mimes[ext]

    # assume an unkown binary format if no match found

    return 'application/octet-stream'


def __chunk(file_name, size):
    start = 0
    with open(file_name, 'r+b') as temp:
        pass

def hash_file(file_name, hash_type='SHA-1', chunks=2**20):
    '''
        Hashes a file at the given path with the given algorithm, and returns the hash.

        @author Adam Vessey

        @param file_name A string containing the path to the relevant file
        @param hash_type A hashing algorithm, currently restricted to those
            available in Fedora 3.4.2 {MD5,SHA-{1,256,38{4,5},512}}
            NOTE:  385 is made to point to 384
        @param chunks The number of hash blocks to read at a time

        @return A string containing the hex digest of the file.

        @todo:  Remove commented debug code.
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
        with open(file_name, 'rb') as temp:
            h = hashlib.new(hashes[hash_type])

            #Should chunk the hashing based on the hash's block_size, and the number of chunks specified.  Yay memory efficiency?
            #This seems to work, it seems a little weird in my head...  May have to look at it in the future?
            #total = 0
            chunksize = chunks * h.block_size
            #Lamba craziness borrowed from stackoverflow.  Huzzah!
            for chunk in iter(lambda: temp.read(chunksize), ''):
                #total += len(chunk)
                #print('Chunksize: %s\tTotal: %s' % (len(chunk), total))
                h.update(chunk)
            #print('File size: %s' % temp.tell())
            return h.hexdigest()
    else:
        raise ValueError('File %s does not exist!' % file_name)

def force_extract_integer_from_string(string_to_cast):
    '''
    This is a simple function that will quash non-numeric characters in a string and return an integer.
    The integer will be made up of all numerals in the string.
    @param string_to_cast
      The string to quash to an int
    @return string_cast_to_int
      The integer value of the quashed string
    '''
    interum_string = re.sub('[^0-9]', '', string_to_cast)#match non-numeric, replaces with nothing
    string_cast_to_int = int(interum_string)
    return string_cast_to_int

if __name__ == '__main__':
    '''
    @todo:
      refine the 'tests'
    '''
    #print(hash_file('/mnt/fjm_obj/dump/Fotos/949_0227818_53.jpg', 'SHA-1'))
    print(force_extract_integer_from_string('l33t'))

    pass
