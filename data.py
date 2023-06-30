import os, csv, json, xlsxwriter, traceback

import dbconnect
import mysql.connector

import deffunc as func
import image

# loading settings
settingsf = open("settings.json", "r")
settings:dict = json.load(settingsf)
settingsf.close()
# check output dir correct
dataoutdir = settings["data"]["outputdir"]
os.system(f'if not exist "{dataoutdir}" mkdir "{dataoutdir}"')
if dataoutdir[-1] != "/":
    dataoutdir += "/"

AInamelist = ["VERSTAPPEN","LECLERC","HAMILTON","NORRIS","VETTEL","ALONSO","SAINZ","BOTTAS","PÉREZ","GASLY",
              "ZHOU","ALBON","OCON","SCHUMACHER","STROLL","RICCIARDO","TSUNODA","MAGNUSSEN","LATIFI","RUSSELL",
              "勒克莱尔","维斯塔潘","拉塞尔","赛恩斯","佩雷兹","诺里斯","阿隆索","里卡多","欧肯","周","角田","加斯利",
              "舒马赫","马格努森","博塔斯","维特尔","斯特尔","阿尔本","拉蒂菲","汉密尔顿",""]







def getLapdata(db:mysql.connector.MySQLConnection,
               sessionid1:int=None, sessionid2:int=None, ipdec:int=None):
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
    
    print(func.delimiter_string(f'Lap time data ({sessionid2})', 60), end="\n\n")


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


    # making output folder
    folder = f'Laptime ({sessionid2})'
    os.system(f'if not exist "{dataoutdir}{folder}" mkdir "{dataoutdir}{folder}"')


    # making xlsx file
    workbook = xlsxwriter.Workbook(f'{dataoutdir}{folder}/Laptime.xlsx')

    for driver in sorted(laptimedata.keys()):
        lapdata = laptimedata[driver]

        # making csv file
        csvfile = open(f'{dataoutdir}{folder}/{lapdata[0][3]}.csv', "w", newline="", encoding='utf-8')
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
    
    print()


    # fastest lapfile
    query = f'SELECT beginUnixTime, curTime, carIndex, driverName, bestLapTimeLapNum, bestLapTimeInStr \
            FROM BestLap \
            WHERE beginUnixTime >= "{sessionid1}" AND beginUnixTime <= "{sessionid2}" \
                AND driverName in (SELECT driverName FROM Participants  \
                                   WHERE beginUnixTime >= "{sessionid1}" AND beginUnixTime <= "{sessionid2}" \
                                     AND aiControlled = 0) \
                AND ipDecimal = {ipdec} \
                AND curUnixTime = (SELECT u FROM (SELECT MAX(curUnixTime) u, beginUnixTime id \
                                                  FROM BestLap GROUP BY beginUnixTime) t \
                                    WHERE id >= "{sessionid1}" AND id <= "{sessionid2}") \
            ORDER BY CASE bestLapTimeInMS \
                    WHEN 0 THEN 2 \
                    ELSE 1 \
                END, bestLapTimeInMS ASC;'
    cursor.execute(query)
    result = cursor.fetchall()

    # making csv file
    csvfile = open(f'{dataoutdir}{folder}/fastest lap.csv', "w", newline="", encoding='utf-8')
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
    print(f'Writing fastest lap data......')
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
    print()




