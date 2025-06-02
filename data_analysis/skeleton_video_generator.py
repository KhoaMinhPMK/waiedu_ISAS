"""
ISAS Challenge 2025 - Skeleton Video Generator
Tạo video animation khung xương từ keypoint data

Tính năng:
- Video MP4 với 30fps như data gốc
- Skeleton được normalize (giữ tỷ lệ ổn định)
- Picture-in-picture ở góc dưới phải (skeleton gốc)
- Màu sắc phân theo body parts
- Background đen
- Hiển thị activity labels (tùy chọn)

Author: AI Assistant
Date: 2024
"""

import pandas as pd
import numpy as np
import cv2
import os
from collections import Counter
from datetime import datetime
import warnings
warnings.filterwarnings('ignore')

class SkeletonVideoGenerator:
    """Lớp tạo video skeleton animation"""
    
    def __init__(self):
        # 17 keypoints chuẩn COCO format
        self.keypoint_names = [
            'nose',           # 0
            'left_eye',       # 1  
            'right_eye',      # 2
            'left_ear',       # 3
            'right_ear',      # 4
            'left_shoulder',  # 5
            'right_shoulder', # 6
            'left_elbow',     # 7
            'right_elbow',    # 8
            'left_wrist',     # 9
            'right_wrist',    # 10
            'left_hip',       # 11
            'right_hip',      # 12
            'left_knee',      # 13
            'right_knee',     # 14
            'left_ankle',     # 15
            'right_ankle'     # 16
        ]
        
        # Kết nối giữa các keypoints
        self.skeleton_connections = [
            # Face
            (0, 1), (0, 2),           # nose to eyes
            (1, 3), (2, 4),           # eyes to ears
            
            # Arms
            (5, 7), (7, 9),           # left arm: shoulder-elbow-wrist
            (6, 8), (8, 10),          # right arm: shoulder-elbow-wrist
            
            # Body
            (5, 6),                   # shoulders
            (5, 11), (6, 12),         # shoulder to hip
            (11, 12),                 # hips
            
            # Legs  
            (11, 13), (13, 15),       # left leg: hip-knee-ankle
            (12, 14), (14, 16),       # right leg: hip-knee-ankle
        ]
        
        # Màu sắc cho từng body part
        self.body_colors = {
            # Face - màu vàng
            (0, 1): '#FFD700', (0, 2): '#FFD700', 
            (1, 3): '#FFD700', (2, 4): '#FFD700',
            
            # Left arm - màu xanh lá
            (5, 7): '#00FF00', (7, 9): '#00FF00',
            
            # Right arm - màu xanh dương  
            (6, 8): '#0080FF', (8, 10): '#0080FF',
            
            # Body - màu đỏ
            (5, 6): '#FF0000', (5, 11): '#FF0000', 
            (6, 12): '#FF0000', (11, 12): '#FF0000',
            
            # Left leg - màu tím
            (11, 13): '#FF00FF', (13, 15): '#FF00FF',
            
            # Right leg - màu cam
            (12, 14): '#FF8000', (14, 16): '#FF8000',
        }
        
        # Settings
        self.video_width = 1280
        self.video_height = 720
        self.fps = 30
        self.pip_size = 0.25  # Picture-in-picture size (25% of main)
        
    def load_keypoint_data(self, user_id, with_labels=False):
        """Load keypoint data cho user cụ thể"""
        
        if with_labels:
            file_path = f"../Train_Data/keypointlabel/keypoints_with_labels_{user_id}.csv"
        else:
            file_path = f"../Train_Data/keypoint/video_{user_id}.csv"
            
        if not os.path.exists(file_path):
            raise FileNotFoundError(f"File không tồn tại: {file_path}")
            
        df = pd.read_csv(file_path)
        print(f"✅ Loaded {len(df)} frames từ {file_path}")
        
        return df
    
    def extract_keypoints_from_row(self, row):
        """Trích xuất keypoints từ một row DataFrame"""
        
        keypoints = np.zeros((17, 2))  # 17 keypoints, 2 coordinates (x, y)
        
        # Mapping tên cột với keypoint indices
        keypoint_mapping = {
            'nose': 0, 'left_eye': 1, 'right_eye': 2, 'left_ear': 3, 'right_ear': 4,
            'left_shoulder': 5, 'right_shoulder': 6, 'left_elbow': 7, 'right_elbow': 8,
            'left_wrist': 9, 'right_wrist': 10, 'left_hip': 11, 'right_hip': 12,
            'left_knee': 13, 'right_knee': 14, 'left_ankle': 15, 'right_ankle': 16
        }
        
        # Tìm và map keypoints
        for kp_name, kp_idx in keypoint_mapping.items():
            x_col = None
            y_col = None
            
            # Tìm cột x và y cho keypoint này
            for col in row.index:
                col_lower = col.lower()
                if kp_name in col_lower and '_x' in col_lower:
                    x_col = col
                elif kp_name in col_lower and '_y' in col_lower:
                    y_col = col
            
            # Lấy giá trị x, y
            if x_col is not None and y_col is not None:
                x_val = row[x_col] if not pd.isna(row[x_col]) else 0
                y_val = row[y_col] if not pd.isna(row[y_col]) else 0
                keypoints[kp_idx] = [x_val, y_val]
        
        return keypoints
    
    def normalize_skeleton(self, keypoints):
        """Normalize skeleton để giữ tỷ lệ ổn định"""
        
        # Tìm center (trung điểm của shoulders hoặc hips)
        left_shoulder = keypoints[5]
        right_shoulder = keypoints[6] 
        left_hip = keypoints[11]
        right_hip = keypoints[12]
        
        # Tính center point
        if not (np.linalg.norm(left_shoulder) == 0 and np.linalg.norm(right_shoulder) == 0):
            center = (left_shoulder + right_shoulder) / 2
        elif not (np.linalg.norm(left_hip) == 0 and np.linalg.norm(right_hip) == 0):
            center = (left_hip + right_hip) / 2
        else:
            valid_keypoints = keypoints[np.linalg.norm(keypoints, axis=1) > 0]
            center = np.mean(valid_keypoints, axis=0) if len(valid_keypoints) > 0 else np.array([self.video_width//2, self.video_height//2])
        
        # Tính scale dựa trên shoulder width hoặc body height
        shoulder_width = np.linalg.norm(right_shoulder - left_shoulder) if not (np.linalg.norm(left_shoulder) == 0 and np.linalg.norm(right_shoulder) == 0) else 100
        
        # Tính body height (từ nose đến ankle trung bình)
        nose = keypoints[0]
        left_ankle = keypoints[15]
        right_ankle = keypoints[16]
        
        if not np.linalg.norm(nose) == 0 and not (np.linalg.norm(left_ankle) == 0 and np.linalg.norm(right_ankle) == 0):
            ankle_center = (left_ankle + right_ankle) / 2 if not np.linalg.norm(left_ankle) == 0 and not np.linalg.norm(right_ankle) == 0 else left_ankle if not np.linalg.norm(left_ankle) == 0 else right_ankle
            body_height = np.linalg.norm(nose - ankle_center)
        else:
            body_height = shoulder_width * 4  # Estimate
        
        # Chọn scale reference (ưu tiên body height)
        scale_reference = max(body_height, shoulder_width * 3)
        if scale_reference == 0:
            scale_reference = 200  # Default scale
        
        # Normalize
        normalized_keypoints = keypoints.copy()
        
        # Center skeleton
        normalized_keypoints = normalized_keypoints - center
        
        # Scale to standard size (200 pixels height)
        target_scale = 200
        current_scale = scale_reference
        scale_factor = target_scale / current_scale if current_scale > 0 else 1
        
        normalized_keypoints = normalized_keypoints * scale_factor
        
        # Move to screen center
        screen_center = np.array([self.video_width // 2, self.video_height // 2])
        normalized_keypoints = normalized_keypoints + screen_center
        
        return normalized_keypoints
    
    def draw_skeleton(self, ax, keypoints, color_scheme='body_parts', alpha=1.0, linewidth=2):
        """Vẽ skeleton lên axes"""
        
        # Clear previous frame
        ax.clear()
        ax.set_xlim(0, self.video_width)
        ax.set_ylim(0, self.video_height)
        ax.set_aspect('equal')
        ax.axis('off')
        ax.set_facecolor('black')
        
        # Invert y-axis để match với coordinate system
        ax.invert_yaxis()
        
        # Vẽ connections
        for connection in self.skeleton_connections:
            start_idx, end_idx = connection
            start_point = keypoints[start_idx]
            end_point = keypoints[end_idx]
            
            # Skip nếu keypoint bị missing
            if np.linalg.norm(start_point) == 0 or np.linalg.norm(end_point) == 0:
                continue
                
            # Chọn màu
            if color_scheme == 'body_parts':
                color = self.body_colors.get(connection, '#FFFFFF')
            else:
                color = '#FFFFFF'  # Default white
            
            # Vẽ line
            ax.plot([start_point[0], end_point[0]], 
                   [start_point[1], end_point[1]], 
                   color=color, linewidth=linewidth, alpha=alpha)
        
        # Vẽ keypoints
        for i, point in enumerate(keypoints):
            if np.linalg.norm(point) == 0:  # Skip missing keypoints
                continue
                
            # Chọn màu cho keypoint
            if i == 0:  # nose
                color = '#FFD700'
            elif i in [1, 2, 3, 4]:  # face
                color = '#FFD700' 
            elif i in [5, 7, 9]:  # left arm
                color = '#00FF00'
            elif i in [6, 8, 10]:  # right arm
                color = '#0080FF'
            elif i in [11, 13, 15]:  # left leg
                color = '#FF00FF'
            elif i in [12, 14, 16]:  # right leg
                color = '#FF8000'
            else:
                color = '#FFFFFF'
            
            ax.scatter(point[0], point[1], c=color, s=30*alpha, alpha=alpha, zorder=10)
    
    def create_skeleton_video(self, user_id, with_labels=False, max_frames=None):
        """Tạo skeleton video cho user cụ thể"""
        
        print(f"\n🎬 Tạo skeleton video cho User {user_id} {'(có labels)' if with_labels else '(không labels)'}")
        print("=" * 60)
        
        # Load data
        df = self.load_keypoint_data(user_id, with_labels)
        
        # Limit frames nếu cần (để test)
        if max_frames and len(df) > max_frames:
            df = df.head(max_frames)
            print(f"⚠️ Giới hạn {max_frames} frames để test")
        
        # Tạo output filename
        output_dir = "../output/videos"
        os.makedirs(output_dir, exist_ok=True)
        
        label_suffix = "_with_labels" if with_labels else "_skeleton_only"
        output_file = f"{output_dir}/user_{user_id}{label_suffix}.mp4"
        
        print(f"🚀 Bắt đầu tạo video: {output_file}")
        
        # Setup OpenCV VideoWriter
        fourcc = cv2.VideoWriter_fourcc(*'mp4v')
        video_writer = cv2.VideoWriter(output_file, fourcc, self.fps, (self.video_width, self.video_height))
        
        # Tạo từng frame
        for frame_idx in range(len(df)):
            row = df.iloc[frame_idx]
            
            # Tạo frame trống (đen)
            frame = np.zeros((self.video_height, self.video_width, 3), dtype=np.uint8)
            
            # Extract keypoints
            keypoints = self.extract_keypoints_from_row(row)
            
            # Main skeleton (normalized)
            normalized_keypoints = self.normalize_skeleton(keypoints)
            
            # Vẽ skeleton lên frame
            self.draw_skeleton_on_frame(frame, normalized_keypoints)
            
            # Picture-in-picture (original scale)
            pip_width = int(self.video_width * self.pip_size)
            pip_height = int(self.video_height * self.pip_size)
            pip_x = self.video_width - pip_width - 20  # 20px margin từ bên phải
            pip_y = self.video_height - pip_height - 20  # 20px margin từ dưới
            
            # Tạo PiP frame
            pip_frame = np.zeros((pip_height, pip_width, 3), dtype=np.uint8)
            
            # Scale original keypoints để fit trong PiP
            original_keypoints = keypoints.copy()
            if not np.all(np.linalg.norm(original_keypoints, axis=1) == 0):
                # Find bounding box
                valid_points = original_keypoints[np.linalg.norm(original_keypoints, axis=1) > 0]
                if len(valid_points) > 0:
                    min_x, min_y = valid_points.min(axis=0)
                    max_x, max_y = valid_points.max(axis=0)
                    
                    # Scale để fit trong PiP
                    scale_x = pip_width / (max_x - min_x) if (max_x - min_x) > 0 else 1
                    scale_y = pip_height / (max_y - min_y) if (max_y - min_y) > 0 else 1
                    scale = min(scale_x, scale_y) * 0.8  # 80% để có margin
                    
                    # Center trong PiP
                    original_keypoints = (original_keypoints - [min_x, min_y]) * scale
                    pip_center = np.array([pip_width/2, pip_height/2])
                    current_center = np.mean(original_keypoints[np.linalg.norm(original_keypoints, axis=1) > 0], axis=0) if len(original_keypoints[np.linalg.norm(original_keypoints, axis=1) > 0]) > 0 else np.array([0, 0])
                    original_keypoints = original_keypoints - current_center + pip_center
            
            # Vẽ skeleton lên PiP
            self.draw_skeleton_on_frame(pip_frame, original_keypoints, alpha=0.8, linewidth=1)
            
            # Ghép PiP vào frame chính
            frame[pip_y:pip_y+pip_height, pip_x:pip_x+pip_width] = pip_frame
            
            # Add labels nếu có
            if with_labels:
                # Tìm cột Action Label
                action_cols = [col for col in df.columns if 'Action' in col and 'Label' in col]
                if action_cols:
                    action_col = action_cols[0]
                    action_label = row[action_col] if not pd.isna(row[action_col]) else "Unknown"
                    
                    # Hiển thị label
                    cv2.putText(frame, f"Activity: {action_label}", (50, 50), 
                               cv2.FONT_HERSHEY_SIMPLEX, 0.7, (255, 255, 255), 2)
            
            # Add frame info
            timestamp = frame_idx / self.fps
            cv2.putText(frame, f"Frame: {frame_idx}", (self.video_width - 200, 50), 
                       cv2.FONT_HERSHEY_SIMPLEX, 0.5, (255, 255, 255), 1)
            cv2.putText(frame, f"Time: {timestamp:.2f}s", (self.video_width - 200, 70), 
                       cv2.FONT_HERSHEY_SIMPLEX, 0.5, (255, 255, 255), 1)
            
            # Viết frame vào video
            video_writer.write(frame)
            
            # Progress
            if frame_idx % 100 == 0 or frame_idx == len(df) - 1:
                print(f"\r🎬 Đang xử lý frame {frame_idx+1}/{len(df)} ({(frame_idx+1)/len(df)*100:.1f}%)", end='', flush=True)
        
        # Đóng video writer
        video_writer.release()
        
        print(f"\n✅ Video đã được tạo: {output_file}")
        print(f"📊 Thông tin: {len(df)} frames, {len(df)/self.fps:.1f} giây, {self.fps} FPS")
        
        return output_file
    
    def draw_skeleton_on_frame(self, frame, keypoints, alpha=1.0, linewidth=2):
        """Vẽ skeleton lên OpenCV frame"""
        
        # Vẽ connections
        for connection in self.skeleton_connections:
            start_idx, end_idx = connection
            start_point = keypoints[start_idx]
            end_point = keypoints[end_idx]
            
            # Skip nếu keypoint bị missing
            if np.linalg.norm(start_point) == 0 or np.linalg.norm(end_point) == 0:
                continue
                
            # Chọn màu (BGR format cho OpenCV)
            color_hex = self.body_colors.get(connection, '#FFFFFF')
            # Convert hex to BGR
            color_rgb = tuple(int(color_hex[i:i+2], 16) for i in (1, 3, 5))
            color_bgr = (color_rgb[2], color_rgb[1], color_rgb[0])  # RGB to BGR
            
            # Vẽ line
            cv2.line(frame, 
                    (int(start_point[0]), int(start_point[1])), 
                    (int(end_point[0]), int(end_point[1])), 
                    color_bgr, linewidth)
        
        # Vẽ keypoints
        for i, point in enumerate(keypoints):
            if np.linalg.norm(point) == 0:  # Skip missing keypoints
                continue
                
            # Chọn màu cho keypoint
            if i == 0:  # nose
                color_bgr = (0, 215, 255)  # FFD700 -> BGR
            elif i in [1, 2, 3, 4]:  # face
                color_bgr = (0, 215, 255)  # FFD700 -> BGR
            elif i in [5, 7, 9]:  # left arm
                color_bgr = (0, 255, 0)   # 00FF00 -> BGR
            elif i in [6, 8, 10]:  # right arm
                color_bgr = (255, 128, 0) # 0080FF -> BGR
            elif i in [11, 13, 15]:  # left leg
                color_bgr = (255, 0, 255) # FF00FF -> BGR
            elif i in [12, 14, 16]:  # right leg
                color_bgr = (0, 128, 255) # FF8000 -> BGR
            else:
                color_bgr = (255, 255, 255)  # White
            
            cv2.circle(frame, (int(point[0]), int(point[1])), 4, color_bgr, -1)
    
    def create_all_videos(self, max_frames_per_video=None):
        """Tạo tất cả 8 videos cho 4 users"""
        
        print("🎬 TẠO TẤT CẢ SKELETON VIDEOS CHO ISAS CHALLENGE 2025")
        print("=" * 70)
        
        users = ['1', '2', '3', '5']  # User IDs
        created_videos = []
        
        for user_id in users:
            try:
                # Video 1: Skeleton only
                print(f"\n📽️ Tạo video skeleton cho User {user_id}...")
                video1 = self.create_skeleton_video(user_id, with_labels=False, max_frames=max_frames_per_video)
                created_videos.append(video1)
                
                # Video 2: Skeleton with labels  
                print(f"\n📽️ Tạo video skeleton + labels cho User {user_id}...")
                video2 = self.create_skeleton_video(user_id, with_labels=True, max_frames=max_frames_per_video)
                created_videos.append(video2)
                
            except Exception as e:
                print(f"❌ Lỗi khi tạo video cho User {user_id}: {e}")
                continue
        
        print(f"\n🎉 HOÀN THÀNH TẠO VIDEOS!")
        print("=" * 70)
        print(f"✅ Đã tạo {len(created_videos)} videos:")
        for video in created_videos:
            file_size = os.path.getsize(video) / (1024*1024)  # MB
            print(f"   📁 {video} ({file_size:.1f} MB)")
        
        return created_videos


def main():
    """Main function"""
    
    # Khởi tạo generator
    generator = SkeletonVideoGenerator()
    
    # Tạo tất cả videos (load hết tất cả frames)
    videos = generator.create_all_videos(max_frames_per_video=None)  # None = load hết data
    
    print(f"\n💡 Videos được tạo với toàn bộ data")
    print(f"📁 Videos được lưu trong: ../output/videos/")


if __name__ == "__main__":
    main() 