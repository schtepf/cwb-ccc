from ccc import Corpus
from pandas import read_csv
import json
import pytest


def test_macro(brexit_corpus):
    corpus = Corpus(brexit_corpus['corpus_name'],
                    lib_path=brexit_corpus['lib_path'],
                    registry_path=brexit_corpus['registry_path'])

    corpus.cqp.Exec("Last=/ap();")
    counts = corpus.counts.matches(corpus.cqp, name="Last")
    print(counts)


@pytest.mark.concordancing
def test_concordancing_simple():
    corpus = Corpus(
        corpus_name="SZ_2009_14"
    )

    query = r'[lemma="Angela"]? [lemma="Merkel"]'
    dump = corpus.query(query)
    concordance = corpus.concordance(dump)

    print(concordance.breakdown)
    print(concordance.size)
    print(concordance.lines(form='kwic'))


@pytest.mark.concordancing
def test_concordancing():
    corpus = Corpus(
        corpus_name="SZ_2009_14"
    )

    query = r'[lemma="Angela"]? [lemma="Merkel"] [word="\("] [lemma="CDU"] [word="\)"]'
    result = corpus.query(query, s_context='s')
    concordance = corpus.concordance(result)

    print(concordance.breakdown)
    print(concordance.size)
    print(concordance.lines([567792], form='dataframes')['df'][0])


@pytest.mark.anchor
def test_anchor():
    corpus = Corpus(
        corpus_name="SZ_2009_14"
    )

    query = r'@0[lemma="Angela"]? @1[lemma="Merkel"] [word="\("] @2[lemma="CDU"] [word="\)"]'
    result = corpus.query(query, s_context='s')
    concordance = corpus.concordance(result)

    print(concordance.breakdown)
    print(concordance.size)
    print(concordance.lines([567792], s_show=['text_id'], form='dataframes')['df'][0])
    print(concordance.lines(s_show=['text_id'], form='dataframes'))


@pytest.mark.collocates
def test_collocates():
    corpus = Corpus(
        corpus_name="SZ_2009_14"
    )

    query = '[lemma="Angela"]? [lemma="Merkel"] [word="\\("] [lemma="CDU"] [word="\\)"]'
    result = corpus.query(query, s_context='s')
    collocates = corpus.collocates(result)

    print(collocates.show())
    print(collocates.show(window=5, order="log_likelihood").head(10))


@pytest.mark.keywords
def test_keywords():
    meta = read_csv("/home/ausgerechnet/corpora/cwb/upload/efe/sz-2009-14.tsv.gz",
                    sep="\t", index_col=0, dtype=str)
    ids = set(meta.loc[
        (meta['ressort'] == "Panorama") & (meta['month'] == '201103')
    ].index.values)
    meta['s_id'] = meta.index

    corpus = Corpus(
        corpus_name="SZ_2009_14"
    )
    corpus.subcorpus_from_s_att('text_id', ids, name='tmp_keywords')
    keywords = corpus.keywords('tmp_keywords')
    print(keywords.show(order='dice').head(50))


@pytest.mark.skip
@pytest.mark.readme_argmin
def test_argmin():
    corpus = Corpus(
        corpus_name="BREXIT_V20190522",
        registry_path="/home/ausgerechnet/corpora/cwb/registry/",
        lib_path="/home/ausgerechnet/projects/spheroscope/app/instance-stable/lib/",
        s_meta="tweet_id"
    )

    query_path = "/home/ausgerechnet/projects/cwb-ccc/tests/gold/query-example.json"
    with open(query_path, "rt") as f:
        query = json.loads(f.read())
    query_result = corpus.query(query['query'], context=None, s_break='tweet',
                                match_strategy='longest')
    concordance = corpus.concordance(query_result)

    result = concordance.show_argmin(query['anchors'], query['regions'])
    print(result.keys())
    print(result['nr_matches'])
    from pandas import DataFrame
    print(DataFrame(result['matches'][0]['df']))
