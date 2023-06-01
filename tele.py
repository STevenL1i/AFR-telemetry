import json, traceback
from datetime import datetime

import dbconnect
import mysql.connector

import data



def getSessionID(db:mysql.connector.MySQLConnection):
    cursor = db.cursor()

    while True:
        datetimestr = input("session date until (format YYYY-MM-DD HH:MM:SS)\n(leave blank to use current time): ")
        if datetimestr == "q" or datetimestr == "Q":
            return None

        queryNum = input("Number of session: ")
        if queryNum == "q" or queryNum == "Q":
            return None
        
        try:
            if datetimestr.replace(" ", "") == "":
                datetimestr = datetime.today().strftime("%Y-%m-%d %H:%M:%S")
            
            timestamp_check = datetime.strptime(datetimestr, "%Y-%m-%d %H:%M:%S")
            queryNum = int(queryNum)
            break

        except ValueError as e:
            if str(e).find("does not match format '%Y-%m-%d %H:%M:%S'") != -1:
                input("date format error, press enter to retry......\n")
            elif str(e).find("invalid literal for int() with base 10") != -1:
                test = input("Press enter to retry, Enter \"q\" to quit......")
                if test == 'q' or test == "q":
                    return -1
            else:
                print(str(e))
            
            print()
        

    query = f'SELECT beginUnixTime, beginTime, packetFormat, \
                     gameMajorVersion, gameMinorVersion, \
                     ipString, ipComeFrom, ipOwner \
            FROM SessionList \
                JOIN IpList ON SessionList.ipDecimal = IpList.ipDecimal \
            WHERE beginTime <= "{datetimestr}" \
            ORDER BY beginTime DESC \
            LIMIT {queryNum};'
    # beginUnixTime - sessionUID is one to one binding
    # but in other table session is identified by beginUnixTime
    # so here get beginUnixTime as sessionUID in data fetching
    cursor.execute(query)
    result = cursor.fetchall()

    # print header first
    print(f'Session data from previous query')
    print(f'{"Session ID":<20}{"Session time":<25}{"Data Ver.":<12}{"Game Ver.":<12}{"SourceIP":<18}{"IPLocation":<20}{"IPOwner":<15}')

    for i in range(len(result)-1, -1, -1):
        session = result[i]
        gamever = f'{session[3]}.{session[4]}'
        ipinfo = json.loads(session[6])["data"][0]
        print(f'{session[0]:<20}{session[1].strftime("%Y-%m-%d %H:%M:%S"):<25}{session[2]:<12}{gamever:<12}{session[5]:<18}{ipinfo["location"]:<12}{session[7]:<15}')











