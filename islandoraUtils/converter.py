'''
Created on Apr 5, 2011

@author: William Panting
@dependancies: Kakadu, ImageMagick, ABBYY CLI

This is a Library that will make file conversions and manipulations like OCR using Python easier. 
Primarily it will use Kakadu and ABBYY
but it will fall back on ImageMagick if Kakadu fails and for some conversions Kakadu does not support.

Used scripts created by Jonathan Green as the starting piont.
Please make sure that the output directory already exists.

TODO: make recursive option
TODO: handle output directory creation
TODO: add more functions
TODO: add video support
TODO: add open office word doc conversions
'''
import logging, subprocess, os
'''
This is a collection of methods that converts various file formats to others.
We use 'convert' due to lack of Kakadu license

@param inPath: source file or dir
@param outPath: destination file or dir
@param kakaduOpts: a list of options or a string 'default'
@param imageMagicOpts: a list of options or a string 'default'  
'''
def tif_to_jp2(inPath,outPath,kakaduOpts=None,imageMagicOpts=None,*extraArgs):
    
    #error checking, does not take TN
    if checkStd(inPath,outPath,extraArgs,kakaduOpts,imageMagicOpts)==False:
        return False
    if kakaduOpts=='TN' or imageMagicOpts=='TN':
        logging.error('This function tif_to_jp2 does not accept the \'TN\' keyword')
        return False
    
    #determine the output directory for the tempfile and for if there are multiple output files due to a directory batch
    #put directory not created error handle here'''
    if os.path.isdir(outPath)==False: #outPath is a file path
        outDirectory,fileNameOut=os.path.split(outPath)
        fileList=(fileNameOut)
    else:#is a driectory
        outDirectory=outPath
    tmpFilePath=os.path.join(outDirectory,'uncompressed.tiff')
    #create list of files to be converted
    if os.path.isdir(inPath)==False:
        inDirectory, fileListStr=os.path.split(inPath)
        fileList=[fileListStr]
    else:
        inDirectory=inPath
        fileList=os.listdir(inPath)#get files in the dir
        for path in os.listdir(inPath):
            pathLength=len(path)
            #remove non tiff entries
            if path[(pathLength-4):pathLength]!='.tif' and path[(pathLength-5):pathLength]!='.tiff' :
                fileList.remove(path)
    
    
    for fileName in fileList:
        
        #if fileNameOut was not in outPath make one up
        if os.path.isdir(outPath)==True:
            fileNameOut=fileName[0:fileName.rindex('.')]+'.jp2'
        filePathIn=os.path.join(inDirectory,fileName)
        filePathOut=os.path.join(outDirectory,fileNameOut)
        #use convert because of lack of kakadu license means we can't convert a compressed tif
        r = subprocess.call(["convert", filePathIn, '+compress', tmpFilePath])
        if r != 0:
            logging.warning('JP2 creation failed (convert return code:%d for file input %s).' % ( r, filePathIn))
            
            
        #prep Kakadu call
        if kakaduOpts!='default':
            kakaduCall=("kdu_compress", "-i", tmpFilePath,"-o", filePathOut)
            kakaduCall.extend(kakaduOpts)
            
        else:
            kakaduCall=["kdu_compress", "-i", tmpFilePath,\
          "-o", filePathOut,\
          "-rate", "0.5", "Clayers=1", "Clevels=7",\
          "Cprecincts={256,256},{256,256},{256,256},{128,128},{128,128},{64,64},{64,64},{32,32},{16,16}",\
          "Corder=RPCL", "ORGgen_plt=yes", "ORGtparts=R", "Cblk={32,32}", "Cuse_sop=yes"]      
        #make Kakadu call
        r = subprocess.call(kakaduCall)
    
       
        #if Kakadu fails use less powerful Imagemagic on origional file
        if r != 0:
            logging.warning('JP2 creation failed. Trying alternative (kdu_compress return code:%d).' % (r) )
           
            #prep image magic call
            if imageMagicOpts!='default':
                imageMagicCall=("convert", filePathIn)
                imageMagicCall.extend(imageMagicOpts)
                imageMagicCall.append(filePathOut)
            else:
                imageMagicCall=["convert", filePathIn, '-compress', 'JPEG2000', '-quality', '50%', filePathOut]
            #make image magic call  
            r = subprocess.call(imageMagicCall)
            if r != 0:
                logging.warning('JP2 creation failed (convert return code:%d for file input %s).' % ( r, filePathIn))
    
        if r == 0:
            logging.info('File converted: %s'% (filePathOut))
        
        #kill the temp file if it exists
        if os.path.exists(tmpFilePath):
            os.remove(tmpFilePath)
        
    return True


