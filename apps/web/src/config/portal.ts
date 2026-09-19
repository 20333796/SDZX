import type { PortalConfig } from '@/types'

export const fallbackPortalConfig: PortalConfig = {
  navigation: [
    {
      title: '知源智汇',
      links: [
        { label: 'AI智慧课程', target: 'resources', category: 'courses' },
        { label: '学科知识图谱', target: 'knowledge-graph' },
        { label: '地学数据', target: 'geo-data' }
      ]
    },
    {
      title: '因材智教',
      links: [
        { label: '学情诊断', target: 'learning-diagnosis' },
        { label: '智能研学', target: 'learning-tasks' },
        { label: '导师图谱', target: 'mentor-graph' }
      ]
    },
    {
      title: '实践智导',
      links: [
        { label: '虚拟仿真', target: 'practice-simulation' },
        { label: '野外实训', target: 'field-training' },
        { label: '工程案例', target: 'case-library' }
      ]
    },
    {
      title: '能力智验',
      links: [
        { label: '智能应用', target: 'geology-design' },
        { label: '独立能力测评', target: 'capability-assessment' },
        { label: '成长画像', target: 'learning-profile' }
      ]
    }
  ],
  stats: [
    { value: '45+', label: '课程资源' },
    { value: '03', label: '学习路径' },
    { value: '试运行', label: '开放状态' }
  ]
}
