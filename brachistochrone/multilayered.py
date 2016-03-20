import numpy as np
import itertools as it

from helpers import *

from mobject.tex_mobject import TexMobject, TextMobject, Brace
from mobject import Mobject, Mobject1D
from mobject.image_mobject import \
    ImageMobject, MobjectFromPixelArray
from topics.three_dimensions import Stars

from animation import Animation
from animation.transform import *
from animation.simple_animations import *
from topics.geometry import *
from topics.characters import Randolph
from topics.functions import *
from mobject.region import  Region
from scene import Scene
from scene.zoomed_scene import ZoomedScene

from camera import Camera
from brachistochrone.light import PhotonScene
from brachistochrone.curves import *


#Two to many
#race light in each
#n layers
#v_1, v_2, v_3
#proportional to sqrt y_1, y_2, y_3
#limiting process

#show sliding object and light
#which path is fastest
#instantaneously obey snell's law

class MultilayeredScene(Scene):
    CONFIG = {
        "n_layers" : 5,
        "top_color" : BLUE_E,
        "bottom_color" : BLUE_A,
        "total_glass_height" : 5,
        "top" : 3*UP,
        "RectClass" : Rectangle #FilledRectangle
    }

    def get_layers(self, n_layers = None):
        if n_layers is None:
            n_layers = self.n_layers
        width = 2*SPACE_WIDTH
        height = float(self.total_glass_height)/n_layers
        rgb_pair = [
            np.array(Color(color).get_rgb())
            for color in self.top_color, self.bottom_color
        ]
        rgb_range = [
            interpolate(*rgb_pair+[x])
            for x in np.arange(0, 1, 1./n_layers)
        ]
        tops = [
            self.top + x*height*DOWN
            for x in range(n_layers)
        ]
        color = Color()
        result = []
        for top, rgb in zip(tops, rgb_range):
            color.set_rgb(rgb)
            rect = self.RectClass(
                height = height, 
                width = width, 
                color = color
            )
            rect.shift(top-rect.get_top())
            result.append(rect)
        return result

    def add_layers(self):
        self.layers = self.get_layers()
        self.add(*self.layers)
        self.freeze_background()

    def get_bottom(self):
        return self.top + self.total_glass_height*DOWN

    def get_continuous_glass(self):
        result = self.RectClass(
            width = 2*SPACE_WIDTH,
            height = self.total_glass_height,
        )
        result.sort_points(lambda p : -p[1])
        result.gradient_highlight(self.top_color, self.bottom_color)
        result.shift(self.top-result.get_top())
        return result


class TwoToMany(MultilayeredScene):
    CONFIG = {
        "RectClass" : FilledRectangle
    }
    def construct(self):
        glass = self.get_glass()
        layers = self.get_layers()

        self.add(glass)
        self.dither()
        self.play(*[
            FadeIn(
                layer,
                rate_func = squish_rate_func(smooth, x, 1)
            )
            for layer, x in zip(layers[1:], it.count(0, 0.2))
        ]+[
            Transform(glass, layers[0])
        ])
        self.dither()

    def get_glass(self):
        return self.RectClass(
            height = SPACE_HEIGHT,
            width = 2*SPACE_WIDTH,
            color = BLUE_E
        ).shift(SPACE_HEIGHT*DOWN/2)


class RaceLightInLayers(MultilayeredScene, PhotonScene):
    CONFIG = {
        "RectClass" : FilledRectangle
    }
    def construct(self):
        self.add_layers()
        line = Line(SPACE_WIDTH*LEFT, SPACE_WIDTH*RIGHT)
        lines = [
            line.copy().shift(layer.get_center())
            for layer in self.layers
        ]

        def rate_maker(x):
            return lambda t : min(x*x*t, 1)
        min_rate, max_rate = 1., 2.
        rates = np.arange(min_rate, max_rate, (max_rate-min_rate)/self.n_layers)
        self.play(*[
            self.photon_run_along_path(
                line,
                rate_func = rate_maker(rate),
                run_time = 2
            )
            for line, rate in zip(lines, rates)
        ])


