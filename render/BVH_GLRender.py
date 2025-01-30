from typing import Optional
from typing_extensions import override
import OpenGL.GL as gl
import OpenGL.GLU as glu
import threading
import time

from render import *
from parser.bvh import *


import motion_formats.BVH_formats as bvh
from np import *


class BVH_GLRenderer(GLRenderer):
    def __init__(self) -> None:
        super().__init__()

        self.motion: Optional[Motion]
        self.ik: Optional[BVH_IK] = BVH_IK(None)
        self.ik_frame_interval = 30


    def set_object(self, skeleton, motion):
        super().set_object(skeleton, motion)
        self.ik.ik_target_skeleton = skeleton

    def reset_desired_position(self):
        self.ik_desired_position = self.ik.target_joint_transform_matrix.T @ np.array([0,0,0,1], dtype=np.float64)
        self.ik.calculate_ik(self.motion.get_posture_at(self.ik_frame), self.ik_target_joint, self.ik_desired_position)

    def move_desired_position(self, translation: np.ndarray):
        if self.ik_desired_position is not None:
            # print("moved desire:", translation)
            self.ik_desired_position = self.ik_desired_position + translation
            self.ik.calculate_ik(self.motion.get_posture_at(self.ik_frame), self.ik_target_joint, self.ik_desired_position)

    @override
    def gl_render(self, frame: Optional[int]) -> None:

        gl.glClear(gl.GL_COLOR_BUFFER_BIT | gl.GL_DEPTH_BUFFER_BIT)
        gl.glClear(gl.GL_COLOR_BUFFER_BIT|gl.GL_DEPTH_BUFFER_BIT)
        gl.glEnable(gl.GL_DEPTH_TEST)
        gl.glPolygonMode(gl.GL_FRONT_AND_BACK, gl.GL_LINE)
        self.gl_camera.lookAt()


        gl.glPointSize(8)
        gl.glColor3ub(255, 153, 255)
        for particle in self.particle_system.particles:
            print(particle.position[1])
            gl.glBegin(gl.GL_POINTS)
            gl.glVertex3f(particle.position[0], particle.position[1], particle.position[2])
            gl.glEnd()
            
        gl.glPointSize(1)
        gl.glColor3ub(255,255,50)
        for force in self.particle_system.forces:
            if force.force_type == ForceType.damped_spring:
                force: Damped_Spring_Force = force
                gl.glBegin(gl.GL_LINES)
                gl.glVertex3f(force.p.position[0], force.p.position[1], force.p.position[2])
                gl.glVertex3f(force.p2.position[0], force.p2.position[1], force.p2.position[2])
                gl.glEnd()

        if self.render_abs_axis:
            GLRenderer.gl_render_axis(1)

        GLRenderer.drawCheckerboardGround(50, 30.0) # 50x50 grid, square size 20.0
        
        if self.motion is not None:
            # self.draw_bipyramid([10,10,10], [20,20,20], 1)
            # self.draw_bipyramid([10,10,10], [0,0,0], 2)
            self.gl_render_bvh_keypoints(frame, self.skeleton.root)
            self.gl_render_bvh_skeleton_recursive(frame, self.skeleton.root)
            if self.ik_enabled:
                tmp_Color = gl.glGetFloatv(gl.GL_CURRENT_COLOR)
                gl.glColor3ub(255,0,0)
                self.gl_render_ik_target_bvh(self.ik_frame, self.skeleton.root)
                # gl.glColor4f(tmp_Color[0], tmp_Color[1], tmp_Color[2], tmp_Color[3])

                if self.ik_desired_position is not None:
                    tmp_point_size = gl.glGetFloat(gl.GL_POINT_SIZE)
                    gl.glColor3ub(0, 0, 255)
                    gl.glPointSize(8)
                    gl.glPushMatrix()
                    gl.glBegin(gl.GL_POINTS)
                    gl.glVertex3f(self.ik_desired_position[0],self.ik_desired_position[1],self.ik_desired_position[2])
                    gl.glEnd()
                    gl.glPopMatrix()
                    gl.glPointSize(tmp_point_size)
                gl.glColor4f(tmp_Color[0], tmp_Color[1], tmp_Color[2], tmp_Color[3])



    def gl_render_ik_target_bvh(self, frame, joint):
        gl.glPushMatrix()
        
        if joint.symbol != bvh.Symbol.root:
            tmp_Color = gl.glGetFloatv(gl.GL_CURRENT_COLOR)
            if self.ik_target_joint is not None and joint.has_child_or_parent(self.ik_target_joint) and joint.parent_depth >= self.ik_target_joint.parent_depth - 1:
                gl.glColor3ub(0,255,0)
                
            gl.glBegin(gl.GL_LINES)
            gl.glVertex3f(joint.offsets[0], joint.offsets[1], joint.offsets[2])
            gl.glVertex3f(0,0,0)
            gl.glEnd()
            gl.glColor4f(tmp_Color[0], tmp_Color[1], tmp_Color[2], tmp_Color[3])

        gl.glTranslatef(joint.offsets[0], joint.offsets[1], joint.offsets[2])

        if frame is not None:
            posture = self.motion.get_posture_at(frame)

            for transformation, amount in posture.get_channels_and_amounts(joint.name):
                transformation.gl_apply(amount)
                
            if self.ik_enabled and self.ik_target_joint is not None:
                if self.ik_target_joint.parent.parent.name == joint.name:
                    self.ik.rotate_tau(1)
                    self.ik.rotate_alpha(1)
                elif self.ik_target_joint.parent.name == joint.name:
                    self.ik.rotate_beta(1)

                if self.ik_enabled and self.ik_target_joint.name == joint.name:
                    tmp_Color = gl.glGetFloatv(gl.GL_CURRENT_COLOR)
                    tmp_point_size = gl.glGetFloat(gl.GL_POINT_SIZE)
                    gl.glColor3ub(50, 200, 50)
                    gl.glPointSize(8)
                    gl.glBegin(gl.GL_POINTS)
                    gl.glVertex3f(0,0,0)
                    gl.glEnd()
                    gl.glPointSize(tmp_point_size)
                    gl.glColor4f(tmp_Color[0], tmp_Color[1], tmp_Color[2], tmp_Color[3])


        if self.render_joint_axis:
            GLRenderer.gl_render_axis(1/10)

        for child in joint.children:
            self.gl_render_ik_target_bvh(frame, child)

        gl.glPopMatrix()

    def draw_pyramid(self, apex, base_center):
        ax, ay, az = apex
        bx, by, bz = base_center

        # Side length of the square base
        side_length = 2.0

        # Calculate the 4 corners of the base
        half_side = side_length / 2
        base_vertices = [
            (bx - half_side, by, bz - half_side),
            (bx + half_side, by, bz - half_side),
            (bx + half_side, by, bz + half_side),
            (bx - half_side, by, bz + half_side),
        ]
        
        gl.glBegin(gl.GL_TRIANGLES)

        # Draw the 4 faces of the pyramid
        for i in range(4):
            # Get the base corner vertices
            v1 = base_vertices[i]
            v2 = base_vertices[(i + 1) % 4]  # Next vertex in the base
            # Draw the triangle with the apex
            gl.glVertex3f(ax, ay, az)  # Apex
            gl.glVertex3f(v1[0], v1[1], v1[2])  # First base corner
            gl.glVertex3f(v2[0], v2[1], v2[2])  # Second base corner

        gl.glEnd()

        ## TODO:: fix to draw base as a square
        # # Optionally, draw the base as a square (using GL_QUADS)
        # gl.glBegin(gl.GL_QUADS)
        # for i in range(4):
        #     gl.glVertex3f(base_vertices[i][0], base_vertices[i][1], base_vertices[i][2])
        # gl.glEnd()



    # def draw_bipyramid(self, bottom_center, top_center, size):
    #     # Calculate vertices
    #     b1 = (bottom_center[0] - size, bottom_center[1] - size, bottom_center[2])
    #     b2 = (bottom_center[0] + size, bottom_center[1] - size, bottom_center[2])
    #     b3 = (bottom_center[0] + size, bottom_center[1] + size, bottom_center[2])
    #     b4 = (bottom_center[0] - size, bottom_center[1] + size, bottom_center[2])
    #     t1 = (top_center[0], top_center[1], top_center[2] + size)

    #     vertices = [b1, b2, b3, b4, t1]

    #     # Draw the base
    #     gl.glBegin(gl.GL_QUADS)
    #     for vertex in vertices[:4]:
    #         gl.glVertex3fv(vertex)
    #     gl.glEnd()

    #     # Draw the sides
    #     gl.glBegin(gl.GL_TRIANGLES)
    #     for i in range(4):
    #         gl.glVertex3fv(vertices[i])
    #         gl.glVertex3fv(vertices[(i + 1) % 4])
    #         gl.glVertex3fv(t1)
    #     gl.glEnd()


    def gl_render_bvh_keypoints(self, frame: Optional[int], joint: Joint):
        gl.glPushMatrix()

        sphere_position = np.array([joint.offsets[0], joint.offsets[1], joint.offsets[2]])
        gl.glTranslatef(*sphere_position)

        if frame is not None:
            posture = self.motion.get_posture_at(frame)

            for transformation, amount in posture.get_channels_and_amounts(joint.name):
                transformation.gl_apply(amount)

        for child in joint.children:
            self.gl_render_bvh_keypoints(frame, child)

        obj_quad = glu.gluNewQuadric()
        glu.gluQuadricDrawStyle(obj_quad, glu.GLU_FILL)
        gl.glPolygonMode(gl.GL_FRONT_AND_BACK, gl.GL_FILL)
        glu.gluQuadricNormals(obj_quad, glu.GLU_SMOOTH)
        glu.gluQuadricOrientation(obj_quad, glu.GLU_OUTSIDE)
        glu.gluQuadricTexture(obj_quad, gl.GL_FALSE)
        # gl.glEnable(gl.GL_LIGHTING)
        # gl.glEnable(gl.GL_LIGHT0)
        # gl.glEnable(gl.GL_COLOR_MATERIAL)
        gl.glColor3f(1.0, 1.0, 0.0)
        glu.gluSphere(obj_quad, 1.0, 32, 32)

        gl.glPopMatrix()


    def gl_render_bvh_skeleton_recursive(self, frame: Optional[int], joint: Joint):
        gl.glPushMatrix()

        if joint.symbol != bvh.Symbol.root:
            gl.glColor3ub(0,255,0)
            self.draw_pyramid((joint.offsets[0], joint.offsets[1], joint.offsets[2]), (0,0,0))

        gl.glTranslatef(joint.offsets[0], joint.offsets[1], joint.offsets[2])

        if frame is not None:
            posture = self.motion.get_posture_at(frame)

            for transformation, amount in posture.get_channels_and_amounts(joint.name):
                transformation.gl_apply(amount)
                
            if self.ik_enabled and self.ik_target_joint is not None:
                frame_diff = np.abs(frame - self.ik_frame)
                if frame_diff <= self.ik_frame_interval:
                    if self.ik_target_joint.parent.parent.name == joint.name:
                        self.ik.rotate_tau(1 - frame_diff / self.ik_frame_interval)
                        self.ik.rotate_alpha(1 - frame_diff / self.ik_frame_interval)
                    elif self.ik_target_joint.parent.name == joint.name:
                        self.ik.rotate_beta(1 - frame_diff / self.ik_frame_interval)

                if self.ik_enabled and self.ik_target_joint.name == joint.name:
                    tmp_Color = gl.glGetFloatv(gl.GL_CURRENT_COLOR)
                    tmp_point_size = gl.glGetFloat(gl.GL_POINT_SIZE)
                    gl.glColor3ub(50, 200, 50)
                    gl.glPointSize(8)
                    gl.glBegin(gl.GL_POINTS)
                    gl.glVertex3f(0,0,0)
                    gl.glEnd()
                    gl.glPointSize(tmp_point_size)
                    gl.glColor4f(tmp_Color[0], tmp_Color[1], tmp_Color[2], tmp_Color[3])

        if self.render_joint_axis:
            GLRenderer.gl_render_axis(1/10)

        for child in joint.children:
            self.gl_render_bvh_skeleton_recursive(frame, child)

        gl.glPopMatrix()


    def get_max_frame(self) -> int:
        if self.motion == None:
            return 0
        return self.motion.get_max_frame()

    def get_frame_time(self) -> float:
        return self.motion.frame_interval

    def set_ik_target_frame(self, ik_target_frame):
        self.ik_frame = ik_target_frame
        if self.ik_target_joint is not None:
            self.ik.calculate_ik(self.motion.get_posture_at(self.ik_frame), self.ik_target_joint, self.ik_desired_position)
    
    def set_ik_target_joint(self, ik_target_joint):
        self.ik_target_joint = ik_target_joint
        self.ik_desired_position = None
        if self.ik_target_joint is not None:
            self.ik.calculate_ik(self.motion.get_posture_at(self.ik_frame), self.ik_target_joint, self.ik_desired_position)
            self.ik_desired_position = self.ik.target_joint_transform_matrix.T @ np.array([0,0,0,1], dtype=np.float64)