def getTeledata(db:mysql.connector.MySQLConnection,
               sessionid1:int=None, sessionid2:int=None, ipdec:int=None):
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
    
    print(func.delimiter_string(f'Telemetry data ({sessionid2})', 60), end="\n\n")


    # fetch session telemetry data
    query = f''
    cursor.execute(query)
    print(f'Fetching tele data from session {sessionid1} to {sessionid2}......')


    # fetch session telemetry data
    query = f'SELECT beginUnixTime, ipDecimal, curTime, carIndex, driverName, currentLapNum, \
                     lapDistance, currentLapTimeInStr, speed, steer, throttle, brake, gear, \
                     engineRPM, ersDeployMode, worldPositionX, worldPositionY, worldPositionZ \
            FROM LapDetails \
            WHERE beginUnixTime >= "{sessionid1}" AND beginUnixTime <= "{sessionid2}" \
              AND driverName in (SELECT driverName FROM Participants \
                                 WHERE beginUnixTime >= "{sessionid1}" AND beginUnixTime <= "{sessionid2}" \
                                 AND aiControlled = 0) \
            ORDER BY carIndex ASC, currentLapNum ASC, LapDistance ASC;'
    cursor.execute(query)
    result = cursor.fetchall()
    
    
    # catagorize telemetry data by driver
    telemetrydata = {}
    for record in result:
        try:
            telemetrydata[record[3]].append(record)
        except KeyError:
            telemetrydata[record[3]] = [record]
    
    
    # making output folder
    folder = f'Telemetry ({sessionid2})'
    os.system(f'if not exist "{dataoutdir}{folder}" mkdir "{dataoutdir}{folder}"')


    # making xlsx file
    # workbook = xlsxwriter.Workbook(f'{dataoutdir}{folder}/Telemetry.xlsx')

    for driver in sorted(telemetrydata.keys()):
        teledata = telemetrydata[driver]

        # making csv file
        csvfile = open(f'{dataoutdir}{folder}/{teledata[0][4]}.csv', "w", newline="", encoding='utf-8')
        header = ["frameIdentifier", "curTime", "driverName", "currentLapNum",
                  "lapDistance", "currentLapTime", "speed", "steer", "throttle", "brake", "gear",
                  "engineRPM", "ersDeployMode", "worldPositionX", "worldPositionY", "worldPositionZ"]
        writer = csv.DictWriter(csvfile, fieldnames=header)
        writer.writeheader()

        # making xlsx sheet
        # skip

        print(f'Writing telemetry data: {teledata[0][4]}......')
        for data in sorted(teledata, key=lambda x: (x[5], x[6])):
            data = {"frameIdentifier": data[1], "curTime": data[2], "driverName": data[4],
                    "currentLapNum": data[5], "lapDistance": data[6], "currentLapTime": data[7],
                    "speed": data[8], "steer": data[9], "throttle": data[10], "brake": data[11], "gear": data[12], 
                    "engineRPM": data[13], "ersDeployMode": data[14],
                    "worldPositionX": data[15], "worldPositionY": data[16], "worldPositionZ": data[17]}
            writer.writerow(data)
        
        csvfile.close()
    print()
    

    # output fastest lap telemetry
    # fastest lapdata
    query = f'SELECT beginUnixTime, curTime, carIndex, driverName, bestLapTimeLapNum, bestLapTimeInStr \
            FROM BestLap \
            WHERE beginUnixTime >= "{sessionid1}" AND beginUnixTime <= "{sessionid2}" \
                AND driverName in (SELECT driverName FROM Participants  \
                                   WHERE beginUnixTime >= "{sessionid1}" AND beginUnixTime <= "{sessionid2}" \
                                     AND aiControlled = 0) \
                AND ipDecimal = {ipdec} \
                AND curUnixTime = (SELECT u FROM (SELECT MAX(curUnixTime) u, beginUnixTime id \
                                                  FROM BestLap GROUP BY beginUnixTime) t \
                                    WHERE id >= "{sessionid1}" AND id <= "{sessionid2}") \
            ORDER BY CASE bestLapTimeInMS \
                    WHEN 0 THEN 2 \
                    ELSE 1 \
                END, bestLapTimeInMS ASC;'
    cursor.execute(query)
    result = cursor.fetchall()

    # making output folder
    folder = f'Fastestlap Telemetry ({sessionid2})'
    os.system(f'if not exist "{dataoutdir}{folder}" mkdir "{dataoutdir}{folder}"')

    for driver in result:
        carindex = driver[2]
        fllapnum = driver[4]
        teledata = telemetrydata[carindex]

        # making csv file
        csvfile = open(f'{dataoutdir}{folder}/{teledata[0][4]}.csv', "w", newline="", encoding='utf-8')
        header = ["frameIdentifier", "curTime", "driverName", "currentLapNum",
                  "lapDistance", "currentLapTime", "speed", "steer", "throttle", "brake", "gear",
                  "engineRPM", "ersDeployMode", "worldPositionX", "worldPositionY", "worldPositionZ"]
        writer = csv.DictWriter(csvfile, fieldnames=header)
        writer.writeheader()

        print(f'Writing fastestlap telemetry data: {teledata[0][4]}......')
        for data in sorted(teledata, key=lambda x: (x[5], x[6])):
            data = {"frameIdentifier": data[1], "curTime": data[2], "driverName": data[4],
                    "currentLapNum": data[5], "lapDistance": data[6], "currentLapTime": data[7],
                    "speed": data[8], "steer": data[9], "throttle": data[10], "brake": data[11], "gear": data[12], 
                    "engineRPM": data[13], "ersDeployMode": data[14],
                    "worldPositionX": data[15], "worldPositionY": data[16], "worldPositionZ": data[17]}
            if data["currentLapNum"] == fllapnum:
                writer.writerow(data)
        
        csvfile.close()
    print()




