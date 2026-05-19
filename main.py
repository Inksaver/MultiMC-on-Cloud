import os
import sys 		# excecuting python.exe
import subprocess	# allows python.exe to execute a subprocess eg pip
import sqlite3
from pathlib import Path

import database         # python module in this project

try:
    import colorama

except ImportError:
    print("Trying to import colorama with sys.executable -m pip install colorama...") 
    subprocess.check_call([sys.executable, "-m", "pip", "install",  "colorama"])
    # If the library is not already installed, the program will attempt to install it using python -m pip install colorama
finally:
    import colorama # Try importing the library again. May need to re-start the program


from colorama import Fore, Back, Style			# use Fore.RED to change foreground colour to RED

if os.name == "nt":
    from colorama import just_fix_windows_console	# see https://pypi.org/project/colorama/ for instructions
    just_fix_windows_console()				# initialise colorama

# assume located in  Dropbox/multimc
# determine os version. os.name = "posix" or "nt"

def clear():
    ''' clears console using appropriate method for current platform'''
    Back.BLACK
    if os.name == 'nt':					# any version of Windows
        os.system('cls')
    else:
        os.system('clear')
        
def get_config_java_path(line, value):
    ''' creates a line ready to insert into a .cfg file  '''
    if line == "":	            # empty line 
        return line
    parts = line.split('=')         # eg [name, 1.12.2]
    if parts[0] == "JavaPath":
        return f"JavaPath={value}" 
    
    return line
    

def get_file_data(config_file, with_name):
    ''' get the game name, path to java library and the os that path refers to '''
    # local functions to get_file_data()
    def get_name(line):
        ''' parse a line of text to find "name=" '''
        if line == "":	            # empty line 
            return ""
        
        parts = line.split('=')         # eg [name, 1.12.2]
        if parts[0] == "name":
            return parts[1] 
        
        return ""                       # default return value    
    
    def get_java_path(line):
        ''' parse a line of text to find "JavaPath=" and the os it refers to '''
        if line == "":	            # empty line 
            return "", ""
        
        parts = line.split('=')         # eg [name, 1.12.2]
        if parts[0] == "JavaPath":
            if '.exe' in parts[1]:
                return parts[1], "nt"
            else:
                return parts[1], "posix"
            
        return "", ""                   # default return value    
    
    
    java_path = ""
    os_type = ""
    name = ""
    file = open(config_file, 'r')
    lines = [line.rstrip() for line in file] 	            # remove newline characters
    for line in lines:
        if java_path == "":                                 # not yet discovered
            java_path, os_type = get_java_path(line)
        else:
            if not with_name:
                file.close()
                return java_path, os_type
        
        if name == "" and with_name:
            name = get_name(line)
        
    file.close()
    
    return java_path, os_type, name

def get_db_record(name, os_type, java_path):
    '''
    see if name exists in database under linuxPath or WindowsPath as appropriate for os
    java_path and os_type has been obtained from config file
    '''
    
    update_config = False                   # set default config unchanged
    update_db = False                       # set default database record unchanged
    record_id = -1                          # set default to no valid record found
    db_nt_path = ""                         # set default windows java path
    db_posix_path = ""                      # set default linux java path
    data = database.find_row(name)          # returns (id, name, javaWindows, javaLinux) in a tuple
    if data == []:                          # no record found. 
        update_db = True                    # returns -1, False, True, "",""
    else:                                   # record found. May need updating eg [(1, '1.12.2', '', 'pathname')]
        record_id = data[0][0]              # record auto-index value
        db_nt_path = data[0][2]
        db_posix_path = data[0][3]        
        if os.name == "nt":                 # running on Windows
            if os_type == "nt":             # config file already has windows path. check if it has changed
                if db_nt_path != java_path: # path does not match. Assume user has changed it in game settings
                    update_db = True
            else:                           # config file has linux path
                update_config = True        # update the config path to Windows
        elif os.name == "posix":            # running on linux
            if os_type == "posix":          # config file already has linux path. check if it has changed
                if db_posix_path != java_path: # path does not match. Assume user has changed it in game settings
                    update_db = True
            else:                           # config file has Windows path
                update_config = True        # update the config path to Linux 
                
    # return id, ?update config, ? update db, windows javaPath, linux javaPath
    return record_id, update_config, update_db, db_nt_path, db_posix_path

def update_instance(config_file):
    ''' parse the .cfg file of each game instance, compare with database and update as required '''
    if os.path.isfile(config_file):
        #print(f"{Fore.LIGHTYELLOW_EX}{config_file}")
        file = open(config_file, 'r')
        lines = [line.rstrip() for line in file] 			# remove newline characters
        # contents now in a list, with \n stripped from the end of each line
        '''
        look for these lines:
        eg JavaPath=/home/inksaver-server/Dropbox/multimc/java/linux/legacy/jre-legacy/bin/java
        (line ends with java = linux, line ends with javaw.exe = windows)
        eg name=1.12.2
        '''
        config_java_path, os_type, name = get_file_data(config_file, True) # get javaPath, os_type of the path and name from the config file
                
        # game name, javaPath and os_type now collected
        # see if name exists in database under linuxPath or WindowsPath as appropriate for os        
        record_id, update_config, update_db, nt_path, posix_path = get_db_record(name, os_type, config_java_path)
        java_path = posix_path 
        
        if os.name == "nt":                                     # currently running on Windows
            java_path = nt_path                                 # set javaPath to windows value in database        # set javaPath to linux version by default        
        
        if java_path == "":
            print (f"{Fore.LIGHTRED_EX}{name} does not have a java path for this os")
        else:
            if update_db:
                # change value of appropriate field 
                print (f"{Fore.LIGHTCYAN_EX}Updating database {name} javaPath from {Fore.LIGHTRED_EX}{config_java_path} to {Fore.LIGHTYELLOW_EX}{java_path}")
                update_record(name, os_type, record_id, java_path.strip())
                               
            if update_config:
                # write a new file based on original, but with new value for javaPath
                print (f"{Fore.LIGHTCYAN_EX}Updating {name} config file: javaPath from {Fore.LIGHTRED_EX}{config_java_path} to {Fore.LIGHTYELLOW_EX}{java_path}")
                write_config(config_file, lines, java_path.strip())
            

