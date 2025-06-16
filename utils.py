import matplotlib.pyplot as plt
from matplotlib.colors import ListedColormap, BoundaryNorm
from matplotlib.image import imread


def plot_ndvi_image(image):

    ndvi_classes = {
        'NDVI < -0.5': '#0c0c0c',
        '-0.5 < NDVI ≤ 0': '#eaeaea',
        '0 < NDVI ≤ 0.1': '#ccc682',
        '0.1 < NDVI ≤ 0.2': '#91bf51',
        '0.2 < NDVI ≤ 0.3': '#70a33f',
        '0.3 < NDVI ≤ 0.4': '#4f892d',
        '0.4 < NDVI ≤ 0.5': '#306d1c',
        '0.5 < NDVI ≤ 0.6': '#0f540a',
        '0.6 < NDVI ≤ 1.0': '#004400'
    }

    # Extraire les couleurs et les bornes
    colors = list(ndvi_classes.values())
    bounds = [-1.0, -0.5, 0.0, 0.1, 0.2, 0.3, 0.4, 0.5, 0.6, 1.0]

    # 4. Créer la colormap et la normalisation
    cmap = ListedColormap(colors)
    norm = BoundaryNorm(bounds, cmap.N)

    # 5. Afficher l'image avec la colorbar
    plt.figure(figsize=(12, 10))

    # Afficher l'image NDVI
    img = plt.imshow(image,  # Utilisez la première couche si image multi-canaux
                    cmap=cmap,
                    norm=norm)

    # Ajouter la colorbar
    cbar = plt.colorbar(img,
                    orientation='vertical',
                    shrink=0.8,
                    ticks=[-0.75, -0.25, 0.05, 0.15, 0.25, 0.35, 0.45, 0.55, 0.8])
    cbar.set_label('Valeurs', fontsize=12)

    # Configurer les étiquettes de la colorbar
    class_labels = list(ndvi_classes.keys())
    cbar.ax.set_yticklabels(class_labels, fontsize=9)

    plt.title("Carte NDVI de l'image", fontsize=14)
    plt.axis('off')
    plt.tight_layout()
    plt.show()