def getTeleFL(db:mysql.connector.MySQLConnection,
            sessionid1:int=None, sessionid2:int=None, ipdec:int=None):
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
    
    print(func.delimiter_string(f'FastestLap tele data ({sessionid2})', 60), end="\n\n")





def getPosdata(db:mysql.connector.MySQLConnection,
               sessionid1:int=None, sessionid2:int=None, ipdec:int=None):
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

    print(func.delimiter_string(f'Race position data ({sessionid2})', 60), end="\n\n")
    

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


    # making output folder
    folder = f'Position ({sessionid2})'
    os.system(f'if not exist "{dataoutdir}{folder}" mkdir "{dataoutdir}{folder}"')

    posfilelist = []
    for driver in sorted(positiondata.keys()):
        driverposdata = positiondata[driver]

        # making csv file
        csvfile = open(f'{dataoutdir}{folder}/{driver}.csv', "w", newline="", encoding='utf-8')
        header = ["driverName", "lapNum", "position"]
        writer = csv.DictWriter(csvfile, fieldnames=header)
        writer.writeheader()

        # writing to csv file
        print(f'Writing position data: {driver}......')
        for lap in sorted(driverposdata):
            data = {"driverName": driver, "lapNum": lap, "position": driverposdata[lap]}
            writer.writerow(data)
        
        csvfile.close()
        posfilelist.append(f'{dataoutdir}{folder}/{driver}.csv')

    print("Exporting race position summary graph......")
    image.getPositionImage(posfilelist, f'{dataoutdir}{folder}/')
    print()




