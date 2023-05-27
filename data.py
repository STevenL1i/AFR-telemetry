import os, csv, json, xlsxwriter, traceback

import dbconnect
import mysql.connector

import deffunc as func

# loading settings
settingsf = open("settings.json", "r")
settings:dict = json.load(settingsf)
settingsf.close()
# check output dir correct
outputdir = settings["outputdir"]
os.system(f'if not exist "{outputdir}" mkdir "{outputdir}"')
if outputdir[-1] != "/":
    outputdir += "/"

AInamelist = ["VERSTAPPEN","LECLERC","HAMILTON","NORRIS","VETTEL","ALONSO","SAINZ","BOTTAS","PÉREZ","GASLY",
              "ZHOU","ALBON","OCON","SCHUMACHER","STROLL","RICCIARDO","TSUNODA","MAGNUSSEN","LATIFI","RUSSELL",
              "勒克莱尔","维斯塔潘","拉塞尔","赛恩斯","佩雷兹","诺里斯","阿隆索","里卡多","欧肯","周","角田","加斯利",
              "舒马赫","马格努森","博塔斯","维特尔","斯特尔","阿尔本","拉蒂菲","汉密尔顿",""]


def asksessionid() -> tuple[int, int]:
    sessionid1 = input("please enter session id 1: ")
    if sessionid1 == "q" or sessionid1 == "Q":
        return None, None
    sessionid2 = input("please enter session id 2: ")
    if sessionid2 == "q" or sessionid2 == "Q":
        return None, None
    
    if sessionid2.replace(" ", "") == "":
        sessionid2 = sessionid1

    try:
        return int(sessionid1), int(sessionid2)
    except ValueError as e:
        return None, None
    



