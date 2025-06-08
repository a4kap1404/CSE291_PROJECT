import torch
from torch.nn import MSELoss
from torch.optim import Adam
from data_utils import load_all_data
from model import PlacementGNN


def compute_relative_loss(out, data, criterion):
    edge_index = data.edge_index

    src, tgt = edge_index
    pred_src, pred_tgt = out[src], out[tgt]
    true_src, true_tgt = data.y[src], data.y[tgt]
    pred_dist = torch.norm(pred_src - pred_tgt, dim=1)
    true_dist = torch.norm(true_src - true_tgt, dim=1)
    loss = criterion(pred_dist, true_dist)

    return loss

def soft_density_loss(x, y, cell_area=0.0001, bin_size=0.05, density_threshold=0.4, sigma=0.01):
    device = x.device
    x = torch.clamp(x, 0.0, 1.0)
    y = torch.clamp(y, 0.0, 1.0)
    x_bins = torch.arange(bin_size / 2, 1.0, bin_size, device=device)
    y_bins = torch.arange(bin_size / 2, 1.0, bin_size, device=device)
    x_centers, y_centers = torch.meshgrid(x_bins, y_bins, indexing='ij')

    Bx, By = x_centers.shape
    num_bins = Bx * By

    x_centers_flat = x_centers.flatten().unsqueeze(0)
    y_centers_flat = y_centers.flatten().unsqueeze(0)
    x_expand = x.unsqueeze(1)  # (N, 1)
    y_expand = y.unsqueeze(1)  # (N, 1)

    dx2 = (x_expand - x_centers_flat) ** 2
    dy2 = (y_expand - y_centers_flat) ** 2
    gauss = torch.exp(-(dx2 + dy2) / (2 * sigma**2))  # (N, B)

    density_per_bin = torch.sum(gauss, dim=0) * cell_area  # (B,)
    bin_area = bin_size * bin_size
    density_norm = density_per_bin / bin_area  # (B,)

    penalty = torch.clamp(density_norm - density_threshold, min=0.0)
    loss = penalty.sum()

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
    print("loading…")
    #device = torch.device("cpu")
    #torch.cuda.is_available = lambda : False    
    device = torch.device('cuda' if torch.cuda.is_available() else 'cpu')
    train_loader, test_loader = load_all_data('raw_graph', train_list=['gcd_asap7'], test_list=['gcd_nangate45'], batch_size=4)
    print("loaded")
    model     = PlacementGNN(in_channels=13, hidden_channels=64, num_layers=6, global_channels=5, conv_type='gcn').to(device)
    opt       = Adam(model.parameters(), lr=2e-4, weight_decay=1e-4)
    criterion = MSELoss().to(device)
    #val_loss = 0
    print("iterating…")
    best_val = float('inf')
    for epoch in range(1,151):
        train_loss = train(train_loader, model, opt, criterion, device,epoch)
        val_loss   = validate(test_loader, model, criterion, device)
        if epoch % 10 == 0:
            print(f"[{epoch:03d}] train={train_loss:.4f} | Val Loss: {val_loss:.4f}")
        #if val_loss < best_val - 1e-6:
            #best_val = val_loss
    torch.save(model.state_dict(), 'best_model.pth')
    print("Done")

if __name__ == "__main__":
    main()