

def FormatEntry(entry, float_digits=3):
    if isinstance(entry, (int, long)):
        return "%d" % entry
    if isinstance(entry, (float)):
        float_convert = r"%#." + float_digits + "g"
        return float_convert % entry
    return entry


def MakeLatexTable(data):
    """ Return a formatted latex table as a string

    Format for input is the following:

    data: a list of lists
    titles: a list of strings

    """
    
    first_row = data[0]
    num_columns = len(first_row)
    num_rows = len(data)

    # Begin the Table
    table = ""
    table += r"\begin{tabular}{r"
    for row in range(num_columns-1):
        table += "|c"
    table += "} \n"
    table += r'\toprule' + '\n'

    # Make the Title Row
    '''
    table += r"\toprule" + " \n \n"
    if titles != None:
        for title in titles:
            table += " & " + title
        pass
    table += r"\\"
    '''
    # Make the body
    #table += r"\toprule"

    for row in data:
        # Add a TopRule "row"
        if row=="TopRule" or row=="toprule":
            table += r"\toprule " + '\n'
            continue
        if(len(row)==0):
            print "Error - MakeLatexTable: No entries in current row"
            raise Exception("MakeLatexTable")
        table += FormatEntry(row[0])
        for entry in row[1:]:
            table += " & " + FormatEntry(entry)
        table += r" \\ " + "\n"
        pass
    table += r"\bottomrule" + ' \n'

    # End
    table += r"\end{tabular}"
    return table

