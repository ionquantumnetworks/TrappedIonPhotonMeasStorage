#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Fri Aug 14 08:10:18 2020

@author: jmhannegan
"""
import math
import random
import time
import os
from os import getpid
import matplotlib.pyplot as plt
import csv
from multiprocessing import Pool,set_start_method
from functools import partial

km = 1000;
us = 0.000001;



def simloop(timestr,i):
    #====For every case====#
    NodeARequestCounter = 0;
    NodeBRequestCounter = 0;
    #losses and standard values
    BranchingRatio = 0.75;
    CollectionEfficiency = 0.1; #0.6NA lens
    IonFiberCoupling = 0.8; #based on photongear 
    QFC780Efficiency = 0.6; #based on the 40% seen, taking out unnecessary optical losses
    QFC1550Efficiency = 0.6;
    DetectorEfficiency780 = 0.8;
    DetectorEfficiency1550 = 0.8;
    NDSPMEfficiency = 0.75; #Photon loss through NDSPM.. doesn't talk about fidelity at all
    fiberAtt1550 = 0.13; #db/km loss
    
    #Photon Registers, begin with no photon. Turn to 1 if the photon makes it through the fiber.
    PhotonA = 0;
    PhotonB = 0;
    StoredA = False;
    StoredB = False;
    
    #Flag Registers, begin with flag off. This lets the nodes know if they should fire or not
    FlagA = 0;
    FlagB = 0;
    

    #Transmission Counters: These go down by 1 every clock cycle.
    #In the loop they are put to a value when a photon is successfully flagged.
    #The nodes will wait to fire again until this goes to zero.
    TranA = 0;
    TranB = 0;
    ReturnA = 0;
    ReturnB = 0;
    NDSPMDelayA = 0;#time it takes NDSPM to make measurement in terms of clock cycles
    NDSPMDelayB = 0;
    #=======================================#
    #PhotonProductionProbability
    PhotonProb = (BranchingRatio * CollectionEfficiency * IonFiberCoupling * QFC780Efficiency * NDSPMEfficiency)*1000 #out of 1000
    #Network Length
    L = i/100; #km
    #lengthlist.append(L)
    #time to traverse network
    Lt =L*1000*1.4/(3*10**8) #kms multiplied by index of refraction and units of seconds
    #Clock Cycle Time (us)
    Period = 1.5;
    #Clock Rep Rate (MHz)
    f = 1;
    #Calculate number of cycles it takes for info to be transferred between node and BSA, rounded up to nearest cycle
    NCycles = math.ceil(Lt / Period * 10**6);#factor of 2 is for classical channel response time
    #Photon Transmission Probability
    #4dB for 1 km
    #keep in mind the effective rounding being done above
    #0.8 is for detector effciency @780
    photonFiberProb = 10**((-fiberAtt1550*L)/10)*10000*DetectorEfficiency1550*QFC1550Efficiency*(QFC1550Efficiency); #2nd QFC is to backconvert for storage, remove if storing at 1550. #convert to being out of 10000 for random number generation.
    print("photon probabilty into fiber after QFC and NDSPM:" + str(PhotonProb))
    print("Distance:" + str(L) + "km")
    print("Network must wait " + str(NCycles) +" cycles " + "to fire again when a photon is successfully sent.")
    #os.system('say "your program has started"')
    n = 100000000;
    entanglementCount=0;
    totalTime = n * Period / 1000000; #convert to seconds #will divide counts by this to get a rate.
    start=time.time()
    for i in range(1, n):
        if (FlagA == 0) and (NDSPMDelayA == 0):
            NodeARequestCounter += 1;
            photonProduced = random.randint(1,1000);
            if photonProduced <= PhotonProb:
                FlagA = 1;
                TranA = NCycles+1; #check if +1 should be here 
                #immediately see if photon makes it to the other end
                photonTransmitted = random.randint(1,10000);
                if photonTransmitted <= photonFiberProb:
                    PhotonA = 1;
                    #print("yes")
            NDSPMDelayA = 0;#if a photon is fired it can't fire again until at least the response from the NDSPM
        if (FlagB == 0) and (NDSPMDelayB == 0):
            NodeBRequestCounter += 1;
            photonProduced = random.randint(1,1000);
            if photonProduced <= PhotonProb:
                FlagB = 1;
                TranB = NCycles+1; #check if +1 should be here
                #immediately see if photon makes it to the other end
                photonTransmitted = random.randint(1,10000);
                if photonTransmitted <= photonFiberProb:
                    PhotonB = 1;
            NDSPMDelayB = 0;#if a photon is fired it can't fire again until at least the response from the NDSPM
    #option 1: 
        #if both photons are produced, instantly add one to the entanglement counter as we assume 100% efficient storage that lasts forever
        #still have the count down happen so that the nodes know when to produce a new photon. - this is now the returnA and returnB counters
        #additional counter takes into account the time for the photons to be stored
        if NDSPMDelayA > 0:
            NDSPMDelayA -= 1;
        if NDSPMDelayB > 0:
            NDSPMDelayB -= 1;
    
        if TranA > 0:
            if TranA == 1:
                #photon is stored when this hits zero from 1
                StoredA = True;
            TranA -= 1;
        if TranB > 0:
            if TranB == 1:
                StoredB = True;
            TranB -= 1;
        
        #this is what the network thinks to be true. In the case of perfect storage we already determined if photons were both really there.
        if StoredA == True and StoredB == True:
            if PhotonA == 1 and PhotonB == 1:
                #adding in a random generator to account for 50% chance of entanglment.. shouldn't change anything fundamentally but will affect variation.
                ent=random.randint(0, 1);
                if ent:
                    entanglementCount += 1;
            PhotonA = 0;
            PhotonB = 0;
            ReturnA = NCycles+1 #still  need to check if the +1 should be here
            ReturnB = NCycles+1
            StoredB = False
            StoredA = False
        
        if ReturnA > 0:
            if ReturnA==1:
                FlagA = 0;
            ReturnA -= 1;
        if ReturnB > 0:
            if ReturnB==1:
                FlagB=0;
            ReturnB -= 1;
            
    stop=time.time()
    entanglementRate = entanglementCount/totalTime
    #ratelist.append(entanglementRate)
    fields = [L,entanglementRate,NodeARequestCounter,NodeBRequestCounter]
    with open("Storage_50k_1500nsClock_"+timestr+".csv", 'a+') as f:   
        writer = csv.writer(f)
        writer.writerow(fields)
    print(str(entanglementCount)+" events in" + str(totalTime) + " seconds.")
    #print(totalTime)
    print("This corresponds to an entalnglement rate of "+str(entanglementRate) + "events per second.")
    print("total time to run code (min):")
    print((stop-start)/60)
    return fields

def double(i):
    print(i)
    return i*2



if __name__ == "__main__":
    #set_start_method('spawn') 
    #result = main()   
    timestr = time.strftime("%Y%m%d-%H%M%S"); #gives a string in year - month -day, hour - minute - second format
    print(timestr);
    func = partial(simloop, timestr);
    ratelist = [];
    lengthlist= [];
    plotlist=[];
    with Pool(6) as p:
        plotlist.append(p.map(func, range(0,5005,50)))
    
    with open("Storage_50k_1500nsClock"+timestr+"final.csv", 'a+') as f:   
        writer = csv.writer(f)
        writer.writerows(plotlist[0])
    
    for i in plotlist[0]:
        lengthlist.append(i[0]);
        ratelist.append(i[1]);
        
    plt.scatter(lengthlist,ratelist)
    plt.xlabel('distance (km)');
    plt.yscale('log');
    plt.ylabel('entanglement rate (1/s)');


# os.system('say "your program has finished"')

# for i in plotlist[0]:
#     lengthlist.append(i[0]);
#     ratelist.append(i[1]);


# plt.scatter(lengthlist,ratelist)
# plt.xlabel('distance (km)');
# plt.yscale('log');
# plt.ylabel('entanglement rate (1/s)');

# #option 2:
    #track the photon's arrival time to the BSA