def getLapdata(db:mysql.connector.MySQLConnection,
               sessionid1:int=None, sessionid2:int=None):
    if sessionid1 == None:
        sessionid1, sessionid2 = asksessionid()
    elif sessionid1 != None and sessionid2 == None:
        sessionid2 = sessionid1

    if sessionid1 == None or sessionid2 == None:
        print("no or error session id")
        return None
    
    cursor = db.cursor()

    # """
    # get driver count of the session
    query = f'SELECT MAX(carIndex) FROM Participants \
            WHERE beginUnixTime >= "{sessionid1}" and beginUnixTime <= "{sessionid2}" \
                AND driverName in (SELECT driverName FROM Participants  \
                                   WHERE beginUnixTime >= "{sessionid1}" AND beginUnixTime <= "{sessionid2}" \
                                     AND aiControlled = 0);'
    cursor.execute(query)
    result = cursor.fetchall()
    drivercount = result[0][0]
    # """


    # fetch session laptime data
    query = f'SELECT beginUnixTime, curTime, CarIndex, driverName, lapNum, \
                     sector1TimeInStr, sector2TimeInStr, sector3TimeInStr, lapTimeInStr, \
                     tyreVisualCompoundInStr, tyreLapNumUsedInThisStint \
            FROM LapHistoryData \
            WHERE beginUnixTime >= "{sessionid1}" AND beginUnixTime <= "{sessionid2}" \
              AND driverName in (SELECT driverName FROM Participants  \
                                 WHERE beginUnixTime >= "{sessionid1}" AND beginUnixTime <= "{sessionid2}" \
                                 AND aiControlled = 0) \
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


    # making output folder
    folder = f'Laptime ({sessionid2})'
    os.system(f'if not exist "{outputdir}{folder}" mkdir "{outputdir}{folder}"')


    # making xlsx file
    workbook = xlsxwriter.Workbook(f'{outputdir}{folder}/Laptime.xlsx')

    for driver in sorted(laptimedata.keys()):
        lapdata = laptimedata[driver]

        # making csv file
        csvfile = open(f'{outputdir}{folder}/{lapdata[0][3]}.csv', "w", newline="")
        header = ["Lap", "driverName", "sector1", "sector2", "sector3", "Laptime", "Tyre", "TyreLapUsed"]
        writer = csv.DictWriter(csvfile, fieldnames=header)
        writer.writeheader()

        # making xlsx sheet
        lapdatasheet = workbook.add_worksheet(lapdata[0][3])
        lapdatasheet.set_column(0,0, 8)
        lapdatasheet.set_column(1,1, 25)
        lapdatasheet.set_column(2,4, 8)
        lapdatasheet.set_column(5,5, 9)
        lapdatasheet.set_column(6,6, 15)
        lapdatasheet.set_column(7,7, 11)

        defaultformat = workbook.add_format({"font_size":11})
        defaultformat.set_font_name("Dengxian")
        defaultformat.set_align("vcenter")
        defaultformat.set_text_wrap()

        # writing header
        for i in range(0, len(header)):
            lapdatasheet.write(0, i, header[i], defaultformat)
        
        rowcursor = 1
        print(f'Writing lap data: {lapdata[0][3]}......')
        for lap in sorted(lapdata, key=lambda x:x[4]):
            # writing to csv file
            data = {"Lap": lap[4], "driverName": lap[3], "sector1": lap[5], "sector2": lap[6], 
                     "sector3": lap[7], "Laptime": lap[8], "Tyre": lap[9], "TyreLapUsed": lap[10]}
            writer.writerow(data)

            # writing to xlsx file
            lapdatasheet.write(rowcursor, 0, lap[4], defaultformat)
            lapdatasheet.write(rowcursor, 1, lap[3], defaultformat)
            lapdatasheet.write(rowcursor, 2, lap[5], defaultformat)
            lapdatasheet.write(rowcursor, 3, lap[6], defaultformat)
            lapdatasheet.write(rowcursor, 4, lap[7], defaultformat)
            lapdatasheet.write(rowcursor, 5, lap[8], defaultformat)
            lapdatasheet.write(rowcursor, 6, lap[9], defaultformat)
            lapdatasheet.write(rowcursor, 7, lap[10], defaultformat)
            rowcursor += 1

        csvfile.close()


    # fastest lapfile
    query = f'SELECT beginUnixTime, curTime, carIndex, driverName, bestLapTimeLapNum, bestLapTimeInStr \
            FROM BestLap \
            WHERE beginUnixTime >= "{sessionid1}" AND beginUnixTime <= "{sessionid2}" \
                AND driverName in (SELECT driverName FROM Participants  \
                                   WHERE beginUnixTime >= "{sessionid1}" AND beginUnixTime <= "{sessionid2}" \
                                     AND aiControlled = 0) \
            ORDER BY curTime DESC, \
                CASE bestLapTimeInMS \
                    WHEN 0 THEN 2 \
                    ELSE 1 \
                END, bestLapTimeInMS ASC \
            LIMIT {drivercount};'
    cursor.execute(query)
    result = cursor.fetchall()

    # making csv file
    csvfile = open(f'{outputdir}{folder}/fastest lap.csv', "w", newline="")
    header = ["LapNum", "driverName", "sector1", "sector2", "sector3", "Laptime", "Tyre", "TyreLapUsed"]
    writer = csv.DictWriter(csvfile, fieldnames=header)
    writer.writeheader()

    # making xlsx sheet
    fastestlapsheet = workbook.add_worksheet("fastest lap")
    fastestlapsheet.set_column(0,0, 8)
    fastestlapsheet.set_column(1,1, 25)
    fastestlapsheet.set_column(2,4, 8)
    fastestlapsheet.set_column(5,5, 9)
    fastestlapsheet.set_column(6,6, 15)
    fastestlapsheet.set_column(7,7, 11)

    # writing header
    for i in range(0, len(header)):
        fastestlapsheet.write(0, i, header[i], defaultformat)

    rowcursor = 1
    for fl in result:
        # writing fastest lap to csv file
        lap = laptimedata[fl[2]][fl[4]-1]
        data = {"LapNum": lap[4], "driverName": lap[3], "sector1": lap[5], "sector2": lap[6], 
                "sector3": lap[7], "Laptime": lap[8], "Tyre": lap[9], "TyreLapUsed": lap[10]}
        writer.writerow(data)

        # writing fastest lap to xlsx file
        fastestlapsheet.write(rowcursor, 0, lap[4], defaultformat)
        fastestlapsheet.write(rowcursor, 1, lap[3], defaultformat)
        fastestlapsheet.write(rowcursor, 2, lap[5], defaultformat)
        fastestlapsheet.write(rowcursor, 3, lap[6], defaultformat)
        fastestlapsheet.write(rowcursor, 4, lap[7], defaultformat)
        fastestlapsheet.write(rowcursor, 5, lap[8], defaultformat)
        fastestlapsheet.write(rowcursor, 6, lap[9], defaultformat)
        fastestlapsheet.write(rowcursor, 7, lap[10], defaultformat)
        rowcursor += 1


    csvfile.close()
    workbook.close()




