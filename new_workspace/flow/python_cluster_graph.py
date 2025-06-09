import os
import argparse
import random
import ast
import numpy as np
import scipy.sparse as sp
from scipy.sparse.linalg import eigsh
from sklearn.cluster import KMeans
from typing import Dict, List, Set, Tuple, Any
from collections import defaultdict


class HypergraphClustering:
    def __init__(self, hyperedges, node_features=None, num_nodes=None):

        self.hyperedges = hyperedges
        self.node_features = node_features or {}

        all_nodes = set()
        for edge in hyperedges:
            all_nodes.update(edge)
        self.all_nodes = sorted(list(all_nodes))
        self.node_to_idx = {node: idx for idx, node in enumerate(self.all_nodes)}
        self.idx_to_node = {idx: node for node, idx in self.node_to_idx.items()}

        if num_nodes is None:
            self.num_nodes = len(self.all_nodes)
        else:
            self.num_nodes = num_nodes

        self.hyperedges_zero_indexed = [[self.node_to_idx[node] for node in edge] for edge in hyperedges]

        self.clusters = None
        self.original_clusters = None
        self.cluster_hypergraph = None
        self.cluster_adj_matrix = None
        self.fixed_nodes = set()
        self.cluster_to_nodes = {}
        self.node_to_cluster = {}

    def construct_incidence_matrix(self):
        rows = []
        cols = []
        data = []

        for e_idx, edge in enumerate(self.hyperedges_zero_indexed):
            for node in edge:
                rows.append(node)
                cols.append(e_idx)
                data.append(1)

        H = sp.csr_matrix((data, (rows, cols)),
                          shape=(self.num_nodes, len(self.hyperedges)))
        return H

    def construct_laplacian(self):
        H = self.construct_incidence_matrix()
        D_v = np.array(H.sum(axis=1)).flatten()
        D_v_sqrt_inv_values = np.zeros_like(D_v, dtype=float)
        nonzero_indices = D_v > 0
        D_v_sqrt_inv_values[nonzero_indices] = 1.0 / np.sqrt(D_v[nonzero_indices])
        D_v_sqrt_inv = sp.diags(D_v_sqrt_inv_values)

        D_e = np.array(H.sum(axis=0)).flatten()

        D_e_inv_values = np.zeros_like(D_e, dtype=float)
        nonzero_indices = D_e > 0
        D_e_inv_values[nonzero_indices] = 1.0 / D_e[nonzero_indices]
        D_e_inv = sp.diags(D_e_inv_values)

        W = sp.eye(len(self.hyperedges))

        HT = H.transpose()
        temp = H.dot(W).dot(D_e_inv).dot(HT)
        normalized_laplacian = sp.eye(self.num_nodes) - D_v_sqrt_inv.dot(temp).dot(D_v_sqrt_inv)

        return normalized_laplacian

    def spectral_clustering(self, n_clusters):
        L = self.construct_laplacian()
        eigvals, eigvecs = eigsh(L, k=min(n_clusters+1, self.num_nodes-1), which='SM')

        idx = eigvals.argsort()
        eigvals = eigvals[idx]
        eigvecs = eigvecs[:, idx]
        features = eigvecs[:, 1:min(n_clusters+1, eigvecs.shape[1])]

        actual_n_clusters = min(n_clusters, features.shape[1])
        #kmeans = KMeans(n_clusters=actual_n_clusters, random_state=42, n_init=10)
        kmeans = KMeans(n_clusters=actual_n_clusters, n_init=10)
        clusters = kmeans.fit_predict(features)

        self.original_clusters = clusters.copy()
        self.clusters = self._process_fixed_nodes(clusters)

        return self.clusters

    def _identify_fixed_nodes(self):
        fixed_nodes = set()

        for node_name, features in self.node_features.items():
            if len(features) >= 3 and features[2] == 1:
                fixed_nodes.add(node_name)

        self.fixed_nodes = fixed_nodes
        return fixed_nodes

    def _process_fixed_nodes(self, original_clusters):
        fixed_nodes = self._identify_fixed_nodes()
        fixed_node_indices = set(self.node_to_idx[node] for node in fixed_nodes if node in self.node_to_idx)

        cluster_groups = defaultdict(list)
        for node_idx, cluster_id in enumerate(original_clusters):
            if node_idx not in fixed_node_indices:
                cluster_groups[cluster_id].append(node_idx)

        new_clusters = np.zeros_like(original_clusters)
        cluster_id = 0

        for original_cluster_id, node_indices in cluster_groups.items():
            if node_indices:
                for node_idx in node_indices:
                    new_clusters[node_idx] = cluster_id
                cluster_id += 1

        for node_idx in fixed_node_indices:
            new_clusters[node_idx] = cluster_id
            cluster_id += 1

        self._update_cluster_mappings(new_clusters)

        return new_clusters

    def _update_cluster_mappings(self, clusters):
        self.cluster_to_nodes = defaultdict(list)
        self.node_to_cluster = {}

        for node_idx, cluster_id in enumerate(clusters):
            node_name = self.idx_to_node[node_idx]
            self.cluster_to_nodes[cluster_id].append(node_name)
            self.node_to_cluster[node_name] = cluster_id

    def evaluate_clustering(self):
        inter_cluster_edges = 0
        cut_edges = 0

        for edge in self.hyperedges_zero_indexed:
            edge_clusters = set(self.clusters[node] for node in edge)

            if len(edge_clusters) > 1:
                cut_edges += 1

            for i, node1 in enumerate(edge):
                for node2 in edge[i+1:]:
                    if self.clusters[node1] != self.clusters[node2]:
                        inter_cluster_edges += 1
                        break

        metrics = {
            "cut_hyperedges": cut_edges,
            "total_hyperedges": len(self.hyperedges),
            "cut_ratio": cut_edges / len(self.hyperedges) if len(self.hyperedges) > 0 else 0,
            "inter_cluster_connections": inter_cluster_edges,
            "num_clusters": len(np.unique(self.clusters)),
            "num_fixed_nodes": len(self.fixed_nodes)
        }

        return metrics

    def construct_cluster_hypergraph(self):
        n_clusters = len(np.unique(self.clusters))
        cluster_hypergraph = []

        cluster_adj_matrix = np.zeros((n_clusters, n_clusters))

        for edge in self.hyperedges_zero_indexed:
            clusters_in_edge = list(set(self.clusters[node] for node in edge))

            if len(clusters_in_edge) > 1:
                clusters_in_edge.sort()
                cluster_hypergraph.append(clusters_in_edge)

                for i, c1 in enumerate(clusters_in_edge):
                    for c2 in clusters_in_edge[i+1:]:
                        cluster_adj_matrix[c1, c2] += 1
                        cluster_adj_matrix[c2, c1] += 1

        unique_cluster_hypergraph = []
        seen = set()
        for edge in cluster_hypergraph:
            edge_tuple = tuple(edge)
            if edge_tuple not in seen:
                seen.add(edge_tuple)
                unique_cluster_hypergraph.append(edge)

        self.cluster_hypergraph = unique_cluster_hypergraph
        self.cluster_adj_matrix = cluster_adj_matrix

        return unique_cluster_hypergraph, cluster_adj_matrix

    def _calculate_cluster_coordinates(self):
        cluster_coords = {}

        for cluster_id in np.unique(self.clusters):
            cluster_nodes = [self.idx_to_node[i] for i in range(self.num_nodes) if self.clusters[i] == cluster_id]

            if cluster_nodes:
                x_coords = []
                y_coords = []

                for node in cluster_nodes:
                    if node in self.node_features:
                        x_coords.append(self.node_features[node][0])  # x
                        y_coords.append(self.node_features[node][1])  # y

                if x_coords and y_coords:
                    avg_x = sum(x_coords) / len(x_coords)
                    avg_y = sum(y_coords) / len(y_coords)
                    cluster_coords[cluster_id] = (avg_x, avg_y)
                else:
                    cluster_coords[cluster_id] = (0.0, 0.0)

        return cluster_coords

    def _create_cluster_hyperedges(self):
        cluster_hyperedges = []

        for original_edge in self.hyperedges:
            clusters_in_edge = []
            for node in original_edge:
                if node in self.node_to_cluster:
                    clusters_in_edge.append(self.node_to_cluster[node])

            unique_clusters = []
            seen = set()
            for cluster in clusters_in_edge:
                if cluster not in seen:
                    unique_clusters.append(cluster)
                    seen.add(cluster)

            if len(unique_clusters) > 1:
                driver_cluster = unique_clusters[0]
                sink_clusters = unique_clusters[1:]

                cluster_hyperedges.append({
                    'driver': driver_cluster,
                    'sinks': sink_clusters
                })

        return cluster_hyperedges

    def write_cluster_formats(self, format1_filename='cluster_hyperedges.txt', format2_filename='cluster_coordinates.txt'):
        if self.clusters is None:
            print("Error: Clustering must be performed before writing cluster formats")
            return

        cluster_coords = self._calculate_cluster_coordinates()

        cluster_hyperedges = self._create_cluster_hyperedges()

        with open(format1_filename, 'a') as f:
            for i, edge in enumerate(cluster_hyperedges, 1):
                driver_cluster = edge['driver']
                sink_clusters = edge['sinks']

                driver_coords = cluster_coords.get(driver_cluster, (0.0, 0.0))

                driver_info = {
                    'driver': {
                        'id': int(driver_cluster),
                        'name': f'cluster_{driver_cluster}',
                        'x': int(driver_coords[0]),
                        'y': int(driver_coords[1]),
                        'is_fixed': driver_cluster in [self.node_to_cluster.get(node, -1) for node in self.fixed_nodes],
                        'area': len(self.cluster_to_nodes[driver_cluster]) * 1000 
                    },
                    'sinks': []
                }

                for sink_cluster in sink_clusters:
                    sink_coords = cluster_coords.get(sink_cluster, (0.0, 0.0))
                    sink_info = {
                        'id': int(sink_cluster),
                        'name': f'cluster_{sink_cluster}',
                        'x': int(sink_coords[0]),
                        'y': int(sink_coords[1]),
                        'is_fixed': sink_cluster in [self.node_to_cluster.get(node, -1) for node in self.fixed_nodes],
                        'area': len(self.cluster_to_nodes[sink_cluster]) * 1000 
                    }
                    driver_info['sinks'].append(sink_info)

                f.write(str(driver_info) + '\n')

        with open(format2_filename, 'w') as f:
            for cluster_id in sorted(cluster_coords.keys()):
                coords = cluster_coords[cluster_id]
                f.write(f"{cluster_id} {int(coords[0])} {int(coords[1])}\n")

        print(f"Cluster information written to:")
        print(f"  Format 1 (hyperedges): {format1_filename}")
        print(f"  Format 2 (coordinates): {format2_filename}")
        print(f"  Total cluster hyperedges: {len(cluster_hyperedges)}")
        print(f"  Total clusters: {len(cluster_coords)}")

    def print_cluster_information(self, format3_filename='cluster_mapping.txt'):

        print("\nCluster Assignments (After Fixed Node Processing):")
        unique_clusters = np.unique(self.clusters)

        with open(format3_filename, 'w') as f:
            for cluster_id in unique_clusters:
                nodes = [self.idx_to_node[i] for i in range(self.num_nodes) if self.clusters[i] == cluster_id]
                fixed_in_cluster = [n for n in nodes if n in self.fixed_nodes]
                regular_in_cluster = [n for n in nodes if n not in self.fixed_nodes]

                
                cluster_info = f"Cluster {cluster_id}: "
                if fixed_in_cluster:
                    cluster_info += f"{fixed_in_cluster}"
                if regular_in_cluster:
                    cluster_info += f"{regular_in_cluster[:]}"
                    cluster_info += ""

                print(cluster_info)
                f.write(f"{cluster_info}\n")

        metrics = self.evaluate_clustering()
        print("\nClustering Metrics:")
        print(f"Total Clusters: {metrics['num_clusters']}")
        print(f"Fixed Nodes (Individual Clusters): {metrics['num_fixed_nodes']}")
        print(f"Cut Hyperedges: {metrics['cut_hyperedges']} / {metrics['total_hyperedges']} " +
              f"({metrics['cut_ratio']:.2%})")
        print(f"Inter-cluster Connections: {metrics['inter_cluster_connections']}")

        if self.cluster_hypergraph is not None:
            print(f"\nCluster-level Hypergraph: {len(self.cluster_hypergraph)} hyperedges")
            for i, edge in enumerate(self.cluster_hypergraph[:]):
                print(f"Hyperedge {i+1}: {edge}")

            print(f"\nCluster-level Adjacency Matrix ({len(self.cluster_adj_matrix)}x{len(self.cluster_adj_matrix[0])}):")
            print(self.cluster_adj_matrix)

