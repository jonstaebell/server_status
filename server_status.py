import subprocess, configparser, sys, os, requests, time
from discord_webhook import DiscordWebhook

def main():
    config_file = sys.argv[0].replace(".py", ".ini") # config file is program name with .py replaced by .ini
    err_file_path = sys.argv[0].replace(".py", ".err") # err file is program name with .py replaced by .err
    params = get_config(config_file) # get program parameters from config file
    err_list = "" # list of servers that are not running

    if params != {}:
        for element in params['server_dict']: # params['server_dict'] is dictionary of ip addresses and server names
            status = get_server_status(element) # get result of pinging each ip address
            name = params['server_dict'][element] # name is server name of corresponding ip address
            print (f"\033[32m{name} is running.\033[0m " if status else f"\033[31m{name} is not running.\033[0m ")
            if not status:
                err_list += name + " " # err_list is a list of all servers in error

        if err_list == "": # all servers are running, so
            # delete contents of error file by writing empty string
            with open(err_file_path, 'a+'):
                os.utime(err_file_path, None) # touch the file first, to create it if it doesn't exist
            _ = write_err(err_file_path, "") # erase contents, if any
        else:
            # if the new_alarm function says the error list has changed or snooze time has elapsed
            # then call the webhook
            if new_alarm(params['snooze_time'], err_file_path, err_list):
                call_webhook(params['webhook_url'], "servers not running on " + os.uname()[1] + ": " + err_list)


def get_config(config_file):
    # return paramaters from configuration file
    #
    param_dict = {}
    param_dict['server_dict'] = {}
    try:
        Config = configparser.ConfigParser()
        Config.read(config_file)
        server_addr = Config.get('required', 'server_addr').split()
        server_name = Config.get('required', 'server_name').split()
        new_dict = {}
        if len(server_addr) != len(server_name): # make sure number of ip addresses and server names are equal
            raise Exception("Lengths of server addresses and names are not equal") 
        for i in range(0,len(server_addr)): # build dictionary for ip_addr as key and server_name as value
            new_dict[server_addr[i]] = server_name[i]
        param_dict["server_dict"] = new_dict # add ip_addr:server_name dictionary as parameter to be returned
        param_dict["webhook_url"] = Config.get('required', 'webhook_url')
        param_dict["snooze_time"] = int(Config.get('required', 'snooze_time'))
    except Exception as e:
        print (f"invalid config file {config_file}: {e}")
        return {} # return empty list on exceptions
    return param_dict

def get_server_status(ip_addr):
   # Pings an IP address
   # returns True if the server is accessable, false if not
   #
    pingresponse = subprocess.call("ping -c 1 %s" % ip_addr,
        shell=True,
        stdout=open('/dev/null', 'w'),
        stderr=subprocess.STDOUT)
    return int(pingresponse) == 0

def write_err(err_file_path, err):
    # reads content of error file and compares the error parameter to the contents of the file
    # if the error and file contents are the same, returns False
    # if the error and file contents differ, writes the new error to the file and returns True
    with open(err_file_path, 'r+') as file:
        old_err = file.read()
        if old_err != err:
            file.seek(0)
            file.write(err) # write new error message
            file.truncate()
            change = True 
        else:
            change = False
        file.close()
    return change

def call_webhook(webhook_url, output_message): 
    # checks the webhook_url parameter, and if present, uses it to send webhook to Discord
    #
    if webhook_url != "": # if url provided, notify Discord to add alert 
        program_name, _ = os.path.splitext(os.path.basename(sys.argv[0])) # remove path and extension from current program name
        webhook = DiscordWebhook(url=webhook_url, content=f"{program_name}: {output_message}")
        response = webhook.execute()
        try:
            response.raise_for_status()
        except requests.exceptions.HTTPError as err:
            print("Error in trying to use Discord Webhook", err)

def new_alarm (snooze_time, file_path, err_list):
    # checks the file used to track when the last alarm occured, and
    # returns True if it's recent, False if not
    #
    try:
        # if time since last modified is greater than snooze time, return True
        create_alarm = (time.time() - os.path.getmtime(file_path)) > snooze_time
    except FileNotFoundError:
        create_alarm = True # file doesn't exist so need to create an alarm

    if create_alarm:
        # touch file to update modification time and create if it doesn't exist
        with open(file_path, 'a'):
            os.utime(file_path, None)
    
    # return true if create_alarm indicates enough time has elapsed
    # OR if write_err indicates that the error list has changed in the file
    return create_alarm or write_err(file_path, err_list)

if __name__ == "__main__":
    main()
