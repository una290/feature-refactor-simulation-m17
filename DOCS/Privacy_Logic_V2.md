# DAE_P1 隱私治理邏輯流程圖 (V2.1 - 邏輯匯流版)

此版本特別強化了 **「降級路徑匯入 PC-Min」** 的視覺表現。

```mermaid
graph TD
    %% 定義風格 (字體放大 3 倍)
    classDef start fill:#f9f,stroke:#333,stroke-width:2px,font-size:42px;
    classDef process fill:#fff,stroke:#333,stroke-width:1px,font-size:42px;
    classDef decision fill:#fff9c4,stroke:#fbc02d,stroke-width:2px,font-size:42px;
    classDef pass fill:#c8e6c9,stroke:#2e7d32,stroke-width:2px,font-size:42px;
    classDef fail fill:#ffcdd2,stroke:#c62828,stroke-width:2px,font-size:42px;
    classDef warning fill:#ffe0b2,stroke:#ef6c00,stroke-width:2px,font-size:42px;
    classDef filter fill:#e1f5fe,stroke:#01579b,stroke-width:3px,font-size:42px,stroke-dasharray: 5 5;

    Start((開始請求)) --> H1{Hook 1: <br/>基礎有效性檢查?}
    
    H1 -- 缺失證據 --> H1_Fail[Verdict: NOT_READY<br/>理由: 隱私政策缺失]
    class H1_Fail fail;
    
    H1 -- 驗證通過 --> Timeline[生成 Timeline & 工程數據]
    
    Timeline --> H2{Hook 2: <br/>出口閘門 (Scope)?}
    
    H2 -- 授權不符 --> FilterGate
    H2 -- 授權匹配 --> H3{Hook 3: <br/>BYUSE 合規驗證?}
    
    %% Hook 3 路徑
    H3 -- "常規場景<br/>(DELIVERY_GRADE)" --> FilterGate
    H3 -- "爭議場景 (Dispute)" --> H3_Check{是否有數位簽章?}
    
    H3_Check -- "否 (NOT_CLOSURE)" --> FilterGate
    H3_Check -- "是 (CLOSURE_GRADE)" --> Final_Priv[輸出: PC-Priv<br/>(完整交付 / 證據閉環)]

    %% 核心過濾閘門 (Logical Convergence)
    FilterGate{{"M12 數據剝離過濾器<br/>(Data Stripping Filter)"}}
    class FilterGate filter;

    FilterGate --> Final_Min[輸出: PC-Min<br/>(敏感數據強制剝離)]

    %% 路徑標註
    subgraph "隱私保護路徑 (Privacy Protection)"
        FilterGate
        Final_Min
    end

    class Start start;
    class H1, H2, H3, H3_Check decision;
    class Final_Priv pass;
    class Final_Min warning;
    class Timeline process;
```

## 邏輯修正說明：
1. **明確匯合 (FilterGate)**：
   - **Hook 2 失敗** (授權不符) -> 進入過濾器。
   - **Hook 3 常規路徑** (`DELIVERY_GRADE`) -> 進入過濾器。
   - **Hook 3 爭議失敗** (`NOT_CLOSURE_GRADE`) -> 進入過濾器。
2. **唯一通行證**：只有「爭議模式」且「通過簽章驗證」的路徑能避開過濾器，獲得 `PC-Priv`。
3. **字體與樣式**：維持 3 倍字體大小，並為過濾器增加了藍色虛線框以示強調。
