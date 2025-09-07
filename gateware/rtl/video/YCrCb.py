# ycbcr2rgb

from migen import *

from litex.soc.interconnect.stream import *

def saturate(i, o, minimum, maximum):
    return [
        If(i > maximum,
            o.eq(maximum)
        ).Elif(i < minimum,
            o.eq(minimum)
        ).Else(
            o.eq(i)
        )
    ]


def coef(value, cw=None):
    return int(value * 2**cw) if cw is not None else value

def rgb_layout(dw):
    return [("r", dw), ("g", dw), ("b", dw)]

def rgb16f_layout(dw):
    return [("rf", dw), ("gf", dw), ("bf", dw)]

def ycbcr444_layout(dw):
    return [("y", dw), ("cb", dw), ("cr", dw)]

def ycbcr422_layout(dw):
    return [("y", dw), ("cb_cr", dw)]

def pix_layout(dw):
    return [("pix", dw)]

def pixf_layout(dw):
    return [("pixf", dw)]

def ycbcr2rgb_coefs(dw, cw=None):
    ca = 0.1819
    cb = 0.0618
    cc = 0.5512
    cd = 0.6495
    xcoef_w = None if cw is None else cw-2
    return {
        "ca" : coef(ca, cw),
        "cb" : coef(cb, cw),
        "cc" : coef(cc, cw),
        "cd" : coef(cd, cw),
        "yoffset" : 2**(dw-4),
        "coffset" : 2**(dw-1),
        "ymax" : 2**dw-1,
        "cmax" : 2**dw-1,
        "ymin" : 0,
        "cmin" : 0,
        "acoef": coef(1/cd, xcoef_w),
        "bcoef": coef(-cb/(cc*(1-ca-cb)), xcoef_w),
        "ccoef": coef(-ca/(cd*(1-ca-cb)), xcoef_w),
        "dcoef": coef(1/cc, xcoef_w)
    }


@CEInserter()
class YCbCr2RGBDatapath(Module):
    latency = 4

    def __init__(self, ycbcr_w, rgb_w, coef_w):
        self.sink = sink = Record(ycbcr444_layout(ycbcr_w))
        self.source = source = Record(rgb_layout(rgb_w))

        # # #

        coefs = ycbcr2rgb_coefs(rgb_w, coef_w)

        # delay ycbcr signals
        ycbcr_delayed = [sink]
        for i in range(self.latency):
            ycbcr_n = Record(ycbcr444_layout(ycbcr_w))
            for name in ["y", "cb", "cr"]:
                self.sync += getattr(ycbcr_n, name).eq(getattr(ycbcr_delayed[-1], name))
            ycbcr_delayed.append(ycbcr_n)

        # Hardware implementation:
        # (Equation from XAPP931)
        #  r = y - yoffset + (cr - coffset)*acoef
        #  b = y - yoffset + (cb - coffset)*bcoef + (cr - coffset)*ccoef
        #  g = y - yoffset + (cb - coffset)*dcoef

        # stage 1
        # (cr - coffset) & (cr - coffset)
        cb_minus_coffset = Signal((ycbcr_w + 1, True))
        cr_minus_coffset = Signal((ycbcr_w + 1, True))
        self.sync += [
            cb_minus_coffset.eq(sink.cb - coefs["coffset"]),
            cr_minus_coffset.eq(sink.cr - coefs["coffset"])
        ]

        # stage 2
        # (y - yoffset)
        # (cr - coffset)*acoef
        # (cb - coffset)*bcoef
        # (cr - coffset)*ccoef
        # (cb - coffset)*dcoef
        y_minus_yoffset = Signal((ycbcr_w + 4, True))
        cr_minus_coffset_mult_acoef = Signal((ycbcr_w + coef_w + 4, True))
        cb_minus_coffset_mult_bcoef = Signal((ycbcr_w + coef_w + 4, True))
        cr_minus_coffset_mult_ccoef = Signal((ycbcr_w + coef_w + 4, True))
        cb_minus_coffset_mult_dcoef = Signal((ycbcr_w + coef_w + 4, True))
        self.sync += [
            y_minus_yoffset.eq(ycbcr_delayed[1].y - coefs["yoffset"]),
            cr_minus_coffset_mult_acoef.eq(cr_minus_coffset * Signal((ycbcr_w, True), reset=coefs["acoef"]  )),
            cb_minus_coffset_mult_bcoef.eq(cb_minus_coffset * Signal((ycbcr_w, True), reset=coefs["bcoef"]  )),
            cr_minus_coffset_mult_ccoef.eq(cr_minus_coffset * Signal((ycbcr_w, True), reset=coefs["ccoef"]  )),
            cb_minus_coffset_mult_dcoef.eq(cb_minus_coffset * Signal((ycbcr_w, True), reset=coefs["dcoef"]  ))
        ]

        # stage 3
        # line addition for all component
        r = Signal((ycbcr_w + 4, True))
        g = Signal((ycbcr_w + 4, True))
        b = Signal((ycbcr_w + 4, True))
        self.sync += [
            r.eq(y_minus_yoffset + cr_minus_coffset_mult_acoef[coef_w-2:]),
            g.eq(y_minus_yoffset + cb_minus_coffset_mult_bcoef[coef_w-2:] +
                                   cr_minus_coffset_mult_ccoef[coef_w-2:]),
            b.eq(y_minus_yoffset + cb_minus_coffset_mult_dcoef[coef_w-2:])
        ]

        # stage 4
        # saturate
        self.sync += [
            saturate(r, source.r, 0, 2**rgb_w-1),
            saturate(g, source.g, 0, 2**rgb_w-1),
            saturate(b, source.b, 0, 2**rgb_w-1)
        ]


