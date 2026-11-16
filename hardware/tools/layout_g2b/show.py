import json, pickle
from render import draw
b = pickle.load(open('board.pkl','rb'))
r = json.load(open('routes.json'))
draw(b, 'routed.png', r, 'routed')
