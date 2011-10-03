'''
Created on March 5, 2011

@author: jonathangreen
Copyied into islandoraUtils by Adam Vessey
TODO:  Should likely be made to use the fileConverter module, so as not to have two copies of code which do much of the same thing...
'''

# These will appear in an IDE as broken dependencies.
# This is OK because they live in the plugins folder but are invoked in the app's main folder
# by the plugin manager
from islandoraUtils.fedoraLib import get_datastream_as_file, update_datastream, mangle_dsid
from shutil import rmtree
from datetime import datetime
from islandoraUtils.metadata.fedora_relationships import rels_int
import os
import subprocess
import string
import httplib
import re
import random
import types
import logging
import fcrepo
#Get etree from somewhere...
from lxml import etree


# thumbnail constants
tn_postfix = '-tn.jpg'
tn_size = (150, 200)
'''
#handle constants
handleServer='damocles.coalliance.org'
handleServerPort='9080'
handleServerApp='/handles/handle.jsp?'


def get_handle(obj):
    try:
      conn = httplib.HTTPConnection(handleServer,handleServerPort,timeout=10)
      conn.request('GET', handleServerApp+'debug=true&adr3=true&pid='+obj.pid)
      res = conn.getresponse()
    except:
      logging.error("Error connecting to Handle Server. PID: %s." % (obj.pid))
      return False

    # convert the response to lowercase and see if it contains success
    text = string.lower(res.read())

    if ( string.find(text,'==>success') != -1 ):
        logging.info("Successfuly created handle for %s." % obj.pid)
        return True
    else:
        logging.info("Failed to create handle for %s." % obj.pid)
        return False
'''
def create_thumbnail(obj, dsid, tnid):
    # We receive a file and create a jpg thumbnail
    directory, file = get_datastream_as_file(obj, dsid, "tmp")
    
    # Make a thumbnail with convert
    r = subprocess.call(['convert', directory+'/'+file+'[0]', '-thumbnail', \
         '%sx%s' % tn_size, '-colorspace', 'rgb', 'jpg:'+directory+'/'+tnid])
   
    if r == 0:
        update_datastream(obj, tnid, directory+'/'+tnid, label='thumbnail', mimeType='image/jpeg')
    else :
        logging.warning('PID:%s DSID:%s Thumbnail creation failed (return code:%d).' % (obj.pid, dsid, r))
        #Try again on failure?
       
    logging.debug(directory)
    logging.debug(file)
    logging.debug(tnid)
    logging.debug(os.listdir(directory))

    rmtree(directory, ignore_errors=True)
    return r

def create_jp2(obj, dsid, jp2id):
    # We receive a TIFF and create a Lossless JPEG 2000 file from it.
    directory, file = get_datastream_as_file(obj, dsid, 'tiff') 
    r = subprocess.call(["convert", directory+'/'+file, '+compress', directory+'/uncompressed.tiff'])
    if r != 0:
        logging.warning('PID:%s DSID:%s JP2 creation failed (convert return code:%d).' % (obj.pid, dsid, r))
        rmtree(directory, ignore_errors=True)
        return r;
    r = subprocess.call(["kdu_compress", "-i", directory+'/uncompressed.tiff', 
      "-o", directory+"/tmpfile_lossy.jp2", "-rate", "0.5", "Clayers=1", "Clevels=7", "Cprecincts={256,256},{256,256},{256,256},{128,128},{128,128},{64,64},{64,64},{32,32},{16,16}", "Corder=RPCL", "ORGgen_plt=yes", "ORGtparts=R", "Cblk={32,32}", "Cuse_sop=yes"])
    if r != 0:
        logging.warning('PID:%s DSID:%s JP2 creation failed. Trying alternative.' % (obj.pid, dsid))
    	r = subprocess.call(["convert", directory+'/'+file, '-compress', 'JPEG2000', '-quality', '50%', directory+'/tmpfile_lossy.jp2'])
        if r != 0:
            logging.warning('PID:%s DSID:%s JP2 creation failed (kdu_compress return code:%d).' % (obj.pid, dsid, r))

    if r == 0:
        update_datastream(obj, jp2id, directory+'/tmpfile_lossy.jp2', label='Compressed JPEG2000', mimeType='image/jp2')

    rmtree(directory, ignore_errors=True)
    return r

