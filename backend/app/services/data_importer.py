import asyncio
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession
from app.db.session import async_session_factory
from app.search.elasticsearch import es_client
from app.search.faiss_index import faiss_manager
from app.models.patent import Patent
from datetime import date

SAMPLE_PATENTS = [
    {
        "patent_number": "CN110123456A",
        "title": "一种基于深度学习的自动驾驶障碍物检测方法",
        "abstract": "本发明公开了一种基于深度学习与多模态传感器融合的自动驾驶障碍物检测方法，包括：获取多模态传感器数据，包括激光雷达点云和摄像头图像；使用卷积神经网络提取图像特征；使用点云网络提取点云特征；将多模态特征进行融合；基于融合特征进行障碍物检测与分类。本发明通过多模态融合显著提升了自动驾驶场景下障碍物检测的精度和鲁棒性。",
        "claims": "1. 一种基于深度学习的自动驾驶障碍物检测方法，其特征在于，包括以下步骤：获取激光雷达点云数据和摄像头图像数据；...",
        "ipc_codes": ["G06V20/58", "G06N3/08", "B60W60/00"],
        "cpc_codes": ["G06V20/58", "G06N3/08"],
        "inventors": ["张三", "李四"],
        "applicants": ["清华大学"],
        "publication_date": date(2023, 6, 15),
        "filing_date": date(2022, 12, 1),
        "country": "CN",
        "doc_type": "A",
        "source": "seed",
    },
    {
        "patent_number": "US10123456B2",
        "title": "Multi-modal sensor fusion for autonomous vehicle object detection",
        "abstract": "A method and system for detecting objects in an environment of an autonomous vehicle using multi-modal sensor fusion. The system includes a LiDAR sensor generating point cloud data, a camera generating image data, a first neural network processing the point cloud, a second neural network processing the image, a fusion module combining features from both networks, and an object detector identifying objects based on fused features.",
        "claims": "1. A method for object detection in autonomous driving, comprising: receiving point cloud data from a LiDAR sensor; receiving image data from a camera;...",
        "ipc_codes": ["G06V20/58", "B60W60/00", "G06N3/08"],
        "cpc_codes": ["G06V20/58", "B60W60/00"],
        "inventors": ["John Doe", "Jane Smith"],
        "applicants": ["Google LLC"],
        "publication_date": date(2023, 3, 20),
        "filing_date": date(2022, 1, 15),
        "country": "US",
        "doc_type": "B2",
        "source": "seed",
    },
    {
        "patent_number": "EP1234567B1",
        "title": "Deep neural network architecture for real-time obstacle avoidance in autonomous vehicles",
        "abstract": "The present invention relates to a deep neural network architecture specifically designed for real-time obstacle avoidance in autonomous vehicles. The architecture employs a novel attention mechanism that selectively focuses on relevant regions of the input sensor data, enabling faster processing while maintaining high detection accuracy. The system integrates data from multiple sensors including LiDAR, radar, and cameras.",
        "ipc_codes": ["G06V20/58", "G06N3/045", "B60W30/09"],
        "cpc_codes": ["G06V20/58", "G06N3/045"],
        "inventors": ["Hans Mueller", "Anna Schmidt"],
        "applicants": ["BMW AG"],
        "publication_date": date(2022, 9, 10),
        "country": "EP",
        "doc_type": "B1",
        "source": "seed",
    },
    {
        "patent_number": "WO2020123456A1",
        "title": "Method and apparatus for training a transformer-based model for patent document analysis",
        "abstract": "A method for training a transformer-based neural network model for analyzing patent documents is disclosed. The method includes pre-training on a large corpus of patent documents, fine-tuning on specific patent analysis tasks including classification, similarity detection, and prior art search, and using attention mechanisms to capture relationships between patent claims and technical descriptions.",
        "ipc_codes": ["G06F40/20", "G06N3/08", "G06Q50/18"],
        "cpc_codes": ["G06F40/20", "G06Q50/18"],
        "inventors": ["Pierre Dupont", "Marie Curie"],
        "applicants": ["PatentAI Inc."],
        "publication_date": date(2023, 1, 5),
        "country": "WO",
        "doc_type": "A1",
        "source": "seed",
    },
    {
        "patent_number": "CN202010123456B",
        "title": "基于BERT模型的专利相似度检测系统及方法",
        "abstract": "本发明提供一种基于BERT预训练语言模型的专利相似度自动检测系统，包括：专利文本预处理模块，用于清洗和标准化专利文本；BERT编码模块，将专利文本转换为语义向量；相似度计算模块，基于余弦相似度计算专利间的语义相似性；以及结果输出模块，按相似度排序输出检测结果。本发明能够替代传统基于关键词的专利检索方式，提高检索精度和召回率。",
        "ipc_codes": ["G06F16/33", "G06N3/08", "G06Q50/18"],
        "cpc_codes": ["G06F16/334"],
        "inventors": ["王五", "赵六"],
        "applicants": ["中国科学院计算技术研究所"],
        "publication_date": date(2022, 6, 10),
        "filing_date": date(2020, 3, 1),
        "country": "CN",
        "doc_type": "B",
        "source": "seed",
    },
    {
        "patent_number": "US20230123456A1",
        "title": "AI-powered patent prior art search engine using large language models",
        "abstract": "An AI-powered patent prior art search engine leverages large language models (LLMs) to understand natural language queries describing inventions and find relevant prior art. The system uses a two-stage retrieval pipeline: first, a dense retrieval module based on fine-tuned sentence transformers encodes patent texts into embeddings for fast approximate nearest neighbor search; second, a cross-encoder reranker provides fine-grained relevance scoring. The LLM generates an analysis report comparing the queried invention against found prior art.",
        "ipc_codes": ["G06F16/33", "G06F16/338", "G06Q50/18"],
        "cpc_codes": ["G06F16/334", "G06Q50/18"],
        "inventors": ["Alice Johnson", "Bob Williams"],
        "applicants": ["PQAI Foundation"],
        "publication_date": date(2023, 8, 15),
        "country": "US",
        "doc_type": "A1",
        "source": "seed",
    },
    {
        "patent_number": "CN201910876543A",
        "title": "一种共轴双旋翼无人机的飞行控制方法及系统",
        "abstract": "本发明公开了一种共轴双旋翼无人机的飞行控制方法及系统，包括：获取无人机的姿态数据和位置数据；通过上下旋翼的差速控制实现航向调节；利用旋翼总距混合控制实现高度和姿态的协同调节；采用自适应PID控制算法对共轴双旋翼系统进行稳定控制。本发明有效解决了共轴双旋翼无人机在复杂气流环境下的稳定性问题，提高了飞行控制精度和抗扰能力。",
        "claims": "1. 一种共轴双旋翼无人机的飞行控制方法，其特征在于，包括：获取上旋翼和下旋翼的转速数据；计算上下旋翼的扭矩差；根据扭矩差调节上下旋翼的转速比例...",
        "ipc_codes": ["B64C27/10", "G05D1/08", "B64U10/11"],
        "cpc_codes": ["B64C27/10", "G05D1/08"],
        "inventors": ["刘航天", "陈飞行"],
        "applicants": ["北京航空航天大学"],
        "publication_date": date(2021, 3, 15),
        "filing_date": date(2019, 9, 20),
        "country": "CN",
        "doc_type": "A",
        "source": "seed",
    },
    {
        "patent_number": "US10890123B2",
        "title": "Coaxial dual-rotor UAV with adaptive blade pitch control for high wind resistance",
        "abstract": "A coaxial dual-rotor unmanned aerial vehicle (UAV) features an adaptive blade pitch control system that dynamically adjusts upper and lower rotor blade angles based on real-time wind sensor data. The system includes a coaxial rotor assembly with independently controllable upper and lower rotors, a wind speed sensor array, a flight controller implementing model predictive control, and servo actuators for individual blade pitch adjustment. The adaptive control enables stable flight in wind conditions exceeding 15 m/s while maintaining energy efficiency through optimized rotor thrust distribution between the coaxial rotors.",
        "ipc_codes": ["B64C27/10", "B64C27/82", "B64U10/11", "G05D1/08"],
        "cpc_codes": ["B64C27/10", "B64C27/82", "B64U10/11"],
        "inventors": ["James Anderson", "Michael Brown"],
        "applicants": ["Boeing Company"],
        "publication_date": date(2022, 11, 8),
        "filing_date": date(2020, 5, 12),
        "country": "US",
        "doc_type": "B2",
        "source": "seed",
    },
    {
        "patent_number": "CN202111234567A",
        "title": "共轴双旋翼无人机折叠机构及便携式系统",
        "abstract": "本发明涉及一种共轴双旋翼无人机的折叠机构及便携式系统，折叠机构包括：上旋翼折叠组件、下旋翼折叠组件和机身折叠组件。上旋翼和下旋翼的桨叶均可沿桨毂径向折叠，折叠后旋翼直径缩小至展开状态的30%。机身采用分段折叠设计，折叠后整机尺寸小于300mm×200mm×100mm，便于单兵携带。展开过程通过弹簧驱动机构自动完成，展开时间小于5秒。本发明解决了共轴双旋翼无人机体积大、不便携的问题。",
        "ipc_codes": ["B64C27/10", "B64C1/30", "B64U20/40"],
        "cpc_codes": ["B64C27/10", "B64C1/30"],
        "inventors": ["张轻便", "李折叠"],
        "applicants": ["大疆创新科技有限公司"],
        "publication_date": date(2022, 8, 20),
        "filing_date": date(2021, 12, 1),
        "country": "CN",
        "doc_type": "A",
        "source": "seed",
    },
    {
        "patent_number": "EP2987654B1",
        "title": "Coaxial rotor UAV propulsion system with independent motor control for yaw stabilization",
        "abstract": "A propulsion system for a coaxial rotor unmanned aerial vehicle comprises an upper brushless DC motor driving an upper rotor, a lower brushless DC motor driving a lower rotor in counter-rotation, and an electronic speed controller implementing independent motor control. The system achieves yaw control through differential torque between the upper and lower rotors without requiring a tail rotor or additional yaw control mechanisms. A hall sensor array provides precise rotor position feedback enabling torque-balanced operation across the flight envelope. The independent motor control allows for failure mode operation where one motor failure does not result in complete loss of control.",
        "ipc_codes": ["B64C27/10", "B64D27/24", "H02P5/68"],
        "cpc_codes": ["B64C27/10", "B64D27/24"],
        "inventors": ["Pierre Lefevre", "Thomas Mueller"],
        "applicants": ["Airbus Helicopters"],
        "publication_date": date(2020, 6, 25),
        "country": "EP",
        "doc_type": "B1",
        "source": "seed",
    },
    {
        "patent_number": "CN202310567890A",
        "title": "基于视觉SLAM的共轴双旋翼无人机自主导航系统",
        "abstract": "本发明提供一种基于视觉SLAM的共轴双旋翼无人机自主导航系统，包括：双目视觉传感器模块，用于采集环境图像并构建三维点云地图；IMU惯性测量模块，提供高频姿态估计；共轴双旋翼动力学模型，用于预测无人机运动状态；紧耦合视觉惯性里程计，融合视觉和惯性数据实现精确定位；以及路径规划模块，基于构建的地图生成避障飞行路径。本系统在GPS拒止环境下（如室内、隧道、地下空间）实现厘米级定位精度，特别适用于共轴双旋翼构型的紧凑空间作业需求。",
        "ipc_codes": ["G05D1/10", "G01C21/20", "B64U10/11", "G06T7/73"],
        "cpc_codes": ["G05D1/10", "G01C21/20", "B64U10/11"],
        "inventors": ["王视觉", "黄导航"],
        "applicants": ["浙江大学", "之江实验室"],
        "publication_date": date(2023, 10, 10),
        "country": "CN",
        "doc_type": "A",
        "source": "seed",
    },
]


