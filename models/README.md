This repository provides scripts to train and evaluate a Graph Neural Network (GNN) for initial placement coordinate prediction using hypergraph data (drivers & sinks). The two main entry points are:

train.py — trains the PlacementGNN model \
eval.py — runs inference on held-out designs and writes predicted placements

# 0. Directory Summary 
```bash
base_model/
├── data_utils.py   # parsing + DataLoader builder
├── model.py        # PlacementGNN definition
├── train.py        # training script
├── eval.py         # inference script
├── requirements.txt
├── raw_graph/      # your input _formatted.txt files
└── pred/           # generated predictions
```
# 1. Environment Setup
Conda (recommended)
```bash
conda create -n gnnplace python=3.11 -y
conda activate gnnplace
pip install -r requirements.txt
```
venv (alternative)
```bash
python3.11 -m venv .venv
source .venv/bin/activate        # macOS/Linux
# .\.venv\Scripts\Activate.ps1 # Windows PowerShell
pip install -r requirements.txt
```
# 2. Data Layout
Place your formatted graph data under a folder (default: /new_workspace/flow/raw_graph/) with filenames like:
```bash
<design>_formatted.txt
<design>_label_formatted.txt
<design>_mapping.txt # only for clustering-based inference
```

# 3. Train
Run train.py using the following command:
```bash
python train.py \
  --data-dir     ./raw_graph \
  --train-designs gcd_asap7 ibex_nangate45 \
  --test-designs  gcd_nangate45 aes_asap7 \
  --batch-size    4 \
  --epochs        150 \
  --lr            2e-4 \
  --weight-decay  1e-4
```
--data-dir      : root folder containing your formatted text files
--train-designs: space-separated list of design names (e.g. gcd_asap7)
--test-designs : space-separated list for validation during training
--batch-size    : number of graphs per batch
--epochs        : number of training epochs
--lr            : learning rate
--weight-decay  : optimizer weight decay

The script will print per-epoch train & validation relative losses, and save the best model to best_model.pth.

# 4 Evaluation / Inference
After training, run eval.py to generate (design)_predictions.txt for each test graph:
```bash
python eval.py \
  --data-dir     ./raw_graph \
  --test-designs gcd_nangate45 \
  --batch-size    1 \
```

Predictions are written into the ./pred/ directory, one file per design:
```bash
pred/ <design>_predictions.txt
```
and a final MSE (relative‐distance) is printed.
