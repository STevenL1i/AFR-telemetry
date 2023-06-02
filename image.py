import os, csv, json

import tkinter
from tkinter import filedialog

import dbconnect
import mysql.connector

import matplotlib
from matplotlib import pyplot as plt
import numpy as np

import deffunc as func


# loading settings
settingsf = open("settings.json", "r")
settings:dict = json.load(settingsf)
settingsf.close()
# check output dir correct
imageoutdir = settings["image"]["outputdir"]
os.system(f'if not exist "{imageoutdir}" mkdir "{imageoutdir}"')
if imageoutdir[-1] != "/":
    imageoutdir += "/"






################## OFFLINE Ver. Image ##################

def getPositionImage(files:tuple=None, outdir:str=None):
    # ask for input files if no inut from parameter
    if files == None:
        root = tkinter.Tk()
        root.withdraw()
        files = filedialog.askopenfilenames()

    # Input files validations
    for file in files:
        try:
            f = open(file, "r")
            reader = csv.DictReader(f)
            header = list(list(reader)[0].keys())
            if header != ["driverName", "lapNum", "position"]:
                raise KeyError
            f.close()
        except FileNotFoundError:
            print(f'File Not Found: {file}')
            return None
        except Exception:
            print(f'File Validation error: {file}')
            return None
        
    
    # get race length (number of laps)
    racelength = 0
    for file in files:
        f = open(file, "r")
        reader = csv.DictReader(f)

        for row in reader:
            if int(row.get("lapNum")) > racelength:
                racelength = int(row.get("lapNum"))
        
        f.close()
    

    # create plot
    length = settings["image"]["position"]["size"]["length"]
    height = settings["image"]["position"]["size"]["height"]
    fig, ax = plt.subplots(figsize=(length/100, height/100))
    # set axis limits
    plt.xlim(0, racelength)         # x-axis of lap number
    plt.ylim(len(files)+1, 0)       # y-axis of num of driver
    # create a twin for y-axis 
    # (as it must create after limit the axis,
    #  otherwise twin axis will not aligned)
    ax2 = ax.twinx()        # dont try to understand it, because I also don't
                            # well I suddenly understand it
                            # twinx means copying an axis making it sharing the x-axis with it,
                            # which means ax and ax2 sharing the x-axis,
                            # not copying ax's x-axis to ax2
    # set twin axis limits
    ax2.set_ylim(len(files)+1, 0)

    # create plot title
    plt.title("Race position summary\n", fontsize=36, fontweight="bold")
    # create plot label
    ax.set_title("Rank", loc="left")
    ax.set_xlabel("Lap Number")
    ax.set_ylabel("Driver")

    # set axis interval
    ax.xaxis.set_major_locator(plt.MultipleLocator(1))
    ax.yaxis.set_major_locator(plt.MultipleLocator(1))
    ax2.yaxis.set_major_locator(plt.MultipleLocator(1))


    # set axis formatter (left)
    def driver_rank(x, pos):
        # x represent a value (don't know what it means)
        # pos represent a tick value, 
        #     referring the y axis locator (starting from 0 from top)
        poscursor = pos - 2
        pos = pos - 1
        if poscursor >= 0 and poscursor < len(posstart):
            return f'{posstart[poscursor]}  {pos}'
    ax.yaxis.set_major_formatter(plt.FuncFormatter(driver_rank))

    # set axis formatter (right)
    def rank_driver(x, pos):
        # x represent a value (don't know what it means)
        # pos represent a tick value, 
        #     referring the y axis locator (starting from 0 from top)
        poscursor = pos - 2
        pos = pos - 1
        if poscursor >= 0 and poscursor < len(posfinal):
            return f'{pos}  {posfinal[poscursor]}'
    ax2.yaxis.set_major_formatter(plt.FuncFormatter(rank_driver))


    # initialize position rank
    posstart = [None] * len(files)
    posfinal = [None] * len(files)

    
    # reading position data
    for file in files:
        lap, pos = [], []
        drivername = ""

        f = open(file, "r")
        reader = csv.DictReader(f)
        for row in reader:
            drivername = row.get("driverName")
            lap.append(int(row.get("lapNum")))
            pos.append(int(row.get("position")))
        f.close()

        # mark overall position data
        posstart[pos[0]-1] = drivername
        posfinal[pos[-1]-1] = drivername

        ax.plot(lap, pos, linewidth=3)
    
    plt.grid(True)

    if outdir == None:
        plt.savefig(f'{imageoutdir}Position summary.png', format="png")
        print(f'Race position summary graph saved to "{imageoutdir}Position summary.png"')
    else:
        plt.savefig(f'{outdir}Position summary.png', format="png")
        print(f'Race position summary graph saved to "{outdir}Position summary.png"')



