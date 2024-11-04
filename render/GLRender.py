from abc import abstractmethod
from typing import List, Optional
from xmlrpc.client import boolean
import OpenGL.GL as gl
from np import *

from utils.bvh import *
from render import *

# class GLRenderObject(RenderObject):
#     def __init__(self, skeleton: Optional[Skeleton] = None) -> None:
#         super().__init__(skeleton)
#         self.ik_enabled = False
        
#     @abstractmethod
#     def gl_render_object(self, frame:int, render_axis:bool, ik_target:Optional[Joint] = None) -> None:
#         pass

#     @abstractmethod
#     def get_frame_time(self) -> float:
#         pass

#     @abstractmethod
#     def get_max_frame(self) -> int:
#         pass


class GLRenderer:
    def __init__(self) -> None:
        # self.objects: List[GLRenderObject] = []
        self.gl_camera: GLCamera = GLCamera()
        
        self.render_abs_axis = True
        self.render_joint_axis = False

        self.ik_enabled: bool = False
        self.ik_frame: int = 0
        self.ik_target_joint: Optional[Joint] = None

        self.ik = None
        self.ik_desired_position: Optional[np.ndarray] = None

        self.skeleton: Optional[Skeleton] = None
        self.motion = None

        self.particle_system: Particle_System = Particle_System()

    def update_particle_dynamics(self):
        self.particle_system.semi_implicit_euler_step(self.particle_update_interval)

    def set_object(self, skeleton, motion):
        self.skeleton = skeleton
        self.motion = motion

    @staticmethod
    def gl_render_axis(scale:float) -> None:
        gl.glPushMatrix()
        gl.glLineWidth(3*scale)
        tmp_Color = gl.glGetFloatv(gl.GL_CURRENT_COLOR)
        gl.glBegin(gl.GL_LINES)
        gl.glColor3ub(255,0,0)
        gl.glVertex3fv(np.array([0.,0.,0.]))
        gl.glVertex3fv(np.array([scale,0.,0.]))
        gl.glColor3ub(0,255,0)
        gl.glVertex3fv(np.array([0.,0.,0.]))
        gl.glVertex3fv(np.array([0.,scale,0.]))
        gl.glColor3ub(0,0,255)
        gl.glVertex3fv(np.array([0.,0.,0.]))
        gl.glVertex3fv(np.array([0.,0.,scale]))
        gl.glEnd()
        gl.glLineWidth(1)
        gl.glColor4f(tmp_Color[0], tmp_Color[1], tmp_Color[2], tmp_Color[3])
        gl.glPopMatrix()

    # @staticmethod
    # def gl_render_grid(row, col) -> None:
    #     tmp_Color = gl.glGetFloatv(gl.GL_CURRENT_COLOR)
    #     gl.glBegin(gl.GL_LINES)   
    #     gl.glColor3ub(255,255,255)
    #     for i in range(row + 1):
    #         gl.glVertex3f(i - row / 2, 0, -col/2)
    #         gl.glVertex3f(i - row / 2, 0, col/2)
    #     for i in range(col + 1):
    #         gl.glVertex3f(-row/2, 0, i - col / 2)
    #         gl.glVertex3f(row/2, 0, i - col / 2)
    #     gl.glEnd()

    #     gl.glColor4f(tmp_Color[0], tmp_Color[1], tmp_Color[2], tmp_Color[3])

    @staticmethod
    def drawCheckerboardGround(grid_size, square_size) -> None:
        half_grid = grid_size * square_size / 2  # Calculate half the grid size

        for i in range(grid_size):
            for j in range(grid_size):
                # Choose color based on position
                rgb_value_light_gray = (0.827, 0.827, 0.827)
                rgb_value_gunmetal_gray = (0.208, 0.243, 0.263)
                rgb_value_blue_gray = (0.416, 0.537, 0.655)
                color = rgb_value_light_gray if (i + j) % 2 == 0 else rgb_value_blue_gray
                gl.glColor3fv(color)

                # Calculate the position centered around (0, 0)
                x = (i * square_size) - half_grid
                z = (j * square_size) - half_grid

                # Draw a square
                gl.glPolygonMode(gl.GL_BACK, gl.GL_FILL)
                gl.glBegin(gl.GL_QUADS)
                gl.glVertex3f(x, 0.0, z)                   # Bottom left
                gl.glVertex3f(x + square_size, 0.0, z)   # Bottom right
                gl.glVertex3f(x + square_size, 0.0, z + square_size)  # Top right
                gl.glVertex3f(x, 0.0, z + square_size)   # Top left
                gl.glEnd()

    @abstractmethod
    def gl_render(self, frame:int) -> None:
        pass

    def set_viewport_size(self, w:int, h:int) -> None:
        self.gl_camera.viewport_width, self.gl_camera.viewport_height = w, h

    def set_view_ortho(self, is_ortho: boolean) -> None:
        self.gl_camera.change_orth(is_ortho)

    def show_abs_axis(self, show: bool) -> None:
        self.render_abs_axis = show

    def show_joint_axis(self, show:bool) -> None:
        self.render_joint_axis = show

    def set_ik_enabled(self, is_enabled:bool):
        self.ik_enabled = is_enabled

