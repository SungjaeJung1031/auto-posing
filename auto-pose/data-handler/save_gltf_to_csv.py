
import numpy as np
import csv
import os

import numpy as np
import csv

class BVHNode:
    def __init__(self, name, offset):
        self.name = name
        self.offset = np.array(offset) if offset and len(offset) == 3 else np.array([0.0, 0.0, 0.0])
        self.children = []
        self.channel_order = []
    
    def add_child(self, child_node):
        self.children.append(child_node)
    
    def set_channels(self, channel_order):
        self.channel_order = channel_order

def parse_bvh(filepath):
    # Parse the BVH file, extracting the hierarchy and motion data
    with open(filepath, 'r') as f:
        lines = f.readlines()
    
    hierarchy = []
    motion = []
    is_motion_section = False
    
    for line in lines:
        if "MOTION" in line:
            is_motion_section = True
            continue
        
        if is_motion_section:
            motion.append(line.strip())
        else:
            hierarchy.append(line.strip())
    
    return hierarchy, motion

def build_hierarchy(hierarchy_lines):
    # Construct skeleton structure from hierarchy lines
    root = None
    node_stack = []
    current_node = None
    
    for line in hierarchy_lines:
        parts = line.split()
        if parts[0] == "ROOT" or parts[0] == "JOINT":
            new_node = BVHNode(parts[1], offset=[0, 0, 0])
            if current_node:
                current_node.add_child(new_node)
            else:
                root = new_node  # Set the root node for the first time
            current_node = new_node
            node_stack.append(new_node)
        elif parts[0] == "OFFSET":
            offset_values = list(map(float, parts[1:])) if len(parts[1:]) == 3 else [0.0, 0.0, 0.0]
            current_node.offset = offset_values
        elif parts[0] == "CHANNELS":
            current_node.set_channels(parts[2:])
        elif parts[0] == "End":
            end_offset = list(map(float, hierarchy_lines.pop().split()[1:])) if len(parts) == 4 else [0.0, 0.0, 0.0]
            current_node.add_child(BVHNode("End_Site", end_offset))
        elif parts[0] == "}":
            if node_stack:
                node_stack.pop()
                if node_stack:
                    current_node = node_stack[-1]  # Set the parent as the current node
    
    return root

def extract_positions(root, motion_data, frame_count, frame_time):
    frame_data = []
    for line in motion_data:
        try:
            frame_values = list(map(float, line.split()))
            frame_data.append(frame_values)
        except ValueError:
            continue

    positions = []
    for frame in range(frame_count):
        frame_values = frame_data[frame]
        position = forward_kinematics(root, frame_values)
        positions.append(position)
    
    return positions

def forward_kinematics(node, channel_data, parent_transform=np.eye(4), data_index=0):
    # Compute the transformation of each node based on its offset and channels
    transformation = np.eye(4)
    transformation[:3, 3] = node.offset
    
    # Handle root position separately if it has translation channels
    if node == root:
        if "Xposition" in node.channel_order:
            transformation[0, 3] += channel_data[data_index]
            data_index += 1
        if "Yposition" in node.channel_order:
            transformation[1, 3] += channel_data[data_index]
            data_index += 1
        if "Zposition" in node.channel_order:
            transformation[2, 3] += channel_data[data_index]
            data_index += 1

    # Apply rotation channels
    for channel in node.channel_order:
        if channel == "Xrotation":
            angle = np.radians(channel_data[data_index])
            rotation = np.array([
                [1, 0, 0],
                [0, np.cos(angle), -np.sin(angle)],
                [0, np.sin(angle), np.cos(angle)]
            ])
            transformation[:3, :3] = rotation @ transformation[:3, :3]
            data_index += 1
        elif channel == "Yrotation":
            angle = np.radians(channel_data[data_index])
            rotation = np.array([
                [np.cos(angle), 0, np.sin(angle)],
                [0, 1, 0],
                [-np.sin(angle), 0, np.cos(angle)]
            ])
            transformation[:3, :3] = rotation @ transformation[:3, :3]
            data_index += 1
        elif channel == "Zrotation":
            angle = np.radians(channel_data[data_index])
            rotation = np.array([
                [np.cos(angle), -np.sin(angle), 0],
                [np.sin(angle), np.cos(angle), 0],
                [0, 0, 1]
            ])
            transformation[:3, :3] = rotation @ transformation[:3, :3]
            data_index += 1
    
    global_position = parent_transform @ transformation
    positions = {node.name: global_position[:3, 3]}
    
    for child in node.children:
        child_positions = forward_kinematics(child, channel_data, global_position, data_index)
        positions.update(child_positions)
    
    return positions

