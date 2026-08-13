# S.P.E.C.T.R.E. Engine - Licensed under AGPL-3.0
# Copyright (c) 2026 M. Sami Furqan. All rights reserved.
# See LICENSE file for full terms.

"""
styles — Core theme and styling package.
"""

from styles.qss import build_qss
from styles.pyqtgraph_theme import apply_pyqtgraph_theme, make_plot_widget

__all__ = ["build_qss", "apply_pyqtgraph_theme", "make_plot_widget"]
