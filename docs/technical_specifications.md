Below are the technical and functional specifications for building a federated learning system using scikit-learn's Random Forest, Flower AI, and ICP smart contracts to predict cardiovascular disease (CVD), based on the project requirements.

# Technical and Functional Specifications for Federated Learning System

This document outlines the technical and functional specifications for a federated learning system that uses the Internet Computer Blockchain (ICP) to train a Random Forest model for predicting cardiovascular disease (CVD). The system leverages scikit-learn for the Random Forest model, Flower AI for federated learning, and ICP smart contracts for decentralized coordination.

---

## 1. Scikit-learn Random Forest Specifications

### Functional Specifications

- **Model Type**: `RandomForestClassifier` from scikit-learn.
- **Purpose**: Predict the presence of cardiovascular disease (CVD) using patient medical data.
- **Input Dataset Format in CSV For Training**:
  | Feature | Category | Column Name | Data Type |
  | ------ | ------ | ------ | ------ |
  | Age | Objective Feature | age | int (days) |
  | Height | Objective Feature | height | int (cm) |
  | Weight | Objective Feature | weight | float (kg) |
  | Gender | Objective Feature | gender | categorical code |
  | Systolic blood pressure | Examination Feature | ap_hi | int |
  | Diastolic blood pressure | Examination Feature | ap_lo | int |
  | Cholesterol | Examination Feature | cholesterol | 1: normal, 2: above normal, 3: well above normal |
  | Glucose | Examination Feature | gluc | 1: normal, 2: above normal, 3: well above normal |
  | Smoking | Subjective Feature | smoke | binary |
  | Alcohol intake | Subjective Feature | alco | binary |
  | Physical activity | Subjective Feature | active | binary |
  | Presence or absence of cardiovascular disease | Target Variable | cardio | binary |

### Technical Specifications

- **Data Preprocessing**:
  - Age: Convert from days to years (`age_years = age_days // 365`).
  - Numerical Features (height, weight, ap_hi, ap_lo): Standardize using `StandardScaler`.
  - Categorical Features:
    - Gender: One-hot encoding using `pandas.get_dummies` or `sklearn.preprocessing.OneHotEncoder`.
    - Cholesterol and Glucose: Ordinal encoding using `sklearn.preprocessing.OrdinalEncoder`.
  - Binary Features: Ensure 0/1 encoding.
- **Hyperparameters**:
  - `n_estimators`: 100 (number of trees).
  - `max_depth`: 10 (maximum depth of each tree).
  - `min_samples_leaf`: 5 (minimum samples per leaf node).
  - `random_state`: 42 (for reproducibility).
- **Local Training**:
  - Each healthcare provider trains a local `RandomForestClassifier` on their dataset.
  - Model updates are the serialized decision trees (e.g., using `joblib` or `pickle`).
- **Technology Stacks**
  - Python 3.10, use "uv" package and project manager.
  - scilearn kit, random forest
  - Local worker node & federated learning client codes under "./client" folder
  - Federated learning server codes under "./server" folder
  - ICP smart contract codes under "./icp" folder
  - Input data set in CSV format under "./dataset" folder
  - Output model files under "./models" folder
  - All samples Scilearn Kit Random Forest Training code under "./samples" folder

---

## 2. Flower AI (Federated Learning) Specifications

### Functional Specifications

- **Framework**: Flower (FLower AI) for federated learning orchestration.
- **Architecture**:
  - **Clients**: Healthcare providers train local models and send updates.
  - **Server**: Coordinates training rounds and aggregates updates.
- **Aggregation**: Combine decision trees from all clients into a global Random Forest.
- **Communication**: Secure client-server communication.

### Technical Specifications

- **Client Implementation**:
  - Use Flower’s `Client` API to define local training logic.
  - Serialize local Random Forest models (e.g., `joblib.dump(model)`).
  - Each client will have an ICP principal ID and authenticate it with server and load the principal id setting in .env
  - When client run, need to have a parameter to load the dataset file, then wait for server to issue command to start the training round.
  - While training round start, will show the console log message.


- **Server Implementation**:
  - Deployed as an ICP canister (see ICP section).
  - Use Flower’s `Server` API to manage training rounds.
  - Register & remove client ICP principal ID into ICP canister
  - List the client ICP principal ID from ICP canister
  - Only authencated client ICP principal ID allow to participate the training round
  - Terminal commands
    - List the connected clients
    - Register the client principal ID
    - Remove the client principal ID
    - List the registered client principal IDs
    - List the previous traning round history (training round ID, timestamp, model file name, participated clients)
    - Start the training round 
    - Quit the server application

- **Aggregation Method**:
  - Collect individual decision trees from each client.
  - Form a global Random Forest by combining all trees.
  - Optionally, weight trees by client dataset size.
- **Communication**:
  - Use gRPC over HTTPS for secure, efficient communication.
- **Security**:
  - Encrypt model updates during transmission.
  - Authenticate clients via ICP canister registration.

---

## 3. ICP Smart Contract Specifications

### Functional Specifications

- **Role**: Host the federated learning server, manage clients, aggregate updates, and store the global model.
- **Key Functions**:
  - **Client Registration**: Register healthcare providers.
  - **Model Update Submission**: Accept updates from clients.
  - **Aggregation**: Combine updates into a global model.
  - **Model Storage**: Maintain the global Random Forest for access.
- **User Interface**: Web-based dashboard for provider interaction.

### Technical Specifications

- **Canister Development**:
  - **Language**: Rust or Motoko or Javascript.
  - **Version**: Use dfx 0.22 and above
  - **Functions**:
    - `register_client`: Register a provider and assign a unique principal ID.
    - `delete_client`: Delete a provider with the principal ID.
    - `list_client`: List a provider.
    - `submit_update`: Receive and validate model updates.
    - `aggregate_updates`: Aggregate updates into the global model.
    - `get_global_model`: Provide access to the global model.
- **Storage**:
  - Store client metadata (e.g., IDs, participation records).
  - Store the serialized global Random Forest (optimize for canister limits).
- **Security**:
  - Leverage ICP’s canister isolation and cryptographic features.
  - Restrict update submissions to registered clients.
- **Scalability**:
  - Support up to 100 clients.
  - Use asynchronous processing or batching for efficiency.

---

## System Interaction

1. **Client Registration**: Providers register with the ICP canister.
2. **Local Training**: Clients train Random Forest models locally using scikit-learn.
3. **Update Submission**: Clients send serialized updates to the ICP-hosted Flower server.
4. **Aggregation**: The ICP canister combines updates (e.g., all trees into one forest).
5. **Global Model Update**: The canister updates and stores the global model.
6. **Model Distribution**: Optionally, distribute the global model to clients (optimized for size).

---

## Additional Requirements

- **Data Privacy**: Only model updates are shared, not raw data.
- **Performance Evaluation**: Use a validation dataset or federated evaluation to assess the global model.
- **User Interface**: Develop a web dashboard using ICP’s frontend tools.

This specification ensures a robust, secure, and decentralized federated learning system for CVD prediction.
