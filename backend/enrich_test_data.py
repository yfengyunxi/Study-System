"""Enrich test user with more data: extra plans, tasks, materials, chats, and focus sessions.
Fully idempotent — safe to run multiple times."""
import sys
import random
from datetime import date, timedelta

from app import app
from extensions import db
from models.chat import ChatHistory, Conversation, Message
from models.focus import FocusSession
from models.material import Material, MaterialFolder
from models.plan import StudyPlan, StudyTask
from models.user import User
from services.time_service import utc_now

today = date.today()
now = utc_now()

# Track how many new items were added this run
stats = {"plans": 0, "tasks": 0, "folders": 0, "materials": 0, "chats": 0, "convs": 0, "fs": 0, "fs_minutes": 0}


def _get_or_create_plan(user_id, title, description, start_date, end_date):
    """Get existing plan by title or create a new one."""
    existing = StudyPlan.query.filter_by(user_id=user_id, title=title).first()
    if existing:
        return existing
    p = StudyPlan(user_id=user_id, title=title, description=description,
                  start_date=start_date, end_date=end_date)
    db.session.add(p)
    db.session.flush()
    stats["plans"] += 1
    return p


def _add_tasks_if_new(user_id, plan_id, tasks_data):
    """Add tasks, skipping any whose title already exists for this plan+user."""
    existing_titles = {
        t.title for t in StudyTask.query.filter_by(user_id=user_id, plan_id=plan_id).all()
    }
    for (title, due_date, status, completed_delta) in tasks_data:
        if title in existing_titles:
            continue
        t = StudyTask(user_id=user_id, plan_id=plan_id, title=title,
                      due_date=due_date, status=status)
        if completed_delta:
            t.completed_at = now - completed_delta
        db.session.add(t)
        stats["tasks"] += 1


def _add_standalone_tasks(user_id, tasks_data):
    """Add standalone tasks (plan_id=None), skipping duplicates by title."""
    existing_titles = {
        t.title for t in StudyTask.query.filter_by(user_id=user_id, plan_id=None).all()
    }
    for (title, due_date, status, completed_delta) in tasks_data:
        if title in existing_titles:
            continue
        t = StudyTask(user_id=user_id, title=title, due_date=due_date, status=status)
        if completed_delta:
            t.completed_at = now - completed_delta
        db.session.add(t)
        stats["tasks"] += 1


def _get_or_create_folder(user_id, name, description):
    """Get existing folder or create one."""
    existing = MaterialFolder.query.filter_by(user_id=user_id, name=name).first()
    if existing:
        return existing
    f = MaterialFolder(user_id=user_id, name=name, description=description)
    db.session.add(f)
    db.session.flush()
    stats["folders"] += 1
    return f


