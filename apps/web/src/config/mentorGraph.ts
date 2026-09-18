export type MentorSchool = string

export type Mentor = {
  id: string
  name: string
  school: MentorSchool
  unit?: string
  title: string
  directions: string[]
  courses?: string[]
  mentorTypes?: string[]
  subjects?: string[]
  summary: string
  sourceUrl: string
}

// Data is transcribed only from the public faculty pages linked below. The graph deliberately does
// not infer contact details, supervision quotas, or course assignments that are absent from a page.
export const mentorSourcePages = {
  facultyPortal: 'https://faculty.cup.edu.cn/zgsydxbjjszy/jscx/index.htm',
  geophysicsFaculty: 'https://www.cup.edu.cn/geophysics/szdw/js/index.htm',
  geoscienceFaculty: 'https://www.cup.edu.cn/geosci/szdw/jiaoshou/index.htm',
  geoscienceDirections: 'https://www.cup.edu.cn/geosci/kxyj/yjfx/index.htm'
} as const

const verifiedMentors: Mentor[] = [
  {
    id: 'yang-tao', name: '杨涛', school: '地球物理学院', title: '教授',
    directions: ['油气地质与地球物理', '智能测井与解释'],
    summary: '官网个人页列示油气地质与地球物理、智能测井与解释等研究方向。',
    sourceUrl: 'https://www.cup.edu.cn/geophysics/szdw/js/56c231b1f358451da8bdea26a3583c34.htm'
  },
  {
    id: 'wang-shangxu', name: '王尚旭', school: '地球物理学院', title: '教授',
    directions: ['地震勘探', '岩石物理实验'],
    summary: '主要从事地震勘探，涵盖岩石物理实验、地震物理模型实验与地震信号分析和反演。',
    sourceUrl: 'https://www.cup.edu.cn/geophysics/szdw/js/155652.htm'
  },
  {
    id: 'chen-xiaohong', name: '陈小宏', school: '地球物理学院', title: '教授',
    directions: ['地震反演', '时移地震油藏监测'],
    summary: '官网介绍其从事地震反演、地震资料处理和时移地震油藏监测研究。',
    sourceUrl: 'https://www.cup.edu.cn/geophysics/szdw/js/155655.htm'
  },
  {
    id: 'zhang-feng', name: '张峰', school: '地球物理学院', title: '教授',
    directions: ['地震正演和反演', '地震多波和各向异性', '储层岩石物理'],
    courses: ['岩石物理学'],
    summary: '研究方向包括地震正反演、多波与各向异性、非常规油气储层岩石物理。',
    sourceUrl: 'https://www.cup.edu.cn/geophysics/szdw/js/68636d147e89414b865fc52be2a0931d.htm'
  },
  {
    id: 'yuan-sanyi', name: '袁三一', school: '地球物理学院', title: '教授',
    directions: ['地球物理信号处理', '油气人工智能', '地震地质工程一体化'],
    summary: '官网列示地球物理信号处理、油气人工智能、地震地质工程一体化等方向。',
    sourceUrl: 'https://www.cup.edu.cn/geophysics/szdw/js/9310716.htm'
  },
  {
    id: 'li-jingye', name: '李景叶', school: '地球物理学院', title: '教授',
    directions: ['地震储层预测与动态监测', '智能地球物理技术'],
    summary: '研究方向为地震储层预测与动态监测、智能地球物理技术与软件研发。',
    sourceUrl: 'https://www.cup.edu.cn/geophysics/szdw/js/155605.htm'
  },
  {
    id: 'wang-tieguan', name: '王铁冠', school: '地球科学学院', title: '教授',
    directions: ['分子有机地球化学', '石油地质学', '油藏地球化学'],
    summary: '官网个人页列示分子有机地球化学、石油地质学、油藏地球化学等专业领域。',
    sourceUrl: 'https://www.cup.edu.cn/geosci/szdw/jiaoshou/50638.htm'
  },
  {
    id: 'pang-xiongqi', name: '庞雄奇', school: '地球科学学院', title: '教授',
    directions: ['油气藏形成与分布规律', '油气成藏机理'],
    summary: '长期从事油气藏形成与分布规律研究，个人页介绍其油气成藏理论与定量评价工作。',
    sourceUrl: 'https://www.cup.edu.cn/geosci/szdw/jiaoshou/50728.htm'
  },
  {
    id: 'zhu-xiaomin', name: '朱筱敏', school: '地球科学学院', title: '教授',
    directions: ['沉积地质学', '储层地质学', '层序地层学', '地震沉积学'],
    courses: ['沉积岩石学', '层序地层学'],
    summary: '从事沉积地质学、储层地质学、层序地层学、地震沉积学和含油气盆地分析。',
    sourceUrl: 'https://www.cup.edu.cn/geosci/szdw/jiaoshou/50639.htm'
  },
  {
    id: 'wu-shenghe', name: '吴胜和', school: '地球科学学院', title: '教授',
    directions: ['油气田开发地质学', '沉积古地理学'],
    courses: ['油矿地质学'],
    summary: '官网说明其从事油气田开发地质学及沉积古地理学教学与科研工作。',
    sourceUrl: 'https://www.cup.edu.cn/geosci/szdw/jiaoshou/50673.htm'
  },
  {
    id: 'qiu-nansheng', name: '邱楠生', school: '地球科学学院', title: '教授',
    directions: ['沉积盆地温压场', '盆地构造-热演化', '地热资源评价'],
    summary: '研究领域包括沉积盆地温压场、盆地构造-热演化、油气成藏机理与地热资源评价。',
    sourceUrl: 'https://www.cup.edu.cn/geosci/szdw/jiaoshou/50659.htm'
  },
  {
    id: 'cai-chunfang', name: '蔡春芳', school: '地球科学学院', title: '教授',
    directions: ['有机-无机相互作用', '油气源对比与成藏', '储层沉积与地球化学'],
    summary: '官网列示有机-无机相互作用、油气源对比与成藏、储层沉积与地球化学等研究领域。',
    sourceUrl: 'https://www.cup.edu.cn/geosci/szdw/jiaoshou/bc263c203fc44e8faa2b624011ac3581.htm'
  }
]

