"""学科知识图谱内容：地质资源与地质工程。

三层结构：课程（本科/研究生主干课）— 知识点（学科核心概念）— 能力（教学产出）。
关系语义：讲授（课程→知识点）、先修（知识点/课程→课程）、支撑（知识点→能力）、训练（课程→能力）、
评价（课程/知识点→能力）。内容为教学元数据，来源于培养方案与课程大纲的公开描述。
"""

from app.schemas import KnowledgeGraphEdge, KnowledgeGraphNode, KnowledgeGraphResponse

def _nodes() -> list[KnowledgeGraphNode]:
    return [
        # ── 课程 ──────────────────────────────────────────────
        KnowledgeGraphNode(id="petroleum-geology", name="油矿地质学", category="课程", description="油气成藏与勘探地质基础，地质资源与地质工程本科核心课。"),
        KnowledgeGraphNode(id="well-log", name="地球物理测井", category="课程", description="测井曲线采集原理与地层、储层解释方法。"),
        KnowledgeGraphNode(id="seismic-exploration", name="地震勘探原理", category="课程", description="地震波传播、叠加成像与构造解释基础。"),
        KnowledgeGraphNode(id="reservoir-engineering", name="油藏工程", category="课程", description="储量计算、开发方案与动态分析。"),
        KnowledgeGraphNode(id="sedimentology", name="沉积岩石学", category="课程", description="碎屑岩与碳酸盐岩沉积体系及储集砂体分布。"),
        KnowledgeGraphNode(id="structural-geology", name="构造地质学", category="课程", description="变形机制、褶皱断裂与含油气构造解析。"),
        KnowledgeGraphNode(id="reservoir-characterization", name="储层表征与建模", category="课程", description="研究生课程：多尺度储层非均质性与地质建模。"),
        KnowledgeGraphNode(id="well-log-advanced", name="测井资料解释与方法", category="课程", description="研究生课程：复杂储层测井评价与岩石物理建模。"),
        # ── 知识点 ────────────────────────────────────────────
        KnowledgeGraphNode(id="source-rock", name="烃源岩", category="知识点", description="油气生成与有机质演化评价。"),
        KnowledgeGraphNode(id="reservoir", name="储层", category="知识点", description="孔隙度、渗透率与储集空间结构。"),
        KnowledgeGraphNode(id="cap-rock", name="盖层", category="知识点", description="封盖条件与突破压力评价。"),
        KnowledgeGraphNode(id="migration", name="油气运移", category="知识点", description="初次与二次运移路径、动力与输导体系。"),
        KnowledgeGraphNode(id="trap", name="圈闭", category="知识点", description="构造、地层和岩性圈闭的识别与有效性的评价。"),
        KnowledgeGraphNode(id="sequence-stratigraphy", name="层序地层学", category="知识点", description="基准面旋回与体系域划分。"),
        KnowledgeGraphNode(id="diagenesis", name="成岩作用", category="知识点", description="压实、胶结与溶蚀对储层物性的改造。"),
        KnowledgeGraphNode(id="facies-analysis", name="沉积相分析", category="知识点", description="相标志、相模式与平面展布恢复。"),
        KnowledgeGraphNode(id="fold-fault", name="褶皱与断裂", category="知识点", description="断裂封闭性与圈闭构造样式。"),
        KnowledgeGraphNode(id="logging-response", name="测井响应机理", category="知识点", description="岩性、物性、含油性与测井曲线的对应关系。"),
        KnowledgeGraphNode(id="archie", name="阿尔奇公式", category="知识点", description="含水饱和度定量解释的岩石物理基础。"),
        KnowledgeGraphNode(id="porosity-logs", name="孔隙度测井系列", category="知识点", description="声波、密度、中子测井及其交会图技术。"),
        KnowledgeGraphNode(id="resistivity-logs", name="电阻率测井", category="知识点", description="侧向、感应测井与侵入带校正。"),
        KnowledgeGraphNode(id="seismic-waves", name="地震波传播", category="知识点", description="反射系数、速度谱与分辨率极限。"),
        KnowledgeGraphNode(id="seismic-interpretation", name="地震资料解释", category="知识点", description="层位标定、构造圈闭与属性分析。"),
        KnowledgeGraphNode(id="volumetrics", name="储量估算", category="知识点", description="容积法参数取值与不确定性分析。"),
        KnowledgeGraphNode(id="geostatistics", name="地质统计学", category="知识点", description="变差函数与随机建模实现。"),
        # ── 能力 ──────────────────────────────────────────────
        KnowledgeGraphNode(id="logging-interpretation", name="测井解释", category="能力", description="使用测井曲线证据完成岩性、物性、含油性判识。"),
        KnowledgeGraphNode(id="reservoir-evaluation", name="储层评价", category="能力", description="综合地质与工程数据评价储层质量与开发可行性。"),
        KnowledgeGraphNode(id="trap-evaluation", name="圈闭评价", category="能力", description="多源证据综合评价圈闭的有效性与风险。"),
        KnowledgeGraphNode(id="structural-interpretation", name="构造解释", category="能力", description="从地震与构造数据恢复构造样式并制图。"),
        KnowledgeGraphNode(id="geological-mapping", name="地质制图", category="能力", description="编制构造图、沉积相图与储层平面图。"),
        KnowledgeGraphNode(id="reserve-assessment", name="储量评估", category="能力", description="组织参数并完成储量申报级别的估算。"),
    ]

