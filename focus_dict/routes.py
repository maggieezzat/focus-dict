from flask import render_template, request, session
from flask_paginate import Pagination, get_page_args, get_page_parameter
from elasticsearch import Elasticsearch
from focus_dict import app
from focus_dict.utils import get_docs
import math
import os
from flask_pymongo import PyMongo



def gen_positions(total):
            
    page_position = {}
    pos = 1
    for i in range(total):
        if i!=0 and i%10==0:
            pos+=1
        page_position[i] = pos

    session['page_position'] = page_position
    return page_position

def import_collections(path="focus_dict/static/collections.txt"):
    arr = []
    i=1
    with open(path, 'r', encoding='utf-8') as f:
        for line in f:
            clean = line.strip().split("-")
            if "None" in clean:
                clean = "الف مد" + " " + "         مجموعة " + clean[2]
            else:
                clean = clean[0] + " " + clean[1] + " " + "         مجموعة " + clean[2]
            t = (i, line.strip(), clean, 0, 0, 0)
            arr.append(t)
            i+=1
    
    session['collections'] = arr
    return arr





def get_page_pairs(offset=0, per_page=10):
    
    end = offset+per_page
    if end > session['total']:
        end = session['total']
    current_coll = session['current_coll']
    
    l = []
    for i in range(offset,end):
        l.append(i)
    
    page_pairs = []
    for num in l:
        p = mongo.db[current_coll].find_one({'index':num})
        page_pairs.append(p)

    return page_pairs



es = Elasticsearch("127.0.0.1", port=9200)
INDEX_NAME = "corpus_merged"

mongo = PyMongo(app)


#when a web browser requests either of these two URLs, Flask is going to invoke this function 
# and pass the return value of it back to the browser as a response
@app.route('/', methods=['GET', 'POST'])
def index():

    session['collections'] = import_collections()
    for i in range(len(session['collections'])):
        coll = session['collections'][i]
        coll = coll[1]
        agr = [ {'$group': {'_id': 1, 'all': { '$sum': '$touched' } } } ]
        val = list(mongo.db[coll].aggregate(agr))
        val = int(val[0]['all'])
        total = mongo.db[coll].find().count() 
        per = str(int((val/total)*100))+"%"
        session['collections'][i] = (session['collections'][i][0], session['collections'][i][1], session['collections'][i][2], val, total, per)
    
    session['current_page'] = 1
    session['search_left'] = {}
    session['search_right'] = {}

    return render_template('index.html', databases=session['collections'])





@app.route('/main', methods=['GET', 'POST'])
def main():

    req = request.form

    session['collections'] = import_collections()
    for i in range(len(session['collections'])):
        coll = session['collections'][i]
        coll = coll[1]
        agr = [ {'$group': {'_id': 1, 'all': { '$sum': '$touched' } } } ]
        val = list(mongo.db[coll].aggregate(agr))
        val = int(val[0]['all'])
        total = mongo.db[coll].find().count() 
        per = str(int((val/total)*100))+"%"
        session['collections'][i] = (session['collections'][i][0], session['collections'][i][1], session['collections'][i][2], val, total, per)
    
    session['current_page'] = 1
    session['search_left'] = {}
    session['search_right'] = {}

    if not req:
        page, per_page, offset = get_page_args(page_parameter='page', per_page_parameter='per_page')
        session['current_page'] = page
        pagination_pairs = get_page_pairs(offset=offset, per_page=per_page)
        pagination = Pagination(page=page, per_page=per_page, total=session['total'], css_framework='bootstrap4')
        return render_template('main.html', res_word1=session['search_left'], res_word2=session['search_right'], pairs=pagination_pairs, pagination=pagination)

    
    for k,v in req.items():
        session['current_coll'] = k
        current_coll = session['current_coll']
        cursor = mongo.db[current_coll].find({})
        pairs = []
        for document in cursor:
          pairs.append(document)

        session['pairs'] = pairs

        session['total'] = len(session['pairs'])
        session['page_position']  = gen_positions(session['total'])
        page, per_page, offset = get_page_args(page_parameter='page', per_page_parameter='per_page')
        session['current_page'] = page
        pagination_pairs = get_page_pairs(offset=offset, per_page=per_page)
        pagination = Pagination(page=page, per_page=per_page, total=session['total'], css_framework='bootstrap4')
        return render_template('main.html', res_word1=session['search_left'], res_word2=session['search_right'], pairs=pagination_pairs, pagination=pagination)