type OfficialTeacher = readonly [MentorSchool, string, string, string]

// Full public directory transcribed from the three faculty-list pages of each college: professor,
// associate professor, and lecturer. A teacher is not given a direction unless it was verified from
// that teacher's public profile above.
const officialTeacherDirectory: OfficialTeacher[] = [
  ['地球物理学院', '教授', '杨涛', '56c231b1f358451da8bdea26a3583c34.htm'],
  ['地球物理学院', '教授', '王尚旭', '155652.htm'],
  ['地球物理学院', '教授', '肖立志', '155668.htm'],
  ['地球物理学院', '教授', '陈小宏', '155655.htm'],
  ['地球物理学院', '教授', '周辉', '155674.htm'],
  ['地球物理学院', '教授', '张峰', '68636d147e89414b865fc52be2a0931d.htm'],
  ['地球物理学院', '教授', '袁三一', '9310716.htm'],
  ['地球物理学院', '教授', '李景叶', '155605.htm'],
  ['地球物理学院', '教授', '谢然红', '155654.htm'],
  ['地球物理学院', '教授', '刘洋', 'd3ed5a9ee3354740ba8133e5fef3dac9.htm'],
  ['地球物理学院', '教授', '柯式镇', '155604.htm'],
  ['地球物理学院', '教授', '高杰', '155658.htm'],
  ['地球物理学院', '教授', '岳文正', '155669.htm'],
  ['地球物理学院', '教授', '李国发', '155646.htm'],
  ['地球物理学院', '教授', '王守东', '165708.htm'],
  ['地球物理学院', '教授', '车小花', '155647.htm'],
  ['地球物理学院', '教授', '吴文圣', '165643.htm'],
  ['地球物理学院', '教授', '陈双全', '9310715.htm'],
  ['地球物理学院', '教授', '廖广志', '06885c50e39e49af8671cea91506344b.htm'],
  ['地球物理学院', '教授', '刘国昌', '8201ce981b99433dbc734bee8bbd73fc.htm'],
  ['地球物理学院', '教授', '黄炜霖', '13b457649de54bba91e2ca144452e19a.htm'],
  ['地球物理学院', '教授', '唐跟阳', '9222dcf9fad8447087c3bc066be68546.htm'],
  ['地球物理学院', '教授', '王兵', '3782aad2eae04bbd9cdb4436a2d5cbb8.htm'],
  ['地球物理学院', '教授', '卢俊强', '9a19199d386741cdad099f12f25274ea.htm'],
  ['地球物理学院', '教授', '马继涛', '6401ee4942304996a53bbcebe2d71248.htm'],
  ['地球物理学院', '教授', '贺艳晓', '5f2dc67c97104d06bdccd14cc128be73.htm'],
  ['地球物理学院', '教授', '潘新朋', '24a4fbeedb454e5ea1e5698dc591b40b.htm'],
  ['地球物理学院', '教授', '聂昕', '2d055851ae93463aad479b4712700d69.htm'],
  ['地球物理学院', '教授', '赵培强', '8c5ac33bdbaf45faa1eca4441b98a4b4.htm'],
  ['地球物理学院', '教授', '陈汉明', '088f5947745c4961a2455fe699a68f71.htm'],
  ['地球物理学院', '教授', '钮凤林（兼）', 'a6523c308a7f44a2be65f06adb770c12.htm'],
  ['地球物理学院', '教授', '饶莹（兼）', '159804.htm'],
  ['地球物理学院', '教授', '谢玉洪（兼）', 'ca42df08cc7e4309bc96900b815469ea.htm'],
  ['地球物理学院', '教授', '姚刚（兼）', '5188869f687c4089988c9a5337cbedfa.htm'],
  ['地球物理学院', '教授', '陈海潮（兼）', 'ab5cd94440c44f518c9a036af96c2c21.htm'],
  ['地球物理学院', '副教授', '宋炜', '155566.htm'],
  ['地球物理学院', '副教授', '张元中', '155693.htm'],
  ['地球物理学院', '副教授', '安勇', '155695.htm'],
  ['地球物理学院', '副教授', '付建伟', '155678.htm'],
  ['地球物理学院', '副教授', '孙朗秋', '155685.htm'],
  ['地球物理学院', '副教授', '唐有彩', '159890.htm'],
  ['地球物理学院', '副教授', '张岩', '156290.htm'],
  ['地球物理学院', '副教授', '刘立峰', '155684.htm'],
  ['地球物理学院', '副教授', '吴迪', '159866.htm'],
  ['地球物理学院', '副教授', '骆春妹', '165644.htm'],
  ['地球物理学院', '副教授', '董春晖', '9310714.htm'],
  ['地球物理学院', '副教授', '丁拼搏', '2020a2c03bae4e74aec30f2721edc597.htm'],
  ['地球物理学院', '副教授', '赵振聪', '04da24a97b5a4b85a0df1699482ec569.htm'],
  ['地球物理学院', '副教授', '陈涛', '9dd3413b935a437ba1875a66bde43a6d.htm'],
  ['地球物理学院', '副教授', '刘晓惠', '2e23bcb352344d5b95f19125d26c7f04.htm'],
  ['地球物理学院', '副教授', '金国文', '9deb5446e74849b38b05b611c3fc45e1.htm'],
  ['地球物理学院', '副教授', '谢佥', '897df96b16404a82bf4c1bcbb7afe46b.htm'],
  ['地球物理学院', '讲师', '梅金顺', '159954.htm'],
  ['地球物理学院', '讲师', '胡亮尘', '159895.htm'],
  ['地球物理学院', '讲师', '范华军', '159282.htm'],
  ['地球物理学院', '讲师', '门百永', '159878.htm'],
  ['地球物理学院', '讲师', '谢豪', '159884.htm'],
  ['地球物理学院', '讲师', '王坤喜', 'b7ea1888339e47de880b4c090c4b5ffd.htm'],
  ['地球物理学院', '讲师', '王松', 'cdb02645f9fc4800a2b820576e7a66d0.htm'],

  ['地球科学学院', '教授', '王铁冠', '50638.htm'],
  ['地球科学学院', '教授', '杨涛', '617d6f611bfb461992bb17a2bbe91a3d.htm'],
  ['地球科学学院', '教授', '庞雄奇', '50728.htm'],
  ['地球科学学院', '教授', '朱筱敏', '50639.htm'],
  ['地球科学学院', '教授', '柳广弟', '50640.htm'],
  ['地球科学学院', '教授', '吴胜和', '50673.htm'],
  ['地球科学学院', '教授', '钟宁宁', '50674.htm'],
  ['地球科学学院', '教授', '邱楠生', '50659.htm'],
  ['地球科学学院', '教授', '曾联波', '50653.htm'],
  ['地球科学学院', '教授', '曾溅辉', '50662.htm'],
  ['地球科学学院', '教授', '蔡春芳', 'bc263c203fc44e8faa2b624011ac3581.htm'],
  ['地球科学学院', '教授', '鲍志东', '50729.htm'],
  ['地球科学学院', '教授', '蒋恕', '95a1eb8450814a09918e94533a3bb03f.htm'],
  ['地球科学学院', '教授', '刘建妮', '6ec6a2f855b1408fb289bb66aef7cf5d.htm'],
  ['地球科学学院', '教授', '王贵文', '50651.htm'],
  ['地球科学学院', '教授', '姜福杰', '164418.htm'],
  ['地球科学学院', '教授', '蔡建超', '7a2507045b4f4b4181653eb86e500bbf.htm'],
  ['地球科学学院', '教授', '罗情勇', 'fa71d06363b94de99db437d1ad540bb1.htm'],
  ['地球科学学院', '教授', '王飞宇', 'db9c8ce528bd4d7987bbc1475d918fdc.htm'],
  ['地球科学学院', '教授', '陈践发', '50668.htm'],
  ['地球科学学院', '教授', '王志章', '50654.htm'],
  ['地球科学学院', '教授', '童亨茂', '50739.htm'],
  ['地球科学学院', '教授', '李素梅', '50641.htm'],
  ['地球科学学院', '教授', '刘成林', '50749.htm'],
  ['地球科学学院', '教授', '季汉成', '50650.htm'],
  ['地球科学学院', '教授', '陈书平', '83162.htm'],
  ['地球科学学院', '教授', '李美俊', '83163.htm'],
  ['地球科学学院', '教授', '谢庆宾', '147869.htm'],
  ['地球科学学院', '教授', '鲜本忠', '1d7696c8f3834ea1acd00c035473cb06.htm'],
  ['地球科学学院', '教授', '于福生', '147870.htm'],
  ['地球科学学院', '教授', '陈冬霞', '3b37728c9d3d426ea6990aecfb2045ca.htm'],
  ['地球科学学院', '教授', '岳大力', '179927.htm'],
  ['地球科学学院', '教授', '龚承林', '179960.htm'],
  ['地球科学学院', '教授', '高岗', '799019f5d66e4c449bf05585fc3385aa.htm'],
  ['地球科学学院', '教授', '牛花朋', '7d13c2ced77b498a95ca05a3c491516f.htm'],
  ['地球科学学院', '教授', '刘小平', 'fc8da2c92685471f99d91ae8850387a6.htm'],
  ['地球科学学院', '教授', '朱世发', 'fa484b82010d47399f3ad363a698b72c.htm'],
  ['地球科学学院', '教授', '能源', '153674455bcd4990bdae461950c17b13.htm'],
  ['地球科学学院', '教授', '葛智渊', '99908b90234b4683a68e0e1139a597a8.htm'],
  ['地球科学学院', '教授', '李平平', '450f9000874e4d2da674dd24c3911cb4.htm'],
  ['地球科学学院', '教授', '廖宗湖', 'd6353f58dc9849e1a02ae2e1182fe9d9.htm'],
  ['地球科学学院', '教授', '常健', 'adfe35abdf304bbebc9794af72e71ec7.htm'],
  ['地球科学学院', '教授', '倪云燕', '82fabe61e16f4a12a99f6436c11b957b.htm'],
  ['地球科学学院', '教授', '刘钰铭', '94905868f4eb4def9f4f6da600d36fd7.htm'],
  ['地球科学学院', '教授', '张琴', '4c59c05a94da4ab1b63b8b34199d2714.htm'],
  ['地球科学学院', '教授', '朱传庆', '1cd3d4137cdd4f47aa6a7083fe790127.htm'],
  ['地球科学学院', '教授', '余一欣', '0d525c55c5844754bb5f26604a8d201b.htm'],
  ['地球科学学院', '教授', '李庆', 'fc2ff32f622642fbba1c19e809befbc3.htm'],
  ['地球科学学院', '教授', '宋泽章', 'f012667e5c704031b01d3919fb66401d.htm'],
  ['地球科学学院', '教授', '孙晶', 'd2360d32b2c74db5ad0a951110afc879.htm'],
  ['地球科学学院', '教授', '倪智勇', 'cd0756de1b9b49bd80f901245ad17434.htm'],
  ['地球科学学院', '教授', '刘汇川', '26f4c956d409486bac7a5e045a1deb5d.htm'],
  ['地球科学学院', '教授', '王俊辉', '2906462d062d4d56b795df85f19ee1ef.htm'],
  ['地球科学学院', '教授', '马勇', '37f389f81b5a41499546a83f5c8701d7.htm'],
  ['地球科学学院', '教授', '庞宏', '3b939fc02f5743339bc658a9c09cbd0a.htm'],
  ['地球科学学院', '教授', '赖锦', 'b86809cc19784ca08960bddf6aa71b52.htm'],
  ['地球科学学院', '教授', '沈卫兵', '4e78bb8ea93443ff90bd9ffa9e895232.htm'],
  ['地球科学学院', '教授', '宋到福', '50df22d56c1a482893f8b1defc7a7cf3.htm'],
  ['地球科学学院', '副教授', '周子勇', '50740.htm'],
  ['地球科学学院', '副教授', '吴欣松', '50748.htm'],
  ['地球科学学院', '副教授', '尹志军', '50750.htm'],
  ['地球科学学院', '副教授', '向才富', '50753.htm'],
  ['地球科学学院', '副教授', '李潍莲', '50759.htm'],
  ['地球科学学院', '副教授', '朱毅秀', '50761.htm'],
  ['地球科学学院', '副教授', '王广利', 'd66f6eeca6da4169bd011f429b98f133.htm'],
  ['地球科学学院', '副教授', '张同钢', '51664.htm'],
  ['地球科学学院', '副教授', '罗良', '100957.htm'],
  ['地球科学学院', '副教授', '吴嘉', '100960.htm'],
  ['地球科学学院', '副教授', '董艳蕾', '50775.htm'],
  ['地球科学学院', '副教授', '方琳浩', '109224.htm'],
  ['地球科学学院', '副教授', '刘志娜', '109225.htm'],
  ['地球科学学院', '副教授', '陈石', '131473.htm'],
  ['地球科学学院', '副教授', '梁婷', '131475.htm'],
  ['地球科学学院', '副教授', '周勇', '147879.htm'],
  ['地球科学学院', '副教授', '陈睿倩', '147882.htm'],
  ['地球科学学院', '副教授', '孙海涛', '179951.htm'],
  ['地球科学学院', '副教授', '徐朝晖', '179959.htm'],
  ['地球科学学院', '副教授', '李壮', '179873.htm'],
  ['地球科学学院', '副教授', '李芳玉', 'c1a41caefdfb496da632eafa4008ffd6.htm'],
  ['地球科学学院', '副教授', '张永旺', '478d73b1298949dba169fddd14b00b23.htm'],
  ['地球科学学院', '副教授', '孙盼科', '59647a344ed24546869e8bc4b81d7185.htm'],
  ['地球科学学院', '副教授', '吕文雅', '91c06487f90c4fbfa966b8366cf0e85f.htm'],
  ['地球科学学院', '副教授', '王海洲', '847741c89f16418a94a703b0fbc1b232.htm'],
  ['地球科学学院', '副教授', '彭旸', '4a373ca628c24983911a2a987104e89c.htm'],
  ['地球科学学院', '副教授', '孙晨皓', 'b86a5d2fe46d4a6b98adf4b46db574c7.htm'],
  ['地球科学学院', '副教授', '乔锦琪', '020d7d4c0276434db912407c6e6a1b20.htm'],
  ['地球科学学院', '副教授', '李伟', '8b761c949f614b65bd6c7c2aa8633f0b.htm'],
  ['地球科学学院', '副教授', '江强', '99cb4413caaf487484da280c79a11753.htm'],
  ['地球科学学院', '副教授', '黄永辉', 'b62fd116e7434e13b352367ee3a52399.htm'],
  ['地球科学学院', '副教授', '乔俊程', '0d34706c7c014b348aedbb42e3594849.htm'],
  ['地球科学学院', '副教授', '胡涛', 'b8bd605ac2314b27b9ff27b913c7cf5c.htm'],
  ['地球科学学院', '副教授', 'Thomas Bernard', '0ab90d5e1a7f42fcb9a4e241c9edd42c.htm'],
  ['地球科学学院', '副教授', '陈迪', 'c8804266a5b74c938d02ac78173f9087.htm'],
  ['地球科学学院', '副教授', '徐振华', '275f772854624c1fa125d76536904e22.htm'],
  ['地球科学学院', '副教授', '王武荣', '21794c3d6f9640f7a1896a4800d5bcdf.htm'],
  ['地球科学学院', '副教授', '肖洪', 'eb7fc3ec9a4147b2a75e4ca2fa94f558.htm'],
  ['地球科学学院', '副教授', '王翘楚', '4281274a1268470aa2eddec26cb554dc.htm'],
  ['地球科学学院', '副教授', '路漫', '80204f58a4dc4e6f93581e9f50ef6039.htm'],
  ['地球科学学院', '副教授', '郑晓薇', 'f1d54a32a62c4359bb9af7d04f5aebbb.htm'],
  ['地球科学学院', '讲师', '孙思敏', '50794.htm'],
  ['地球科学学院', '讲师', '蔡毅', '50792.htm'],
  ['地球科学学院', '讲师', '杨革联', '50791.htm'],
  ['地球科学学院', '讲师', '唐文连', '50790.htm'],
  ['地球科学学院', '讲师', '魏立春', '50789.htm'],
  ['地球科学学院', '讲师', '李海燕', '50784.htm'],
  ['地球科学学院', '讲师', '孙明亮', '50776.htm'],
  ['地球科学学院', '讲师', '杨程宇', '04346e5123ed4204bd13527a15279c53.htm'],
  ['地球科学学院', '讲师', '张瑞', '47b93c6df89d49e9975b72b5ee6a7d04.htm'],
  ['地球科学学院', '讲师', '庞小娇', 'f72f470f0ed944d3b0be01e534088868.htm'],
  ['地球科学学院', '讲师', '尤兵', '8772853386c64813819d4f705401cc52.htm'],
  ['地球科学学院', '讲师', '焦小芹', '1825bdb4e99a4e518c651a1d2eeba996.htm']
]

