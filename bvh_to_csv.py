import bvhio
import csv

import os

class BVH2CSV():
    def generate_csv_data(self):
        bvh_input_dir = os.path.join(os.getcwd(), "./data/100STYLE")
        csv_output_dir = os.path.join(os.getcwd(), "./data/100STYLE_CSV")

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
            self.extract_keypoints_for_dnn(bvh_input_file, csv_output_file)

    def extract_keypoints_for_dnn(self, bvh_input_path, csv_output_path):
        root = bvhio.readAsHierarchy(bvh_input_path)
        root = bvhio.Joint('Root', restPose=bvhio.Transform(scale=1)).attach(root)

        bvh = bvhio.readAsBvh(bvh_input_path)
        print(f'Frames: {bvh.FrameCount}')

        joint_name_list: list[str] = []
        joint_position_world_list: list[tuple[float, float, float]] = []

        with open(csv_output_path, mode='w', newline='') as file:
            writer = csv.writer(file)

            for frame in range(bvh.FrameCount): 
                joint_position_world_list = []

                for (joint, index, depth) in root.loadPose(frame).layout():
                    if (joint.Name == "Root"):
                        continue

                    if frame == 0:
                        joint_name_list.append(joint.Name + "_x")
                        joint_name_list.append(joint.Name + "_y")
                        joint_name_list.append(joint.Name + "_z")
                        
                    joint_position_world_list.append(joint.PositionWorld.x)
                    joint_position_world_list.append(joint.PositionWorld.y)
                    joint_position_world_list.append(joint.PositionWorld.z)
                    

                if frame == 0:
                    writer.writerow(joint_name_list)

                writer.writerow(joint_position_world_list)


def main():
    bvh2csv = BVH2CSV()
    bvh2csv.generate_csv_data()

if __name__ == '__main__':
    main()