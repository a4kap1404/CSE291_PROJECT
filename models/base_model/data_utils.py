import os
import ast
import torch
import random
import numpy as np
from scipy.sparse import csr_matrix
from scipy.sparse.linalg import eigsh
from torch_geometric.data import Data, Batch
from torch_geometric.loader import DataLoader
#from torch.serialization import add_safe_globals
import torch.nn.functional as F
from sklearn.preprocessing import StandardScaler
from datetime import datetime


def parse_formatted(filepath):
    globals_ = {}
    bounds = {}
    with open(filepath, 'r') as f:
        lines = f.read().splitlines()
    f.close()
    for l in lines:
        if '=' in l:
            key, val = l.split('=', 1)
            key = key.strip()
            if key in {'lx', 'ly', 'ux', 'uy'}:
                bounds[key] = float(val.strip())
            else:
                globals_[key] = float(val.strip())
    records = [ast.literal_eval(l) for l in lines if l.strip().startswith('{')]
    drivers = [r['driver']['id'] for r in records]
    sinks = [s['id'] for r in records for s in r['sinks']]
    node_ids = sorted(set(drivers + sinks))
    return node_ids, records, globals_, bounds

def parse_label_formatted(label_path, node_ids, bounds):
    lines = []
    with open(label_path, 'r') as f:
        for row in f:
            parts = row.strip().split()
            if len(parts) == 3 and parts[0].isdigit():
                lines.append((int(parts[0]), float(parts[1]), float(parts[2])))
    f.close()
    ids, xs, ys = zip(*lines)
    xs = np.array(xs)
    ys = np.array(ys)
    lx, ly, ux, uy = bounds['lx'], bounds['ly'], bounds['ux'], bounds['uy']

    x_norm = (xs - lx) / (ux - lx)
    y_norm = (ys - ly) / (uy - ly)

    # clamp if outside lower or upper bound
    x_norm = np.clip(x_norm, 0.0, 1.0)
    y_norm = np.clip(y_norm, 0.0, 1.0)
    # map back to node order
    id2coord = {i: (x_norm[idx], y_norm[idx]) for idx, i in enumerate(ids)}
    coords = [id2coord.get(nid, (0.0, 0.0)) for nid in node_ids]
    return torch.tensor(coords, dtype=torch.float)

# ## Matrix/Feature Generation and Relative Loss
def build_edge_index(node_ids, records, bidirectional=True):
    id2idx = {nid: i for i, nid in enumerate(node_ids)}
    edges = []
    for r in records:
        d = id2idx[r['driver']['id']]
        for s in r['sinks']:
            sid = id2idx[s['id']]
            edges.append((d, sid))
            if bidirectional:
                edges.append((sid, d))
    if not edges:
        return torch.empty((2, 0), dtype=torch.long)
    return torch.tensor(edges, dtype=torch.long).t().contiguous()

def build_adjacency(N, edge_index):
    src, dst = edge_index.cpu().numpy()
    return csr_matrix((np.ones(len(src)), (src, dst)), shape=(N, N))

def fix_signs(eigvecs):
    for i in range(eigvecs.shape[1]):
        if np.abs(eigvecs[:, i]).sum() == 0:
            continue
        if eigvecs[np.argmax(np.abs(eigvecs[:, i])), i] < 0:
            eigvecs[:, i] *= -1
    return eigvecs
        
def compute_laplacian_eigenvectors(adj, k=10, normalized=True):
    N = adj.shape[0]
    k_eff = min(k, max(N-1, 0))
    deg = np.array(adj.sum(axis=1)).flatten()
    if normalized:
        inv_s = np.where(deg > 0, 1.0/np.sqrt(deg), 0.0)
        #inv_s = np.zeros_like(deg)
        #nonzero = deg > 0
        #inv_s[nonzero] = 1.0 / np.sqrt(deg[nonzero])
        D = csr_matrix((inv_s, (range(N), range(N))), shape=adj.shape)
        L = csr_matrix(np.eye(N)) - D @ adj @ D
    else:
        D = csr_matrix((deg, (range(N), range(N))), shape=adj.shape)
        L = D - adj
    if k_eff < 1:
        return np.zeros((N, 0), dtype=np.float32)
    try:
        _, vecs = eigsh(L, k=k_eff+1, which='SM')
    except:
        _, vecs = np.linalg.eigh(L.toarray())
        
    #vecs = fix_signs(vecs)
    #scaler = StandardScaler()
    #vecs_norm = scaler.fit_transform(vecs)

    X = vecs  # shape: [num_nodes, 10]
    X_min = np.min(X, axis=0, keepdims=True)  # shape: (1, 10)
    X_max = np.max(X, axis=0, keepdims=True)
    vecs_norm = (X - X_min) / (X_max - X_min + 1e-6)

    return vecs_norm[:, 1:k_eff+1]

def shuffle_nodes(data: Data) -> Data:
    num_nodes = data.num_nodes
    perm = torch.randperm(num_nodes)

    data.x = data.x[perm]
    data.y = data.y[perm]

    if hasattr(data, "node_ids"):
        data.node_ids = torch.tensor(data.node_ids)[perm].tolist()
    
    inv_perm = torch.empty_like(perm)
    inv_perm[perm] = torch.arange(num_nodes)
    data.edge_index = inv_perm[data.edge_index]

    return data


