"""
===========================================================
SkewT-logP diagram: using transforms and custom projections
===========================================================

This serves as an intensive exercise of matplotlib's transforms and custom
projection API. This example produces a so-called SkewT-logP diagram, which is
a common plot in meteorology for displaying vertical profiles of temperature.
As far as matplotlib is concerned, the complexity comes from having X and Y
axes that are not orthogonal. This is handled by including a skew component to
the basic Axes transforms. Additional complexity comes in handling the fact
that the upper and lower X-axes have different data ranges, which necessitates
a bunch of custom classes for ticks,spines, and the axis to handle this.

"""

from matplotlib.axes import Axes
import matplotlib.transforms as transforms
import matplotlib.axis as maxis
import matplotlib.spines as mspines
from matplotlib.projections import register_projection


# The sole purpose of this class is to look at the upper, lower, or total
# interval as appropriate and see what parts of the tick to draw, if any.
class SkewXTick(maxis.XTick):
    def update_position(self, loc):
        # This ensures that the new value of the location is set before
        # any other updates take place
        self._loc = loc
        super(SkewXTick, self).update_position(loc)

    def _has_default_loc(self):
        return self.get_loc() is None

    def _need_lower(self):
        return (self._has_default_loc() or
                transforms.interval_contains(self.axes.lower_xlim,
                                             self.get_loc()))

    def _need_upper(self):
        return (self._has_default_loc() or
                transforms.interval_contains(self.axes.upper_xlim,
                                             self.get_loc()))

    @property
    def gridOn(self):
        return (self._gridOn and (self._has_default_loc() or
                transforms.interval_contains(self.get_view_interval(),
                                             self.get_loc())))

    @gridOn.setter
    def gridOn(self, value):
        self._gridOn = value

    @property
    def tick1On(self):
        return self._tick1On and self._need_lower()

    @tick1On.setter
    def tick1On(self, value):
        self._tick1On = value

    @property
    def label1On(self):
        return self._label1On and self._need_lower()

    @label1On.setter
    def label1On(self, value):
        self._label1On = value

    @property
    def tick2On(self):
        return self._tick2On and self._need_upper()

    @tick2On.setter
    def tick2On(self, value):
        self._tick2On = value

    @property
    def label2On(self):
        return self._label2On and self._need_upper()

    @label2On.setter
    def label2On(self, value):
        self._label2On = value

    def get_view_interval(self):
        return self.axes.xaxis.get_view_interval()


# This class exists to provide two separate sets of intervals to the tick,
# as well as create instances of the custom tick
class SkewXAxis(maxis.XAxis):
    def _get_tick(self, major):
        return SkewXTick(self.axes, None, '', major=major)

    def get_view_interval(self):
        return self.axes.upper_xlim[0], self.axes.lower_xlim[1]


# This class exists to calculate the separate data range of the
# upper X-axis and draw the spine there. It also provides this range
# to the X-axis artist for ticking and gridlines
class SkewSpine(mspines.Spine):
    def _adjust_location(self):
        pts = self._path.vertices
        if self.spine_type == 'top':
            pts[:, 0] = self.axes.upper_xlim
        else:
            pts[:, 0] = self.axes.lower_xlim


# This class handles registration of the skew-xaxes as a projection as well
# as setting up the appropriate transformations. It also overrides standard
# spines and axes instances as appropriate.
class SkewXAxes(Axes):
    # The projection must specify a name.  This will be used be the
    # user to select the projection, i.e. ``subplot(111,
    # projection='skewx')``.
    name = 'skewx'

    def _init_axis(self):
        # Taken from Axes and modified to use our modified X-axis
        self.xaxis = SkewXAxis(self)
        self.spines['top'].register_axis(self.xaxis)
        self.spines['bottom'].register_axis(self.xaxis)
        self.yaxis = maxis.YAxis(self)
        self.spines['left'].register_axis(self.yaxis)
        self.spines['right'].register_axis(self.yaxis)

    def _gen_axes_spines(self):
        spines = {'top': SkewSpine.linear_spine(self, 'top'),
                  'bottom': mspines.Spine.linear_spine(self, 'bottom'),
                  'left': mspines.Spine.linear_spine(self, 'left'),
                  'right': mspines.Spine.linear_spine(self, 'right')}
        return spines

    def _set_lim_and_transforms(self):
        """
        This is called once when the plot is created to set up all the
        transforms for the data, text and grids.
        """
        rot = 30

        # Get the standard transform setup from the Axes base class
        Axes._set_lim_and_transforms(self)

        # Need to put the skew in the middle, after the scale and limits,
        # but before the transAxes. This way, the skew is done in Axes
        # coordinates thus performing the transform around the proper origin
        # We keep the pre-transAxes transform around for other users, like the
        # spines for finding bounds
        self.transDataToAxes = self.transScale + \
            self.transLimits + transforms.Affine2D().skew_deg(rot, 0)

        # Create the full transform from Data to Pixels
        self.transData = self.transDataToAxes + self.transAxes

        # Blended transforms like this need to have the skewing applied using
        # both axes, in axes coords like before.
        self._xaxis_transform = (transforms.blended_transform_factory(
            self.transScale + self.transLimits,
            transforms.IdentityTransform()) +
            transforms.Affine2D().skew_deg(rot, 0)) + self.transAxes

    @property
    def lower_xlim(self):
        return self.axes.viewLim.intervalx

    @property
    def upper_xlim(self):
        pts = [[0., 1.], [1., 1.]]
        return self.transDataToAxes.inverted().transform(pts)[:, 0]


# Now register the projection with matplotlib so the user can select
# it.
register_projection(SkewXAxes)

