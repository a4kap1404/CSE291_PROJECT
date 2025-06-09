#!/usr/bin/env python
import os
import torch
import numpy as np
import argparse
from data_utils import load_all_data, parse_formatted, map_nodes_to_coordinates
from model import PlacementGNN
from train import loss_function
import time


def infer_wrapper(model, test_loader, start, clustering_mode=1, run_path='./raw_graph'):
    # Load trained weights
    PATH = './best_model.pth'
    model.load_state_dict(torch.load(PATH, map_location=model.device))
    os.makedirs('./pred', exist_ok=True)
    model.eval()
    total_loss = 0.0
    criterion = torch.nn.MSELoss()
    # Iterate over each graph in the test set
    for data in test_loader.dataset:
        # Get records for naming/mapping
        if clustering_mode:
            cluster_file = os.path.join(run_path, data.design_name + '_mapping.txt')
            name_map = os.path.join('../../new_workspace/flow/raw_graph/', data.design_name + '_formatted.txt')
            _, records, _, _ = parse_formatted(name_map)
        else:
            formatted_fp = os.path.join(run_path, data.design_name + '_formatted.txt')
            _, records, _, _ = parse_formatted(formatted_fp)

        # Move to device
        data = data.to(model.device)
        batch_vec = torch.zeros(data.x.size(0), dtype=torch.long, device=model.device)
        out = model(data.x, data.edge_index, batch_vec, data.u)

        # Compute loss
        loss = loss_function(out, data, criterion)
        total_loss += loss.item()

        # Normalize predictions back to core bounds
        x, y = out[:,0], out[:,1]
        x_min, x_max = x.min(), x.max()
        y_min, y_max = y.min(), y.max()
        x_range = (x_max - x_min).clamp(min=1e-6)
        y_range = (y_max - y_min).clamp(min=1e-6)
        x_scaled = (x - x_min) / x_range
        y_scaled = (y - y_min) / y_range
        scaled = torch.stack([x_scaled, y_scaled], dim=1)

        lx, ly = data.bounds['lx'], data.bounds['ly']
        ux, uy = data.bounds['ux'], data.bounds['uy']
        scale = torch.tensor([ux - lx, uy - ly], device=scaled.device)
        offset = torch.tensor([lx, ly], device=scaled.device)
        preds = (scaled * scale + offset).detach().cpu().numpy()

        # Build id->name mapping
        id2name = {}
        for rec in records:
            d = rec['driver']
            id2name[d['id']] = d.get('name', str(d['id']))
            for s in rec['sinks']:
                id2name[s['id']] = s.get('name', str(s['id']))

        # Handle clustering mapping
        if clustering_mode:
            cluster_ids = data.node_ids
            combined = [[int(cid), float(px), float(py)] for cid,(px,py) in zip(cluster_ids, preds)]
            pred_mapped = map_nodes_to_coordinates(cluster_file, combined)
            node_ids = np.array([row[0] for row in pred_mapped])
            vals     = np.array([row[1:] for row in pred_mapped])
        else:
            node_ids = np.array(data.node_ids)
            vals     = preds

        # Exclude fixed pins
        fixed_ids = set(data.fixed_ids)
        mask = [nid not in fixed_ids for nid in node_ids]
        names = [id2name[nid] for nid, m in zip(node_ids, mask) if m]
        coords = vals[mask]

        # Write predictions
        out_path = f'./pred/{data.design_name}_predictions.txt'
        with open(out_path, 'w') as fout:
            fout.write('InstanceName x_center y_center\n')
            for name,(xv,yv) in zip(names, coords):
                fout.write(f'{name} {xv:.4f} {yv:.4f}\n')
        print(f'Saved {out_path}')

    avg_loss = total_loss / len(test_loader.dataset)
    end = time.time()
    print(f'MSE: {avg_loss:.4f}')
    print(f"Inference time: {end - start:.2f} seconds")


def main():
    start = time.time()
    parser = argparse.ArgumentParser()
    parser.add_argument('--data-dir', required=True)
    parser.add_argument('--test-designs', nargs='+', required=True)
    parser.add_argument('--batch-size', type=int, default=1)
    parser.add_argument('--clustering', type=int, default=1,
                        help='1 to use clustering mapping, 0 for direct')
    args = parser.parse_args()
    device = torch.device('cuda' if torch.cuda.is_available() else 'cpu')
    
    # Load only test split
    _, test_loader = load_all_data(
        root_dir   = args.data_dir,
        train_list = [],
        test_list  = args.test_designs,
        batch_size = args.batch_size,
        device     = device
    )

    # Instantiate model
    sample = next(iter(test_loader))
    in_dim = sample.x.shape[1]
    model = PlacementGNN(in_channels=13, hidden_channels=64, num_layers=6, global_channels=5, conv_type='gcn').to(device)
    model.device = device

    # Run inference
    infer_wrapper(model, test_loader, start, clustering_mode=args.clustering,
                  run_path=args.data_dir)

if __name__ == '__main__':
    main()
