# I've used a different cost function - check
# Use left multiplication everywhere
# Check relataive poses and stuff everywhere

import numpy as np 
import tensorflow as tf
#from pose_estimation.keyframe_utils import *
#import pose_estimation.optimiser as optimiser

tf.enable_eager_execution()
camera_matrix = np.eye(3,3) # Read from doc later
camera_matrix_inv = np.linalg.inv(camera_matrix)
thresh = 0.1

def tf_eulerAnglesToRotationMatrix(theta0,theta1,theta2):
    '''
    Converts rotation angles about x,y and z axis to a rotation matrix
    '''
    R_x = [[1, 0, 0],[0, math.cos(theta0), -math.sin(theta0)],[0, math.sin(theta0), math.cos(theta0)]]
    R_y = [[math.cos(theta1), 0, math.sin(theta1)],[0, 1, 0],[-math.sin(theta1), 0, math.cos(theta1)]]
    R_z = [[math.cos(theta2), -math.sin(theta2), 0],[math.sin(theta2), math.cos(theta2), 0],[0, 0, 1]]
    R = tf.transpose(tf.matmul(tf.transpose(R_z),tf.matmul(tf.transpose(R_y),tf.transpose(R_x))))
    return R

def tf_get_back_T(T): # Returns 4x4 matrix
	theta0 = T[3]
	theta1 = T[4]
	theta2 = T[5]
	R = tf_eulerAnglesToRotationMatrix(theta0,theta1,theta2)
	temp = [[R[0][0],R[0][1],R[0][2],T[0]],[R[1][0],R[1][1],R[1][2],T[1]],[R[2][0],R[2][1],R[2][2],T[2]],[0,0,0,1]]
	pose = tf.matmul([[1,0,0,0],[0,1,0,0],[0,0,1,0],[0,0,0,1]],temp)
	return pose

def tf_get_min_rep(T): # Returns 6 vector
	R = T[:,:3]

	# Check if R is rotation matrix

	sy = math.sqrt(R[0, 0] * R[0, 0] + R[1, 0] * R[1, 0])
	singular = sy < 1e-6

	if not singular:
		theta0 = math.atan2(R[2, 1], R[2, 2])
		theta1 = math.atan2(-R[2, 0], sy)
		theta2 = math.atan2(R[1, 0], R[0, 0])
	else:
		theta0 = math.atan2(-R[1, 2], R[1, 1])
		theta1 = math.atan2(-R[2, 0], sy)
		theta2 = 0

	temp = [T[0][3],T[1][3],T[2][3],theta0,theta1,theta2]
	return tf.matmul([[1,1,1,1,1,1]],temp)

def find_cost(world_poses, poses, covariances):
	cost = 0
	j = 0
	for i in world_poses:
		if j==0:
			continue
		wp = tf_get_back_T(i)
		wp_prev = tf_get_back_T(world_poses[j-1])
		cost_t = tf_get_min_rep(tf.transpose(tf.matmul(tf.matmul(tf.transpose(tf.linalg.inv(world_poses[j-1])),tf.transpose(tf.linalg.inv(poses[j]))),tf.transpose(wp)))[:3])
		cost = cost + tf.matmul(tf.matmul(cost_t.T,tf.transpose(tf.linalg.inv(covariances[j]))),cost_t)
		j+=1
	return cost

def find_grad(world_poses,poses,covariances):
	with tf.GradientTape() as tape:
		loss_value = find_cost(world_poses,poses,covariances)
	return tape.gradient(loss_value,world_poses)

def create_point_cloud(keyframes,world_poses):
	return 1

def pose_graph_optimisation(keyframes):
	'''
	Optimises graph

	Inputs:
		keyframe: list of keyframes (of keyframe class)

	Returns:
		Points cloud
	'''

	poses = []
	world_poses = []
	covariances = []
	j = 0
	for i in keyframes:
		poses[j] = np.append(get_min_rep(i.T),np.array([0,0,0,1],0)) # 4x4 pose
		if j==0:
			world_poses[0] = poses[0]
		else:
			world_poses[j] = np.matmul(world_poses[j-1],poses[j]) # Initial guess. Is a 4x4 matrix
		world_poses[j] = get_min_rep(world_poses[j]) # 6 vector
		covariances[j] = i.C
		j += 1

	optimizer = tf.train.AdamOptimizer(learning_rate = 0.01)


	i = -1
	while(1):
		i += 1
		grads = find_grad(world_poses, poses,covariances)
		optimizer.apply_gradients(zip(grads,world_poses),global_step = tf.train.get_or_create_global_step())

		loss = find_cost(world_poses,poses,covariances)
		if loss<thresh:
			break

	cloud = create_point_cloud(keyframes,world_poses)
	return cloud





