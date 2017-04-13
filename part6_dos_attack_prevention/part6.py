import socket
import os,time
from threading import Thread

class RequestThread(Thread):

    def __init__(self, threadNo, thread_connection,dos):
        Thread.__init__(self)
        self.threadNo = threadNo
        self.connection = thread_connection
        self.dos = dos

    def run(self):
        intialRequest = self.connection.recv(1024)
        print intialRequest
        if self.dos == True:
            time.sleep(10)
            # print "done1"

        request,method = GetRequestDict(intialRequest)
        if method == "POST":
            http_response = handlePostRequest(request,intialRequest,self.connection)
        else:
            http_response = handleRequest(request)

        #print http_response
        self.connection.sendall(http_response)
        self.connection.close()
        time.sleep(6)
        # print "Thread is closing", self.threadNo

def GetRequestDict(request):
    ret = dict()
    requestlist = request.split('\n')
    for requestelement in requestlist:
        Headers = requestelement.split(' ')
        if Headers[0] == "Content-Type:":
            ret["boundary"] = Headers[2][10:len(Headers[2])]
            ret["boundary"] = "---" + ret["boundary"]
        if Headers[0] == "Content-Disposition:":
            ret["filename"] = Headers[3][10:len(Headers[3])-2]
            method = "POST"
            flag = 1
            return ret,method
        elif len(Headers) >= 2:
            ret[Headers[0]] = Headers[1]
            if Headers[0]=="GET":
                method = "GET"
                ret["Version"] = Headers[2]
                ret["GET"] = ret["GET"][1:]
                return ret,method


def handleRequest(request):
    if request["GET"] not in os.listdir("./"):
        http_response = """\
HTTP/1.1 200 OK

<html>
<h1>404 Not Found!</h1>
</html>
"""
    else:
        with open(request["GET"]) as f:
            http_response = """\
HTTP/1.1 200 OK

"""
            for line in f:
                http_response += line

    return http_response

def handlePostRequest(request,intialRequest,connection):
    if not request["filename"]:
        http_response = """\
HTTP/1.1 200 OK

<html>
<body>
<h1>
 Hey! Select the file
<br>
<a href= "http://127.0.0.1:9991/upload.html"> Upload Again </a>
</h1>
</body>
</html>
"""
        return http_response

    fname = "uploads/"+request["filename"]
    fobj = open(fname,"w+")
    lines = intialRequest.split('\n')
    fbeg = 0
    it = 0
    for line in lines:
        it += 1
        if line == request["boundary"]:
            fbeg = 1
        if fbeg and fbeg <6:
            fbeg +=1
        if fbeg > 5 and it != len(lines):
            fobj.write(line+"\n")
        elif it == len(lines):
            fobj.write(line)

    wflag = 1
    while wflag:
        newRequest = connection.recv(1024)
        requestlist = newRequest.split('\n')
        ite = 0
        for requestelement in requestlist:
            ite += 1
            if requestelement == request["boundary"] :
                wflag = 0
                break
            else:
                if ite != len(requestlist):
                    fobj.write(requestelement+"\n")
                else:
                    fobj.write(requestelement)
        # for ite in range(len(requestlist)):
        #     if requestlist[ite] == request["boundary"] :
        #         wflag = 0
        #         break
        #     else:
        #         if ite < len(requestlist)-1  and requestlist[ite+1] != request["boundary"] :
        #             fobj.write(requestlist[ite]+"\n")
        #         else:
        #             if ite < len(requestlist)-1 and requestlist[ite+1] != request["boundary"]:
        #                 fobj.write(requestlist[ite])

    fobj.close()
    connection.settimeout(2)

    try:
        a = connection.recv(1024)
    except:
        a = "timeout"
    # print "Printing a :", a
    http_response = """\
HTTP/1.1 200 OK

<html>
<body>
<h1>
 File (%s) has been Uploaded cheers!
<br>
<a href= "http://127.0.0.1:9991/upload.html"> Upload Again </a>
</h1>
</body>
</html>
""" %request["filename"]
    return http_response

def checkForDos(current_client):
    # if noOfRequest received from a particular client in timeInterval then block it for 10 seconds
    noOfRequest = 10
    timeInterval = 4
    count = 0
    log = open("logs.txt","a+")
    lines = log.readlines()
    log.close()
    log = open("logs.txt","w+")
    for line in lines:
        element = line.split(' ')
        if time.time() - float(element[1][:len(element[1])-1]) < timeInterval:
            log.write(line)
        else:
            continue
        # print element[0],client_address,element[0] == client_address
        if element[0] == current_client:
            count += 1
    log.close()
    if count > noOfRequest:
        return True
    else:
        return False

HOST, PORT = '127.0.0.1', 9991

socket_listen = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
socket_listen.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
socket_listen.bind((HOST, PORT))
socket_listen.listen(5)
print 'Serving HTTP on port %s ...' % PORT

requestList = list()
os.remove("logs.txt")
while True:
    log = open("logs.txt","a+")
    client_connection, client_address = socket_listen.accept()
    log.write(client_address[0]+" "+str(time.time())+"\n")
    log.close()
    dos = checkForDos(client_address[0])
    newRequest = RequestThread(len(requestList), client_connection,dos)
    dos = False
    newRequest.start()
    requestList.append(newRequest)

    for request in requestList:
        if not request.isAlive():
            requestList.remove(request)
            request.join()
