import numpy as np

import matplotlib as mpl
import matplotlib.patches as mpat
import matplotlib.pyplot as plt
import matplotlib.colors as mcol


def pm_array_drawing_points(
        x_left=0., y_bottom=0.,
        row_height=0.5, col_width=1.,
        n_addr_bits=4, n_word_bits=8,  # N.B. could come from the device
        cell_slant_tangent=0.42,  # about 30 degrees
        ):
    """
    Calculate point locations of inner (hexagon) and outer (rhombus) polygons
    for an ideal PM cell.
    """
    # work out cell coordinates
    cell_y_scale = row_height / col_width

    def cell_coord_transform(xys, slant_right=True):
        xys = np.asarray(xys)
        xs, ys = xys[..., 0], xys[..., 1]
        xs = xs + (1 if slant_right else -1) * ys * cell_slant_tangent
        ys *= cell_y_scale
        result = np.stack([xs, ys])
        result = result.transpose()
        return result

    def cell_drawing_points(slant_right=True):
        # Calculate outer boundary and hole points in cell-scale coordinates.
        # This accounts for the slant and relative vertical scaling, but not
        # overall scaling (=horizontal size factor) or cell position offset.
        bl, br, tr, tl = 0, 1, 2, 3
        outer_margin_xys = [(0., 0), (1, 0), (1, 1), (0, 1)]
        inner_margin_xys = [(0.1, 0.1), (0.9, 0.1), (0.9, 0.9), (0.1, 0.9)]
        centre_left_pt = (0.1, 0.5)
        centre_right_pt = (0.9, 0.5)
        outer_margin_xys = cell_coord_transform(outer_margin_xys, slant_right=slant_right)
        inner_margin_xys = cell_coord_transform(inner_margin_xys, slant_right=slant_right)
        centre_left_pt, = cell_coord_transform([centre_left_pt], slant_right=slant_right)
        centre_right_pt, = cell_coord_transform([centre_right_pt], slant_right=slant_right)
        # make the hexagon hole points, which depend on the slant.
        hexagon_pts = np.array([
            inner_margin_xys[bl],
            inner_margin_xys[br],
            centre_right_pt,
            inner_margin_xys[tr],
            inner_margin_xys[tl],
            centre_left_pt])
        if slant_right:
            hexagon_pts[0][0] = centre_left_pt[0]  # shift BL right
            hexagon_pts[3][0] = centre_right_pt[0] # shift TR left
        else:
            hexagon_pts[1][0] = centre_right_pt[0]  # shift BR left
            hexagon_pts[4][0] = centre_left_pt[0]  # shift TL right
        return outer_margin_xys, hexagon_pts

    def all_cells_outers_inners():
        cell_outer_rhs, cell_inner_rhs = cell_drawing_points(slant_right=True)
        cell_outer_lhs, cell_inner_lhs = cell_drawing_points(slant_right=False)
        n_outer = cell_outer_rhs.shape[0]
        n_inner = cell_inner_rhs.shape[0]

        # Replicate these for each row with offsets
        n_words = 2 ** n_addr_bits

        # Target: (outers/inners)[n_words, n_word_bits, (n_outer/n_inner), 2)
        all_outers = np.zeros((n_words, n_word_bits, n_outer, 2))
        all_inners = np.zeros((n_words, n_word_bits, n_inner, 2))

        row_offsets = (row_height * np.arange(n_words)).reshape(
            (n_words, 1, 1, 1))
        col_offsets = (col_width * np.arange(n_word_bits)).reshape(
            (1, n_word_bits, 1, 1))

        for arr in (all_outers, all_inners):
            arr[..., 0:1] += col_offsets
            arr[..., 1:2] += row_offsets

        # The odd rows, which lean left, need shifting right to join up.
        x_stagger = cell_outer_rhs[-1, 0] - cell_outer_rhs[0, 0]  # X(end-start)
        all_outers[1::2, ..., 0] += x_stagger
        all_inners[1::2, ..., 0] += x_stagger

        # Add the bottom-left location offset to all points.
        for points in all_outers, all_inners:
            points[..., 0] += x_left
            points[..., 1] += y_bottom

        # Add the relevant polygon point locations to all points.
        all_outers[::2, ...] += cell_outer_rhs
        all_outers[1::2, ...] += cell_outer_lhs
        all_inners[::2, ...] += cell_inner_rhs
        all_inners[1::2, ...] += cell_inner_lhs

        return all_outers, all_inners

    return all_cells_outers_inners()

