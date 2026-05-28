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

java_installs_linux = []                                # names of all java installs in linux eg runtime-epsilon
java_installs_windows = []                              # names of all java installs in windows eg java-runtime-epsilon
# assume this file located in  Dropbox/multimc/ConfigSwitcher

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
    
def get_file_data(config_file):
    ''' get the config_file as a list of lines, game name, path to java library and the os that path refers to '''
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
        if line == "":	                # empty line 
            return "", ""
        
        if line == "java":              #default setting
            return "java", ""
        
        parts = line.split('=')         # eg [name, 1.12.2]
        if parts[0] == "JavaPath":
            if '.exe' in parts[1]:
                return parts[1], "nt"
            else:
                return parts[1], "posix"
            
        return "", ""                   # default return value    
    
    
    config_java_path = ""
    config_os_type = ""
    name = ""
    file = open(config_file, 'r')
    lines = [line.rstrip() for line in file] 	                    # remove newline characters
    for line in lines:
        if config_java_path == "":                                  # not yet discovered
            config_java_path, config_os_type = get_java_path(line)  # use local function
        
        if name == "":
            name = get_name(line)
        
    file.close()
    
    if config_java_path == "" or config_java_path == "java":
        if os.name == "nt":
            config_java_path = get_java_path("windows", config_file)
            config_os_type = "nt"
        else:
            config_java_path = get_java_path("linux", config_file)
            config_os_type = "posix"
    
    return lines, config_java_path, config_os_type, name

def get_db_record(name):
    ''' see if name exists in database '''
    
    record_id = -1                                      # set default to no valid record found
    db_nt_path = ""                                     # set default windows java path
    db_posix_path = ""                                  # set default linux java path
    data = database.find_row(name)                      # returns (id, name, javaWindows, javaLinux) in a tuple
    if data != []:                                      # no record found.                                              # record found. May need updating eg [(1, '1.12.2', '', 'pathname')]
        record_id = data[0][0]                          # record auto-index value
        db_nt_path = data[0][2]                         # database path for windows java
        db_posix_path = data[0][3]                      # database path for linux java      
    # return id, windows javaPath, linux javaPath
    return record_id, db_nt_path, db_posix_path

def get_java_path(os_type, name):
    ''' get user choice of java path '''
    print(f"{Fore.LIGHTRED_EX}No {os_type} java installation defined for {name}")               # Ask user for a Linux java install
    if os_type == "windows":
        response = menu(" Choose correct java install", java_installs_windows)
    else:
        response = menu(" Choose correct java install", java_installs_linux)
    
    return options[response]                    

def get_resolved_paths(name, config_os_type, config_java_path, db_nt_path, db_posix_path):
    ''' check if config  / database needs updating and return java paths for current config file and database records '''
    update_db_nt = False
    update_db_posix = False
    update_config = False    
    if os.name == "nt":                                                                                 # running on Windows
        if config_os_type == "nt":                                                                      # config file is configured for Windows
            if config_java_path != db_nt_path:                                                          # java path in config (Windows) does not match database
                update_db_nt = True
                print(f"{Fore.LIGHTRED_EX}Conflict between config file (1) and database record (2)")
                options = [config_java_path, db_nt_path]
                response = menu(" Choose correct option", options )
                db_nt_path = options[response]
        else:                                                                                           # config file is configured for Linux
            update_config = True                                                                        # need to change config file to Windows path
            if db_nt_path == "":                                                                        # Windows path not recorded
                update_db_nt = True
                db_nt_path = get_java_path("windows", name)
                                          
            config_java_path = db_nt_path                                                               # set config_java_path to Winows from database or user input
                
    else:                                                                                               # running on Linux
        if config_os_type == "posix":                                                                   # config file is configured for Linux
            if config_java_path != db_posix_path:                                                       # java path in config (Linux) does not match database
                update_db_posix = True
                print(f"{Fore.LIGHTRED_EX}Conflict between config file (1) and database record (2)")
                options = [config_java_path, db_posix_path]
                response = menu(" Choose correct option", options )
                db_posix_path = options[response]                             
        else:                                                                                           # config file is configured for Linux
            update_config = True                                                                        # need to change config file to Windows path
            if db_posix_path == "":                                                                     # Windows path not recorded
                update_db_posix = True
                db_posix_path = get_java_path("linux", name)

            config_java_path = db_posix_path                                                            # set config_java_path to Winows from database or user input  
            
    return update_db_nt, update_db_posix, update_config, config_java_path, db_nt_path, db_posix_path