'''
ABBYY OCR CLI Command Line Tool support

@param: inPath: source file or dir
@param: outPath: destination file or dir
@param: inputOpts: the ABBYY command line options not associated with a specific file output tyep, can be None
@param: fileTypeOpts: 1. a dictionary where the key is a file output type and the vale is a string 'default' or list of options, or 2. a string 'default'

@return bool: true if successful false if not

TODO: make default output options for all output file types 
'''
def tif_OCR(inPath,outPath,fileTypeOpts,inputOpts=None,*extraArgs):
    '''
    #quick and dirty parameter input check
    if(isinstance(fileTypeOpts, dict)!=True and fileTypeOpts!='default')\
    or(isinstance(inputOpts, list)!=True and inputOpts!='default' and inputOpts!=None)\
    or isinstance(inPath, str)!=True \
    or isinstance(outPath, str)!=True\
    or len(extraArgs)!=0:        
        logging.error('Bad function call to tif_OCR')
        return False
  '''
        #error checking, does not take TN
    if checkStd(inPath,outPath,extraArgs,inputOpts)==False:
        return False
    if fileTypeOpts=='TN' or inputOpts=='TN':
        logging.error('This function tif_to_jp2 does not accept the \'TN\' keyword')
        return False
    #special dictionary error checking
    if isinstance(fileTypeOpts, dict)==False and fileTypeOpts!='default':
        logging.error('The fileTypeOpts must be a dictionary or the keyword \'default\'.' )
        return False
      
    #prevents the script from attempting to write multiple output files to one output file path
    if os.path.isdir(inPath)==True and os.path.isdir(outPath)!=True:
        logging.error('If the input path is a directory, so must be the output path.')
        return False
    if len(fileTypeOpts)>1 and fileTypeOpts!='default' and os.path.isdir(outPath)!=True:
        logging.error('If there is to be more than one output file then the output path must be a directory.')
        return False
        
    #determine the output directory if there are multiple output files due to a directory batch
    #put directory not created error handling here'''
    if os.path.isdir(outPath)==False:
        outDirectory,fileNameOut=os.path.split(outPath)
        fileList=(fileNameOut)
    else:#is a driectory
        outDirectory=outPath
    
    #create list of files to be converted
    if os.path.isdir(inPath)==False:
        inDirectory, fileListStr=os.path.split(inPath)
        fileList=[fileListStr]
    else:
        inDirectory=inPath
        fileList=os.listdir(inPath)#get files in the dir
        for path in fileList:
            pathLength=len(path)
            #remove non tiff entries
            if path[(pathLength-4):pathLength]!='.tif' and path[(pathLength-5):pathLength]!='.tiff' :
                fileList.remove(path)
        
    for fileName in fileList:
        #some useful vars
        absPathFileIn=os.path.join(inDirectory,fileName)
        absPathFileOutNoExt=os.path.join(outDirectory,fileName[0:fileName.rindex('.')])
        
        #reset the ABBYY call
        ABBYY_Call=['CLI']
        #input opts and input file
        if inputOpts!='default' and inputOpts!=None:
            ABBYY_Call.extend(inputOpts)
        ABBYY_Call.extend(('-if',absPathFileIn))     

        #determine output file extension, and input check
        for outputType,outputOpts in fileTypeOpts.iteritems():
            if outputType=='PDF':
                extension='.pdf'
                defaultOutPutOpts=('-pem','ImageOnText','-pfq','75')
            elif outputType=='HTML':
                extension='.html'
                defaultOutPutOpts=()
            elif outputType=='RTF':
                extension='.rtf'
                defaultOutPutOpts=()
            elif outputType=='DBF':
                extension='.dbf'
                defaultOutPutOpts=()
            elif outputType=='XML':
                extension='.xml'
                defaultOutPutOpts=()
            elif outputType=='Text':
                extension='.txt'
                defaultOutPutOpts=('-tel','-tpb','-tet','UTF8')
            elif outputType=='XLS':
                extension='.xls'
                defaultOutPutOpts=()
            else:
                logging.error('Incorrect output type specified for ABBYY CLI.')
                return 1
            #append this round of output info
            ABBYY_Call.extend(('-f',outputType))
            if outputOpts!='default':
                ABBYY_Call.extend(fileTypeOpts[outputType])
            else:
                ABBYY_Call.extend(defaultOutPutOpts)
            #append output file for this round
            ABBYY_Call.extend(('-of',absPathFileOutNoExt+extension))
        
        #make ABBYYcall
        r = subprocess.call(ABBYY_Call)
        if r != 0:
            logging.warning('JP2 creation failed (ABBYY CLI return code:%d).' % ( r))
        if r == 0:
            logging.info('File OCR\'d: %s'% (absPathFileIn))
    return True

