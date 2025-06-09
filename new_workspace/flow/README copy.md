# Dataset

This folder covers invocation of openroad, running synth, floorplan and placement upto step 3_2_place_iop, label generation, graph construction and formatting, and finally clustering of nodes using spectral clustering which will be used as our dataset.

# Dataset Composition

The training data includes variations of designs GCD-NanGate45, IBEX-NanGate45, AES-NanGate45, GCD-ASAP7, IBEX-ASAP7, AES-ASAP7, and ARIANE136-NanGate45 with parameters such as Core Utilization, Core Aspect Ratio, and Place Desnity being varied. It also includes 82 synthetic designs generated using Artnet.

The test data includes JPEG-ASAP7, JPEG-NanGate45 and SWERV_WRAPPER-NanGate45.

# Data Format

Formatted file (*_formatted.txt): Contains core/die bounds (Die Width, Die Height, Core Width, Core Height, lx, ly, ux, uy), global metrics (Core Aspect Ratio, Utilization, Place Density), and a list of net records. Each record is a Python dict with a driver and list of sinks, each having id, name, is_fixed, and area fields.

Label file (*_label_formatted.txt): Contains ground-truth x_center and y_center for each pin, one line per instance: &lt;ID&gt; &lt;X&gt; &lt;Y&gt;

# Datset Generation Flow

First set the design variables in &lt;repo_dir&gt;/new_workspace/set_variables.sh
The first few variables (counter_*) can be ignored as they are not used in test mode.
Enter the name of the design to be tested in DESIGN and tech_node as shown below.
Set test_mode=1 when testing (not in bulk data generation mode).

DESIGN=jpeg
tech_node=asap7
test_mode=1
threshold=50

Then follow the steps below.

## Openroad and Label Generation
We have already run the orfs_copy command to load ORFS into &lt;repo_dir&gt;/new_workspace/
Run the following command:

```bash
cd <repo_dir>/new_workspace/flow/
source get_openroad_run.sh # run placement
```

## Hypergraph generation and formatting
Run the following command to generate the formatted hypergraph file and labels to train the model:

```bash
cd <repo_dir>/new_workspace/flow/
source get_graph_label.sh # extract graph data and labels
```

## Perform clustering
Run the following command to perfrom clustering (spectral clustering) and generate the formatted hypergraph file:

```bash
cd <repo_dir>/new_workspace/flow/
source get_clusters.sh # extract graph data and labels
```

The data from &lt;repo_dir&gt;/new_workspace/raw_graph_clustered/ can now be used by the model for training and &lt;repo_dir&gt;/new_workspace/raw_graph_test/ can be used for inference. The model at &lt;repo_dir&gt;/models/base_model already points to these directories.