@app.route('/back', methods=['GET', 'POST'])
def back():
    for i in range(len(session['collections'])):
        coll = session['collections'][i]
        coll = coll[1]
        agr = [ {'$group': {'_id': 1, 'all': { '$sum': '$touched' } } } ]
        val = list(mongo.db[coll].aggregate(agr))
        val = int(val[0]['all'])
        total = mongo.db[coll].find().count() 
        per = str(int((val/total)*100))+"%"
        session['collections'][i] = (session['collections'][i][0], session['collections'][i][1], session['collections'][i][2], val, total, per)
    
    return render_template('index.html', databases=session['collections'])




@app.route('/batch', methods=['GET', 'POST'])
def batch():


    current_coll = session['current_coll']

    req = request.form

    if not req:
        page, per_page, offset = get_page_args(page_parameter='page', per_page_parameter='per_page')
        current_page = page
        pagination_pairs = get_page_pairs(offset=offset, per_page=per_page)
        pagination = Pagination(page=page, per_page=per_page, total=session['total'], css_framework='bootstrap4')
        return render_template('main.html', res_word1=session['search_left'], res_word2=session['search_right'], pairs=pagination_pairs, pagination=pagination)

    pair = {}
    for k,v in req.items():
        if k == 'word1':
            pair = mongo.db[current_coll].find_one({"word1": v})
        elif k == 'word2':
            pair = mongo.db[current_coll].find_one({"word2": v})


    ind = pair['index']
    page = session['page_position'][ind]
    session['current_page'] = page

    offset = int(ind/10) * 10
    per_page = 10
    pagination_pairs = get_page_pairs(offset=offset, per_page=per_page)
    pagination = Pagination(page=page, per_page=per_page, total=session['total'], css_framework='bootstrap4')


    res_word1 = {}
    res_word1['SearchTerm'] = pair['word1']
    sents_word1 = get_docs(es, INDEX_NAME, pair['word1'])
    sents_word1 = sents_word1[:100]
    res_word1['hits'] = sents_word1
    res_word1['total'] = len(sents_word1)

    res_word2 = {}
    res_word2['SearchTerm'] = pair['word2']
    sents_word2 = get_docs(es, INDEX_NAME, pair['word2'])
    sents_word2 = sents_word2[:100]
    res_word2['hits'] = sents_word2    
    res_word2['total'] = len(sents_word2)

    session['search_left'] = res_word1
    session['search_right'] = res_word2

    return render_template('main.html', res_word1=res_word1, res_word2=res_word2, pairs=pagination_pairs, pagination=pagination)



@app.route('/search', methods=['GET','POST'])
def req_search():

    current_coll = session['current_coll']

    req = request.form

    
    if not req:
        page, per_page, offset = get_page_args(page_parameter='page', per_page_parameter='per_page')
        session['current_page'] = page
        pagination_pairs = get_page_pairs(offset=offset, per_page=per_page)
        pagination = Pagination(page=page, per_page=per_page, total=session['total'], css_framework='bootstrap4')
        return render_template('main.html', res_word1=session['search_left'], res_word2=session['search_right'], pairs=pagination_pairs, pagination=pagination)

    
    page = session['current_page']
    offset = page*10 - 10
    per_page = 10
    pagination_pairs = get_page_pairs(offset=offset, per_page=per_page)
    pagination = Pagination(page=page, per_page=per_page, total=session['total'], css_framework='bootstrap4')

    res_word1 = {}
    res_word2 = {}

    for k,v in req.items():
        search_term = v
        if k == 'search-left':
            res_word1 = {}
            res_word2 = session['search_right']

            if len(search_term) > 0:
                sents = get_docs(es, INDEX_NAME, search_term)
                sents = sents[:100]
                res_word1['SearchTerm'] = search_term
            else:
                sents = []
                res_word1['SearchTerm'] = " "
            
            res_word1['hits'] = sents
            res_word1['total'] = len(sents) 
            session['search_left'] = res_word1
        
        elif k == 'search-right':
            res_word1 = session['search_left']
            res_word2 = {}
            if len(search_term) > 0:
                sents = get_docs(es, INDEX_NAME, search_term)
                sents = sents[:100]
                res_word2['SearchTerm'] = search_term
            else:
                sents =[]
                res_word2['SearchTerm']=" "
            res_word2['hits'] = sents
            res_word2['total'] = len(sents)
            session['search_right'] = res_word2
    

    return render_template('main.html', res_word1=res_word1, res_word2=res_word2, pairs=pagination_pairs, pagination=pagination)



