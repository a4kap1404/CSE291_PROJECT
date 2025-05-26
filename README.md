# PlacementGNN: Automated Node Placement Using Graph Neural Networks

This repository implements a workflow for predicting node placement coordinates in VLSI designs using a Graph Neural Network (GNN). It covers data parsing, graph construction, feature engineering, model training with custom loss functions, and final prediction export.

# Data Format

Formatted file (*_formatted.txt): Contains core/die bounds (Die Width, Die Height, Core Width, Core Height, lx, ly, ux, uy), global metrics (Core Aspect Ratio, Utilization, Place Density), and a list of net records. Each record is a Python dict with a driver and list of sinks, each having id, name, is_fixed, is_macro, is_seq and area fields.

Label file (*_label_formatted.txt): Contains ground-truth x_center and y_center for each pin, one line per instance: &lt;ID&gt; &lt;X&gt; &lt;Y&gt;

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
Stacks of graph convolutions (SAGEConv by default; can swap GATv2Conv or GCNConv) followed by ReLU. \
Global-feature concatenation and MLP readout to predict coordinates per node.


# Instructions to Run the Code
1. Data generation: 

```bash
cd <repo_dir>/new_workspace/flow/
source get_config_floorplan.sh
source get_nets_text.sh  #set mode = 0
source extract_input_features.sh
source get_nets_text.sh #set mode = 1
source get_formatted_labels.sh
```

2. To Train the model: \
Upload the datasets in the form - *_formatted.txt and *_label_formatted.txt and update the path in RUN_PATH. \
To use our dataset, the path is - &lt;repo_dir&gt;/new_workspace/flow/raw_graph/. The script already uses this path. 

3. To run inference: \
The trained code is saved under &lt;repo_dir&gt;/models/base_model/gnn_all.pth. 

# Results 
Validation Results on gcd_nangate45: \
1. 3.9% Reduction in HPWL
2. Number of Nesterov iterations by 60.
3. Total loss calculated was 0.0029.

# Further Improvements
1. Incorporate ArtNet to generate diverse dataset for the model to train from. 
2. Clustering is in progress. Will incorporate the algorithm to see an improvement in placement metrics. 
3. Experiment with overlap and hpwl penalty to further fine-tune the predictions. 
