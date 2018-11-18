#!/usr/bin/env python3

import queue as queue
import threading
import time
import logging
import random
import cv2
import os

logging.basicConfig(level=logging.DEBUG, format='(%(threadName)-9s) %(message)s',)

BUF_SIZE = 10
#generate our two queues. 
q = queue.Queue(BUF_SIZE)
q2 = queue.Queue(BUF_SIZE)

class ProducerThread(threading.Thread): #extract 
    def __init__(self, group=None, target=None, name=None, args=(), kwargs=None, verbose=None):
        super(ProducerThread,self).__init__()
        self.target = target
        self.name = name

    def run(self):
        # globals
        outputDir    = 'frames'
        clipFileName = 'clip.mp4'
        # initialize frame count
        count = 0

        # open the video clip
        vidcap = cv2.VideoCapture(clipFileName)

        # create the output directory if it doesn't exist
        if not os.path.exists(outputDir):
            print("Output directory {} didn't exist, creating".format(outputDir))
            os.makedirs(outputDir)

        # read one frame
        success,image = vidcap.read()

        print("Reading frame {} {} ".format(count, success))
        while success: #while we have something to extract. 
            if q.qsize() < 10: #make sure our queue isn't too large 
                # write the current frame out as a jpeg image
                cv2.imwrite("{}/frame_{:04d}.jpg".format(outputDir, count), image)   
                success,image = vidcap.read()
                print('Reading frame {}'.format(count))
                item = count #make our item hold our current count we just did. 
                q.put(item) #push to our queue to ensure that the next thread pulls the right number.  
                count += 1
        return

class ConsumerThread(threading.Thread): #convert to grayscale 
    def __init__(self, group=None, target=None, name=None,args=(), kwargs=None, verbose=None): #just initialization. 
        super(ConsumerThread,self).__init__()
        self.target = target
        self.name = name
        return

    def run(self):
        # globals
        outputDir = 'frames'

        # initialize frame count
        count = 0

        # get the next frame file name
        inFileName = "{}/frame_{:04d}.jpg".format(outputDir, count)

        # load the next file
        inputFrame = cv2.imread(inFileName, cv2.IMREAD_COLOR)
        while inputFrame is not None: #make sure there is even a fram to display. 
            
            if not q.empty(): #make sure we have something to take from 1st queue
                if q2.qsize() < 10: #make sure our second queue doesn't get too large
                    item = q.get()#get number to convert to grayscale currently 
                    print("Converting frame {}".format(item))

                    # convert the image to grayscale
                    grayscaleFrame = cv2.cvtColor(inputFrame, cv2.COLOR_BGR2GRAY)
                    
                    # generate output file name
                    outFileName = "{}/grayscale_{:04d}.jpg".format(outputDir, item)

                    # write output file
                    cv2.imwrite(outFileName, grayscaleFrame)
                    
                    
                    count += 1
                    q2.put(item) #now we want to push to the second queue our number for it to display. 
                    # generate input file name for the next frame
                    inFileName = "{}/frame_{:04d}.jpg".format(outputDir, item+1)

                    # load the next frame
                    inputFrame = cv2.imread(inFileName, cv2.IMREAD_COLOR)
        return
    
class SecondConsumerThread(threading.Thread): #extract 
    def __init__(self, group=None, target=None, name=None, args=(), kwargs=None, verbose=None): #initializing my thread. 
        super(SecondConsumerThread,self).__init__()
        self.target = target
        self.name = name

    def run(self):
                
        # globals
        outputDir    = 'frames'
        frameDelay   = 42       # the answer to everything

        # initialize frame count
        count = 0

        startTime = time.time()

        # Generate the filename for the first frame 
        frameFileName = "{}/grayscale_{:04d}.jpg".format(outputDir, count)

        # load the frame
        frame = cv2.imread(frameFileName)

        while frame is not None:#make sure there is a frame available. 
            if not q2.empty(): #make sure there is something in the queue to use. 
                item = q2.get() #this grabs our next count for display. 
                print("Displaying frame {}".format(item))
                # Display the frame in a window called "Video"
                cv2.imshow("Video", frame)

                # compute the amount of time that has elapsed
                # while the frame was processed
                elapsedTime = int((time.time() - startTime) * 1000)
                print("Time to process frame {} ms".format(elapsedTime))
                
                # determine the amount of time to wait, also
                # make sure we don't go into negative time
                timeToWait = max(1, frameDelay - elapsedTime)

                # Wait for 42 ms and check if the user wants to quit
                if cv2.waitKey(timeToWait) and 0xFF == ord("q"):
                    break    

                # get the start time for processing the next frame
                startTime = time.time()
                
                # get the next frame filename
                frameFileName = "{}/grayscale_{:04d}.jpg".format(outputDir, item + 1)

                # Read the next frame file
                frame = cv2.imread(frameFileName)

        # make sure we cleanup the windows, otherwise we might end up with a mess
        cv2.destroyAllWindows()
            
        return     
if __name__ == '__main__':
    
    p = ProducerThread(name='producer')#extract
    c = ConsumerThread(name='consumer')#grayscale
    dc = SecondConsumerThread(name = 'consumer2')#display 

    p.start()
    time.sleep(2) #put in a delay to let an initial queue to build for the consumer thread. 
    c.start()
    time.sleep(2) 
    dc.start()
    