def menu(title, menu_list):
    ''' displays a menu. Returns a numerical choice '''
    
    print(f"{Fore.YELLOW}{title}{Fore.CYAN}")
    for i in range(1, len(menu_list) + 1):				# makes sure menu is displayed from eg 1 to 3 for human preference rather than 0 to 2
        print(f"    {Fore.BLUE}{i} {Fore.CYAN}{menu_list[i - 1]}")	# converts back to machine readable 0 index

    while True:
        choice = input(f"{Fore.YELLOW}Enter the {Fore.BLUE}number{Fore.YELLOW} of your choice:_{Fore.MAGENTA}")
        if choice.isnumeric():						    # checks to see whether input is fully numeric, as in solely numbers (no - or .)
            choice = int(choice)					    # int won't error now since .isnumeric() passed, so convert choice to a positive integer.
            if choice > 0 and choice <= len(menu_list): # checking index fits length of list.
                return choice -1						# all checks passed, returns a value (breaks loop).
    
    

def update_instance(config_file):
    ''' 
    parse the .cfg file of each game instance, compare with database and update as required
    eg "1.7.10/instance.cfg"
    '''
    if os.path.isfile(config_file):
        '''
        look for these lines:
        eg JavaPath=/home/user/Dropbox/multimc/java/linux/legacy/jre-legacy/bin/java
        (line ends with java = linux, line ends with javaw.exe = windows)
        eg name=1.12.2
        '''
        lines, config_java_path, config_os_type, name = get_file_data(config_file) # get javaPath, config_os_type of the path and name from the config file
        record_id, db_nt_path, db_posix_path = get_db_record(name)
        update_db_nt, update_db_posix, update_config, config_java_path, db_nt_path, db_posix_path = get_resolved_paths(name, config_os_type, config_java_path, db_nt_path, db_posix_path)
        
        changes = False
        if update_db_nt:                                                                   # database needs updating
            print (f"\t{Fore.LIGHTCYAN_EX}Updating database {Fore.LIGHTYELLOW_EX}{name}{Fore.LIGHTCYAN_EX} Windows javaPath")
            update_record(name, config_os_type, record_id, db_nt_path)
            changes = True
        if update_db_posix:                                                                   # database needs updating
            print (f"\t{Fore.LIGHTCYAN_EX}Updating database {Fore.LIGHTYELLOW_EX}{name}{Fore.LIGHTCYAN_EX} Linux javaPath")
            update_record(name, config_os_type, record_id, db_posix_path)    
            changes = True
        if update_config:
            print (f"\t{Fore.LIGHTCYAN_EX}Updating {Fore.LIGHTYELLOW_EX}{name}{Fore.LIGHTCYAN_EX} config file: {Fore.LIGHTWHITE_EX}javaPath={config_java_path}")
            write_config(config_file, lines, config_java_path)
            changes = True
        if not changes:
            print (f"\t{Fore.LIGHTCYAN_EX}{name}{Fore.YELLOW}\tNo changes required")       

