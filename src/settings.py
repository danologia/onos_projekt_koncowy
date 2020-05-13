import os

PROJECT_DIR = os.path.normpath(os.path.join(os.path.dirname(__file__), ".."))

DATA_DIR = os.path.join(PROJECT_DIR, 'data')
RAW_DATA_DIR = os.path.join(DATA_DIR, 'raw')
PROCESSED_DATA_DIR = os.path.join(DATA_DIR, 'processed')
NODES_DIR = os.path.join(PROCESSED_DATA_DIR, 'nodes.csv')
EDGES_DIR = os.path.join(PROCESSED_DATA_DIR, 'edges.csv')
RESULT_DIR = os.path.join(PROJECT_DIR, 'results')

try:
    from src.user_settings import *
except ImportError:
    pass
