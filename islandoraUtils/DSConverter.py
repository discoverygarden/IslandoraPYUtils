'''
Created on March 5, 2011

@author: jonathangreen
Copyied into islandoraUtils by Adam Vessey
TODO:  Should likely be made to use the fileConverter module, so as not to have
two copies of code which do much of the same thing... If someone is doing this
this should be treated as the cannonical copy. I have been updating these
conversion scripts with input from JWA and Colorado.
'''

from islandoraUtils.fedoraLib import get_datastream_as_file, update_datastream
from shutil import rmtree, move
from datetime import datetime
import os
import subprocess
import logging
from lxml import etree
from fcrepo.connection import FedoraConnectionException
import re

# thumbnail constants
tn_postfix = '-tn.jpg'
tn_size = (150, 200)

def create_thumbnail(obj, dsid, tnid):
    logger = logging.getLogger('islandoraUtils.DSConverter.create_thumbnail')

    # We receive a file and create a jpg thumbnail
    directory, file = get_datastream_as_file(obj, dsid, "tmp")
    
    # fine out what mimetype the input file is
    try:
        mime = obj[dsid].mimeType
    except KeyError:
        mime = None

    infile = os.path.join(directory, file)
    tmpfile = os.path.join(directory, 'tmp.jpg')
    tnfile = os.path.join(directory, tnid)

    # make the thumbnail based on the mimetype of the input
    # right now we assume everything but video/mp4 can be handled 
    if mime == 'video/mp4':
        r = subprocess.call(['ffmpeg', '-itsoffset', '-4', '-i', infile, '-vcodec', 'mjpeg',\
             '-vframes', '1', '-an', '-f', 'rawvideo', tmpfile])
        if r == 0:
            r = subprocess.call(['convert', '%s[0]' % tmpfile, '-thumbnail', '%sx%s' % tn_size,\
                 '-colorspace', 'rgb', 'jpg:%s'%tnfile])
    else:
        # Make a thumbnail with convert
        r = subprocess.call(['convert', '%s[0]' % infile, '-thumbnail', \
             '%sx%s' % tn_size, '-colorspace', 'rgb', '+profile', '*', 'jpg:%s'%tnfile])
   
    if r == 0:
        update_datastream(obj, tnid, directory+'/'+tnid, label='thumbnail', mimeType='image/jpeg')
    else :
        logger.warning('PID:%s DSID:%s Thumbnail creation failed (return code:%d).' % (obj.pid, dsid, r))
       
    logger.debug(directory)
    logger.debug(file)
    logger.debug(tnid)
    logger.debug(os.listdir(directory))

    rmtree(directory, ignore_errors=True)
    return r

def create_jp2(obj, dsid, jp2id):
    logger = logging.getLogger('islandoraUtils.DSConverter.create_jp2')
    # We receive a TIFF and create a Lossless JPEG 2000 file from it.
    directory, file = get_datastream_as_file(obj, dsid, 'tiff') 
    r = subprocess.call(["convert", directory+'/'+file, '+compress', '-colorspace', 'RGB', directory+'/uncompressed.tiff'])
    if r != 0:
        logger.warning('PID:%s DSID:%s JP2 creation failed (convert return code:%d).' % (obj.pid, dsid, r))
        rmtree(directory, ignore_errors=True)
        return r;
    r = subprocess.call(["kdu_compress", "-i", directory+'/uncompressed.tiff', "-o", directory+"/tmpfile_lossy.jp2", "-rate", "0.5", "Clayers=1", "Clevels=7", "Cprecincts={256,256},{256,256},{256,256},{128,128},{128,128},{64,64},{64,64},{32,32},{16,16}", "Corder=RPCL", "ORGgen_plt=yes", "ORGtparts=R", "Cblk={32,32}", "Cuse_sop=yes"])
    if r != 0:
        logger.warning('PID:%s DSID:%s JP2 creation failed. Trying alternative.' % (obj.pid, dsid))
    	r = subprocess.call(["convert", directory+'/'+file, '-compress', 'JPEG2000', '-quality', '50%', directory+'/tmpfile_lossy.jp2'])
        if r != 0:
            logger.warning('PID:%s DSID:%s JP2 creation failed (kdu_compress return code:%d).' % (obj.pid, dsid, r))

    if r == 0:
        update_datastream(obj, jp2id, directory+'/tmpfile_lossy.jp2', label='Compressed JPEG2000', mimeType='image/jp2')

    rmtree(directory, ignore_errors=True)
    return r

