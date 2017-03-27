# -*- coding: utf-8 -*-
"""
Created on Wed Oct 19 10:50:51 2016

@author: nancynan
"""
#import sys
from collections import defaultdict
#import os
import time
#os.system('clear')

class Apriori:
    
    
    def __init__(self, input_file, min_sup):
        self.input_file = input_file
        self.min_sup = min_sup
        self.translist = []
        self.items_with_sup = []
        self.freqset = defaultdict(int)
        self.enlarged = {}
        self.L1_count = {} 
        self.L1_TID = {}
    
    def _readFile(self):
        with open(self.input_file, 'rU') as f:
            for line in f:
#                print(line)
                lines = line.strip().split(',')
                lines[0] = 'age:'+lines[0]
                lines[1] = 'workclass:'+lines[1]
                lines[2] = 'fnlwgt:'+lines[2]
                lines[3] = 'education:'+lines[3]
                lines[4] = 'ed_num:'+lines[4]
                lines[5] = 'marital-status:'+lines[5]
                lines[6] = 'occupation:'+lines[6]
                lines[7] = 'relationship:'+lines[7]
                lines[8] = 'race:'+lines[8]
                lines[9] = 'sex:'+lines[9]
                lines[10] = 'capital-gain:'+lines[10]
                lines[11] = 'capital-loss:'+lines[11]
                lines[12] = 'hrs-per-week:'+lines[12]
                lines[13] = 'native-country:'+lines[13]
                yield lines
                
    def find_C1(self):
        C1=set()
        tid=0
        for row in self._readFile():
            rowi=frozenset(row)
            self.translist.append(rowi)
            tid += 1
            for i in rowi:
                C1.add(frozenset([i]))
                if i not in self.L1_TID:
                    self.L1_TID[i]=set([tid])
                else:
                    self.L1_TID[i].add(tid)
        return C1
                    
    
    def prunestep(self,C):
        L=set()
        freqsetloc = defaultdict(int)

        for item in C:
            if all(x in self.L1_count for x in list(item)):
                min_item = self.findMinItem(item)
                # TID:list of transaaction IDs for min_item
                TID = self.L1_TID[min_item]
                # only scan those with id in TID
                for index in TID:
                    if item.issubset(self.translist[index-1]):
                        self.freqset[item] += 1
                        freqsetloc[item] += 1
        for key,value in freqsetloc.items():
            support=float(value)/len(self.translist)
            if support>=min_sup:
                L.add(key)
        return L
        
    def findMinItem(self, items):
        # split into single item and return them with min_sup
        minimum =100000
        for key,value in self.L1_count.items():
            if key in items and value < minimum:
                minimum = value
        for key,value in self.L1_count.items():
            if value == minimum:
                return key 

    def getL1Count(self, C1):
        # for content of dictionary L1_count
        local_set = defaultdict(int)
        for item in C1:
            for rowi in self.translist:
                if item.issubset(rowi):
                    local_set[item] += 1
        for item, count in local_set.items():
            support = float(count)/len(self.translist)
            if support >= min_sup:
                key = [k for k in item][0]
                self.L1_count[key]=count
        return 
        
    def Support(self, item):
        return float(self.freqset[item]) / len(self.translist)    
        
    def joinstep(self, itemset, length):
        Ck=set()
        for i in itemset:
            for j in itemset:
                joinres=i.union(j)
                if len(joinres)==length:
                    Ck.add(joinres)
        return Ck
                
    def run(self):
        C1=self.find_C1()
        self.getL1Count(C1)
        Lk=self.prunestep(C1)
        k=2
        empset=set([])

        while (Lk!=empset):
            self.enlarged[k-1]=Lk
            nextC=self.joinstep(Lk,k)
            nextL=self.prunestep(nextC)
            Lk=nextL
            k+=1
            
        for value in self.enlarged.values():
            for item in value:
                self.items_with_sup.append(
                (tuple(item), self.Support(item)))
                    
    def printitembysup(self):
            i = 1
            for item, support in sorted(
            self.items_with_sup, key=lambda i: i[1],
            reverse=True):
                print ('Item %d: %s, Support: %.3f' % (i, str(item), support))
                i += 1
            
    def writefreqpat(self):
        with open('improved_apriori_output.csv', 'w') as f:
            for item, support in sorted(
                self.items_with_sup, key=lambda i: i[1],
                reverse=True):
                f.write('%.3f, %s\n' % (support, ','.join(item)))
    

if __name__ == '__main__':
#    begin1=time.time()
    input_file = 'adult_data.csv'
    
    #!!you can change into any number in (0,1)
    min_sup = 0.5

    a = Apriori(input_file, min_sup)
    a.run()
    a.printitembysup()

    # !!add # below if don't want csv file
    a.writefreqpat()
#    stop1=time.time()
#    print ('imroved_fp takes',(stop1-begin1))
