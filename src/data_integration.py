from src.settings import RAW_DATA_DIR, DEFAULT_NODES_DIR, DEFAULT_EDGES_DIR, get_nodes_and_edges_dir, PROCESSED_DATA_DIR
import os
import json
from itertools import combinations, product
import pandas as pd
import sys
import matplotlib.pyplot as plt


def read_years(years_with_paths):
    publications_yearly = {}
    for year, year_path in years_with_paths:
        data_files_names = os.listdir(year_path)
        data_files_paths = [os.path.join(year_path, data_file) for data_file in data_files_names]
        year_publications = []
        for path in data_files_paths:
            with open(path, "rt") as f:
                file_publications = json.load(f)
                year_publications.extend(file_publications)
        publications_yearly[year] = year_publications
    return publications_yearly


def read_raw_data():
    available_years = [d for d in os.listdir(RAW_DATA_DIR) if os.path.isdir(os.path.join(RAW_DATA_DIR, d))
                       and d != 'authors']
    years_paths = [os.path.join(RAW_DATA_DIR, yr) for yr in available_years]
    years_with_paths = zip(available_years, years_paths)
    years_data = read_years(years_with_paths)
    return years_data


def parse_graph(data, starting_year=None):
    nodes = {}
    edges = {}
    if starting_year is None:
        starting_year = min([int(yr) for yr in data.keys()])
    for year, year_publications in data.items():
        if int(year) >= starting_year:
            for publication in year_publications:
                authors = publication['authors']

                def get_id(link: str) -> str:
                    return link.rsplit('=', maxsplit=1)[1]

                node_data = {
                    get_id(author['link']): author['name']
                    for author in authors
                }
                nodes.update(node_data)

                id_pairs = combinations(node_data.keys(), 2)
                edge_data = [tuple(sorted(pair)) for pair in id_pairs]
                for id_pair in edge_data:
                    if id_pair not in edges:
                        edges[id_pair] = 0
                    edges[id_pair] += 1
    nodes_flat = [[id, name] for id, name in nodes.items()]
    edges_flat = [[frm, to, weight] for (frm, to), weight in edges.items()]
    return nodes_flat, edges_flat


def save_graph_data(nodes, edges, starting_year=None):
    if starting_year is not None:
        nodes_dir, edges_dir = get_nodes_and_edges_dir(starting_year)
    else:
        nodes_dir, edges_dir = DEFAULT_NODES_DIR, DEFAULT_EDGES_DIR
    nodes_pd = pd.DataFrame(nodes, columns=['id', 'label'])
    nodes_pd.to_csv(nodes_dir, index=False)
    edges_pd = pd.DataFrame(edges, columns=['source', 'target', 'weight'])
    edges_pd.to_csv(edges_dir, index=False)


def plot_authors_and_collaborations_numbers_by_years():
    starting_years = range(2000, 2021, 1)
    authors_counts = []
    collaborations_counts = []
    for year in starting_years:
        nodes_dir, edges_dir = get_nodes_and_edges_dir(year)
        with open(nodes_dir) as f:
            for i, _ in enumerate(f):
                pass
        authors_counts.append(i - 1)
        with open(edges_dir) as f:
            for i, _ in enumerate(f):
                pass
        collaborations_counts.append(i - 1)
    plt.scatter(starting_years, authors_counts)
    plt.xticks(starting_years, rotation=45)
    plt.xlabel("Początkowy rok")
    plt.ylabel("Liczba autorów")
    plt.title("Liczba unikalnych autorów w bazie")
    plt.show()
    plt.scatter(starting_years, collaborations_counts)
    plt.xticks(starting_years, rotation=45)
    plt.xlabel("Początkowy rok")
    plt.title("Liczba unikalnych kolaboracji w bazie")
    plt.ylabel("Liczba kolaboracji")
    plt.show()


