import os
import sqlite3
import gradio as gr # 导入 Gradio 库
from langchain_community.agent_toolkits.sql.base import create_sql_agent
from langchain_community.agent_toolkits.sql.toolkit import SQLDatabaseToolkit
from langchain_community.utilities.sql_database import SQLDatabase
from langchain_google_genai import ChatGoogleGenerativeAI


def setup_database(db_name="sample.db"):
    """
    创建并填充 SQLite 数据库。
    如果数据库文件已存在，则不会进行任何操作。
    """
    if os.path.exists(db_name):
        print(f"数据库 '{db_name}' 已存在，跳过创建过程。")
        return

    print(f"创建并填充新的数据库 '{db_name}'...")
    conn = sqlite3.connect(db_name)
    cursor = conn.cursor()

    # --- 创建表 ---
    # 学生表
    cursor.execute('''
    CREATE TABLE students (
        student_id TEXT PRIMARY KEY,
        student_name TEXT NOT NULL,
        major TEXT
    )
    ''')

    # 课程表
    cursor.execute('''
    CREATE TABLE courses (
        course_id TEXT PRIMARY KEY,
        course_name TEXT NOT NULL,
        department TEXT,
        credits INTEGER
    )
    ''')

    # 注册表 (连接学生和课程)
    cursor.execute('''
    CREATE TABLE enrollments (
        enrollment_id INTEGER PRIMARY KEY AUTOINCREMENT,
        student_id TEXT,
        course_id TEXT,
        grade REAL,
        FOREIGN KEY (student_id) REFERENCES students (student_id),
        FOREIGN KEY (course_id) REFERENCES courses (course_id)
    )
    ''')

    # --- 插入示例数据 ---
    # 学生数据
    students_data = [
        ('S001', 'Alice', 'Computer Science'),
        ('S002', 'Bob', 'Physics'),
        ('S003', 'Charlie', 'Computer Science'),
        ('S004', 'David', 'Mathematics')
    ]
    cursor.executemany('INSERT INTO students (student_id, student_name, major) VALUES (?, ?, ?)', students_data)

    # 课程数据
    courses_data = [
        ('CS101', 'Introduction to Programming', 'Computer Science', 3),
        ('PHY201', 'Classical Mechanics', 'Physics', 4),
        ('CS303', 'Algorithms and Data Structures', 'Computer Science', 4),
        ('MATH101', 'Calculus I', 'Mathematics', 4)
    ]
    cursor.executemany('INSERT INTO courses (course_id, course_name, department, credits) VALUES (?, ?, ?, ?)', courses_data)

    # 注册数据
    enrollments_data = [
        ('S001', 'CS101', 95.5),
        ('S001', 'CS303', 88.0),
        ('S002', 'PHY201', 91.2),
        ('S003', 'CS101', 92.0),
        ('S004', 'MATH101', 85.0),
        ('S004', 'CS101', 89.5) # David 也选了 CS101
    ]
    cursor.executemany('INSERT INTO enrollments (student_id, course_id, grade) VALUES (?, ?, ?)', enrollments_data)

    # 提交更改并关闭连接
    conn.commit()
    conn.close()
    print("数据库创建和数据填充完成。")


# === 步骤 0: 设置数据库 ===
# 这将创建 sample.db 文件并填充数据（如果它尚不存在）
setup_database()


# === 步骤 1: 设置 Google API 密钥 ===
# 使用环境变量而不是在代码中硬编码密钥
# 在终端运行: export GOOGLE_API_KEY="YOUR_API_KEY"
api_key = os.environ.get("GOOGLE_API_KEY")
if not api_key:
   raise ValueError("请设置 GOOGLE_API_KEY 环境变量。")


# === 步骤 2: 设置 LLM ===
llm = ChatGoogleGenerativeAI(
    model="models/gemini-2.0-flash",  # could be changed to gemini-1.5-pro or other models
    temperature=0.2
)

# === 步骤 3: 连接到数据库 ===
db_uri = "sqlite:///sample.db"
db = SQLDatabase.from_uri(db_uri)

# === 步骤 4: 构建 LLM + Agent 工具包 ===
toolkit = SQLDatabaseToolkit(db=db, llm=llm)

agent_executor = create_sql_agent(
    llm=llm,
    toolkit=toolkit,
    verbose=True,
    agent_type="openai-tools", # 使用推荐的 agent type
)


# === 步骤 5: 创建 Gradio 交互界面 ===

# 定义与 Agent 交互的函数，供 Gradio 调用
def get_agent_response(user_query):
    """
    接收用户输入，调用 Agent，并返回格式化的答案。
    """
    print(f"接收到用户查询: {user_query}")
    if not user_query.strip():
        return "请输入一个问题。"
    try:
        response = agent_executor.invoke(user_query)
        # response 是一个字典，最终答案在 'output' 键中
        return response['output']
    except Exception as e:
        print(f"❌ 查询出错: {e}")
        return f"查询时遇到错误: {e}"

# 创建并配置 Gradio 界面
iface = gr.Interface(
    fn=get_agent_response,
    inputs=gr.Textbox(
        lines=3,
        label="您的问题",
        placeholder="用自然语言向数据库提问，例如：\n- 哪些学生主修计算机科学？\n- 列出所有课程及其学分。\n- David 选了哪些课？成绩是多少？"
    ),
    outputs=gr.Markdown(label="🧠 AI Agent 的回答"),
    title="🎓 大学数据库 AI 助教",
    description="这是一个由 AI驱动的 SQL Agent。您可以直接用自然语言查询大学数据库中的信息，无需编写 SQL 代码。",
    allow_flagging="never",
    examples=[
        ["List all students in the 'Computer Science' major."],
        ["What is the average grade for the 'CS101' course?"],
        ["Which student has the highest grade in 'PHY201'?"]
    ]
)

# 启动界面
print("\n--- 正在启动 Gradio 交互界面 ---")
print("启动后，请在浏览器中打开显示的网址 (通常是 http://127.0.0.1:7860)")
iface.launch()