def pm_array_graphics(cell_points_outers_inners, axes=None):
    # Create and return graphical elements for the PM, from given path points.
    outers_points, inners_points = cell_points_outers_inners

    if axes is None:
        axes = plt.axes()

    # Extract dimensions of the arrays
    n_words, n_word_bits, n_outers = outers_points.shape[:3]
    assert inners_points[:,:,0,:].shape == outers_points[:,:,0,:].shape
    n_inners = inners_points.shape[2]

    # Construct element control (settings) types.
    cell_inner_color = mcol.hex2color('#c0f8ff')
    hole_inner_color_0 = mcol.hex2color('#f8fcff')
    hole_inner_color_1 = mcol.hex2color('#c0a090')
    data = np.random.uniform(size=(n_words, n_word_bits))
    data = (data > 0.7).astype(bool)
    elements = {}
    for i_row in range(n_words):
        for i_col in range(n_word_bits):
            # cell_inner_color = (float(i_row) / n_words, float(i_col) / n_word_bits, 0.0)
            cell_name = 'cell_{:03d}_{:03d}'.format(i_row, i_col)

            outer_name = 'outerpoly__{}'.format(cell_name)
            outerpoly = mpat.Polygon(
                outers_points[i_row, i_col],
                closed=True, edgecolor='black', linewidth=1.5,
                facecolor=cell_inner_color, zorder=2)
            elements[outer_name] = outerpoly

            inner_name = 'innerpoly__{}'.format(cell_name)
            bit_color = (hole_inner_color_1
                         if data[i_row, i_col]
                         else hole_inner_color_0)
            innerpoly = mpat.Polygon(
                inners_points[i_row, i_col],
                closed=True, edgecolor='black', linewidth=1.5,
                facecolor=bit_color, zorder=4)
            elements[inner_name] = innerpoly

            for el in (outerpoly, innerpoly):
                axes.add_patch(el)

    return elements


def adjust_row(elements, i_row, y_stretch=1.4, linewidth=2.5, zorder_inc=10):
    cell_row_name = 'cell_{:03d}'.format(i_row)
    for el_name, poly in elements.items():
        if cell_row_name in el_name:
            pts = poly.get_xy()
            base_y = pts[0, 1]
            pts[..., 1] = base_y + y_stretch * (pts[..., 1] - base_y)
            poly.set_linewidth(linewidth)
            z = poly.get_zorder()
            poly.set_zorder(z + zorder_inc)

if __name__ == '__main__':
    outers_inners = pm_array_drawing_points(n_addr_bits=6)
    plt.figure(figsize=(16,10))
    ax = plt.axes()
    elems = pm_array_graphics(outers_inners, axes=ax)
    n_rows = outers_inners[0].shape[0]
    # ax.autoscale()
    # x0, x1 = ax.get_xlim()
    # dx = (x1 - x0) * 0.1
    # ax.set_xlim((x0-dx, x1+dx))
    # y0, y1 = ax.get_ylim()
    # dy = (y1 - y0) * 0.1
    # ax.set_ylim((y0-dy, y1+dy))
    ax.set_xlim(-12, 24)
    ax.set_ylim(-2, 34)

    plt.pause(0.03)

    for i_try in range(10):
        i_row_select = int(np.round(np.random.uniform(0, n_rows + 1)))
    # for i_row_select in range(n_rows):
        fracts = np.linspace(1.0, 1.6, 10)
        fracts = np.concatenate([fracts, fracts[::-1]])
        for fract in fracts:
            # tweak row UP then DOWN
            adjust_row(elements=elems, i_row=i_row_select,
                       y_stretch=fract,
                       linewidth=3.5, zorder_inc=10)
            plt.pause(0.03)
            # "untweak"
            # N.B. don't need to revert every time, but this is simple
            adjust_row(elements=elems, i_row=i_row_select,
                       y_stretch=1.0/fract,
                       linewidth=1.5, zorder_inc=-10)

    print('!!DONE!!')
    plt.pause(0.01)
    plt.show()