#import the following from utils


def isRotationMatrix(R):
    '''
    Checks if a matrix is a valid rotation matrix.
    '''
    Rt = np.transpose(R)
    shouldBeIdentity = np.dot(Rt, R)
    I = np.identity(3, dtype=R.dtype)
    n = np.linalg.norm(I - shouldBeIdentity)
    return n < 1e-6


def extract_angles(R):
    '''
    Extract rotation angles

    Returns: aplha, beta, gamma (as np array)
    '''

    assert(isRotationMatrix(R))  # Throws error if false

    sy = math.sqrt(R[0, 0] * R[0, 0] + R[1, 0] * R[1, 0])

    singular = sy < 1e-6

    if not singular:
        x = math.atan2(R[2, 1], R[2, 2])
        y = math.atan2(-R[2, 0], sy)
        z = math.atan2(R[1, 0], R[0, 0])
    else:
        x = math.atan2(-R[1, 2], R[1, 1])
        y = math.atan2(-R[2, 0], sy)
        z = 0

    return np.array([x, y, z])

def get_min_rep(T):
    '''
    Convert 3*4 matrix into 6*1 vector

    [x y z alpha beta gamma]

    '''
    t = T[:, 3]
    x, y, z = t

    angles = extract_angles(T[:, :3])

    T_vect = np.zeros(6)
    T_vect[:3] = t
    T_vect[3:6] = angles
    return T_vect



def eulerAnglesToRotationMatrix(theta):
    '''
    Converts rotation angles about x,y and z axis to a rotation matrix
    '''
    R_x = np.array([[1, 0, 0],
                    [0, math.cos(theta[0]), -math.sin(theta[0])],
                    [0, math.sin(theta[0]), math.cos(theta[0])]
                    ])

    R_y = np.array([[math.cos(theta[1]), 0, math.sin(theta[1])],
                    [0, 1, 0],
                    [-math.sin(theta[1]), 0, math.cos(theta[1])]
                    ])

    R_z = np.array([[math.cos(theta[2]), -math.sin(theta[2]), 0],
                    [math.sin(theta[2]), math.cos(theta[2]), 0],
                    [0, 0, 1]
                    ])
    R = np.dot(R_z, np.dot(R_y, R_x))

    return R


def fix_u(u_prop):
    '''
    Fixes a pixel location if it is negative or out of bounds

    Arguments;
            u_prop: pixel location

    Returns:
            u_prop: fixed pixel location
    '''
    if u_prop[0] >= im_size[0]:
        u_prop[0] = im_size[0] - 1
    elif u_prop[0] < 0:
        u_prop[0] = 0
    if u_prop[1] >= im_size[1]:
        u_prop[1] = im_size[1] - 1
    elif u_prop[1] < 0:
        u_prop[1] = 0
    return u_prop


def get_back_T(T_fl):
    '''
    Converts the minimal representation of the pose into the normal 3x4 transformation matrix
    '''
    # print "The flattened pose input is ",T_fl,'\n\n\n'
    T = np.ones((3, 4))
    T[:, 3] = T_fl[:3]  # 4th column of T = first 3 elements of T_fl
    R = eulerAnglesToRotationMatrix(T_fl[3:6])
    T[:, :3] = R
    return T

def get_delD(D):
    return 0.01  # Change later to calculate based on input depth map


def huber_norm(x):
    '''
    Calculates and Returns the huber norm

    Arguments:
            x: Input

    Returns:
            Huber norm of x
    '''
    delta = 1  # Change later
    if abs(x) < delta:
        return 0.5 * (x**2)
    else:
        return delta * (abs(x) - (delta / 2))