# Mementos Melee 🎭👊

![Project Status](https://img.shields.io/badge/Status-Alpha-orange) ![Language](https://img.shields.io/badge/Language-Python_3.10-blue) ![Engine](https://img.shields.io/badge/Engine-PyGame-green)

> **A Python-based 2D Fighting Game Engine featuring "Cognitive Crisis" — a unique trivia-based comeback mechanic.**

## 📖 About The Project
**Mementos Melee** is a fighting game built entirely from scratch using Python and PyGame. Unlike standard fighters, it integrates a twist: the **Cognitive Crisis** system.

When a player reaches critical health (<20%), the combat engine pauses the physics simulation and triggers a high-stakes trivia event. Answering correctly heals the player (Risk/Reward), blending reflex-based gameplay with knowledge retrieval.

# [Gameplay Screenshots]
<img width="993" height="497" alt="image" src="https://github.com/user-attachments/assets/567a0200-ef07-4c8c-96ca-fa8e6d234277" />

<img width="982" height="494" alt="image" src="https://github.com/user-attachments/assets/c7268f0b-cd97-4733-965a-6b328ce2d28f" />


*(Current Alpha build showing the mechanics-first "graybox" phase with hitbox visualization and UI)*

## ✨ Key Features
* **Custom State Machine:** Robust architecture handling distinct game states (`MENU`, `FIGHT`, `PAUSE`, `TRIVIA`) without blocking the game loop.
* **"Cognitive Crisis" Mechanic:** A JSON-driven QTE system that interrupts combat for a trivia challenge.
* **Finite State Machine (FSM) AI:** A CPU opponent that uses a proximity-based decision tree to chase, attack, or retreat.
* **Scalable Architecture:** Entity-Component design allowing for easy addition of new fighters or mechanics.

## 🛠️ Technical Highlights
| Category | Implementation |
| :--- | :--- |
| **Language** | Python 3.10+ |
| **Library** | PyGame (Rendering & Input) |
| **Data** | JSON (Trivia Questions) |
| **Patterns** | State Pattern, Game Loop, OOP |

## 🚀 Roadmap
The current version serves as the **Mechanics Alpha**.
* [x] **Core Mechanics:** Physics, Hitboxes, Health Systems.
* [x] **AI Opponent:** Basic "Chase & Attack" FSM.
* [ ] **Aesthetic Overhaul:** Transitioning to *Persona 5* stylized minimalism.
* [ ] **More Features:** Adding a character select screen and the option to choose from several categories of trivia questions.

## 💻 How to Run
```bash
# Clone the repository
git clone [https://github.com/NebMen/mementos-melee.git](https://github.com/NebMen/mementos-melee.git)

# Install dependencies
pip install pygame

# Run the game
python main.py
