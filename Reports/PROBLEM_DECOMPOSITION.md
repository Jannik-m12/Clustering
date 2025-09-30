
# Problem Decomposition Report

## 1. Ultimate Impact Goal
To enable **GlobalCorp to reduce ESG risks and enhance sustainable value creation** by clustering companies based on financial performance, industry, region, and ESG scores to uncover actionable sustainability patterns.

---

## 2. Sub-Problems (5W Framework)

1. **Who:** Which companies (by industry, size, or region) show ESG performance gaps that stakeholders should prioritize?  
2. **What:** What relationships exist between financial health (Revenue, ProfitMargin, MarketCap, GrowthRate) and ESG_Overall scores?  
3. **When:** When (over the reporting years 2015–2025) do ESG improvements or declines most affect financial outcomes?  
4. **Where:** Where (Region) are ESG strengths or risks concentrated?  
5. **Why:** Why does clustering this dataset provide unique value? (Reveals hidden ESG/financial trade-offs, highlights sector/region-specific opportunities, and informs investment/strategic decisions).  

---

## 3. Feasibility/Impact Matrix

| Potential Clustering Objective                         | Feasibility (Low–High) | Impact (Low–High) |
|-------------------------------------------------------|------------------------|-------------------|
| Clustering companies by **ESG_Overall score**         | High                   | High              |
| Clustering industries by **ProfitMargin & ESG score** | High                   | High              |
| Clustering regions by **average ESG performance**     | Medium                 | High              |
| Clustering companies by **GrowthRate vs ESG score**   | Medium                 | Medium            |
| Clustering by **MarketCap & ESG performance**         | Medium                 | High              |

---

## 4. Selected Clustering Problems
1. **Clustering companies by ESG_Overall scores** (High feasibility, high impact).  
2. **Clustering industries by ProfitMargin & ESG performance** (High feasibility, high impact).  
3. **Clustering regions by ESG_Overall averages** (Medium feasibility, high impact).  

---

## 5. SMART Objectives for Priority Problems

### Objective 1: ESG Performance Clustering
- **Specific:** Cluster companies based on their **ESG_Overall** score to identify leaders, laggards, and mid-performers.  
- **Measurable:** Produce 3–5 ESG clusters capturing at least 90% of dataset variability.  
- **Achievable:** Use ESG_Overall column directly from dataset.  
- **Relevant:** Highlights systemic ESG performance patterns for stakeholders.  
- **Time-bound:** Complete clustering within **4 weeks**.  

### Objective 2: Industry Profitability vs ESG
- **Specific:** Cluster industries by **ProfitMargin** and **ESG_Overall** scores to explore trade-offs.  
- **Measurable:** Identify at least 3 clusters showing distinct ESG/profitability profiles.  
- **Achievable:** Use Industry, ProfitMargin, and ESG_Overall fields.  
- **Relevant:** Supports sustainability strategies that balance profitability and ESG performance.  
- **Time-bound:** Deliver results within **6 weeks**.  

### Objective 3: Regional ESG Patterns
- **Specific:** Cluster regions based on **average ESG_Overall** scores across companies.  
- **Measurable:** Identify 3 regional ESG profiles (leaders, average, underperformers).  
- **Achievable:** Use Region and ESG_Overall fields.  
- **Relevant:** Informs regulators and investors about regional ESG risks and strengths.  
- **Time-bound:** Deliver analysis within **8 weeks**.  

---

## 6. Capstone Connection
This decomposition directly leverages dataset columns (**Industry, Region, ProfitMargin, GrowthRate, MarketCap, ESG_Overall**) to design clustering tasks that:  
- Reveal **patterns of ESG performance across industries and regions**.  
- Identify **trade-offs between profitability and sustainability**.  
- Provide **stakeholder-ready insights** aligned with GlobalCorp’s sustainability strategy.  

The clustering objectives serve as the backbone of the capstone, ensuring that results are both **methodologically sound** and **practically actionable**.
