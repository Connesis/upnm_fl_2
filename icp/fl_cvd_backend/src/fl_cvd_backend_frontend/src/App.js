import { html, render } from 'lit-html';
import { fl_cvd_backend_backend } from 'declarations/fl_cvd_backend_backend';
import logo from './logo2.svg';

class App {
  clients = [];
  trainingRounds = [];
  model = null;

  constructor() {
    this.#loadData();
  }

  #loadData = async () => {
    try {
      this.clients = await fl_cvd_backend_backend.list_clients();
      this.trainingRounds = await fl_cvd_backend_backend.list_training_rounds();
      this.model = await fl_cvd_backend_backend.get_global_model();
      this.#render();
    } catch (error) {
      console.error('Error loading data:', error);
    }
  };

  #handleRegister = async (e) => {
    e.preventDefault();
    try {
      const result = await fl_cvd_backend_backend.register_client();
      if (result) {
        alert('Client registered successfully!');
        this.#loadData(); // Refresh data
      } else {
        alert('Failed to register client. You might already be registered.');
      }
    } catch (error) {
      console.error('Error registering client:', error);
      alert('Error registering client');
    }
  };

  #handleStartRound = async (e) => {
    e.preventDefault();
    try {
      // In a real implementation, we would get the list of participants
      // For now, we'll just pass an empty array
      const result = await fl_cvd_backend_backend.start_training_round([]);
      if (result) {
        alert('Training round started successfully!');
        this.#loadData(); // Refresh data
      } else {
        alert('Failed to start training round');
      }
    } catch (error) {
      console.error('Error starting training round:', error);
      alert('Error starting training round');
    }
  };

  #render() {
    let body = html`
      <main>
        <img src="${logo}" alt="DFINITY logo" />
        <h1>Federated Learning System for CVD Prediction</h1>
        
        <section>
          <h2>Client Management</h2>
          <button @click="${this.#handleRegister}">Register Client</button>
          <h3>Registered Clients (${this.clients.length})</h3>
          <ul>
            ${this.clients.map(client => html`
              <li>
                <strong>Principal:</strong> ${client.id.toString()}<br>
                <strong>Registered:</strong> ${new Date(Number(client.registered_at / 1000000n)).toLocaleString()}<br>
                <strong>Last Active:</strong> ${new Date(Number(client.last_active / 1000000n)).toLocaleString()}
              </li>
            `)}
          </ul>
        </section>
        
        <section>
          <h2>Training Rounds</h2>
          <button @click="${this.#handleStartRound}">Start New Training Round</button>
          <h3>Previous Rounds (${this.trainingRounds.length})</h3>
          <ul>
            ${this.trainingRounds.map(round => html`
              <li>
                <strong>Round ID:</strong> ${round.id}<br>
                <strong>Timestamp:</strong> ${new Date(Number(round.timestamp / 1000000n)).toLocaleString()}<br>
                <strong>Model File:</strong> ${round.model_file}<br>
                <strong>Participants:</strong> ${round.participants.length}
              </li>
            `)}
          </ul>
        </section>
        
        <section>
          <h2>Global Model</h2>
          <p>Model size: ${this.model ? this.model.length : 0} bytes</p>
          <button>Download Global Model</button>
        </section>
      </main>
    `;
    render(body, document.getElementById('root'));
  }
}

export default App;