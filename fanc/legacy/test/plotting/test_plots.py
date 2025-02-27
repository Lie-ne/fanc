from __future__ import division
import matplotlib as mpl
mpl.use('Agg')
import matplotlib.pyplot as plt
import fanc
import fanc.plotting as kplot
import os.path
import pytest
import numpy as np
import pybedtools as pbt

def abs_ax_aspect(ax):
    bbox = ax.get_position()
    fig = ax.figure
    aspect = (bbox.height*fig.get_figheight())/(bbox.width*fig.get_figwidth())
    return aspect

@pytest.mark.plotting
class TestHicPlot:
    def setup_method(self, method):
        self.hic = fanc.load(fanc.example_data["hic"], mode="r")
        self.hic_matrix = self.hic[:]
        self.hic_matrix[10, :] = 0
        self.hic_matrix[:, 10] = 0

    def teardown_method(self, method):
        self.hic.close()

    @pytest.mark.parametrize("norm", ["lin", "log"])
    @pytest.mark.parametrize("max_dist", [None, 400000])
    @pytest.mark.parametrize("colormap", ["viridis", mpl.cm.get_cmap("Reds")])
    @pytest.mark.parametrize("colorbar", [True, False])
    @pytest.mark.parametrize("blend_zero", [True, False])
    @pytest.mark.parametrize("aspect", [.345])
    @pytest.mark.parametrize("vrange", [(None, .3), (.01, .4)])
    @pytest.mark.parametrize("proportional", [True, False])
    @pytest.mark.parametrize("crange", [(77390001, 78600000)])
    @pytest.mark.parametrize("unmappable_color", [".345"])
    def test_hicplot_inputs(self, norm, max_dist, colormap, colorbar,
                            blend_zero, aspect, vrange, crange, unmappable_color,
                            proportional):
        start, end = crange
        vmin, vmax = vrange
        hplot = kplot.HicPlot(hic_data=self.hic_matrix, title="quark", norm=norm, vmin=vmin, vmax=vmax,
                              max_dist=max_dist, colormap=colormap, show_colorbar=colorbar,
                              blend_zero=blend_zero, aspect=aspect, unmappable_color=unmappable_color,
                              proportional=proportional)
        gfig = kplot.GenomicFigure([hplot])
        selector = "chr11:{}-{}".format(start, end)
        fig, axes = gfig.plot(selector)
        assert axes[0].get_title() == "quark"
        norm_values = {"lin": mpl.colors.Normalize,
                       "log": mpl.colors.LogNorm}
        assert isinstance(hplot.collection.norm, norm_values[norm])
        assert axes[0].get_xlim() == (start, end)
        if vmin is not None:
            assert hplot.collection.norm.vmin == vmin
        if vmax is not None:
            assert hplot.collection.norm.vmax == vmax
        if proportional:
            if max_dist is None:
                assert abs_ax_aspect(hplot.ax) == pytest.approx(.5)
            else:
                rl = end - start
                assert abs_ax_aspect(hplot.ax) == pytest.approx(.5*min(max_dist, rl)/rl)
        else:
            assert abs_ax_aspect(hplot.ax) == aspect
        colorbar_values = {True: mpl.colorbar.Colorbar,
                           False: type(None)}
        assert isinstance(hplot.colorbar, colorbar_values[colorbar])
        hic_matrix = self.hic_matrix[selector, selector]
        zero_mask = np.isclose(hic_matrix, 0.)
        unmap_mask = np.all(zero_mask, axis=0)
        unmap_mask = np.logical_or(unmap_mask, unmap_mask[:, np.newaxis])
        if unmappable_color is not None:
            unmap_color = mpl.colors.colorConverter.to_rgba(unmappable_color)
            assert np.all(np.isclose(hplot.collection.get_facecolors()[unmap_mask.T.ravel(), :], unmap_color))
        # blend zero only really makes sense with log normalization, with 
        # linear normalization 0 values map to the first colormap value anyway
        if norm == "log":
            exp_zero = np.logical_and(zero_mask, np.logical_not(unmap_mask))
            if np.sum(exp_zero) > 0:
                zero_value = hplot.colormap(0)
                zero_blended = np.all(np.isclose(hplot.collection.get_facecolors()[exp_zero.T.ravel(), :], zero_value))
                assert blend_zero == zero_blended
        plt.close(fig)

    @pytest.mark.parametrize("norm", ["lin", "log"])
    @pytest.mark.parametrize("colormap", ["viridis", mpl.cm.get_cmap("Reds")])
    @pytest.mark.parametrize("colorbar", [True, False])
    @pytest.mark.parametrize("blend_zero", [True, False])
    @pytest.mark.parametrize("aspect", [.345])
    @pytest.mark.parametrize("vrange", [(None, .3), (.01, .4)])
    @pytest.mark.parametrize("crange", [(77390001, 78600000)])
    @pytest.mark.parametrize("unmappable_color", [".345"])
    @pytest.mark.parametrize("adjust_range", [True, False])
    def test_hicplot2d_inputs(self, norm, colormap, colorbar,
                              blend_zero, aspect, vrange, crange, unmappable_color,
                              adjust_range):
        start, end = crange
        vmin, vmax = vrange
        hplot = kplot.HicPlot2D(hic_data=self.hic_matrix, title="quark", norm=norm, vmin=vmin, vmax=vmax,
                                colormap=colormap, show_colorbar=colorbar, adjust_range=adjust_range,
                                blend_zero=blend_zero, aspect=aspect, unmappable_color=unmappable_color)
        gfig = kplot.GenomicFigure([hplot])
        selector = "chr11:{}-{}".format(start, end)
        fig, axes = gfig.plot(selector)
        assert axes[0].get_title() == "quark"
        norm_values = {"lin": mpl.colors.Normalize,
                       "log": mpl.colors.LogNorm}
        assert isinstance(hplot.norm, norm_values[norm])
        assert axes[0].get_xlim() == (start, end)
        assert axes[0].get_ylim() == (start, end)
        if vmin is not None:
            assert hplot.im.norm.vmin == vmin
        if vmax is not None:
            assert hplot.im.norm.vmax == vmax
        assert hplot.aspect == aspect
        assert abs_ax_aspect(axes[0]) == pytest.approx(aspect)
        colorbar_values = {True: mpl.colorbar.Colorbar,
                           False: type(None)}
        assert isinstance(hplot.colorbar, colorbar_values[colorbar])
        hic_matrix = self.hic_matrix[selector, selector]
        zero_mask = np.isclose(hic_matrix, 0.)
        unmap_mask = np.all(zero_mask, axis=0)
        unmap_mask = np.logical_or(unmap_mask, unmap_mask[:, np.newaxis])
        if unmappable_color is not None:
            unmap_color = mpl.colors.colorConverter.to_rgba(unmappable_color)
            assert np.all(np.isclose(hplot.im.get_array()[unmap_mask, :], unmap_color))
        # blend zero only really makes sense with log normalization, with
        # linear normalization 0 values map to the first colormap value anyway
        if norm == "log":
            exp_zero = np.logical_and(zero_mask, np.logical_not(unmap_mask))
            if np.sum(exp_zero) > 0:
                zero_value = hplot.colormap(0)
                zero_blended = np.all(np.isclose(hplot.im.get_array()[exp_zero, :], zero_value))
                assert blend_zero == zero_blended
        plt.close(fig)

    @pytest.mark.parametrize("n_hic", [1, 3])
    @pytest.mark.parametrize("yscale", ["linear", "log"])
    @pytest.mark.parametrize("ylim", [(1, 10), (None, 5)])
    @pytest.mark.parametrize("slice_region", ["chr11:77800000-77850000"])
    @pytest.mark.parametrize("names", [None, True])
    def test_hicsliceplot(self, n_hic, yscale, ylim, slice_region, names):
        hic_data = self.hic_matrix if n_hic == 1 else [self.hic_matrix]*n_hic
        names_passed = None if names is None else ["hic{}".format(i) for i in range(n_hic)]
        splot = kplot.HicSlicePlot(hic_data, slice_region, names=names_passed,
                                   ylim=ylim, yscale=yscale)
        gfig = kplot.GenomicFigure([splot])
        selector = "chr11:{}-{}".format(77400000, 78600000)
        fig, axes = gfig.plot(selector)
        assert axes[0].get_yscale() == yscale
        for a, b in zip(ylim, axes[0].get_ylim()):
            assert a is None or a == pytest.approx(b)
        if names is not None:
            assert all(l.get_label() == n_p for l, n_p in zip(axes[0].get_lines(), names_passed))
        plt.close(fig)

    @pytest.mark.parametrize("width", [3.7])
    @pytest.mark.parametrize("cax_width", [.42])
    @pytest.mark.parametrize("ticks_last", [True, False])
    @pytest.mark.parametrize("draw_labels", [True, False])
    @pytest.mark.parametrize("draw_ticks", [True, False])
    @pytest.mark.parametrize("draw_x_axis", [True, False])
    def test_tick_removal(self, width, cax_width, ticks_last, draw_labels, draw_ticks, draw_x_axis):
        splot = kplot.HicSlicePlot(self.hic_matrix, "chr11:77800000-77850000")
        hplot = kplot.HicPlot2D(hic_data=self.hic_matrix,
                                draw_ticks=draw_ticks, draw_tick_labels=draw_labels,
                                draw_x_axis=draw_x_axis)
        hplot2 = kplot.HicPlot(hic_data=self.hic_matrix)
        gfig = kplot.GenomicFigure([splot, hplot, hplot2],
                                   width=width, ticks_last=ticks_last, cax_width=cax_width)
        selector = "chr11:{}-{}".format(77400000, 78600000)
        fig, axes = gfig.plot(selector)
        # hplot2 should always have labels and lines
        assert all(l.get_visible() for l in axes[2].get_xticklabels()) and all(l.get_visible() for l in axes[2].xaxis.get_majorticklines())
        # hplot labels are affected by the three draw parameters
        should_have_labels = draw_x_axis and draw_labels and (not ticks_last)
        assert should_have_labels == all(l.get_visible() for l in axes[1].get_xticklabels())
        # But it should have tick lines even when ticks_last=True
        should_have_ticks = draw_x_axis and draw_ticks
        assert should_have_ticks == all(l.get_visible() for l in axes[1].xaxis.get_majorticklines())
        assert should_have_ticks == all(l.get_visible() for l in axes[1].xaxis.get_minorticklines())
        # splot should always have ticks and lines
        assert all(l.get_visible() for l in axes[0].xaxis.get_majorticklines())
        assert all(l.get_visible() for l in axes[0].xaxis.get_minorticklines())
        # splot only labels if ticks_last=False
        assert ticks_last != all(l.get_visible() for l in axes[0].get_xticklabels())
        bbox = axes[0].get_position()
        figsize = fig.get_size_inches()
        assert bbox.width*figsize[0] == pytest.approx(width)
        bbox = hplot.cax.get_position()
        assert bbox.width*figsize[0] == pytest.approx(cax_width)
        plt.close(fig)


