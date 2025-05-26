# PlacementGNN: Automated Node Placement Using Graph Neural Networks

This repository implements a workflow for predicting node placement coordinates in VLSI designs using a Graph Neural Network (GNN). It covers data parsing, graph construction, feature engineering, model training with custom loss functions, and final prediction export.

# Data Format

Formatted file (*_formatted.txt): Contains core/die bounds (Die Width, Die Height, Core Width, Core Height, lx, ly, ux, uy), global metrics (Core Aspect Ratio, Utilization, Place Density), and a list of net records. Each record is a Python dict with a driver and list of sinks, each having id, name, is_fixed, is_macro, is_seq and area fields.

Label file (*_label_formatted.txt): Contains ground-truth x_center and y_center for each pin, one line per instance: <instanceName> <x> <y>.

# Methodology

Parsing and Normalization: \
Bounds: Extract lx, ly, ux, uy to define the placement region. \
Global Features: Normalize Core Aspect Ratio, Utilization, and Place Density into [0,1]. \
Labels: Normalize labels using bounds into a [0,1] range, clip and store as targets.

Graph Construction: \
Nodes: Each pin (driver or sink) becomes a graph node, ordered by unique IDs. \
Edges: Directed edges from each driver to its sinks (and reverse if bidirectional). 

Feature Engineering: \
Eigenvectors: Computed the top 10 non-trivial Laplacian eigenvectors of the normalized adjacency matrix, forming the node feature matrix. \
Global Vector Matrix: Appended the 3 global normalized metrics as a per-node feature broadcast via batching.

Loss Functions: \
Absolute Loss: Mean Squared Error between predicted and target normalized coordinates. \
Relative Loss: MSE of pairwise distances (driver & sink) between predictions vs ground truth.

Model Architecture: \
Stacks of graph convolutions (SAGEConv by default; can swap GATv2Conv or GCNConv), each followed by ReLU. \
Global-feature concatenation and MLP readout to predict 2D coordinates per node.

Further Improvements: \
Incorporate ArtNet to generate diverse dataset for the model to train from. \
Append an overlap penalty to further fine-tune the predictions