const profileBase: Record<MentorSchool, Record<string, string>> = {
  地球物理学院: {
    教授: 'https://www.cup.edu.cn/geophysics/szdw/js/',
    副教授: 'https://www.cup.edu.cn/geophysics/szdw/fjs/',
    讲师: 'https://www.cup.edu.cn/geophysics/szdw/jshi/'
  },
  地球科学学院: {
    教授: 'https://www.cup.edu.cn/geosci/szdw/jiaoshou/',
    副教授: 'https://www.cup.edu.cn/geosci/szdw/fujiaoshou/',
    讲师: 'https://www.cup.edu.cn/geosci/szdw/jiangshi/'
  }
}

const verifiedByTeacher = new Map(verifiedMentors.map((mentor) => [`${mentor.school}:${mentor.name}`, mentor]))

export const mentors: Mentor[] = officialTeacherDirectory.map(([school, title, name, page]) => {
  const verified = verifiedByTeacher.get(`${school}:${name}`)
  if (verified) return { ...verified, title }
  return {
    id: `${school}:${name}`,
    name,
    school,
    title,
    directions: [],
    summary: '中国石油大学（北京）学院官网师资队伍名录已列示该教师。',
    sourceUrl: `${profileBase[school][title]}${page}`
  }
})

type PortalTeacher = {
  id: string
  fullName: string
  facultyPid: string | null
  facultyName: string | null
  jobTitle: string | null
  path: string
  teacherType: string | null
  subjectName: string | null
}

