# This python code will be used to extract the table data from the parameterization test runs in LandTrendr
# I will be running different runs in LandTrendr in Google Earth Engine to test how the black box model, LandTrendr, used
# to classify land change over a remote sensing time series, varies based on systematic adjustment of the model parameters in Google Earth Engine
# I am testing this parameterization over a few main polygons with similar file names which leads to the specific string indexing in the
# function preprocessing.  The output rasters from numerous runs will then have their data extracted and put into a csvs to allow for quantitative
# comparisons across the 80+ rasters.


import arcpy
print "Arcpy imported!"
import os
print "os imported!"
arcpy.CheckOutExtension("3D")  # check out extension so the int function can be used

class PathError(Exception):  # create error for path error of gdb
    pass

try:
    def preprocessing(x, shape, RasterLoc, Loc):
        print x  # print name of file being worked with on any given loop
        name = x[0:-4]  # select out just the name minus .tif
        outname = name + "_proj"  # create output name for projected raster
        inputloc = RasterLoc + os.sep + x  # raster location to be passed to project_raster since it's just stored in a folder
        clipped = name + "_clipped"  # name for output of clipped raster
        RowsLoc = Loc + os.sep + name + ".csv"  # name for csv file output by
        projected = arcpy.ProjectRaster_management(inputloc, outname, ELC)  # run project raster first because running it at the end was causing problems with the empty rasters earlier running int or clip first
        intname = name + "_int"  # name for int output
        Int = arcpy.Int_3d(projected, intname)  # run int output to generate attribute table that can be exported
        arcpy.Delete_management(projected)  # delete projected raster
        arcpy.Clip_management(Int, "", clipped, shape, "", "ClippingGeometry")  # clip the integer raster so that we're only counting points within the ELC boundary
        arcpy.Delete_management(Int)  # delete the integer raster so we're just left with one final raster
        arcpy.CopyRows_management(clipped, RowsLoc)  # run copy rows tool
        print "pre processing and copy rows complete onto the next"  # status update
        return clipped

    csvname = raw_input("Please enter the file name of the master CSV this code will create (include .csv): ")  # this will request from the user what they will call the csv file that will be  output by the code
    Wkspace = r"C:\Users\theod\Desktop\Theodore\Grad_School\Research - Land Cover Change\LCLUC_Cambodia_GIS\Play.gdb"  # path for workspace we'll be using
    if os.path.exists(Wkspace):  # error check to make sure wkspace path exists
        pass
    else:
        raise PathError  # if wkspace path doesn't exist then raise path error
    arcpy.env.workspace = Wkspace
    arcpy.env.overwriteOutput = True
    print "Wkspace created"
    print Wkspace
    ELC = "ELC33_mod_buffered_500m"  # set to variable name of shapefile ELC we'll be looping through params for
    Loc = r"C:\Users\theod\Desktop\Theodore\Grad_School\Research - Land Cover Change\LCLUC_Cambodia_GIS\Tables\Python_Tables"  # location to write csv tables to
    outputLoc = Loc + os.sep + csvname  # create path for where we'll create the output csv
    print "path ready to create csv"
    opened = open(outputLoc, "w")  # create output csv in chosen location
    header = "ELC#,Preval,Mag,Year,Count,Hectares" + "\n"  # put together header of output csv
    print "Header ready"
    opened.write(header)  # write header as first line of output csv
    print "created csv and wrote header"  # status update
    # create list of GEE exports in target directory - we will iterate through this list and extrac the data from them
    RasterLoc = r"C:\Users\theod\Desktop\Theodore\Grad_School\Research - Land Cover Change\LCLUC_Cambodia_GIS\Parameterization\ELC33"  # the folder where the parameterization rasters for a given ELC will be
    filelist = os.listdir(RasterLoc)   # generate a full list of the GEE parameter run exports that we'll loop across and analyze each separately
    length = len(filelist)  # get number of files we'll be iterating over
    cntr = 1  # counter for marking progress of loops
    fields = ["SHAPE@", "cartodb_id"]  # fields to be selected from shapefile we'll be working with
    cursor = arcpy.da.SearchCursor(ELC, fields)  # create cursor to access shape and ELC number
    for row in cursor:  # brief for loop that will only loop once so we can access the shape field (for clipping purposes), and cartodb field
        shape = row[0]  # put geometry object into a variable so I can use this to clip in the preprocessing function
        cartodbid = str(int(row[1]))  # convert ELC number into an integer then string so it can be written to the final csv
    print "cursor created and variables for shape and id set.  Bout to start big loop"  # status update
    for x in filelist:  # create for loop to loop through the list of all the different parameterization rasters created by GEE
        preval = x[28:31]  # select the preval of change attribute (from LT) of a given GEE run results  from the filename
        magnitude = x[35:38]  # select the magnitude of change attribute (from LT) from the filename
        rasloc = RasterLoc + os.sep + x  # take file name from list and create a full path to pass to function
        print rasloc
        goodraster = preprocessing(x, shape, RasterLoc, Loc)  # run raster pre-processing (int, clip, project) and return the final raster ready to go
        print "success!  Ran the preprocessing function"  # status update
        propfields = ["CELLSIZEX", "CELLSIZEY"]  # list variable to access to get raster properties
        raspropx = arcpy.GetRasterProperties_management(goodraster, propfields[0])  # get x cell sizes in map units (meters here) so I can convert to hectares
        xsize = float(raspropx.getOutput(0))  # set x size to variable
        raspropy = arcpy.GetRasterProperties_management(goodraster, propfields[1])  # get y cell size in map units (meters in this case) so I can convert to hectares
        ysize = float(raspropy.getOutput(0))  # set y size to variable
        CellArea = xsize * ysize  # get cell area in map units so I can convert to hectares
        CopyRows = "ELC" + cartodbid + ".csv"  # create name for csv that will contain rows of exported table
        RowsLoc = os.path.join(Loc, CopyRows)  # create path for copy rows tool to use
        TxtName = "ELC" + cartodbid + ".txt" + ".xml"  # create paths for xml file created by copy rows that will need to be deleted
        TxtLoc = os.path.join(Loc, TxtName)  # create a file path for xml file so we can delete it later
        arcpy.CopyRows_management(goodraster, RowsLoc)  # run copy rows tool
        CopiedRows = open(RowsLoc, "r")  # open file we just created that conains the rows
        header = CopiedRows.readline()  # skip over header
        for line in CopiedRows:  # start for loop to loop over the rows of the exported csv attribute table of the raster
            line = line.strip()  # remove new line character at end of each line
            # split each line by commas - contents[0] = OBJECTID, contents[1] = VALUE (year of greatest disturbance), contents[2] = COUNT - number of pixels disturbed in that year
            contents = line.split(",")  # split each row by commas
            MapArea = CellArea * float(contents[2])  # multiply map cell size by cell count to get total area of each class in map units - sq meters in this case
            Hectares = MapArea / 10000  # convert square meters of cells to hectares
            # structure of lines to write: ELCnum, Preval, Mag, Year (VALUE), Count, Hectares
            line = cartodbid + "," + preval + "," + magnitude + "," + contents[1] + "," + contents[2] + "," + str(Hectares) + "\n"  # concatenate values into new comma separated string to write to output file
            opened.write(line)  # write each new line to the output combined csv
        CopiedRows.close()  # close the csv created by the copy rows tool
        print "Raster copied rows closed"
        os.remove(RowsLoc)  # delete csv file copied from raster so I don't generae hundredsof csv files
        os.remove(TxtLoc)  # delete text xmls created by copy rows
        print "removed csv and xml files"
        remains = length - cntr  # calculate how many loops remain to do
        print "We've finished loop number %s, we have %s left to go!" % (str(cntr), str(remains))  # print status update for how many loops done and how many remain
        cntr = cntr + 1  # increase counter for status update printouts
    opened.close()
    print "Closed and saved the msster output"
    del cursor
except PathError:
    print "That path for the GeoDB doesn't exist, please try again!"
except Exception, e:  # other outside, python errors
    print "Error: " + str(e)  # prints python related error
    print arcpy.GetMessages()  # prints arcpy related errors