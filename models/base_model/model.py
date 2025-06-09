import torch
import torch.nn.functional as F
from torch.nn import Module, Linear, LayerNorm, Sequential, ReLU
from torch_geometric.nn import GATv2Conv, SAGEConv, GCNConv

class PositionalEncoder(torch.nn.Module):
    def __init__(self, pe_dim, hidden_dim):
        super().__init__()
        self.pe_mlp = torch.nn.Sequential(
            torch.nn.Linear(pe_dim, hidden_dim),
            torch.nn.ReLU(),
            torch.nn.Linear(hidden_dim, hidden_dim)
        )

    def forward(self, pe):
        return self.pe_mlp(pe)
# In[8]:

class PlacementGNN(torch.nn.Module):
    def __init__(self, in_channels, hidden_channels=64, num_layers=3, global_channels=3, conv_type='sage'):
        super().__init__()
        #self.pos_encoder = PositionalEncoder(pe_dim=in_channels, hidden_dim=64)
        ConvMap = {'gat': GATv2Conv, 'sage': SAGEConv, 'gcn': GCNConv}
        Conv = ConvMap[conv_type]
        self.convs = torch.nn.ModuleList()
        for i in range(num_layers):
            self.convs.append(
                Conv(
                    in_channels  if i == 0 else hidden_channels,
                    #hidden_channels,
                    hidden_channels
                )
            )
        self.norm = torch.nn.LayerNorm(hidden_channels)
        self.post_lin = torch.nn.Linear(hidden_channels + global_channels, hidden_channels)
        self.out_lin = torch.nn.Linear(hidden_channels, 2)

    def forward(self, x, edge_index, batch, u, edge_attr=None):
        #pe_encoded = self.pos_encoder(x)
        #x = pe_encoded
        for conv in self.convs:
            if isinstance(conv, GATv2Conv):
                x = conv(x, edge_index, edge_attr)
            else:
                x = conv(x, edge_index)
            x = F.relu(x)
        x = self.norm(x)
        u_exp = u[batch]
        h = torch.cat([x, u_exp], dim=1)
        h = F.relu(self.post_lin(h))
        return self.out_lin(h)