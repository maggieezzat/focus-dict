from flask import render_template, request
from flask_paginate import Pagination, get_page_args, get_page_parameter
from elasticsearch import Elasticsearch
from focus_dict import app
from focus_dict.utils import get_docs
from focus_dict.models import Pair
import math
import os
from mongoengine import connect, disconnect_all



def gen_positions(total):
            
    page_position = {}
    pos = 1
    for i in range(total):
        if i!=0 and i%10==0:
            pos+=1
        page_position[i] = pos

    return page_position




def get_page_pairs(offset=0, per_page=10):
    
    end = offset+per_page
    
    l = []
    for i in range(offset,end):
        l.append(i)
    
    p = Pair.objects(index__in=l)
    
    page_pairs = []
    for pair in p:
        page_pairs.append(pair.to_dict())

    return page_pairs


def import_dbs(path="focus_dict/static/databases.txt"):
    arr = []
    i=1
    with open(path, 'r', encoding='utf-8') as f:
        for line in f:
            clean = line.strip().split("-")
            if "None" in clean:
                clean = "الف مد" + " " + "         مجموعة " + clean[2]
            else:
                clean = clean[0] + " " + clean[1] + " " + "         مجموعة " + clean[2]
            t = (i, line.strip(), clean)
            arr.append(t)
            i+=1
    return arr



INDEX_NAME = "corpus_merged"
search_left = {}
search_right = {}
current_page = 1
total = 0
page_position = []
es = Elasticsearch("127.0.0.1", port=9200)
databases = import_dbs()
disconnect_all()
conn = ""

#when a web browser requests either of these two URLs, Flask is going to invoke this function 
# and pass the return value of it back to the browser as a response
@app.route('/', methods=['GET', 'POST'])
@app.route('/index', methods=['GET', 'POST'])
def index():

    req = request.form

    if not req:
        return render_template('index.html', databases=databases)
    
    for k,v in req.items():
        global total
        global page_position
        global conn
        
        disconnect_all()
        conn = k
        connect(k, host='localhost', port=27017)
        total = len(Pair.objects())
        page_position = gen_positions(total)
        page, per_page, offset = get_page_args(page_parameter='page', per_page_parameter='per_page')
        current_page = page
        pagination_pairs = get_page_pairs(offset=offset, per_page=per_page)
        pagination = Pagination(page=page, per_page=per_page, total=total, css_framework='bootstrap4')
        return render_template('main.html', res_word1=search_left, res_word2=search_right, pairs=pagination_pairs, pagination=pagination)




@app.route('/batch', methods=['GET', 'POST'])
def batch():

    req = request.form

    global current_page
    global search_right
    global search_left
    global conn

    connect(conn)
    if not req:
        page, per_page, offset = get_page_args(page_parameter='page', per_page_parameter='per_page')
        current_page = page
        pagination_pairs = get_page_pairs(offset=offset, per_page=per_page)
        pagination = Pagination(page=page, per_page=per_page, total=total, css_framework='bootstrap4')
        return render_template('main.html', res_word1=search_left, res_word2=search_right, pairs=pagination_pairs, pagination=pagination)

    pair = {}
    for k,v in req.items():
        if k == 'word1':
            pair = Pair.objects(word1=v).first()
        elif k == 'word2':
            pair = Pair.objects(word2=v).first()

    ind = pair['index']
    page = page_position[ind]
    current_page = page
    
    offset = int(ind/10) * 10
    per_page = 10
    pagination_pairs = get_page_pairs(offset=offset, per_page=per_page)
    pagination = Pagination(page=page, per_page=per_page, total=total, css_framework='bootstrap4')


    res_word1 = {}
    res_word1['SearchTerm'] = pair['word1']
    #sents_word1 = get_docs(es, INDEX_NAME, pair['word1'])
    sents_word1 = []
    sents_word1 = sents_word1[:100]
    res_word1['hits'] = sents_word1
    res_word1['total'] = len(sents_word1)

    res_word2 = {}
    res_word2['SearchTerm'] = pair['word2']
    #sents_word2 = get_docs(es, INDEX_NAME, pair['word2'])
    sents_word2 = []
    sents_word2 = sents_word2[:100]
    res_word2['hits'] = sents_word2    
    res_word2['total'] = len(sents_word2)

    search_left = res_word1
    search_right = res_word2

    return render_template('main.html', res_word1=res_word1, res_word2=res_word2, pairs=pagination_pairs, pagination=pagination)



