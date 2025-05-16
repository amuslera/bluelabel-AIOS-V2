import React from 'react';
import { Terminal } from '../../components/Terminal/Terminal';

export const TerminalPage: React.FC = () => {
  return (
    <div className="h-[calc(100vh-200px)]">
      <Terminal />
    </div>
  );
};