'''
This function will use image magick to convert tifs to jpgs
@param: inPath: source file or dir
@param: outPath: destination file or dir
@param imageMagicOpts: can be 'default' 'TN' or a list of options to use

@return bool: true if successful false if not
'''
def tif_to_jpg(inPath,outPath, imageMagicOpts,*extraArgs):
    #error checking
    if checkStd(inPath,outPath,extraArgs,imageMagicOpts)==False:
        return False
    
    #determine the output directory for the tempfile and for if there are multiple output files due to a directory batch
    #put directory not created error handle here'''
    if os.path.isdir(outPath)==False: #outPath is a file path
        outDirectory,fileNameOut=os.path.split(outPath)
        fileList=(fileNameOut)
    else:#is a driectory
        outDirectory=outPath
    #create list of files to be converted
    if os.path.isdir(inPath)==False:
        inDirectory, fileListStr=os.path.split(inPath)
        fileList=[fileListStr]
    else:
        inDirectory=inPath
        fileList=os.listdir(inPath)#get files in the dir
        for path in os.listdir(inPath):
            pathLength=len(path)
            #remove non tiff entries
            if path[(pathLength-4):pathLength]!='.tif' and path[(pathLength-5):pathLength]!='.tiff' :
                fileList.remove(path)
    
    
    for fileName in fileList:
        
        #if fileNameOut was not in outPath make one up
        if os.path.isdir(outPath)==True:
            fileNameOut=fileName[0:fileName.rindex('.')]+'.jpg'
        filePathIn=os.path.join(inDirectory,fileName)
        filePathOut=os.path.join(outDirectory,fileNameOut)
        
        #create image magick call
        if imageMagicOpts=='defautl':
            imageMagicCall=["convert", filePathIn, '-compress', 'JPEG', '-quality', '50%', filePathOut]
        elif imageMagicOpts=='TN':
            imageMagicCall=["convert", filePathIn, "-thumbnail", "85x110!", "-gravity", "center", "-extent", "85x110", filePathOut]
        else:
            imageMagicCall=["convert",filePathIn]
            imageMagicCall.extend(imageMagicOpts)
            imageMagicCall.append(filePathOut)
        
        #make image magic call  
        r = subprocess.call(imageMagicCall)
        if r != 0:
            logging.warning('JPG creation failed (convert return code:%d for file input %s).' % ( r, filePathIn))
        if r == 0:
            logging.info('File converted: %s'% (filePathOut))
    return True

'''
@param: inPath: source file or dir
@param: outPath: destination file or dir

@return bool: true if successful false if not
'''
def pdf_to_swf(inPath,outPath,*extraArgs):
    '''
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
'''
    return True

'''
@param: inPath: source file or dir
@param: outPath: destination file or dir

@return bool: true if successful false if not
'''
def wav_to_ogg(inPath,outPath,*extraArgs):
    '''
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
    '''
    return True