def process(input_file, output_file_path):
    graph_features = []
    node_features = {}
    hyperedges = []

    f_wr = open(f"{output_file_path}_formatted.txt", "w")

    with open(input_file, 'r') as f:
        for line in f:
            #net = ast.literal_eval(line.strip())
            line = line.strip()
            if line.startswith('{'):
                net = ast.literal_eval(line)
                graph_features.append(net)
            else:
                f_wr.write(f"{line}\n")
                continue

    f_wr.close()

    for node in graph_features:
        edge_nodes = []
        driver = node['driver']
        name = driver['id']
        x = float(driver['x'])
        y = float(driver['y'])
        is_fixed = int(driver['is_fixed'])
        area = float(driver['area'])

        node_features[name] = [x, y, is_fixed, area]
        edge_nodes.append(name)

        for sink in node['sinks']:
            name = sink['id']
            x = float(sink['x'])
            y = float(sink['y'])
            is_fixed = int(sink['is_fixed'])
            area = float(sink['area'])

            node_features[name] = [x, y, is_fixed, area]
            edge_nodes.append(name)

        if edge_nodes not in hyperedges:
            hyperedges.append(edge_nodes)

    print(f"Loaded {len(hyperedges)} hyperedges with {len(node_features)} nodes")
    print(f"Fixed nodes: {[node for node, features in node_features.items() if features[2] == 1]}")

    hgc = HypergraphClustering(hyperedges, node_features)

    #n_clusters = 300
    n_clusters = random.randint(300, 500)
    print(f"\nPerforming spectral clustering with {n_clusters} clusters...")

    clusters = hgc.spectral_clustering(n_clusters=n_clusters)
    cluster_hypergraph, cluster_adj_matrix = hgc.construct_cluster_hypergraph()

    hgc.print_cluster_information(f"{output_file_path}_mapping.txt")

    print("\nWriting cluster information to files...")
    hgc.write_cluster_formats(f"{output_file_path}_formatted.txt", f"{output_file_path}_label_formatted.txt")


