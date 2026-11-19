from torch import nn

class StellarCollapseMLP(nn.Module):
    def __init__(self, input_size, hidden_size):
        super().__init__()
        self.hidden = nn.Linear(input_size, hidden_size)
        self.relu = nn.ReLU()
        self.output = nn.Linear(hidden_size, 1)
        self.sigmoid = nn.Sigmoid()

    def forward(self, x):
        x = self.relu(self.hidden(x))
        return self.sigmoid(self.output(x))
