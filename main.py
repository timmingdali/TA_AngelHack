import numpy as np
import cv2
import cv2.aruco as aruco
import subprocess
import wolframalpha
from numpy import linalg as LA
from time import sleep
import serial
import io
import sympy

#contains stroke id and strokes coordinates
class stroke:
    def __init__(self,id):
        self.id = id
        self.pts = []
    def push(self,this_point):
        self.pts.append(this_point)


ser=serial.Serial('/dev/ttyACM0',9600,timeout=1)
equation = []
stroke_count = 0
#coordinate for bounding box
minX = 999999
minY = 999999
maxX = 0
maxY = 0
this_stroke = stroke(stroke_count) #start from 0
pts_for_display = [] # all the pts per frame

# cv2.namedWindow('frame', cv2.WINDOW_NORMAL)

width=1920
height=1080
backGround = np.ones((height,width,3), np.uint8)
# backGround[:,0:int(width/2)] = (255,0,0)      # (B, G, R)
# backGround[:,int(width/2):width] = (0,255,0)
# cv2.imwrite('NnzxG4S.png',backGround)
# backGround = cv2.imread('NnzxG4S.jpg',0)
# while True:
# cv2.imshow('frame', backGround)
# sleep(100)
# img = cv2.imread('NnzxG4S.png',0)





def projection_coordinate():
    global minX
    global minY
    global maxX
    global maxY
    coord = [None]*2
    coord[0] = int(maxX+0.1*(maxY - minY))*3
    coord[1] = int(0.5*(maxY+minY))*2
    if len(coord) is not 2:
        print('incorrect coordinate')
    return coord

def connectToWolframAlpha(scginkFile):
    print(scginkFile)
    log = open('output.txt','w') #write to the output
    sub = scginkFile
    p = subprocess.Popen(['./seshat','-c','Config/CONFIG','-i',sub,'-r','render.pgm','>','output.txt'],stdout=log)
    p.wait()
    log.close()

    question = ''
    with open('output.txt','r+') as f:
        for line in f:
            if line[0:5] == 'LaTeX':
                print(line[6:-1])
                question = line[6:-1]
    appId = 'AX97L2-XKGP9A38R5'
    client = wolframalpha.Client(appId)

    response = client.query(question)
    if response['@success'] == 'false':
        print('cannot resolve')
        return None
    else:
        answer = next(response.results).text
        print(answer)
        if '=' in answer:
            answer = answer.split("= ",1)[1]
        return answer


def finished_one_stroke():
    global equation
    global stroke_count
    global this_stroke
    print(str(this_stroke.pts))
    equation.append(this_stroke)
    stroke_count = stroke_count + 1
    this_stroke = stroke(stroke_count)
    print('finished one stroke')

def finished_one_equation():
    global minX
    global minY
    global maxX
    global maxY
    global equation
    global stroke_count
    ans_coord = projection_coordinate()
    print(str(equation))
    #reset min and max
    minX = 999999
    miny = 999999
    maxX = 0
    maxY = 0
    write_to_file()
    sleep(1)
    ans = ' ='
    ans = ans + connectToWolframAlpha('log.scgink')
    stroke_count = 0
    equation = []
    print('cleared equation')
    return ans,ans_coord
def write_to_file():
    global pts_for_display
    pts_for_display = []
    global equation
    global stroke_count
    file = open('log.scgink','w') #seshat file
    file.write('SCG_INK\n')
    file.write(str(stroke_count))
    file.write('\n')
    for stk in equation:
        file.write(str(len(stk.pts)))
        file.write('\n')
        for pt in stk.pts:
            file.write(str(pt[0]))
            file.write(' ')
            file.write(str(pt[1]))
            file.write('\n')
    print('finished writing to file')

cap = cv2.VideoCapture(1)
dictionary = cv2.aruco.Dictionary_get(aruco.DICT_4X4_50)
num_stroke = 0
# cap.set(cv2.CAP_PROP_FRAME_WIDTH,1080)
cap.set(cv2.CAP_PROP_FPS,35)
fps = cap.get(cv2.CAP_PROP_FPS)
print(fps)
last_button=None
yellowed=False
ans = ''
ans_coord=[]
scale = 7
screen=np.zeros((1080,1920,3),np.uint8)
while(True):
    button=ser.readline().decode("utf-8").rstrip()
    ser.write(b'f')
    # print(button)
    ret, frame = cap.read()

    if not ret:
        print('plz check camera setting')
        break
    # gray = cv2.cvtColor(frame,cv2.COLOR_BGR2GRAY) #gray picture as filter
    res = cv2.aruco.detectMarkers(frame,dictionary) #locate marker
    center = [None] * 4
    if len(res[0]) is 3:
        test = res[1][0][0]
        center[res[1][0][0]]= tuple((res[0][0][0][0]+res[0][0][0][1]+res[0][0][0][2]+res[0][0][0][3])/4)
        center[res[1][1][0]] = tuple((res[0][1][0][0]+res[0][1][0][1]+res[0][1][0][2]+res[0][1][0][3])/4)
        cv2.rectangle(frame,center[0],center[1],(0,255,255),3)
        tip = tuple((res[0][2][0][0]+res[0][2][0][1]+res[0][2][0][2]+res[0][2][0][3])/4)
    elif len(res[0]) is 1:
        tip = tuple((res[0][0][0][0] + res[0][0][0][1] + res[0][0][0][2] + res[0][0][0][3]) / 4)
    else:
        tip = None
    if button == "yellow":
        if not (tip is None):
            this_stroke.push(tip) #add the written pts to the list
            pts_for_display.append(tip)
            minX = min(tip[0],minX)
            minY = min(tip[1],minY)
            maxX = max(tip[0], maxX)
            maxY = max(tip[1], maxY)
            print('added',tip,'to stroke',num_stroke)
            yellowed=True
    elif button =='red' and last_button != button and yellowed:
        ans,ans_coord= finished_one_equation()
        yellowed=False

    elif last_button == "yellow":
        finished_one_stroke()

    #each frame display all the pts in the list on the screen
    for pt in pts_for_display:
        cv2.circle(frame,pt,2,(0,0,255),2)
    cv2.rectangle(frame,(minX,minY),(maxX,maxY),(0,0,255),3)
    font = cv2.FONT_HERSHEY_SIMPLEX
    if ans_coord and ans:
        cv2.putText(screen,ans,(ans_coord[0],ans_coord[1]),font,scale,(255,255,255),2,cv2.LINE_AA)
    cv2.imshow('frame',cv2.aruco.drawDetectedMarkers(frame,res[0],res[1]))
    cv2.imshow('screen',screen)
    if cv2.waitKey(1) & 0XFF == ord('q'):
        break

    last_button=button
    # ser.reset_input_buffer()

cap.release()
cv2.destroyAllWindows()