# Teklo Study - Mechanologist Evo Card Design Project

## Project Overview

This repository contains the development and design documentation for **Teklovossen**, a Mechanologist hero for the Flesh and Blood trading card game's Modular Ascension set. The project focuses on creating thematic Evo equipment, AI items, and supporting cards that showcase Teklo Energy manipulation, nanotechnology, and artificial intelligence integration.

> **NOTES**
**This is a fan-made project and is not affiliated with Legend Story Studios or the official Flesh and Blood game.**

<div align="center">


<img src="evos\Nano Evos\evo_study. 2025, 22_22_28.png" alt="Custom Fabrication" width="400"/>

*Teklo Custom Fabrication - A key resource for Mechanologist strategies*

</div>

## Why ?
As a fresh new player of **Flesh and Blood**, I was looking for a hero that can fit my playstyle. And as a lover of technology and futurism, Teklovossen was a perfect match.
Maybe because I am a programmer, or because I love Sci-Fi movies, but I was really attracted by the idea of playing a hero that can manipulate technology and use it to his advantage.

But after playing a few games with him, I realize that his card pool was really limited, and that he was not really *competitive*.

A friend of mine, known as "If I have a Blue I Win" told me one day:
**"Why not create additional cards for Teklovossen? and see if can be more competitive?"**

I was thinking about it for a while, and finally I decided to do it.

So Thank You **Laurent** !



##  Project Goals

- Design balanced and thematic Evo equipment sets for multiple tech paths
- Create comprehensive card evaluation and balance testing systems
- Develop lore-consistent mechanics that fit the Flesh and Blood game system
- Generate visual concepts and art direction for card designs (Using AI tools)
- Create an expansion of Teklovossen's playstyle options

## 📁 File Structure

```
tekloStudy/
├── .gitignore                    # Git ignore rules
├── README.md                     # This file
├── teklostudy.md                # Main card design documentation
├── teklostudyv1.ipynb           # Interactive development notebook
└── evos/                        # Visual concept art
    ├── evo_*.png               # Generated card art concepts
    ├── Biomancy evo/           # Biomancy theme artwork
    └── Quantuum Evo/           # Quantum theme artwork
```

##  Hero Themes

### **AI Integration Path**
- **Focus**: Artificial intelligence synergies and tactical combat protocols
- **Key Cards**: `IA — Singularity Cannon`, `AI — Predator Logic`
- **Mechanics**: AI item synergies, attack enhancement, resource conversion

### **Nano Technology Path** 
- **Focus**: Microscopic self-replication and adaptive armor systems
- **Key Cards**: `Evo — Nanite Core Reactor`, `Nanite Devastator`
- **Mechanics**: Nanite counters, equipment transformation, adaptive defense
- **Signature Action**: `Singularity Protocol: Nano Genesis`

### **Biomancy Evolution Path**
- **Focus**: Bio-mechanical symbiosis and organic technology integration  
- **Key Cards**: `Evo Bio-Oaken Soul` series, `Symbiotic Strike`
- **Mechanics**: Symbiote token generation, biological enhancement, adaptive scaling

### **Quantum Manipulation Path**
- **Focus**: Probabilistic control and multidimensional precision
- **Key Cards**: `Evo Quantum Processor`, `Quantum Nexus`  
- **Mechanics**: Quantum charge manipulation, probability effects, reality bending



<div align="center">

<img src="evos/Quantuum Evo/evo_study. 2025, 23_23_19.png" alt="Quantum Nexus" width="400"/> <img src="evos/Quantuum Evo/evo_study. 2025, 23_09_33.png" alt="Quantum processor" width="400"/>

*Quantum Evo to put on base Evo Steel Soul Evos*

</div>

##  Development Tools

### **Card Balance Evaluator**
The project includes a comprehensive Python-based card evaluation system in `teklostudyv1.ipynb`:

```python
evaluator = CardEvaluator()
evaluator.add_card(
    name="Card Name",
    card_type="Equipment/Item/Action", 
    cost="X Teklo Energy",
    power_level=7,    # 1-10 scale
    complexity=5,     # 1-10 scale  
    fun_factor=8,     # 1-10 scale
    balance=6,        # 1-10 scale
    theme_fit=9       # 1-10 scale
)
```

### **Balance Guidelines**
- **Equipment Cost**: 2-5 Teklo Energy for Evo pieces
- **Item Activation**: 1-3 Teklo Energy per use
- **Target Balance Score**: 7+/10 for competitive viability
- **Power Level Range**: 6-8 for consistent meta positioning

##  Visual Development

The `evos` directory contains generated artwork concepts:

