# PlacementGNN: Automated Node Placement Using Graph Neural Networks

This repository implements a workflow for predicting node placement coordinates in VLSI designs using a Graph Neural Network (GNN). It covers data parsing, graph construction, feature engineering, model training with custom loss functions, and final prediction export.

For best reproducibility, clone the repositry into a docker container with openroad already built, preferably the ECE260C container.

# Data Format

Formatted file (*_formatted.txt): Contains core/die bounds (Die Width, Die Height, Core Width, Core Height, lx, ly, ux, uy), global metrics (Core Aspect Ratio, Utilization, Place Density), and a list of net records. Each record is a Python dict with a driver and list of sinks, each having id, name, is_fixed, is_macro, is_seq and area fields.

Label file (*_label_formatted.txt): Contains ground-truth x_center and y_center for each pin, one line per instance.

Mapping file (*_mapping.txt): This has the cluster to node mapping, preserving the information of the nodes present in each cluster. 

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
Fixed-Pin Anchors: Append a binary is_fixed flag plus the normalized (x,y) coordinates of fixed pins, so the network has spatial anchor points. \
Global Vector Matrix: Concatenate the shared, normalized global metrics (AR, Util, Density) onto each node’s feature vector via broadcasting in the data batch.

Loss Functions: 
1. Absolute Loss: Mean Squared Error between predicted and target normalized coordinates. 
2. Relative Loss: MSE between predicted and true pairwise distances along each hyperedge — encourages correct spacing.  
3. Density Penalty: Soft binning of (x,y) predictions into grid cells, penalizing bins that exceed a target density threshold. 
4. HPWL: Sum of max-min x and y spans per net; can be added to loss to reduce wiring cost. 
5. Overlap Loss: Penalizes predicted nodes that fall too close (less than min spacing) to each other.

Note: We omitted absolute coordinate MSE during final training because it dominated gradients and reduced generalization.

Model Architecture: \
Stacks of graph convolutions (SAGEConv by default; can swap GATv2Conv or GCNConv) followed by ReLU. \
Global-feature concatenation and MLP readout to predict coordinates per node.


# Instructions to Run the Code
1. Data generation: 
The generated dataset is present in new_workspace/flow/raw_graph/.  The dataset includes designs such as: gcd_nangate45, ibex_nangate45, aes_nangate45, gcd_asap7, ibex_asap7, aes_asap7, ariane136_nangate45.\
Detailed information regarding new data generation and existing dataset is present in new_workspace/flow/.

2. To Train the model:
Details on running train.py are given in base_model/.
Launch training in one command:
```bash
python train.py \
  --data-dir      /new_workspace/flow/raw_graph_clustered \
  --train-designs gcd_nangate45 ibex_asap7 aes_asap7 \
  --test-designs  gcd_asap7 \
  --batch-size    4 \
  --epochs        150 \
  --lr            2e-4 \
  --weight-decay  1e-4
``` 
The script reports per‑epoch training & validation loss and writes the best model to best_model.pth. (explained in detail in base_model/)

3. To run inference: \
Use eval.py to generate placement predictions:
```bash
python eval.py \
  --data-dir      ./raw_graph \
  --test-designs  gcd_asap7 \
  --batch-size    1 \
  --clustering    1
```
Scripts and commands to evaluate are given in base_model/. Predictions are written to ./pred/<lt>design<gt>_predictions.txt.

# Experiments
We conducted several studies to refine our placement model:

1. Loss Functions: We found that training with only the relative-distance loss (pairwise edge-length MSE) yielded better validation performance compared to combining with absolute coordinate MSE, which tended to dominate gradients and hurt generalization.

2. GNN Layers: We compared GCNConv, GATv2Conv, and GraphSAGE. GraphSAGE with 6 layers provided the best trade‑off between expressiveness and stability, and worked inductively on unseen netlists. It was also more stable than full-graph attention (GAT) or dense normalization (GCN) on big, sparse hypergraphs.

3. Fixed-pin Features: Appending each node’s fixed-pin normalized (x,y) coordinates as extra features helped the model anchor mobile nodes relative to fixed endpoints.

4. Clustering: Grouping nodes (instances, pins and macros) into clusters during training and mapping back at inference reduced graph size per batch, speeding up training and inference without losing accuracy.

These design choices together improved validation loss consistency and placement quality on unseen designs.

# Results 
Validation Results on trained data gcd_nangate45: 
1. 3.9% Reduction in HPWL
2. Number of Nesterov iterations by 60.
3. Total MSE loss calculated was 0.0029.