class YCbCr2RGB(PipelinedActor, Module):
    def __init__(self, ycbcr_w=8, rgb_w=8, coef_w=8):
        self.sink = sink = Endpoint(EndpointDescription(ycbcr444_layout(ycbcr_w)))
        self.source = source = Endpoint(EndpointDescription(rgb_layout(rgb_w)))

        # # #

        self.submodules.datapath = YCbCr2RGBDatapath(ycbcr_w, rgb_w, coef_w)
        PipelinedActor.__init__(self, self.datapath.latency)
        self.comb += self.datapath.ce.eq(self.pipe_ce)
        for name in ["y", "cb", "cr"]:
            self.comb += getattr(self.datapath.sink, name).eq(getattr(sink, name))
        for name in ["r", "g", "b"]:
            self.comb += getattr(source, name).eq(getattr(self.datapath.source, name))




@ResetInserter()
class YCbCr422to444(Module):
    """YCbCr 422 to 444

      Input:                    Output:
        Y0    Y1    Y2   Y3       Y0     Y1   Y2   Y3
      Cb01  Cr01  Cb23 Cr23  --> Cb01  Cb01 Cb23 Cb23
                                 Cr01  Cr01 Cr23 Cr23
    """
    latency = 2
    def __init__(self, dw=8):
        self.sink = sink = Endpoint(EndpointDescription(ycbcr422_layout(dw)))
        self.source = source = Endpoint(EndpointDescription(ycbcr444_layout(dw)))

        # # #

        y_fifo = SyncFIFO([("data", dw)], 4)
        cb_fifo = SyncFIFO([("data", dw)], 4)
        cr_fifo = SyncFIFO([("data", dw)], 4)
        self.submodules += y_fifo, cb_fifo, cr_fifo

        # input
        parity_in = Signal()
        self.sync += If(sink.valid & sink.ready, parity_in.eq(~parity_in))
        self.comb += [
            y_fifo.sink.first.eq(sink.first),
            y_fifo.sink.last.eq(sink.last),
            If(~parity_in,
                y_fifo.sink.valid.eq(sink.valid & sink.ready),
                y_fifo.sink.data.eq(sink.y),
                cb_fifo.sink.valid.eq(sink.valid & sink.ready),
                cb_fifo.sink.data.eq(sink.cb_cr),
                sink.ready.eq(y_fifo.sink.ready & cb_fifo.sink.ready)
            ).Else(
                y_fifo.sink.valid.eq(sink.valid & sink.ready),
                y_fifo.sink.data.eq(sink.y),
                cr_fifo.sink.valid.eq(sink.valid & sink.ready),
                cr_fifo.sink.data.eq(sink.cb_cr),
                sink.ready.eq(y_fifo.sink.ready & cr_fifo.sink.ready)
            )
        ]


        # output
        parity_out = Signal()
        self.sync += If(source.valid & source.ready, parity_out.eq(~parity_out))
        self.comb += [
            source.valid.eq(y_fifo.source.valid &
                            cb_fifo.source.valid &
                            cr_fifo.source.valid),
            source.y.eq(y_fifo.source.data),
            source.cb.eq(cb_fifo.source.data),
            source.cr.eq(cr_fifo.source.data),
            y_fifo.source.ready.eq(source.valid & source.ready),
            cb_fifo.source.ready.eq(source.valid & source.ready & parity_out),
            cr_fifo.source.ready.eq(source.valid & source.ready & parity_out),
            source.first.eq(y_fifo.source.first),
            source.last.eq(y_fifo.source.last),
        ]