def create_mp4(obj, dsid, mp4id):
    logger = logging.getLogger('islandoraUtils.DSConverter.create_mp4')
    directory, file = get_datastream_as_file(obj, dsid, 'video') 

    infile = os.path.join(directory, file)
    avifile = os.path.join(directory, 'output.avi')
    mp4file = os.path.join(directory, 'output.mp4')
    h264file = os.path.join(directory, 'output_video.h264')
    rawfile = os.path.join(directory, 'output_audio.raw')
    aacfile = os.path.join(directory, 'output_audio.aac')

    # mp4box is stupid as a bag of hammers. if you do not check if there is a audio stream it will 
    # fill the filesystem by creating a file full of junk. It also will just assume the frame rate
    # is 25fps no matter what it is, so we need to get that
    p = subprocess.Popen(['mediainfo', infile], stdout=subprocess.PIPE)
    out, err = p.communicate()
    #logger.debug('Mediainfo: %s' % out)

    # we need the framerate this is sort of ugly
    frame_rate = re.search('Frame rate\s*:\s*(\d*\.\d*) fps', out).group(1)
    if not frame_rate:
        frame_rate = '30'

    # check if we have audio we can probably do this more efficiently
    audio = re.search('Audio\n', out)

    # mencoder will encode WMV with a frame rate of 1000 (!) fps if we do not set the -ofps option.
    r = subprocess.call(["mencoder", infile, '-o', avifile, '-ofps', frame_rate, '-vf', 'scale=640:480,harddup', \
    '-af', 'resample=44100', '-oac', 'faac', '-faacopts', 'br=96', '-ovc', 'x264', '-x264encopts',\
    'bitrate=200:threads=2:turbo=2:bframes=1:nob_adapt:frameref=4:subq=5:me=umh:partitions=all'])

    if r != 0:
        logger.error('PID:%s DSID:%s MP4 creation (mencoder) failed.' % (obj.pid, dsid))
        return r
    
    if(audio):
        subprocess.call(['MP4Box', '-aviraw', 'audio', avifile])
        # again MP4Box contains vacuous space instead of logic, so we have to rename this file
        move(rawfile, aacfile)

    subprocess.call(['MP4Box', '-aviraw', 'video', avifile])

    args = ['MP4Box', '-add', h264file]
    if(audio):
        args.append('-add')
        args.append(aacfile)
    args.append('-fps')
    args.append(frame_rate)
    args.append(mp4file)

    r = subprocess.call(args)
    if r == 0:
        update_datastream(obj, mp4id, mp4file, label='compressed mp4', mimeType='video/mp4')
    else:
        logger.warning('PID:%s DSID:%s MP4 creation (MP4Box) failed.' % (obj.pid, dsid))

    rmtree(directory, ignore_errors=True)
    return r

