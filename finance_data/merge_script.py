import pandas as pd
import os

# تحديد المسار الكامل للمجلد الذي يحتوي على الملفات
folder_path = r"C:\Users\Zaher\Desktop\New folder"  # استبدل بمسار المجلد

# التحقق من وجود المجلد
if not os.path.exists(folder_path):
    print(f"المجلد {folder_path} غير موجود! يرجى التحقق من المسار.")
    exit()

# البحث عن جميع الملفات التي تطابق النمط *_data.csv
file_pattern = "*_data.csv"
file_paths = [os.path.join(folder_path, f) for f in os.listdir(folder_path) if f.endswith("_data.csv")]

# التحقق من وجود الملفات
if not file_paths:
    print(f"لا توجد ملفات تطابق النمط {file_pattern} في المجلد {folder_path}.")
    exit()

# قراءة ودمج جميع الملفات
try:
    # قراءة جميع الملفات في قائمة DataFrames
    dfs = [pd.read_csv(file) for file in file_paths]
    
    # دمج جميع DataFrames في DataFrame واحد
    merged_df = pd.concat(dfs, ignore_index=True)
    
    # ترتيب البيانات حسب العمود "Date" إذا كان موجودًا
    if 'Date' in merged_df.columns:
        merged_df['Date'] = pd.to_datetime(merged_df['Date'])  # تحويل العمود إلى نوع تاريخ
        merged_df = merged_df.sort_values(by='Date')
    else:
        print("تحذير: العمود 'Date' غير موجود. سيتم حفظ البيانات دون ترتيب.")
    
    # حفظ الملف المدمج كلاحقة .csv
    output_file = os.path.join(folder_path, "merged_file.csv")
    merged_df.to_csv(output_file, index=False)
    print(f"تم دمج {len(file_paths)} ملفات وحفظها في: {output_file}")
except Exception as e:
    print(f"حدث خطأ أثناء معالجة الملفات: {e}")