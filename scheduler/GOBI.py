import sys
sys.path.append('scheduler/BPTI/')

from .Scheduler import *
from .BPTI.train import *

class GOBIScheduler(Scheduler):
	def __init__(self, data_type):
		super().__init__()
		self.model = eval(data_type+"()")
		self.model, _, _, _ = load_model(data_type, self.model, data_type)
		self.data_type = data_type

	def run_GOBI(self):
		cpu = [host.getCPU() for host in self.env.hostlist]
		alloc = []; prev_alloc = {}
		for c in self.env.containerlist:
			oneHot = [0] * len(self.env.hostlist)
			if c: prev_alloc[c.id] = c.getHostID()
			if c and c.getHostID() != -1: oneHot[c.getHostID()] = 1
			else: oneHot[np.random.randint(0,len(self.env.hostlist))] = 1
			alloc.append(oneHot)
		init = np.concatenate((np.array([cpu]).transpose(), alloc), axis=1)
		init = torch.tensor(init, dtype=torch.float, requires_grad=True)
		result, iteration, fitness = opt(init, self.model, [], self.data_type)
		decision = []
		for cid in prev_alloc:
			one_hot = result[cid, 1:].tolist()
			new_host = one_hot.index(max(one_hot))
			if prev_alloc[cid] != new_host: decision.append((cid, new_host))
		return decision

	def selection(self):
		return []

	def placement(self, containerIDs):
		first_alloc = np.all([not (c and c.getHostID() != -1) for c in self.env.containerlist])
		decision = self.run_GOBI()
		return decision