def getTyretempdata(db:mysql.connector.MySQLConnection,
                sessionid1:int=None, sessionid2:int=None, ipdec:int=None):
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

    print(func.delimiter_string(f'Tyre wear data ({sessionid2})', 60), end="\n\n")


    # fetching tyre temperature data
    query = f'SELECT CarTelemetry.beginUnixTime, CarTelemetry.curTime, CarTelemetry.CarIndex, CarTelemetry.driverName, \
                     LapData.currentLapNum, LapData.lapDistance, \
                     CarTelemetry.tyresSurfaceTemperatureFL, CarTelemetry.tyresSurfaceTemperatureFR, \
                     CarTelemetry.tyresSurfaceTemperatureRL, CarTelemetry.tyresSurfaceTemperatureRR, \
                     CarTelemetry.tyresInnerTemperatureFL, CarTelemetry.tyresInnerTemperatureFR, \
                     CarTelemetry.tyresInnerTemperatureRL, CarTelemetry.tyresInnerTemperatureRR \
            FROM CarTelemetry JOIN LapData \
                                ON CarTelemetry.beginUnixTime = LapData.beginUnixTime \
                               AND CarTelemetry.curUnixTime = LapData.curUnixTime \
                               AND CarTelemetry.carIndex = LapData.carIndex \
                               AND CarTelemetry.ipDecimal = LapData.ipDecimal \
            WHERE CarTelemetry.beginUnixTime >= "{sessionid1}" AND CarTelemetry.beginUnixTime <= "{sessionid2}" \
              AND CarTelemetry.driverName in (SELECT driverName FROM Participants  \
                                              WHERE beginUnixTime >= "{sessionid1}" AND beginUnixTime <= "{sessionid2}" \
                                                AND aiControlled = 0) \
              AND CarTelemetry.ipDecimal = {ipdec} \
            ORDER BY CarTelemetry.carIndex ASC ,CarTelemetry.curUnixTime ASC;'
    print(f'Fetching tyre temp data from session {sessionid1} to {sessionid2}......')
    cursor.execute(query)
    result = cursor.fetchall()

    # catagorize tyre temperature data by driver
    tyretempdata = {}
    for record in result:
        try:
            tyretempdata[record[2]].append(record)
        except KeyError:
            tyretempdata[record[2]] = [record]

    
    # making output folder
    folder = f'Tyre Temperature ({sessionid2})'
    os.system(f'if not exist "{dataoutdir}{folder}" mkdir "{dataoutdir}{folder}"')


    # making xlsx file
    workbook = xlsxwriter.Workbook(f'{dataoutdir}{folder}/TyreTemp.xlsx')

    for driver in sorted(tyretempdata.keys()):
        tyredata = tyretempdata[driver]

        # making csv file
        csvfile = open(f'{dataoutdir}{folder}/{tyredata[0][3]}.csv', "w", newline="", encoding='utf-8')
        header = ["Lap", "driverName", "LapDistance",
                  "SurfaceFL", "SurfaceFR", "SurfaceRL", "SurfaceRR",
                  "InnerFL", "InnerFR", "InnerRL", "InnerRR"]
        writer = csv.DictWriter(csvfile, fieldnames=header)
        writer.writeheader()

        # making xlsx sheet
        tyretempsheet = workbook.add_worksheet(tyredata[0][3])
        tyretempsheet.set_column(0,0, 8)
        tyretempsheet.set_column(1,1, 25)
        tyretempsheet.set_column(2,2, 11)
        tyretempsheet.set_column(3,10, 9)

        defaultformat = workbook.add_format({"font_size":11})
        defaultformat.set_font_name("Dengxian")
        defaultformat.set_align("vcenter")
        defaultformat.set_text_wrap()

        # writing header
        for i in range(0, len(header)):
            tyretempsheet.write(0, i, header[i], defaultformat)
        

        rowcursor = 1
        print(f'Writing tyre temp data: {tyredata[0][3]}......')
        for record in sorted(tyredata, key=lambda x:x[1]):
            # writing to csv file
            data = {"Lap": record[4], "driverName": record[3], "LapDistance": record[5],
                    "SurfaceFL": record[6], "SurfaceFR": record[7], "SurfaceRL": record[8], "SurfaceRR": record[9],
                    "InnerFL": record[10], "InnerFR": record[11], "InnerRL": record[12], "InnerRR": record[13]}
            writer.writerow(data)

            # writing to xlsx file
            tyretempsheet.write(rowcursor, 0, record[4], defaultformat)
            tyretempsheet.write(rowcursor, 1, record[3], defaultformat)
            tyretempsheet.write(rowcursor, 2, record[5], defaultformat)
            tyretempsheet.write(rowcursor, 3, record[6], defaultformat)
            tyretempsheet.write(rowcursor, 4, record[7], defaultformat)
            tyretempsheet.write(rowcursor, 5, record[8], defaultformat)
            tyretempsheet.write(rowcursor, 6, record[9], defaultformat)
            tyretempsheet.write(rowcursor, 7, record[10], defaultformat)
            tyretempsheet.write(rowcursor, 8, record[11], defaultformat)
            tyretempsheet.write(rowcursor, 9, record[12], defaultformat)
            tyretempsheet.write(rowcursor, 10, record[13], defaultformat)
            rowcursor += 1

        csvfile.close()
    
    workbook.close()
    print()