def _edges() -> list[KnowledgeGraphEdge]:
    return [
        # 课程 → 知识点（讲授）
        KnowledgeGraphEdge(source="petroleum-geology", target="source-rock", relation="讲授"),
        KnowledgeGraphEdge(source="petroleum-geology", target="reservoir", relation="讲授"),
        KnowledgeGraphEdge(source="petroleum-geology", target="trap", relation="讲授"),
        KnowledgeGraphEdge(source="petroleum-geology", target="migration", relation="讲授"),
        KnowledgeGraphEdge(source="petroleum-geology", target="cap-rock", relation="讲授"),
        KnowledgeGraphEdge(source="sedimentology", target="facies-analysis", relation="讲授"),
        KnowledgeGraphEdge(source="sedimentology", target="sequence-stratigraphy", relation="讲授"),
        KnowledgeGraphEdge(source="sedimentology", target="diagenesis", relation="讲授"),
        KnowledgeGraphEdge(source="structural-geology", target="fold-fault", relation="讲授"),
        KnowledgeGraphEdge(source="well-log", target="logging-response", relation="讲授"),
        KnowledgeGraphEdge(source="well-log", target="porosity-logs", relation="讲授"),
        KnowledgeGraphEdge(source="well-log", target="resistivity-logs", relation="讲授"),
        KnowledgeGraphEdge(source="seismic-exploration", target="seismic-waves", relation="讲授"),
        KnowledgeGraphEdge(source="seismic-exploration", target="seismic-interpretation", relation="讲授"),
        KnowledgeGraphEdge(source="reservoir-engineering", target="volumetrics", relation="讲授"),
        KnowledgeGraphEdge(source="reservoir-characterization", target="geostatistics", relation="讲授"),
        KnowledgeGraphEdge(source="well-log-advanced", target="archie", relation="讲授"),
        # 先修
        KnowledgeGraphEdge(source="sedimentology", target="petroleum-geology", relation="先修"),
        KnowledgeGraphEdge(source="structural-geology", target="petroleum-geology", relation="先修"),
        KnowledgeGraphEdge(source="petroleum-geology", target="reservoir-engineering", relation="先修"),
        KnowledgeGraphEdge(source="well-log", target="well-log-advanced", relation="先修"),
        KnowledgeGraphEdge(source="petroleum-geology", target="reservoir-characterization", relation="先修"),
        KnowledgeGraphEdge(source="fold-fault", target="trap", relation="支撑"),
        KnowledgeGraphEdge(source="sequence-stratigraphy", target="facies-analysis", relation="支撑"),
        KnowledgeGraphEdge(source="diagenesis", target="reservoir", relation="支撑"),
        KnowledgeGraphEdge(source="facies-analysis", target="reservoir", relation="支撑"),
        # 知识点 → 能力（支撑）
        KnowledgeGraphEdge(source="logging-response", target="logging-interpretation", relation="支撑"),
        KnowledgeGraphEdge(source="porosity-logs", target="logging-interpretation", relation="支撑"),
        KnowledgeGraphEdge(source="resistivity-logs", target="logging-interpretation", relation="支撑"),
        KnowledgeGraphEdge(source="archie", target="logging-interpretation", relation="支撑"),
        KnowledgeGraphEdge(source="reservoir", target="reservoir-evaluation", relation="支撑"),
        KnowledgeGraphEdge(source="diagenesis", target="reservoir-evaluation", relation="支撑"),
        KnowledgeGraphEdge(source="trap", target="trap-evaluation", relation="支撑"),
        KnowledgeGraphEdge(source="migration", target="trap-evaluation", relation="支撑"),
        KnowledgeGraphEdge(source="seismic-interpretation", target="structural-interpretation", relation="支撑"),
        KnowledgeGraphEdge(source="fold-fault", target="structural-interpretation", relation="支撑"),
        KnowledgeGraphEdge(source="facies-analysis", target="geological-mapping", relation="支撑"),
        KnowledgeGraphEdge(source="sequence-stratigraphy", target="geological-mapping", relation="支撑"),
        KnowledgeGraphEdge(source="volumetrics", target="reserve-assessment", relation="支撑"),
        KnowledgeGraphEdge(source="geostatistics", target="reserve-assessment", relation="支撑"),
        # 课程 → 能力（训练/评价）
        KnowledgeGraphEdge(source="well-log", target="logging-interpretation", relation="训练"),
        KnowledgeGraphEdge(source="well-log-advanced", target="logging-interpretation", relation="训练"),
        KnowledgeGraphEdge(source="reservoir-engineering", target="reserve-assessment", relation="训练"),
        KnowledgeGraphEdge(source="reservoir-characterization", target="reservoir-evaluation", relation="训练"),
        KnowledgeGraphEdge(source="seismic-exploration", target="structural-interpretation", relation="训练"),
        KnowledgeGraphEdge(source="petroleum-geology", target="trap-evaluation", relation="评价"),
        KnowledgeGraphEdge(source="petroleum-geology", target="geological-mapping", relation="训练"),
    ]

COURSE_GRAPH = KnowledgeGraphResponse(nodes=_nodes(), edges=_edges())
