
# 📊 BÁO CÁO PHÂN TÍCH DỮ LIỆU ISAS CHALLENGE 2025

**Thời gian tạo báo cáo:** 2025-06-01 20:31:27

## 🎯 TỔNG QUAN CHUNG

### Thống kê cơ bản:
- **Tổng số frames:** 345,162 frames
- **Tổng thời lượng:** 3.20 giờ (191.8 phút)
- **Số users:** 4
- **Tần số:** 30 FPS
- **Số keypoints:** 17 điểm (34 tọa độ)

### Chất lượng nhãn:
- **Frames có nhãn:** 322,590 / 345,162 (93.5%)
- **Frames thiếu nhãn:** 22,572 (6.5%)

## 📈 PHÂN PHỐI HOẠT ĐỘNG

### Tổng quan:
- **Tổng số loại hoạt động:** 9
- **Hoạt động bình thường:** 245,400 frames (76.1%)
- **Hoạt động bất thường:** 77,190 frames (23.9%)
- **Tỷ lệ Normal:Abnormal:** 76.1:23.9

### Chi tiết từng hoạt động:
- **Sitting quietly** (✅ Bình thường): 71,370 frames (22.1%, 39.6 phút)
- **Walking** (✅ Bình thường): 63,480 frames (19.7%, 35.3 phút)
- **Using phone** (✅ Bình thường): 56,280 frames (17.4%, 31.3 phút)
- **Eating snacks** (✅ Bình thường): 54,270 frames (16.8%, 30.1 phút)
- **Biting** (⚠️ Bất thường): 22,920 frames (7.1%, 12.7 phút)
- **Attacking** (⚠️ Bất thường): 20,100 frames (6.2%, 11.2 phút)
- **Head banging** (⚠️ Bất thường): 17,880 frames (5.5%, 9.9 phút)
- **Throwing things** (⚠️ Bất thường): 14,010 frames (4.3%, 7.8 phút)
- **Throwing** (⚠️ Bất thường): 2,280 frames (0.7%, 1.3 phút)


## 👥 THỐNG KÊ TỪNG USER

### User 1:
- **Tổng frames:** 76,456 frames
- **Thời lượng:** 42.5 phút
- **Frames có nhãn:** 73,050 (95.5%)
- **Bình thường vs Bất thường:** 74.8% vs 25.2%
- **Chất lượng keypoints:** 0.00% missing values
- **Độ phân giải video:** 1233 × 756 pixels
- **Độ di chuyển:** X=1.59, Y=1.01 pixels/frame

### User 2:
- **Tổng frames:** 74,638 frames
- **Thời lượng:** 41.5 phút
- **Frames có nhãn:** 71,250 (95.5%)
- **Bình thường vs Bất thường:** 76.9% vs 23.1%
- **Chất lượng keypoints:** 0.00% missing values
- **Độ phân giải video:** 902 × 750 pixels
- **Độ di chuyển:** X=1.18, Y=0.68 pixels/frame

### User 3:
- **Tổng frames:** 118,087 frames
- **Thời lượng:** 65.6 phút
- **Frames có nhãn:** 106,470 (90.2%)
- **Bình thường vs Bất thường:** 77.3% vs 22.7%
- **Chất lượng keypoints:** 0.00% missing values
- **Độ phân giải video:** 1280 × 757 pixels
- **Độ di chuyển:** X=1.36, Y=0.89 pixels/frame

### User 5:
- **Tổng frames:** 75,981 frames
- **Thời lượng:** 42.2 phút
- **Frames có nhãn:** 71,820 (94.5%)
- **Bình thường vs Bất thường:** 74.7% vs 25.3%
- **Chất lượng keypoints:** 0.00% missing values
- **Độ phân giải video:** 1296 × 762 pixels
- **Độ di chuyển:** X=1.63, Y=1.14 pixels/frame



## ⚠️ VẤN ĐỀ VÀ THÁCH THỨC

### 1. Mất cân bằng dữ liệu: **NGHIÊM TRỌNG**
- Tỷ lệ Normal/Abnormal: 76.1%/23.9%
- Khuyến nghị: Sử dụng SMOTE, class weighting, hoặc Focal Loss

### 2. Missing Labels:
- 22,572 frames (6.5%) thiếu nhãn
- Khuyến nghị: Xử lý bằng interpolation hoặc loại bỏ

### 3. Chất lượng Keypoints:
- Tổng thể: XUẤT SẮC (< 0.1% missing values)
- Tất cả users có chất lượng keypoints tốt

## 💡 KHUYẾN NGHỊ TIẾP THEO

### 1. Data Preprocessing:
```python
# Thống nhất nhãn
df['Action Label'] = df['Action Label'].replace('Throwing', 'Throwing things')

# Xử lý missing values
df = df.dropna(subset=['Action Label'])

# Chuẩn hóa keypoints
for col in keypoint_columns:
    df[col] = (df[col] - df[col].mean()) / df[col].std()
```

### 2. Model Development:
- **Kiến trúc:** LSTM hoặc Transformer cho time series
- **Class balancing:** class_weight={'normal': 1, 'abnormal': 3}
- **Evaluation:** Leave-One-Subject-Out (LOSO) validation
- **Metrics:** F1-score cho lớp abnormal, Accuracy tổng thể

### 3. Feature Engineering:
- Velocity: np.diff(keypoints, axis=0)
- Acceleration: np.diff(velocity, axis=0)
- Relative positions giữa các keypoints
- Body pose angles

## 📊 BIỂU ĐỒ VÀ VISUALIZATION

Các biểu đồ đã được tạo và lưu trong thư mục `output/charts/`:
1. `activity_distribution_analysis.png` - Phân tích phân phối hoạt động
2. `keypoint_quality_analysis.png` - Phân tích chất lượng keypoints
3. `comprehensive_summary.png` - Tổng kết toàn diện

---

**Kết luận:** Dữ liệu có chất lượng tốt với keypoints chính xác, tuy nhiên cần xử lý vấn đề mất cân bằng và missing labels trước khi training model.

**Generated by:** ISAS Challenge 2025 Complete Analysis Tool
**Timestamp:** 2025-06-01 20:31:27