type PortalTeacherResponse = {
  list: PortalTeacher[]
  pages: number
}

const portalApi = 'https://faculty.cup.edu.cn/TPHP/website/teacherMaster'

// These are the top-level teaching units returned by the official platform's unit hierarchy.
// Records from research institutes that are not attached to a current top-level college retain
// their official unit name instead of being assigned to a college by inference.
export const officialTopLevelUnits: Record<string, string> = {
  '200': '地球科学学院',
  '201': '石油工程学院',
  '202': '化学工程与环境学院',
  '203': '机械与储运工程学院',
  '204': '地球物理学院',
  '205': '理学院',
  '206': '经济管理学院',
  '207': '马克思主义学院',
  '208': '外国语学院',
  '209': '体育与人文艺术学院',
  '214': '新能源与材料学院',
  '216': '安全与海洋工程学院',
  '233': '人工智能学院',
  '234': '人工智能学院',
  '235': '非常规油气科学技术研究院',
  '240': '碳中和未来技术学院',
  '241': '碳中和示范性能源学院'
}

function splitOfficialValue(value: string | null): string[] {
  return (value ?? '').split('，').map((item) => item.trim()).filter(Boolean)
}

function toPortalMentor(teacher: PortalTeacher): Mentor {
  const school = officialTopLevelUnits[teacher.facultyPid ?? ''] ?? teacher.facultyName ?? '未标注单位'
  const verified = verifiedByTeacher.get(`${school}:${teacher.fullName}`)
  const mentorTypes = splitOfficialValue(teacher.teacherType)
  const subjects = splitOfficialValue(teacher.subjectName)
  if (verified) {
    return {
      ...verified,
      id: `portal:${teacher.id}`,
      title: teacher.jobTitle ?? verified.title,
      unit: teacher.facultyName ?? undefined,
      mentorTypes,
      subjects,
      sourceUrl: `https://faculty.cup.edu.cn/${teacher.path}/`
    }
  }
  return {
    id: `portal:${teacher.id}`,
    name: teacher.fullName,
    school,
    unit: teacher.facultyName ?? undefined,
    title: teacher.jobTitle ?? '职称未公开',
    directions: [],
    mentorTypes,
    subjects,
    summary: '中国石油大学（北京）官方教师平台已列示该教师的公开信息。',
    sourceUrl: `https://faculty.cup.edu.cn/${teacher.path}/`
  }
}

