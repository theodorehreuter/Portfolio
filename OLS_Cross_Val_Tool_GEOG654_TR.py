#UMDCP GEOG654 - GIS And Spatial Modeling
#Final Project
#Python code for tool
#Theodore Reuter

#This tool will run provide cross validation of Ordinary Least Squares Regression on a polygon dataset comprised of "n" polygons.
# The dataset will be split into two parts, one polygon, and the rest representing n-1 polygons.  OLS will be run on the larger dataset,
# and then validate this model on the single polygon that was separated.  This program will then loop through every polygon and preform an identical
# splitting, OLS, and validation process so that every polygon will be used as a validation for a model derived from the rest of the dataset - the cross validation.
# OLS will run as many times as there are polygons, with each run being validated against a different polygons.  This code was written as a final project for a
# grad school course, so for  programmatical simplicity and time constraints in creating this tool, OLS will only accept 4 explanatory variables.
# The this class I focused on census tracts in washington DC and using OLS to calculate the poverty rate based on 4 simple explanatory variables.

import arcpy
import os

class ExtensionError(Exception): #if spatial analyst extension cannot be checked out
    pass
try:
    Wkspace = arcpy.GetParameterAsText(0) #set workspace
    MasterIn = arcpy.GetParameterAsText(1) #polygon master in shapefile containing independant and dependant variables, must be polygon shapefile will be chopped/looped through by polygon
    UniqID = arcpy.GetParameterAsText(2) #unique id for each polygon needed for OLS
    Depend = arcpy.GetParameterAsText(3) # dependant variable for running OLS - this will be TOT_CRIME for this project, a sum of all crime events recorded by DC police in that cencus tract over the year
    IndepUno = arcpy.GetParameterAsText(4) #independant variable 1 for running OLS - this will be total population of census tract for my final project
    IndepDuo = arcpy.GetParameterAsText(5) #independant variable 2 for running OLS - this will be the poverty rate (in %) of the cencus tract for my final project
    IndepTres = arcpy.GetParameterAsText(6) #independant variable 3 for running OLS - this will be the unemployment rate (as %) of the census tract of my final project
    IndepQuad = arcpy.GetParameterAsText(7) #independant variable 4 for runni6ng OLS - this will be median income of census tract of my final project
    OutOLS = arcpy.GetParameterAsText(8) #output shapefile file containing residuals for each iteration.  This will be written over again and again (overwrite = true) as it is not the  point of this project, but is required to run OLS with arcpy.  Last output will not be overwritten
    CoefTbl = arcpy.GetParameterAsText(9) #output table file (in .dbf, workable with arcpy and cursors) that will contain the regression coefficients used later to reconstruct the regression eq and predict crime - key variable.  We be continually overwritten except for last table produced
    Output = arcpy.GetParameterAsText(10) #create output file to hold results
    
    #run error checks and initial message outputs
    if arcpy.CheckExtension("Spatial" == "Available"): #check availability of spatial extension
        arcpy.CheckOutExtension("Spatial") #if extension is available, check out spatial extension for use
    else:
        raise ExtensionError #if extension is not available, raise ExtensionError
    arcpy.AddMessage("Your Master Input file is %s" % (MasterIn)) #output arcpy message stating what input shapefile is
    arcpy.AddMessage("Your Unique Id field is %s, your dependant variable is %s, your independant variables are %s, %s, %s, %s" % (UniqID, Depend, IndepUno, IndepDuo, IndepTres, IndepQuad)) #message sharing what the fields required for OLS are - unique ID, dependant and independant variables
    arcpy.AddMessage("Your OLS Output file for the final (and ONLY final) loop iteration will be located here: %s." % (OutOLS)) #message of where OLS output will be but only for last loop, as others will be overwritten
    arcpy.AddMessage("Your CoefTbl for the final (and ONLY final) loop iteration will be located here: %s." % (CoefTbl)) #message of where coef table will be, but only the last loop as others will be overwritten
    
    arcpy.env.workspace = Wkspace #set the workspace to location set by user in input above 
    arcpy.env.overwriteOutput = True #set overwrite to true 
    RowCount = arcpy.GetCount_management(MasterIn) #get row count of master in shapefile
    arcpy.AddMessage("Your input shapefile has %s rows!  That's how many times we'll be running OLS and the loop, so this might take a bit, that's a lot of number crunching.  Put your feet up and relax." % (RowCount)) #row count message to give user idea of how long this will take - this is a processing heavy tool
    
    #create output feature class and prepare for THE LOOP - DUN DUN DUNNNNNNN.  In the immortal words of Samuel L Jackson: "Hold on to ya butts"
    ExplanFields = [IndepUno, IndepDuo, IndepTres, IndepQuad] #create list object of explanatory fields to be used to run OLS each loop iteration, always same var
    spatial_ref = arcpy.Describe(MasterIn).spatialReference #get spatial reference from master input so output shapefile can have same reference
    arcpy.CreateFeatureclass_management(Wkspace, Output, "POLYGON", "", "DISABLED", "DISABLED", spatial_ref) #create output shapefile that will be populated with cross validation information
    arcpy.AddField_management(Output, "GEOID", "STRING") #create field to carry over GEOID field, the unique ID by census bureau for census tract identification    
    arcpy.AddField_management(Output, "OLS_PRED", "FLOAT") #create field that will contain predicted dependant variable outputs of a polygon after running cross validation and extract OLS coefficients to run regression equation on this polygon using it's independant variable quantities
    arcpy.AddField_management(Output, "ACTUAL", "FLOAT") #create field that will contain actual value of dependant variable we will be testing regression against for cross validation
    arcpy.AddField_management(Output, "CRS_VAL_DIFF", "FLOAT")#create field that will contain difference between actual level of dependant var and OLS prediction for regression calculated from rest of dataset
    SrchCursor = arcpy.da.SearchCursor(MasterIn, "*") #create master search cursor Used to iterate through master input and preform cross validation loop, and grab all fields
    fields = arcpy.ListFields(MasterIn) #create list of field objects, through which I can access the name of the ID field so we can iterate through and make progressive selections based on that field
    TheGuide = fields[0].name #Get name of first field, the ID field that can't be deleted, so that we can make our selections on this field
    CoefFields = ["Variable", "Coef"] #fields I will grab from coefficient table to reconstruct regression equation
    
    IDCursor = arcpy.da.SearchCursor(MasterIn, "*") #create search cursor for finding first number of ID field, grab all fields
    IDvalues = [cheese[0] for cheese in IDCursor] #put first value of the first field in each row (cheese) into a list object 
    Cntr = min(IDvalues) #find minimum of the above list object, which will be the starting number - might be zero or 1, that's why this code is here.  Will iterate from here.
    RMSEList = [] #blank list to append errors to for calculating errors
    
    #THE LOOP - "That's no loop.  That's a space station.  It's too big to be a space station.  I've got a bad feeling about this."
    searchplay = arcpy.da.SearchCursor(MasterIn, "*") #create search cursor for master loop that will be used to preform cross validation
    for row in searchplay: #begin master loop within which cross validation will be preformed
        WhereClause = "\"%s\" = %s" % (TheGuide, Cntr) #create clause for select to cut out one row to use as erase feature to split dataset
        Eraser = "ERASER" #create variable name for out feature that will be used as the erase feature - also later used as validation data to compare OLS results to
        Splitter = "Splitter" #name of file that will contain the REST of the data - this is what OLS will be run on
        arcpy.Select_analysis(MasterIn, Eraser, WhereClause) #select and create the one polygon later to be used for validation
        arcpy.Erase_analysis(MasterIn, Eraser, Splitter) #split main input into two datasets needed for cross validation, using erase row feature created
        
        #get output coefficient values from OLS coefficient output tables - will use these shortly to construct regression equation.
        arcpy.OrdinaryLeastSquares_stats(Splitter, UniqID, OutOLS, Depend, ExplanFields, CoefTbl) #run OLS on split dataset minus validation polygon
        print "OLS run!"
        CoefCursor = arcpy.da.SearchCursor(CoefTbl, CoefFields) #create search cursor of coefficent output table so I can get coefficients to create regression equation                     
        print "CoefCursor created!"
        VarList = [] #empty list that I will append key/value pairs to from coefficient table
        for CoefRow in CoefCursor:
            VarAppender = CoefRow[1] #grab key value pair - first value is variable/intercept, second is value of coefficient.  This will be in order variables were picked in tool input
            VarList.append(VarAppender) #append each key value pair to the empty list - variables are appeneded in order they are picked in tool input, so no need to match by names
        del CoefCursor
        
        #get validation variable values to run through constructed regression equation for the shapefile with one polygon we split off for validation
        OneCursor = arcpy.SearchCursor(Eraser, ExplanFields) #create search cursor of shapefile that was the one polygon - number used to put into regression eq with coeff extracted above.  Use regular search cursor since has getValue method, easier to query values by field
        for OneRow in OneCursor:
            Shape = OneRow.getValue("Shape") #get shape object to insert into new shapefile
            GEOID = OneRow.getValue("GEOID") #get GEOID field
            ValOne = OneRow.getValue(IndepUno) #get value of first explanatory variable
            ValTwo = OneRow.getValue(IndepDuo) #get value of second explanatory variable
            ValThree = OneRow.getValue(IndepTres) #get value of third explanatory variable
            ValFour = OneRow.getValue(IndepQuad) #get value of fourth explanatory variable
            Actual = OneRow.getValue(Depend) #reality value of actual quantity we are modeling.  Value we will be comparing OLS prediction to
        del OneCursor #delete cursor so we don't keep making lots of cursors
        #construct regression equation and run variables through it.
        
        OLSPred = VarList[0] + (VarList[1] * ValOne) + (VarList[2] * ValTwo) + (VarList[3] * ValThree) + (VarList[4]* ValFour) #grab value from key value pairs in order
        #VarList[0][1] is always intercept from coef table, how arcgis constructs it.  VarList[1][1] is coef of 1st indep var.  VarList[2][1] is coef of 2nd indep var and so on
        
        #Insert information into output shapefile using insert cursor
        Difference = OLSPred - Actual #calculate difference between prediction by OLS and validation data
        Diffsq = Difference*Difference #square difference for RMSE calculations
        RMSEList.append(Diffsq) #append difference to list so RMSE can be calculated
        InsertFields = ["SHAPE@", "GEOID", "OLS_PRED", "ACTUAL", "CRS_VAL_DIFF"] #create list of fields for insert cursor
        InsertCursor = arcpy.da.InsertCursor(Output, InsertFields) #create insert cursor we'll use to insert cross validation data into empty output shapefile
        Insertion = [Shape, GEOID, OLSPred, Actual, Difference] #create list of data to insert into insert cursor
        InsertCursor.insertRow(Insertion)
        del InsertCursor #delete insert cursor after inserting data so information can be saved in table    
        Cntr = Cntr + 1 #counter increased by 1 each loop to print message showing how we're going.
        print "Count is %s" % (Cntr) #for testing purposes - use arcpy.addmessage in final
        arcpy.AddMessage("We're on iteration # %s of THE LOOP.  We're still going." % (Cntr)) #arcpy message print out to show how tool is progressing
        
    
    RMSE = math.sqrt((float(sum(RMSEList))/float(RowCount[0]))) #calculate root mean square error for final output and convert RowCount row object to float by first calling unicode with RowCount[0], then to float
    arcpy.AddMessage("Whew, that was a lot of number crunching but we're finally done.") #add message indicating program is done
    arcpy.AddMessage("There is an output file waiting for you at %s, and a coefficient table of the last iteration at %s." % (Output, CoefTbl)) #message for where output are.
    arcpy.AddMessage("Your total RMSE is %f" % (RMSE)) #add message outputting total errors
    
except ExtensionError: #determine what error message will be output if spatial analyst extension is not available
    arcpy.AddError("The extensions you need for this tool are unavailable.  You've been blocked like Lebron blocked Curry.")
except Exception, e: #other outside, python errors
    print "Error: " + str(e) #prints python related error   
    print arcpy.GetMessages() #prints arcpy related errors
    arcpy.AddError(e) #Adds errors to custom GIS tools