def getFastestlapImage(file:str=None, outdir:str=None):
    if file == None:
        root = tkinter.Tk()
        root.withdraw()
        file = filedialog.askopenfilename()

    # Input files validations
    try:
        f = open(file, "r")
        reader = csv.DictReader(f)
        header = list(list(reader)[0].keys())
        if header != ["LapNum", "driverName", "sector1", "sector2", 
                    "sector3", "Laptime", "Tyre", "TyreLapUsed"]:
            raise KeyError
        f.close()
    except FileNotFoundError:
        print(f'File Not Found: {file}')
    except Exception:
        print(f'File Validation error: {file}')
        exit(0)


    # create plot
    length = settings["image"]["fastestlap"]["size"]["length"]
    height = settings["image"]["fastestlap"]["size"]["height"]
    fig, ax = plt.subplots(figsize=(length/100, height/100))
    # set axis limits
    # plt.xlim()
    # plt.ylim()

    # create plot title
    plt.title("Fastest lap comparison\n", fontsize=36, fontweight="bold")
    # create plot label
    ax.set_title("Fastest lap", loc="left")
    ax.set_xlabel("Driver")
    ax.set_ylabel("Interval")

    # set axis interval
    ax.xaxis.set_major_locator(plt.MultipleLocator(1))
    ax.yaxis.set_major_locator(plt.MultipleLocator(0.1))


    # reading fastest lap time data
    f = open(file, "r")
    reader = csv.DictReader(f)
    driver, laptime = [], []
    for row in reader:
        if row.get("Laptime") == "":
            continue
        driver.append(row.get("driverName"))
        laptime.append(func.laptime_To_second(row.get("Laptime")))
    f.close()

    fastestlap = func.second_To_laptime(laptime[0])
    for i in range(len(laptime)-1, -1, -1):
        laptime[i] = float(f'{laptime[i] - laptime[0]:.3f}')
    
    plt.ylim(0, laptime[-1]+0.1)

    plt.bar(driver, laptime)
    plt.text(0, laptime[0], fastestlap+"\n", ha="center")
    for i in range(1, len(driver)):
        plt.text(i, laptime[i], f'+{laptime[i]:.3f}\n', ha="center")
    
    if outdir == None:
        plt.savefig(f'{imageoutdir}FastestLap summary.png', format="png")
        print(f'Fastest lap summary graph saved to "{imageoutdir}FastestLap comparison.png"')
    else:
        plt.savefig(f'{outdir}FastestLap summary.png', format="png")
        print(f'Fastest lap summary graph saved to "{outdir}FastestLap comparison.png"')




def getLaptimeImage(files:tuple=None, outdir:str=None):
    # ask for input files if no inut from parameter
    if files == None:
        root = tkinter.Tk()
        root.withdraw()
        files = filedialog.askopenfilenames()

    # Input files validations
    for file in files:
        try:
            f = open(file, "r")
            reader = csv.DictReader(f)
            header = list(list(reader)[0].keys())
            if header != ["Lap", "driverName", "sector1", "sector2",
                          "sector3", "Laptime", "Tyre", "TyreLapUsed"]:
                raise KeyError
            f.close()
        except FileNotFoundError:
            print(f'File Not Found: {file}')
            return None
        except Exception:
            print(f'File Validation error: {file}')
            return None
        
    
    # get race length (number of laps)
    racelength = 0
    for file in files:
        f = open(file, "r")
        reader = csv.DictReader(f)

        for row in reader:
            if int(row.get("Lap")) > racelength:
                racelength = int(row.get("Lap"))
        
        f.close()
    

    # create plot
    length = settings["image"]["laptime"]["size"]["length"]
    height = settings["image"]["laptime"]["size"]["height"]
    fig, ax = plt.subplots(figsize=(length/100, height/100))
    # set axis limits
    # plt.xlim(0, racelength)
    # plt.ylim()
    
    # create plot title
    plt.title("Lap time comparison\n", fontsize=36, fontweight="bold")
    # create plot label
    ax.set_title("Laptime", loc="left")
    ax.set_xlabel("Lap")
    ax.set_ylabel("Time")

    # set axis interval
    ax.xaxis.set_major_locator(plt.MultipleLocator(1))
    ax.yaxis.set_major_locator(plt.MultipleLocator(1))


    # set axis formatter (left)
    def laptimeformat(x, pos):
        return func.second_To_laptime(x)
    ax.yaxis.set_major_formatter(plt.FuncFormatter(laptimeformat))
    

    # reading laptime data
    drivers = []
    for file in files:
        lap, laptime = [], []

        f = open(file, "r")
        reader = csv.DictReader(f)
        for row in reader:
            drivername = row.get("driverName")
            laptime_str = row.get("Laptime")
            if laptime_str.replace(" ","") == "":
                    continue
            lap.append(row.get("Lap"))
            
            try:
                laptime.append(float(laptime_str))
            except ValueError:
                laptime.append(func.laptime_To_second(laptime_str))
        f.close()
            
        drivers.append(drivername)
        
        ax.plot(lap, laptime, label=drivername, linewidth=2)

    plt.grid(True)
    ax.legend(frameon=False)

    filename = 'Laptime ('
    for i in range(0, len(drivers)-1):
        filename += drivers[i] + " vs "
    filename += drivers[-1] + ")"

    if outdir == None:
        plt.savefig(f'{imageoutdir}{filename}.png', format="png")
        print(f'Lap time comparison graph saved to "{imageoutdir}{filename}"')
    else:
        plt.savefig(f'{outdir}{filename}.png', format="png")
        print(f'Lap time comparison graph saved to "{outdir}{filename}"')