@pytest.mark.plotting
class TestPlots:
    def setup_method(self, method):
        self.bigwig_path = fanc.example_data["chip_bigwig"]
        self.pyBigWig = pytest.importorskip("pyBigWig")
        self.bigwig = self.pyBigWig.open(fanc.example_data["chip_bigwig"])
        self.bedgraph_path = fanc.example_data["chip_bedgraph"]
        self.gtf_path = fanc.example_data["gene_gtf"]
        self.peak_path = fanc.example_data["chip_peak_bed"]
        self.bedgraph_list = [(x.chrom, x.start, x.end, x.score) for x in pbt.BedTool(self.bedgraph_path)]

    def teardown_method(self, method):
        self.bigwig.close()

    @pytest.mark.filterwarnings("ignore:BigWigPlot")
    @pytest.mark.parametrize("file", ["bigwig", "bedgraph"])
    @pytest.mark.parametrize("crange", [(77497000, 77500000)])
    @pytest.mark.parametrize("n_bw", [1, 3])
    @pytest.mark.parametrize("ylim", [(1, 10), (None, 5)])
    @pytest.mark.parametrize("yscale", ["linear", "log"])
    @pytest.mark.parametrize("names", [None, True])
    @pytest.mark.parametrize("bin_size", [50, 2])
    def test_bigwig_plot(self, file, crange, n_bw, ylim, yscale, names, bin_size):
        path = getattr(self, "{}_path".format(file))
        bw_data = path if n_bw == 1 else [path]*n_bw
        names_passed = None if names is None else ["bw{}".format(i) for i in range(n_bw)]
        bplot = kplot.BigWigPlot(bw_data, names=names_passed, bin_size=bin_size,
                                  ylim=ylim, yscale=yscale)
        gfig = kplot.GenomicFigure([bplot])
        fig, axes = gfig.plot("chr11:{}-{}".format(*crange))
        assert axes[0].get_yscale() == yscale
        for a, b in zip(ylim, axes[0].get_ylim()):
            assert a is None or a == pytest.approx(b)
        if names is not None:
            assert all(l.get_label() == n_p for l, n_p in zip(axes[0].get_lines(), names_passed))
        # Should figure out exactly how many data points I expect instead...
        assert all(len(l.get_ydata()) > 5 for l in axes[0].get_lines())
        plt.close(fig)

    @pytest.mark.parametrize("collapse", [True, False])
    @pytest.mark.parametrize("squash_group", [(True, "gene_id"), (False, "transcript_id")])
    def test_geneplot(self, collapse, squash_group):
        squash, group_by = squash_group
        gplot = kplot.GenePlot(self.gtf_path,
                               collapse=collapse,
                               squash=squash,
                               group_by=group_by)
        gfig = kplot.GenomicFigure([gplot])
        selector = "chr11:77490000-77500000"
        fig, axes = gfig.plot(selector)
        assert len(axes[0].patches) == (19 if squash else 49)
        plt.close(fig)

    @pytest.mark.parametrize("crange", [(77497000, 77500000)])
    def test_highlight_plot(self, crange):
        bplot = kplot.BigWigPlot(self.bigwig_path)
        gplot = kplot.GenePlot(self.gtf_path)
        high = kplot.HighlightAnnotation(self.peak_path)
        gfig = kplot.GenomicFigure([bplot, gplot, high])
        fig, axes = gfig.plot("chr11:{}-{}".format(*crange))
        p1 = high.patches[0]
        assert gplot.ax.transAxes.transform((0, 0))[1] == pytest.approx(p1._transform.transform(p1.get_xy())[1])

    @pytest.mark.parametrize("crange", [(77497000, 77500000)])
    def test_invert_x_independent_x(self, crange):
        offset = 150000
        bplot = kplot.BigWigPlot(self.bigwig_path)
        gplot = kplot.GenePlot(self.gtf_path)
        gfig = kplot.GenomicFigure([bplot, gplot], invert_x=True)
        fig, axes = gfig.plot("chr11:{}-{}".format(*crange))
        ax_lim = axes[0].get_xlim()
        assert (ax_lim[0] > ax_lim[1] for ax_lim in (a.get_xlim() for a in axes))
        bplot = kplot.BigWigPlot(self.bigwig_path, invert_x=True)
        gplot = kplot.GenePlot(self.gtf_path)
        gfig = kplot.GenomicFigure([bplot, gplot], independent_x=True)
        fig, axes = gfig.plot(["chr11:{}-{}".format(*crange), "chr11:{}-{}".format(crange[0] + offset, crange[1] + offset)])
        ax_lim = [ax.get_xlim() for ax in axes]
        abs_tol = 10000
        assert ax_lim[0][0] == pytest.approx(crange[1], abs=abs_tol)
        assert ax_lim[0][1] == pytest.approx(crange[0], abs=abs_tol)
        assert ax_lim[1][0] == pytest.approx(crange[1] + offset, abs=abs_tol)
        assert ax_lim[1][1] == pytest.approx(crange[0] + offset, abs=abs_tol)

    @pytest.mark.parametrize("data_source", [("bigwig",), ("bedgraph_list",), ("bigwig_path",), ("bigwig", "bigwig_path"), ("bedgraph_path", "bedgraph_list")])
    @pytest.mark.parametrize("bin_size", [None, 100])
    def test_lineplot(self, data_source, bin_size):
        data = [getattr(self, d) for d in data_source]
        if len(data) == 1:
            data = data[0]
        lplot = kplot.LinePlot(data, bin_size=bin_size)
        gfig = kplot.GenomicFigure([lplot])
        fig, axes = gfig.plot("chr11:77497000-77500000")
        assert all(len(l.get_ydata()) > 5 for l in axes[0].get_lines())

    @pytest.mark.parametrize("data_source", [{"a": "bigwig"}, {"a": "bedgraph_list", "b": "bigwig_path"}])
    @pytest.mark.parametrize("bin_size", [None])
    def test_lineplot_dict_input(self, data_source, bin_size):
        data = {k: getattr(self, d) for k, d in data_source.items()}
        lplot = kplot.LinePlot(data, bin_size=bin_size)
        gfig = kplot.GenomicFigure([lplot])
        fig, axes = gfig.plot("chr11:77497000-77500000")
        assert all(len(l.get_ydata()) > 5 for a in axes for l in a.get_lines())
        assert all(l.get_label() == n_p for l, n_p in zip(axes[0].get_lines(), data.keys()))

    def test_genomic_feature_plot(self):
        gfplot = kplot.GenomicFeaturePlot(self.peak_path, label_field=8)
        gfig = kplot.GenomicFigure([gfplot])
        fig, axes = gfig.plot("chr11:77497000-77500000")
        assert len(axes[0].patches) == 2

    @pytest.mark.parametrize("attribute", ["score", 6])
    def test_genomic_feature_score_plot(self, attribute):
        gfsplot = kplot.GenomicFeatureScorePlot(self.peak_path, attribute=attribute)
        gfig = kplot.GenomicFigure([gfsplot])
        fig, axes = gfig.plot("chr11:77497000-77500000")
        assert len(axes[0].patches) == 2
