# Raster table extraction
# Written by: Theodore Reuter
# Purpose: Written as part of a research project of land use and land cover change in Cambodia, this code will
# take an input integer raster produced by the "LandTrendr" project
# on Google Earth Engine, of the entire country and iterate through a series of polygons representing various
# land sales.  Each polygon will be used to clip the raster, and exported as a csv to get the raster attribute table
# This csv will then be read, the count extracted, converted to hectares, and then this information including the new
# hectares calculation will be written to a master output csv.
# this file will be converting the cell counts of rasters into total hectares.  The conversion factor will be based
# upon an assumption that the units of the rasters are in meters that this code was originally written for.
# If this is not the case, plesae examine the code and change it as needed.


import arcpy
print "Arcpy library imported"
import os
print "os library imported"


class PathError(Exception):  # create error for path error of gdb
    pass


try:
    csvname = raw_input("Please enter the file name of the master CSV this code will create (include .csv): ")  # this will request from the user what they will call the csv file that will be  output by the code
    #Wkspace = raw_input("Please enter path for gdb we will be working with today: ")  # request path to gdb we will be getting data from
    #InputRas = raw_input("Please enter the name of the raster we will be extracting data from: ") #request name of raster we will be getting data from
    Wkspace = r"C:\Users\theod\Desktop\Theodore\Grad_School\Research - Land Cover Change\LCLUC_Cambodia_GIS\LT_Multi_Indices.gdb"
    InputRas = "SWIR_NBR_cohen_n_Hansen_Bi_Com"
    if os.path.exists(Wkspace):
        pass
    else:
        raise PathError
    InputShpFile = "ELC_mod_buffered_500m_backup"  # key variable
    arcpy.env.workspace = Wkspace
    arcpy.env.overwriteOutput = True
    Loc = r"C:\Users\theod\Desktop\Theodore\Grad_School\Research - Land Cover Change\LCLUC_Cambodia_GIS\Tables\Python_Tables"  # location to write csv tables to
    propfields = ["CELLSIZEX", "CELLSIZEY"]  # list variable to access to get raster properties
    raspropx = arcpy.GetRasterProperties_management(InputRas, propfields[0])  # get x cell sizes in map units (meters here) so I can convert to hectares
    xsize = float(raspropx.getOutput(0))  # set x size to variable
    raspropy = arcpy.GetRasterProperties_management(InputRas, propfields[1])  # get y cell size in map units (meters in this case) so I can convert to hectares
    ysize = float(raspropy.getOutput(0))  # set y size to variable
    CellArea = xsize * ysize  # get cell area in map units so I can convert to hectares
    output = Loc + os.sep + csvname
    opened = open(output, "w")
    header = "ELC#,Year,Count,Hectares" + "\n"
    opened.write(header)  # write header information to file
    CursorFields = ["SHAPE@", "cartodb_id"]
    cursor = arcpy.da.SearchCursor(InputShpFile, CursorFields)  # create cursor using fields and input shapefile
    Countrows = str(arcpy.GetCount_management(InputShpFile).getOutput(0))  # run Count Rows tool to export the rows from an individual ELCs int raster
    print "We are about to begin THE LOOP.  We'll be iterating through %s times, so it might take a while." % Countrows  # message to update on progress
    cntr = 1  # counter to be used to update on progress.
    for row in cursor:
        shape = row[0]  # row[0] is a geometry object representing the shape field
        ELCnum = row[1]  # row[1] will be cartodb_id which is what we are calling the ELC number
        ClippedRaster = "Clipped" + "ELC" + str(int(ELCnum))  # have to convert ELCnum to int to get ride of decimal which messes up pathing and tool, then convert to string to concatenate
        ClipResult = arcpy.Clip_management(InputRas, "", ClippedRaster, shape, "", "ClippingGeometry")  # the main input raster has already been convered to Int using raster calculator so we can go straight to exporting the rows
        CopyRows = "ELC" + str(int(ELCnum)) + ".csv"  # create name for csv that will contain rows of exported table
        RowsLoc = os.path.join(Loc, CopyRows)  # create path for copy rows tool to use
        TxtName = "ELC" + str(int(ELCnum)) + ".txt" + ".xml"  # create paths for xml file created by copy rows that will need to be deleted
        TxtLoc = os.path.join(Loc, TxtName)
        arcpy.CopyRows_management(ClipResult, RowsLoc)  # run copy rows tool
        CopiedRows = open(RowsLoc, "r")  # open file we just created that conains the rows
        header = CopiedRows.readline()  # skip over header
        for line in CopiedRows:
            line = line.strip()  # remove new line character at end of each line
            # split each line by commas - contents[0] = OBJECTID, contents[1] = VALUE (year of greatest disturbance), contents[2] = COUNT - number of pixels disturbed in that year
            contents = line.split(",")
            MapArea = CellArea * float(contents[2])  # multiply map cell size by cell count to get total area of each class in map units - sq meters in this case
            Hectares = MapArea/10000  # convert square meters of cells to hectares
            # structure of lines to write: ELCnum, Year (VALUE), Count, Hectares
            line = str(ELCnum) + "," + contents[1] + "," + contents[2] + "," + str(Hectares) + "\n"  # concatenate values into new comma separated string to write to output file
            opened.write(line)  # write each new line to the output combined csv
        CopiedRows.close()
        print "Copied rows closed"
        os.remove(RowsLoc)  # delete csv file copied from raster so I don't generae hundredsof csv files
        print "csv file removed"
        os.remove(TxtLoc)  # delete text xmls created by copy rows
        print "xml file removed"
        arcpy.Delete_management(ClipResult)  # delete the clipped raster so we don't get hundreds of rasters floating around
        LoopRemain = str(int(Countrows) - cntr)  # subtract loops completed from total loops we need to run, convert to string for next line to use placeholder
        print "We have completed copying over the info from one polygon.  Onto the next!  That's %s down, %s left" % (cntr, LoopRemain)  # update message printed every loop
        cntr = cntr + 1
    opened.close()
    del cursor  # after looping through delete cursor
    print "That's it!  All done.  I'm proud of ya kid."

except PathError:
    print "That path for the GeoDB doesn't exist, please try again!"
except Exception, e:  # other outside, python errors
    print "Error: " + str(e)  # prints python related error
    print arcpy.GetMessages()  # prints arcpy related errors
