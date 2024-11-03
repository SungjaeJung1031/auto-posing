import sys
cupy_module_name = 'cupy'
if cupy_module_name in sys.modules:
    import cupy as np
else:
    import numpy as np

from core.math.decl import *
import math

def eye_T():
    return EYE_T.copy()


def eye_R():
    return EYE_R.copy()


def zero_p():
    return ZERO_P.copy()


def zero_R():
    return ZERO_R.copy()

def numpy_get_unit(array: np.ndarray) -> np.ndarray:
    result: np.ndarray = array / np.linalg.norm(array)
    return result

def distance_of(position1: np.ndarray, position2: np.ndarray) -> float:
    distance = np.linalg.norm(position2 - position1)
    return distance

def decompose_by(vector: np.ndarray, direction: np.ndarray) -> np.ndarray:
    unit: np.ndarray = numpy_get_unit(direction)
    decomposed: np.ndarray = np.dot(vector, direction) * unit
    return decomposed


# def normalize(v):
#     """
#     Divide vector by its norm. The method handles vectors with type list and
#     np.array.
#     """
#     is_list = type(v) == list
#     length = np.linalg.norm(v)
#     if length > EPSILON:
#         norm_v = np.array(v) / length
#         if is_list:
#             return list(norm_v)
#         else:
#             return norm_v
#     else:
#         warnings.warn("!!!The length of input vector is almost zero!!!")
#         return v


# def slerp(R1, R2, t):
#     """
#     Spherical linear interpolation (https://en.wikipedia.org/wiki/Slerp)
#     between R1 and R2 with parameter t, 0 ≤ t ≤ 1
#     """
#     return np.dot(
#         R1, conversions.A2R(t * conversions.R2A(np.dot(R1.transpose(), R2)))
#     )


# def lerp(v0, v1, t):
#     """
#     Simple linear interpolation between v0 and v1 with parameter t, 0 ≤ t ≤ 1
#     """
#     return v0 + (v1 - v0) * t


# def invertT(T):
#     R = T[:3, :3]
#     p = T[:3, 3]
#     invT = eye_T()
#     R_trans = R.transpose()
#     R_trans_p = np.dot(R_trans, p)
#     invT[:3, :3] = R_trans
#     invT[:3, 3] = -R_trans_p
#     return invT


# def componentOnVector(inputVector, directionVector):
#     return np.inner(directionVector, inputVector) / np.dot(
#         directionVector, directionVector
#     )


# def projectionOnVector(inputVector, directionVector):
#     return componentOnVector(inputVector, directionVector) * directionVector


# def R_from_vectors(vec1, vec2):
#     """
#     Returns R such that R dot vec1 = vec2
#     """
#     vec1 = normalize(vec1)
#     vec2 = normalize(vec2)

#     rot_axis = normalize(np.cross(vec1, vec2))
#     inner = np.inner(vec1, vec2)
#     theta = math.acos(inner)

#     if rot_axis[0] == 0 and rot_axis[1] == 0 and rot_axis[2] == 0:
#         rot_axis = [0, 1, 0]

#     x, y, z = rot_axis
#     c = inner
#     s = math.sin(theta)
#     R = np.array(
#         [
#             [
#                 c + (1.0 - c) * x * x,
#                 (1.0 - c) * x * y - s * z,
#                 (1 - c) * x * z + s * y,
#             ],
#             [
#                 (1.0 - c) * x * y + s * z,
#                 c + (1.0 - c) * y * y,
#                 (1.0 - c) * y * z - s * x,
#             ],
#             [
#                 (1.0 - c) * z * x - s * y,
#                 (1.0 - c) * z * y + s * x,
#                 c + (1.0 - c) * z * z,
#             ],
#         ]
#     )
#     return R


# def project_rotation_1D(R, axis):
#     """
#     Project a 3D rotation matrix to the closest 1D rotation
#     when a rotational axis is given
#     """
#     Q, angle = quaternion.Q_closest(
#         conversions.R2Q(R), [0.0, 0.0, 0.0, 1.0], axis,
#     )
#     return angle


