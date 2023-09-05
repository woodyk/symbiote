import React from 'react';
import { BrowserRouter as Router, Route, Switch } from 'react-router-dom';
import HomePage from './pages/HomePage';
import ChatPage from './pages/ChatPage';
import SettingsPage from './pages/SettingsPage';
import HelpPage from './pages/HelpPage';

function App() {
  return (
    <Router>
      <Switch>
        <Route path="/" exact component={HomePage} />
        <Route path="/chat" component={ChatPage} />
        <Route path="/settings" component={SettingsPage} />
        <Route path="/help" component={HelpPage} />
      </Switch>
    </Router>
  );
}

export default App;

