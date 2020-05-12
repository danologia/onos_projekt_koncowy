from src.settings import RAW_DATA_DIR, PICKLED_JSON_DIR, NODES_DIR, EDGES_DIR
import os
import json
import pickle as pkl
from itertools import combinations
import pandas as pd


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
    available_years = ['2011']
    years_paths = [os.path.join(RAW_DATA_DIR, yr) for yr in available_years]
    years_with_paths = zip(available_years, years_paths)
    years_data = read_years(years_with_paths)
    return years_data


def save_data_dict(data_dict):
    with open(PICKLED_JSON_DIR, "wb+") as f:
        pkl.dump(data_dict, f, protocol=pkl.HIGHEST_PROTOCOL)


def load_data_dict():
    with open(PICKLED_JSON_DIR, "rb") as f:
        return pkl.load(f)


def parse_graph(data):
    nodes = {}
    edges = {}
    for year, year_publications in data.items():
        for publication in year_publications:
            authors = publication['authors']

            def get_id(link: str) -> str:
                return link.rsplit('=', maxsplit=1)[1]

            node_data = {
                get_id(author['link']): (author['name'], author['link'])
                for author in authors
            }
            nodes.update(node_data)

            id_pairs = combinations(node_data.keys(), 2)
            edge_data = [tuple(sorted(pair)) for pair in id_pairs]
            for id_pair in edge_data:
                if id_pair not in edges:
                    edges[id_pair] = 0
                edges[id_pair] += 1
    nodes_flat = [[id, name, link] for id, (name, link) in nodes.items()]
    edges_flat = [[frm, to, weight] for (frm, to), weight in edges.items()]
    return nodes_flat, edges_flat


def save_graph_data(nodes, edges):
    nodes_pd = pd.DataFrame(nodes, columns=['id', 'label', 'link'])
    nodes_pd.to_csv(NODES_DIR, index=False)
    edges_pd = pd.DataFrame(edges, columns=['source', 'target', 'weight'])
    edges_pd.to_csv(EDGES_DIR, index=False)


if __name__ == '__main__':
    data = load_data_dict()
    nodes, edges = parse_graph(data)
    save_graph_data(nodes, edges)