@app.route('/save', methods=['GET','POST'])
def save_state():

    current_coll = session['current_coll']

    req = request.form

    if not req:
        page, per_page, offset = get_page_args(page_parameter='page', per_page_parameter='per_page')
        session['current_page'] = page
        pagination_pairs = get_page_pairs(offset=offset, per_page=per_page)
        pagination = Pagination(page=page, per_page=per_page, total=session['total'], css_framework='bootstrap4')
        return render_template('main.html', res_word1=session['search_left'], res_word2=session['search_right'], pairs=pagination_pairs, pagination=pagination)


    for key, word in req.items():
        word_order = key.split("_")[0]
        if word_order == "word1":
            pair = mongo.db[current_coll].find_one({"word1": word})
            filter = {"word1": word}
            newvalues = { "$set": { 'touched': 1} } 
            result =  mongo.db[current_coll].update_one(filter, newvalues)
            if key == 'word1_merge':
                state = pair['word1_merge']
                
                if state == False:
                    newvalues = { "$set": { 'word1_merge': True, "word1_delete":False } } 
                    result =  mongo.db[current_coll].update_one(filter, newvalues)
                else:
                    newvalues = { "$set": { 'word1_merge': False} }
                    result =  mongo.db[current_coll].update_one(filter, newvalues)           
            elif key == 'word1_delete':
                state = pair['word1_delete']
                if state == False:
                    newvalues = { "$set": { 'word1_delete': True, "word1_merge":False } } 
                    result =  mongo.db[current_coll].update_one(filter, newvalues)
                else:
                    newvalues = { "$set": { "word1_delete":False } } 
                    result =  mongo.db[current_coll].update_one(filter, newvalues)
        elif word_order == "word2":
            pair = mongo.db[current_coll].find_one({"word2": word})
            filter = {"word2": word}
            newvalues = { "$set": { 'touched': 1} } 
            result =  mongo.db[current_coll].update_one(filter, newvalues)
            if key == 'word2_merge':
                state = pair['word2_merge']
                if state == False:
                    newvalues = { "$set": { 'word2_merge': True, "word2_delete":False } } 
                    result =  mongo.db[current_coll].update_one(filter, newvalues)
                else:
                    newvalues = { "$set": { 'word2_merge': False } } 
                    result =  mongo.db[current_coll].update_one(filter, newvalues)
            elif key == 'word2_delete':
                state = pair['word2_delete']
                if state == False:
                    newvalues = { "$set": { 'word2_delete': True, "word2_merge":False } } 
                    result =  mongo.db[current_coll].update_one(filter, newvalues)
                else:
                    newvalues = { "$set": { "word2_delete":False } } 
                    result =  mongo.db[current_coll].update_one(filter, newvalues)
        
    
    page = session['current_page']
    offset = page*10 - 10
    per_page = 10
    pagination_pairs = get_page_pairs(offset=offset, per_page=per_page)
    pagination = Pagination(page=page, per_page=per_page, total=session['total'], css_framework='bootstrap4')
    return render_template('main.html', res_word1=session['search_left'], res_word2=session['search_right'], pairs=pagination_pairs, pagination=pagination)
