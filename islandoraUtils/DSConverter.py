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
import math

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
        # grab the 'middle' of the video for use in creating thumbnails from mp4s
        p = subprocess.Popen(['ffmpeg', '-i', infile], stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        stdout, stderr = p.communicate()
        # use stderr as ffmpeg expects two params, but duration is still returned with only the source
        duration = re.search("Duration:\s{1}\d{2}:\d{2}:\d{2}\.\d{2},", stderr).group();
        duration = duration.replace("Duration: ", '')
        duration = duration.split('.')
        # get everything before the milliseconds in hr:min:seconds format
        duration = duration[0]
        duration = map(int, duration.split(':'))
        time = math.floor(((duration[0] * 360) + (duration[1] * 60) + duration[2]) / 2)
        r = subprocess.call(['ffmpeg', '-itsoffset', '-4', '-ss', str(time), '-i', infile, '-vcodec', 'mjpeg',\
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
    mp4file = os.path.join(directory, 'output.mp4')
    
    # In 'new' ffmpeg implementations the option of a preset file has changed to -preset. To be consistent throughout point at a directory with the preset.
    r = subprocess.call(['ffmpeg', '-i', infile, '-f', 'mp4', '-vcodec', 'libx264', '-fpre', '/usr/share/ffmpeg/libx264-normal.ffpreset', '-acodec', 'libfaac', '-ab', '128k', '-ac', '2', '-async', '1', '-movflags', 'faststart', mp4file])
    if r == 0:
        update_datastream(obj, mp4id, mp4file, label='compressed mp4', mimeType='video/mp4')
    else:
        logger.warning('PID:%s DSID:%s MP4 creation (ffmpeg) failed.' % (obj.pid, dsid))

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


def create_swf(obj, dsid, swfid, args = None):
    logger = logging.getLogger('islandoraUtils.DSConverter.create_swf')
    directory, file = get_datastream_as_file(obj, dsid, "pdf") #recieve PDF create a SWF for use with flexpaper
    program = ['pdf2swf', directory+'/'+file, '-o', directory+'/'+swfid]
    if args == None:
        default_args = ['-T 9', '-f', '-t', '-s', 'storeallcharacters', '-G']
        pdf2swf = subprocess.Popen(program + default_args, stdout=subprocess.PIPE)
        out, err = pdf2swf.communicate()
        # try with additional arguments
        if pdf2swf.returncode != 0:
            logger.warning('PID:%s DSID:%s SWF creation failed. Trying alternative.' % (obj.pid, dsid))
            extra_args = ['-s', 'poly2bitmap']
            pdf2swf = subprocess.Popen(program + default_args + extra_args, stdout=subprocess.PIPE)
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
    else:
        r = subprocess.call(program + args)
        if r != 0:
            logger.warning('PID:%s DSID:%s SWF creation failed (pdf 2swf return code:%d).' % (obj.pid, dsid, r))
        if r == 0:
            update_datastream(obj, swfid, directory+'/'+swfid, label='pdf to swf', mimeType='application/x-shockwave-flash')
    rmtree(directory, ignore_errors=True)
    return r

def create_pdf(obj, dsid, pdfid):
    logger = logging.getLogger('islandoraUtils.DSConverter.create_pdf' )
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

def create_fits(obj, dsid, derivativeid = 'FITS', args = []):
    logger = logging.getLogger('islandoraUtils.DSConverter.create_fits' )
    directory, file = get_datastream_as_file(obj, dsid, "document")
    in_file = directory + '/' + file
    out_file = directory + '/FITS.xml'
    program = ['fits', '-i', in_file, '-o', out_file]
    r = subprocess.call(program + args)
    if r != 0:
        logger.warning('PID:%s DSID:%s FITS creation failed (fits return code:%d).' % (obj.pid, dsid, r))
    if r == 0:
        update_datastream(obj, derivativeid, out_file, label='FITS Generated Image Metadata', mimeType='text/xml')
    rmtree(directory, ignore_errors=True)
    return r

def create_csv(obj, dsid = 'OBJ', derivativeid = 'CSV', args = []):
    logger = logging.getLogger('islandoraUtils.DSConverter.create_csv' )
    directory, file = get_datastream_as_file(obj, dsid, "document")
    in_file = directory + '/' + file
    process = subprocess.Popen(['xls2csv', '-x', in_file] + args, stdout=subprocess.PIPE);
    output = process.communicate()[0]
    if process.returncode != 0:
        logger.warning('PID:%s DSID:%s CSV creation failed (xls2csv return code:%d).' % (obj.pid, dsid, r))
    if process.returncode == 0:
        num_sheet = 0
        out_file = directory + '/' + 'csv.csv'
        logger.warning('Output: ' + output)
        sheets  = output.split("\f")
        for sheet in sheets:
            if len(sheet) != 0:
                logger.warning('PID:%s DSID:%s CSV create sheet: %d.' % (obj.pid, dsid, num_sheet))
                f = open(out_file, 'w')
                f.write(sheet)
                f.close()
                new_dsid =  derivativeid + '_SHEET_' + str(num_sheet) if num_sheet > 0 else derivativeid
                update_datastream(obj, new_dsid, out_file, 'CSV Generated Metadata', 'text/csv')
                num_sheet += 1
    rmtree(directory, ignore_errors=True)
    return process.returncode