if __name__ == "__main__":
    # You can run this script in this manner:  openroad -python python_read_design.py
    parser = argparse.ArgumentParser(description="Example script to perform global placement initialization using OpenROAD.")
    parser.add_argument("-d", default="ibex", help="Give the design name")
    parser.add_argument("-t", default="nangate45", help="Give the technology node")
    parser.add_argument("-p", default="nangate45", help="Give the result_path")
    parser.add_argument("-f", default="nangate45", help="Give the flow variant")
    parser.add_argument("-m", default="0", help="Give the mode (testing = 1)")

    args = parser.parse_args()

    tech_node = args.t
    design = args.d
    path = args.p
    flow = args.f
    test = args.m

    if test == "1":
        input_file = "./raw_graph/" + str(design) + "_" + str(tech_node) + "_" + str(flow) + "_formatted.txt"
    else:
        input_file = "./raw_graph_output/" + str(design) + "_" + str(tech_node) + "_" + str(flow) + "_output.txt"

    output_file_path = "./raw_graph_test/" + str(design) + "_" + str(tech_node) + "_" + str(flow)
    #output_file_path = "./raw_graph_clustered/" + str(design) + "_" + str(tech_node) + "_" + str(flow)
    os.makedirs(os.path.dirname(output_file_path), exist_ok=True)

    process(input_file, output_file_path)
