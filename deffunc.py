import os, platform
import json
import mysql.connector

def get_sysinfo():
    sys = platform.uname()
    info = "PC System info: \n"
    info += f'    System: {sys.system}\n'
    info += f'    Node: {sys.node}\n'
    info += f'    Version: {sys.version}\n'
    info += f'    Machine: {sys.machine}\n'
    info += f'    Processor: {sys.processor}\n'

    return info


def logging(filepath, msg:str="", end:str="\n"):
    logf = open(filepath, "a")
    logf.write(msg + end)
    logf.close()


def get_key(my_dict, val):
    for key, value in my_dict.items():
        if val == value:
            return key
    return "key doesnt exist"


def second_To_laptime(laptime_sec:float):
    return f'{int(laptime_sec//60)}:{laptime_sec - int(laptime_sec//60)*60:.3f}'


def laptime_To_second(laptime:str):
    minute = int(laptime[:laptime.find(":")])
    second = float(laptime[laptime.find(":")+1:])

    return minute*60 + second


def delimiter_string(string:str, length:int):
    outputString = f' {string} '
    while len(outputString) < length:
        outputString = "-" + outputString + "-"
    
    outputString = outputString[:length]
    return outputString


def get_LPdict(LPsettings:dict) -> dict:
    LPdict = {}
    allkey = LPsettings.keys()
    allkey_list = []
    for key in allkey:
        allkey_list.append(int(key))
    allkey_list.sort()
    for i in range(0,len(allkey_list)):
        try:
            for j in range(int(allkey_list[i]), int(allkey_list[i+1])):
                LPdict[j] = LPsettings[str(allkey_list[i])]
        except IndexError:
            LPdict[j+1] = LPsettings[str(allkey_list[i-1])]
    
    return LPdict


def asksessionid() -> tuple[int, int]:
    sessionid1 = input("please enter session id 1: ")
    if sessionid1 == "q" or sessionid1 == "Q":
        return 'Nosession', 'Nosession'
    sessionid2 = input("please enter session id 2: ")
    if sessionid2 == "q" or sessionid2 == "Q":
        return 'Nosession', 'Nosession'
    
    if sessionid2.replace(" ", "") == "":
        sessionid2 = sessionid1

    try:
        return int(sessionid1), int(sessionid2)
    except ValueError as e:
        return None, None


def checkIPsrc(db:mysql.connector.MySQLConnection, sessionid:int):
    cursor = db.cursor()

    # check whether multiple ip source of the session
    query = f'SELECT beginUnixTime, beginTime, IpList.ipDecimal, \
                     ipString, ipComeFrom, ipOwner \
            FROM SessionList \
                JOIN IpList ON SessionList.ipDecimal = IpList.ipDecimal \
            WHERE beginUnixTime = "{sessionid}";'
    cursor.execute(query)
    result = cursor.fetchall()

    if len(result) == 1:
        return result[0][2]
    

    print(f'Multiple ip source detected\nSession ID: {sessionid}\n')
    print(f'{"option":<8}{"SourceIP":<18}{"IPLocation":<20}{"IPOwner":<15}')
    for i in range(0, len(result)):
        session = result[i]
        ipinfo = json.loads(session[4])["data"][0]
        print(f'{i+1:<8}{session[3]:<18}{ipinfo["location"]:<12}{session[5]:<15}')
    
    print()
    choice = input("Please choose an IP source: ")
    print()
    try:
        choice = int(choice)-1
        if choice < 0:
            choice = len(result)
        return result[choice][2]
    except (ValueError, IndexError):
        return None
    