def create_mp3(obj, dsid, mp3id):
    # We recieve a WAV file. Create a MP3
    directory, file = get_datastream_as_file(obj, dsid, "wav")
    
    # Make MP3 with lame
    # Allow it (joint) Stereo (might be good to check if the input is stereo?) and VBR...  Probably a good idea to enforce ISO, given our area.
    r = subprocess.call(['lame', '-mj', '-v', '-V6', '-B224', '--strictly-enforce-ISO', directory+'/'+file, directory+'/'+mp3id])
    if r == 0:
      update_datastream(obj, mp3id, directory+'/'+mp3id, label='compressed to mp3', mimeType='audio/mpeg')
    else:
      logging.warning('PID:%s DSID:%s MP3 creation failed (lame return code:%d).' % (obj.pid, dsid, r))

    rmtree(directory, ignore_errors=True)
    return r

def create_ogg(obj, dsid, oggid):
    #recieve a wav file create a OGG
    directory, file = get_datastream_as_file(obj, dsid, "wav")
    
    # Make OGG with ffmpeg
    r = subprocess.call(['ffmpeg', '-i', directory+'/'+file, '-acodec', 'libvorbis', '-ab', '48k', directory+'/'+oggid])
    if r == 0:
        update_datastream(obj, oggid, directory+'/'+oggid, label='compressed to ogg', mimeType='audio/ogg')
    else:
        logging.warning('PID:%s DSID:%s OGG creation failed (ffmpeg return code:%d).' % (obj.pid, dsid, r))
    rmtree(directory, ignore_errors=True)
    return r

def create_swf(obj, dsid, swfid):
    #recieve PDF create a SWF for use with flexpaper
    directory, file = get_datastream_as_file(obj, dsid, "pdf")
    
    r = subprocess.call(['pdf2swf', directory+'/'+file, '-o', directory+'/'+swfid,\
         '-T 9', '-f', '-t', '-s', 'storeallcharacters', '-G'])
    if r != 0:
        logging.warning('PID:%s DSID:%s SWF creation failed. Trying alternative.' % (obj.pid, dsid))
        r = subprocess.call(['pdf2swf', directory+'/'+file, '-o', directory+'/'+swfid,\
             '-T 9', '-f', '-t', '-s', 'storeallcharacters', '-G', '-s', 'poly2bitmap'])
        if r != 0:
            logging.warning('PID:%s DSID:%s SWF creation failed (pdf2swf return code:%d).' % (obj.pid, dsid, r))

    if r == 0:
        update_datastream(obj, swfid, directory+'/'+swfid, label='pdf to swf', mimeType='application/x-shockwave-flash')

    rmtree(directory, ignore_errors=True)
    return r

def create_pdf(obj, dsid, pdfid):
    #recieve document and create a PDF with libreoffice if possible
    directory, file = get_datastream_as_file(obj, dsid, "document")
    
    subprocess.call(['soffice', '--headless', '-convert-to', 'pdf', '-outdir', directory, directory+'/'+file])
    newfile = file.split('.',1)[0]
    newfile += '.pdf'

    if os.path.isfile(directory + '/' + newfile):
        update_datastream(obj, pdfid, directory+'/'+newfile, label='doc to pdf', mimeType='application/pdf')
        # we should probably be using true or false like normal python, but i stay consistant here
        value = 0
    else:
        value = 1
        logging.warning('PID:%s DSID:%s PDF creation failed.' % (obj.pid, dsid))

    rmtree(directory, ignore_errors=True)
    return value

def marcxml_to_mods(obj, dsid, dsidOut='MODS'):
    logger = logging.getLogger('islandoraUtils.DSConverter.marcxml_to_mods')
    directory, file = get_datastream_as_file(obj, dsid, 'MARCXML')
    logger.debug('Got datastream')
    marcxml = etree.parse(os.path.join(directory, file))
    logger.debug('Parsed datastream')
    transform = etree.XSLT(etree.parse(os.path.join(os.path.dirname(__file__), '__resources/marcxml2mods.xslt')))
    logger.debug('Parsed XSLT')
    transformed = transform(marcxml)
    logger.debug('Transformed datastream')

    with open(os.path.join(directory, dsidOut), 'w', 0) as temp:
      transformed.write(temp)
      logger.debug('Wrote transformed DS to disk')

    r = update_datastream(obj, dsidOut, temp.name, label='MODS (translated from MARCXML)', mimeType="text/xml")
    
    rmtree(directory, ignore_errors=True)
    return r

def check_dates(obj, dsid, derivativeid):
    date = datetime.strptime( obj[dsid].createdDate, '%Y-%m-%dT%H:%M:%S.%fZ' )
    derdate = datetime.strptime( obj[derivativeid].createdDate, '%Y-%m-%dT%H:%M:%S.%fZ' )

    if date > derdate:
        return True
    else:
        return False