def load_all_data(root_dir, train_list, test_list, batch_size=16, shuffle=True, device=None):
    """
    Loads DataLoaders for training and testing splits.
    If train_list is empty, train_loader will be None.
    """
    train_data_list = []
    test_data_list  = []

    # Walk through files and assign to train or test lists
    for dp, _, files in os.walk(root_dir):
        for f in files:
            if not f.endswith('_formatted.txt') or f.endswith('_label_formatted.txt'):
                continue
            # derive design name from first two tokens
            parts = f.split('_')
            curr_file = parts[0] + '_' + parts[1] if len(parts) >= 2 else parts[0]

            if curr_file in train_list:
                split = 'train'
            elif curr_file in test_list:
                split = 'test'
            else:
                continue

            # construct paths
            fp = os.path.join(dp, f)
            lf = fp.replace('_formatted.txt', '_label_formatted.txt')
            if not os.path.exists(lf):
                continue

            # parse and build graph
            node_ids, records, globals_, bounds = parse_formatted(fp)
            orig_coords = {rec['driver']['id']:(rec['driver']['x'], rec['driver']['y']) for rec in records}
            for rec in records:
                for s in rec['sinks']:
                    orig_coords[s['id']] = (s['x'], s['y'])
            feats = torch.tensor(
                compute_laplacian_eigenvectors(
                    build_adjacency(len(node_ids), build_edge_index(node_ids, records)), 10
                ), dtype=torch.float
            )
            labels = parse_label_formatted(lf, node_ids, bounds)
            u_vec = torch.tensor([
                (globals_['Core Aspect Ratio'] - 0.5) / 0.4,
                (globals_['Utilization']      - 40.0) / 28.0,
                (globals_['Place Density']    - 0.2) / 0.3,
                (globals_['core_width']     / 1e6),
                (globals_['core_height']    / 1e6),
            ], dtype=torch.float).unsqueeze(0)
            edges = build_edge_index(node_ids, records)

            # fixed IO mask and coords
            fixed_ids = [rec['driver']['id'] for rec in records if rec['driver'].get('is_fixed')]
            fixed_ids += [s['id'] for rec in records for s in rec['sinks'] if s.get('is_fixed')]
            lx, ly, ux, uy = bounds['lx'], bounds['ly'], bounds['ux'], bounds['uy']
            norm_coords = []
            is_io = []
            for nid in node_ids:
                if nid in orig_coords:
                    x, y = orig_coords[nid]
                    x = max(0.0, min(1.0, (x - lx) / (ux - lx)))
                    y = max(0.0, min(1.0, (y - ly) / (uy - ly)))
                else:
                    x, y = -1.0, -1.0
            
                norm_coords.append((x, y))
                is_io.append(1.0 if nid in fixed_ids else 0.0)
            is_io_tensor     = torch.tensor(is_io, dtype=torch.float).unsqueeze(1)
            coords_tensor    = torch.tensor(norm_coords, dtype=torch.float)
            feats = torch.cat([feats, is_io_tensor, coords_tensor], dim=1)

            data = Data(x=feats, edge_index=edges, u=u_vec, y=labels)
            data.design_name = f.replace('_formatted.txt', '')
            data.node_ids    = node_ids
            data.bounds      = bounds
            data.fixed_ids   = fixed_ids

            data = shuffle_nodes(data)
            if device:
                data = data.to(device)

            if split == 'train':
                train_data_list.append(data)
            else:
                test_data_list.append(data)

    # Construct DataLoaders
    if not test_data_list:
        raise RuntimeError("No test graphs found; check your test_list names.")
    test_loader = DataLoader(
        test_data_list,
        batch_size   = batch_size,
        shuffle      = False,
        exclude_keys = ['node_ids','bounds','fixed_ids']
    )

    train_loader = None
    if train_list:
        if not train_data_list:
            raise RuntimeError("No training graphs found; check your train_list names.")
        train_loader = DataLoader(
            train_data_list,
            batch_size   = batch_size,
            shuffle      = shuffle,
            exclude_keys = ['node_ids','bounds','fixed_ids']
        )

    return train_loader, test_loader


def map_nodes_to_coordinates(cluster_file, combined_preds):
    node_to_cluster = {}
    
    with open(cluster_file, 'r') as f:
        for line in f:
            line = line.strip()
            if line:
                cluster_part, nodes_part = line.split(': ')
                cluster_id = int(cluster_part.split()[1])
                nodes_str = nodes_part.strip('[]')
                if nodes_str:
                    nodes = [int(x.strip()) for x in nodes_str.split(',')]
                    for node in nodes:
                        node_to_cluster[node] = cluster_id
    
    cluster_coordinates = {}
    for row in combined_preds:
        cluster_id = int(row[0])
        x_coord = float(row[1])
        y_coord = float(row[2])
        cluster_coordinates[cluster_id] = (x_coord, y_coord)
    
    output_data = []
    for node in sorted(node_to_cluster.keys()):
        cluster_id = node_to_cluster[node]
        if cluster_id in cluster_coordinates:
            x_coord, y_coord = cluster_coordinates[cluster_id]
            output_data.append([node, x_coord, y_coord])
        else:
            print(f"Warning: No coordinates found for cluster {cluster_id}")
    
    return output_data