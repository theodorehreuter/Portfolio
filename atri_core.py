#  This script is written by Theodore Reuter, Geospatial Fellow working at the USDOT BTS OSAV OST on the port performance project.  This script is designed to
# take csv inputs of GPS points and run them through python geospatial packages and scripts to produce truck turn times.  Turn time is defined as the amount of time
# a truck spends inside the target polygon (terminal) on a given trip (visitng and picking up a container, entering, inhabiting, and leaving the terminal).
import os
import numpy as np
import pandas as pd
import geopandas as gp
import shapely as shp
csvname = input("Please enter the name of the output trip table csv, including .csv : ")
csvfolder = input("Please enter the name of the absolute path for the folder you would like to save the csv in: ")
pd.set_option('display.max_columns', None)  # set to see all columns I'm working with
pd.set_option('display.width', 400)  # display width of console so all columns are displayed
folder = r"C:\Users\treuter\Desktop\Theo\Queries\Outputs"  # folder holding query results
file = "v1_LA_LB_201811.csv"
fullfile = "lalb_core_112018.csv"
tester = "dda7e0dd16b947b695702ae5f099be_core_nov2018.csv"
loc = os.path.join(folder, file)  # create location I can pass to pandas dataframe command
fullloc = os.path.join(folder, fullfile)
print(fullloc)
# create pandas data frame and set the first row as column headers - bring in GPS data to a dataframe
df = pd.read_csv(fullloc, header=0, dtype={"fmi_atri_truck_gps_core.heading": str, "fmi_atri_truck_gps_core.truckid": str})

# rename columns to be shorter
df.rename(columns={
    "fmi_atri_truck_gps_core.readdate": "readdate",
    "fmi_atri_truck_gps_core.y": "y",
    "fmi_atri_truck_gps_core.x": "x",
    "fmi_atri_truck_gps_core.speed": "speed",
    "fmi_atri_truck_gps_core.heading": "heading",
    "fmi_atri_truck_gps_core.truckid": "truckid",
    "fmi_atri_truck_gps_core.version": "version",
    "fmi_atri_truck_gps_core.rdate": "rdate"
}, inplace=True)
df = df.drop(['version', 'rdate'], 1)  # drop unneccesary column.  Fewer columns now with millions of points, the better
# commence the analysis.  On my signal, unleash pandas!  Bring on the bamboo!
df.insert(6, "datetime", "Any")  # add new column to end called 'datetime' and populate every row with value 'any'
df['datetime'] = pd.to_datetime(df['readdate'])  # set value of 'datetime' column to readdate and convert to datetime type
# create a geometry column using shapely and set each value to the tuple x,y where x is the x column from data frame and y is y column from dataframe
geometry = [shp.geometry.Point(xy) for xy in zip(df['x'], df['y'])]
crs = {'init': 'epsg:4326'}  # create a dictionary of coordinate system that will be passed to the geodataframe creation statement
gdf = gp.GeoDataFrame(df, crs=crs, geometry=geometry)  # create geodataframe using the data frame, crs created, and set geometry column equal to points created 2 lines up
gdf = gdf.drop('readdate', 1)  # drop now redundant original readdate field
print("Before dropping duplicates we have " + str(len(gdf.index)) + " rows")
termshp = gp.read_file(r"C:\Users\treuter\Desktop\Theo\PortPerformance\Shapefiles\LA_FMS.shp") # bring in terminal shapefile as GeoDataFrame Object

#explore for duplicates
dupsAll = gdf.pivot_table(index=['truckid', 'speed', 'heading', 'x', 'y', 'datetime'], aggfunc='size')  # pivot table tallying duplicates
sorted = dupsAll.sort_values(0, ascending=False)  # create sorted list of duplicates by which descends by most dupes to least
gdf = gdf.drop_duplicates(['truckid', 'speed', 'heading', 'x', 'y', 'datetime'])  # drop duplicates if they columns listed are all alike
print("After dropping duplicates we have " + str(len(gdf.index)) + " rows")  # compare rows