class NLayers(MultilayeredScene):
    CONFIG = {
        "RectClass" : FilledRectangle
    }
    def construct(self):
        self.add_layers()
        brace = Brace(
            Mobject(
                Point(self.top),
                Point(self.get_bottom())
            ),
            RIGHT
        )
        n_layers = TextMobject("$n$ layers")
        n_layers.next_to(brace)

        self.dither()

        self.add(brace)
        self.show_frame()

        self.play(
            GrowFromCenter(brace),
            GrowFromCenter(n_layers)
        )
        self.dither()

class ShowLayerVariables(MultilayeredScene, PhotonScene):
    CONFIG = {
        "RectClass" : FilledRectangle
    }
    def construct(self):
        self.add_layers()
        v_equations = []
        start_ys = []
        end_ys = []
        center_paths = []
        braces = []
        for layer, x in zip(self.layers[:3], it.count(1)):
            eq_mob = TexMobject(
                ["v_%d"%x, "=", "\sqrt{\phantom{y_1}}"],
                size = "\\Large"
            )
            eq_mob.shift(layer.get_center()+2*LEFT)
            v_eq = eq_mob.split()
            v_eq[0].highlight(layer.get_color())
            path = Line(SPACE_WIDTH*LEFT, SPACE_WIDTH*RIGHT)
            path.shift(layer.get_center())
            brace_endpoints = Mobject(
                Point(self.top),
                Point(layer.get_bottom())
            )
            brace = Brace(brace_endpoints, RIGHT)
            brace.shift(x*RIGHT)

            start_y = TexMobject("y_%d"%x, size = "\\Large")
            end_y = start_y.copy()
            start_y.next_to(brace, RIGHT)
            end_y.shift(v_eq[-1].get_center())
            nudge = 0.2*RIGHT
            end_y.shift(nudge)

            v_equations.append(v_eq)
            start_ys.append(start_y)
            end_ys.append(end_y)
            center_paths.append(path)            
            braces.append(brace)

        for v_eq, path, time in zip(v_equations, center_paths, [2, 1, 0.5]):
            photon_run = self.photon_run_along_path(
                path,
                rate_func = None
            )
            self.play(
                FadeToColor(v_eq[0], WHITE),
                photon_run,
                run_time = time
            )
        self.dither()

        starts = [0, 0.3, 0.6]
        self.play(*it.chain(*[
            [
                GrowFromCenter(
                    mob,
                    rate_func=squish_rate_func(smooth, start, 1)
                )
                for mob, start in zip(mobs, starts)
            ]
            for mobs in start_ys, braces
        ]))
        self.dither()

        triplets = zip(v_equations, start_ys, end_ys)
        anims = []
        for v_eq, start_y, end_y in triplets:
            anims += [
                ShowCreation(v_eq[1]),
                ShowCreation(v_eq[2]),
                Transform(start_y.copy(), end_y)
            ]
        self.play(*anims)
        self.dither()


class LimitingProcess(MultilayeredScene):
    CONFIG = {
        "RectClass" : FilledRectangle
    }
    def construct(self):
        num_iterations = 3
        layer_sets = [
            self.get_layers((2**x)*self.n_layers)
            for x in range(num_iterations)
        ]
        aligned_layer_sets = [
            Mobject(*[
                Mobject(
                    *layer_sets[x][(2**x)*index:(2**x)*(index+1)]
                ).ingest_sub_mobjects()
                for index in range(self.n_layers)
            ])
            for x in range(num_iterations)
        ]
        aligned_layer_sets.append(self.get_continuous_glass())
        curr_set = aligned_layer_sets[0]
        self.add(curr_set)
        for layer_set in aligned_layer_sets[1:]:
            self.dither()
            self.play(Transform(curr_set, layer_set))
        self.dither()