async function fetchPortalPage(currentPage: number): Promise<PortalTeacherResponse> {
  const body = new URLSearchParams({
    currentPage: String(currentPage),
    fullName: '',
    subjectName: '',
    facultyName: '',
    titleLevel: '',
    teacherType: '',
    nameInitials: ''
  })
  const response = await fetch(portalApi, {
    method: 'POST',
    headers: { 'Content-Type': 'application/x-www-form-urlencoded' },
    body
  })
  if (!response.ok) throw new Error(`Official faculty portal returned ${response.status}`)
  return response.json() as Promise<PortalTeacherResponse>
}

// The platform's unfiltered result is the authoritative all-public-teacher directory. Pages are
// fetched with bounded concurrency so the browser does not flood the university's public service.
export async function loadOfficialTeacherDirectory(): Promise<Mentor[]> {
  const firstPage = await fetchPortalPage(1)
  const pages: PortalTeacherResponse[] = [firstPage]
  let nextPage = 2
  await Promise.all(Array.from({ length: Math.min(6, Math.max(0, firstPage.pages - 1)) }, async () => {
    while (nextPage <= firstPage.pages) {
      const page = nextPage++
      pages[page - 1] = await fetchPortalPage(page)
    }
  }))
  return pages.flatMap((page) => page.list).map(toPortalMentor)
}