def getTyreweardata(db:mysql.connector.MySQLConnection,
                sessionid1:int=None, sessionid2:int=None, ipdec:int=None):
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

    print(func.delimiter_string(f'Tyre wear data ({sessionid2})', 60), end="\n\n")


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

    
    # making output folder
    folder = f'Tyre Wear ({sessionid2})'
    os.system(f'if not exist "{dataoutdir}{folder}" mkdir "{dataoutdir}{folder}"')


    # making xlsx file
    workbook = xlsxwriter.Workbook(f'{dataoutdir}{folder}/TyreWear.xlsx')

    for driver in sorted(tyreweardata.keys()):
        tyredata = tyreweardata[driver]

        # making csv file
        csvfile = open(f'{dataoutdir}{folder}/{tyredata[0][3]}.csv', "w", newline="", encoding='utf-8')
        header = ["Lap", "driverName", "FL", "FR", "RL", "RR"]
        writer = csv.DictWriter(csvfile, fieldnames=header)
        writer.writeheader()

        # making xlsx sheet
        tyrewearsheet = workbook.add_worksheet(tyredata[0][3])
        tyrewearsheet.set_column(0,0, 8)
        tyrewearsheet.set_column(1,1, 25)
        tyrewearsheet.set_column(2,5, 6)

        defaultformat = workbook.add_format({"font_size":11})
        defaultformat.set_font_name("Dengxian")
        defaultformat.set_align("vcenter")
        defaultformat.set_text_wrap()

        # writing header
        for i in range(0, len(header)):
            tyrewearsheet.write(0, i, header[i], defaultformat)

        rowcursor = 1
        print(f'Writing tyre wear data: {tyredata[0][3]}......')
        for lap in sorted(tyredata, key=lambda x:x[4]):
            # writing to csv file
            data = {"Lap": lap[4], "driverName": lap[3], "FL": lap[5],
                    "FR": lap[6], "RL": lap[7], "RR": lap[8]}
            writer.writerow(data)

            # writing to xlsx file
            tyrewearsheet.write(rowcursor, 0, lap[4], defaultformat)
            tyrewearsheet.write(rowcursor, 1, lap[3], defaultformat)
            tyrewearsheet.write(rowcursor, 2, lap[5], defaultformat)
            tyrewearsheet.write(rowcursor, 3, lap[6], defaultformat)
            tyrewearsheet.write(rowcursor, 4, lap[7], defaultformat)
            tyrewearsheet.write(rowcursor, 5, lap[8], defaultformat)
            rowcursor += 1

        csvfile.close()

    workbook.close()
    print()




def getFinalClassification(db:mysql.connector.MySQLConnection,
                           sessionid1:int=None, sessionid2:int=None, ipdec:int=None):
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

    print(func.delimiter_string(f'Final Classification data ({sessionid2})', 60), end="\n\n")


    # fetch session final classification data
    query = f'SELECT beginUnixTime, curTime, position, driverName, \
                     numLaps, gridPosition, numPitStops, \
                     bestLapTimeStr, totalRaceTimeStr, overallResult, \
                     numPenalties, penaltiesTime, tyreStintsVisual \
            FROM FinalClassification \
            WHERE beginUnixTime >= "{sessionid1}" AND beginUnixTime <= "{sessionid2}" \
              AND ipDecimal = {ipdec} \
            ORDER BY position ASC;'
    cursor.execute(query)
    print(f'Fetching finalclassification data from session {sessionid1} to {sessionid2}......')
    result = cursor.fetchall()


    # making output folder
    folder = f'Final Classification'
    os.system(f'if not exist "{dataoutdir}{folder}" mkdir "{dataoutdir}{folder}"')


    # making csv file
    csvfile = open(f'{dataoutdir}{folder}/FinalClassification_{sessionid2}.csv', "w", newline="", encoding='utf-8')
    header = ["position", "driverName", "numLaps", "grid", "pits",
              "bestlap", "totaltime", "gap", "numPen", "penalty", "tyreStint"]
    writer = csv.DictWriter(csvfile, fieldnames=header)
    writer.writeheader()


    # making xlsx file
    workbook = xlsxwriter.Workbook(f'{dataoutdir}{folder}/FinalClassification_{sessionid2}.xlsx')
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
    print()


    # get race diretcor data of the session by the way
    getRaceDirector(db, sessionid1, sessionid2, ipdec)




