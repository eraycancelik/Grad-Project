import matplotlib.pyplot as plt

REFRIGERANTS = {
    'R134a':   {'color': '#2196F3', 'marker': 'o', 'label': 'R134a (HFC)'},
    'R290':    {'color': '#4CAF50', 'marker': 's', 'label': 'R290 (Propan)'},
    'R1234yf': {'color': '#FF9800', 'marker': '^', 'label': 'R1234yf (HFO)'},
    'R744':    {'color': '#9C27B0', 'marker': 'D', 'label': 'R744 (CO₂)'},
    'R600a':   {'color': '#F44336', 'marker': 'v', 'label': 'R600a (İzobütan)'},
}

GWP = {'R134a': 1370, 'R290': 20, 'R1234yf': 4, 'R744': 1, 'R600a': 20}
ODP = {'R134a': 0,    'R290': 0,  'R1234yf': 0, 'R744': 0, 'R600a': 0}

REFRIGERANT_CODES = {ref: i for i, ref in enumerate(REFRIGERANTS)}

def setup_matplotlib_config():
    plt.rcParams.update({
        'figure.dpi': 120,
        'font.family': 'DejaVu Sans',
        'axes.grid': True,
        'grid.alpha': 0.3,
        'axes.spines.top': False,
        'axes.spines.right': False,
    })
