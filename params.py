import numpy as np

# Gen stuff
camera_matrix = np.eye(3,3) # Camera matrix
camera_matrix_inv = np.linalg.inv(camera_matrix) 
im_size = (480,640) # Size of image

# For pose estimation
sigma_p = 0.1 # Some white noise variance thing for uncertainty
index_matrix = np.reshape(np.dstack(np.meshgrid(np.arange(480),np.arange(640),indexing = 'xy')),(480*640,2)) # For some vectorizations
index_matrix_2 = np.hstack([index_matrix,np.ones((480*640,1))]) # For generating point cloud
threshold_for_high_grad = 150
threshold_for_graph_opt = 20
learning_rate_for_graph_opt = 0.1