def getRaceDirector(db:mysql.connector.MySQLConnection,
                    sessionid1:int=None, sessionid2:int=None, ipdec:int=None):
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

    print(func.delimiter_string(f'Race Director data ({sessionid2})', 60), end="\n\n")
    

    # fetch session race director data
    query = f'SELECT beginUnixTime, curTime, lapNum, driverName, otherDriverName, \
                     penaltyDescription, infringementDescription, timeGained, placesGained \
            FROM PenaltyUpdate \
            WHERE beginUnixTime >= "{sessionid1}" AND beginUnixTime <= "{sessionid2}" \
              AND ipDecimal = {ipdec} \
            ORDER BY curTime ASC;'
    cursor.execute(query)
    print(f'Fetching racedirector data from session {sessionid1} to {sessionid2}......')
    result = cursor.fetchall()

    # making output folder
    folder = f'Final Classification'
    os.system(f'if not exist "{dataoutdir}{folder}" mkdir "{dataoutdir}{folder}"')

    
    # making csv file
    csvfile = open(f'{dataoutdir}{folder}/RaceDirector_{sessionid2}.csv', "w", newline="", encoding='utf-8')
    header = ["Lap", "driverName", "driverInvolved", "PenaltyType", "PenaltyDescriptions",
              "timeGained", "placeGained"]
    writer = csv.DictWriter(csvfile, fieldnames=header)
    writer.writeheader()


    # making xlsx file
    workbook = xlsxwriter.Workbook(f'{dataoutdir}{folder}/RaceDirector_{sessionid2}.xlsx')
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
    print()




def getWeatherReport(db:mysql.connector.MySQLConnection,
                     sessionid1:int=None, sessionid2:int=None, ipdec:int=None):
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

    print(func.delimiter_string(f'Weather report ({sessionid2})', 60), end="\n\n")


    # fetch weather report data
    query = f'SELECT beginUnixTime, curTime, timeOffset, sessionTypeInStr, \
                     weatherInStr, rainPercentage, trackTemperature \
            FROM WeatherForecast \
            WHERE beginUnixTime >= "{sessionid1}" AND beginUnixTime <= "{sessionid2}" \
              AND curUnixTime = (SELECT MIN(curUnixTime) FROM WeatherForecast \
                                 WHERE beginUnixTime >= "{sessionid1}" AND beginUnixTime <= "{sessionid2}") \
              AND ipDecimal = {ipdec} \
            ORDER BY curTime ASC, sessionTypeInStr ASC, timeOffset ASC;'
    print(f'Fetching weather report from session {sessionid1} to {sessionid2}......')
    cursor.execute(query)
    result = cursor.fetchall()


    # making output folder
    folder = f'Final Classification'
    os.system(f'if not exist "{dataoutdir}{folder}" mkdir "{dataoutdir}{folder}"')


    # making csv file
    csvfile = open(f'{dataoutdir}{folder}/WeatherReport_{sessionid2}.csv', "w", newline="", encoding='utf-8')
    header = ["Time", "timeOffset", "Session", "Weather", "RainPct.", "TrackTemp"]
    writer = csv.DictWriter(csvfile, fieldnames=header)
    writer.writeheader()


    # making xlsx file
    workbook = xlsxwriter.Workbook(f'{dataoutdir}{folder}/WeatherReport_{sessionid2}.xlsx')
    weathersheet = workbook.add_worksheet(f'WeatherReport_{sessionid2}')
    weathersheet.set_column(0,0, 20)
    weathersheet.set_column(1,1, 9)
    weathersheet.set_column(2,2, 10)
    weathersheet.set_column(2,2, 10)
    weathersheet.set_column(3,3, 15)
    weathersheet.set_column(4,4, 7)
    weathersheet.set_column(5,5, 10)


    defaultformat = workbook.add_format({"font_size":11})
    defaultformat.set_font_name("Dengxian")
    defaultformat.set_align("vcenter")
    defaultformat.set_text_wrap()

    # writing header
    for i in range(0, len(header)):
        weathersheet.write(0, i, header[i], defaultformat)
    

    rowcursor = 1
    print(f'Writing weather report data from session {sessionid1} to {sessionid2}......')
    for record in result:
        # writing to csv file
        data = {"Time": record[1], "timeOffset": record[2], "Session": record[3],
                "Weather": record[4], "RainPct.": record[5], "TrackTemp": record[6]}
        writer.writerow(data)


        # writing to xlsx file
        weathersheet.write(rowcursor, 0, record[1].strftime("%Y-%m-%d %H:%M:%S"), defaultformat)
        weathersheet.write(rowcursor, 1, record[2], defaultformat)
        weathersheet.write(rowcursor, 2, record[3], defaultformat)
        weathersheet.write(rowcursor, 3, record[4], defaultformat)
        weathersheet.write(rowcursor, 4, record[5], defaultformat)
        weathersheet.write(rowcursor, 5, record[6], defaultformat)
        rowcursor += 1

    csvfile.close()
    workbook.close()
    print()