def getTeledata(db:mysql.connector.MySQLConnection,
               sessionid1:int=None, sessionid2:int=None):
    if sessionid1 == None:
        sessionid1, sessionid2 = asksessionid()
    elif sessionid1 != None and sessionid2 == None:
        sessionid2 = sessionid1

    if sessionid1 == None or sessionid2 == None:
        print("no or error session id")
        return None
    
    cursor = db.cursor()




def getFinalClassification(db:mysql.connector.MySQLConnection,
                           sessionid1:int=None, sessionid2:int=None):
    if sessionid1 == None:
        sessionid1, sessionid2 = asksessionid()
    elif sessionid1 != None and sessionid2 == None:
        sessionid2 = sessionid1

    if sessionid1 == None or sessionid2 == None:
        print("no or error session id")
        return None
    
    cursor = db.cursor()


    # fetch session final classification data
    query = f'SELECT beginUnixTime, curTime, position, driverName, \
                     numLaps, gridPosition, numPitStops, \
                     bestLapTimeStr, totalRaceTimeStr, overallResult, \
                     numPenalties, penaltiesTime, tyreStintsVisual \
            FROM FinalClassification \
            WHERE beginUnixTime >= "{sessionid1}" AND beginUnixTime <= "{sessionid2}" \
            ORDER BY position ASC;'
    cursor.execute(query)
    print(f'Fetching finalclassification data from session {sessionid1} to {sessionid2}......')
    result = cursor.fetchall()


    # making output folder
    folder = f'Final Classification'
    os.system(f'if not exist "{outputdir}{folder}" mkdir "{outputdir}{folder}"')


    # making csv file
    csvfile = open(f'{outputdir}{folder}/FinalClassification_{sessionid2}.csv', "w", newline="")
    header = ["position", "driverName", "numLaps", "grid", "pits",
              "bestlap", "totaltime", "gap", "numPen", "penalty", "tyreStint"]
    writer = csv.DictWriter(csvfile, fieldnames=header)
    writer.writeheader()


    # making xlsx file
    workbook = xlsxwriter.Workbook(f'{outputdir}{folder}/FinalClassification_{sessionid2}.xlsx')
    fcsheet = workbook.add_worksheet(f'FinalClassification_{sessionid2}')
    fcsheet.set_column(0,0, 8)
    fcsheet.set_column(1,1, 25)
    fcsheet.set_column(2,4, 8)
    fcsheet.set_column(5,7, 9)
    fcsheet.set_column(8,9, 8)
    fcsheet.set_column(10,10, 80)

    defaultformat = workbook.add_format({"font_size":11})
    defaultformat.set_font_name("Dengxian")
    defaultformat.set_align("vcenter")
    defaultformat.set_text_wrap()

    # writing header
    for i in range(0, len(header)):
        fcsheet.write(0, i, header[i], defaultformat)
    

    rowcursor = 1
    print(f'Writing finalclassification data from session {sessionid1} to {sessionid2}......')
    for driver in result:
        # writing to csv file
        data = {"position": driver[2], "driverName": driver[3], "numLaps": driver[4],
                "grid": driver[5], "pits": driver[6], "bestlap": driver[7], "totaltime": driver[8],
                "gap": driver[9], "numPen": driver[10], "penalty": driver[11], "tyreStint": driver[12]}
        writer.writerow(data)

        
        # writing to xlsx file
        fcsheet.write(rowcursor, 0, driver[2], defaultformat)
        fcsheet.write(rowcursor, 1, driver[3], defaultformat)
        fcsheet.write(rowcursor, 2, driver[4], defaultformat)
        fcsheet.write(rowcursor, 3, driver[5], defaultformat)
        fcsheet.write(rowcursor, 4, driver[6], defaultformat)
        fcsheet.write(rowcursor, 5, driver[7], defaultformat)
        fcsheet.write(rowcursor, 6, driver[8], defaultformat)
        fcsheet.write(rowcursor, 7, driver[9], defaultformat)
        fcsheet.write(rowcursor, 8, driver[10], defaultformat)
        fcsheet.write(rowcursor, 9, driver[11], defaultformat)
        fcsheet.write(rowcursor, 10, driver[12], defaultformat)
        rowcursor += 1

    csvfile.close()
    workbook.close()


    # get race diretcor data of the session by the way
    getRaceDirector(db, sessionid1, sessionid2)