def update_settings():
    '''
    check current multimc.cfg. eg Windows uses javaw.exe:
    JavaPath=java/windows/java-runtime-epsilon/bin/javaw.exe
    this path will be empty when multimc(.exe) is first started
    update database entry for "multimc.cfg"
    '''
    print (f"{Fore.LIGHTGREEN_EX}Checking multimc settings..")
    config_file = os.path.join("..", "multimc.cfg") 
    lines, config_java_path, config_os_type, name = get_file_data(config_file)      # get javaPath and config_os_type of the path from the config file
    name = "multimc.cfg"
    '''
    lines = list of all lines in the config file
    config_java_path = "" or "java" or "java/windows/..
    config_os_type = "", "nt", "posix"
    
    '''
    record_id, db_nt_path, db_posix_path = get_db_record("multimc.cfg")
    update_db_nt, update_db_posix, update_config, config_java_path, db_nt_path, db_posix_path = get_resolved_paths(name, config_os_type, config_java_path, db_nt_path, db_posix_path)
    
    changes = False
    if update_db_nt:                                                                   # database needs updating
        print (f"\t{Fore.LIGHTCYAN_EX}Updating database {Fore.YELLOW}{name}{Fore.LIGHTCYAN_EX} Windows javaPath")
        update_record(name, config_os_type, record_id, db_nt_path)
        changes = True
        
    if update_db_posix:                                                                   # database needs updating
        print (f"\t{Fore.LIGHTCYAN_EX}Updating database {Fore.YELLOW}{name}{Fore.LIGHTCYAN_EX} Linux javaPath")
        update_record(name, config_os_type, record_id, db_posix_path)
        changes = True

    if update_config:
        print (f"\t{Fore.LIGHTCYAN_EX}Updating {Fore.YELLOW}{name}{Fore.LIGHTCYAN_EX} config file: {Fore.LIGHTWHITE_EX}javaPath={config_java_path}")
        write_config(config_file, lines, config_java_path)
        changes = True
        
    if not changes:
        print (f"\t{Fore.LIGHTCYAN_EX}{name}{Fore.YELLOW}\tNo changes required")
        
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
    print(f"{ Style.BRIGHT}{Fore.LIGHTGREEN_EX}Checking for {Fore.YELLOW}database...") 
    
    if not os.path.isfile(db_name):
        print(f"{Fore.LIGHTGREEN_EX}\tCreating sqlite database {Fore.YELLOW}{db_name}...") 
        database.create(db_name)
        
    database.open(db_name)
    print(f"{Style.BRIGHT}{Fore.LIGHTCYAN_EX}\tdatabase opened") 
    
    if database.conn == None:
        return False
    
    return True
        
def write_config(config_file, lines, java_path):
    ''' 
    original file contents have been modified in a list of lines. Write the list back to a file
    eg "1.7.10/instance.cfg"
    '''
    with open(config_file, 'w+') as f:                      # open file    
        for line in lines:
            line = get_config_java_path(line, java_path)
            f.write(f"{line}\n")                            # write back to file
        
        print(f"{Fore.YELLOW}{config_file} updated")
    
    f.close()                                               # close the file            

def main():    
    ''' central control '''
    
    # get lists of windows and linux java installs from multimc/java
    # populate list of java installations for windows
    instance_path = Path(os.path.join("..", "java", "windows"))
    for item in instance_path.iterdir():
        if item.is_dir():
            java_installs_windows.append(item)
            
    # populate list of java installations for linux
    instance_path = Path(os.path.join("..", "java", "linux"))
    for item in instance_path.iterdir():
        if item.is_dir():
            java_installs_linux.append(item)    
    
    if os.name == "posix" and java_installs_linux == []:
        print (f"{Fore.LIGHTRED_EX}Please add at least one java install to multimc/java/linux/")
    elif os.name == "nt" and java_installs_windows == []:
        print (f"{Fore.LIGHTRED_EX}Please add at least one java install to multimc/java/windows/")    
    else:    
        db_name = "javapath.db"                                     # database name
        if open_database(db_name):   
            update_settings()                                   # multimc.cfg is configured
        
            # iterate path Dropbox/multimc/instances, ignore _LAUNCHER_TEMP and instgroups.json
            instance_path = Path(os.path.join("..","instances"))
            print (f"{Fore.LIGHTGREEN_EX}Iterating game instances...")
            
            # Iterate through the contents of "instances"
            for item in instance_path.iterdir():
                if item.is_dir():
                    config_file = os.path.join(item, "instance.cfg")
                    update_instance(config_file)                    # eg "1.7.10/instance.cfg"
                    
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
            
            
            print(f"{Fore.YELLOW}\nStart {Fore.LIGHTRED_EX}MultiMC{Fore.YELLOW} from shortcut")
        else:                                                                       # cannot create / connect to database
            print(f"{Fore.LIGHTRED_EX}\nUnable to connect to database{Fore.RESET}")                    
                         
main()  

input(f"{Fore.RESET}\nEnter to quit")