def flatten_positions(positions_per_frame):
    flattened_data = []
    joint_names = []
    
    for frame_positions in positions_per_frame:
        flattened_frame = []
        frame_joint_names = []
        
        for joint_name, pos in sorted(frame_positions.items()):
            flattened_frame.extend(pos)
            if not joint_names:  # Only build joint names once
                frame_joint_names.extend([f"{joint_name}_x", f"{joint_name}_y", f"{joint_name}_z"])
        
        flattened_data.append(flattened_frame)
        if not joint_names:  # Save names only once
            joint_names = frame_joint_names
            
    return flattened_data, joint_names

def save_to_csv(flattened_data, joint_names, filename="keypoints_data.csv"):
    with open(filename, mode="w", newline="") as f:
        writer = csv.writer(f)
        writer.writerow(joint_names)  # Write header row
        for frame_data in flattened_data:
            writer.writerow(frame_data)

def extract_keypoints_for_dnn(bvh_input_path, csv_output_path):
    hierarchy, motion = parse_bvh(bvh_input_path)
    global root  # To make root accessible in forward_kinematics
    root = build_hierarchy(hierarchy)
    
    frame_count = int(motion[0].split()[1])
    frame_time = float(motion[1].split()[2])
    
    positions_per_frame = extract_positions(root, motion, frame_count, frame_time)
    flattened_data, joint_names = flatten_positions(positions_per_frame)
    
    save_to_csv(flattened_data, joint_names, csv_output_path)
    print("{} data saved to {}".format(bvh_input_path, csv_output_path))

def generate_training_data():
    bvh_input_dir = os.path.join(os.getcwd(), "data/100STYLE")
    csv_output_dir = os.path.join(os.getcwd(), "data/100STYLE_CSV")
    if not os.path.isdir(csv_output_dir):
        os.makedirs(csv_output_dir)

    for path, folders, files in os.walk(bvh_input_dir):
        if not files: continue

        src = os.path.join(path, files[0])
        dst_path = path.replace(bvh_input_dir, '') + os.sep
        dst_folder = csv_output_dir + dst_path

        # create the target dir if doesn't exist
        if not os.path.exists(dst_folder):
            os.makedirs(dst_folder)

    bvh_input_files = []
    csv_output_files = []
    for dirpath, subdirs, files in os.walk(bvh_input_dir):
        bvh_input_files.extend(os.path.join(dirpath, x) for x in files if x.endswith(".bvh"))

    for bvh_input_file in bvh_input_files:
        csv_output_file = bvh_input_file.replace("100STYLE", "100STYLE_CSV")
        csv_output_file = os.path.splitext(csv_output_file)[0]+'.csv'
        print("input: {}".format(bvh_input_file))
        print("output: {}".format(csv_output_file))
        extract_keypoints_for_dnn(bvh_input_file, csv_output_file)

    # for bvh_input_file in bvh_input_files:
    #     csv_output_file = bvh_input_file.replace("100STYLE", "100STYLE_CSV")
    #     base = os.path.splitext(csv_output_file)[0]
    #     os.rename(csv_output_file, base + ".csv")

    #     csv_output_files.append(csv_output_file)

    # print(bvh_input_files)

    



# Example Usage
# bvh_path = "path_to_your_bvh_file.bvh"
# extract_keypoints_for_dnn(bvh_path)

generate_training_data()