def getTyrewearImage(files:tuple=None, outdir:str=None):
    # ask for input files if no inut from parameter
    if files == None:
        root = tkinter.Tk()
        root.withdraw()
        files = filedialog.askopenfilenames()

    # Input files validations
    for file in files:
        try:
            f = open(file, "r")
            reader = csv.DictReader(f)
            header = list(list(reader)[0].keys())
            if header != ["Lap", "driverName", "FL", "FR", "RL", "RR"]:
                raise KeyError
            f.close()
        except FileNotFoundError:
            print(f'File Not Found: {file}')
            return None
        except Exception:
            print(f'File Validation error: {file}')
            return None
    

    # get race length (number of laps)
    racelength = 0
    for file in files:
        f = open(file, "r")
        reader = csv.DictReader(f)

        for row in reader:
            if int(row.get("Lap")) > racelength:
                racelength = int(row.get("Lap"))
        
        f.close()
    
    # create plot
    length = settings["image"]["tyrewear"]["size"]["length"]
    height = settings["image"]["tyrewear"]["size"]["height"]
    fig, axs = plt.subplots(2, 2, figsize=(length/100, height/100))
    ax1:plt.Axes = axs[0,0]      # Front-Left tyre
    ax2:plt.Axes = axs[0,1]      # Front-Right tyre
    ax3:plt.Axes = axs[1,0]      # Rear-Left tyre
    ax4:plt.Axes = axs[1,1]      # Rear-Right tyre
    # set axis limits
    # plt.xlim(0, racelength)
    # plt.ylim(0, 100)

    # create plot title
    fig.suptitle("Tyre wear comparison", fontsize=36, fontweight="bold")
    # create plot label
    ax1.set_title("Front Left", loc="left")
    ax1.set_xlabel("Lap")
    ax2.set_ylabel("Wear")
    ax2.set_title("Front Right", loc="left")
    ax2.set_xlabel("Lap")
    ax2.set_ylabel("Wear")
    ax3.set_title("Rear Left", loc="left")
    ax3.set_xlabel("Lap")
    ax3.set_ylabel("Wear")
    ax4.set_title("Rear Right", loc="left")
    ax4.set_xlabel("Lap")
    ax4.set_ylabel("Wear")

    # set axis interval
    ax1.xaxis.set_major_locator(plt.MultipleLocator(1))
    ax1.yaxis.set_major_locator(plt.MultipleLocator(5))
    ax2.xaxis.set_major_locator(plt.MultipleLocator(1))
    ax2.yaxis.set_major_locator(plt.MultipleLocator(5))
    ax3.xaxis.set_major_locator(plt.MultipleLocator(1))
    ax3.yaxis.set_major_locator(plt.MultipleLocator(5))
    ax4.xaxis.set_major_locator(plt.MultipleLocator(1))
    ax4.yaxis.set_major_locator(plt.MultipleLocator(5))
    

    # set axis formatter (left)
    def numberformat(x, pos):
        return int(x)
    # ax1.yaxis.set_major_formatter(plt.FuncFormatter(numberformat))


    # reading tyre wear data
    drivers = []
    maxmaxwear = []
    for file in files:
        lap, fl, fr, rl, rr = [], [], [], [], []

        f = open(file, "r")
        reader = csv.DictReader(f)
        for row in reader:
            drivername = row.get("driverName")
            lap.append(row.get("Lap"))
            fl.append(float(row.get("FL")))
            fr.append(float(row.get("FR")))
            rl.append(float(row.get("RL")))
            rr.append(float(row.get("RR")))
        f.close()

        drivers.append(drivername)

        maxmaxwear.append(max([max(fl), max(fr), max(rl), max(rr)]))
        ax1.plot(lap, fl, label=drivername, linewidth=2)
        ax2.plot(lap, fr, label=drivername, linewidth=2)
        ax3.plot(lap, rl, label=drivername, linewidth=2)
        ax4.plot(lap, rr, label=drivername, linewidth=2)
    
    ax1.set_ylim(0, max(maxmaxwear)+5)
    ax2.set_ylim(0, max(maxmaxwear)+5)
    ax3.set_ylim(0, max(maxmaxwear)+5)
    ax4.set_ylim(0, max(maxmaxwear)+5)
    
    ax1.grid(True)
    ax2.grid(True)
    ax3.grid(True)
    ax4.grid(True)
    ax1.legend(frameon=False)
    ax2.legend(frameon=False)
    ax3.legend(frameon=False)
    ax4.legend(frameon=False)

    filename = 'Tyre Wear ('
    for i in range(0, len(drivers)-1):
        filename += drivers[i] + " vs "
    filename += drivers[-1] + ")"

    if outdir == None:
        plt.savefig(f'{imageoutdir}{filename}.png', format="png")
        print(f'Tyre wear comparison graph saved to "{imageoutdir}{filename}.png"')
    else:
        plt.savefig(f'{outdir}{filename}.png', format="png")
        print(f'Tyre wear comparison graph saved to "{outdir}{filename}.png"')