@app.route('/search', methods=['GET','POST'])
def req_search():

    req = request.form

    global current_page
    global search_right
    global search_left
    global conn

    connect(conn)
    
    if not req:
        page, per_page, offset = get_page_args(page_parameter='page', per_page_parameter='per_page')
        current_page = page
        pagination_pairs = get_page_pairs(offset=offset, per_page=per_page)
        pagination = Pagination(page=page, per_page=per_page, total=total, css_framework='bootstrap4')
        return render_template('main.html', res_word1=search_left, res_word2=search_right, pairs=pagination_pairs, pagination=pagination)

    
    page = current_page
    offset = page*10 - 10
    per_page = 10
    pagination_pairs = get_page_pairs(offset=offset, per_page=per_page)
    pagination = Pagination(page=page, per_page=per_page, total=total, css_framework='bootstrap4')

    res_word1 = {}
    res_word2 = {}

    for k,v in req.items():
        search_term = v
        if k == 'search-left':
            res_word1 = {}
            res_word2 = search_right

            if len(search_term) > 0:
                #sents = get_docs(es, INDEX_NAME, search_term)
                sents = []
                sents = sents[:100]
                res_word1['SearchTerm'] = search_term
            else:
                sents = []
                res_word1['SearchTerm'] = " "
            
            res_word1['hits'] = sents
            res_word1['total'] = len(sents) 
            search_left = res_word1
        
        elif k == 'search-right':
            res_word1 = search_left
            res_word2 = {}
            if len(search_term) > 0:
                #sents = get_docs(es, INDEX_NAME, search_term)
                sents = []
                sents = sents[:100]
                res_word2['SearchTerm'] = search_term
            else:
                sents =[]
                res_word2['SearchTerm']=" "
            res_word2['hits'] = sents
            res_word2['total'] = len(sents)
            search_right = res_word2
    

    return render_template('main.html', res_word1=res_word1, res_word2=res_word2, pairs=pagination_pairs, pagination=pagination)



@app.route('/save', methods=['GET','POST'])
def save_state():

    global current_page
    global conn

    connect(conn)

    req = request.form

    if not req:
        page, per_page, offset = get_page_args(page_parameter='page', per_page_parameter='per_page')
        current_page = page
        pagination_pairs = get_page_pairs(offset=offset, per_page=per_page)
        pagination = Pagination(page=page, per_page=per_page, total=total, css_framework='bootstrap4')
        return render_template('main.html', res_word1=search_left, res_word2=search_right, pairs=pagination_pairs, pagination=pagination)


    for key, word in req.items():
        word_order = key.split("_")[0]
        if word_order == "word1":
            pair = Pair.objects(word1=word).first()
            if key == 'word1_merge':
                state = pair['word1_merge']
                if state == False:
                    pair.update(set__word1_merge=True)
                    pair.update(set__word1_delete=False)
                else:
                    pair.update(set__word1_merge=False)             
            elif key == 'word1_delete':
                state = pair['word1_delete']
                if state == False:
                    pair.update(set__word1_delete=True)
                    pair.update(set__word1_merge=False)
                else:
                    pair.update(set__word1_delete=False)
        elif word_order == "word2":
            pair = Pair.objects(word2=word).first()
            if key == 'word2_merge':
                state = pair['word2_merge']
                if state == False:
                    pair.update(set__word2_merge=True)
                    pair.update(set__word2_delete=False)
                else:
                    pair.update(set__word2_merge=False)
            elif key == 'word2_delete':
                state = pair['word2_delete']
                if state == False:
                    pair.update(set__word2_delete=True)
                    pair.update(set__word2_merge=False)
                else:
                    pair.update(set__word2_delete=False)
        
    
    page = current_page
    offset = page*10 - 10
    per_page = 10
    pagination_pairs = get_page_pairs(offset=offset, per_page=per_page)
    pagination = Pagination(page=page, per_page=per_page, total=total, css_framework='bootstrap4')
    return render_template('main.html', res_word1=search_left, res_word2=search_right, pairs=pagination_pairs, pagination=pagination)
