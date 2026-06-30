"""Seed sample study plans and tasks for the current user."""
import sys
from datetime import date, timedelta

from app import app
from extensions import db
from models.plan import StudyPlan, StudyTask
from models.user import User
from services.time_service import utc_now

today = date.today()


def seed(user_id):
    user = User.query.get(user_id)
    if not user:
        print(f"User {user_id} not found, creating test user...")
        user = User(username="test", nickname="测试同学")
        user.set_password("123456")
        db.session.add(user)
        db.session.flush()
        user_id = user.id
        print(f"Created user test, id={user_id}, password=123456")

    # ── Plan 1: Active — 数据库系统概论 ──────────────────────────
    p1 = StudyPlan(
        user_id=user_id,
        title="数据库系统概论",
        description="掌握关系模型、SQL 查询优化、事务与并发控制，结合课程 PPT 和教材练习。",
        start_date=today - timedelta(days=10),
        end_date=today + timedelta(days=20),
    )
    db.session.add(p1)
    db.session.flush()

    tasks_p1 = [
        StudyTask(user_id=user_id, plan_id=p1.id, title="阅读第1章 绪论",
                  description="了解数据库系统基本概念、数据模型分类", due_date=today - timedelta(days=8), status="done",
                  completed_at=utc_now() - timedelta(days=8)),
        StudyTask(user_id=user_id, plan_id=p1.id, title="完成关系代数练习（5道题）",
                  description="选择、投影、连接、除运算", due_date=today - timedelta(days=5), status="done",
                  completed_at=utc_now() - timedelta(days=5)),
        StudyTask(user_id=user_id, plan_id=p1.id, title="SQL 单表查询练习",
                  description="WHERE、GROUP BY、HAVING、ORDER BY", due_date=today - timedelta(days=2), status="done",
                  completed_at=utc_now() - timedelta(days=2)),
        StudyTask(user_id=user_id, plan_id=p1.id, title="多表连接与嵌套查询",
                  description="INNER/LEFT/RIGHT JOIN、EXISTS、子查询", due_date=today, status="todo"),
        StudyTask(user_id=user_id, plan_id=p1.id, title="索引与查询优化笔记",
                  description="B+树、哈希索引、EXPLAIN 分析", due_date=today + timedelta(days=3), status="todo"),
        StudyTask(user_id=user_id, plan_id=p1.id, title="事务 ACID 与隔离级别",
                  description="理解脏读、不可重复读、幻读", due_date=today + timedelta(days=7), status="todo"),
        StudyTask(user_id=user_id, plan_id=p1.id, title="期末复习：真题 + 错题回顾",
                  description="复习全书重点，做2套模拟题", due_date=today + timedelta(days=18), status="todo"),
    ]
    for t in tasks_p1:
        db.session.add(t)

    # ── Plan 2: Active — Python 数据分析 ─────────────────────────
    p2 = StudyPlan(
        user_id=user_id,
        title="Python 数据分析实战",
        description="用 Pandas、Matplotlib、Scikit-learn 完成数据清洗到建模全流程。",
        start_date=today - timedelta(days=3),
        end_date=today + timedelta(days=14),
    )
    db.session.add(p2)
    db.session.flush()

    tasks_p2 = [
        StudyTask(user_id=user_id, plan_id=p2.id, title="Pandas 数据读取与清洗",
                  description="read_csv、dropna、fillna、apply", due_date=today - timedelta(days=1), status="done",
                  completed_at=utc_now() - timedelta(days=1)),
        StudyTask(user_id=user_id, plan_id=p2.id, title="数据可视化：Matplotlib 基础",
                  description="折线图、柱状图、散点图、子图布局", due_date=today, status="todo"),
        StudyTask(user_id=user_id, plan_id=p2.id, title="Seaborn 高级图表",
                  description="热力图、箱线图、pairplot", due_date=today + timedelta(days=2), status="todo"),
        StudyTask(user_id=user_id, plan_id=p2.id, title="特征工程与标准化",
                  description="One-Hot、归一化、缺失值处理", due_date=today + timedelta(days=5), status="todo"),
        StudyTask(user_id=user_id, plan_id=p2.id, title="Scikit-learn 分类模型",
                  description="逻辑回归、决策树、随机森林", due_date=today + timedelta(days=9), status="todo"),
    ]
    for t in tasks_p2:
        db.session.add(t)

    # ── Plan 3: Overdue — 计算机网络 ─────────────────────────────
    p3 = StudyPlan(
        user_id=user_id,
        title="计算机网络（自顶向下）",
        description="重点复习应用层、传输层、网络层核心协议，配套 Wireshark 实验。",
        start_date=today - timedelta(days=20),
        end_date=today - timedelta(days=2),
    )
    db.session.add(p3)
    db.session.flush()

    tasks_p3 = [
        StudyTask(user_id=user_id, plan_id=p3.id, title="应用层：HTTP/DNS 协议",
                  due_date=today - timedelta(days=18), status="done",
                  completed_at=utc_now() - timedelta(days=18)),
        StudyTask(user_id=user_id, plan_id=p3.id, title="传输层：TCP 三次握手与拥塞控制",
                  due_date=today - timedelta(days=12), status="done",
                  completed_at=utc_now() - timedelta(days=12)),
        StudyTask(user_id=user_id, plan_id=p3.id, title="网络层：IP 分片与路由算法",
                  due_date=today - timedelta(days=6), status="todo"),
        StudyTask(user_id=user_id, plan_id=p3.id, title="链路层与 Wireshark 抓包实验",
                  due_date=today - timedelta(days=3), status="todo"),
    ]
    for t in tasks_p3:
        db.session.add(t)

    # ── Plan 4: Not started — 操作系统 ───────────────────────────
    p4 = StudyPlan(
        user_id=user_id,
        title="操作系统概念",
        description="进程管理、内存管理、文件系统三大部分。",
        start_date=today + timedelta(days=5),
        end_date=today + timedelta(days=30),
    )
    db.session.add(p4)
    db.session.flush()

    tasks_p4 = [
        StudyTask(user_id=user_id, plan_id=p4.id, title="进程与线程概念",
                  due_date=today + timedelta(days=7), status="todo"),
        StudyTask(user_id=user_id, plan_id=p4.id, title="CPU 调度算法",
                  due_date=today + timedelta(days=10), status="todo"),
        StudyTask(user_id=user_id, plan_id=p4.id, title="死锁检测与避免",
                  due_date=today + timedelta(days=14), status="todo"),
    ]
    for t in tasks_p4:
        db.session.add(t)

    # ── Plan 5: Completed — 线性代数 ─────────────────────────────
    p5 = StudyPlan(
        user_id=user_id,
        title="线性代数考前冲刺",
        description="矩阵运算、特征值、二次型，集中刷题总结。",
        start_date=today - timedelta(days=15),
        end_date=today - timedelta(days=1),
    )
    db.session.add(p5)
    db.session.flush()

    tasks_p5 = [
        StudyTask(user_id=user_id, plan_id=p5.id, title="矩阵运算练习",
                  due_date=today - timedelta(days=13), status="done",
                  completed_at=utc_now() - timedelta(days=13)),
        StudyTask(user_id=user_id, plan_id=p5.id, title="行列式与秩",
                  due_date=today - timedelta(days=9), status="done",
                  completed_at=utc_now() - timedelta(days=9)),
        StudyTask(user_id=user_id, plan_id=p5.id, title="特征值与特征向量",
                  due_date=today - timedelta(days=5), status="done",
                  completed_at=utc_now() - timedelta(days=5)),
        StudyTask(user_id=user_id, plan_id=p5.id, title="二次型与正定矩阵",
                  due_date=today - timedelta(days=2), status="done",
                  completed_at=utc_now() - timedelta(days=2)),
    ]
    for t in tasks_p5:
        db.session.add(t)

    # ── Standalone tasks (no plan) ──────────────────────────────
    standalone = [
        StudyTask(user_id=user_id, title="整理课程笔记到 Notion",
                  due_date=today, status="todo"),
        StudyTask(user_id=user_id, title="下载下周课件并上传知识库",
                  due_date=today + timedelta(days=1), status="todo"),
        StudyTask(user_id=user_id, title="复习昨日 SQL 错题",
                  due_date=today - timedelta(days=1), status="done",
                  completed_at=utc_now() - timedelta(days=1)),
    ]
    for t in standalone:
        db.session.add(t)

    db.session.commit()
    print(f"Seeded: 5 plans, {len(tasks_p1) + len(tasks_p2) + len(tasks_p3) + len(tasks_p4) + len(tasks_p5)} plan tasks, 3 standalone tasks")


if __name__ == "__main__":
    with app.app_context():
        user_id = int(sys.argv[1]) if len(sys.argv) > 1 else 1
        seed(user_id)