if __name__ == '__main__':
    # Now make a simple example using the custom projection.
    from matplotlib.ticker import (MultipleLocator, NullFormatter,
                                   ScalarFormatter)
    import matplotlib.pyplot as plt
    from six import StringIO
    import numpy as np
    import re

    pressro = "4 3 . 6   5 0 . 0   5 3 . 3   5 6 . 3   6 3 . 2   6 8 . 2   7 0 . 0   8 0 . 2   9 2 . 9   1 0 0 . 0   1 0 7 . 0   1 2 0 . 0   1 2 2 . 0   1 5 0 . 0   1 5 7 . 0   1 7 0 . 0   1 7 5 . 0   1 8 4 . 0   1 9 5 . 0   1 9 9 . 0   2 0 0 . 0   2 0 6 . 0   2 3 3 . 0   2 3 7 . 0   2 5 0 . 0   2 5 6 . 0   2 7 2 . 0   2 7 6 . 0   2 8 2 . 0   2 8 4 . 0   2 8 6 . 0   2 9 0 . 0   2 9 4 . 0   3 0 0 . 0   3 1 7 . 0   3 2 9 . 0   3 4 1 . 0   3 5 0 . 0   3 5 3 . 0   3 5 6 . 0   3 6 5 . 0   3 9 5 . 0   4 0 0 . 0   4 2 7 . 0   4 5 0 . 0   4 6 8 . 0   5 0 0 . 0   5 1 1 . 0   5 7 4 . 0   6 2 7 . 0   6 4 3 . 0   6 4 7 . 0   6 5 9 . 0   7 0 0 . 0   7 4 1 . 0   7 6 5 . 0   7 8 5 . 0   8 5 0 . 0   8 5 2 . 0   9 2 5 . 0   9 3 5 . 0   9 4 7 . 0   9 6 1 . 0"
    tempro = "2 0 9 . 6 5   2 1 2 . 2 5   2 1 3 . 2 5   2 1 0 . 4 5   2 1 2 . 2 5   2 0 9 . 2 5   2 1 0 . 0 4 9 9 9   2 1 2 . 2 5   2 0 8 . 4 5   2 1 0 . 2 5   2 1 3 . 6 5   2 1 3 . 8 4 9 9 9   2 1 2 . 4 5   2 1 9 . 0 4 9 9 9   2 2 0 . 4 5   2 2 1 . 8 4 9 9 9   2 2 3 . 4 5   2 2 2 . 8 4 9 9 9   2 2 4 . 6 5   2 2 3 . 4 5   2 2 3 . 8 4 9 9 9   2 2 4 . 2 5   2 3 0 . 4 5   2 2 9 . 8 4 9 9 9   2 3 1 . 8 4 9 9 9   2 3 4 . 2 5   2 3 7 . 4 5   2 3 7 . 2 5   2 3 8 . 2 5   2 3 9 . 0 4 9 9 9   2 3 9 . 4 5   2 3 9 . 4 5   2 3 9 . 8 4 9 9 9   2 4 1 . 2 5   2 4 4 . 8 4 9 9 9   2 4 6 . 2 5   2 4 9 . 6 5   2 5 0 . 0 4 9 9 9   2 5 1 . 0 4 9 9 9   2 5 3 . 8 4 9 9 9   2 5 5 . 4 5   2 5 9 . 2 5   2 5 9 . 6 5   2 6 1 . 6 5   2 6 4 . 0 5   2 6 3 . 8 5   2 6 5 . 8 5   2 6 6 . 8 5   2 6 7 . 2 5   2 7 1 . 4 4 9 9 8   2 7 1 . 8 5   2 7 0 . 8 5   2 7 1 . 0 5   2 7 3 . 7 5   2 7 3 . 5 5   2 7 5 . 3 5   2 7 5 . 7 5   2 7 4 . 7 5   2 7 4 . 5 5   2 7 7 . 9 4 9 9 8   2 7 7 . 9 4 9 9 8   2 7 8 . 9 4 9 9 8   2 7 9 . 5 5"   
    dewptro = "2 0 0 . 6 5   2 0 3 . 2 5   2 0 4 . 2 5   2 0 1 . 4 5   2 0 3 . 2 5   2 0 0 . 2 5   2 0 1 . 0 4 9 9 9   2 0 3 . 2 5   1 9 9 . 4 5   2 0 1 . 2 5   2 0 3 . 6 5   2 0 3 . 8 4 9 9 9   2 0 2 . 4 5   2 0 9 . 0 4 9 9 9   2 1 0 . 4 5   2 1 1 . 8 4 9 9 9   2 1 2 . 4 5   2 1 2 . 8 4 9 9 9   2 1 4 . 6 5   2 1 3 . 4 5   2 1 3 . 8 4 9 9 9   2 1 5 . 2 5   2 2 1 . 4 5   2 2 0 . 8 4 9 9 9   2 2 2 . 8 4 9 9 9   2 2 7 . 2 5   2 3 0 . 4 5   2 2 8 . 2 5   2 2 9 . 2 5   2 3 2 . 0 4 9 9 9   2 3 1 . 4 5   2 3 0 . 4 5   2 3 1 . 8 4 9 9 9   2 3 3 . 2 5   2 3 7 . 8 4 9 9 9   2 3 9 . 2 5   2 4 4 . 6 5   2 4 3 . 0 4 9 9 9   2 4 6 . 4 5   2 5 1 . 0 4 9 9 9   2 5 2 . 9 5   2 5 7 . 5 5   2 5 7 . 9 4 9 9 8   2 6 0 . 5 5   2 6 3 . 2 5   2 6 2 . 8 5   2 6 5 . 1 5   2 6 6 . 2 5   2 6 6 . 6 5   2 7 0 . 9 4 9 9 8   2 7 1 . 4 4 9 9 8   2 7 0 . 3 5   2 7 0 . 5 5   2 7 3 . 3 5   2 7 2 . 9 4 9 9 8   2 7 4 . 9 4 9 9 8   2 7 5 . 2 5   2 7 4 . 1 5   2 7 3 . 9 4 9 9 8   2 7 7 . 0 5   2 7 7 . 2 5   2 7 7 . 8 5   2 7 8 . 1 5"   
 
    print(pressro)
    pressro = re.sub(r'\s(\.)\s+(\d)', r'\1\2', pressro)
    pressro = re.sub('(?<=\d) (?=\d)', '', pressro)
    pressro = re.sub(r'\s+\s', r' ', pressro)
    print(pressro)
    pressro = np.fromstring(pressro,dtype=float,sep=' ')
    print(pressro,pressro.shape)
    
    print(tempro)
    tempro = re.sub(r'\s(\.)\s+(\d)', r'\1\2', tempro)
    tempro = re.sub('(?<=\d) (?=\d)', '', tempro)
    tempro = re.sub(r'\s+\s', r' ', tempro)
    print(tempro)
    tempro = np.fromstring(tempro,dtype=float,sep=' ')
    print(tempro,tempro.shape)
    
    print(dewptro)
    dewptro = re.sub(r'\s(\.)\s+(\d)', r'\1\2', dewptro)
    dewptro = re.sub('(?<=\d) (?=\d)', '', dewptro)
    dewptro = re.sub(r'\s+\s', r' ', dewptro)
    print(dewptro)
    dewptro = np.fromstring(dewptro,dtype=float,sep=' ')
    print(dewptro,dewptro.shape)
    
    pro = pressro
    print("PR = ", pro, pro.shape)
    Tro = tempro
    print("T = ", Tro, Tro.shape)
    Tcro = Tro-273.15 
    print("Tc = ", Tcro, Tcro.shape)
    Tdro = dewptro
    print("TD = ", Tdro, Tdro.shape)
    Tdcro = Tdro-273.15 
    print("TDc = ", Tdcro, Tdcro.shape)
    
