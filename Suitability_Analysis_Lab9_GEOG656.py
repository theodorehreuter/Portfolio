#GEOG-656 Programming and Scripting
#Lab 9 - Raster Objects
#Theodore Reuter
#This script was written as part of a lab assignment to preform a suitability analysis using rasters and arcgis geoprocessing tools.

import arcpy
import os


class UnitError(Exception): #create error class for unit error if units are not correct
    pass 
class WeightError(Exception): #create error class for weight error if weight units are not correct and/or do not add up to 1
    pass
class ExtensionError(Exception): # create error class for extension error if spatial extension is not checked out
    pass
try:
    Wkspace = arcpy.GetParameterAsText(0)  # get workspace as string from tool input
    DemRas = arcpy.GetParameterAsText(1)  # get file location of DEM raster as string from tool input
    LandRas = arcpy.GetParameterAsText(2) # get file location of Landuse Raster as string from tool input
    WeightOneStr = arcpy.GetParameterAsText(3) # get weight one input as string, to later be converted to a float for manipulation and raster algebra
    WeightTwoStr = arcpy.GetParameterAsText(4) # get weight two input as a string, to later be converted to a float for manipulation and raster algebra
    Units = arcpy.GetParameterAsText(5) #get units as string from tool input, to later be used in final areal calculations
    OutputRas = arcpy.GetParameterAsText(6) #to set file location of the output final land use suitability raster
    Suitability_output = arcpy.GetParameterAsText(7) #to get file location of final output text file of suitability calculations in PG county
    
    arcpy.AddMessage("Weight 1 is: %s" % WeightOneStr)
    arcpy.AddMessage("Weight 2 is: %s" % WeightTwoStr)
    arcpy.AddMessage("Areal unit chosen is: %s" % Units)
    WeightOne = float(WeightOneStr) #convert weight one input string into float so it can be tested, manipulated, and used in later calculations
    WeightTwo = float(WeightTwoStr) #convert weight two input string into float so it can be tested, manipulated, and used later in calculations
    if (Units == "Acres") or (Units == "Hectares"): #if units are either hectares or arces, proceed with code
        pass
    else:
        raise UnitError #if units are incorrect, stop program and raise unit error
    if (WeightOne >= 0) and (WeightOne <= 1) and (WeightTwo >= 0) and (WeightTwo <= 1): #if weights fall within the correct range, proceed to second test of weight values
        if (WeightOne + WeightTwo == 1): #test that sum of weights is equal to one.
            pass
        else:
            raise WeightError #if sum of weights does not equal one, stop program and raise weight error and scold user appropriately
    else: #if weights are not in the correct rage
        raise WeightError #raise weight error after first conditional, stop program, and give user a stern talking to.
    if arcpy.CheckExtension("Spatial" == "Available"): #check availability of spatial extension
        arcpy.CheckOutExtension("Spatial") #if extension is available, check out spatial extension for use
    else:
        raise ExtensionError #if extension is not available, raise ExtensionError
    
    arcpy.env.workspace = Wkspace #set the workspace to location set by user in input above 
    arcpy.env.overwriteOutput = True #set overwrite to true
    DemExtent = arcpy.Raster(DemRas)
    arcpy.env.extent = DemExtent.extent #set extent
    
    
    #build reclassification tables for later use
    SlpTbl = arcpy.sa.RemapRange([[0,3,5], [3,6,4], [6,9,3], [9,15,2], [15,30,1]]) #create reclassification table to reclassify slope raster
    AspTbl = arcpy.sa.RemapRange([[-1,0,5], [0,45,1], [45,135,3], [135,225,5], [225,315,3], [315,360,1]]) #create reclassification table to reclassify aspect raster
    LandUseTbl = arcpy.sa.RemapValue([[11,0], [21,1], [22,0], [23,0], [24,0], [31,1], [41,0], [42,0], [43,0], [52,1], [71,1], [81,0], [82,0], [90, 0], [95,0]]) #reclassify table for land use raster
    
    slopeOutRas = arcpy.sa.Slope(DemRas) #run slope analysis on DEM raster
    slopeOutRas.save("pg_slope") #save output slope raster in workspace location
    arcpy.AddMessage("Slope raster created!  Neat!") #add message to arcmap tool as it's running signaling completion of slope calculation
    SlopeReclass = arcpy.sa.Reclassify(slopeOutRas, "VALUE", SlpTbl) #relcassify slope raster using reclassification table above
    SlopeReclass.save("slope_reclass") #save reclasses slope raster object as file
    arcpy.AddMessage("Slope raster reclassified!  Well how about that?") #add message to arcpmap tool as it's running
    
    AspectOutRas = arcpy.sa.Aspect(DemRas) #run aspect analysis on DEM raster
    AspectOutRas.save("pg_aspect") #save aspect raster in workspace location
    arcpy.AddMessage("Aspect raster created.  He's heating up!") #add message to arcmap tool as it's running signaling completion of aspect calculation
    AspectReclass = arcpy.sa.Reclassify(AspectOutRas, "VALUE", AspTbl) #reclassify aspect raster using reclassification table created above
    AspectReclass.save("aspect_reclass") #save reclassed aspect raster object as a file
    arcpy.AddMessage("Aspect raster reclassified!   He's on fire!") #add message to arcmap tool as it's running
    
    LandUseReclass = arcpy.sa.Reclassify(LandRas, "VALUE", LandUseTbl) #reclassify land use raster based on land use table created above
    LandUseReclass.save("Land_Reclass") #save reclassified raster with name set earlier by user when setting up tool.
    arcpy.AddMessage("Landuse raster reclassified.  Nice.") #add message upon reclassification while running too in arcmap
    
    Suitability = arcpy.sa.Int(((WeightOne * SlopeReclass) + (WeightTwo * AspectReclass))*LandUseReclass) #create final suitability raster
    Suitability.save(OutputRas) #save suitability raster object as permanent raster
    arcpy.AddMessage("Final suitability raster created.  That's some fine work there partner.") #message to show up while running tool in 
    SuitDescr = arcpy.Describe(Suitability) #create describe object of final suitability raster to get stuff like file path, cell size, etc for output calculation
    Suitpath = SuitDescr.catalogPath #create variable that contains full file path of suitability raster
    arcpy.AddMessage("The final suitability raster path is: %s" % Suitpath) #output path of suitability raster
    
    
    #Post processing to run once rasters have all been created.  Here the final information on area avaialble will be calculated and written to a text file.
    SuitDescr = arcpy.Describe(OutputRas) #create describe object of final suitability raster to get stuff like file path, cell size, etc for output calculation
    Suitpath = SuitDescr.catalogPath #create variable that contains full file path of suitability raster    
    YSize = SuitDescr.meanCellHeight #access output raster describe object and get y cell size, assuming meters
    XSize = SuitDescr.meanCellWidth #access output raster describe object and get x cell size, assuming meters
    CellArea = YSize * XSize #multiply x and y cell size to get average cell area
    os.chdir(Wkspace) #set python working directory to arcpy working directory 
    txtdir = os.chdir("..") #move up one directory level so I can write the text file, a text file cannot be written to a gdb which is needed for the raster calculations
    fyl = open(Suitability_output, "w") #create text file with name of output parameter from tool, and create in write mode
    fyl.write("Susainability Class, Pixel Count, Total Area (%s)\n" % (Units)) #write header line to file that will be populated later with the data from the raster
    fields = ["Value", "Count"] #fields I will grab from search cursor
    cur = arcpy.SearchCursor(OutputRas, fields) #create serach cursor of sustainability raster with fields previously selected
    for row in cur: #begin while loop to run through data in raster attribute table
        value = row.Value #get value of suitability class - 0 to 5
        StrValue = str(value) #convert integer value into string so it can be written to output text file
        count = row.Count #get total count of pixels of that class
        StrCount = str(count) #convert pixel count to string so it can be written into output text file
        SqMTot = CellArea * count #get total area in meters squared multiplying count times
        if (Units == "Acres"): #if loop for writing to text file if acres is the unit chose
            TotAcArea = SqMTot * 0.000247105 #calculated total area in acres if unit selected is acres
            StrAcreArea = "%.3f" % (TotAcArea)  #convert area float value into a string with 3 decimal places so it can be written to the file
            WriteAcrArea = StrAcreArea + "\n" #add new line character to last string to be written to file so new datapoints get a new line
            AcreList = StrValue + ", " + StrCount + ", " + WriteAcrArea #compose list to write to file
            fyl.write(AcreList) #write to output text file
            arcpy.AddMessage("Suitability class %d - Area = %s %s" % (value, StrAcreArea, Units)) #output arcpy message containing output data
        elif (Units == "Hectares"): #if loop to run for writing to text file if hectares is the unit selected
            TotHecArea = SqMTot * 0.0001 #caluclate total area in hectares if unit selected in hectares
            StrHecArea = "%.3f" % (TotHecArea) #convert total amount of hectares to string value with 3 decimal points so it can be written to the file
            WriteHecArea = StrHecArea + "\n" #add new line character to hectare number so that new lines are created in output file
            HecList = StrValue + ", " + StrCount + ", " + WriteHecArea #compose list to write to file
            fyl.write(HecList) #write to output text file
            arcpy.AddMessage("Suitability class %d - Area = %s %s" % (value, StrHecArea, Units)) #output arcpy message containing output 
    fyl.close #close text file we've been writing to to save changes
    del cur #delete search cursor
    arcpy.AddMessage("Suitability tool complete!  Suitability file has been written!")    
except UnitError: #determine what error message will be output if the units input are incorrect
    arcpy.AddError("You picked the wrong units silly!  It's like comparing African and European Swallows, it's not a question of where he grips it, but weight ratios!  Also units.  Try again")
except WeightError: #determine what error message will be output if the weights selected do not match the appropriate conditions
    arcpy.AddError("Arrgh!  The weights need to be between 0-1 and add up to 1.  Read the directions!  You didn't read them?  Well put down the bottle, take a few deep breaths and try again.  Jeez...")
except ExtensionError: #determine what error message will be output if spatial analyst extension is not available
    arcpy.AddError("The extensions you need for this tool are unavailable.  You've been blocked!  No soup for you!")
except Exception, e: #other outside, python errors
    print "Error: " + str(e) #prints python related error   
    print arcpy.GetMessages() #prints arcpy related errors
    arcpy.AddError(e) #Adds errors to custom GIS tools