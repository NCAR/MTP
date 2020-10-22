

#f = open("../MTP_data.txt", 'r')
f = open("testData.txt", 'r')

oldline = 0

for line in f:
    if line[0] == 'B':
        # check if it is a Bline, else don't care
        # remove trailing end of line \n or \r\n's
        line = line.rstrip()
        # remove B and space from start
        line = line[2: len(line)]             
        line = line.split(" ")
        
        if oldline is not 0:
            # all cases but first
            print (line)

            for index, data in enumerate(line):
                #print( index, data )
                difference = abs(int(data)-int(oldline[index]))
                print (difference)


        else:
            # first case
            print("firstcase")

        oldline = line
