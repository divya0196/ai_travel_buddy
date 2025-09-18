# AI Weekend Travel Buddy 🤖✈️

A sophisticated multi-agent system that generates personalized 2-day travel itineraries using collaborative AI agents. The system employs a nested multi-agent architecture where specialized agents work together to create optimized, budget-friendly travel plans.

## 🌟 Features

- **Multi-Agent Architecture**: Coordinated system with Explorer, Budget, and Food agents
- **Personalized Itineraries**: Custom 2-day plans based on interests and preferences
- **Budget Optimization**: Intelligent budget allocation across accommodation, food, activities, and transport
- **Route Optimization**: Efficient routing using traveling salesman algorithms
- **Dietary Accommodation**: Support for various dietary restrictions and preferences
- **Real-time Cost Validation**: Cross-agent budget validation and adjustment
- **Local Recommendations**: Authentic local food specialties and cultural tips
- **RESTful API**: Easy-to-use HTTP endpoints for integration

## 🏗️ Architecture

### Master Coordinator Agent
- Orchestrates the entire trip planning workflow
- Manages inter-agent communication
- Synthesizes final itinerary from all agent inputs

### Specialized Agents
- **Explorer Agent**: Finds attractions, optimizes routes, manages scheduling
- **Budget Agent**: Handles budget allocation, cost estimation, and financial optimization
- **Food Agent**: Recommends restaurants, handles dietary restrictions, provides local food tips

## 🚀 Quick Start

### Prerequisites
- Python 3.8+
- pip package manager


