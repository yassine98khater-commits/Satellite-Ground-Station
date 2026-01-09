# gui_app.py
"""
Satellite Tracker Pro - Rennes, France
Version avec actualisation auto + direction satellite + texte lisible
"""

import sys
import warnings
warnings.filterwarnings('ignore')

from PyQt6.QtWidgets import (QApplication, QMainWindow, QWidget, QVBoxLayout, 
                             QHBoxLayout, QPushButton, QListWidget, QLabel, 
                             QGroupBox, QTextEdit, QSplitter, QComboBox)
from PyQt6.QtCore import QTimer, Qt
from PyQt6.QtGui import QFont
import matplotlib.pyplot as plt
from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg as FigureCanvas
from matplotlib.figure import Figure
import matplotlib.patches as mpatches
import numpy as np
from datetime import datetime
import pytz

from tle_manager import TLEManager
from tracker import SatelliteTracker
from predictor import PassPredictor
from satellite_db import get_satellite_info


class InteractiveEarthMapWidget(FigureCanvas):
    """Carte interactive avec direction du satellite"""
    
    def __init__(self, parent=None, tracker=None):
        self.fig = Figure(figsize=(16, 10), facecolor='#0a0a0a', dpi=120)
        super().__init__(self.fig)
        self.tracker = tracker
        self.selected_satellite = None
        
        # Historique de position pour calculer la direction
        self.last_position = None
        
        # État pan et zoom
        self.center_lon = -1.6778  # Rennes
        self.center_lat = 48.1173
        self.zoom_level = 1.5
        self.panning = False
        self.pan_start = None
        self.update_pending = False
        
        try:
            import cartopy.crs as ccrs
            import cartopy.feature as cfeature
            self.has_cartopy = True
            
            self.ax = self.fig.add_subplot(111, projection=ccrs.PlateCarree(), 
                                          facecolor='#1a1a2e')
            self.ccrs = ccrs
            self.cfeature = cfeature
            
            self.fig.subplots_adjust(left=0, right=1, top=0.97, bottom=0.03)
            
        except ImportError:
            print("Cartopy non disponible")
            self.has_cartopy = False
            self.ax = self.fig.add_subplot(111, facecolor='#1a1a2e')
            self.fig.subplots_adjust(left=0, right=1, top=0.97, bottom=0.03)
        
        self.setup_earth_map()
        
        # Événements souris
        self.mpl_connect('scroll_event', self.on_scroll)
        self.mpl_connect('button_press_event', self.on_mouse_press)
        self.mpl_connect('button_release_event', self.on_mouse_release)
        self.mpl_connect('motion_notify_event', self.on_mouse_move)
        
    def on_scroll(self, event):
        """Gestion du zoom avec molette"""
        if event.inaxes != self.ax:
            return
        
        if event.button == 'up':
            new_zoom = min(self.zoom_level * 1.3, 20.0)
        elif event.button == 'down':
            new_zoom = max(self.zoom_level / 1.3, 0.8)
        else:
            return
        
        if event.xdata and event.ydata:
            zoom_factor = new_zoom / self.zoom_level
            dx = event.xdata - self.center_lon
            dy = event.ydata - self.center_lat
            
            self.center_lon = event.xdata - dx / zoom_factor
            self.center_lat = event.ydata - dy / zoom_factor
        
        self.zoom_level = new_zoom
        self.request_update()
    
    def on_mouse_press(self, event):
        if event.inaxes != self.ax:
            return
        
        if event.button == 1:
            self.panning = True
            self.pan_start = (event.xdata, event.ydata) if event.xdata and event.ydata else None
            self.setCursor(Qt.CursorShape.ClosedHandCursor)
    
    def on_mouse_release(self, event):
        self.panning = False
        self.pan_start = None
        self.setCursor(Qt.CursorShape.ArrowCursor)
        self.update_view_immediate()
    
    def on_mouse_move(self, event):
        if not self.panning or not self.pan_start or not event.xdata or not event.ydata:
            return
        
        dx = self.pan_start[0] - event.xdata
        dy = self.pan_start[1] - event.ydata
        
        self.center_lon += dx
        self.center_lat += dy
        
        self.center_lat = max(-85, min(85, self.center_lat))
        
        while self.center_lon > 180:
            self.center_lon -= 360
        while self.center_lon < -180:
            self.center_lon += 360
        
        self.request_update()
    
    def request_update(self):
        if not self.update_pending:
            self.update_pending = True
            QTimer.singleShot(50, self.update_view_throttled)
    
    def update_view_throttled(self):
        self.update_pending = False
        self.update_view_immediate()
    
    def update_view_immediate(self):
        if not self.has_cartopy:
            self.draw()
            return
        
        lon_range = 180 / self.zoom_level
        lat_range = 90 / self.zoom_level
        
        extent = [
            self.center_lon - lon_range,
            self.center_lon + lon_range,
            max(-90, self.center_lat - lat_range),
            min(90, self.center_lat + lat_range)
        ]
        
        self.ax.set_extent(extent, crs=self.ccrs.PlateCarree())
        self.draw()
        
    def setup_earth_map(self):
        """Configuration carte haute résolution"""
        self.ax.clear()
        
        if self.has_cartopy:
            if self.zoom_level > 5.0:
                resolution = '10m'
            elif self.zoom_level > 2.0:
                resolution = '50m'
            else:
                resolution = '110m'
            
            self.ax.stock_img()
            
            borders = self.cfeature.NaturalEarthFeature(
                category='cultural',
                name='admin_0_boundary_lines_land',
                scale=resolution,
                facecolor='none',
                edgecolor='white',
                alpha=0.6
            )
            self.ax.add_feature(borders, linewidth=0.5, zorder=3)
            
            coastline = self.cfeature.NaturalEarthFeature(
                category='physical',
                name='coastline',
                scale=resolution,
                facecolor='none',
                edgecolor='#8BC34A'
            )
            self.ax.add_feature(coastline, linewidth=0.8, zorder=3)
            
            if self.zoom_level > 0.8:
                gl = self.ax.gridlines(draw_labels=True, linewidth=0.4, color='cyan', 
                                      alpha=0.4, linestyle='--', zorder=2)
                gl.xlabel_style = {'size': 9, 'color': 'white'}
                gl.ylabel_style = {'size': 9, 'color': 'white'}
                gl.top_labels = False
                gl.right_labels = False
            
            if self.zoom_level > 1.0:
                self.update_view_immediate()
            else:
                self.ax.set_global()
        else:
            self.ax.set_xlim(-180, 180)
            self.ax.set_ylim(-90, 90)
            self.ax.grid(True, alpha=0.2, color='cyan')
        
        self.ax.set_title(' Satellite Tracker - Rennes, France', 
                         color='white', fontsize=13, pad=10, fontweight='bold')
        
        # Marqueur Rennes
        if self.tracker:
            from config import OBSERVER_LAT, OBSERVER_LON
            transform = self.ccrs.PlateCarree() if self.has_cartopy else None
                
            self.ax.plot(OBSERVER_LON, OBSERVER_LAT, 'r*', markersize=32, 
                        zorder=100, markeredgecolor='yellow', 
                        markeredgewidth=3, transform=transform)
            
            label_size = min(16, 10 + self.zoom_level * 0.5)
            self.ax.text(OBSERVER_LON + 0.2, OBSERVER_LAT + 0.2, 'RENNES', 
                        color='red', fontsize=label_size, fontweight='bold',
                        bbox=dict(boxstyle='round,pad=0.5', facecolor='yellow', 
                                alpha=0.95, edgecolor='red', linewidth=2),
                        transform=transform, zorder=101)
    
    def update_satellites(self, satellites_positions, selected_sat=None):
        """Mise à jour avec ligne de direction du satellite"""
        self.selected_satellite = selected_sat
        self.setup_earth_map()
        
        if not satellites_positions:
            self.draw()
            return
        
        transform = self.ccrs.PlateCarree() if self.has_cartopy else None
        
        for sat_name, pos in satellites_positions.items():
            if pos:
                lon = pos['longitude']
                lat = pos['latitude']
                
                if sat_name == selected_sat:
                    # Satellite sélectionné
                    self.ax.plot(lon, lat, 'o', color='#FFFF00', markersize=5, 
                               markeredgecolor='#FF8C00', markeredgewidth=1, zorder=99,
                               transform=transform)
                    
                    
                    
                    # Ligne de connexion vers Rennes
                    if pos['is_visible']:
                        from config import OBSERVER_LAT, OBSERVER_LON
                        self.ax.plot([OBSERVER_LON, lon], [OBSERVER_LAT, lat], 
                                   'w-', linewidth=12, alpha=0.25, zorder=96,
                                   transform=transform)
                        self.ax.plot([OBSERVER_LON, lon], [OBSERVER_LAT, lat], 
                                   '#00FFFF', linewidth=7, alpha=0.7, zorder=97,
                                   transform=transform)
                        self.ax.plot([OBSERVER_LON, lon], [OBSERVER_LAT, lat], 
                                   '#FFFF00', linewidth=3.5, alpha=1.0, zorder=98,
                                   transform=transform)
                    
                    # NOUVELLE FONCTIONNALITÉ: Flèche de direction du satellite
                    self.draw_satellite_direction(lon, lat, pos, transform)
                    
                else:
                    # Autres satellites
                    color = '#00FF00' if pos['is_visible'] else '#666666'
                    size = 13 if pos['is_visible'] else 2
                    alpha = 0.9 if pos['is_visible'] else 0.5
                    
                    self.ax.plot(lon, lat, 'o', color=color, markersize=size, 
                               markeredgecolor='white', markeredgewidth=0.5, 
                               alpha=alpha, transform=transform, zorder=60)
                    
                    if self.zoom_level > 6.0:
                        self.ax.text(lon + 0.4, lat + 0.4, sat_name, color=color, 
                                   fontsize=8, alpha=alpha, transform=transform,
                                   bbox=dict(boxstyle='round,pad=0.2', 
                                           facecolor='black', alpha=0.7))
        
        """# Légende améliorée
        from matplotlib.lines import Line2D
        legend_elements = [
            Line2D([0], [0], marker='*', color='w', markerfacecolor='red', 
                   markersize=18, label='Rennes', linestyle='None'),
            Line2D([0], [0], marker='o', color='w', markerfacecolor='yellow', 
                   markersize=15, label='Satellite Sélectionné', linestyle='None'),
            Line2D([0], [0], color='#FF00FF', linewidth=3, label='Direction du Satellite'),
            Line2D([0], [0], marker='o', color='w', markerfacecolor='lime', 
                   markersize=12, label='Visible', linestyle='None'),
            Line2D([0], [0], marker='o', color='w', markerfacecolor='gray', 
                   markersize=10, label='Caché', linestyle='None')
        ]
        self.ax.legend(handles=legend_elements, loc='lower left', 
                      facecolor='#0a0a0a', edgecolor='cyan', 
                      labelcolor='white', fontsize=10, framealpha=0.95)"""
        
        self.draw()
    
    def draw_satellite_direction(self, lon, lat, pos, transform):
        """Dessine une flèche montrant la direction du satellite"""
        from config import OBSERVER_LAT, OBSERVER_LON
        
        # Calculer le vecteur de vélocité du satellite
        if 'velocity_km_s' in pos:
            # Utiliser les données de vélocité de Skyfield
            velocity = pos['velocity_km_s']
            
            # Calculer la direction approximative (simplifiée)
            # La vélocité est un vecteur [vx, vy, vz]
            if hasattr(velocity, '__len__') and len(velocity) >= 2:
                vx, vy = velocity[0], velocity[1]
            else:
                # Si pas de données de vélocité, estimer depuis la position précédente
                if self.last_position:
                    vx = lon - self.last_position[0]
                    vy = lat - self.last_position[1]
                else:
                    vx, vy = 1, 0  # Valeur par défaut
            
            # Normaliser et mettre à l'échelle pour la visualisation
            magnitude = np.sqrt(vx**2 + vy**2)
            if magnitude > 0:
                # Longueur de la flèche basée sur le zoom
                arrow_length = 5.0 / self.zoom_level
                
                dx = (vx / magnitude) * arrow_length
                dy = (vy / magnitude) * arrow_length
                
                # Calculer si le satellite s'approche ou s'éloigne de Rennes
                current_distance = np.sqrt((lon - OBSERVER_LON)**2 + (lat - OBSERVER_LAT)**2)
                future_lon = lon + dx
                future_lat = lat + dy
                future_distance = np.sqrt((future_lon - OBSERVER_LON)**2 + (future_lat - OBSERVER_LAT)**2)
                
                # Couleur selon direction
                if future_distance < current_distance:
                    # S'approche de Rennes
                    arrow_color = '#00FF00'  # Vert
                    direction_text = "→ Rennes"
                else:
                    # S'éloigne de Rennes
                    arrow_color = '#FF0066'  # Rose/Rouge
                    direction_text = "← Rennes"
                
                # Dessiner la flèche de direction
                # Ligne principale
                self.ax.plot([lon, lon + dx], [lat, lat + dy], 
                           color=arrow_color, linewidth=4, alpha=0.8, zorder=95,
                           transform=transform)
                
                # Flèche (pointe)
                arrow = mpatches.FancyArrowPatch(
                    (lon, lat), (lon + dx, lat + dy),
                    arrowstyle='->', mutation_scale=30, 
                    color=arrow_color, linewidth=3, alpha=0.9, zorder=95,
                    transform=transform
                )
                self.ax.add_patch(arrow)
                
                # Texte indiquant la direction
                text_offset = arrow_length * 0.6
                self.ax.text(lon + dx + text_offset, lat + dy + text_offset, direction_text,
                           color=arrow_color, fontsize=10, fontweight='bold',
                           bbox=dict(boxstyle='round,pad=0.3', facecolor='black', 
                                   alpha=0.8, edgecolor=arrow_color, linewidth=1.5),
                           transform=transform, zorder=96)
            
            # Sauvegarder la position actuelle pour la prochaine fois
            self.last_position = (lon, lat)


