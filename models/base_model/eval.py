#!/usr/bin/env python
import os
import torch
import numpy as np
import argparse
from data_utils import load_all_data, parse_formatted, map_nodes_to_coordinates
from model import PlacementGNN
from train import loss_function
import time


def infer_wrapper(model, test_loader, start, clustering_mode=1, run_path='../../new_workspace/flow/raw_graph_test'):
    # Load trained weights
    PATH = './gnn_all.pth'
    model.load_state_dict(torch.load(PATH, map_location=model.device))
    os.makedirs('./predictions', exist_ok=True)
    model.eval()
    total = 0.0
    criterion = torch.nn.MSELoss().to(model.device)
    # Iterate over each graph in the test set
    with torch.no_grad():
        for i, data in enumerate(test_loader.dataset):

            if (clustering_mode):
                cluster_file = os.path.join(f"{run_path}", data.design_name + '_mapping.txt')
                name_map_file = os.path.join(f"../../new_workspace/flow/raw_graph", data.design_name + '_formatted.txt')
                _, records, _, _ = parse_formatted(name_map_file)
            else:
                formatted_fp = os.path.join(f"{run_path}", data.design_name + '_formatted.txt')
                _, records, _, _ = parse_formatted(formatted_fp)
                
            data = data.to(model.device)
            batch_vec = torch.zeros(data.x.size(0), dtype=torch.long, device=model.device)
            out = model(data.x, data.edge_index, batch_vec, data.u)

            loss = loss_function(out, data, criterion)
            total += loss.item()
            
            # out: shape [num_nodes, 2]
            x = out[:, 0]
            y = out[:, 1]
            x_min, x_max = x.min(), x.max()
            y_min, y_max = y.min(), y.max()
            
            x_range = x_max - x_min
            y_range = y_max - y_min
            x_range = x_range if x_range > 1e-6 else 1.0
            y_range = y_range if y_range > 1e-6 else 1.0
            
            x_scaled = (x - x_min) / x_range
            y_scaled = (y - y_min) / y_range
            
            out = torch.stack([x_scaled, y_scaled], dim=1)  # shape: [num_nodes, 2]

            lx, ux = data.bounds['lx'], data.bounds['ux']
            ly, uy = data.bounds['ly'], data.bounds['uy']
            scale  = torch.tensor([ux - lx, uy - ly], device=out.device)
            offset = torch.tensor([lx, ly], device=out.device)
            preds  = (out * scale + offset).cpu().numpy()
            
            id2name = {}
            fixed_ids = []
            for rec in records:
                d = rec['driver']
                id2name[d['id']] = d.get('name', str(d['id']))
                for s in rec['sinks']:
                    id2name[s['id']] = s.get('name', str(s['id']))

            if (clustering_mode):
            
                cluster_ids = data.node_ids.tolist() if torch.is_tensor(data.node_ids) else data.node_ids
                combined_preds = [
                    [int(cid), float(x), float(y)]
                    for cid, (x, y) in zip(cluster_ids, preds)
                ]
                pred_mapped = map_nodes_to_coordinates(cluster_file, combined_preds)
                
                node_ids = np.array([int(row[0]) for row in pred_mapped])
                
                fixed_ids = [int(rec['driver']['id']) for rec in records if rec['driver'].get('is_fixed')]
                fixed_ids += [int(s['id']) for rec in records for s in rec['sinks'] if s.get('is_fixed')]
                
                mask = ~np.isin(node_ids, fixed_ids)
                names = [id2name.get(nid, str(nid)) for nid in node_ids]
                names = [name for name, m in zip(names, mask) if m]
                preds_new = np.array([[row[1], row[2]] for row in pred_mapped])[mask]
    
                fname = f"./predictions/{data.design_name}_predictions.txt"
                with open(fname, "w", newline="") as f:
                    f.write(f"InstanceName x_center y_center\n")
                    for name, row in zip(names, preds_new):
                        x_coord, y_coord = row
                        f.write(f"{name} {x_coord:.4f} {y_coord:.4f}\n")
                print(f"Saved {fname}")
                f.close()
                
            else:

                node_ids   = data.node_ids.tolist() if torch.is_tensor(data.node_ids) else data.node_ids
                names = [id2name.get(nid, str(nid)) for nid in node_ids]
                if hasattr(data, 'fixed_ids') and data.fixed_ids:
                    mask = ~np.isin(node_ids, data.fixed_ids)
                    names = [name for name, m in zip(names, mask) if m]
                    preds = preds[mask]
        
                fname = f"./pred/{data.design_name}_predictions.txt"
                with open(fname, "w", newline="") as f:
                    f.write(f"InstanceName x_center y_center\n")
                    for name, (xv, yv) in zip(names, preds):
                        f.write(f"{name} {xv:.4f} {yv:.4f}\n")
                print(f"Saved {fname}")
                f.close()
    end = time.time()
    print(f'MSE: {total/len(test_loader.dataset):.4f}')
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
    model = PlacementGNN(in_channels=13, hidden_channels=64, num_layers=4, global_channels=5, conv_type='gcn').to(device)
    model.device = device

    # Run inference
    infer_wrapper(model, test_loader, start, clustering_mode=args.clustering,
                  run_path=args.data_dir)

if __name__ == '__main__':
    main()
