import json, traceback


import image


def offlinemain():
    
    option = [
        "position summary",         # passed
        "fastest lap",              # standby
        "lap time",                 # passed
        "tyre wear",                # passed
        "telemetry",                # waiting for database update
    ]

    while True:
        try:
            print("Welcome to AFR telemetry graph app")
            print()
            for i in range(0, len(option)):
                print(f'{i+1}. {option[i]}')
            print("type \"other\" for other more graph")
            print()
            print("0. exit")
            print()
            choice = input("your choice: ")

            if choice == "1" or choice.replace(" ","").lower() == "position":
                image.getPositionImage()
                input("press enter back to main menu......")
                print()



            if choice == "2" or choice.replace(" ","").lower() == "fastestlap":
                image.getFastestlapImage()
                input("press enter back to main menu......")
                print()



            elif choice == "3" or choice.replace(" ","").lower() == "laptime":
                image.getLaptimeImage()
                input("press enter back to main menu......")
                print()



            elif choice == "4" or choice.replace(" ","").lower() == "tyrewear":
                image.getTyrewearImage()
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
    offlinemain()