################## ONLINE Ver. Image ##################

def getPositionImage_ONLINE(db:mysql.connector.MySQLConnection,
                            sessionid1:int=None, sessionid2:int=None,
                            ipdec:int=None, outdir:str=None):
    cursor = db.cursor()

    if sessionid1 == None:
        sessionid1, sessionid2 = func.asksessionid()
    elif sessionid1 != None and sessionid2 == None:
        sessionid2 = sessionid1

    if sessionid1 == None or sessionid2 == None:
        query = "SELECT MAX(beginUnixTime) FROM SessionList;"
        cursor.execute(query)
        result = cursor.fetchall()
        sessionid1 = result[0][0]
        sessionid2 = result[0][0]
    
    if ipdec == None:
        ipdec = func.checkIPsrc(db, sessionid2)
    if ipdec == None:
        print("No/Wrong IP source selected......")
        return None

    print(func.delimiter_string(f'Race position summary ({sessionid2})', 60), end="\n\n")


    positiondata = {}
    """
    positiondata = {
        "driverName": {lapNum: carPosition}
    }
    """

    # get starting grid position (from finalclassification)
    query = f'SELECT beginUnixTime, curTime, position, driverName, gridPosition, numLaps, position \
            FROM FinalClassification \
            WHERE beginUnixTime >= "{sessionid1}" AND beginUnixTime <= "{sessionid2}" \
              AND ipDecimal = {ipdec} \
            ORDER BY position ASC;'
    cursor.execute(query)
    result = cursor.fetchall()

    # catagorize grid position by driver
    for driver in result:
        positiondata[driver[3]] = {0: driver[4], driver[5]+1: driver[6]}


    # fetch position data
    query = f'SELECT l1.beginUnixTime, l1.curTime, l1.carIndex, l1.driverName, l1.currentLapNum, l1.carPosition \
            FROM LapData l1 JOIN LapData l2 \
                             ON l1.beginUnixTime = l2.beginUnixTime \
                            AND l1.carIndex = l2.carIndex \
                            AND l1.currentLapTimeInMS > l2.currentLapTimeInMS \
                            AND l1.lapDistance > l2.lapDistance \
                            AND l1.curUnixTime = l2.curUnixTime - 1 \
            WHERE l1.beginUnixTime >= "{sessionid1}" AND l1.beginUnixTime <= "{sessionid2}" \
              AND l1.ipDecimal = {ipdec} \
            ORDER BY l1.carIndex, l1.currentLapNum ASC;'
    cursor.execute(query)
    print(f'Fetching race position from session {sessionid1} to {sessionid2}......')
    result = cursor.fetchall()

    # catagorize position data by driver
    for lappos in result:
        positiondata[lappos[3]][lappos[4]] = lappos[5]
    

    # get race length (number of laps)
    racelength = 0
    for driver in positiondata.keys():
        lapdone = max(sorted(positiondata[driver]))
        if lapdone > racelength:
            racelength = lapdone
    

    print("Exporting race position summary graph......")
    # create plot
    length = settings["image"]["position"]["size"]["length"]
    height = settings["image"]["position"]["size"]["height"]
    fig, ax = plt.subplots(figsize=(length/100, height/100))
    # set axis limits
    plt.xlim(0, racelength)         # x-axis of lap number
    plt.ylim(len(positiondata)+1, 0)       # y-axis of num of driver
    # create a twin for y-axis 
    # (as it must create after limit the axis,
    #  otherwise twin axis will not aligned)
    ax2 = ax.twinx()        # dont try to understand it, because I also don't
                            # well I suddenly understand it
                            # twinx means copying an axis making it sharing the x-axis with it,
                            # which means ax and ax2 sharing the x-axis,
                            # not copying ax's x-axis to ax2
    # set twin axis limits
    ax2.set_ylim(len(positiondata)+1, 0)

    # create plot title
    plt.title("Race position summary\n", fontsize=36, fontweight="bold")
    # create plot label
    ax.set_title("Rank", loc="left")
    ax.set_xlabel("Lap Number")
    ax.set_ylabel("Driver")

    # set axis interval
    ax.xaxis.set_major_locator(plt.MultipleLocator(1))
    ax.yaxis.set_major_locator(plt.MultipleLocator(1))
    ax2.yaxis.set_major_locator(plt.MultipleLocator(1))


    # set axis formatter (left)
    def driver_rank(x, pos):
        # x represent a value (don't know what it means)
        # pos represent a tick value, 
        #     referring the y axis locator (starting from 0 from top)
        poscursor = pos - 2
        pos = pos - 1
        if poscursor >= 0 and poscursor < len(posstart):
            return f'{posstart[poscursor]}  {pos}'
    ax.yaxis.set_major_formatter(plt.FuncFormatter(driver_rank))

    # set axis formatter (right)
    def rank_driver(x, pos):
        # x represent a value (don't know what it means)
        # pos represent a tick value, 
        #     referring the y axis locator (starting from 0 from top)
        poscursor = pos - 2
        pos = pos - 1
        if poscursor >= 0 and poscursor < len(posfinal):
            return f'{pos}  {posfinal[poscursor]}'
    ax2.yaxis.set_major_formatter(plt.FuncFormatter(rank_driver))


    # initialize position rank
    posstart = [None] * len(positiondata)
    posfinal = [None] * len(positiondata)


    # reading position data
    for driver in positiondata:
        lap, pos = [], []
        drivername = driver

        for l in sorted(positiondata[driver]):
            lap.append(l)
            pos.append(positiondata[driver][l])
        
        # mark overall position data
        posstart[pos[0]-1] = drivername
        posfinal[pos[-1]-1] = drivername

        ax.plot(lap, pos, linewidth=3)
    
    plt.grid(True)

    if outdir == None:
        plt.savefig(f'{imageoutdir}Position summary ({sessionid2}).png', format="png")
        print(f'Race position summary graph saved to "{imageoutdir}Position summary ({sessionid2}).png"')

    else:
        plt.savefig(f'{outdir}Position summary ({sessionid2}).png', format="png")
        print(f'Race position summary graph saved to "{outdir}Position summary ({sessionid2}).png"')