# test for point IN/OUT quality - IN if inside the terminal in question, OUT if outside terminal
gdf.insert(6, "In_Out", "Any")  # add new column to end called 'datetime' and populate every row with value 'any'
termpoly = termshp.loc[0, 'geometry']  # creates a shapely.geometry.polygon.Polygon object - geometry object representing terminal polygon that can be passed
gdf['In_Out'] = np.where(gdf['geometry'].within(termpoly), 'IN', 'OUT') # run conditional and test point geometry and set 'in_out' field based on rel with term poly
inside = gdf.loc[gdf['In_Out'] == 'IN']  # create a dataframe of only points that are inside the terminal

# create series of dataframe where each is all the datapoints for one truckid

listgdfs = []  # create empty list that will be filled with separate dataframe representing each turck
for x in inside['truckid'].unique():  # create loop to run over list of unique truckids for any trucks that enter the terminal
    newframe = gdf.loc[gdf['truckid'] == x]  # create a dataframe that is only the gps points for a truck with truckids that are at any time inside the terminal
    newframe.reset_index(drop=True, inplace=True)  # reset index of every dataframe for ease of later counting
    listgdfs.append(newframe)  # append this dataframe to the list of dataframes
print("List of dataframes by truckid created")
print("We have " + str(len(inside['truckid'].unique())) + " unique truckids of trucks that enter the terminal")  #testing lengths to see how many dataframes I should have
print("list of dataframe has " + str(len(listgdfs)) + " entries")  # getting number of new dataframes created
tottrucks = len(listgdfs)
print("Testing that all records are present")
sumlist = []  # create blank list for all rows test
for x in listgdfs:
    length = int(len(x.index))  # get number of rows in a given dataframe
    sumlist.append(length)  # append this integer to the blank list
totrows = sum(sumlist)  # sum list (each entry which represents the rows in a given separated dataframe)
print("Total rows in separate dataframes is: " + str(totrows))  # this output should be equal to the # rows in first imported dataframe
# column names for master summary dataframe
summaryColNames = ['truckid', 'TruckTripID', 'inside_pings', 'Entry_Time', 'Exit_Time', 'Time_In_Term', 'Time_In_Term (sec)', "max_ping_gap",
                   "min_ping_gap", "median_ping_gap,", "mean_ping_gap", "std_dev_ping_gap", "Time_Ping_Out_To_In", "Time_Ping_In_To_Out"]
SummaryFrame = pd.DataFrame(columns=summaryColNames) # create empty master summary dataframe

# following big loop will create a dataframe that is a summary of all the trips through the terminal for a given truck id
# After calculating trips for a given truck this miniframe will be appended to the master dataframe created in the previous line of code

