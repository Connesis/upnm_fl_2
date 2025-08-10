import Array "mo:base/Array";
import Hash "mo:base/Hash";
import HashMap "mo:base/HashMap";
import Iter "mo:base/Iter";
import Nat "mo:base/Nat";
import Option "mo:base/Option";
import Principal "mo:base/Principal";
import Text "mo:base/Text";
import Time "mo:base/Time";
import Blob "mo:base/Blob";
import Buffer "mo:base/Buffer";
import Result "mo:base/Result";
import Float "mo:base/Float";
import Int "mo:base/Int";

actor FL_CVD_Backend {

    // Types
    public type ClientStatus = {
        #Pending;     // Waiting for admin approval
        #Active;      // Approved and can participate
        #Inactive;    // Temporarily inactive
        #Rejected;    // Registration denied
        #Suspended;   // Temporarily blocked by admin
    };

    public type Role = {
        #Admin;       // Full system control
        #Server;      // Federated learning server operations
        #Client;      // Registered federated learning clients
        #Observer;    // Read-only access
    };

    public type Permission = {
        #ManageClients;   // Register/remove/approve clients
        #ManageRounds;    // Start/complete training rounds
        #ViewStats;       // Read system statistics
        #UpdateModels;    // Store model metadata
        #SystemAdmin;     // Full administrative access
    };

    public type Client = {
        id: Principal;
        registered_at: Time.Time;
        last_active: Time.Time;
        status: ClientStatus;
        total_rounds_participated: Nat;
        total_samples_contributed: Nat;
    };

    public type ClientParticipation = {
        principal_id: Principal;
        client_name: Text;
        dataset_filename: Text;
        samples_contributed: Nat;
        trees_contributed: Nat;
    };

    public type ModelMetadata = {
        round_id: Nat;
        timestamp: Time.Time;
        training_start_time: Time.Time;
        training_end_time: Time.Time;
        num_clients: Nat;
        total_examples: Nat;
        num_trees: Nat;
        accuracy: Float;
        model_hash: Text;
        model_filename: Text;
        participants: [ClientParticipation];
    };

    public type TrainingRound = {
        id: Nat;
        timestamp: Time.Time;
        model_file: Text;
        participants: [Principal];
        status: RoundStatus;
        metadata: ?ModelMetadata;
    };

    public type RoundStatus = {
        #Pending;
        #InProgress;
        #Completed;
        #Failed;
    };

    public type ClientRegistrationResult = {
        #Success: Client;
        #AlreadyRegistered;
        #PendingApproval: Client;
        #Error: Text;
    };

    // Custom hash function for Nat to avoid deprecation warning
    private func natHash(n: Nat): Hash.Hash {
        Text.hash(Nat.toText(n))
    };

    // Storage (marked as transient for development)
    private transient var clients = HashMap.HashMap<Principal, Client>(10, Principal.equal, Principal.hash);
    private transient var trainingRounds = HashMap.HashMap<Nat, TrainingRound>(10, Nat.equal, natHash);
    private transient var nextRoundId: Nat = 1;
    private transient var globalModel: Blob = Blob.fromArray([]);
    private transient var modelMetadata = HashMap.HashMap<Nat, ModelMetadata>(10, Nat.equal, natHash);

    // Role-based access control
    private stable var admin: Principal = Principal.fromText("2vxsx-fae"); // Will be set during init
    private transient var roles = HashMap.HashMap<Principal, Role>(10, Principal.equal, Principal.hash);
    private stable var serverPrincipal: ?Principal = null;

    // Permission checking functions
    private func hasRole(principal: Principal, role: Role) : Bool {
        switch (roles.get(principal)) {
            case (?userRole) {
                userRole == role or userRole == #Admin
            };
            case null {
                // Check if this is the admin principal
                principal == admin
            };
        }
    };

    private func hasPermission(principal: Principal, permission: Permission) : Bool {
        switch (roles.get(principal)) {
            case (?#Admin) { true };
            case (?#Server) {
                permission == #ManageRounds or
                permission == #UpdateModels or
                permission == #ViewStats
            };
            case (?#Client) {
                permission == #ViewStats
            };
            case (?#Observer) {
                permission == #ViewStats
            };
            case null {
                // Check if this is the admin principal
                if (principal == admin) { true } else { false }
            };
        }
    };

    // Admin initialization (can only be called once by deployer)
    public shared(msg) func init_admin() : async Bool {
        // Only allow this to be called once by the deployer
        if (admin != Principal.fromText("2vxsx-fae")) {
            return false;
        };
        admin := msg.caller;
        roles.put(admin, #Admin);
        return true;
    };

    // Admin functions
    public shared(msg) func admin_set_server(serverPrincipalId: Principal) : async Bool {
        if (not hasRole(msg.caller, #Admin)) {
            return false;
        };
        roles.put(serverPrincipalId, #Server);
        serverPrincipal := ?serverPrincipalId;
        return true;
    };

    public shared(msg) func admin_approve_client(clientId: Principal) : async Bool {
        if (not hasRole(msg.caller, #Admin)) {
            return false;
        };

        switch (clients.get(clientId)) {
            case (?client) {
                if (client.status == #Pending) {
                    let updatedClient: Client = {
                        id = client.id;
                        registered_at = client.registered_at;
                        last_active = Time.now();
                        status = #Active;
                        total_rounds_participated = client.total_rounds_participated;
                        total_samples_contributed = client.total_samples_contributed;
                    };
                    clients.put(clientId, updatedClient);
                    roles.put(clientId, #Client);
                    return true;
                } else {
                    return false; // Client not in pending status
                };
            };
            case null {
                return false; // Client not found
            };
        };
    };

    public shared(msg) func admin_reject_client(clientId: Principal) : async Bool {
        if (not hasRole(msg.caller, #Admin)) {
            return false;
        };

        switch (clients.get(clientId)) {
            case (?client) {
                if (client.status == #Pending) {
                    let updatedClient: Client = {
                        id = client.id;
                        registered_at = client.registered_at;
                        last_active = client.last_active;
                        status = #Rejected;
                        total_rounds_participated = client.total_rounds_participated;
                        total_samples_contributed = client.total_samples_contributed;
                    };
                    clients.put(clientId, updatedClient);
                    return true;
                } else {
                    return false; // Client not in pending status
                };
            };
            case null {
                return false; // Client not found
            };
        };
    };

    public shared(msg) func admin_remove_client(clientId: Principal) : async Bool {
        if (not hasRole(msg.caller, #Admin)) {
            return false;
        };

        // Remove from clients and roles
        clients.delete(clientId);
        roles.delete(clientId);
        return true;
    };

    public query func get_pending_clients() : async [Client] {
        let allClients = Iter.toArray(clients.vals());
        Array.filter<Client>(allClients, func(client: Client) : Bool {
            switch (client.status) {
                case (#Pending) { true };
                case (_) { false };
            }
        });
    };

    public query func get_admin_principal() : async Principal {
        admin
    };

    // Client management functions
    public shared(msg) func register_client() : async Bool {
        let clientId = msg.caller;
        
        // Check if client is already registered
        if (Option.isSome(clients.get(clientId))) {
            return false;
        };
        
        // Register new client with Pending status (requires admin approval)
        let newClient: Client = {
            id = clientId;
            registered_at = Time.now();
            last_active = Time.now();
            status = #Pending;
            total_rounds_participated = 0;
            total_samples_contributed = 0;
        };
        
        clients.put(clientId, newClient);
        return true;
    };
    
    public shared(msg) func delete_client(clientId: Principal) : async Bool {
        let caller = msg.caller;
        
        // Only allow client to delete themselves
        if (caller != clientId) {
            return false;
        };
        
        // Check if client exists
        if (Option.isNull(clients.get(clientId))) {
            return false;
        };
        
        // Delete client
        clients.delete(clientId);
        return true;
    };
    
    public query func list_clients() : async [Client] {
        let values = Iter.toArray(clients.vals());
        return values;
    };
    
    // Model update functions
    public shared(msg) func submit_update(modelBlob: Blob) : async Bool {
        let clientId = msg.caller;

        // Check if client is registered and active
        switch (clients.get(clientId)) {
            case (?client) {
                if (client.status != #Active) {
                    return false; // Only active clients can submit updates
                };
            };
            case null {
                return false; // Client not registered
            };
        };
        
        // Update client's last active time
        switch (clients.get(clientId)) {
            case (?client) {
                let updatedClient: Client = {
                    id = client.id;
                    registered_at = client.registered_at;
                    last_active = Time.now();
                    status = client.status;
                    total_rounds_participated = client.total_rounds_participated;
                    total_samples_contributed = client.total_samples_contributed;
                };
                clients.put(clientId, updatedClient);
            };
            case null {};
        };
        
        // In a real implementation, we would store the model update
        // For now, we'll just acknowledge receipt
        return true;
    };
    
    // Aggregation functions
    public shared func aggregate_updates() : async Bool {
        // In a real implementation, we would aggregate model updates from clients
        // For now, we'll just return true to indicate success
        return true;
    };
    
    // Global model functions
    public shared func update_global_model(modelBlob: Blob) : async Bool {
        globalModel := modelBlob;
        return true;
    };
    
    public query func get_global_model() : async Blob {
        return globalModel;
    };
    
    // Training round functions (server-only)
    public shared(msg) func start_training_round(participants: [Principal]) : async ?Nat {
        // Check if caller has server permissions
        if (not hasPermission(msg.caller, #ManageRounds)) {
            return null;
        };

        // Verify all participants are registered and active
        for (participant in participants.vals()) {
            switch (clients.get(participant)) {
                case (?client) {
                    if (client.status != #Active) {
                        return null; // Only active clients can participate
                    };
                };
                case null {
                    return null; // Participant not registered
                };
            };
        };
        
        // Create new training round
        let roundId = nextRoundId;
        nextRoundId += 1;
        
        let newRound: TrainingRound = {
            id = roundId;
            timestamp = Time.now();
            model_file = "model_" # Nat.toText(roundId) # ".joblib";
            participants = participants;
            status = #Pending;
            metadata = null;
        };
        
        trainingRounds.put(roundId, newRound);
        return ?roundId;
    };
    
    public query func list_training_rounds() : async [TrainingRound] {
        let values = Iter.toArray(trainingRounds.vals());
        return values;
    };
    
    public query func get_training_round(roundId: Nat) : async ?TrainingRound {
        return trainingRounds.get(roundId);
    };

    public query func get_training_round_metadata(roundId: Nat) : async ?ModelMetadata {
        return modelMetadata.get(roundId);
    };

    public query func get_all_training_rounds() : async [(Nat, TrainingRound)] {
        return Iter.toArray(trainingRounds.entries());
    };

    public query func get_all_model_metadata() : async [(Nat, ModelMetadata)] {
        return Iter.toArray(modelMetadata.entries());
    };

    public query func get_training_history() : async {
        total_rounds: Nat;
        rounds: [(Nat, ModelMetadata)];
    } {
        let rounds = Iter.toArray(modelMetadata.entries());
        return {
            total_rounds = rounds.size();
            rounds = rounds;
        };
    };

    // Enhanced client management functions
    public shared(msg) func register_client_enhanced() : async ClientRegistrationResult {
        let clientId = msg.caller;

        // Check if client is already registered
        switch (clients.get(clientId)) {
            case (?existingClient) {
                return #AlreadyRegistered;
            };
            case null {
                // Register new client with Pending status (requires admin approval)
                let newClient: Client = {
                    id = clientId;
                    registered_at = Time.now();
                    last_active = Time.now();
                    status = #Pending;
                    total_rounds_participated = 0;
                    total_samples_contributed = 0;
                };

                clients.put(clientId, newClient);
                return #PendingApproval(newClient);
            };
        };
    };

    public shared(msg) func update_client_status(clientId: Principal, newStatus: ClientStatus) : async Bool {
        let caller = msg.caller;

        // Only allow client to update their own status or admin (for now, any caller can update)
        switch (clients.get(clientId)) {
            case (?client) {
                let updatedClient: Client = {
                    id = client.id;
                    registered_at = client.registered_at;
                    last_active = client.last_active;
                    status = newStatus;
                    total_rounds_participated = client.total_rounds_participated;
                    total_samples_contributed = client.total_samples_contributed;
                };
                clients.put(clientId, updatedClient);
                return true;
            };
            case null {
                return false;
            };
        };
    };

    public query func get_client_info(clientId: Principal) : async ?Client {
        return clients.get(clientId);
    };

    public query func get_active_clients() : async [Client] {
        let allClients = Iter.toArray(clients.vals());
        Array.filter<Client>(allClients, func(client: Client) : Bool {
            switch (client.status) {
                case (#Active) { true };
                case (_) { false };
            }
        });
    };

    // Model metadata management
    public shared func store_model_metadata(roundId: Nat, metadata: ModelMetadata) : async Bool {
        modelMetadata.put(roundId, metadata);

        // Update the training round with metadata
        switch (trainingRounds.get(roundId)) {
            case (?round) {
                let updatedRound: TrainingRound = {
                    id = round.id;
                    timestamp = round.timestamp;
                    model_file = round.model_file;
                    participants = round.participants;
                    status = #Completed;
                    metadata = ?metadata;
                };
                trainingRounds.put(roundId, updatedRound);
                return true;
            };
            case null {
                return false;
            };
        };
    };

    public query func get_model_metadata(roundId: Nat) : async ?ModelMetadata {
        return modelMetadata.get(roundId);
    };



    // Training round management enhancements
    public shared func update_round_status(roundId: Nat, newStatus: RoundStatus) : async Bool {
        switch (trainingRounds.get(roundId)) {
            case (?round) {
                let updatedRound: TrainingRound = {
                    id = round.id;
                    timestamp = round.timestamp;
                    model_file = round.model_file;
                    participants = round.participants;
                    status = newStatus;
                    metadata = round.metadata;
                };
                trainingRounds.put(roundId, updatedRound);
                return true;
            };
            case null {
                return false;
            };
        };
    };

    public shared func complete_training_round_enhanced(
        roundId: Nat,
        participants: [ClientParticipation],
        totalExamples: Nat,
        numTrees: Nat,
        accuracy: Float,
        modelHash: Text,
        modelFilename: Text,
        trainingStartTime: Time.Time,
        trainingEndTime: Time.Time
    ) : async Bool {
        switch (trainingRounds.get(roundId)) {
            case (?round) {
                // Create enhanced metadata
                let metadata: ModelMetadata = {
                    round_id = roundId;
                    timestamp = Time.now();
                    training_start_time = trainingStartTime;
                    training_end_time = trainingEndTime;
                    num_clients = participants.size();
                    total_examples = totalExamples;
                    num_trees = numTrees;
                    accuracy = accuracy;
                    model_hash = modelHash;
                    model_filename = modelFilename;
                    participants = participants;
                };

                // Extract principal IDs for the training round
                let principalIds = Array.map<ClientParticipation, Principal>(participants, func(p) = p.principal_id);

                // Update training round
                let updatedRound: TrainingRound = {
                    id = round.id;
                    timestamp = round.timestamp;
                    model_file = modelFilename;
                    participants = principalIds;
                    status = #Completed;
                    metadata = ?metadata;
                };

                trainingRounds.put(roundId, updatedRound);
                modelMetadata.put(roundId, metadata);

                // Update participant statistics
                for (participant in participants.vals()) {
                    switch (clients.get(participant.principal_id)) {
                        case (?client) {
                            let updatedClient: Client = {
                                id = client.id;
                                registered_at = client.registered_at;
                                last_active = Time.now();
                                status = client.status;
                                total_rounds_participated = client.total_rounds_participated + 1;
                                total_samples_contributed = client.total_samples_contributed + participant.samples_contributed;
                            };
                            clients.put(participant.principal_id, updatedClient);
                        };
                        case null {};
                    };
                };

                return true;
            };
            case null {
                return false;
            };
        };
    };

    // Statistics and analytics
    public query func get_system_stats() : async {
        total_clients: Nat;
        active_clients: Nat;
        total_rounds: Nat;
        completed_rounds: Nat;
        total_samples_processed: Nat;
    } {
        let allClients = Iter.toArray(clients.vals());
        let activeClients = Array.filter<Client>(allClients, func(client: Client) : Bool {
            switch (client.status) {
                case (#Active) { true };
                case (_) { false };
            }
        });

        let allRounds = Iter.toArray(trainingRounds.vals());
        let completedRounds = Array.filter<TrainingRound>(allRounds, func(round: TrainingRound) : Bool {
            switch (round.status) {
                case (#Completed) { true };
                case (_) { false };
            }
        });

        var totalSamples: Nat = 0;
        for (client in allClients.vals()) {
            totalSamples += client.total_samples_contributed;
        };

        {
            total_clients = allClients.size();
            active_clients = activeClients.size();
            total_rounds = allRounds.size();
            completed_rounds = completedRounds.size();
            total_samples_processed = totalSamples;
        }
    };

    // Authentication helper
    public query func is_client_registered(clientId: Principal) : async Bool {
        Option.isSome(clients.get(clientId));
    };

    public query func is_client_active(clientId: Principal) : async Bool {
        switch (clients.get(clientId)) {
            case (?client) {
                switch (client.status) {
                    case (#Active) { true };
                    case (_) { false };
                }
            };
            case null { false };
        };
    };
}