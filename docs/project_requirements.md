# Product Requirements Document (PRD)

## Introduction

This Product Requirements Document (PRD) outlines the requirements for a federated learning system built on the Internet Computer Blockchain (ICP) to predict cardiovascular disease (CVD) using medical record data. The system enables healthcare providers to collaboratively train a Random Forest model without sharing sensitive patient data, leveraging the Flower framework for federated learning and the ICP blockchain for decentralized, secure, and transparent operations.

## Objectives

- Develop a federated learning system that allows multiple healthcare providers to collaboratively train a shared CVD prediction model.
- Integrate the ICP blockchain to manage decentralized model training and ensure secure operations.
- Implement a Random Forest model using scikit-learn for accurate CVD prediction.
- Utilize the Flower framework to orchestrate federated learning across distributed clients.
- Ensure the system is scalable, secure, and compliant with data privacy standards.

## Stakeholders

- **Healthcare Providers**: Primary users who train local models and contribute to the global model.
- **Patients**: Indirect stakeholders whose anonymized, privacy-preserved data is used for training.
- **Developers**: Responsible for building and maintaining the system.
- **Researchers**: May utilize the model for further analysis or improvements.
- **Regulatory Bodies**: Ensure compliance with data protection regulations (e.g., HIPAA, GDPR).

## Functional Requirements

- **Client Registration**: Healthcare providers can register with the system to participate in federated learning.
- **Local Model Training**: Providers can train a local Random Forest model on their private dataset.
- **Model Update Submission**: Providers can submit model updates (e.g., parameters) to the federated learning server.
- **Model Aggregation**: The server aggregates updates from all providers to update the global model using federated averaging adapted for Random Forests.
- **Global Model Access**: Providers can access the global model to make predictions.
- **Data Preprocessing**: Standardized preprocessing guidelines or scripts ensure consistency across providers.
- **Performance Evaluation**: Mechanisms to evaluate the global model’s performance are included.
- **User Interface**: A web-based dashboard allows providers to register, manage participation, submit updates, and access the global model.
- **Training Configuration**: Administrators can configure federated learning parameters (e.g., number of training rounds, aggregation method, convergence criteria).

## Non-Functional Requirements

- **Performance**: The system efficiently handles up to 100 healthcare providers and large datasets.
- **Security**: Ensures data privacy by keeping patient data local, sharing only model updates.
- **Scalability**: Scales to accommodate additional providers without significant performance loss.
- **Usability**: Provides an intuitive interface for healthcare providers.
- **Reliability**: Maintains high availability, critical for healthcare applications.
- **Compliance**: Adheres to relevant data protection and privacy regulations (e.g., HIPAA, GDPR).

## System Architecture

The system comprises three main components:

1. **Federated Learning Clients**:
   - Operated by healthcare providers.
   - Train local Random Forest models using scikit-learn.
   - Communicate with the server via the Flower framework.
2. **Federated Learning Server**:
   - A canister smart contract on the ICP blockchain.
   - Coordinates training rounds, aggregates model updates, and maintains the global model.
3. **ICP Blockchain**:
   - Provides decentralized infrastructure with secure, transparent operations via canister isolation and cryptography.

### Data Flow
- Clients train local models and send updates to the server.
- The server aggregates updates and refreshes the global model.
- The updated global model is redistributed to clients for the next round.

### Tech Stack
- **Machine Learning**: scikit-learn (Random Forest)
- **Federated Learning**: Flower
- **Blockchain**: ICP (canisters in Rust or Motoko)
- **Languages**: Python (ML and federated learning), Rust/Motoko (canisters)

## Data Requirements

### Dataset Features
- Age (int, days)
- Height (int, cm)
- Weight (float, kg)
- Gender (categorical)
- Systolic Blood Pressure (int)
- Diastolic Blood Pressure (int)
- Cholesterol Level (1: Normal, 2: Above Normal, 3: Well Above Normal)
- Glucose Level (1: Normal, 2: Above Normal, 3: Well Above Normal)
- Smoking Status (binary)
- Alcohol Intake (binary)
- Physical Activity (binary)
- Cardiovascular Disease (target, binary)

### Data Preprocessing
- Convert age from days to years.
- Normalize height and weight.
- One-hot encode gender.
- Ordinal encode cholesterol and glucose levels.
- Ensure binary features are encoded as 0 or 1.

### Data Privacy
- All data remains local; only model updates are shared.

## User Stories

- As a healthcare provider, I want to register with the system to contribute to the global CVD prediction model.
- As a healthcare provider, I want to train a local model on my patient data and submit updates to improve the global model without sharing raw data.
- As a healthcare provider, I want to use the global model to predict CVD risk for my patients.
- As a system administrator, I want to monitor the federated learning process to ensure proper participation.

## Constraints and Assumptions

### Constraints
- Must comply with data privacy laws (e.g., HIPAA, GDPR).
- Limited by ICP blockchain capabilities (e.g., canister storage, computational resources).
- Random Forest must be compatible with federated learning aggregation methods.

### Assumptions
- Providers have infrastructure to run client software.
- Providers are willing to participate in federated learning.
- ICP blockchain operates reliably.
- Dataset features are consistent across providers.

## Dependencies

- Flower AI framework for federated learning.
- scikit-learn for Random Forest implementation.
- ICP blockchain for decentralized operations.
- Third-party libraries for data preprocessing and secure communication.

## Acceptance Criteria

- Successfully trains a global Random Forest model via federated learning.
- Achieves at least 80% accuracy on a validation dataset.
- Ensures no raw patient data is exchanged.
- Handles up to 100 providers without significant performance issues.
- Passes security audits and complies with relevant regulations.

