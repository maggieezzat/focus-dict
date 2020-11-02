from elasticsearch import Elasticsearch, helpers
import os
import time

def init_esServer(host, port):
    es = Elasticsearch(host=host, port=port)
    return es

def create_index(es, index_name):
    es.indices.create(index=index_name)

def check_if_index_exists(es, index_name):
    return es.indices.exists(index=index_name)

def delete_index(es, index_name):
    if check_if_index_exists(es, index_name):
        if es.indices.delete(index_name)['acknowledged'] == True:
            return True
        else:
            return False

def insert_doc(es, index_name, body, id=None):
    es.index(index_name, doc_type="corpus", id=id, body= body)

def get_docs(es, index_name, term, limit=100):
    res = es.search(index=index_name, body={"query":{"constant_score":{"filter":{"term":{"text":term}}}}}, size=limit)['hits']['hits']
    outcomes = []
    for i in res:
        outcomes.append(i['_source']['text'])
    return outcomes
    #res = helpers.scan(es,query={"from":0, "query":{"term":{"text":term}}})
    #for r in res:
    #    outcomes.append(r['_source']['text'])
    #    if len(outcomes)>=limit:
    #        break
    #return outcomes
        
def bulk_insert(es,docs):
    helpers.bulk(es,actions=docs)

def insert_corpus_es(es, index_name, corpus_path):
    with open(corpus_path,'r', encoding='utf-8') as f:
        count = 0
        docs = []
        for line in f:
            count += 1
            doc = {"_index":index_name, "_id":count, "_source":{"text":line.strip()}}
            docs.append(doc)
            if count % 500000 == 0:
                bulk_insert(es,docs)
                docs = []
                print(count)
        if len(docs)>0:
            bulk_insert(es, docs)
            


if __name__=='__main__':
    
    
    INDEX_NAME = "corpus_merged"
    es = init_esServer('localhost',9200)
    #delete_index(es, INDEX_NAME)
    if not check_if_index_exists(es, INDEX_NAME):
        start = time.time()
        create_index(es, INDEX_NAME)
        #insert_corpus_es(es, INDEX_NAME, "/media/corpus_merged_clean.txt")
        end = time.time()
        hours, rem = divmod(end-start, 3600)
        minutes, seconds = divmod(rem, 60)
        print("Done Creating Indices. Total time:  {:0>2}:{:0>2}:{:0>2}".format(int(hours),int(minutes),int(seconds)))