#IASI Sounding Profile
    
    press = "0 . 0 1 6   0 . 0 3 8   0 . 0 7 6   0 . 1 3 6   0 . 2 2 4   0 . 3 4 5   0 . 5 0 6   0 . 7 1 3   0 . 9 7 5   1 . 2 9 7   1 . 6 8 7   2 . 1 5 2   2 . 7   3 . 3 3 9   4 . 0 7 7   4 . 9 2   5 . 8 7 7   6 . 9 5 6   8 . 1 6 5   9 . 5 1 1   1 1 . 0   1 2 . 6   1 4 . 4   1 6 . 4   1 8 . 5   2 0 . 9   2 3 . 4   2 6 . 1   2 9 . 1   3 2 . 2   3 5 . 6   3 9 . 2   4 3 . 1   4 7 . 1   5 1 . 5   5 6 . 1   6 0 . 9   6 6 . 1   7 1 . 5   7 7 . 2   8 3 . 2   8 9 . 5   9 6 . 1   1 0 3 . 0   1 1 0 . 2   1 1 7 . 7   1 2 5 . 6   1 3 3 . 8   1 4 2 . 3   1 5 1 . 2   1 6 0 . 4   1 7 0 . 0   1 8 0 . 0   1 9 0 . 3   2 0 0 . 9   2 1 2 . 0   2 2 3 . 4   2 3 5 . 2   2 4 7 . 4   2 5 9 . 9   2 7 2 . 9   2 8 6 . 2   3 0 0 . 0   3 1 4 . 1   3 2 8 . 6   3 4 3 . 6   3 5 8 . 9   3 7 4 . 7   3 9 0 . 8   4 0 7 . 4   4 2 4 . 4   4 4 1 . 8   4 5 9 . 7   4 7 7 . 9   4 9 6 . 6   5 1 5 . 7   5 3 5 . 2   5 5 5 . 1   5 7 5 . 5   5 9 6 . 3   6 1 7 . 5   6 3 9 . 1   6 6 1 . 1   6 8 3 . 6   7 0 6 . 5   7 2 9 . 8   7 5 3 . 6   7 7 7 . 7   8 0 2 . 3   8 2 7 . 3   8 5 2 . 7   8 7 8 . 6   9 0 4 . 8   9 3 1 . 5"
    pressdp = "0 . 0 0 9   0 . 0 2 5   0 . 0 5 5   0 . 1 0 4   0 . 1 7 7   0 . 2 8   0 . 4 2   0 . 6 0 4   0 . 8 3 7   1 . 1 2 8   1 . 4 8 3   1 . 9 1   2 . 4 1 6   3 . 0 0 9   3 . 6 9 6   4 . 4 8 5   5 . 3 8 4   6 . 4 0 1   7 . 5 4 4   8 . 8 2 1   1 0 . 2   1 1 . 8   1 3 . 5   1 5 . 4   1 7 . 4   1 9 . 7   2 2 . 1   2 4 . 7   2 7 . 6   3 0 . 6   3 3 . 9   3 7 . 4   4 1 . 1   4 5 . 1   4 9 . 3   5 3 . 7   5 8 . 5   6 3 . 5   6 8 . 7   7 4 . 3   8 0 . 1   8 6 . 3   9 2 . 7   9 9 . 5   1 0 6 . 5   1 1 3 . 9   1 2 1 . 6   1 2 9 . 7   1 3 8 . 0   1 4 6 . 7   1 5 5 . 8   1 6 5 . 2   1 7 5 . 0   1 8 5 . 1   1 9 5 . 6   2 0 6 . 4   2 1 7 . 6   2 2 9 . 2   2 4 1 . 2   2 5 3 . 6   2 6 6 . 3   2 7 9 . 5   2 9 3 . 0   3 0 7 . 0   3 2 1 . 3   3 3 6 . 0   3 5 1 . 2   3 6 6 . 7   3 8 2 . 7   3 9 9 . 1   4 1 5 . 9   4 3 3 . 1   4 5 0 . 7   4 6 8 . 7   4 8 7 . 2   5 0 6 . 1   5 2 5 . 4   5 4 5 . 1   5 6 5 . 2   5 8 5 . 8   6 0 6 . 8   6 2 8 . 2   6 5 0 . 1   6 7 2 . 3   6 9 5 . 0   7 1 8 . 1   7 4 1 . 6   7 6 5 . 6   7 9 0 . 0   8 1 4 . 8   8 4 0 . 0   8 6 5 . 6   8 9 1 . 6   9 1 8 . 1   9 4 4 . 9"   
    temp = "2 1 7 . 7 9 6 8 8   2 2 2 . 3 9 0 6 2   2 2 9 . 5 6 2 5   2 3 7 . 8 7 5   2 4 5 . 1 8 7 5   2 5 3 . 7 1 8 7 5   2 6 1 . 6 8 7 5   2 6 6 . 2 3 4 3 8   2 6 6 . 7 5   2 6 3 . 7 1 8 7 5   2 5 7 . 5 3 1 2 5   2 5 0 . 1 4 0 6 2   2 4 3 . 6 0 9 3 8   2 3 8 . 7 1 8 7 5   2 3 5 . 9 6 8 7 5   2 3 2 . 5 6 2 5   2 2 8 . 1 0 9 3 8   2 2 4 . 4 8 4 3 8   2 2 1 . 2 9 6 8 8   2 1 9 . 1 8 7 5   2 1 7 . 9 5 3 1 2   2 1 6 . 9 3 7 5   2 1 6 . 0   2 1 5 . 1 4 0 6 2   2 1 4 . 2 0 3 1 2   2 1 4 . 2 9 6 8 8   2 1 5 . 3 5 9 3 8   2 1 6 . 4 6 8 7 5   2 1 7 . 1 0 9 3 8   2 1 7 . 0 1 5 6 2   2 1 6 . 0 6 2 5   2 1 5 . 5 1 5 6 2   2 1 5 . 6 7 1 8 8   2 1 6 . 0 3 1 2 5   2 1 6 . 0 9 3 7 5   2 1 5 . 2 9 6 8 8   2 1 3 . 9 5 3 1 2   2 1 2 . 4 6 8 7 5   2 1 1 . 4 6 8 7 5   2 1 0 . 7 8 1 2 5   2 0 9 . 6 8 7 5   2 0 9 . 0 9 3 7 5   2 0 8 . 1 2 5   2 0 7 . 0 4 6 8 8   2 0 6 . 6 8 7 5   2 0 7 . 1 8 7 5   2 0 8 . 3 7 5   2 1 0 . 0   2 1 1 . 7 8 1 2 5   2 1 3 . 9 0 6 2 5   2 1 6 . 2 9 6 8 8   2 1 9 . 1 8 7 5   2 2 2 . 5 9 3 7 5   2 2 6 . 5   2 3 1 . 4 6 8 7 5   2 3 6 . 5 4 6 8 8   2 4 0 . 6 5 6 2 5   2 4 3 . 7 6 5 6 2   2 4 5 . 9 5 3 1 2   2 4 7 . 4 0 6 2 5   2 4 8 . 5   2 4 9 . 2 3 4 3 8   2 4 9 . 8 2 8 1 2   2 5 0 . 4 5 3 1 2   2 5 1 . 3 1 2 5   2 5 2 . 0 6 2 5   2 5 2 . 6 0 9 3 8   2 5 3 . 0 6 2 5   2 5 3 . 4 6 8 7 5   2 5 3 . 9 2 1 8 8   2 5 4 . 3 7 5   2 5 4 . 7 9 6 8 8   2 5 5 . 1 8 7 5   2 5 5 . 5 6 2 5   2 5 5 . 7 3 4 3 8   2 5 6 . 0   2 5 6 . 2 8 1 2 5   2 5 6 . 6 7 1 8 8   2 5 7 . 1 4 0 6 2   2 5 8 . 7 5   2 6 1 . 6 5 6 2 5   2 6 1 . 2 6 5 6 2   2 5 6 . 7 8 1 2 5   2 5 2 . 7 6 5 6 2   2 5 3 . 1 4 0 6 2   2 5 7 . 2 3 4 3 8   2 5 9 . 5 9 3 7 5   2 6 1 . 7 3 4 3 8   2 6 3 . 5 7 8 1 2   2 6 5 . 6 4 0 6 2   2 6 7 . 6 0 9 3 8   2 6 8 . 9 6 8 7 5   2 7 1 . 4 3 7 5   2 7 3 . 5 3 1 2 5"   
    dewpt = "1 4 9 . 3 8 1 9 9   1 5 2 . 2 4 1 2 4   1 5 5 . 2 3 7 3 2   1 5 7 . 7 0 5 8 9   1 5 9 . 8 9 1 3 9   1 6 1 . 7 4 6 3 7   1 6 3 . 3 4 5 1 5   1 6 4 . 7 5 5 4 5   1 6 5 . 9 6 4 2 8   1 6 7 . 0 8 9 7 4   1 6 8 . 1 4 8 8 2   1 6 9 . 1 4 7 5 8   1 7 0 . 1 3 3 3 6   1 7 1 . 0 7 2 5 6   1 7 1 . 9 7 4 9 5   1 7 2 . 8 3 7 6 3   1 7 3 . 6 6 0 6 9   1 7 4 . 4 4 7 8   1 7 5 . 2 1 1 4 7   1 7 5 . 9 4 5 2 5   1 7 6 . 6 3 2 3 5   1 7 7 . 3 2 8 4 3   1 7 7 . 9 7 6 0 1   1 7 8 . 6 0 0 1 6   1 7 9 . 1 7 6 3 3   1 7 9 . 7 6 7 6   1 8 0 . 3 0 6 4 1   1 8 0 . 8 2 9 9 3   1 8 1 . 3 5 6 1   1 8 1 . 8 3 4 7   1 8 2 . 2 7 6 2 8   1 8 2 . 6 9 8 4 1   1 8 3 . 1 0 7 2 7   1 8 3 . 5 1 0 5 3   1 8 3 . 9 0 5 8 4   1 8 4 . 2 8 9 2 8   1 8 4 . 6 7 5 3 7   1 8 5 . 0 4 3 7 3   1 8 5 . 4 8 1 8   1 8 5 . 8 1 7 6 9   1 8 6 . 1 3 1 8 5   1 8 6 . 4 4 3 9 2   1 8 6 . 7 4 0 3 7   1 8 7 . 1 7 6 7 9   1 8 7 . 7 7 7 2 4   1 8 8 . 2 9 9 5   1 8 9 . 0 8 0 0 6   1 8 9 . 9 3 1 6 3   1 9 1 . 0 6 1 3 6   1 9 2 . 7 0 9 2   1 9 4 . 5 5 5 5 7   1 9 6 . 3 5 5 0 1   1 9 8 . 6 4 6 3 6   2 0 0 . 8 9 5 2 8   2 0 2 . 9 5 8 5 9   2 0 4 . 8 0 2 8 9   2 0 6 . 7 0 2 6 5   2 0 8 . 8 0 3 6 8   2 1 0 . 9 8 6 7   2 1 3 . 3 2 3 9 7   2 1 5 . 8 1 4 9 6   2 1 9 . 6 2 7 6   2 2 3 . 6 8 6 6 6   2 2 7 . 6 6 7 0 8   2 3 1 . 6 9 7 2 5   2 3 5 . 5 4 6 5   2 3 9 . 0 2 8 1 5   2 4 2 . 7 3 3 2 9   2 4 6 . 1 1 3 1   2 4 9 . 0 8 2 8 1   2 5 1 . 2 1 5 2   2 5 3 . 2 5 7 3 5   2 5 5 . 1 3 4 3 4   2 5 6 . 6 2 7 4 7   2 5 7 . 7 4 6 9 5   2 5 8 . 6 3 2 7 5   2 5 8 . 9 5 8 4 4   2 5 8 . 6 2 4 5   2 5 8 . 9 2 3 4 6   2 6 0 . 4 9 8 8   2 6 0 . 8 9 9 2   2 5 7 . 0 8 0 7 5   2 5 1 . 2 4 1 2   2 4 7 . 9 4 5 9 2   2 4 9 . 0 0 6 4 1   2 5 0 . 7 9 8 6 1   2 5 1 . 5 3 0 6 4   2 5 1 . 8 0 5 3 4   2 5 1 . 8 5 1 9   2 5 1 . 6 7 0 1   2 5 0 . 7 9 6 0 4   2 5 3 . 8 9 8 6 5   2 5 7 . 0 7 3 8 2   2 5 9 . 9 1 6 7 8   2 6 1 . 8 3 3 8"   
 
    print(press)
    press = re.sub(r'\s(\.)\s+(\d)', r'\1\2', press)
    press = re.sub('(?<=\d) (?=\d)', '', press)
    press = re.sub(r'\s+\s', r' ', press)
    print(press)
    press = np.fromstring(press,dtype=float,sep=' ')
    print(press,press.shape)
    
    print(pressdp)
    pressdp = re.sub(r'\s(\.)\s+(\d)', r'\1\2', pressdp)
    pressdp = re.sub('(?<=\d) (?=\d)', '', pressdp)
    pressdp = re.sub(r'\s+\s', r' ', pressdp)
    print(pressdp)
    pressdp = np.fromstring(pressdp,dtype=float,sep=' ')
    print(pressdp,pressdp.shape)
    
    print(temp)
    temp = re.sub(r'\s(\.)\s+(\d)', r'\1\2', temp)
    temp = re.sub('(?<=\d) (?=\d)', '', temp)
    temp = re.sub(r'\s+\s', r' ', temp)
    print(temp)
    temp = np.fromstring(temp,dtype=float,sep=' ')
    print(temp,temp.shape)
    
    print(dewpt)
    dewpt = re.sub(r'\s(\.)\s+(\d)', r'\1\2', dewpt)
    dewpt = re.sub('(?<=\d) (?=\d)', '', dewpt)
    dewpt = re.sub(r'\s+\s', r' ', dewpt)
    print(dewpt)
    dewpt = np.fromstring(dewpt,dtype=float,sep=' ')
    print(dewpt,dewpt.shape)
    
    p = press
    print("PR = ", p, p.shape)
    pdp1 = pressdp
    print("PR_DP = ", pdp1, pdp1.shape)
    T = temp
    print("T = ", T, T.shape)
    Tc = T-273.15 
    print("Tc = ", Tc, Tc.shape)
    Td = dewpt
    print("TD = ", Td, Td.shape)
    Tdc = Td-273.15 
    print("TDc = ", Tdc, Tdc.shape)
    