print("commencing master loop")
counter = 0  # set to zero progress counter.  Will use this to follow how far along the code is when processing millions of records and thousands of truck ids
trucksinterm = inside['truckid'].unique()  # get list of truck ids that have points in terminal - will loop through this list of ids
for p in trucksinterm:
    # first calculate time lag between points
    workdf = gdf.loc[gdf['truckid'] == p].copy()  # place holder line to work with one truckid that I know enters the terminal
    # workdf = listgdfs[x].copy()  # grab a dataframe from list of dataframes
    # added .copy() so that pandas knows this is a new dataframe I'm working on and not just a slice of gdf, otherwise getting settingwithcopy warning
    workdf = workdf.sort_values(by='datetime', ascending=True)  # sort a dataframe of a given truckids gps points by datetime field in chronological order
    workdf.reset_index(drop=True, inplace=True)  # reset index in place - MUST COME AFTER DATETIME SORTING or screws stuff up cause indexes get remixed
    workdf.insert(7, "Time_Lag", "Any")  # add new column to end called 'time_lag' and populate every row with value 'any'
    print("added time lag column")

    for x in workdf.index:
        #set a specific 'time-lag' field by subtracting the previous row's datetime from the datetime of the row in question
        # represents time between two consecutive gps pings
        workdf.loc[workdf.index[x], 'Time_Lag'] = workdf.loc[workdf.index[x], 'datetime'] - workdf.loc[workdf.index[x -1], 'datetime']
    # go back and force set the first entry to not a number because we do not know where it was before this point - likely cut off by our bounding box in query
    workdf.loc[min(workdf.index), 'Time_Lag'] = 'NaT'

    # add markers to indicate if a point is the first in or out of a terminal
    workdf.insert(8, "Entry_Exit", "Any")
    print("Added entry_exit column")
    for z in workdf.index:
        if workdf.loc[workdf.index[z], 'In_Out'] == 'OUT' and workdf.loc[workdf.index[z-1], 'In_Out'] == 'IN':
            workdf.loc[workdf.index[z], 'Entry_Exit'] = 'EXIT'  # if previous point was 'IN" and this point is "OUT" call it an exit point
        elif workdf.loc[workdf.index[z], 'In_Out'] == 'IN' and workdf.loc[workdf.index[z-1], 'In_Out'] == 'OUT':
            workdf.loc[workdf.index[z], 'Entry_Exit'] = 'ENTRY'  # if previous point was "OUT" and this point is 'IN' call it an entry point
        else:
            workdf.loc[workdf.index[z], 'Entry_Exit'] = ''  # if a point is not exit or entry, leave this field empty
    workdf.loc[min(workdf.index), 'Entry_Exit'] = 'NaN'  # set first point to NaN because we do not know what came before

    workdf.insert(9, "SegmentID", "Any")  # create new column
    print("Added SegmentID column")
    segnum = 1  # first segment for any truck frame will be number 1
    for y in workdf.index:
        if y == 0:
            workdf.loc[workdf.index[y], 'SegmentID'] = segnum  # set first row to segment 1
        elif workdf.loc[workdf.index[y], 'In_Out'] == workdf.loc[workdf.index[y-1], 'In_Out']:  # if both rows are the same relationship to terminal (In/out) continue segment number
            workdf.loc[workdf.index[y], 'SegmentID'] = segnum
        elif workdf.loc[workdf.index[y], 'In_Out'] != workdf.loc[workdf.index[y-1], 'In_Out']:  # if consecutive rows are not the same relationship to terminal (in/out) new segment
            segnum = segnum + 1  # increase counter to indicate new segment
            workdf.loc[workdf.index[y], 'SegmentID'] = segnum

    workdf.insert(10, "TripSeg", "Any")
    workdf['TripSeg'] = workdf['In_Out'] + "-" + workdf['SegmentID'].astype(str)  # create  a column identifying each column
    print("Added and created TripSeg column")

    workdf.insert(11, "TruckTrip", "Any")
    workdf['TruckTrip'] = workdf['truckid'].astype(str) + "-" + workdf['TripSeg']  # create a unique id for each trip through terminal with truck and trip id
    print("Added and created TruckTrip unique trip ID column")

    TermTrips = workdf.loc[workdf["In_Out"] == 'IN']
    # create list of unique values of trips of truck pings IN the terminal.  T
    segmentlist = TermTrips.SegmentID.unique()
    # print(segmentlist)
    arraylist = []  # empty list that I will fill with lists of array values
    tripcolumns = ['truckid', 'TruckTripID', 'inside_pings', 'Entry_Time', 'Exit_Time', 'Time_In_Term', 'Time_In_Term (sec)', "max_ping_gap",
                   "min_ping_gap", "median_ping_gap,", "mean_ping_gap", "std_dev_ping_gap", "Time_Ping_Out_To_In", "Time_Ping_In_To_Out"]

    # DO NOT CHANGE ORDER OF FOLLOWING LOOP OPERATIONS UNLESS YOU WANT TROUBLE
    #  Will be appending values in the order of the column names in the above list 'tripcolumns' so they
    #  match for the array that will be turned into a dataframe.  Bad order, info goes in wrong problem, bad news bears.  Proceed with caution
    for x in segmentlist:
        values = []  # empty list that will be filled with calculated values and then appended to master list which will be passed to np.array
        tripframe = workdf.loc[workdf['SegmentID'] == x].copy()  # create a trip frame.   Will calculate stuff like trip time from this frame
        values.append(tripframe.loc[min(tripframe.index), 'truckid'])   # get truckid and append - same every segment here but vary across big loop
        values.append(tripframe.loc[min(tripframe.index), 'TruckTrip'])  # append trucktrip Id so each trip has unique id
        values.append(len(tripframe.index))  # append the number of pings
        values.append(tripframe.loc[min(tripframe.index), 'datetime'])  # grab first datetime in in trip and append it as the 'entry-time'
        ExitPtIndex = max(tripframe.index) + 1  # KEY STEP KEY STEP get index value of next point - this is first point outside terminal, will be considered part of this trip
        # accomodate condition of if last row in dataframe is "IN" there will not be an next point to join
        if ExitPtIndex in tripframe.index:
            # KEY STEP append get first row after last 'IN' point will be last point of this 'trip' and ther "EXIT" point.
            # ESSENTIAL - sorting by only inside points earlier, we are counting the first point outside the terminal as the 'exit point' and 'exit time'
            fullTripFrame = tripframe.append(workdf.loc[ExitPtIndex])
        else:  # if last row in dataframe is "IN" simple change variable name and we append nothing - boundary case
            fullTripFrame = tripframe
        values.append(fullTripFrame.loc[max(fullTripFrame.index), 'datetime'])  # append to summary frame as exit time datetime of first point outside terminal poly
        # append last time lag point - difference between last point registered in terminal and first point outside.  Need to know this time for possible filtering
        # print(fullTripFrame)
        values.append(fullTripFrame['Time_Lag'].sum())  # append value for 'Time In Term' column - sum of time lags between last point before going in terminal and first point coming out
        values.append((fullTripFrame['Time_Lag'].sum()).total_seconds())  # turn the total time delta into seconds and append to list for eventual inclusion in final output

        # reset index so following loop works othersie values in index are way off - need to use indexes to calculate trip lengths etc
        fullTripFrame.reset_index(drop=True, inplace=True)
        # cannot directly calcuate mean and std of timedeltas, so will create new column converting timedelta to seconds and then calcstats at a later date
        fullTripFrame.insert(13, "Time_Lag_Sec", "Any")  # as a new column so can calucate stats on ping lags
        print("calculating ping stats")
        print(fullTripFrame.index)
        for y in fullTripFrame.index:
            if y == min(fullTripFrame.index):  # this will be the NaT case
                if fullTripFrame.loc[fullTripFrame.index[y], 'Time_Lag'] == 'NaT':
                    fullTripFrame.loc[fullTripFrame.index[y], 'Time_Lag_Sec'] = None
                else:
                    fullTripFrame.loc[fullTripFrame.index[y], 'Time_Lag_Sec'] = fullTripFrame.loc[fullTripFrame.index[y], 'Time_Lag'].total_seconds()
            else:
                # convert timedelta to seconds so I can run mean, std, median
                fullTripFrame.loc[fullTripFrame.index[y], 'Time_Lag_Sec'] = fullTripFrame.loc[fullTripFrame.index[y], 'Time_Lag'].total_seconds()
        # print("Finished calculating time lag in sec now time lag stats")
        values.append(fullTripFrame['Time_Lag_Sec'].max())  # get max time lag between pings and append to trip summary
        values.append(fullTripFrame['Time_Lag_Sec'].min())  # get min time lag between pings and append to trip summary
        values.append(fullTripFrame['Time_Lag_Sec'].median())  # append the median value in seconds of time pings to trip summary list
        values.append(fullTripFrame['Time_Lag_Sec'].mean())  # append the mean value in seconds of time pings to trip summary list
        values.append(fullTripFrame['Time_Lag_Sec'].std())  # get std in seconds and append to trip summary list
        values.append(fullTripFrame.loc[min(fullTripFrame.index), 'Time_Lag_Sec'])  # appends time for "Time_Ping_Out_To_In" to summary list
        values.append(fullTripFrame.loc[max(fullTripFrame.index), 'Time_Lag_Sec'])  # append last time lag for '"Time_Ping_In_To_Out" to summary list
        arraylist.append(values)  #  append trip stats list to list, starting to create array of lists that will make up trip summaries frame for a truck
        # end loop for getting data for various trips for a second truck.

    trucksummaryframe = pd.DataFrame(np.array(arraylist), columns=tripcolumns)  # create new dataframe out of trip summaries created in above loop
    # will next seek to append this summary mini-frame to the master summmary frame
    print(trucksummaryframe)
    SummaryFrame = SummaryFrame.append(trucksummaryframe, ignore_index=True)  # append mini-frame to master summary frame and reset index every time
    counter = counter + 1  # increase progress counter
    remaining = tottrucks - counter  # update remaining counter
    print("completed a truck summary!  Only " + str(remaining) + " to go!")  # progress message

print(SummaryFrame)
print("All done.  Whew.")
# export trip summary table as csv
csvpath = os.path.join(csvfolder, csvname)
SummaryFrame.to_csv(csvpath)  # output table as csv
