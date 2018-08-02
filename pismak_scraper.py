#!/usr/bin/env python
# -*- coding: utf-8 -*- 

import urllib2
import urllib
import csv
import re
import time
import sys
import os
import time
import datetime

from selenium import webdriver
from selenium.webdriver.common.keys import Keys
from selenium.common.exceptions import TimeoutException
from selenium.webdriver.chrome.options import Options
from xvfbwrapper import Xvfb
from bs4 import BeautifulSoup

USER_AGENT = 'Mozilla/5.0 (Windows NT 6.1) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/41.0.2228.0 Safari/537.36'
opts = Options()
opts.add_argument("user-agent="+USER_AGENT)
URL = 'http://www.pismak.cz/index.php?data=read&id=489600'
TAG_RE = re.compile(r'<[^>]+>')

def atoi(s):
    return int(s) if s.isdigit() else float(s)

def similar(a, b):
    return SequenceMatcher(None, a, b).ratio()

def load_page(URL):
    browser.set_page_load_timeout(12)
    while True:
        try:
            browser.get(URL)
        except TimeoutException:
            print "Timeout, retrying..."
            continue
        else:
            break
    return 
       
def check_exists_by_xpath(xpath):
    try:
        browser.find_element_by_xpath(xpath)
    except NoSuchElementException:
        return False
    return True

def create_url(y, m, pg, kat, zanr, vyber, ordd):
    url = "http://www.pismak.cz/index.php?data=list&&"
    url += "pg="+str(pg)+"&"
    url += "kat="+str(kat)+"&"
    url += "zanr="+str(zanr)+"&"
    url += "vyber="+str(vyber)+"&"
    url += "y="+str(y)+"&"
    url += "m="+str(m).zfill(2)+"&"
    url += "ok=ok&&&"
    url += "ord="+str(ordd)
    return url

def download_page(URL):
    headers = { 'User-Agent' : USER_AGENT }
    req = urllib2.Request(URL, None, headers)
    try:
        response = urllib2.urlopen(req)
    except Exception as e:
        return ""
    page = response.read()
    # print page
    response.close() # its always safe to close an open connection
    return page

def extract_page_IDs(URL):
    dataset = []
    time.sleep(2)
    load_page(URL)
    html = browser.page_source
    soup = BeautifulSoup(html, "lxml")
    table = soup.findAll("table", attrs={"class":"vypis"})
    if len(table) < 2:
        return -1
    else:
        table = table[1]

    dataset = []
    for row in table.find_all("tr")[1:]:
        index = int(msplt(str(row), [['index.php?data=read&amp;id=', 1], ['"', 0]]))
        dataset.append(index)
    return dataset

def msplt(s, l):
    if l == []: return s
    sn = s
    for inst in l:
        # print sn, inst[0], sn.split(inst[0])
        sn = sn.split(inst[0])[inst[1]]
    return sn

def iterate_and_move(source, phrase, num, l, count=0):
    occurence = 0
    for i, row in enumerate(source):
        if phrase in row:
            if occurence >= count:
                break
            else:
                occurence += 1
    return msplt(source[i+num], l)

def extract_block(source, start_str, end_str, start_num=0, end_num=0):
    occurence, start, end = 0, -1, -1
    N = len(source)
    for i in xrange(N):
        if start_str in source[i]:
            if occurence >= start_num:
                break
            else:
                occurence += 1
    start, occurence = i+1, 0
    for i in xrange(start+1, N):
        if end_str in source[i]:
            if occurence >= end_num:
                break
            else:
                occurence += 1
    end = i
    return source[start:end]

def remove_tags(text):
    return TAG_RE.sub('', text)

