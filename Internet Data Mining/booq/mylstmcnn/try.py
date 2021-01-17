import numpy as np
import matplotlib.pyplot as plt

t = [i for i in range(10)]
plt.plot(t, [i for i in range(len(t))], 'b')
label = ['t', 't**2']
plt.legend(label, loc='upper left')
plt.savefig('./test2.jpg')
plt.show()