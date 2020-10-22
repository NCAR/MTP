with open("MTP_data_11_30_tf02.txt", "r") as datafile:
    with open ("MTP_data_11_30_TF02_SANITIZED.txt", 'a') as sdata:
        # while not done:
        lineData = datafile.readline()
        line = lineData.split(' ')
        first = line[0].split(':')
        if first[0] is 'M01' or 'M02' or 'Pt':
            for l in line:
                if first[0] is 'M01' or 'M02' or 'Pt':
                    saveline = first[0] + ":" + str(int(first[1].decode('ascii'),16))
                    print("saveline start: %s", saveline)
                else:
                    saveline = saveline + str(int(line.decode('ascii'),16))
                    print("saveline next: %s", saveline)
        else:
            saveline = lineData
        print("saveline: " + saveline)
        sdata.write(saveline)   