def getFastestlapImage_ONLINE(db:mysql.connector.MySQLConnection,
                              sessionid1:int=None, sessionid2:int=None,
                              ipdec:int=None, outdir:str=None):
    cursor = db.cursor()

    if sessionid1 == None:
        sessionid1, sessionid2 = func.asksessionid()
    elif sessionid1 != None and sessionid2 == None:
        sessionid2 = sessionid1

    if sessionid1 == None or sessionid2 == None:
        query = "SELECT MAX(beginUnixTime) FROM SessionList;"
        cursor.execute(query)
        result = cursor.fetchall()
        sessionid1 = result[0][0]
        sessionid2 = result[0][0]
    
    if ipdec == None:
        ipdec = func.checkIPsrc(db, sessionid2)
    if ipdec == None:
        print("No/Wrong IP source selected......")
        return None

    print(func.delimiter_string(f'Fastest lap summary ({sessionid2})', 60), end="\n\n")


    # fetch fastest lapfile
    query = f'SELECT beginUnixTime, curTime, carIndex, driverName, bestLapTimeLapNum, bestLapTimeInStr \
            FROM BestLap \
            WHERE beginUnixTime >= "{sessionid1}" AND beginUnixTime <= "{sessionid2}" \
                AND driverName in (SELECT driverName FROM Participants  \
                                   WHERE beginUnixTime >= "{sessionid1}" AND beginUnixTime <= "{sessionid2}" \
                                     AND aiControlled = 0) \
                AND ipDecimal = {ipdec} \
                AND curUnixTime = (SELECT MAX(curUnixTime) FROM BestLap \
                                   WHERE beginUnixTime >= "{sessionid1}" AND beginUnixTime <= "{sessionid2}")\
            ORDER BY CASE bestLapTimeInMS \
                    WHEN 0 THEN 2 \
                    ELSE 1 \
                END, bestLapTimeInMS ASC;'
    cursor.execute(query)
    result = cursor.fetchall()


    print("Exporting fastest lap comparison graph......")
    # create plot
    length = settings["image"]["fastestlap"]["size"]["length"]
    height = settings["image"]["fastestlap"]["size"]["height"]
    fig, ax = plt.subplots(figsize=(length/100, height/100))
    # set axis limits
    # plt.xlim()
    # plt.ylim()

    # create plot title
    plt.title("Fastest lap comparison\n", fontsize=36, fontweight="bold")
    # create plot label
    ax.set_title("Fastest lap", loc="left")
    ax.set_xlabel("Driver")
    ax.set_ylabel("Interval")

    # set axis interval
    ax.xaxis.set_major_locator(plt.MultipleLocator(1))
    ax.yaxis.set_major_locator(plt.MultipleLocator(0.1))


    # reading fastest lap time data
    driver, laptime = [], []
    for lap in result:
        if lap[5] == "":
            continue
        driver.append(lap[3])
        laptime.append(func.laptime_To_second(lap[5]))

    fastestlap = func.second_To_laptime(laptime[0])
    for i in range(len(laptime)-1, -1, -1):
        laptime[i] = float(f'{laptime[i] - laptime[0]:.3f}')
    
    plt.ylim(0, laptime[-1]+0.1)

    plt.bar(driver, laptime)
    plt.text(0, laptime[0], fastestlap+"\n", ha="center")
    for i in range(1, len(driver)):
        plt.text(i, laptime[i], f'+{laptime[i]:.3f}\n', ha="center")
    
    if outdir == None:
        plt.savefig(f'{imageoutdir}FastestLap comparison ({sessionid2}).png', format="png")
        print(f'Fastest lap summary graph saved to "{imageoutdir}FastestLap comparison ({sessionid2}).png"')
    else:
        plt.savefig(f'{outdir}FastestLap summary.png', format="png")
        print(f'Fastest lap summary graph saved to "{outdir}FastestLap comparison ({sessionid2}).png"')




