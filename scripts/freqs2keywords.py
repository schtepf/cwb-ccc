from pandas import read_csv, to_numeric
# from pandas import concat
from association_measures import measures, frequencies
from argparse import ArgumentParser
from numpy import log2


def logratio(row):
    C1 = row['O11'] + row['O21']
    C2 = row['O12'] + row['O22']
    ratio = row['O11'] / C1 / (row['O12'] / C2)
    return round(log2(ratio), 2)


def calculate_keywords(df1, df2, C1, C2, lonely=True, how='first'):

    if how == 'second':
        return calculate_keywords(df2, df1, lonely=lonely, how='first')

    # only in one list
    if lonely:
        items1 = set(df1.index)
        items2 = set(df2.index)

        only1 = df1.loc[items1 - items2]
        only1['ppm'] = round(only1['O11'] / C1 * 1000000, 2)

        # only2 = df2.loc[items2 - items1]
        # only2['ppm'] = round(only2['O12'] / C2 * 1000000, 2)

        # df_only = concat([only1, only2])
        # df_only.fillna(0, inplace=True)
        # df_only['diff'] = df_only['O11'] - df_only['O12']
        # df_only.sort_values(by=['diff', 'item'], ascending=False, inplace=True)

        df_only = only1
        df_only['freq_1'] = to_numeric(df_only['O11'], downcast='integer')
        # df_only['freq_2'] = to_numeric(df_only['O12'], downcast='integer')
        # df_only = df_only[['freq_1', 'ppm', 'freq_2', 'item']]

        # reset index and sort by frequency
        df_only.index.name = 'item'
        df_only = df_only.reset_index()
        df_only = df_only.sort_values(by=['freq_1', 'item'], ascending=False)

        # use index for ranking
        df_only = df_only.reset_index()
        df_only.index.name = 'rank'
        df_only.index = df_only.index + 1

        # reduce to relevant columns
        df_only = df_only[['item', 'freq_1', 'ppm']]

    else:
        df_only = None

    # join dataframes
    df = df1.join(df2, how='inner')
    df.fillna(0, inplace=True)

    df["O21"] = C1 - df["O11"]
    df["O22"] = C2 - df["O12"]

    # some more names
    df["f1"] = df["O11"] + df["O12"]  # overall counts of word
    df["f2"] = df["O11"] + df["O21"]  # size of corpus 1
    df["N"] = C1 + C2

    df = df.join(frequencies.expected_frequencies(df))

    # ppm and comparision
    df['ppm_1'] = round(df['O11'] / C1 * 1000000, 2)
    df['ppm_1_e'] = round(df['E11'] / C1 * 1000000, 2)
    df['ppm_2'] = round(df['O12'] / C2 * 1000000, 2)
    df['ppm_2_e'] = round(df['E12'] / C2 * 1000000, 2)

    # calculate association measures
    df = df.join(measures.calculate_measures(df))
    df['log_likelihood'] = round(df['log_likelihood'], 2)
    df['log_ratio'] = df.apply(logratio, axis=1)
    df.index.name = 'item'

    return df, df_only


def main(args, complete=False):

    print('reading 1st list ...', end="\r")
    df1 = read_csv(args.path1, sep="\t", header=None, quoting=3,
                   keep_default_na=False)
    print('reading 1st list ... %d items' % df1.shape[0])
    print('reading 2nd list ...', end="\r")
    df2 = read_csv(args.path2, sep="\t", header=None, quoting=3,
                   keep_default_na=False)
    print('reading 2nd list ... %d items' % df2.shape[0])

    # get corpus sizes
    C1 = df1[0].sum()
    C2 = df2[0].sum()

    # drop hapax legomena
    if args.cut_off is not None:
        print('dropping hapax legomena ...', end="\r")
        df2 = df2.loc[df2[0] >= args.cut_off]
        print('dropping hapax legomena ... %d items' % df2.shape[0])

    print('combining relevant columns')
    if len(args.col) == 0:
        col1 = list(df1.columns[1:])
        col2 = list(df2.columns[1:])
    else:
        col1 = col2 = args.col

    df1['INDEX'] = df1[col1].agg(' '.join, axis=1)
    df1 = df1.drop(col1, axis=1)
    df1 = df1.set_index('INDEX')
    df1.index.name = 'item'
    df1.columns = ['O11']

    df2['INDEX'] = df2[col2].agg(' '.join, axis=1)
    df2 = df2.drop(col2, axis=1)
    df2 = df2.set_index('INDEX')
    df2.index.name = 'item'
    df2.columns = ['O12']

    print('calculating keyness')
    df, df_only = calculate_keywords(df1, df2, C1, C2, lonely=args.lonely)

    # re-formatting dataframe
    df.sort_values(
        by=[args.order, 'item'],
        ascending=False, inplace=True
    )
    df = df.reset_index()
    all_columns = set(df.columns)
    important = ['item', args.order, 'O11', 'ppm_1', 'O12', 'ppm_2']
    if args.order != 'log_likelihood':
        important = important + ['log_likelihood']
    if complete:
        important = important + list(all_columns - set(important))
    df = df[important]
    df.index.name = 'rank'
    df.index = df.index + 1

    print('writing results')
    df.to_csv(args.path_out + ".tsv.gz", sep="\t", compression="gzip")
    df.iloc[:50000].to_excel(args.path_out + ".xls")

    if df_only is not None:
        df_only.to_csv(args.path_out + ".lonely.tsv.gz", sep="\t", compression="gzip")
        df_only.iloc[:50000].to_excel(args.path_out + ".lonely.xls")


if __name__ == '__main__':

    parser = ArgumentParser()
    parser.add_argument("path1",
                        type=str,
                        help="first frequency list")
    parser.add_argument("path2",
                        type=str,
                        help="second frequency list")
    parser.add_argument("path_out",
                        type=str,
                        help="prefix to save result to")
    parser.add_argument("-l",
                        "--lonely",
                        dest='lonely',
                        action='store_false',
                        help="do *not* determine items that only appear in one list",
                        default=True)
    parser.add_argument("-c",
                        "--col",
                        dest='col',
                        type=list,
                        nargs='+',
                        default=list(),
                        help="list of 0-based columns to form items [1:]")
    parser.add_argument("--cut_off",
                        type=int,
                        default=2,
                        help="minimum frequency for second list [2]")
    parser.add_argument("-o",
                        "--order",
                        type=str,
                        default="log_ratio",
                        help="what AM to use for ordering [log_ratio]")
    args = parser.parse_args()

    main(args)