def update_settings():
    '''
    check current multimc.cfg. eg Windows uses javaw.exe:
    JavaPath=java/windows/epsilon/java-runtime-epsilon/bin/javaw.exe
    this path will be empty when multimc(/.exe) is first started
    update database entry for "multimc.cfg"
    '''
    print (f"{Fore.LIGHTGREEN_EX}Checking program settings..")
    config_file = "../multimc.cfg"
    file = open(config_file, 'r')
    lines = [line.rstrip() for line in file] 			# remove newline characters    
    java_path, os_type = get_file_data(config_file, False) # get javaPath and os_type of the path from the config file
    # javaPath could still be empty
    if java_path == "":                                     # os_type is not known either
        print (f"{Fore.LIGHTRED_EX}mulimc.cfg current javaPath is empty!")
    else:
        print (f"{Fore.LIGHTCYAN_EX}mulimc.cfg current javaPath: {java_path}")
           
    # return id, ?update config, ?update db, windows javaPath, linux javaPath
    record_id, update_config, update_db, nt_path, posix_path = get_db_record("multimc.cfg", os_type, java_path)
    java_path = posix_path                                  # set javaPath to linux version by default
    if os.name == "nt":                                     # currently running on Windows
        java_path = nt_path                                 # set javaPath to windows value in database
    
    if update_db:                                           # database needs updating
        print (f"{Fore.LIGHTCYAN_EX}Updating database multimc.cfg javaPath")
        update_record("multimc.cfg", os_type, record_id, java_path)

                
    if update_config and java_path != "":
        print (f"{Fore.LIGHTCYAN_EX}Updating multimc.cfg config file: javaPath")
        write_config("../multimc.cfg", lines, java_path.strip())     
    
def update_record(name, os_type, record_id, java_path):
    ''' insert or update record(s) in the database '''
    if record_id > -1 and java_path != "":              # valid record found
        if os_type == "nt":
            database.update_row(record_id, "javaWindows", java_path.strip())
        elif os_type == "posix":
            database.update_row(record_id, "javaLinux", java_path.strip())  
            
    else:                                               # no record for name eg multimc.cfg or 1.7.10
        if os_type == "nt":                             # add java_path for windows
            database.insert_row("game", ["name", "javaWindows", "javaLinux"], [name, java_path, ""])
        elif os_type == "posix":                        # add java_path for linux
            database.insert_row("game", ["name", "javaWindows", "javaLinux"], [name, "", java_path])
        else:                                           # os_type not known so use empty paths for both
            database.insert_row("game", ["name", "javaWindows", "javaLinux"], [name,"",""])    

    
def open_database(db_name):
    ''' open/create sqlite database '''
    print(f"{ Style.BRIGHT}{Fore.LIGHTGREEN_EX}Checking for {Fore.LIGHTYELLOW_EX}java paths database...") 
    
    if not os.path.isfile(db_name):
        print(f"{Fore.LIGHTGREEN_EX}Creating sqlite database {Fore.LIGHTYELLOW_EX}{db_name}...") 
        database.create(db_name)
        
    database.open(db_name)
    
    if database.conn == None:
        print(f"{Fore.LIGHTRED_EX}Unable to connect to database{Fore.RESET}")
        return False
    
    return True
        
def write_config(config_file, lines, java_path):
    ''' original file contents have been modified in a list of lines. Write the list back to a file'''
    with open(config_file, 'w+') as f:                      # open file    
        for line in lines:
            line = get_config_java_path(line, java_path)
            f.write(f"{line}\n")                            # write back to file
        
        print(f"{Fore.LIGHTYELLOW_EX}{config_file} updated")
    
    f.close()                                               # close the file            

def main():    
    ''' central control '''
    db_name = "javapath.db"
    if open_database(db_name):   
        update_settings()
        
        # iterate path Dropbox/multimc/instances, ignore _LAUNCHER_TEMP and instgroups.json
        instance_path = Path("../instances")
        print (f"{Fore.LIGHTGREEN_EX}Iterating game instances...")
        
        # Iterate through the contents of "instances"
        for item in instance_path.iterdir():
            if item.is_dir():
                config_file = os.path.join(item, "instance.cfg")
                update_instance(config_file)
                
        '''
        attempts here to run multimc and close this script
        nothing works so far, as closing the terminal closes multimc
        '''
        #if os.name == "nt":
            #subprocess.run(["../MultiMC.exe"], shell=False, capture_output=False)
            #os.startfile("..\MultiMC.exe") # windows only
        #else: 
            #subprocess.run(["../MultiMC"])
            #subprocess.Popen("../MultiMC") 
            #make sure a .desktop shortcut is present
            #subprocess.run(["../MultiMC.desktop"])
            
            
        print(f"{Fore.LIGHTYELLOW_EX}\nStart MultiMC from shortcut")
                         
main()  

input(f"{Fore.RESET}\nEnter to quit")