def getLaptimeImage_ONLINE(db:mysql.connector.MySQLConnection,
                           sessionid1:int=None, sessionid2:int=None,
                           ipdec:int=None, outdir:str=None):
    cursor = db.cursor()

    if sessionid1 == None:
        sessionid1, sessionid2 = func.asksessionid()
    elif sessionid1 != None and sessionid2 == None:
        sessionid2 = sessionid1

    if sessionid1 == None or sessionid2 == None:
        query = "SELECT MAX(beginUnixTime) FROM SessionList;"
        cursor.execute(query)
        result = cursor.fetchall()
        sessionid1 = result[0][0]
        sessionid2 = result[0][0]
    elif sessionid1 == "Nosession" and sessionid2 == "Nosession":
        return None

    if ipdec == None:
        ipdec = func.checkIPsrc(db, sessionid2)
    if ipdec == None:
        print("No/Wrong IP source selected......")
        return None
    
    print(func.delimiter_string(f'Lap time comparison ({sessionid2})', 60), end="\n\n")


    # fetch session laptime data
    query = f'SELECT beginUnixTime, curTime, CarIndex, driverName, lapNum, \
                     sector1TimeInStr, sector2TimeInStr, sector3TimeInStr, lapTimeInStr, \
                     tyreVisualCompoundInStr, tyreLapNumUsedInThisStint \
            FROM LapHistoryData \
            WHERE beginUnixTime >= "{sessionid1}" AND beginUnixTime <= "{sessionid2}" \
              AND driverName in (SELECT driverName FROM Participants  \
                                 WHERE beginUnixTime >= "{sessionid1}" AND beginUnixTime <= "{sessionid2}" \
                                 AND aiControlled = 0) \
              AND ipDecimal = {ipdec} \
            ORDER BY curTime ASC, carIndex ASC, lapNum ASC;'
    cursor.execute(query)
    print(f'Fetching lap data from session {sessionid1} to {sessionid2}......')
    result = cursor.fetchall()
    

    # catagorize laptime data by driver
    laptimedata = {}
    for record in result:
        try:
            laptimedata[record[2]].append(record)
        except KeyError:
            laptimedata[record[2]] = [record]


    # ask user for which drivers in the data pool (for comparison)
    print(f'{"Index":<8}{"Driver":<20}')
    for index in sorted(laptimedata.keys()):
        print(f'{index:<8}{laptimedata[index][0][3]}')
    print()
    choices = input("Enter the driver selected (seperate by comma): ")
    if choices == "q" or choices == "Q":
        return None
    
    choices = choices.split(",")
    driverselect = []
    for choice in choices:
        try:
            index = int(choice.replace(" ", ""))
            laptimedata[index]
            driverselect.append(index)
        except (ValueError, KeyError):
            continue
    

    # get race length (number of laps)
    racelength = 0
    for index in driverselect:
        laps = len(laptimedata[index])
        if laps > racelength:
            racelength = laps
    

    # create plot
    length = settings["image"]["laptime"]["size"]["length"]
    height = settings["image"]["laptime"]["size"]["height"]
    fig, ax = plt.subplots(figsize=(length/100, height/100))
    # set axis limits
    # plt.xlim(0, racelength)
    # plt.ylim()
    
    # create plot title
    plt.title("Lap time comparison\n", fontsize=36, fontweight="bold")
    # create plot label
    ax.set_title("Laptime", loc="left")
    ax.set_xlabel("Lap")
    ax.set_ylabel("Time")

    # set axis interval
    ax.xaxis.set_major_locator(plt.MultipleLocator(1))
    ax.yaxis.set_major_locator(plt.MultipleLocator(1))


    # set axis formatter (left)
    def laptimeformat(x, pos):
        return func.second_To_laptime(x)
    ax.yaxis.set_major_formatter(plt.FuncFormatter(laptimeformat))


    # reading laptime data
    drivers = []
    for index in driverselect:
        drivername = laptimedata[index][0][3]
        lap, laptime = [], []
        for row in sorted(laptimedata[index], key=lambda x:x[4]):
            if row[8].replace(" ", "") == "":
                continue

            try:
                lap.append(row[4])
                laptime.append(float(row[8]))
            except ValueError:
                laptime.append(func.laptime_To_second(row[8]))
        
        drivers.append(drivername)

        ax.plot(lap, laptime, label=drivername, linewidth=2)

    plt.grid(True)
    ax.legend(frameon=False)

    filename = 'Laptime ('
    for i in range(0, len(drivers)-1):
        filename += drivers[i] + " vs "
    filename += drivers[-1] + ")"

    if outdir == None:
        plt.savefig(f'{imageoutdir}{filename} ({sessionid2}).png', format="png")
        print(f'Lap time comparison graph saved to "{imageoutdir}{filename} ({sessionid2}).png"')
    else:
        plt.savefig(f'{outdir}{filename} ({sessionid2}).png', format="png")
        print(f'Lap time comparison graph saved to "{outdir}{filename} ({sessionid2}).png"')




