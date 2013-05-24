'''
    @file
        This file will hold the code to create summaries that can be used by the 
        ingester object.
    
    Created on 29/10/2012
    
    @author
        William Panting
'''

import os, csv

def summarize_directory(directory, file_name_to_write = None):
    '''
        This function will get a summary for a directory and possibly
        print it to a file in that directory.
        
        @param string directory
            The directory to write the summary for.
        @param string file_name_to_write
            The fiel to write the report to.
    '''
    
    # Gather data for report.
    paths_and_times = dict()
    for path, dirs, files in os.walk(unicode(directory)):
        for file_name in files:
            file_path = os.path.join(path, file_name)
            try:
                last_modified_time = os.path.getmtime(file_path)
                paths_and_times[file_path] = last_modified_time
            except OSError:
                # Don't add a missing file to the summary.
                pass
    
    # Write out report if a file name was provided.
    if file_name_to_write is not None:
        with open(os.path.join(directory, file_name_to_write), 'w') as report_file_handle:
            csv_writer = csv.writer(report_file_handle)
            csv_writer.writerow(['file_path', 'last_modified_date'])
            for path in paths_and_times:
                csv_writer.writerow([path.encode('utf-8'), paths_and_times[path]])
                
    return(os.path.join(directory, file_name_to_write))