def enrich(user_id):
    user = db.session.get(User, user_id)
    if not user:
        # Create test user if needed
        user = User(username="test", nickname="测试同学")
        user.set_password("123456")
        db.session.add(user)
        db.session.flush()
        user_id = user.id
        print(f"Created user test, id={user_id}, password=123456")

    print(f"Enriching data for user: {user.username} (id={user_id})")

    # ═══════════════════════════════════════════════════════════
    # 1. Extra plans + tasks
    # ═══════════════════════════════════════════════════════════

    p6 = _get_or_create_plan(user_id, "深度学习入门（吴恩达课程）",
        "跟学 Coursera 深度学习专项课程，完成编程作业和笔记整理。",
        today - timedelta(days=7), today + timedelta(days=30))
    _add_tasks_if_new(user_id, p6.id, [
        ("神经网络基础与正向传播", today - timedelta(days=5), "done", timedelta(days=5)),
        ("反向传播与梯度下降推导", today - timedelta(days=2), "done", timedelta(days=2)),
        ("手写数字识别实战（MNIST）", today, "todo", None),
        ("卷积神经网络 CNN 原理", today + timedelta(days=4), "todo", None),
        ("ResNet 与迁移学习", today + timedelta(days=10), "todo", None),
        ("RNN/LSTM 序列模型", today + timedelta(days=18), "todo", None),
    ])

    p7 = _get_or_create_plan(user_id, "英语六级备考计划",
        "每天背单词 + 真题训练，目标 550+。",
        today - timedelta(days=14), today + timedelta(days=45))
    _add_tasks_if_new(user_id, p7.id, [
        ("核心词汇 2000 词（第1轮）", today - timedelta(days=10), "done", timedelta(days=10)),
        ("听力真题精听 ×5 套", today - timedelta(days=6), "done", timedelta(days=6)),
        ("长篇阅读技巧 + 练习", today - timedelta(days=3), "done", timedelta(days=3)),
        ("写作模板整理 + 仿写2篇", today + timedelta(days=1), "todo", None),
        ("翻译专项训练（文化类）", today + timedelta(days=4), "todo", None),
        ("阅读真题精做 ×3 套", today + timedelta(days=8), "todo", None),
        ("考前全真模拟 + 错题回顾", today + timedelta(days=14), "todo", None),
    ])

    p8 = _get_or_create_plan(user_id, "软件工程导论",
        "理解需求分析、设计模式、敏捷开发、测试驱动开发等核心概念。",
        today - timedelta(days=3), today + timedelta(days=21))
    _add_tasks_if_new(user_id, p8.id, [
        ("需求工程与用例图", today - timedelta(days=1), "done", timedelta(days=1)),
        ("UML 类图与时序图练习", today + timedelta(days=2), "todo", None),
        ("设计模式：单例/工厂/观察者", today + timedelta(days=6), "todo", None),
        ("敏捷开发与 Scrum 流程", today + timedelta(days=10), "todo", None),
        ("软件测试策略与 JUnit", today + timedelta(days=15), "todo", None),
    ])

    p9 = _get_or_create_plan(user_id, "数据结构期末复习",
        "链表、栈队列、树、图、排序算法全面复习。",
        today - timedelta(days=25), today - timedelta(days=3))
    _add_tasks_if_new(user_id, p9.id, [
        ("链表操作（插入/删除/反转）", today - timedelta(days=22), "done", timedelta(days=22)),
        ("栈与队列应用", today - timedelta(days=18), "done", timedelta(days=18)),
        ("二叉树遍历（前中后序）", today - timedelta(days=14), "done", timedelta(days=14)),
        ("二叉搜索树与平衡", today - timedelta(days=8), "done", timedelta(days=8)),
        ("图的 DFS/BFS", today - timedelta(days=4), "todo", None),
        ("最短路径 Dijkstra", today - timedelta(days=2), "todo", None),
        ("排序算法对比总结", today - timedelta(days=1), "todo", None),
    ])

    p10 = _get_or_create_plan(user_id, "学术论文写作方法",
        "学习论文结构、文献综述写作、引用规范。",
        today - timedelta(days=30), today - timedelta(days=5))
    _add_tasks_if_new(user_id, p10.id, [
        ("阅读《学术写作指南》第1-3章", today - timedelta(days=28), "done", timedelta(days=28)),
        ("文献检索与 EndNote 使用", today - timedelta(days=22), "done", timedelta(days=22)),
        ("摘要与引言写作练习", today - timedelta(days=16), "done", timedelta(days=16)),
        ("方法论与实验设计写作", today - timedelta(days=10), "done", timedelta(days=10)),
        ("参考文献格式（APA/GB）", today - timedelta(days=6), "done", timedelta(days=6)),
    ])

    _add_standalone_tasks(user_id, [
        ("整理本周学习笔记并上传", today + timedelta(days=2), "todo", None),
        ("预约图书馆自习座位", today, "done", timedelta(hours=3)),
        ("购买《算法导论》第四版", today + timedelta(days=5), "todo", None),
        ("给导师发邮件确认论文方向", today - timedelta(days=1), "todo", None),
    ])

    # ═══════════════════════════════════════════════════════════
    # 2. Material folders + materials
    # ═══════════════════════════════════════════════════════════

    folders_data = [
        ("数据库", "数据库相关课件、论文、笔记"),
        ("Python学习", "Python 编程与数据分析资料"),
        ("计算机网络", "网络协议与实验资料"),
        ("深度学习", "深度学习课程与论文"),
        ("英语学习", "六级备考、英语文献"),
    ]
    folders = {}
    for name, desc in folders_data:
        folders[name] = _get_or_create_folder(user_id, name, desc)

    materials_data = [
        # (title, file_name, file_type, folder_name, status, summary, keywords)
        ("数据库系统概念 第6版", "database_system_concepts.pdf", "pdf", "数据库", "ready",
         "数据库系统经典教材，涵盖关系模型、SQL、事务管理等核心内容。",
         "数据库,关系模型,SQL,事务,教材"),
        ("MySQL 优化实战笔记", "mysql_optimization.md", "markdown", "数据库", "ready",
         "MySQL 查询优化实战总结，包括索引优化、慢查询分析和配置调优。",
         "MySQL,优化,索引,查询"),
        ("Python 数据分析 案例集", "python_da_cases.ipynb", "notebook", "Python学习", "ready",
         "10 个真实数据分析案例，含 Pandas、Matplotlib、Scikit-learn 代码。",
         "Python,Pandas,数据分析,可视化"),
        ("Pandas 官方文档精华", "pandas_cheatsheet.pdf", "pdf", "Python学习", "ready",
         "Pandas 常用 API 速查，包含数据清洗、变换、聚合操作。",
         "Pandas,API,数据清洗"),
        ("TCP-IP 协议详解 卷1", "tcp_ip_v1.pdf", "pdf", "计算机网络", "ready",
         "TCP/IP 协议栈详细分析，从链路层到应用层的完整讲解。",
         "TCP,IP,协议,网络"),
        ("Wireshark 抓包实验指导", "wireshark_lab.pdf", "pdf", "计算机网络", "ready",
         "Wireshark 实操指南，包含 HTTP/DNS/TCP 抓包实验步骤。",
         "Wireshark,抓包,实验"),
        ("深度学习入门讲义", "deep_learning_notes.pdf", "pdf", "深度学习", "ready",
         "吴恩达课程配套讲义，神经网络、CNN、RNN 等核心概念。",
         "深度学习,神经网络,CNN,讲义"),
        ("CS231n 课程笔记中文版", "cs231n_notes_cn.md", "markdown", "深度学习", "ready",
         "斯坦福 CS231n 课程中文笔记，图像分类、目标检测等。",
         "CS231n,计算机视觉,课程笔记"),
        ("六级真题 2024年6月", "cet6_202406.pdf", "pdf", "英语学习", "ready",
         "2024年6月大学英语六级真题（含答案与解析）。",
         "六级,真题,英语"),
        ("英语写作高分模板", "english_writing_templates.docx", "docx", "英语学习", "ready",
         "六级/考研英语写作常用模板与高分句型总结。",
         "写作,模板,六级"),
        ("操作系统概念 第10版", "os_concepts.pdf", "pdf", None, "ready",
         "操作系统经典教材，进程管理、内存管理、文件系统。",
         "操作系统,进程,内存,文件系统"),
        ("算法竞赛入门经典", "algorithm_contest.pdf", "pdf", None, "processing",
         "ACM/蓝桥杯算法竞赛入门，含 200+ 例题与代码。",
         "算法,竞赛,ACM"),
        ("机器学习数学基础", "ml_math_basics.pdf", "pdf", "深度学习", "failed",
         "线性代数、概率论、优化理论在 ML 中的应用。",
         "数学,机器学习,线性代数"),
    ]

    existing_file_names = {m.file_name for m in Material.query.filter_by(user_id=user_id).all()}
    for m_data in materials_data:
        if m_data[1] in existing_file_names:
            continue
        m = Material(
            user_id=user_id,
            folder_id=folders[m_data[3]].id if m_data[3] in folders else None,
            title=m_data[0], file_name=m_data[1],
            file_path=f"uploads/{user_id}/{m_data[1]}",
            file_type=m_data[2], status=m_data[4],
            summary=m_data[5], keywords=m_data[6],
            index_state="ready" if m_data[4] == "ready" else ("failed" if m_data[4] == "failed" else "not_indexed"),
            created_at=now - timedelta(days=random.randint(1, 20)),
        )
        if m_data[4] == "failed":
            m.error_message = "处理超时，请重新上传或重建索引"
        db.session.add(m)
        stats["materials"] += 1

    # ═══════════════════════════════════════════════════════════
    # 3. Chat history (legacy)
    # ═══════════════════════════════════════════════════════════

    existing_questions = {c.question for c in ChatHistory.query.filter_by(user_id=user_id).all()}
    legacy_chats = [
        ("数据库中的 B+ 树索引和 Hash 索引有什么区别？",
         "B+ 树索引支持范围查询和排序，是数据库中最常用的索引结构。Hash 索引只支持等值查询，不支持范围查询。对于 = 查询，Hash 索引更快；对于 >、<、BETWEEN 等范围查询，必须使用 B+ 树索引。"),
        ("Pandas 中如何高效处理缺失值？",
         "处理缺失值推荐三步法：1) 用 df.isnull().sum() 查看缺失情况；2) 根据业务逻辑选择策略：删除 dropna()（缺失比例高时）、填充 fillna()（均值/中位数/众数/前向填充）、插值 interpolate()；3) 对于分类特征，可以用 'missing' 作为单独类别。"),
        ("TCP 三次握手过程中如果最后一次 ACK 丢了会怎样？",
         "如果第三次握手（客户端 ACK）丢失，服务器会重传 SYN+ACK。客户端因为已经进入 ESTABLISHED 状态，收到重传的 SYN+ACK 后会再次发送 ACK。如果客户端已经在发送数据，数据段的 ACK 标志也能让服务器完成握手，所以通常不会造成连接失败。"),
        ("CNN 卷积神经网络中 1×1 卷积有什么作用？",
         "1×1 卷积主要有三个作用：1) 降维/升维 — 改变通道数而不改变空间尺寸，减少参数量；2) 增加非线性 — 配合激活函数增加模型表达能力；3) 跨通道信息融合 — 在 Inception 和 ResNet 中广泛应用。"),
    ]
    for q, a in legacy_chats:
        if q in existing_questions:
            continue
        h = ChatHistory(user_id=user_id, question=q, answer=a, references_json="[]",
                        created_at=now - timedelta(days=random.randint(1, 7), hours=random.randint(0, 23)))
        db.session.add(h)
        stats["chats"] += 1

    # ═══════════════════════════════════════════════════════════
    # 4. Conversations + Messages
    # ═══════════════════════════════════════════════════════════

    existing_conv_titles = {c.title for c in Conversation.query.filter_by(user_id=user_id).all()}

    if "数据库索引优化讨论" not in existing_conv_titles:
        conv1 = Conversation(
            user_id=user_id, title="数据库索引优化讨论",
            default_scope_json='{"scope_type":"all"}',
            status="active",
            created_at=now - timedelta(days=2), updated_at=now - timedelta(hours=1),
        )
        db.session.add(conv1)
        db.session.flush()
        for role, content, msg_status, created in [
            ("user", "如何分析一条 SQL 语句的执行计划？", "succeeded", timedelta(days=2)),
            ("assistant", "使用 EXPLAIN 或 EXPLAIN ANALYZE 关键字可以查看执行计划。关注 type（访问类型：ALL<index<range<ref<const）、key（使用的索引）、rows（扫描行数）、Extra（Using filesort/Using temporary 需要优化）。", "succeeded", timedelta(days=2)),
            ("user", "如果 type 是 ALL 应该怎么优化？", "succeeded", timedelta(hours=4)),
            ("assistant", "type=ALL 表示全表扫描，优化方法：1) 为 WHERE/JOIN/ORDER BY 列创建索引；2) 使用覆盖索引避免回表；3) 改写查询（如用 INNER JOIN 替代子查询）；4) 考虑分区表减小扫描范围。先用 EXPLAIN 确认索引是否被用到。", "succeeded", timedelta(hours=4)),
            ("user", "覆盖索引是什么？", "succeeded", timedelta(hours=1)),
            ("assistant", "覆盖索引（Covering Index）是指查询所需的所有列都在索引中，不需要回表查聚簇索引。例如 SELECT a,b FROM t WHERE a=1，如果 (a,b) 上有联合索引，就是覆盖索引。EXPLAIN 中 Extra 列会显示 Using index。", "succeeded", timedelta(hours=1)),
        ]:
            db.session.add(Message(conversation_id=conv1.id, user_id=user_id,
                                   role=role, content=content, status=msg_status,
                                   created_at=now - created))
        stats["convs"] += 1

    if "Pandas 数据清洗问题" not in existing_conv_titles:
        conv2 = Conversation(
            user_id=user_id, title="Pandas 数据清洗问题",
            default_scope_json='{"scope_type":"all"}',
            status="active",
            created_at=now - timedelta(days=5), updated_at=now - timedelta(days=5),
        )
        db.session.add(conv2)
        db.session.flush()
        for role, content, msg_status, created in [
            ("user", "Pandas 读取 CSV 文件乱码怎么办？", "succeeded", timedelta(days=5)),
            ("assistant", "使用 encoding 参数指定编码：pd.read_csv('file.csv', encoding='gbk') 或 encoding='utf-8'。如果还乱码，先 detect 编码：用 chardet 库自动检测文件编码。", "succeeded", timedelta(days=5)),
            ("user", "如何合并两个 DataFrame？", "succeeded", timedelta(days=5)),
            ("assistant", "按需求选择：pd.concat([df1, df2]) 纵向拼接（按行）；pd.merge(df1, df2, on='key') 横向关联（类似 SQL JOIN）；df1.join(df2) 按索引关联。merge 支持 left/right/inner/outer 四种连接方式。", "succeeded", timedelta(days=5)),
        ]:
            db.session.add(Message(conversation_id=conv2.id, user_id=user_id,
                                   role=role, content=content, status=msg_status,
                                   created_at=now - created))
        stats["convs"] += 1

    # ═══════════════════════════════════════════════════════════
    # 5. Focus sessions — realistic 14-day history
    # ═══════════════════════════════════════════════════════════

    existing_fs_ids = {fs.client_session_id for fs in FocusSession.query.filter_by(user_id=user_id).all()}

    for days_ago in range(14, 0, -1):
        d = today - timedelta(days=days_ago)
        is_weekday = d.weekday() < 5

        if is_weekday:
            num_sessions = random.choices([1, 2, 3, 0], weights=[30, 40, 20, 10])[0]
        else:
            num_sessions = random.choices([0, 1, 2], weights=[45, 35, 20])[0]

        for i in range(num_sessions):
            cid = f"seed-{d.isoformat()}-{i}"
            if cid in existing_fs_ids:
                continue

            hour = random.randint(8, 22)
            minute = random.randint(0, 59)
            started = datetime(d.year, d.month, d.day, hour, minute, 0)
            duration_min = random.choices([25, 30, 45, 50, 60, 15, 90],
                                          weights=[40, 15, 20, 10, 7, 5, 3])[0]
            duration_sec = duration_min * 60

            db.session.add(FocusSession(
                user_id=user_id, client_session_id=cid,
                started_at=started, ended_at=started + timedelta(seconds=duration_sec),
                duration_seconds=duration_sec, planned_seconds=duration_sec,
                study_date=d, timezone_offset_minutes=-480,
                source="pomodoro", status="completed",
            ))
            stats["fs"] += 1
            stats["fs_minutes"] += duration_min

    # ═══════════════════════════════════════════════════════════
    # Commit & Summary
    # ═══════════════════════════════════════════════════════════
    db.session.commit()

    total_plans = StudyPlan.query.filter_by(user_id=user_id).count()
    total_tasks = StudyTask.query.filter_by(user_id=user_id).count()
    total_materials = Material.query.filter_by(user_id=user_id).count()
    total_folders = MaterialFolder.query.filter_by(user_id=user_id).count()
    total_chats = ChatHistory.query.filter_by(user_id=user_id).count()
    total_convs = Conversation.query.filter_by(user_id=user_id).count()
    total_fs = FocusSession.query.filter_by(user_id=user_id).count()

    print(f"\nEnrichment complete for {user.username}:")
    print(f"  Plans:     {total_plans} total ({stats['plans']} new)")
    print(f"  Tasks:     {total_tasks} total ({stats['tasks']} new)")
    print(f"  Materials: {total_materials} total ({stats['materials']} new) in {total_folders} folders ({stats['folders']} new)")
    print(f"  Chats:     {total_chats} legacy + {total_convs} conversations ({stats['chats']} new chats, {stats['convs']} new convs)")
    print(f"  Focus:     {total_fs} sessions ({stats['fs']} new, {stats['fs_minutes']} new minutes)")


if __name__ == "__main__":
    with app.app_context():
        uid = int(sys.argv[1]) if len(sys.argv) > 1 else None
        if uid is None:
            user = User.query.filter_by(username="test").first()
            if not user:
                # Create test user
                user = User(username="test", nickname="测试同学")
                user.set_password("123456")
                db.session.add(user)
                db.session.commit()
                print(f"Created user test, id={user.id}, password=123456")
            uid = user.id
        enrich(uid)
