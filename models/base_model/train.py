import torch
from torch.nn import MSELoss
from torch.optim import Adam
from data_utils import load_all_data
from model import PlacementGNN
import argparse


def compute_relative_loss(out, data, criterion):
    edge_index = data.edge_index

    src, tgt = edge_index
    pred_src, pred_tgt = out[src], out[tgt]
    true_src, true_tgt = data.y[src], data.y[tgt]
    pred_dist = torch.norm(pred_src - pred_tgt, dim=1)
    true_dist = torch.norm(true_src - true_tgt, dim=1)
    loss = criterion(pred_dist, true_dist)

    return loss

def loss_function(out, data, criterion):
    pred_x, pred_y = out[:, 0], out[:, 1]
    #density = soft_density_loss(pred_x, pred_y, cell_area=0.0001, bin_size=0.05, density_threshold=0.6, sigma=0.01)
    #loss = 0.0 * criterion(out, data.y) + 1.0 * compute_relative_loss(out, data, criterion) + 0.0 * density
    loss = compute_relative_loss(out, data, criterion)
    return loss

def adjust_learning_rate(optimizer, epoch):
    adjust_list = [100]
    if epoch in adjust_list:
        for param_group in optimizer.param_groups:
            param_group['lr'] = param_group['lr'] * 0.2


def train(loader, model, opt, criterion, device, epoch):
    model.train()
    total = 0
    for data in loader:
        data = data.to(device)
        opt.zero_grad()
        out = model(data.x, data.edge_index, data.batch, data.u)
        loss = loss_function(out, data, criterion)
        loss.backward()
        opt.step()
        total += loss.item() * data.num_graphs
    avg_loss = total/len(loader.dataset)
    if (epoch) % 10 == 0:
        print(f'Epoch {epoch} Training loss: MSE: {avg_loss:.4f}')
    return total / len(loader.dataset)

def validate(loader, model, criterion, device):
    model.eval()
    total_loss = 0.0
    total_nodes = 0
    with torch.no_grad():
        for data in loader:
            data = data.to(device)
            out = model(data.x, data.edge_index, data.batch, data.u)
            src, tgt = data.edge_index
            rel_loss = criterion((out[src]-out[tgt]).norm(dim=1),
                                  (data.y[src]-data.y[tgt]).norm(dim=1))
            total_loss += rel_loss.item() * data.num_nodes
            total_nodes += data.num_nodes
    return total_loss / total_nodes


def main():
    p = argparse.ArgumentParser(description="Train PlacementGNN")
    p.add_argument('--data-dir',        default='./raw_graph',
                   help="root folder containing *_formatted.txt graphs")
    p.add_argument('--train-designs',  nargs='+', required=True,
                   help="e.g. gcd_asap7")
    p.add_argument('--test-designs',   nargs='+', required=True,
                   help="e.g. gcd_nangate45")
    p.add_argument('--batch-size',      type=int, default=4)
    p.add_argument('--epochs',          type=int, default=100)
    p.add_argument('--lr',              type=float, default=2e-4)
    p.add_argument('--weight-decay',    type=float, default=1e-4)
    args = p.parse_args()
    print("Loading Data")  
    device = torch.device('cuda' if torch.cuda.is_available() else 'cpu')
    train_loader, test_loader = load_all_data(args.data_dir, train_list=args.train_designs, test_list=args.test_designs, batch_size=args.batch_size)
    print("Data Loading Done")
    model     = PlacementGNN(in_channels=13, hidden_channels=64, num_layers=6, global_channels=5, conv_type='sage').to(device)
    opt       = Adam(model.parameters(), lr=args.lr, weight_decay=args.weight_decay)
    criterion = MSELoss().to(device)
    val_loss = 0
    print("Iterating over epochs")
    best_val = float('inf')
    for epoch in range(1,201):
        train_loss = train(train_loader, model, opt, criterion, device,epoch)
        val_loss   = validate(test_loader, model, criterion, device)
        if epoch % 10 == 0:
            print(f"[{epoch:03d}] train={train_loss:.4f} | Val Loss: {val_loss:.4f}")
        if val_loss < best_val - 1e-6:
            best_val = val_loss
            torch.save(model.state_dict(), 'best_model.pth')
    print("Best model saved under best_model.pth")
    print("Done")

if __name__ == "__main__":
    main()