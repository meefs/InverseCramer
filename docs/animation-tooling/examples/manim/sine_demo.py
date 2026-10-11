import numpy as np
from manim import *


class SineDot(Scene):
    def construct(self):
        axes = Axes(x_range=[0, 2 * PI, PI / 2], y_range=[-1.5, 1.5, 1],
                    x_length=10, y_length=4)
        curve = axes.plot(lambda x: np.sin(x), color=BLUE)
        dot = Dot(axes.c2p(0, 0), color=YELLOW)
        title = Text("Sine traced by a moving dot", font_size=36).to_edge(UP)
        self.play(Create(axes), Create(curve), FadeIn(title))
        self.play(MoveAlongPath(dot, curve), run_time=3, rate_func=smooth)
        self.wait(0.5)