def deleteSessionData(db:mysql.connector.MySQLConnection,
                      sessionid1:int=None, sessionid2:int=None):
    cursor = db.cursor()
    
    if sessionid1 == None:
        sessionid1, sessionid2 = func.asksessionid()
    elif sessionid1 != None and sessionid2 == None:
        sessionid2 = sessionid1

    if sessionid1 == None or sessionid2 == None:
        print("no or error session id")
        return None
    elif sessionid1 == "Nosession" and sessionid2 == "Nosession":
        print("no or error session id")
        return None
    
    print(func.delimiter_string(f'Delete data ({sessionid1} - {sessionid2})', 60), end="\n\n")


    query = f'SHOW full tables WHERE Table_Type = "BASE TABLE";'
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
        except mysql.connector.errors.ProgrammingError as e:
            print(str(e))
            continue

    db.commit()
    print()








# ------ testing use case ------ #
sessionid1 = 1687003456
sessionid2 = 1687003456
sessionid3 = 1687005345
sessionid4 = 1687005345

# getLapdata(dbconnect.connect_with_conf("server.json", "db"), sessionid1)
# getLapdata(dbconnect.connect_with_conf("server.json", "db"), sessionid3)
# getTeledata(dbconnect.connect_with_conf("server.json", "db"), sessionid1)
# getTeledata(dbconnect.connect_with_conf("server.json", "db"), sessionid3)
# getPosdata(dbconnect.connect_with_conf("server.json", "db"), sessionid3)
# getTyreweardata(dbconnect.connect_with_conf("server.json", "db"), sessionid3)
# getTyretempdata(dbconnect.connect_with_conf("server.json", "db"), sessionid1)
# getTyretempdata(dbconnect.connect_with_conf("server.json", "db"), sessionid3)

# getFinalClassification(dbconnect.connect_with_conf("server.json", "db"), sessionid1)
# getFinalClassification(dbconnect.connect_with_conf("server.json", "db"), sessionid3)
# getRaceDirector(dbconnect.connect_with_conf("server.json", "db"), sessionid1)
# getRaceDirector(dbconnect.connect_with_conf("server.json", "db"), sessionid3)

# getWeatherReport(dbconnect.connect_with_conf("server.json", "db"), sessionid1)




# deleteSessionData(dbconnect.connect_with_conf("server.json", "db"), 1)