def getTyrewearImage_ONLINE(db:mysql.connector.MySQLConnection,
                           sessionid1:int=None, sessionid2:int=None,
                           ipdec:int=None, outdir:str=None):
    cursor = db.cursor()

    if sessionid1 == None:
        sessionid1, sessionid2 = func.asksessionid()
    elif sessionid1 != None and sessionid2 == None:
        sessionid2 = sessionid1

    if sessionid1 == None or sessionid2 == None:
        query = "SELECT MAX(beginUnixTime) FROM SessionList;"
        cursor.execute(query)
        result = cursor.fetchall()
        sessionid1 = result[0][0]
        sessionid2 = result[0][0]
    elif sessionid1 == "Nosession" and sessionid2 == "Nosession":
        return None

    if ipdec == None:
        ipdec = func.checkIPsrc(db, sessionid2)
    if ipdec == None:
        print("No/Wrong IP source selected......")
        return None
    
    print(func.delimiter_string(f'Tyre wear comparison ({sessionid2})', 60), end="\n\n")


    # fetching tyre wear data
    query = f'SELECT l1.beginUnixTime, l1.curTime, l1.carIndex, l1.driverName, l1.currentLapNum, \
                     CarDamage.tyresWearFL, CarDamage.tyresWearFR, CarDamage.tyresWearRL, CarDamage.tyresWearRR \
            FROM LapData l1 JOIN LapData l2 \
                                ON l1.beginUnixTime = l2.beginUnixTime \
                                AND l1.carIndex = l2.carIndex \
                                AND l1.currentLapTimeInMS > l2.currentLapTimeInMS \
                                AND l1.lapDistance > l2.lapDistance \
                                AND l1.curUnixTime = l2.curUnixTime - 1 \
                                AND l1.ipDecimal = l2.ipDecimal \
                            JOIN CarDamage \
                                ON l1.beginUnixTime = CarDamage.beginUnixTime \
                                AND l1.curUnixTime = CarDamage.curUnixTime \
                                AND l1.carIndex = CarDamage.carIndex \
                                AND l1.ipDecimal = CarDamage.ipDecimal \
            WHERE l1.beginUnixTime >= "{sessionid1}" AND l1.beginUnixTime <= "{sessionid2}" \
              AND l1.ipDecimal = {ipdec} \
            ORDER BY l1.carIndex, l1.currentLapNum ASC;'
    print(f'Fetching tyre wear data from session {sessionid1} to {sessionid2}......')
    cursor.execute(query)
    result = cursor.fetchall()

    # catagorize tyre wear data by driver
    tyreweardata = {}
    for record in result:
        try:

            tyreweardata[record[2]].append(record)
        except KeyError:
            tyreweardata[record[2]] = [record]
    
    
    # ask user for which drivers in the data pool (for comparison)
    print(f'{"Index":<8}{"Driver":<20}')
    for index in sorted(tyreweardata.keys()):
        print(f'{index:<8}{tyreweardata[index][0][3]}')
    print()
    choices = input("Enter the drivers selected (seperate by comma): ")
    if choices == "q" or choices == "Q":
        return None
    
    choices = choices.split(",")
    driverselect = []
    for choice in choices:
        try:
            index = int(choice.replace(" ", ""))
            tyreweardata[index]
            driverselect.append(index)
        except (ValueError, KeyError):
            continue


    # get race length (number of laps)
    racelength = 0
    for index in driverselect:
        laps = len(tyreweardata[index])
        if laps > racelength:
            racelength = laps


    # create plot
    length = settings["image"]["tyrewear"]["size"]["length"]
    height = settings["image"]["tyrewear"]["size"]["height"]
    fig, axs = plt.subplots(2, 2, figsize=(length/100, height/100))
    ax1:plt.Axes = axs[0,0]      # Front-Left tyre
    ax2:plt.Axes = axs[0,1]      # Front-Right tyre
    ax3:plt.Axes = axs[1,0]      # Rear-Left tyre
    ax4:plt.Axes = axs[1,1]      # Rear-Right tyre
    # set axis limits
    # plt.xlim(0, racelength)
    # plt.ylim(0, 100)

    # create plot title
    fig.suptitle("Tyre wear comparison", fontsize=36, fontweight="bold")
    # create plot label
    ax1.set_title("Front Left", loc="left")
    ax1.set_xlabel("Lap")
    ax2.set_ylabel("Wear")
    ax2.set_title("Front Right", loc="left")
    ax2.set_xlabel("Lap")
    ax2.set_ylabel("Wear")
    ax3.set_title("Rear Left", loc="left")
    ax3.set_xlabel("Lap")
    ax3.set_ylabel("Wear")
    ax4.set_title("Rear Right", loc="left")
    ax4.set_xlabel("Lap")
    ax4.set_ylabel("Wear")

    # set axis interval
    ax1.xaxis.set_major_locator(plt.MultipleLocator(1))
    ax1.yaxis.set_major_locator(plt.MultipleLocator(5))
    ax2.xaxis.set_major_locator(plt.MultipleLocator(1))
    ax2.yaxis.set_major_locator(plt.MultipleLocator(5))
    ax3.xaxis.set_major_locator(plt.MultipleLocator(1))
    ax3.yaxis.set_major_locator(plt.MultipleLocator(5))
    ax4.xaxis.set_major_locator(plt.MultipleLocator(1))
    ax4.yaxis.set_major_locator(plt.MultipleLocator(5))
    

    # set axis formatter (left)
    def numberformat(x, pos):
        return int(x)
    # ax1.yaxis.set_major_formatter(plt.FuncFormatter(numberformat))


    # reading tyre wear data
    drivers = []
    maxmaxwear = []
    for index in driverselect:
        drivername = tyreweardata[index][0][3]
        lap, fl, fr, rl, rr = [], [], [], [], []

        for row in sorted(tyreweardata[index], key=lambda x:x[4]):
            lap.append(row[4])
            fl.append(row[5])
            fr.append(row[6])
            rl.append(row[7])
            rr.append(row[8])
        
        drivers.append(drivername)

        maxmaxwear.append(max([max(fl), max(fr), max(rl), max(rr)]))
        ax1.plot(lap, fl, label=drivername, linewidth=2)
        ax2.plot(lap, fr, label=drivername, linewidth=2)
        ax3.plot(lap, rl, label=drivername, linewidth=2)
        ax4.plot(lap, rr, label=drivername, linewidth=2)
    
    ax1.set_ylim(0, max(maxmaxwear)+5)
    ax2.set_ylim(0, max(maxmaxwear)+5)
    ax3.set_ylim(0, max(maxmaxwear)+5)
    ax4.set_ylim(0, max(maxmaxwear)+5)
    
    ax1.grid(True)
    ax2.grid(True)
    ax3.grid(True)
    ax4.grid(True)
    ax1.legend(frameon=False)
    ax2.legend(frameon=False)
    ax3.legend(frameon=False)
    ax4.legend(frameon=False)

    filename = 'Tyre Wear ('
    for i in range(0, len(drivers)-1):
        filename += drivers[i] + " vs "
    filename += drivers[-1] + ")"

    if outdir == None:
        plt.savefig(f'{imageoutdir}{filename} ({sessionid2}).png', format="png")
        print(f'Tyre wear comparison graph saved to "{imageoutdir}{filename} ({sessionid2}).png"')
    else:
        plt.savefig(f'{outdir}{filename} ({sessionid2}).png', format="png")
        print(f'Tyre wear comparison graph saved to "{outdir}{filename} ({sessionid2}).png"')



# ------ testing use case ------ #
# getPositionImage()
# getLaptimeImage()
# getTyrewearImage()
# getFastestlapImage()

# getPositionImage_ONLINE(dbconnect.connect_with_conf("server.json", "db"))
# getFastestlapImage_ONLINE(dbconnect.connect_with_conf("server.json", "db"))
# getLaptimeImage_ONLINE(dbconnect.connect_with_conf("server.json", "db"))
# getTyrewearImage_ONLINE(dbconnect.connect_with_conf("server.json", "db"))