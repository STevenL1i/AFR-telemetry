import json, traceback

import dbconnect
import mysql.connector

import tele
import image

# loading settings
settingsf = open("settings.json", "r")
settings:dict = json.load(settingsf)
settingsf.close()
mode = settings["image"]["mode"]


def main(mode:str):
    if mode == "ONLINE":
        db = dbconnect.connect_with_auth(host=settings["server"],
                                         port=3306,
                                         user="telepublic",
                                         password="afr@telepublic",
                                         database="f1_2022_tele")
    
    option = [
        "recent session id",        # passed
        "position summary",         # passed
        "fastest lap",              # standby
        "lap time",                 # passed
        "tyre wear",                # passed
        #"telemetry",               # waiting for database update
    ]

    while True:
        try:
            print("Welcome to AFR telemetry graph app")
            print(f'Current mode: {mode}')
            print()
            for i in range(0, len(option)):
                print(f'{i+1}. {option[i]}')
            print("type \"other\" for other more graph")
            print()
            print("0. exit")
            print()
            choice = input("your choice: ")

            if choice == "1" or choice.replace(" ","").lower() == "sessiondata" \
                             or choice.replace(" ","").lower() == "sessionid":
                if mode == "OFFLINE":
                    print("This function is not support for OFFLINE MODE\nPlease enter ONLINE MODE for this function")
                else:
                    tele.getSessionID(db)
                input("press enter back to main menu......")
                print()



            elif choice == "2" or choice.replace(" ","").lower() == "position":
                if mode == "OFFLINE":
                    image.getPositionImage()
                else:
                    image.getPositionImage_ONLINE(db)
                input("press enter back to main menu......")
                print()



            if choice == "3" or choice.replace(" ","").lower() == "fastestlap":
                if mode == "OFFLINE":
                    image.getFastestlapImage()
                else:
                    image.getFastestlapImage_ONLINE(db)
                input("press enter back to main menu......")
                print()



            elif choice == "4" or choice.replace(" ","").lower() == "laptime":
                if mode == "OFFLINE":
                    image.getLaptimeImage()
                else:
                    image.getLaptimeImage_ONLINE(db)
                input("press enter back to main menu......")
                print()



            elif choice == "5" or choice.replace(" ","").lower() == "tyrewear":
                if mode == "OFFLINE":
                    image.getTyrewearImage()
                else:
                    image.getTyrewearImage_ONLINE(db)
                input("press enter back to main menu......")
                print()







            elif choice.replace(" ", "").lower() == "other":
                print()
                print(f'{"option":<25}{"graph descriptions":<50}\n')
                print(f'{"position":<25}{"Get race position summary of given position data"}')
                print(f'{"fastestlap":<25}{"Get fastest lap summary of given fastestlap data"}')
                print(f'{"laptime":<25}{"Get lap time comparison of given laptime data"}')
                print(f'{"tyrewear":<25}{"Get tyre wear comparison of given tyre wear data"}')
                
                print()
                input("press enter back to main menu......")
                print()
            
            elif choice == "0" or choice.replace(" ", "").lower == "exit" \
                               or choice.replace(" ", "").lower == "quit":
                input("press enter to exit......")
                exit(0)
        

        except Exception as e:
            print(str(e) + "\n")
            print(traceback.format_exc() + "\n\n")
            print("please contact administrator to address this issue")
            input("press enter back to main menu......")






if __name__ == "__main__":
    # offline mode is by default
    # use ONLINE mode only when specified in settings
    if mode == "ONLINE":
        main("ONLINE")
    else:
        main("OFFLINE")