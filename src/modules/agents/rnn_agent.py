import torch.nn as nn
import torch.nn.functional as F

# エージェント間でパラメーターを共有（同じ1つのネットワークを使う）


class RNNAgent(nn.Module):
    """
    RNN (GRU)を用いたエージェントネットワーク
    """

    def __init__(self, input_shape, args):
        super(RNNAgent, self).__init__()
        self.args = args

        self.fc1 = nn.Linear(input_shape, args.rnn_hidden_dim)
        # 回帰ニューラルネットワークを使うか
        if self.args.use_rnn:
            print("use RNN!")
            self.rnn = nn.GRUCell(args.hidden_dim, args.hidden_dim)
        else:
            print("use Linear instead of RNN!")
            self.rnn = nn.Linear(args.hidden_dim, args.hidden_dim)
        self.fc2 = nn.Linear(args.rnn_hidden_dim, args.n_actions)

    def init_hidden(self):
        """
        RNNの隠れ層を0で初期化
        """
        # make hidden states on same device as model
        return self.fc1.weight.new(1, self.args.rnn_hidden_dim).zero_()

    def forward(self, inputs, hidden_state):
        x = F.relu(self.fc1(inputs))
        h_in = hidden_state.reshape(-1, self.args.hidden_dim)
        if self.args.use_rnn:
            h = self.rnn(x, h_in)
        else:
            h = F.relu(self.rnn(x))
        q = self.fc2(h)
        return q, h
