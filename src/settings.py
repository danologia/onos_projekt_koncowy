import os

PROJECT_DIR = os.path.normpath(os.path.join(os.path.dirname(__file__), ".."))

DATA_DIR = os.path.join(PROJECT_DIR, 'data')
RAW_DATA_DIR = os.path.join(DATA_DIR, 'raw')
AUTHORS_DIR = os.path.join(RAW_DATA_DIR, 'authors')
PROCESSED_DATA_DIR = os.path.join(DATA_DIR, 'processed')
DEFAULT_NODES_DIR = os.path.join(PROCESSED_DATA_DIR, 'nodes.csv')
DEFAULT_EDGES_DIR = os.path.join(PROCESSED_DATA_DIR, 'edges.csv')
RESULT_DIR = os.path.join(PROJECT_DIR, 'results')


def get_dir_with_year(dir, year):
    return f"_{str(year)}.".join(dir.rsplit('.', maxsplit=1))


def get_nodes_and_edges_dir(year):
    return get_dir_with_year(DEFAULT_NODES_DIR, year), get_dir_with_year(DEFAULT_EDGES_DIR, year)

try:
    from src.user_settings import *
except ImportError:
    pass