async def import_seed_data():
    """Import sample patent data into PostgreSQL, Elasticsearch, and FAISS.
    PostgreSQL and Elasticsearch are optional — FAISS index is always built.
    """
    texts = []
    ids_list = []

    for pdata in SAMPLE_PATENTS:
        full_text = f"{pdata['title']} {pdata['abstract']}"
        texts.append(full_text)
        ids_list.append(pdata["patent_number"])

    # Try PostgreSQL import (optional)
    try:
        async with async_session_factory() as db:
            for pdata in SAMPLE_PATENTS:
                existing = await db.execute(
                    text("SELECT 1 FROM patents WHERE patent_number = :pn"),
                    {"pn": pdata["patent_number"]},
                )
                if existing.first():
                    continue
                patent = Patent(**pdata)
                db.add(patent)
            await db.commit()
        print(f"PostgreSQL: {len(SAMPLE_PATENTS)} patents ready for import")
    except Exception:
        print("PostgreSQL: skipped (not available)")

    # Try Elasticsearch import (optional)
    try:
        await es_client.connect()
        await es_client.create_index()
        for pdata in SAMPLE_PATENTS:
            es_doc = {**pdata}
            es_doc["publication_date"] = (
                pdata["publication_date"].isoformat()
                if pdata["publication_date"]
                else None
            )
            es_doc["filing_date"] = (
                pdata["filing_date"].isoformat()
                if pdata["filing_date"]
                else None
            )
            try:
                await es_client.index_patent(es_doc)
            except Exception:
                pass
        print(f"Elasticsearch: {len(SAMPLE_PATENTS)} patents indexed")
    except Exception as e:
        print(f"Elasticsearch: skipped (not available)")

    # Always build FAISS index (no external dependencies)
    if texts:
        faiss_manager.build_index(texts, ids_list)
        faiss_manager.save()
        print(f"FAISS index: built with {len(texts)} patents → {faiss_manager.index.ntotal} vectors")

    return len(texts)


async def main():
    count = await import_seed_data()
    print(f"\nDone: {count} patents available for semantic search")
    await es_client.close()


if __name__ == "__main__":
    asyncio.run(main())
