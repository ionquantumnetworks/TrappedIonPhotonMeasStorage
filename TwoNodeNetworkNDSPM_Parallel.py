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
import matplotlib.pyplot as plt
import csv
from multiprocessing import Pool
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
    DetectorEfficiency780 = 0.8;
    NDSPMEfficiency = 0.75; #Photon loss through NDSPM.. doesn't talk about fidelity at all
    
    #Photon Registers, begin with no photon. Turn to 1 if the photon makes it through the fiber.
    PhotonA = 0;
    PhotonB = 0;
    
    #Flag Registers, begin with flag off. This lets the nodes know if they should fire or not
    FlagA = 0;
    FlagB = 0;
    
    #===For case with no photon storage===#
    #Transmission Counters: These go down by 1 every clock cycle.
    #In the loop they are put to a value when a photon is successfully flagged.
    #The nodes will wait to fire again until this goes to zero.
    TranA = 0;
    TranB = 0;
    NDSPMDelayA = 0;#time it takes NDSPM to make measurement in terms of clock cycles
    NDSPMDelayB = 0;
    #=======================================#
    #PhotonProductionProbability
    PhotonProb = (BranchingRatio * CollectionEfficiency * IonFiberCoupling * QFC780Efficiency * NDSPMEfficiency)*1000 #out of 1000
    #Network Length
    L = i/100; #km
    #time to traverse network
    Lt =L*1000*1.5/(3*10**8) #kms multiplied by index of refraction and units of seconds
    #Clock Cycle Time (us)
    Period = 1.5;
    #Clock Rep Rate (MHz)
    f = 1/Period;
    #Calculate number of cycles to wait if photon successfully collected, rounded up to nearest cycle
    NCycles = math.ceil(2*Lt / Period * 10**6);#factor of 2 is for classical channel response time
    #Photon Transmission Probability
    #4dB for 1 km
    #keep in mind the effective rounding being done above
    #0.8 is for detector effciency @780
    photonFiberProb = 10**((-3*L)/10)*10000*DetectorEfficiency780; #convert to being out of 10000 for random number generation.
    print("photon probabilty into fiber after QFC and NDSPM:" + str(PhotonProb))
    print("Distance:" + str(L) + "km")
    print("Network must wait " + str(NCycles) +" cycles " + "to fire again when a photon is successfully sent.")
    #os.system('say "your program has started"')
    n = 100000000;
    #recording entanglement events
    entanglementCount=0;
    #recording the times node A fires at a time that could produce entanglement(rather than wasted shots)
    usefulA = 0;
    #recording the times node B fires at a time that could produce entanglement(rather than wasted shots)
    usefulB = 0; 
    #realtime runtime
    totalTime = n * Period / 1000000; #convert to seconds #will divide counts by this to get a rate.
    start=time.time()
    for i in range(1, n):
        if (FlagA == 0) and (NDSPMDelayA == 0):
            NodeARequestCounter += 1;
            if (TranB == 0):
                usefulA += 1;
            photonProduced = random.randint(1,1000);
            if photonProduced <= PhotonProb:
                FlagA = 1;
                TranA = NCycles+1; #check if +1 should be here 
                #immediately see if photon makes it to the other end
                photonTransmitted = random.randint(1,10000);
                if photonTransmitted <= photonFiberProb:
                    PhotonA = 1;
                    #print("yes")
            NDSPMDelayA = 0+0; #if a photon is fired it can't fire again until at least the response from the NDSPM
        if (FlagB == 0) and (NDSPMDelayB == 0):
            NodeBRequestCounter += 1;
            #if node A isn't waiting for the network length (and didn't just fire because they are trying simlutaneously), node B is not wasting it's photon production.
            #if (TranA == 0) or (TranA == NCycles + 1):
            #    usefulB += 1;
            photonProduced = random.randint(1,1000);
            if photonProduced <= PhotonProb:
                FlagB = 1;
                TranB = NCycles+1; #check if +1 should be here
                #immediately see if photon makes it to the other end
                photonTransmitted = random.randint(1,10000);
                if photonTransmitted <= photonFiberProb:
                    PhotonB = 1;
            NDSPMDelayB = 0+0;#if a photon is fired it can't fire again until at least the response from the NDSPM
    #option 1: 
        #if both just produced photons at the same time, instantly add one to the entanglement counter
        #still have the count down happen so that the nodes know when to produce a new photon
        #this will have the disadvantage of not keeping track of when the photon makes it to the other side
        #which would matter for the storage and retrieval case.
        if PhotonA == 1 and PhotonB == 1:
            entanglementCount += 1;
        PhotonA = 0;
        PhotonB = 0;
        if TranA > 0:
            TranA -= 1;
        if TranB > 0:
            TranB -= 1;
        if TranA == 0:
            FlagA = 0;
        if TranB == 0:
            FlagB = 0;
        if NDSPMDelayA > 0:
            NDSPMDelayA -= 1;
        if NDSPMDelayB > 0:
            NDSPMDelayB -= 1;
    stop=time.time()
    entanglementRate = entanglementCount/totalTime
    fields = [L,entanglementRate,NodeARequestCounter,NodeBRequestCounter,usefulA,usefulB]
    with open("NoStorage_NoDelay_1500nsClock"+timestr+".csv", 'a+') as f:   
        writer = csv.writer(f)
        writer.writerow(fields)
    print(str(entanglementCount)+" events in " + str(totalTime) + " seconds.")
    #print(totalTime)
    print("This corresponds to an entalnglement rate of "+str(entanglementRate) + " events per second.")
    print("total time to run code (min):")
    print((stop-start)/60)
    return fields

if __name__ == "__main__":
    #set_start_method('spawn') 
    #result = main()   
    timestr = time.strftime("%Y%m%d-%H%M%S"); #gives a string in year - month -day, hour - minute - second format
    daystr = time.strftime("%Y%m%d");
    print(timestr);
    func = partial(simloop, timestr);
    ratelist = [];
    lengthlist= [];
    plotlist=[];
    with Pool(6) as p:
        plotlist.append(p.map(func,range(0,501,5)))
    with open("NoStorage_NoDelay_1500nsClock"+timestr+"final.csv", 'a+') as f:   
        writer = csv.writer(f)
        writer.writerows(plotlist[0])
    for i in plotlist[0]:
        lengthlist.append(i[0]);
        ratelist.append(i[1]);
        
    plt.scatter(lengthlist,ratelist)
    plt.xlabel('distance (km)');
    plt.yscale('log');
    plt.ylabel('entanglement rate (1/s)');