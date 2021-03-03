from ccc import Corpus
from ccc.keywords import Keywords
from pandas import read_csv
import pytest

from .conftest import LOCAL


@pytest.mark.skipif(not LOCAL, reason='works on my machine')
@pytest.mark.brexit
@pytest.mark.meta
def test_keywords_from_satt_values(brexit):

    # get relevant ids
    meta = read_csv(brexit['meta_path'], dtype=str, sep="\t")
    ids_replies = set(meta.loc[meta['in_reply_status'] == "1"]['id'])

    # create subcorpus
    corpus = Corpus(corpus_name=brexit['corpus_name'])
    df_dump = corpus.query_s_att('tweet_id', ids_replies).df

    # keywords
    keywords = Keywords(corpus, df_dump, p_query='lemma')
    lines = keywords.show(order='log_ratio', cut_off=None)
    assert(lines.index[0] == "@pama1969")


@pytest.mark.query
def test_keywords_from_query(germaparl):

    # get subcorpus as dump
    corpus = Corpus(corpus_name=germaparl['corpus_name'],
                    registry_path=germaparl['registry_path'])
    df_dump = corpus.query('"Seehofer" expand to s').df

    # keywords
    keywords = Keywords(corpus, df_dump)
    lines = keywords.show(order='log_ratio')
    assert(lines.index[1] == "Gesundheitsreform")


@pytest.mark.query
def test_keywords_from_dump(germaparl):

    # get subcorpus as dump
    corpus = Corpus(corpus_name=germaparl['corpus_name'],
                    registry_path=germaparl['registry_path'])
    df_dump = corpus.dump_from_query('"und" expand to s')

    # keywords
    keywords = Keywords(corpus, df_dump)
    lines = keywords.show(order='log_likelihood', min_freq=10)
    print(lines)
    assert(lines.index[1] == "Dame")


@pytest.mark.subcorpus
def test_keywords_switch(germaparl):

    # get some regions
    corpus = Corpus(corpus_name=germaparl['corpus_name'],
                    registry_path=germaparl['registry_path'])
    df_all = corpus.query('"und" expand to s', name='Und_all').df

    df_head = df_all.head(500)
    df_tail = df_all.tail(500)

    # will show keywords for head
    keywords = Keywords(corpus, df_dump=df_head, p_query="lemma")
    lines_head = keywords.show(order='log_likelihood')

    # will show keywords for tail
    keywords = Keywords(corpus, df_dump=df_tail, p_query="lemma")
    lines_tail = keywords.show(order='log_likelihood')

    assert(not lines_head.equals(lines_tail))