def getRaceDirector(db:mysql.connector.MySQLConnection,
                    sessionid1:int=None, sessionid2:int=None):
    if sessionid1 == None:
        sessionid1, sessionid2 = asksessionid()
    elif sessionid1 != None and sessionid2 == None:
        sessionid2 = sessionid1

    if sessionid1 == None or sessionid2 == None:
        print("no or error session id")
        return None

    cursor = db.cursor()
    

    # fetch session race director data
    query = f'SELECT beginUnixTime, curTime, lapNum, driverName, otherDriverName, \
                     penaltyDescription, infringementDescription, timeGained, placesGained \
            FROM PenaltyUpdate \
            WHERE beginUnixTime >= "{sessionid1}" AND beginUnixTime <= "{sessionid2}" \
            ORDER BY curTime ASC;'
    cursor.execute(query)
    print(f'Fetching racedirector data from session {sessionid1} to {sessionid2}......')
    result = cursor.fetchall()

    # making output folder
    folder = f'Final Classification'
    os.system(f'if not exist "{outputdir}{folder}" mkdir "{outputdir}{folder}"')

    
    # making csv file
    csvfile = open(f'{outputdir}{folder}/RaceDirector_{sessionid2}.csv', "w", newline="")
    header = ["Lap", "driverName", "driverInvolved", "PenaltyType", "PenaltyDescriptions",
              "timeGained", "placeGained"]
    writer = csv.DictWriter(csvfile, fieldnames=header)
    writer.writeheader()


    # making xlsx file
    workbook = xlsxwriter.Workbook(f'{outputdir}{folder}/RaceDirector_{sessionid2}.xlsx')
    rdsheet = workbook.add_worksheet(f'RaceDirector_{sessionid2}')
    rdsheet.set_column(0,0, 8)
    rdsheet.set_column(1,2, 25)
    rdsheet.set_column(3,3, 40)
    rdsheet.set_column(4,4, 50)
    rdsheet.set_column(5,6, 10)

    defaultformat = workbook.add_format({"font_size":11})
    defaultformat.set_font_name("Dengxian")
    defaultformat.set_align("vcenter")
    defaultformat.set_text_wrap()

    # writing header
    for i in range(0, len(header)):
        rdsheet.write(0, i, header[i], defaultformat)


    rowcursor = 1
    print(f'Writing racedirector data from session {sessionid1} to {sessionid2}......')
    for record in result:
        # writing to csv file
        data = {"Lap": record[2], "driverName": record[3], "driverInvolved": record[4],
                "PenaltyType": record[5], "PenaltyDescriptions": record[6],
                "timeGained": record[7], "placeGained": record[8]}
        writer.writerow(data)


        # writing to xlsx file
        rdsheet.write(rowcursor, 0, record[2], defaultformat)
        rdsheet.write(rowcursor, 1, record[3], defaultformat)
        rdsheet.write(rowcursor, 2, record[4], defaultformat)
        rdsheet.write(rowcursor, 3, record[5], defaultformat)
        rdsheet.write(rowcursor, 4, record[6], defaultformat)
        rdsheet.write(rowcursor, 5, record[7], defaultformat)
        rdsheet.write(rowcursor, 6, record[8], defaultformat)
        rowcursor += 1
    

    csvfile.close()
    workbook.close()