class SkyViewWidget(FigureCanvas):
    """Vue du ciel avec texte bien organisé"""
    
    def __init__(self, parent=None):
        self.fig = Figure(figsize=(6, 6), facecolor='#0a0a0a', dpi=100)
        super().__init__(self.fig)
        
        self.ax = self.fig.add_subplot(111, projection='polar', facecolor='#0d1117')
        self.fig.subplots_adjust(left=0.05, right=0.95, top=0.95, bottom=0.05)
        
        self.setup_sky_view()
        
    def setup_sky_view(self):
        self.ax.clear()
        self.ax.set_theta_zero_location('N')
        self.ax.set_theta_direction(-1)
        self.ax.set_ylim(0, 90)
        self.ax.set_yticks([0, 30, 60, 90])
        self.ax.set_yticklabels(['90°', '60°', '30°', '0°'], color='white', fontsize=10)
        self.ax.set_title('Vue du Ciel depuis Rennes', color='white', 
                         pad=20, fontsize=13, fontweight='bold')
        self.ax.tick_params(colors='white')
        self.ax.grid(True, alpha=0.4, color='cyan', linewidth=0.8)
        
    def update_satellite_position(self, position):
        self.setup_sky_view()
        
        if position and position['is_visible']:
            azimuth_rad = np.radians(position['azimuth'])
            elevation_angle = 90 - position['elevation']
            
            self.ax.plot(azimuth_rad, elevation_angle, 'o', color='yellow', 
                        markersize=22, markeredgecolor='orange', markeredgewidth=3,
                        zorder=10)
            
            info_text = (
                f"AZIMUT\n{position['azimuth']:.1f}°\n\n"
                f"ÉLÉVATION\n{position['elevation']:.1f}°\n\n"
                f"DISTANCE\n{position['distance_km']:.0f} km"
            )
            
            self.ax.text(0.02, 0.98, info_text, 
                        transform=self.ax.transAxes,
                        color='yellow', fontsize=11,
                        bbox=dict(boxstyle='round,pad=0.7', facecolor='black', 
                                alpha=0.9, edgecolor='yellow', linewidth=2),
                        fontweight='bold',
                        verticalalignment='top',
                        horizontalalignment='left')
        else:
            self.ax.text(0, 45, 'SOUS L\'HORIZON', color='#FF4444', fontsize=16,
                        ha='center', fontweight='bold',
                        bbox=dict(boxstyle='round,pad=0.7', facecolor='black', 
                                alpha=0.9, edgecolor='red', linewidth=2))
        
        self.draw()