#IASI MW
    
    pressj1 = "0 . 0 1 6   0 . 0 3 8   0 . 0 7 6   0 . 1 3 6   0 . 2 2 4   0 . 3 4 5   0 . 5 0 6   0 . 7 1 3   0 . 9 7 5   1 . 2 9 7   1 . 6 8 7   2 . 1 5 2   2 . 7   3 . 3 3 9   4 . 0 7 7   4 . 9 2   5 . 8 7 7   6 . 9 5 6   8 . 1 6 5   9 . 5 1 1   1 1 . 0   1 2 . 6   1 4 . 4   1 6 . 4   1 8 . 5   2 0 . 9   2 3 . 4   2 6 . 1   2 9 . 1   3 2 . 2   3 5 . 6   3 9 . 2   4 3 . 1   4 7 . 1   5 1 . 5   5 6 . 1   6 0 . 9   6 6 . 1   7 1 . 5   7 7 . 2   8 3 . 2   8 9 . 5   9 6 . 1   1 0 3 . 0   1 1 0 . 2   1 1 7 . 7   1 2 5 . 6   1 3 3 . 8   1 4 2 . 3   1 5 1 . 2   1 6 0 . 4   1 7 0 . 0   1 8 0 . 0   1 9 0 . 3   2 0 0 . 9   2 1 2 . 0   2 2 3 . 4   2 3 5 . 2   2 4 7 . 4   2 5 9 . 9   2 7 2 . 9   2 8 6 . 2   3 0 0 . 0   3 1 4 . 1   3 2 8 . 6   3 4 3 . 6   3 5 8 . 9   3 7 4 . 7   3 9 0 . 8   4 0 7 . 4   4 2 4 . 4   4 4 1 . 8   4 5 9 . 7   4 7 7 . 9   4 9 6 . 6   5 1 5 . 7   5 3 5 . 2   5 5 5 . 1   5 7 5 . 5   5 9 6 . 3   6 1 7 . 5   6 3 9 . 1   6 6 1 . 1   6 8 3 . 6   7 0 6 . 5   7 2 9 . 8   7 5 3 . 6   7 7 7 . 7   8 0 2 . 3   8 2 7 . 3   8 5 2 . 7   8 7 8 . 6   9 0 4 . 8   9 3 1 . 5"
    tempj1 = "2 2 8 . 6 4 0 6 2   2 3 1 . 7 5   2 3 7 . 7 0 3 1 2   2 4 5 . 0 1 5 6 2   2 5 1 . 5 4 6 8 8   2 5 9 . 3 2 8 1 2   2 6 6 . 6 0 9 3 8   2 7 0 . 0   2 6 9 . 6 8 7 5   2 6 5 . 4 3 7 5   2 5 8 . 6 7 1 8 8   2 5 1 . 6 5 6 2 5   2 4 4 . 5 4 6 8 8   2 3 7 . 8 7 5   2 3 2 . 4 3 7 5   2 2 7 . 4 6 8 7 5   2 2 4 . 4 3 7 5   2 2 1 . 6 5 6 2 5   2 2 0 . 1 2 5   2 1 9 . 0 6 2 5   2 1 8 . 1 4 0 6 2   2 1 7 . 5 7 8 1 2   2 1 7 . 0 1 5 6 2   2 1 6 . 4 6 8 7 5   2 1 6 . 1 5 6 2 5   2 1 5 . 8 5 9 3 8   2 1 5 . 5 6 2 5   2 1 5 . 2 6 5 6 2   2 1 4 . 9 6 8 7 5   2 1 4 . 6 8 7 5   2 1 4 . 4 0 6 2 5   2 1 4 . 0 6 2 5   2 1 3 . 6 4 0 6 2   2 1 3 . 2 0 3 1 2   2 1 2 . 7 8 1 2 5   2 1 2 . 3 4 3 7 5   2 1 1 . 8 7 5   2 1 1 . 5 3 1 2 5   2 1 1 . 1 8 7 5   2 1 0 . 8 5 9 3 8   2 1 0 . 4 8 4 3 8   2 1 0 . 1 8 7 5   2 1 0 . 1 7 1 8 8   2 1 0 . 3 4 3 7 5   2 1 1 . 5 4 6 8 8   2 1 2 . 7 6 5 6 2   2 1 3 . 9 5 3 1 2   2 1 5 . 2 0 3 1 2   2 1 6 . 6 2 5   2 1 8 . 0   2 1 9 . 3 5 9 3 8   2 2 0 . 8 5 9 3 8   2 2 2 . 3 7 5   2 2 3 . 8 4 3 7 5   2 2 5 . 4 0 6 2 5   2 2 8 . 1 2 5   2 3 0 . 7 8 1 2 5   2 3 3 . 3 5 9 3 8   2 3 5 . 8 9 0 6 2   2 3 8 . 3 1 2 5   2 4 0 . 7 9 6 8 8   2 4 3 . 0 3 1 2 5   2 4 5 . 1 5 6 2 5   2 4 7 . 2 6 5 6 2   2 4 9 . 0 4 6 8 8   2 5 0 . 7 6 5 6 2   2 5 2 . 2 1 8 7 5   2 5 3 . 6 4 0 6 2   2 5 4 . 9 0 6 2 5   2 5 6 . 0 7 8 1 2   2 5 7 . 2 1 8 7 5   2 5 8 . 2 5   2 5 9 . 2 5   2 6 0 . 2 3 4 3 8   2 6 1 . 2 0 3 1 2   2 6 1 . 9 6 8 7 5   2 6 2 . 6 7 1 8 8   2 6 3 . 3 4 3 7 5   2 6 4 . 0 1 5 6 2   2 6 4 . 6 7 1 8 8   2 6 5 . 2 9 6 8 8   2 6 5 . 9 0 6 2 5   2 6 6 . 4 6 8 7 5   2 6 6 . 9 6 8 7 5   2 6 7 . 3 1 2 5   2 6 7 . 2 8 1 2 5   2 6 7 . 0 4 6 8 8   2 6 6 . 8 1 2 5   2 6 6 . 5 7 8 1 2   2 6 6 . 3 4 3 7 5   2 6 6 . 1 2 5   2 6 5 . 9 6 8 7 5   2 6 5 . 8 4 3 7 5   2 6 5 . 8 5 9 3 8"   
    dewptj1 = "1 5 0 . 6 6 9 4 3   1 5 3 . 6 6 4 4 6   1 5 6 . 7 9 4 5 3   1 5 9 . 3 7 9 5 3   1 6 1 . 6 6 7 5   1 6 3 . 6 1 9 2 2   1 6 5 . 3 0 6 2 3   1 6 6 . 7 9 7 3 2   1 6 8 . 0 7 8 3 1   1 6 9 . 2 7 4 8 1   1 7 0 . 3 9 5 4 8   1 7 1 . 4 5 9 3 2   1 7 2 . 5 0 6 4 4   1 7 3 . 5 0 6 3 5   1 7 4 . 4 6 4 5 1   1 7 5 . 3 8 2 3 4   1 7 6 . 2 5 5 1   1 7 7 . 0 9 6 0 1   1 7 7 . 9 1 3 2 8   1 7 8 . 6 9 5 3   1 7 9 . 4 2 9 3 5   1 8 0 . 1 7 3 2 8   1 8 0 . 8 6 7 2 6   1 8 1 . 5 3 2 2 6   1 8 2 . 1 5 2 8 3   1 8 2 . 7 8 4 3 6   1 8 3 . 3 6 6 8 2   1 8 3 . 9 2 8 4 5   1 8 4 . 4 9 3 1 8   1 8 5 . 0 0 8 5 9   1 8 5 . 4 8 5 6 3   1 8 5 . 9 4 2 6 1   1 8 6 . 3 8 0 5 2   1 8 6 . 8 1 8 2 5   1 8 7 . 2 4 7 9 1   1 8 7 . 6 5 9 8 4   1 8 8 . 0 7 4 7   1 8 8 . 4 7 6 7 9   1 8 8 . 9 4 6 4 3   1 8 9 . 4 6 7 9 6   1 8 9 . 9 7 4 3 3   1 9 0 . 4 8 0 4 5   1 9 0 . 9 6 6 2 3   1 9 1 . 6 0 7 8 6   1 9 2 . 8 9 9 0 5   1 9 4 . 2 1 8 7 2   1 9 5 . 5 6 7 9 6   1 9 6 . 9 6 5 4 8   1 9 8 . 4 9 2 2   2 0 0 . 6 9 2 1 1   2 0 3 . 5 5 1 0 4   2 0 6 . 7 5 0 8 4   2 1 0 . 0 9 6 3 4   2 1 3 . 5 0 9 7 4   2 1 7 . 0 0 3 8 3   2 2 0 . 3 3 0 8 1   2 2 3 . 8 8 3 6 7   2 2 6 . 8 2 0 8 5   2 2 9 . 8 9 6 1 8   2 3 2 . 5 3 3   2 3 4 . 9 0 6 2 3   2 3 7 . 2 3 4 8   2 3 9 . 5 3 6 0 1   2 4 1 . 3 0 7 2 5   2 4 2 . 2 0 6 9 2   2 4 2 . 7 9 8 2 6   2 4 3 . 3 6 7 2   2 4 3 . 8 0 3 8   2 4 4 . 0 0 8 8   2 4 3 . 9 8 8 3 7   2 4 3 . 8 8 7 6 6   2 4 3 . 3 1 4 9 6   2 4 2 . 5 7 4 2 5   2 4 0 . 7 8 0 6 7   2 3 7 . 8 6 2 8 5   2 3 4 . 3 6 5 9 4   2 3 1 . 5 1 1 6 1   2 2 8 . 3 4 0 2 7   2 2 5 . 2 9 8 4 5   2 2 3 . 1 7 6 5 6   2 2 1 . 7 5 7 3   2 2 0 . 3 6 2 6 9   2 1 9 . 4 4 5 2 4   2 1 9 . 0 4 4 9 4   2 1 8 . 5 8 7 2 5   2 1 8 . 1 5 1 5 7   2 1 8 . 1 4 3 4   2 1 8 . 0 7 6 5 8   2 1 8 . 2 2 9 0 8   2 2 0 . 4 7 1 7 1   2 2 3 . 2 0 2 7 1   2 2 8 . 5 1 4 8   2 3 4 . 4 6 0 9 8   2 4 1 . 9 5 3 2 2   2 4 6 . 8 5 2 1 4"   
    pressdp = "0 . 0 0 9   0 . 0 2 5   0 . 0 5 5   0 . 1 0 4   0 . 1 7 7   0 . 2 8   0 . 4 2   0 . 6 0 4   0 . 8 3 7   1 . 1 2 8   1 . 4 8 3   1 . 9 1   2 . 4 1 6   3 . 0 0 9   3 . 6 9 6   4 . 4 8 5   5 . 3 8 4   6 . 4 0 1   7 . 5 4 4   8 . 8 2 1   1 0 . 2   1 1 . 8   1 3 . 5   1 5 . 4   1 7 . 4   1 9 . 7   2 2 . 1   2 4 . 7   2 7 . 6   3 0 . 6   3 3 . 9   3 7 . 4   4 1 . 1   4 5 . 1   4 9 . 3   5 3 . 7   5 8 . 5   6 3 . 5   6 8 . 7   7 4 . 3   8 0 . 1   8 6 . 3   9 2 . 7   9 9 . 5   1 0 6 . 5   1 1 3 . 9   1 2 1 . 6   1 2 9 . 7   1 3 8 . 0   1 4 6 . 7   1 5 5 . 8   1 6 5 . 2   1 7 5 . 0   1 8 5 . 1   1 9 5 . 6   2 0 6 . 4   2 1 7 . 6   2 2 9 . 2   2 4 1 . 2   2 5 3 . 6   2 6 6 . 3   2 7 9 . 5   2 9 3 . 0   3 0 7 . 0   3 2 1 . 3   3 3 6 . 0   3 5 1 . 2   3 6 6 . 7   3 8 2 . 7   3 9 9 . 1   4 1 5 . 9   4 3 3 . 1   4 5 0 . 7   4 6 8 . 7   4 8 7 . 2   5 0 6 . 1   5 2 5 . 4   5 4 5 . 1   5 6 5 . 2   5 8 5 . 8   6 0 6 . 8   6 2 8 . 2   6 5 0 . 1   6 7 2 . 3   6 9 5 . 0   7 1 8 . 1   7 4 1 . 6   7 6 5 . 6   7 9 0 . 0   8 1 4 . 8   8 4 0 . 0   8 6 5 . 6   8 9 1 . 6   9 1 8 . 1   9 4 4 . 9"
    
    print(pressj1)
    pressj1 = re.sub(r'\s(\.)\s+(\d)', r'\1\2', pressj1)
    pressj1 = re.sub('(?<=\d) (?=\d)', '', pressj1)
    pressj1 = re.sub(r'\s+\s', r' ', pressj1)
    print(pressj1)
    pressj1 = np.fromstring(pressj1,dtype=float,sep=' ')
    print(pressj1,pressj1.shape)
    
    print(pressdp)
    pressdp = re.sub(r'\s(\.)\s+(\d)', r'\1\2', pressdp)
    pressdp = re.sub('(?<=\d) (?=\d)', '', pressdp)
    pressdp = re.sub(r'\s+\s', r' ', pressdp)
    print(pressdp)
    pressdp = np.fromstring(pressdp,dtype=float,sep=' ')
    print(pressdp,pressdp.shape)
    
    print(tempj1)
    tempj1 = re.sub(r'\s(\.)\s+(\d)', r'\1\2', tempj1)
    tempj1 = re.sub('(?<=\d) (?=\d)', '', tempj1)
    tempj1 = re.sub(r'\s+\s', r' ', tempj1)
    print(tempj1)
    tempj1 = np.fromstring(tempj1,dtype=float,sep=' ')
    print(tempj1,tempj1.shape)
    
    print(dewptj1)
    dewptj1 = re.sub(r'\s(\.)\s+(\d)', r'\1\2', dewptj1)
    dewptj1 = re.sub('(?<=\d) (?=\d)', '', dewptj1)
    dewptj1 = re.sub(r'\s+\s', r' ', dewptj1)
    print(dewptj1)
    dewptj1 = np.fromstring(dewptj1,dtype=float,sep=' ')
    print(dewptj1,dewptj1.shape)
    
    pj1 = pressj1
    print("PR = ", pj1, pj1.shape)
    Tj1 = tempj1
    print("T = ", Tj1, Tj1.shape)
    Tcj1 = Tj1-273.15 
    print("Tc = ", Tcj1, Tcj1.shape)
    Tdj1 = dewptj1
    print("TD = ", Tdj1, Tdj1.shape)
    Tdcj1 = Tdj1-273.15 
    print("TDc = ", Tdcj1, Tdcj1.shape)
    pdp2 = pressdp
    print("PR_DP = ", pdp2, pdp2.shape)

    h = np.array([2697,5370])
    Zkm = np.array([2.697,5.370])
    """    
    idx_pup = np.where(p == 506.1)
    idx_plo = np.where(p == 718.1)
    print("PUP idx = ", idx_pup)
    print("PLO idx = ", idx_plo)
    
    #Compute the Microburst Windspeed Potential Index (MWPI)
    #MiRS
    Z_UP = Zkm[1]
    print("Z_UP = ", Z_UP)
    P_UP = p[idx_pup]
    print("P_UP = ", P_UP)
    T_UP = T[idx_pup]
    print("T_UP = ", T_UP)
    TD_UP = Td[idx_pup]
    print("TD_UP = ", TD_UP)
    Z_LO = Zkm[0]
    print("Z_LO = ", Z_LO)
    P_LO = p[idx_plo]
    print("P_LO = ", P_LO)
    T_LO = T[idx_plo]
    print("T_LO = ", T_LO)
    TD_LO = Td[idx_plo]
    print("TD_LO = ", TD_LO)

    CAPE = 0
    """   
        
    idx_pup = np.where(pj1 == 496.6)
    idx_plo = np.where(pj1 == 706.5)
    print("PUP idx = ", idx_pup)
    print("PLO idx = ", idx_plo)
    idx_pupdp = np.where(pdp2 == 506.1)
    idx_plodp = np.where(pdp2 == 718.1)
    print("PUP_DP idx = ", idx_pupdp)
    print("PLO_DP idx = ", idx_plodp)
    Z_UP = Zkm[1]
    print("Z_UP = ", Z_UP)
    P_UP = pj1[idx_pup]
    print("P_UP = ", P_UP)
    T_UP = Tj1[idx_pup]
    print("T_UP = ", T_UP)
    TD_UP = Tdj1[idx_pupdp]
    print("TD_UP = ", TD_UP)
    Z_LO = Zkm[0]
    print("Z_LO = ", Z_LO)
    P_LO = pj1[idx_plo]
    print("P_LO = ", P_LO)
    T_LO = Tj1[idx_plo]
    print("T_LO = ", T_LO)
    TD_LO = Tdj1[idx_plodp]
    print("TD_LO = ", TD_LO)

    CAPE = 0
    
    def MWPI(Z_UP, Z_LO, T_UP, T_LO, TD_UP, TD_LO, CAPE):
            gamma = (T_LO - T_UP)/(Z_UP - Z_LO)
            DD_UP = T_UP - TD_UP
            print("DD_UP = ", DD_UP)
            DD_LO = T_LO - TD_LO
            print("DD_LO = ", DD_LO)
            DDD = DD_LO - DD_UP
            if DDD < 0:
                DDD = 0
            print("DDD = ", DDD)
            MWPIv1 = (CAPE/100) + gamma + DDD
            MWPIv2 = (CAPE/1000) + (gamma/5) + (DDD/5)
            WGP = (0.4553 * MWPIv1) + 28.769
            WGPv2 = (0.35435365777*(MWPIv2**2)) + (1.29598552473*MWPIv2) + 33.8176788073
            return gamma, MWPIv1, MWPIv2, WGP, WGPv2
    
    def Haines_H(T_UP, T_LO, TD_LO):
            Tdiff = T_LO - T_UP
            print("Tdiff = ", Tdiff)
            DD_LO = T_LO - TD_LO
            print("DD_LO = ", DD_LO)
            if Tdiff < 17:
                ST = 1
            elif Tdiff >= 17 and Tdiff <= 21:
                ST = 2
            else:
                ST = 3   
            if DD_LO < 14:
                MT = 1
            elif DD_LO >= 14 and DD_LO <= 20:
                MT = 2
            else:    
                MT = 3
            HI = ST + MT    
            print("ST = ", ST)
            print("MT = ", MT)
            print("HI = ", HI)
            return HI
 
    def Haines_M(T_UP, T_LO, TD_LO):
            Tdiff = T_LO - T_UP
            print("Tdiff = ", Tdiff)
            DD_LO = T_LO - TD_LO
            print("DD_LO = ", DD_LO)
            if Tdiff < 5:
                ST = 1
            elif Tdiff >= 5 and Tdiff <= 10:
                ST = 2
            else:
                ST = 3   
            if DD_LO < 5:
                MT = 1
            elif DD_LO >= 5 and DD_LO <= 12:
                MT = 2
            else:    
                MT = 3
            HI = ST + MT    
            print("ST = ", ST)
            print("MT = ", MT)
            print("HI = ", HI)
            return HI
        
    def C_Haines(T_UP, T_LO, TD_LO):
            Tdiff = T_LO - T_UP
            print("Tdiff = ", Tdiff)
            DD_LO = T_LO - TD_LO
            print("DD_LO = ", DD_LO)
            CA=((T_LO-T_UP)/2)-2
            CB=((T_LO-TD_LO)/3)-1
            if(T_LO-TD_LO)>30:
                DD_LO=30
            if CB>5:
                CB=5+((CB-5)/2)
            CH=CA+CB
            return CH
       
    gamma, MWPIv1, MWPIv2, WGP, WGPv2 = MWPI(Z_UP, Z_LO, T_UP, T_LO, TD_UP, TD_LO, CAPE)
    """
    #MiRS
    idx_pup_mid = np.where(p == 718.1)
    idx_plo_mid = np.where(p == 865.6)
    T_UP_mid = T[idx_pup_mid]
    print("T_UP_mid = ", T_UP_mid)
    T_LO_mid = T[idx_plo_mid]
    print("T_LO_mid = ", T_LO_mid)
    TD_LO_mid = Td[idx_plo_mid]
    print("TD_LO_mid = ", TD_LO_mid)
    """
   
    idx_pup_mid = np.where(pj1 == 706.5)
    idx_plo_mid = np.where(pj1 == 852.7)
    idx_pupdp_mid = np.where(pdp2 == 718.1)
    idx_plodp_mid = np.where(pdp2 == 865.6)
    T_UP_mid = T[idx_pup_mid]
    print("T_UP_mid = ", T_UP_mid)
    T_LO_mid = T[idx_plo_mid]
    print("T_LO_mid = ", T_LO_mid)
    TD_LO_mid = Td[idx_plodp_mid]
    print("TD_LO_mid = ", TD_LO_mid)
    
    HI_M = Haines_M(T_UP_mid, T_LO_mid, TD_LO_mid)
    HI_H = Haines_H(T_UP, T_LO, TD_LO)
    C_H = C_Haines(T_UP_mid, T_LO_mid, TD_LO_mid)
    
    print("Haines Index MID = ", HI_M)
    print("Haines Index HIGH = ", HI_H)
    print("C_Haines Index = ", C_H)
    print("CAPE = ", CAPE)
    print("Gamma = ", gamma)
    print("MWPIv1 = ", MWPIv1)
    print("WGP = ", WGP)
    print("MWPIv2 = ", MWPIv2)
    print("WGPv2 = ", WGPv2)
   
    # Create a new figure. The dimensions here give a good aspect ratio
    fig = plt.figure(figsize=(10, 10))
    ax = fig.add_subplot(111, projection='skewx')

    plt.grid(True)

    # Plot the data using normal plotting functions, in this case using
    # log scaling in Y, as dictated by the typical meteorological plot
    ax.semilogy(Tc, p, color='C3', linewidth=5, label='Temperature')
    ax.semilogy(Tdc, pdp1, color='C2', linewidth=5, label='Dew Point')
    ax.semilogy(Tcj1, pj1, color='C3', linewidth=5, linestyle='--', label='Temperature MW')
    ax.semilogy(Tdcj1, pdp2, color='C2', linewidth=5, linestyle='--', label='Dew Point MW')
    ax.semilogy(Tcro, pro, color='k')
    ax.semilogy(Tdcro, pro, color='k', linestyle='--')
    
    plt.text(-52,130,'500-700 mb Lapse Rate = 2.3 K/km', weight='bold', fontsize=12)
    #plt.text(-50,145,'MWPI = 1.18', fontsize=12)
    plt.text(-50,145,'GUST = 48.8 kt', weight='bold', fontsize=12)
    plt.text(-48,160,'C Haines Index = 8.8', weight='bold', fontsize=12)
    #plt.text(-46,175,'HI MID = 5', fontsize=12)
    #plt.text(-44,190,'HI HIGH = 4', fontsize=12)
        
    # An example of a slanted line at constant X
    l = ax.axvline(0, color='C0')

    # Disables the log-formatting that comes with semilogy
    ax.yaxis.set_major_formatter(ScalarFormatter())
    ax.yaxis.set_minor_formatter(NullFormatter())
    ax.set_yticks(np.linspace(100, 1000, 10))
    ax.set_ylim(1050, 100)

    ax.xaxis.set_major_locator(MultipleLocator(10))
    ax.set_xlim(-50, 50)
    plt.ylabel("Pressure (mb)")
    plt.xlabel("Temperature/Dew Point (C)")
    plt.title("Metop-A IASI-MW 0139 UTC 30 October 2012\n"
              "RAOB Sterling, VA 0300 UTC 30 October 2012")
    plt.legend(loc='lower right')
    plt.savefig("skewt_iasi_mw_1030_0139.png",dpi=250,bbox_inches='tight')
    plt.show()
    