def getPosdata(db:mysql.connector.MySQLConnection,
               sessionid1:int=None, sessionid2:int=None):
    if sessionid1 == None:
        sessionid1, sessionid2 = asksessionid()
    elif sessionid1 != None and sessionid2 == None:
        sessionid2 = sessionid1

    if sessionid1 == None or sessionid2 == None:
        print("no or error session id")
        return None

    cursor = db.cursor()
    positiondata = {}
    """
    positiondata = {
        "driverName": {lapNum: carPosition}
    }
    """

    # get starting grid position (from finalclassification)
    query = f'SELECT beginUnixTime, curTime, position, driverName, gridPosition \
            FROM FinalClassification \
            WHERE beginUnixTime >= "{sessionid1}" AND beginUnixTime <= "{sessionid2}" \
            ORDER BY position ASC;'
    cursor.execute(query)
    result = cursor.fetchall()

    # catagorize grid position by driver
    for driver in result:
        positiondata[driver[3]] = {0: driver[4]}


    # fetch position data
    query = f'SELECT l1.beginUnixTime, l1.curTime, l1.carIndex, l1.driverName, l1.currentLapNum, l1.carPosition \
            FROM LapData l1 JOIN LapData l2 \
                             ON l1.beginUnixTime = l2.beginUnixTime \
                            AND l1.carIndex = l2.carIndex \
                            AND l1.currentLapTimeInMS > l2.currentLapTimeInMS \
                            AND l1.lapDistance > l2.lapDistance \
                            AND l1.curUnixTime = l2.curUnixTime - 1 \
            WHERE l1.beginUnixTime >= "{sessionid1}" AND l1.beginUnixTime <= "{sessionid2}" \
            ORDER BY l1.carIndex, l1.currentLapNum ASC;'
    cursor.execute(query)
    result = cursor.fetchall()

    # catagorize position data by driver
    for lappos in result:
        positiondata[lappos[3]][lappos[4]] = lappos[5]


    # making output folder
    folder = f'Position ({sessionid2})'
    os.system(f'if not exist "{outputdir}{folder}" mkdir "{outputdir}{folder}"')

    for driver in positiondata.keys():
        driverposdata = positiondata[driver]

        # making csv file
        csvfile = open(f'{outputdir}{folder}/{driver}.csv', "w", newline="")
        header = ["driverName", "lapNum", "position"]
        writer = csv.DictWriter(csvfile, fieldnames=header)
        writer.writeheader()

        # writing to csv file
        for lap in sorted(driverposdata):
            data = {"driverName": driver, "lapNum": lap, "position": driverposdata[lap]}
            writer.writerow(data)
        
        csvfile.close()









def deleteSessionData(db:mysql.connector.MySQLConnection,
                      sessionid1:int=None, sessionid2:int=None):
    if sessionid1 == None:
        sessionid1, sessionid2 = asksessionid()
    elif sessionid1 != None and sessionid2 == None:
        sessionid2 = sessionid1

    if sessionid1 == None or sessionid2 == None:
        print("no or error session id")
        return None

    cursor = db.cursor()

    query = f'SHOW tables;'
    cursor.execute(query)
    result = cursor.fetchall()

    print(f'deleting tele data from session {sessionid1} to {sessionid2}......')
    for table in result:
        tablename = bytes(table[0]).decode('utf-8')
        if tablename == "IpList":
            continue
        
        try:
            query = f'DELETE FROM {tablename} \
                    WHERE beginUnixTime >= "{sessionid1}" AND beginUnixTime <= "{sessionid2}";'
            print(f'deleting data from {tablename}......')
            cursor.execute(query)
        except mysql.connector.errors.ProgrammingError:
            continue

    db.commit()




# ------ testing use case ------ #
getLapdata(dbconnect.connect_with_conf("server.json", "db"), 1684670903)
getLapdata(dbconnect.connect_with_conf("server.json", "db"), 1684673362)
getTeledata(dbconnect.connect_with_conf("server.json", "db"), 1684670903)
getTeledata(dbconnect.connect_with_conf("server.json", "db"), 1684673362)
getFinalClassification(dbconnect.connect_with_conf("server.json", "db"), 1684670903)
getFinalClassification(dbconnect.connect_with_conf("server.json", "db"), 1684673362)

getPosdata(dbconnect.connect_with_conf("server.json", "db"), 1684673362)




# deleteSessionData(dbconnect.connect_with_conf("server.json", "db"), 1)