def create_mp3(obj, dsid, mp3id, args = None):

    logger = logging.getLogger('islandoraUtils.DSConverter.create_mp3')
    
    #mimetype throws keyerror if it doesn't exist
    try:
        mime = obj[dsid].mimeType
    except KeyError:
        mime = None

    if mime == 'audio/mpeg':
        ext = 'mp3'
    else:
        ext = 'wav'

    # We recieve a WAV file. Create a MP3
    directory, file = get_datastream_as_file(obj, dsid, ext)
    
    # I think we need more sensible defaults for web streaming
    if args == None:
        args = ['-mj', '-v', '-V6', '-B224', '--strictly-enforce-ISO']

    args.insert(0, 'lame')
    args.append(os.path.join(directory,file))
    outpath = os.path.join(directory,mp3id)
    args.append(outpath)

    # Make MP3 with lame
    r = subprocess.call(args)
    if r == 0:
      update_datastream(obj, mp3id, outpath, label='compressed to mp3', mimeType='audio/mpeg')
    else:
      logger.warning('PID:%s DSID:%s MP3 creation failed (lame return code:%d).' % (obj.pid, dsid, r))

    rmtree(directory, ignore_errors=True)
    return r

def create_ogg(obj, dsid, oggid):
    logger = logging.getLogger('islandoraUtils.DSConverter.create_ogg')
    #recieve a wav file create a OGG
    directory, file = get_datastream_as_file(obj, dsid, "wav")
    
    # Make OGG with ffmpeg
    r = subprocess.call(['ffmpeg', '-i', directory+'/'+file, '-acodec', 'libvorbis', '-ab', '96k', directory+'/'+oggid])
    if r == 0:
        update_datastream(obj, oggid, directory+'/'+oggid, label='compressed to ogg', mimeType='audio/ogg')
    else:
        logger.warning('PID:%s DSID:%s OGG creation failed (ffmpeg return code:%d).' % (obj.pid, dsid, r))
    rmtree(directory, ignore_errors=True)
    return r

def create_swf(obj, dsid, swfid):
    logger = logging.getLogger('islandoraUtils.DSConverter.create_swf')
    #recieve PDF create a SWF for use with flexpaper
    directory, file = get_datastream_as_file(obj, dsid, "pdf")
    
    pdf2swf = subprocess.Popen(['pdf2swf', directory+'/'+file, '-o', directory+'/'+swfid,\
         '-T 9', '-f', '-t', '-s', 'storeallcharacters', '-G'], stdout=subprocess.PIPE)
    out, err = pdf2swf.communicate()
    if pdf2swf.returncode != 0:
        logger.warning('PID:%s DSID:%s SWF creation failed. Trying alternative.' % (obj.pid, dsid))
        pdf2swf = subprocess.Popen(['pdf2swf', directory+'/'+file, '-o', directory+'/'+swfid,\
             '-T 9', '-f', '-t', '-s', 'storeallcharacters', '-G', '-s', 'poly2bitmap'], stdout=subprocess.PIPE)
        out, err = pdf2swf.communicate()

    # catch the case where PDF2SWF fails to create the file, but returns 
    if pdf2swf.returncode == 0 and os.path.isfile(directory + '/' + swfid):
        update_datastream(obj, swfid, directory+'/'+swfid, label='pdf to swf', mimeType='application/x-shockwave-flash')
        r = 0
    elif not os.path.isfile(directory + '/' + swfid):
        logger.warning('PID:%s DSID:%s SWF creation failed (pdf2swf returned: "%s").' % (obj.pid, dsid, out))
        r = 1
    else:
        logger.warning('PID:%s DSID:%s SWF creation failed (pdf2swf return code:%d).' % (obj.pid, dsid, pdf2swf.returncode))
        r = pdf2swf.returncode

    rmtree(directory, ignore_errors=True)
    return r

def create_pdf(obj, dsid, pdfid):
    logger = logging.getLogger('islandoraUtils.DSConverter.create_pdf')
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
        logger.warning('PID:%s DSID:%s PDF creation failed.' % (obj.pid, dsid))

    logger.debug(os.listdir(directory))
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
    try:
        date = datetime.strptime( obj[dsid].createdDate, '%Y-%m-%dT%H:%M:%S.%fZ' )
        derdate = datetime.strptime( obj[derivativeid].createdDate, '%Y-%m-%dT%H:%M:%S.%fZ' )
    except FedoraConnectionException:
        return True

    if date > derdate:
        return True
    else:
        return False