- **Core Evo Sets**: Visual representations of equipment transformations
- **Biomancy Theme**: Organic-tech fusion aesthetic with teal/bronze frames
- **Quantum Theme**: Prismatic energy with reality-bending visual effects
- **Corporate Theme**: Industrial precision with Teklo branding elements

##  Current Card Status

### **Balanced Cards** 
- `Evo — NeuroWeave Visor` - Card draw utility (Balance: 8/10)
- `Self-Assembly Protocol` - Nano fabricate variant (Balance: 7/10)

### **Cards Needing Balance** ⚠️
- `AI — Singularity Cannon` - Uncapped scaling (Balance: 4/10)
- `AI — Predator Logic` - Free reaction too powerful (Balance: 5/10)  
- `Evo — Nanite Core Reactor` - Missing cost definition (Balance: 5/10)

##  Getting Started

### **Prerequisites**
- Python 3.8+ for running the evaluation notebook
- Jupyter Notebook or Jupyter Lab
- Required packages: `pandas`, `numpy`, `matplotlib`

### **Setup**
```bash
git clone <repository-url>
cd tekloStudy
pip install pandas numpy matplotlib jupyter
jupyter notebook teklostudyv1.ipynb
```

### **Usage**
1. **Read the Documentation**: Start with `teklostudy.md` for complete card designs
2. **Run Balance Analysis**: Use `teklostudyv1.ipynb` to evaluate card balance
3. **Test New Designs**: Add your cards to the evaluator for balance scoring
4. **Generate Visuals**: Check `evos` for artwork inspiration

## Gameplay Integration
<div align="center">

### **Resource Tokens of the Modular Ascension Fan made expansion**
<img src="evos/evo_study.%202025,%2022_24_33.png" alt="Teklo Memory" width="400"/> <img src="evos/evo_study.%202025,%2022_24_31.png" alt="Teklo Energy" width="400"/>

*Teklo Memory & Teklo Energy - Core resources for Mechanologist gameplay*

</div>


### **Teklo Energy System**
- Primary resource for Mechanologist actions
- Generation: 1-2 per turn typical
- Storage: Limited to encourage active play
- Spending: Most abilities cost 1-2 energy

### **Evo Transformation Mechanics**
- **Base → Evo**: Meaningful upgrade with 3-5 Teklo Energy cost
- **Multi-Evo Synergies**: Exponential power scaling
- **Battleworn Durability**: Sustainable through multiple combats

##  Balance Methodology

### **Problem Identification**
- **Too Cheap**: Effect too powerful for cost
- **Unlimited Scaling**: No caps or restrictions  
- **No Counterplay**: Opponent cannot respond effectively
- **Power Creep**: Strictly better than existing options

### **Fix Implementation**
- **Cost Adjustment**: Increase Teklo Energy requirements
- **Add Limitations**: "Once per turn" or scaling caps
- **Timing Restrictions**: Reaction costs or conditional triggers
- **Resource Pressure**: Decay mechanics or maintenance costs

##  Development Workflow

1. **Design Phase**: Create thematic mechanics in `teklostudy.md`
2. **Analysis Phase**: Score cards using the balance evaluator
3. **Iteration Phase**: Adjust costs and limitations based on scores
4. **Testing Phase**: Theoretical gameplay analysis
5. **Visual Phase**: Generate concept art for approved designs

##  Contributing

You are welcome to contribute ideas, card designs, or balance suggestions. Please follow the development workflow and ensure all new cards are documented and evaluated.

When adding new cards or themes:

1. **Document in Markdown**: Add complete card text to `teklostudy.md`
2. **Evaluate Balance**: Score using the Python evaluator
3. **Target Metrics**: Aim for Balance 7+, Power Level 6-8
4. **Theme Consistency**: Ensure 9+ theme fit score
5. **Update Documentation**: Include mechanical rationale

##  Future Development

### **Planned Features**
- Interactive card database with search functionality
- Automated balance recommendations ( But live testing are still needed )
- Meta-game impact simulation
- Comprehensive playtest framework


### **Additional Themes**
- **Corporate Succession**: Executive equipment line
- **Underground Resistance**: Stealth and disruption mechanics  
- **Military Defense**: Protection and tactical systems
- **Research Division**: Experimental and discovery effects

---

**Project Status**: Active Development  
**Last Updated**: January 2025  
**License**: Personal Project - Educational Use

For questions about specific cards or balance concerns, reference the detailed analysis in `teklostudyv1.ipynb` or the complete card documentation in `teklostudy.md`.
Feel free to open issues or pull requests for contributions!
Contact: support@fabtcgcompanion.com