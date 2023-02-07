import re
import sys

error_warning_list ={ "Error" : [], "Warning" : [] }
warning_exception_list = { "C3912W", "C9962I", "L9962I", "A9962I", "#1-D", "#177-D", "#550-D" }
error_exception_list = { }

def isExcept(code, exceptionList):
    if str(code) in exceptionList:
        return True
    return False

def parseWarningLog(fileName, outputFile):
    with open(fileName) as warnings_log_file:
        for line in warnings_log_file:
            if re.search("Warning:\s.*:\s", line):
                split_list = line.split(": ")
                if(len(split_list) == 4 ):
                    details = split_list[-4]
                else:
                    details = ""
                code = split_list[-2].replace(' ', '')
                if code == "":
                    code = "--"
                message = "\"" + split_list[-1].replace("\n", '') + "\""
                if "Warning" in split_list:
                    if not isExcept(code, warning_exception_list):
                        error_warning_list["Warning"].append({"Code" : code, "Message" : message, "Details" : details})
                elif "Error" in split_list:
                    error_warning_list["Warning"].append({"Code" : code, "Message" : message, "Details" : details})

    # Output to the .CSV file
    with open(outputFile, "w") as output_csv:
        output_csv.write("Code,Message,Details\n")
        for item in error_warning_list["Warning"]:
            output_csv.write(item["Code"] + "," + item["Message"] + "," + item["Details"] + "\n")

if __name__=="__main__":
    if (len(sys.argv) != 5):
        print("Missing command line parameter")
        exit(1)
    if (sys.argv[1] == "-i" and sys.argv[3] == "-o"):
        inputFile = sys.argv[2]
        outputFile = sys.argv[4]
        parseWarningLog(inputFile, outputFile)