# def project_rotation_2D(R, axis1, axis2, order="zyx"):
#     """
#     Project a 3D rotation matrix to the 2D rotation
#     when two rotational axes are given
#     """
#     zyx = conversions.R2E(R, order)
#     index1 = utils.axis_to_index(axis1)
#     index2 = utils.axis_to_index(axis2)
#     if index1 == 0 and index2 == 1:
#         return np.array(zyx[2], zyx[1])
#     elif index1 == 0 and index2 == 2:
#         return np.array(zyx[2], zyx[0])
#     elif index1 == 1 and index2 == 0:
#         return np.array(zyx[1], zyx[2])
#     elif index1 == 1 and index2 == 2:
#         return np.array(zyx[1], zyx[0])
#     elif index1 == 2 and index2 == 0:
#         return np.array(zyx[0], zyx[2])
#     elif index1 == 2 and index2 == 1:
#         return np.array(zyx[0], zyx[1])
#     else:
#         raise Exception


# def project_rotation_3D(R):
#     """
#     Project a 3D rotation matrix to the 3D rotation.
#     It will just returns corresponding axis-angle.
#     """
#     return conversions.R2A(R)


# def project_angular_vel_1D(w, axis):
#     """
#     Project a 3D angular velocity to 1d angular velocity.
#     """
#     return np.linalg.norm(np.dot(w, axis))


# def project_angular_vel_2D(w, axis1, axis2):
#     """
#     Project a 3D angular velocity to 2d angular velocity.
#     """
#     index1 = utils.axis_to_index(axis1)
#     index2 = utils.axis_to_index(axis2)
#     return np.array([w[index1], w[index2]])


# def project_angular_vel_3D(w):
#     """
#     Project a 3D angular velocity to 3d angular velocity.
#     """
#     return w


# def truncnorm(mu, sigma, lower, upper):
#     """
#     Generate a sample from a truncated normal districution
#     """
#     return np.atleast_1d(
#         stats.truncnorm(
#             (lower - mu) / sigma, (upper - mu) / sigma, loc=mu, scale=sigma
#         ).rvs()
#     )


# def random_unit_vector(dim=3):
#     """
#     Generate a random unit-vector (whose length is 1.0)
#     """
#     while True:
#         v = np.random.uniform(-1.0, 1.0, size=dim)
#         l = np.linalg.norm(v)
#         if l < constants.EPSILON:
#             continue
#         v = v / l
#         break
#     return v


# def random_position(mu_l, sigma_l, lower_l, upper_l, dim=3):
#     """
#     Generate a random position by a truncated normal districution
#     """
#     l = truncnorm(mu=mu_l, sigma=sigma_l, lower=lower_l, upper=upper_l)
#     return random_unit_vector(dim) * l


# def random_rotation(mu_theta, sigma_theta, lower_theta, upper_theta):
#     """
#     Generate a random position by a truncated normal districution
#     """
#     theta = truncnorm(
#         mu=mu_theta, sigma=sigma_theta, lower=lower_theta, upper=upper_theta
#     )
#     return conversions.A2R(random_unit_vector() * theta)


# def lerp_from_paired_list(x, xy_pairs, clamp=True):
#     """
#     Given a list of data points in the shape of [[x0,y0][x1,y1],...,[xN,yN]],
#     this returns an interpolated y value that correspoinds to a given x value
#     """
#     x0, y0 = xy_pairs[0]
#     xN, yN = xy_pairs[-1]
#     # if clamp is false, then check if x is inside of the given x range
#     if not clamp:
#         assert x0 <= x <= xN
#     # Return the boundary values if the value is outside """
#     if x <= x0:
#         return y0
#     elif x >= xN:
#         return yN
#     else:
#         """ Otherwise, return linearly interpolated values """
#         for i in range(len(xy_pairs) - 1):
#             x1, y1 = xy_pairs[i]
#             x2, y2 = xy_pairs[i + 1]
#             if x1 <= x < x2:
#                 alpha = (x - x1) / (x2 - x1)
#                 return (1.0 - alpha) * y1 + alpha * y2
#     raise Exception("This should not be reached!!!")