class Poet(object):
    def __init__(self, URL):
        raw_source = download_page(URL)
        soup = BeautifulSoup(raw_source, 'lxml')
        page = raw_source.split('<')
        page2 = raw_source.split('\n')
        self.poet_name = iterate_and_move(page, 'TD id="dilo_tabulka_nadpis', 0, [[">", -1]])
        self.poet_published = iterate_and_move(page, 'id="dilo_td">datum / id', 2, [[">", -1], [" ", 0]])
        self.poet_id = int(iterate_and_move(page, 'id="dilo_td">datum / id', 2, [[">", -1], [' ', 2]]))
        self.author_name = iterate_and_move(page, 'id="dilo_td">autor', 3, [[">", -1]])
        self.author_id = int(iterate_and_move(page, 'id="dilo_td">autor', 3, [["=", 3], ['"', 0]]))
        self.poet_category = iterate_and_move(page, 'id="dilo_td">kategorie', 3, [[">", -1]])
        self.poet_viewed = int(iterate_and_move(page, 'id="dilo_td">zobrazeno', 2, [[">", -1]])[:-1])
        self.poet_tips = int(iterate_and_move(page, 'id="dilo_td">počet tipů', 2, [[">", -1]]))
        self.poet_liked = int(iterate_and_move(page, 'id="dilo_td">v oblíbených', 2, [[">", -1]])[:-1])
        self.poet_clubbed = iterate_and_move(page, 'id="dilo_td">zařazeno do klubů', 2, [[">", -1]])
        dilo = soup.findAll("td", attrs={"id":"dilo_main"})
        if "dilo_tabulka_prolog" in raw_source:
            self.poet_prolog = dilo[0].text.encode('utf-8').replace("`", '"')
            self.poet_text = dilo[1].text.encode('utf-8').replace("`", '"')
        else:
            self.poet_prolog = ""
            self.poet_text = dilo[0].text.encode('utf-8').replace("`", '"')

    def get(self, variable):
        return eval(variable)

def pismak_download_category(cat):
    f = open('read_IDs_'+str(cat)+'.txt', 'a')
    for year in range(2018, 1999, -1):
        for month in range(12, -1, -1):
            stop, page = True, 1
            while stop:
                URL = create_url(year, month, page, cat, "", "", "")
                stck = extract_page_IDs(URL)
                if stck == -1:
                    stop = False
                    break
                else:
                    page += 1
                    for row in stck:
                        f.write(str(row)+'\n')
                    print stck
    f.close()

def save_mark(fileName, num):
    fmark = open(fileName, "w")
    fmark.write(str(num))
    fmark.close()
    return 

categories = [33, 15, 11, 13, 14]

### DOWNLOAD CATEGORY ###

display = Xvfb()
display.start()
browser = webdriver.Chrome("/home/hermanda/bin/chromedriver")
pismak_download_category(cat)
raw_input()
browser.close()
display.stop()

### DOWNLOAD POEMS WITH SAVED IDs ###

for cat in [14, 33, 15, 11, 13]:
    mark = 0
    mark_filename = "mark_poem_"+str(cat)+".dat"
    if os.path.isfile(mark_filename):
        with open(mark_filename, "r") as fmark:
            s = fmark.read()[:]
            print "Saved ", s
            mark = int(s[:])

    total_poems = 0
    fin = open('read_IDs_'+str(cat)+'.txt', 'r')
    for line in fin:
        total_poems += 1
    fin.close()

    fin = open('read_IDs_'+str(cat)+'.txt', 'r')
    fout = open('poems_'+str(cat)+'.txt', 'a')
    writer = csv.writer(fout, delimiter=';', quotechar='`', quoting=csv.QUOTE_NONNUMERIC)

    for i in range(mark):
        fin.next()

    flag_start = time.time()
    poems_downloaded = 0
    for num in fin:
        mark += 1
        poems_downloaded += 1
        poem_ID = int(num[:-1])
        URL = "http://www.pismak.cz/index.php?data=read&id="+str(poem_ID)
        time_eta = datetime.timedelta(seconds=(time.time()-flag_start)/poems_downloaded*(total_poems-mark))
        try:
            p = Poet(URL)
            data_row = [p.poet_id, p.poet_name, p.poet_published, \
                p.poet_category, cat, p.poet_viewed, \
                p.poet_tips, p.poet_liked, p.author_name, p.author_id, \
                p.poet_prolog, p.poet_text]
            print mark, "/", total_poems, "ETA", str(time_eta), data_row[0], data_row[1], data_row[2], data_row[6], data_row[8]
            writer.writerow(data_row)
        except:
            print mark, "/", total_poems, "ETA", str(time_eta), "ERR"
            pass
        save_mark(mark_filename, mark)
        time.sleep(0.01)

    fin.close()
    fout.close()
