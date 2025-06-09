# Dataset

This folder covers invocation of openroad, running synth, floorplan and placement upto step 3_2_place_iop, label generation, graph construction and formatting, and finally clustering of nodes using spectral clustering which will be used as our dataset.

# Dataset Composition

The training data includes variations of designs GCD-NanGate45, IBEX-NanGate45, AES-NanGate45, GCD-ASAP7, IBEX-ASAP7, AES-ASAP7, and ARIANE136-NanGate45 with parameters such as Core Utilization, Core Aspect Ratio, and Place Desnity being varied. It also includes 82 synthetic designs generated using Artnet.

The test data includes JPEG-ASAP7, JPEG-NanGate45 and SWERV_WRAPPER-NanGate45.

# Data Format

Formatted file (*_formatted.txt): Contains core/die bounds (Die Width, Die Height, Core Width, Core Height, lx, ly, ux, uy), global metrics (Core Aspect Ratio, Utilization, Place Density), and a list of net records. Each record is a Python dict with a driver and list of sinks, each having id, name, is_fixed, and area fields.

Label file (*_label_formatted.txt): Contains ground-truth x_center and y_center for each pin, one line per instance: &lt;ID&gt; &lt;X&gt; &lt;Y&gt;

# Datset Generation Flow

First set the design variables in 

## Openroad and Label Generation
We have run the orfs_copy command to load ORFS into &lt;repo_dir&gt;/new_workspace/

```bash
cd <repo_dir>/new_workspace/flow/
source get_openroad_run.sh # run placement
source get_get_graph_label.sh # extract graph data and labels
```

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

Set variables in set_variables.sh (do not have to run)
test_mode=1 during test runs.

```bash
cd <repo_dir>/new_workspace/flow/
source get_openroad_run.sh # run placement
source get_get_graph_label.sh # extract graph data and labels
```

2. To Train the model: \
Upload the datasets in the form - *_formatted.txt and *_label_formatted.txt and update the path in RUN_PATH. \
To use our dataset, the path is - &lt;repo_dir&gt;/new_workspace/flow/raw_graph/. The script already uses this path. 

3. To run inference: \
The trained code is saved under &lt;repo_dir&gt;/models/base_model/gnn_all.pth. 

4. To feed predicitons into openroad and evaluate metrics

```bash
cd <repo_dir>/new_workspace/flow/
openroad -python -exit python_complete_loop.py -d gcd -t asap7 -p ./results/asap7/gcd/gcd_run_5_4_1 -f gcd_run_5_4_1 -b 0.2
``` 

# Results 
Validation Results on trained data gcd_nangate45: 
1. 3.9% Reduction in HPWL
2. Number of Nesterov iterations by 60.
3. Total MSE loss calculated was 0.0029.

# Further Improvements
1. Incorporate ArtNet to generate diverse dataset for the model to train from. 
2. Clustering is in progress. Will incorporate the algorithm to see an improvement in placement metrics. 
3. Experiment with overlap and hpwl penalty to further fine-tune the predictions. 