class MainWindow(QMainWindow):
    """Fenêtre principale avec actualisation auto"""
    
    def __init__(self):
        super().__init__()
        
        self.tle_manager = TLEManager()
        self.tracker = SatelliteTracker()
        self.predictor = None
        self.selected_satellite = None
        self.paris_tz = pytz.timezone('Europe/Paris')
        
        self.setWindowTitle("🛰️ Satellite Tracker Pro - Rennes, France")
        self.setGeometry(50, 50, 1900, 1050)
        self.setStyleSheet("background-color: #0d1117; color: white;")
        
        self.setup_ui()
        self.load_satellites()
        
        # Timer pour mise à jour carte et vue du ciel
        self.map_timer = QTimer()
        self.map_timer.timeout.connect(self.update_display)
        self.map_timer.start(3000)  # Toutes les 3 secondes
        
        # NOUVEAU: Timer pour actualisation automatique des coordonnées
        self.info_timer = QTimer()
        self.info_timer.timeout.connect(self.update_coordinates_only)
        self.info_timer.start(2000)  # Toutes les 2 secondes
        
    def setup_ui(self):
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        main_layout = QHBoxLayout(central_widget)
        
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.setSpacing(0)
        
        main_splitter = QSplitter(Qt.Orientation.Horizontal)
        main_splitter.setStyleSheet("""
            QSplitter::handle {
                background-color: #00FFFF;
                width: 3px;
            }
            QSplitter::handle:hover {
                background-color: #FFFF00;
            }
        """)
        
        left_panel = self.create_left_panel()
        center_panel = self.create_center_panel()
        right_panel = self.create_right_panel()
        
        main_splitter.addWidget(left_panel)
        main_splitter.addWidget(center_panel)
        main_splitter.addWidget(right_panel)
        main_splitter.setSizes([250, 1320, 330])
        
        main_layout.addWidget(main_splitter)
        
    def create_left_panel(self):
        panel = QGroupBox("🛰️ SATELLITES")
        panel.setStyleSheet("QGroupBox { color: cyan; font-weight: bold; font-size: 14px; }")
        layout = QVBoxLayout()
        
        self.category_combo = QComboBox()
        self.category_combo.addItems(['stations', 'weather', 'amateur', 'cubesat'])
        self.category_combo.setStyleSheet("""
            QComboBox {
                background-color: #161b22;
                color: white;
                padding: 6px;
                border: 2px solid cyan;
                font-size: 12px;
            }
        """)
        self.category_combo.currentTextChanged.connect(self.on_category_changed)
        
        layout.addWidget(QLabel("Catégorie:", styleSheet="color: white; font-size: 12px;"))
        layout.addWidget(self.category_combo)
        
        self.satellite_list = QListWidget()
        self.satellite_list.setStyleSheet("""
            QListWidget {
                background-color: #161b22;
                border: 2px solid cyan;
                color: white;
                font-size: 12px;
            }
            QListWidget::item {
                padding: 6px;
            }
            QListWidget::item:selected {
                background-color: #1f6feb;
            }
            QListWidget::item:hover {
                background-color: #264f78;
            }
        """)
        self.satellite_list.itemClicked.connect(self.on_satellite_selected)
        layout.addWidget(self.satellite_list)
        
        instructions = QLabel(
            "💡 Contrôles:\n"
            "• Molette = Zoom\n"
            "• Glisser = Déplacer\n"
            "• Flèche = Direction satellite\n"
            "• Vert = S'approche\n"
            "• Rose = S'éloigne"
        )
        instructions.setStyleSheet("""
            color: yellow; 
            font-size: 11px; 
            padding: 10px;
            background-color: #161b22;
            border: 1px solid yellow;
            border-radius: 5px;
        """)
        layout.addWidget(instructions)
        
        refresh_btn = QPushButton("🔄 Actualiser TLEs")
        refresh_btn.clicked.connect(self.load_satellites)
        refresh_btn.setStyleSheet("""
            QPushButton {
                background-color: #238636;
                color: white;
                border: none;
                padding: 12px;
                font-weight: bold;
                font-size: 13px;
            }
            QPushButton:hover {
                background-color: #2ea043;
            }
        """)
        layout.addWidget(refresh_btn)
        
        panel.setLayout(layout)
        return panel
        
    def create_center_panel(self):
        panel = QWidget()
        panel.setStyleSheet("background-color: #0a0a0a;")
        layout = QVBoxLayout()
        
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)
        
        self.earth_map = InteractiveEarthMapWidget(tracker=self.tracker)
        layout.addWidget(self.earth_map)
        
        controls_layout = QHBoxLayout()
        controls_layout.setContentsMargins(5, 2, 5, 2)
        
        reset_view_btn = QPushButton("🏠 Rennes")
        reset_view_btn.clicked.connect(self.reset_map_view)
        reset_view_btn.setStyleSheet("""
            QPushButton {
                background-color: #1f6feb;
                color: white;
                border: none;
                padding: 6px;
                font-weight: bold;
                font-size: 11px;
            }
            QPushButton:hover {
                background-color: #388bfd;
            }
        """)
        controls_layout.addWidget(reset_view_btn)
        
        world_view_btn = QPushButton("🌍 Monde")
        world_view_btn.clicked.connect(self.world_view)
        world_view_btn.setStyleSheet("""
            QPushButton {
                background-color: #238636;
                color: white;
                border: none;
                padding: 6px;
                font-weight: bold;
                font-size: 11px;
            }
            QPushButton:hover {
                background-color: #2ea043;
            }
        """)
        controls_layout.addWidget(world_view_btn)
        
        zoom_info = QLabel("🔄 Coordonnées actualisées automatiquement")
        zoom_info.setStyleSheet("color: lime; font-size: 10px; font-style: italic;")
        controls_layout.addWidget(zoom_info)
        
        layout.addLayout(controls_layout)
        
        panel.setLayout(layout)
        return panel
    
    def reset_map_view(self):
        self.earth_map.zoom_level = 2.5
        self.earth_map.center_lon = -1.6778
        self.earth_map.center_lat = 48.1173
        self.update_display()
    
    def world_view(self):
        self.earth_map.zoom_level = 1.0
        self.earth_map.center_lon = 0
        self.earth_map.center_lat = 20
        self.update_display()
        
    def create_right_panel(self):
        splitter = QSplitter(Qt.Orientation.Vertical)
        splitter.setStyleSheet("""
            QSplitter::handle {
                background-color: cyan;
                height: 3px;
            }
            QSplitter::handle:hover {
                background-color: yellow;
            }
        """)
        
        sky_group = QGroupBox("🔭 VUE DU CIEL")
        sky_group.setStyleSheet("QGroupBox { color: cyan; font-weight: bold; font-size: 13px; }")
        sky_layout = QVBoxLayout()
        sky_layout.setContentsMargins(2, 2, 2, 2)
        self.sky_view = SkyViewWidget()
        sky_layout.addWidget(self.sky_view)
        sky_group.setLayout(sky_layout)
        
        info_group = QGroupBox("ℹ️ INFORMATIONS")
        info_group.setStyleSheet("QGroupBox { color: cyan; font-weight: bold; font-size: 13px; }")
        info_layout = QVBoxLayout()
        
        refresh_info_btn = QPushButton("🔄 Actualiser Prédictions Complètes")
        refresh_info_btn.clicked.connect(self.update_info_panel_full)
        refresh_info_btn.setStyleSheet("""
            QPushButton {
                background-color: #1f6feb;
                color: white;
                border: none;
                padding: 8px;
                font-weight: bold;
                font-size: 11px;
            }
            QPushButton:hover {
                background-color: #388bfd;
            }
        """)
        info_layout.addWidget(refresh_info_btn)
        
        # TEXTE BEAUCOUP PLUS LISIBLE
        self.info_display = QTextEdit()
        self.info_display.setReadOnly(True)
        self.info_display.setStyleSheet("""
            QTextEdit {
                background-color: #000000;
                border: 2px solid cyan;
                color: #FFFFFF;
                font-family: 'Consolas', 'Monaco', 'Courier New', monospace;
                font-size: 13px;
                padding: 10px;
                line-height: 1.6;
            }
        """)
        
        # Améliorer encore plus la police
        font = QFont("Consolas", 13)
        font.setWeight(QFont.Weight.Medium)
        self.info_display.setFont(font)
        
        info_layout.addWidget(self.info_display)
        info_group.setLayout(info_layout)
        
        splitter.addWidget(sky_group)
        splitter.addWidget(info_group)
        splitter.setSizes([280, 520])
        
        return splitter
        
    def load_satellites(self):
        category = self.category_combo.currentText()
        
        self.satellite_list.clear()
        self.info_display.setText("⏳ Chargement des satellites...")
        
        satellites = self.tle_manager.download_tles(category)
        
        for sat in satellites[:20]:
            self.tracker.add_satellite(sat['name'], sat['line1'], sat['line2'])
            self.satellite_list.addItem(sat['name'])
        
        self.predictor = PassPredictor(self.tracker)
        self.info_display.setHtml(
            '<p style="color: lime; font-size: 14px; font-weight: bold;">'
            f'✓ Chargé {len(satellites[:20])} satellites depuis {category}'
            '</p>'
        )
        
    def on_category_changed(self, category):
        self.load_satellites()
        
    def on_satellite_selected(self, item):
        self.selected_satellite = item.text()
        self.update_display()
        self.update_info_panel_full()
        
    def update_display(self):
        """Mise à jour carte et vue du ciel"""
        if not self.selected_satellite:
            return
            
        position = self.tracker.get_position(self.selected_satellite)
        
        if not position:
            return
        
        all_positions = {self.selected_satellite: position}
        self.earth_map.update_satellites(all_positions, self.selected_satellite)
        self.sky_view.update_satellite_position(position)
    
    def update_coordinates_only(self):
        """NOUVEAU: Actualisation automatique SEULEMENT des coordonnées"""
        if not self.selected_satellite:
            return
        
        position = self.tracker.get_position(self.selected_satellite)
        
        if not position:
            return
        
        # Mettre à jour SEULEMENT la section coordonnées (pas tout le texte)
        current_text = self.info_display.toPlainText()
        
        # Si le texte contient déjà des infos, mettre à jour juste les coordonnées
        if "POSITION:" in current_text:
            # Extraire et reconstruire avec nouvelles coordonnées
            parts = current_text.split("VUE DEPUIS RENNES:")
            if len(parts) >= 2:
                # Garder tout après "VUE DEPUIS RENNES:"
                rest_of_text = "VUE DEPUIS RENNES:" + parts[1]
                
                # Créer nouvelle section position
                new_coords = f"""{'='*60}
  {self.selected_satellite}
{'='*60}

📍 POSITION ACTUELLE (actualisée automatiquement):
   Latitude:    {position['latitude']:>10.4f}°
   Longitude:   {position['longitude']:>10.4f}°
   Altitude:    {position['altitude_km']:>10.1f} km
   

"""
                self.info_display.setHtml(
                    f'<pre style="color: white; font-size: 13px; line-height: 1.6;">'
                    f'{new_coords}{rest_of_text}</pre>'
                )
    
    def update_info_panel_full(self):
        """Mise à jour COMPLÈTE du panneau info avec prédictions"""
        if not self.selected_satellite:
            return
            
        position = self.tracker.get_position(self.selected_satellite)
        
        if not position:
            return
        
        info = get_satellite_info(self.selected_satellite)
        
        def format_time_french(iso_string):
            utc_dt = datetime.fromisoformat(iso_string.replace('Z', '+00:00'))
            paris_dt = utc_dt.astimezone(self.paris_tz)
            tz_name = paris_dt.strftime('%Z')
            return paris_dt.strftime(f'%d/%m/%Y  %H:%M:%S {tz_name}')
        
        # Utiliser HTML pour meilleure lisibilité
        info_html = f"""
        <div style="font-family: Consolas, monospace; font-size: 13px; line-height: 1.8; color: white;">
        
        <p style="color: cyan; font-size: 16px; font-weight: bold; border-bottom: 2px solid cyan; padding-bottom: 5px;">
        {'='*60}<br>
        📡 {self.selected_satellite}<br>
        {'='*60}
        </p>
        
        <p style="color: lime; font-size: 14px; font-weight: bold;">
        📍 POSITION ACTUELLE:
        </p>
        <p style="color: white; margin-left: 20px;">
        Latitude:    <span style="color: yellow;">{position['latitude']:.4f}°</span><br>
        Longitude:   <span style="color: yellow;">{position['longitude']:.4f}°</span><br>
        Altitude:    <span style="color: yellow;">{position['altitude_km']:.1f} km</span>
        </p>
        
        <p style="color: cyan; font-size: 14px; font-weight: bold; margin-top: 15px;">
        👁️ VUE DEPUIS RENNES:
        </p>
        <p style="color: white; margin-left: 20px;">
        Azimut:      <span style="color: orange;">{position['azimuth']:.1f}°</span><br>
        Élévation:   <span style="color: orange;">{position['elevation']:.1f}°</span><br>
        Distance:    <span style="color: orange;">{position['distance_km']:.1f} km</span><br>
        Visible:     <span style="color: {'lime' if position['is_visible'] else 'red'}; font-weight: bold;">
                     {'OUI ✓' if position['is_visible'] else 'NON ✗'}</span>
        </p>
        
        <p style="color: yellow; font-size: 14px; font-weight: bold; margin-top: 15px;">
        ☀️ ENSOLEILLEMENT:
        </p>
        <p style="color: white; margin-left: 20px;">
        Au soleil:   <span style="color: {'yellow' if position.get('sunlit') else 'gray'};">
                     {'OUI' if position.get('sunlit') else 'NON'}</span>
        </p>
        
        <p style="color: cyan; font-size: 14px; font-weight: bold; margin-top: 15px; border-top: 1px solid cyan; padding-top: 10px;">
        ℹ️ INFORMATIONS SATELLITE:
        </p>
        <p style="color: white; margin-left: 20px;">
        Origine:     <span style="color: lightblue;">{info.get('origin', 'Inconnu')}</span><br>
        Usage:       <span style="color: lightblue;">{info.get('purpose', 'Inconnu')}</span><br>
        Type:        <span style="color: lightblue;">{info.get('type', 'Inconnu')}</span><br>
        Déploiement: <span style="color: lightblue;">{info.get('deployment', 'Inconnu')}</span>
        </p>
        
        <p style="color: lightgray; margin-left: 20px; margin-top: 10px; font-size: 12px;">
        {info.get('description', 'Aucune description disponible')}
        </p>
        """
        
        # Ajouter prédictions
        if self.predictor:
            passes = self.predictor.find_passes(self.selected_satellite, duration_days=3)
            if passes:
                best_pass = self.predictor.get_best_pass(passes)
                
                info_html += f"""
                <p style="color: magenta; font-size: 15px; font-weight: bold; margin-top: 20px; border-top: 2px solid magenta; padding-top: 10px;">
                🔮 PRÉDICTIONS (3 Jours) - HEURE FRANÇAISE
                </p>
                <p style="color: white; margin-left: 20px;">
                Total: <span style="color: yellow; font-weight: bold;">{len(passes)} passages</span> au-dessus de 10°
                </p>
                
                <p style="color: yellow; font-size: 14px; font-weight: bold; margin-top: 15px;">
                ⭐ MEILLEUR PASSAGE:
                </p>
                <p style="color: white; margin-left: 20px;">
                Lever:       <span style="color: lime;">{format_time_french(best_pass['rise_time_str'])}</span><br>
                Maximum:     <span style="color: lime;">{format_time_french(best_pass['max_time_str'])}</span><br>
                Élévation:   <span style="color: orange; font-weight: bold;">{best_pass['max_elevation']:.1f}°</span><br>
                Coucher:     <span style="color: lime;">{format_time_french(best_pass['set_time_str'])}</span><br>
                Durée:       <span style="color: cyan;">{best_pass['duration_str']}</span>
                </p>
                
                <p style="color: cyan; font-size: 13px; font-weight: bold; margin-top: 15px;">
                📋 PROCHAINS PASSAGES:
                </p>
                """
                
                for i, p in enumerate(passes[:5], 1):
                    info_html += f"""
                    <p style="color: white; margin-left: 20px; margin-top: 10px; border-left: 3px solid cyan; padding-left: 10px;">
                    <span style="color: yellow; font-weight: bold;">Passage #{i}:</span><br>
                    Lever:     <span style="color: lightgreen;">{format_time_french(p['rise_time_str'])}</span><br>
                    Maximum:   <span style="color: lightgreen;">{format_time_french(p['max_time_str'])}</span><br>
                    Élévation: <span style="color: orange;">{p['max_elevation']:.1f}°</span><br>
                    Durée:     <span style="color: cyan;">{p['duration_str']}</span>
                    </p>
                    """
            else:
                info_html += f"""
                <p style="color: red; font-size: 14px; margin-top: 20px;">
                ❌ Aucun passage au-dessus de 10° dans les 3 prochains jours.
                </p>
                """
        
        info_html += "</div>"
        
        self.info_display.setHtml(info_html)


def main():
    app = QApplication(sys.argv)
    app.setStyle('Fusion')
    
    window = MainWindow()
    window.show()
    
    sys.exit(app.exec())


if __name__ == "__main__":
    main()