'''
@param: inPath: source file or dir
@param: outPath: destination file or dir

@return bool: true if successful false if not
'''
def wav_to_mp3(inPath,outPath,*extraArgs):
    '''
    # We recieve a WAV file. Create a MP3
    directory, file = get_datastream_as_file(obj, dsid, "wav")
    
    # Make MP3 with lame
    r = subprocess.call(['lame', '-mm', '--cbr', '-b48', directory+'/'+file, directory+'/'+mp3id])
    if r == 0:
      update_datastream(obj, mp3id, directory+'/'+mp3id, label='compressed to mp3', mimeType='audio/mpeg')
    else:
      logging.warning('PID:%s DSID:%s MP3 creation failed (lame return code:%d).' % (obj.pid, dsid, r))

    rmtree(directory, ignore_errors=True)
    return r
    '''
    return True

'''
@param: inPath: source file or dir
@param: outPath: destination file or dir

@return bool: true if successful false if not
'''
def pdf_to_jpg(inPath,outPath,*extraArgs):
    '''
    os.system('sips -s format jpeg \"tmpfile.pdf\" -z 150 150 --out \"tmpfile.jpg\" >/dev/null')
    
    
    OR
    
    
    
    def create_thumbnail(obj, dsid, tnid):
    # We receive a file and create a jpg thumbnail
    directory, file = get_datastream_as_file(obj, dsid, "tmp")
    
    # Make a thumbnail with convert
    r = subprocess.call(['convert', directory+'/'+file+'[0]', '-thumbnail', \
         '%sx%s' % (tn_size[0], tn_size[1]), directory+'/'+tnid])
   
    if r == 0:
        update_datastream(obj, tnid, directory+'/'+tnid, label='thumbnail', mimeType='image/jpeg')

        # this is necessary because we are using curl, and the library caches 
        try:
            if (obj['TN'].label.split('/')[0] != 'image'): 
                if(obj[dsid].mimeType.split('/')[0] == 'image'):
                    update_datastream(obj, 'TN', directory+'/'+tnid, label=obj[dsid].mimeType, mimeType='image/jpeg')
        except FedoraConnectionException:
            update_datastream(obj, 'TN', directory+'/'+tnid, label=obj[dsid].mimeType, mimeType='image/jpeg')
    else :
        logging.warning('PID:%s DSID:%s Thumbnail creation failed (return code:%d).' % (obj.pid, dsid, r))
    '''
    return True

'''
collection of helper functions used by the API functions
'''

'''
Does some standardized error checking on the input and output path arguments
@param pathIn: input path to check
@param pathOut: output path to check
@return bool: return false if the arguments are not valid, true if they are
'''
def checkPaths(pathIn, pathOut):
    #make sure that the indicated paths are valid
    if os.path.lexists(pathIn)==False:
        logging.error('The indicated input path is not valid: '+pathIn)
        return False
    
    if os.path.isdir(pathOut):
        return True
    elif os.path.isfile(pathOut):
        logging.error('If the output path is a file it can not already exist: '+ pathOut)
        return False
    elif os.path.lexists(os.path.dirname(pathOut))!=True:
        logging.error('The output path is invalid: '+pathOut)
        return False
        
        
    #make sure that if the input path is a directory that the output path is also a directory
    if os.path.isdir(pathIn)==True and os.path.isdir(pathOut)==False:
        logging.error('If the input path is a directory then so must be the output directory')
        return False
    
    return True

'''
Does some standardized checking on command line option arguments
@param optsIn: option set to check
@return bool: return false if the arguments are not valid, true if they are
'''
def checkOpts(optsIn):
    if isinstance(optsIn, list)==False and optsIn!='default' and optsIn!='TN':
        logging.error('CommandLine arguments must be lists or a known keyword like \'TN\' or \'default\'' )
        return False
    return True

'''
Does a standard check to see if too many args was passed in
@param args: list holding the *args to be checked
@return bool: return false if the arguments are not valid, true if they are
'''
def checkExtraArgs(args):
    if len(args)>0:
        logging.error('Too many arguments supplied:'+args)
        return False
    return True

'''
Wrapper function that calls all standard error checking
@param pathIn: input path to check
@param pathOut: output path to check
@param args: list holding the *args to be checked
@param optsIn: option set to check
@return bool: return false if the arguments are not valid, true if they are
'''
def checkStd(pathIn,pathOut,args,*opts):
    if checkPaths(pathIn,pathOut)==False:
        return False
    if checkExtraArgs(args)==False:
        return False
    for optSet in opts:
        if checkOpts(optSet)==False:
            return False
    return True