def main():
    db = dbconnect.connect_with_conf("server.json", "db")
    
    option = [
        "recent session id",        # passed
        "session lapdata",          # passed
        "telemetry data",           # waiting for database update
        "final classification",     # passed
        "fetch all data",           # passed
    ]

    while True:
        try:
            print("Welcome to AFR telemetry data center")
            print()
            for i in range(0, len(option)):
                print(f'{i+1}. {option[i]}')
            print("type \"other\" for other more data")
            print()
            print("0. exit")
            print()
            choice = input("your choice: ")

            if choice == "1" or choice.replace(" ","").lower() == "sessiondata" \
                             or choice.replace(" ","").lower() == "sessionid":
                getSessionID(db)
                input("press enter back to main menu......")
                print()



            elif choice == "2" or choice.replace(" ","").lower() == "lapdata" \
                               or choice.replace(" ","").lower() == "laptime":
                data.getLapdata(db)
                input("press enter back to main menu......")
                print()

            

            elif choice == "3" or choice.replace(" ","").lower() == "teledata" \
                               or choice.replace(" ","").lower() == "telemetry":

                input("press enter back to main menu......")
                print()



            elif choice == "4" or choice.replace(" ","").lower() == "fcdata" \
                               or choice.replace(" ","").lower() == "finalclass":
                data.getFinalClassification(db)
                input("press enter back to main menu......")
                print()



            elif choice.replace(" ","").lower() == "rddata" \
              or choice.replace(" ","").lower() == "racedirector":
                data.getRaceDirector(db)
                input("press enter back to main menu......")
                print()



            elif choice.replace(" ","").lower() == "posdata" \
              or choice.replace(" ","").lower() == "position":
                data.getPosdata(db)
                input("press enter back to main menu......")
                print()



            elif choice.replace(" ","").lower() == "tyrewear":
                data.getTyreweardata(db)
                input("press enter back to main menu......")
                print()


            
            elif choice.replace(" ","").lower() == "tyretemp":
                data.getTyretempdata(db)
                input("press enter back to main menu......")
                print()



            elif choice == "5" or choice.replace(" ","").lower() == "alldata":
                # qualiying
                print("please enter qualiying session id")
                sessionid1, sessionid2 = data.asksessionid()
                if sessionid1 == None or sessionid2 == None:
                    print("no or error session id")
                    input("press enter back to main menu......")
                    continue

                ipdec1 = data.checkIPsrc(db, sessionid2)
                if ipdec1 == None:
                    print("No/Wrong IP source selected......")
                    return None

                # race
                print("please enter race session id")
                sessionid3, sessionid4 = data.asksessionid()
                if sessionid3 == None or sessionid4 == None:
                    print("no or error session id")
                    input("press enter back to main menu......")
                    continue

                ipdec2 = data.checkIPsrc(db, sessionid4)
                if ipdec2 == None:
                    print("No/Wrong IP source selected......")
                    return None

                # quali part
                data.getLapdata(db, sessionid1, sessionid2, ipdec1)
                data.getTeledata(db, sessionid1, sessionid2, ipdec1)
                data.getTyretempdata(db, sessionid1, sessionid2, ipdec1)
                data.getWeatherReport(db, sessionid1, sessionid2, ipdec1)
                data.getFinalClassification(db, sessionid1, sessionid2, ipdec1)

                # race part
                data.getLapdata(db, sessionid3, sessionid4, ipdec2)
                data.getTeledata(db, sessionid3, sessionid4, ipdec2)
                data.getTyretempdata(db, sessionid3, sessionid4, ipdec2)
                data.getTyreweardata(db, sessionid3, sessionid4, ipdec2)
                data.getFinalClassification(db, sessionid3, sessionid4, ipdec2)
                data.getPosdata(db, sessionid3, sessionid4, ipdec2)


                input("press enter back to main menu......")
                print()
            
            
            
            elif choice == "deldata":
                data.deleteSessionData(db)
                input("press enter back to main menu......")
                print()

            
            elif choice.replace(" ", "").lower() == "other":
                print()
                print(f'{"option":<25}{"data descriptions":<50}\n')
                print(f'{"sessionid":<25}{"Get sessionid on given time and amount":<50}')
                print(f'{"laptime":<25}{"Get lap time data of given session":<50}')
                print(f'{"telemetry":<25}{"Get telemetry data of given session":<50}')
                print(f'{"position":<25}{"Get race position data of given session":<50}')
                print(f'{"tyrewear":<25}{"Get tyre wear data of given session":<50}')
                print(f'{"tyretemp":<25}{"Get tyre temperature data of given session":<50}')

                print(f'{"finalclass":<25}{"Get final classification of given session":<50}')
                print(f'{"racedirector":<25}{"Get race director data of given session":<50}')
                print(f'{"weather":<25}{"Get weather report data of given session":<50}')

                print(f'{"alldata":<25}{"Get all data of given session":<50}')
                
                print()
                input("press enter back to main menu......")
                print()


            elif choice == "0" or choice.replace(" ","").lower() == "exit" \
                               or choice.replace(" ","").lower() == "quit":
                input("press enter to exit......")
                db.close()
                exit(0)
    

        except Exception as e:
            print(str(e) + "\n")
            print(traceback.format_exc() + "\n\n")
            print("please contact administrator to address this issue")
            input("press enter back to main menu......")



if __name__ == "__main__":
    main()

    # ------ testing use case ------ #
    # getSessionID(dbconnect.connect_with_conf("server.json", "db"))