def add_data_to_nodes(nodes_file_path):
    nodes = pd.read_csv(nodes_file_path, dtype=object)
    authors = []
    ids = nodes['id'].to_list()
    for id in ids:
        with open(os.path.join(RAW_DATA_DIR, 'authors', str(id) + '.json'), 'r') as f:
            auth = json.load(f)
            authors.append(auth)
    df = pd.DataFrame(authors)
    df2 = pd.merge(nodes, df, on='id').drop('name', axis=1)
    df2 = df2.replace({
        'disciplines': {
            'Nieznane': '[]'
        },
        'publications': {
            'Nieznane': 0
        },
        'citations': {
            'Nieznane': 0
        },
        'impact_factor': {
            'Nieznane': 0
        },
        'supervisorships': {
            'Nieznane': 0
        },
    })

    new_path = "_with_authors.".join(nodes_file_path.rsplit('.', maxsplit=1))
    df2.to_csv(new_path, index=False)
    print(df2.head())


def read_departments_data(nodes_file_path):
    nodes = pd.read_csv(nodes_file_path, dtype=object)
    authors_mapping = dict(zip(nodes['id'], nodes['department']))
    unique_departments = list(set(authors_mapping.values()))
    return authors_mapping, unique_departments


def flatten_edges_file_by_deps_collaborations(department_mapping, unique_departments, edges_file_path):
    def merge(dict, pair, weight):
        dict[pair] += int(weight)
    return flatten_edges_file_by_departments(department_mapping, unique_departments, edges_file_path,
                                             lambda dict, pair, weight: merge(dict, pair, weight))


def flatten_edges_file_by_deps_number(department_mapping, unique_departments, edges_file_path):
    def merge(dict, pair, _):
        dict[pair] += 1
    return flatten_edges_file_by_departments(department_mapping, unique_departments, edges_file_path,
                                             lambda dict, pair, weight: merge(dict, pair, weight))


def flatten_edges_file_by_departments(department_mapping, unique_departments, edges_file_path, merging_fun):
    edges = pd.read_csv(edges_file_path, dtype=object)

    unique_departments.remove('Nieznane')
    department_pairs = product(unique_departments, repeat=2)
    sorted_pairs = sorted([tuple(sorted(pair)) for pair in department_pairs])

    result_nodes = pd.DataFrame({
        'id': unique_departments,
        'label': unique_departments
    })

    result_edges = {
        pair: 0
        for pair in sorted_pairs
    }

    for _, (source, target, weight) in edges.iterrows():
        source_dep = department_mapping[source]
        target_dep = department_mapping[target]
        if source_dep != 'Nieznane' and target_dep != 'Nieznane':
            pair = tuple(sorted((source_dep, target_dep)))
            merging_fun(result_edges, pair, weight)

    sources, targets = zip(*result_edges.keys())
    sources = list(sources)
    targets = list(targets)
    values = list(result_edges.values())
    result_edges = pd.DataFrame({
        'source': sources,
        'target': targets,
        'weight': values
    })
    return result_nodes, result_edges


def flatten_by_departments(type, year):
    if type == 'works':
        fn = flatten_edges_file_by_deps_number
    elif type == 'colabs':
        fn = flatten_edges_file_by_deps_collaborations

    mapping, departments = read_departments_data(os.path.join(PROCESSED_DATA_DIR, f"nodes_{year}_with_authors.csv"))
    nodes, edges = fn(mapping, departments,
                                                         os.path.join(PROCESSED_DATA_DIR, f"edges_{year}.csv"))
    nodes.to_csv(os.path.join(PROCESSED_DATA_DIR, f"nodes_{year}_deps_{type}.csv"), index=False)
    edges.to_csv(os.path.join(PROCESSED_DATA_DIR, f"edges_{year}_deps_{type}.csv"), index=False)


if __name__ == '__main__':
    pd.set_option('display.max_rows', None)
    pd.set_option('display.max_columns', None)
    pd.set_option('display.width', None)
    pd.set_option('display.max_colwidth', -1)
    flatten_by_departments('works', 2015)
    # add_data_to_nodes(os.path.join(PROCESSED_DATA_DIR, "nodes_2015.csv"))
    # plot_authors_and_collaborations_numbers_by_years()
    # # starting_years = range(2000, 2021, 1)
    # # data = read_raw_data()
    # # for year in starting_years:
    # #     nodes, edges = parse_graph(data, year)
    # #     save_graph_data(nodes, edges, year)
    #
    # starting_year = None
    # if len(sys.argv) > 0:
    #     try:
    #         starting_year = int(sys.argv[0])
    #     except ValueError:
    #         pass
    # data = read_raw_data()
    # nodes, edges = parse_graph(data)
    # save_graph_data(nodes, edges)