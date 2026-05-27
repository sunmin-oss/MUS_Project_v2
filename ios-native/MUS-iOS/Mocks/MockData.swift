import Foundation

/// Mock 資料源（W1 / Demo 模式使用）
enum MockData {
    static let profiles: [Profile] = [
        Profile(id: "p1", name: "我本人", isPrimary: true, avatarSystemName: "person.crop.circle.fill"),
        Profile(id: "p2", name: "媽媽", isPrimary: false, avatarSystemName: "figure.dress"),
        Profile(id: "p3", name: "爸爸", isPrimary: false, avatarSystemName: "figure.arms.open")
    ]

    static let drugs: [Drug] = [
        Drug(id: 101, chineseName: "普拿疼", englishName: "Paracetamol",
             licenseNumber: "衛部藥製字第000123號", shape: "圓形", color: "白色", usage: "退燒、止痛"),
        Drug(id: 102, chineseName: "胃乳片", englishName: "Aluminum Hydroxide",
             licenseNumber: "衛部藥製字第000456號", shape: "圓形", color: "粉紅", usage: "緩解胃酸過多"),
        Drug(id: 103, chineseName: "阿斯匹靈", englishName: "Aspirin",
             licenseNumber: "衛部藥輸字第000789號", shape: "圓形", color: "白色", usage: "解熱鎮痛、抗血小板")
    ]

    static let medications: [Medication] = [
        Medication(id: "m1", profileId: "p1", drugName: "普拿疼 500mg",
                   dosage: "1 顆", frequency: "每 6 小時", mealTiming: "飯後",
                   nextDoseAt: Date().addingTimeInterval(3600), currentStock: 12),
        Medication(id: "m2", profileId: "p1", drugName: "胃乳片",
                   dosage: "2 顆", frequency: "三餐飯後", mealTiming: "飯後",
                   nextDoseAt: Date().addingTimeInterval(7200), currentStock: 3),
        Medication(id: "m3", profileId: "p2", drugName: "降血壓藥",
                   dosage: "1 顆", frequency: "每日一次", mealTiming: "早餐後",
                   nextDoseAt: Date().addingTimeInterval(28800), currentStock: 25)
    ]

    static let consultations: [ConsultationSummary] = [
        ConsultationSummary(id: "c1", title: "服用普拿疼疑問",
                            lastMessagePreview: "感冒可以同時吃兩種止痛藥嗎？",
                            updatedAt: Date().addingTimeInterval(-3600), isAI: true),
        ConsultationSummary(id: "c2", title: "胃乳片與其他藥物",
                            lastMessagePreview: "需要間隔多久服用？",
                            updatedAt: Date().addingTimeInterval(-86400), isAI: true)
    ]

    static let pharmacies: [Pharmacy] = [
        Pharmacy(id: "ph1", name: "康是美 (站前店)", address: "台北市中正區忠孝西路1段",
                 latitude: 25.0478, longitude: 121.5170, isNHIContracted: true, is24h: false),
        Pharmacy(id: "ph2", name: "屈臣氏 (西門店)", address: "台北市萬華區成都路",
                 latitude: 25.0421, longitude: 121.5067, isNHIContracted: true, is24h: false),
        Pharmacy(id: "ph3", name: "丁丁藥局 (24h)", address: "台北市大安區忠孝東路4段",
                 latitude: 25.0418, longitude: 121.5495, isNHIContracted: true, is24h: true)
    ]

    static let safetyAlerts: [SafetyAlert] = [
        SafetyAlert(id: "s1", level: .major,
                    title: "交互作用警告",
                    message: "阿斯匹靈與抗凝血劑同時服用可能增加出血風險",
                    recommendation: "建議諮詢藥師或醫師調整劑量")
    ]
}
