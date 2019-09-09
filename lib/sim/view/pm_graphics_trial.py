import numpy as np

import matplotlib as mpl
import matplotlib.patches as mpat
import matplotlib.pyplot as plt

#
# OLD: stuff relating to drawing a address-distributor array
#
# top_inlet_height=3.,
# btm_control_height=6.,
# control_width=4.,
# # controls are: sel, cancel, read
# # shown at bottom, colour coded with flash ?
# control_colours_base={'select': 'brown',
#                       'cancel': 'blue',
#                       'read': 'red'}):
# address selection area width
# each-bit, w:n = 0:0, 1:1, 2:1.5, 3:2, 4:2.5 etc ?
# ~ 0.5*(n + 1) ##except 0:0.5
# all-bits, w:n = 0:0, 1:1, 2:2.5, 3:4.5, 4:7
# ~ sum{1,n: 0.5*(n+1)} = 0.5 * n*0.5*(2 + (n+1))
# ~ 0.25 * n(n + 3)
# ~ 0.75*n + 0.25*n^2
# 0:0, 1:1, 2:2.5, 3:
# w_addr = 0.25 * n_addr_bits * (n_addr_bits + 3)
#    # making upper rows proportionally wider
#     n_rows = 2 ** n_addr_bits
#     w_addrs = np.arange(0, n_addr_bits + 1, dtype=float)
#     w_addrs = 0.25 * w_addrs * (w_addrs + 3)


# x_addrs = x_lhs_main - w_addrs  # 0-->x, 1-->(x-w1), n-->(x - w1 - ... wN)

def pm_array_drawing_points(
        x_lhs_rom, y_btm_rom,
        row_height=0.5, col_width=1.,
        n_addr_bits=4, n_word_bits=8,  # N.B. could come from the device
        # cell_slant_right=True,  # TODO: remove this when plotting rows
        cell_slant_tangent=0.42,  # about 30 degrees
        ):

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

        all_outers = all_outers + row_offsets + col_offsets
        all_inners = all_inners + row_offsets + col_offsets
        all_outers[::2, :, :, :] += cell_outer_rhs
        all_outers[1::2, :, :, :] += cell_outer_lhs
        all_inners[::2, :, :, :] += cell_inner_rhs
        all_inners[1::2, :, :, :] += cell_inner_lhs
        return all_outers, all_inners

    return all_cells_outers_inners()


if __name__ == '__main__':
    # def plt_one(slant_right):
    #     outer, inner = pm_array_drawing_points(0., 0., cell_slant_right=slant_right)
    #     border = mpat.Polygon(outer, closed=True, edgecolor='red', facecolor=None)
    #     hole = mpat.Polygon(inner, closed=True, edgecolor='black', facecolor='green')
    #     ax = plt.axes()
    #     ax.add_patch(border)
    #     ax.add_patch(hole)
    #     ax.autoscale()
    #     plt.show()
    #
    # for slant_right in (True, False):
    #     plt_one(slant_right)
    outers, inners = pm_array_drawing_points(0., 0.)
    print outers